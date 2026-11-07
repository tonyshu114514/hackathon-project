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

from findit import apr, arcgis, ckan, gtfs
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

    # City boundary: the fallback extent when the inventory has no sites for this city.
    burl, _ = layer("boundary", meta)
    boundary = cached(f"{slug}_boundary", lambda: arcgis.query_all(
        burl, where=f"UPPER(CITY) = '{city['match']}'", max_offset=0.0001))
    bshape = to_shape(boundary[0].get("geometry")) if boundary else None
    if not sites and bshape is None:
        print("  ! no sites and no city boundary matched. Check the spelling in meta.json fields / sample.")
        return
    if not sites:
        print("  ! no sites in SCAG's inventory for this city; context layers will use the city boundary.")

    oid = m["oid"]
    apn_f = FIELD_OVERRIDES["site_apn"] or arcgis.find_field(
        m["fields"], exact=("Assessor_Parcel_Number",), contains=(("apn",), ("parcel",)))
    shapes = [to_shape(s.get("geometry")) for s in sites]
    extent = [s for s in shapes if s is not None] or [bshape]
    xs = [b for s in extent for b in (s.bounds[0], s.bounds[2])]
    ys = [b for s in extent for b in (s.bounds[1], s.bounds[3])]
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
    if sites and sum(len(v or []) for v in fps.values()) == 0:
        print("  ! zero footprints for every site: the spatial query may be failing. Coverage will be unknown.")

    # Parcels (year built) and SCAG zoning, matched by APN.
    apns = [digits(s["attributes"].get(apn_f)) for s in sites if apn_f]
    apns = [a for a in apns if a]
    for key, exact, store in ([] if not sites else (("parcels", ("ASSESSMENT_NO",), "parcels"), ("zoning", ("APN24",), "zoning"))):
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

    # City RHNA progress (HCD, data.ca.gov).
    try:
        rows = cached(f"{slug}_rhna", lambda: ckan.search_all(SOURCES["rhna"]["ckan"], {"Jurisdiction": city["match"]}))
        if "rhna" not in meta:
            meta["rhna"] = {"url": SOURCES["rhna"]["page"], "label": SOURCES["rhna"]["label"],
                            "fetched": date.today().isoformat()}
            save_meta(meta)
        print(f"  rhna: {len(rows)} rows")
    except Exception as e:
        print(f"  ! rhna failed ({e}). RHNA progress will be left off.")

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
    if "places" not in meta:
        meta["places"] = {"url": SOURCES["places"]["page"], "label": SOURCES["places"]["label"],
                          "fetched": date.today().isoformat()}
        save_meta(meta)
    print(f"  places: {len(cached(f'{slug}_places', places))} sites named")


def fetch_gtfs(meta):
    path = CACHE / "octa_gtfs.zip"
    if path.exists():
        return
    print("\n== OCTA bus routes (GTFS)")
    try:
        r = requests.get(gtfs.URL, headers=arcgis.UA, timeout=180)
        r.raise_for_status()
        path.write_bytes(r.content)
        meta["gtfs"] = {"url": gtfs.URL, "label": "OCTA GTFS feed (bus routes)", "fetched": date.today().isoformat()}
        save_meta(meta)
        print(f"  saved {len(r.content) // 1024} KB")
    except Exception as e:
        print(f"  ! OCTA GTFS failed ({e}). Bus routes will be left off the map.")


def fetch_apr(meta):
    path = CACHE / "apr_a2.json"
    if path.exists():
        return
    print("\n== HCD Annual Progress Report, Table A2 (permits by APN)")
    try:
        res, rows = apr.fetch_rows([c["match"] for c in CITIES.values()])
        path.write_text(json.dumps(rows))
        meta["apr"] = {"url": apr.PAGE, "label": f"HCD Housing Element APR data ({res.get('name')})",
                       "fetched": date.today().isoformat(), "resource_id": res["id"]}
        save_meta(meta)
        print(f"  kept {len(rows)} rows for our three cities")
    except Exception as e:
        print(f"  ! APR failed ({e}). The permit check will show unknown.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", choices=list(CITIES), action="append")
    ap.add_argument("--skip-apr", action="store_true", help="skip the statewide permit data")
    args = ap.parse_args()
    meta = load_meta()
    for slug in args.city or list(CITIES):
        fetch_city(slug, meta)
    fetch_gtfs(meta)
    if not args.skip_apr:
        fetch_apr(meta)
    print("\nDone. Now run: python build.py")


if __name__ == "__main__":
    main()
