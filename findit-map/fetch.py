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

from findit import apr, arcgis, ckan, gtfs, surplus
from findit.geom import to_shape
from findit.sources import AREA_LAYERS, CITIES, FIELD_OVERRIDES, SOURCES

CACHE = pathlib.Path("data/cache")
CACHE.mkdir(parents=True, exist_ok=True)
SKIP = set()  # layer keys to skip this run, from --skip
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


def hcd_to_scag(f):
    """Rename HCD Table A fields to the SCAG names build.py already reads, and keep HCD's extras.

    HCD rows with every capacity at 0 (Santa Ana lists all sites as 'Pending Project' with no units)
    get None, so capacity shows as unknown instead of zero.
    """
    a = f["attributes"]
    caps = [a.get("Lower_Income_Capacity"), a.get("Moderate_Income_Capacity"),
            a.get("Above_Moderate_Income_Capacity"), a.get("Total_Capacity")]
    blank = all(not c for c in caps)
    out = {
        "OBJECTID": a.get("OBJECTID_1"), "Jurisdiction": a.get("jurisdiction_name"), "COUNTY": a.get("County_Name"),
        "Assessor_Parcel_Number": a.get("AssessorParcelNumber"),
        "Low_Income_HE_Capacity": None if blank else caps[0],
        "Moderate_Income_HE_Capacity": None if blank else caps[1],
        "Above_Moderate_Income_HE_Capacity": None if blank else caps[2],
        "Total_HE_Capacity": None if blank else caps[3],
        "HE_Address": a.get("Site_Address_Intersection"), "HE_Existing_Use": a.get("Existing_Use_Vacancy"),
        "HE_Status": a.get("Site_Status"), "HE_Publicly_Owned": a.get("Publicly_Owned"),
        "HE_Zoning": a.get("Zoning_Designation_Current"), "HE_Max_Density": a.get("Max_Density_Allowed_units_per_a"),
        "HE_Acres": a.get("Parcel_Size_Acres"), "HE_Prior_Cycles": a.get("Identified_in_Last_Two_Planning"),
    }
    return {"attributes": out, "geometry": f.get("geometry")}


def in_clauses(field, values, n=150):
    vals = sorted(set(values))
    for i in range(0, len(vals), n):
        yield f"{field} IN (" + ",".join("'" + v.replace("'", "''") + "'" for v in vals[i:i + n]) + ")"


def fetch_city(slug, meta):
    city = CITIES[slug]
    print(f"\n== {city['name']}")

    src = city.get("sites", "he_sites")
    url, m = layer(src, meta)
    if src == "hcd_sites":
        where = f"UPPER(jurisdiction_name) = '{city['match']}'"
        sites = cached(f"{slug}_sites", lambda: [hcd_to_scag(f) for f in arcgis.query_all(url, where)])
        # Field detection below reads m["fields"]; point it at the renamed attributes.
        m = dict(m, oid="OBJECTID", fields=list(sites[0]["attributes"]) if sites else m["fields"])
    else:
        county = arcgis.find_field(m["fields"], exact=("COUNTY",))
        juris = arcgis.find_field(m["fields"], exact=("Jurisdiction",), contains=(("juris",),))
        where = f"UPPER({juris}) LIKE '%{city['match']}%'" + (f" AND UPPER({county}) = 'ORANGE'" if county else "")
        sites = cached(f"{slug}_sites", lambda: arcgis.query_all(url, where))
        # SCAG lists no existing use. Borrow it from HCD's Table A record for the same APN, so open land can be
        # scored the same way as the HCD cities when footprints are skipped (build.py joins by APN).
        try:
            hurl, _ = layer("hcd_sites", meta)
            hcd = cached(f"{slug}_hcd_use", lambda: [hcd_to_scag(f) for f in arcgis.query_all(
                hurl, f"UPPER(jurisdiction_name) = '{city['match']}'", geometry=False)])
            print(f"  HCD existing use for SCAG sites: {len(hcd)} HCD records")
        except Exception as e:
            print(f"  ! HCD existing use failed ({e}). Open land stays unknown when footprints are skipped.")
    print(f"  housing-element sites: {len(sites)} ({SOURCES[src]['label'].split(' (')[0]})")

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
    # Surplus Land Act notices for this city become extra candidate sites (findit/surplus.py), so the same
    # footprint, parcel, zoning, hazard and permit lookups below cover them.
    sites = sites + surplus_sites(slug, city, meta, apn_f)

    shapes = [to_shape(s.get("geometry")) for s in sites]
    extent = [s for s in shapes if s is not None] or [bshape]
    xs = [b for s in extent for b in (s.bounds[0], s.bounds[2])]
    ys = [b for s in extent for b in (s.bounds[1], s.bounds[3])]
    bbox = (min(xs) - 0.003, min(ys) - 0.003, max(xs) + 0.003, max(ys) + 0.003)

    # Building footprints: one small query per site, saved as it goes so a crash can resume.
    # The OC footprint server has been unreliable, so a failure here never stops the run: coverage is then unknown.
    fp_path = CACHE / f"{slug}_footprints.json"
    fps = json.loads(fp_path.read_text()) if fp_path.exists() else {}
    furl = None
    if "footprints" in SKIP:
        print("  footprints: skipped (--skip footprints); coverage will be unknown")
    else:
        try:
            furl, _ = layer("footprints", meta)
        except Exception as e:
            print(f"  ! footprints layer unavailable ({e}); coverage will be unknown")
    todo = [] if furl is None else [s for s in sites if str(s["attributes"].get(oid)) not in fps]
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
    if sites and furl is not None and sum(len(v or []) for v in fps.values()) == 0:
        print("  ! zero footprints for every site: the spatial query may be failing. Coverage will be unknown.")

    # Parcels (year built) and SCAG zoning, matched by APN.
    apns = [digits(s["attributes"].get(apn_f)) for s in sites if apn_f]
    apns = [a for a in apns if a]
    for key, exact, store in ([] if not sites else (("parcels", ("ASSESSMENT_NO",), "parcels"), ("zoning", ("APN24",), "zoning"))):
        try:
            lurl, lm = layer(key, meta)
        except Exception as e:
            print(f"  ! {key} failed ({e}). Year built and zoning from this layer will show unknown.")
            continue
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
        try:
            rows = cached(f"{slug}_{store}", get)
        except Exception as e:
            print(f"  ! {key} failed ({e}). Year built and zoning from this layer will show unknown.")
            continue
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
            if sh is None or s["attributes"].get("HE_Address"):
                continue  # the city's own address is used first, so no lookup is needed
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


