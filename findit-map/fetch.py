"""Download and cache every layer the map needs, for each city.

Run once on a laptop with internet. Re-running skips anything already in data/cache/.
Delete a file in data/cache/ to refresh it.

    python fetch.py                  # all three cities
    python fetch.py --city irvine    # one city
"""
import argparse
import json
import pathlib
import re
import time
from datetime import date

import requests

from findit import arcgis, ckan
from findit.geom import to_shape
from findit.sources import AREA_LAYERS, CITIES, FIELD_OVERRIDES, SOURCES

CACHE = pathlib.Path("data/cache")
CACHE.mkdir(parents=True, exist_ok=True)
META = CACHE / "meta.json"


def load_meta():
    return json.loads(META.read_text()) if META.exists() else {}


def save_meta(m):
    META.write_text(json.dumps(m, indent=2))


def cached(name, fn):
    path = CACHE / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text())
    data = fn()
    path.write_text(json.dumps(data))
    return data


def layer(key, meta):
    if key in meta and "url" in meta[key]:
        return meta[key]["url"], meta[key]
    url = arcgis.resolve_layer(SOURCES[key])
    li = arcgis.info(url)
    meta[key] = {"url": url, "label": SOURCES[key]["label"], "fetched": date.today().isoformat(),
                 "fields": arcgis.field_names(li), "oid": li.get("objectIdField", "OBJECTID")}
    save_meta(meta)
    return url, meta[key]


def digits(s):
    return re.sub(r"\D", "", str(s or ""))


def like_sample(sample, d):
    """Format digits d the way sample APN is written (e.g. 397-341-05)."""
    if sample is None or len(digits(sample)) != len(d):
        return d
    it = iter(d)
    return "".join(next(it) if c.isdigit() else c for c in str(sample))


def in_clauses(field, values, n=150):
    vals = sorted(set(values))
    for i in range(0, len(vals), n):
        yield f"{field} IN (" + ",".join("'" + v.replace("'", "''") + "'" for v in vals[i:i + n]) + ")"