def fetch_surplus(meta):
    """Statewide Surplus Land Act notices CSV from data.ca.gov, cached once; the staff-contact column is dropped."""
    path = CACHE / "surplus_noa.json"
    if path.exists():
        return
    print("\n== HCD Surplus Land Act notices (data.ca.gov)")
    try:
        pkg = requests.get("https://data.ca.gov/api/3/action/package_show", params={"id": surplus.PACKAGE},
                           headers=arcgis.UA, timeout=60).json()["result"]
        res = next(r for r in pkg["resources"] if (r.get("format") or "").upper() == "CSV")
        r = requests.get(res["url"], headers=arcgis.UA, timeout=300)
        r.raise_for_status()
        rows = surplus.read_rows(r.content.decode("utf-8-sig", errors="replace"))
        path.write_text(json.dumps(rows))
        meta["surplus"] = {"url": SOURCES["surplus"]["page"], "label": SOURCES["surplus"]["label"],
                           "fetched": date.today().isoformat(), "csv": res["url"], "modified": pkg.get("metadata_modified")}
        save_meta(meta)
        print(f"  saved {len(rows)} notice rows statewide")
    except Exception as e:
        print(f"  ! surplus notices failed ({e}). Surplus sites will be left off.")


def surplus_sites(slug, city, meta, apn_field):
    """This city's Surplus Land Act notices as pseudo sites, with parcel outlines from the county layer by APN."""
    path = CACHE / "surplus_noa.json"
    rows = json.loads(path.read_text()) if path.exists() else []
    mine = surplus.rows_for_city(rows, city["match"])
    if not mine:
        return []

    def build():
        apns = sorted({digits(r["APN"]) for r in mine if len(digits(r["APN"])) >= 8})
        geom = {}
        if apns:
            try:
                lurl, lm = layer("parcels", meta)
                f = FIELD_OVERRIDES.get("parcel_apn") or arcgis.find_field(lm["fields"], exact=("ASSESSMENT_NO",), contains=(("apn",),))
                try:
                    sample = arcgis.query_once(lurl, where=f"{f} IS NOT NULL", out_fields=f, geometry=False, count=1)
                except Exception:
                    sample = []
                fmt = sample[0]["attributes"][f] if sample else None
                for clause in in_clauses(f, [like_sample(fmt, a) for a in apns]):
                    for feat in arcgis.query_once(lurl, where=clause, out_fields=f, geometry=True):
                        geom[digits(feat["attributes"].get(f))] = feat.get("geometry")
            except Exception as e:
                print(f"  ! parcel outlines for surplus notices failed ({e}); outlines will be approximate.")
        out = []
        for r in mine:
            d = digits(r["APN"])
            site = surplus.to_site(r, geom.get(d) if len(d) >= 8 else None)
            if site:
                out.append(site)
        return out

    out = cached(f"{slug}_surplus", build)
    n_approx = sum(1 for x in out if x["attributes"].get("SLA_APPROX_OUTLINE"))
    print(f"  surplus land notices: {len(out)} sites ({n_approx} with an approximate outline)")
    return out


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
        print(f"  kept {len(rows)} rows for the {len(CITIES)} Orange County jurisdictions")
    except Exception as e:
        print(f"  ! APR failed ({e}). The permit check will show unknown.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", choices=list(CITIES), action="append")
    ap.add_argument("--skip-apr", action="store_true", help="skip the statewide permit data")
    ap.add_argument("--skip", action="append", default=[], metavar="LAYER",
                    help="skip a layer this run, e.g. --skip footprints when the OC server is down")
    args = ap.parse_args()
    SKIP.update(args.skip)
    meta = load_meta()
    if "surplus" not in SKIP:
        fetch_surplus(meta)
    for slug in args.city or list(CITIES):
        fetch_city(slug, meta)
    fetch_gtfs(meta)
    if not args.skip_apr:
        fetch_apr(meta)
    print("\nDone. Now run: python build.py")


if __name__ == "__main__":
    main()