def fetch_city(slug, meta):
    city = CITIES[slug]
    print(f"\n== {city['name']}")

    url, m = layer("he_sites", meta)
    county = arcgis.find_field(m["fields"], exact=("COUNTY",))
    juris = arcgis.find_field(m["fields"], exact=("Jurisdiction",), contains=(("juris",),))
    where = f"UPPER({juris}) LIKE '%{city['match']}%'" + (f" AND UPPER({county}) = 'ORANGE'" if county else "")
    sites = cached(f"{slug}_sites", lambda: arcgis.query_all(url, where))
    print(f"  housing-element sites: {len(sites)}")
    if not sites:
        print("  ! no sites matched. Check the Jurisdiction spelling in meta.json fields / sample.")
        return
    oid = m["oid"]
    apn_f = FIELD_OVERRIDES["site_apn"] or arcgis.find_field(
        m["fields"], exact=("Assessor_Parcel_Number",), contains=(("apn",), ("parcel",)))
    shapes = [to_shape(s.get("geometry")) for s in sites]
    xs = [b for s in shapes if s is not None for b in (s.bounds[0], s.bounds[2])]
    ys = [b for s in shapes if s is not None for b in (s.bounds[1], s.bounds[3])]
    bbox = (min(xs) - 0.003, min(ys) - 0.003, max(xs) + 0.003, max(ys) + 0.003)

    # Building footprints: one small query per site, saved as it goes so a crash can resume.
    furl, _ = layer("footprints", meta)
    fp_path = CACHE / f"{slug}_footprints.json"
    fps = json.loads(fp_path.read_text()) if fp_path.exists() else {}
    todo = [s for s in sites if str(s["attributes"].get(oid)) not in fps]
    for i, s in enumerate(todo, 1):
        key = str(s["attributes"].get(oid))
        rings = (s.get("geometry") or {}).get("rings")
        try:
            fps[key] = arcgis.query_once(furl, spatial=arcgis.polygon_filter(rings)) if rings else None
        except Exception as e:
            print(f"  footprints failed for site {key}: {e}")
            fps[key] = None
        if i % 25 == 0 or i == len(todo):
            fp_path.write_text(json.dumps(fps))
            print(f"  footprints: {i}/{len(todo)}")
    if sum(len(v or []) for v in fps.values()) == 0:
        print("  ! zero footprints for every site: the spatial query may be failing. Coverage will be unknown.")

    # Parcels (year built) and SCAG zoning, matched by APN.
    apns = [digits(s["attributes"].get(apn_f)) for s in sites if apn_f]
    apns = [a for a in apns if a]
    for key, exact, store in (("parcels", ("ASSESSMENT_NO",), "parcels"), ("zoning", ("APN24",), "zoning")):
        lurl, lm = layer(key, meta)
        f = (FIELD_OVERRIDES.get("parcel_apn") if key == "parcels" else None) or \
            arcgis.find_field(lm["fields"], exact=exact, contains=(("apn",),))
        if not f or not apns:
            print(f"  ! {key}: no APN field found, skipping")
            continue

        def get(lurl=lurl, f=f, key=key):
            try:
                sample = arcgis.query_once(lurl, where=f"{f} IS NOT NULL", out_fields=f,
                                           geometry=False, count=1)
            except Exception:
                sample = []
            fmt = sample[0]["attributes"][f] if sample else None
            out = []
            for clause in in_clauses(f, [like_sample(fmt, a) for a in apns]):
                out += arcgis.query_once(lurl, where=clause, geometry=False)
            return out
        rows = cached(f"{slug}_{store}", get)
        got = {digits(r["attributes"].get(f)) for r in rows}
        print(f"  {key}: matched {len(got & set(apns))}/{len(set(apns))} site APNs")

    # Hazard and transit layers: everything intersecting the city's site bounding box.
    for key in ("flood", "fire_lra", "fire_sra", "landslide", "hqta"):
        try:
            lurl, _ = layer(key, meta)
            rows = cached(f"{slug}_{key}", lambda lurl=lurl: arcgis.query_all(
                lurl, spatial=arcgis.envelope(bbox), max_offset=0.00002))
            print(f"  {key}: {len(rows)} polygons")
        except Exception as e:
            print(f"  ! {key} failed ({e}). The map will show this check as unknown.")

    # Tract and nearby-point layers: a wider box so points just outside a site still count.
    wide = (bbox[0] - 0.012, bbox[1] - 0.012, bbox[2] + 0.012, bbox[3] + 0.012)
    for key in AREA_LAYERS:
        try:
            lurl, _ = layer(key, meta)
            rows = cached(f"{slug}_{key}", lambda lurl=lurl: arcgis.query_all(
                lurl, spatial=arcgis.envelope(wide), max_offset=0.00005))
            print(f"  {key}: {len(rows)} features")
        except Exception as e:
            print(f"  ! {key} failed ({e}). The map will show this check as unknown.")

    # Place names from OpenStreetMap (Nominatim), used to label sites with no assessor address.
    # Nominatim's policy is at most one request per second, so this takes about a minute per city.
    def places():
        out = {}
        for s, sh in zip(sites, shapes):
            if sh is None:
                continue
            pt = sh.representative_point()
            try:
                r = requests.get("https://nominatim.openstreetmap.org/reverse", headers=arcgis.UA, timeout=30,
                                 params={"lat": pt.y, "lon": pt.x, "format": "jsonv2", "zoom": 17}).json()
                out[str(s["attributes"].get(oid))] = {"road": r.get("address", {}).get("road"),
                                                      "display_name": r.get("display_name")}
            except Exception as e:
                print(f"  place lookup failed for site {s['attributes'].get(oid)}: {e}")
            time.sleep(1.1)
        return out
    print(f"  places: {len(cached(f'{slug}_places', places))} sites named")

    # HCD tables on data.ca.gov, matched by jurisdiction name.
    for key, filt, fields in (
            ("apr_a2", {"JURIS_NAME": city["match"]}, APR_FIELDS),
            ("rhna", {"Jurisdiction": city["match"]}, None)):
        try:
            rows = cached(f"{slug}_{key}", lambda key=key, filt=filt, fields=fields:
                          ckan.search_all(SOURCES[key]["ckan"], filt, fields))
            if key not in meta:
                meta[key] = {"url": SOURCES[key]["page"], "label": SOURCES[key]["label"],
                             "fetched": date.today().isoformat()}
                save_meta(meta)
            print(f"  {key}: {len(rows)} rows")
        except Exception as e:
            print(f"  ! {key} failed ({e}). The map will show this check as unknown.")


APR_FIELDS = ["YEAR", "APN", "PRIOR_APN", "STREET_ADDRESS", "PROJECT_NAME", "UNIT_CAT", "TENURE",
              "NO_ENTITLEMENTS", "ENT_APPROVE_DT1", "NO_BUILDING_PERMITS", "BP_ISSUE_DT1", "CO_ISSUE_DT1",
              "BP_ACUTELY_LOW_INCOME_DR", "BP_ACUTELY_LOW_INCOME_NDR", "BP_EXTREMELY_LOW_INCOME_DR",
              "BP_EXTREMELY_LOW_INCOME_NDR", "BP_VLOW_INCOME_DR", "BP_VLOW_INCOME_NDR",
              "BP_LOW_INCOME_DR", "BP_LOW_INCOME_NDR", "BP_MOD_INCOME_DR", "BP_MOD_INCOME_NDR",
              "BP_ABOVE_MOD_INCOME", "CO_ACUTELY_LOW_INCOME_DR", "CO_ACUTELY_LOW_INCOME_NDR",
              "CO_EXTREMELY_LOW_INCOME_DR", "CO_EXTREMELY_LOW_INCOME_NDR", "CO_VLOW_INCOME_DR", "CO_VLOW_INCOME_NDR", "CO_LOW_INCOME_DR",
              "CO_LOW_INCOME_NDR", "CO_MOD_INCOME_DR", "CO_MOD_INCOME_NDR", "CO_ABOVE_MOD_INCOME",
              "LATITUDE", "LONGITUDE"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", choices=list(CITIES), action="append")
    args = ap.parse_args()
    meta = load_meta()
    for slug in args.city or list(CITIES):
        fetch_city(slug, meta)
    print("\nDone. Now run: python build.py")


if __name__ == "__main__":
    main()
