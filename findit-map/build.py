"""Score every cached housing-element site and write the map page.

    python build.py        # writes site/index.html, site/artifact.html and data/results.json
"""
import json
import pathlib
import re
from datetime import date

from shapely.geometry import box
from shapely.strtree import STRtree

from findit import apr, gtfs
from findit.arcgis import find_field
from findit.geom import to_feet, to_polys, to_shape, union
from findit.sources import ASSUMPTIONS, CITIES, FIELD_OVERRIDES, SOURCES

CACHE = pathlib.Path("data/cache")
OUT_HTML = pathlib.Path("site/index.html")
OUT_ARTIFACT = pathlib.Path("site/artifact.html")
OUT_JSON = pathlib.Path("data/results.json")
A = {k: v["value"] for k, v in ASSUMPTIONS.items()}
SFHA = re.compile(r"^(A|AE|AH|AO|AR|A99|V|VE)$")
THIS_YEAR = date.today().year


def load(name):
    p = CACHE / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def digits(s):
    return re.sub(r"\D", "", str(s or ""))


def num(v):
    try:
        x = float(str(v).replace(",", ""))
        return x if x == x else None
    except (TypeError, ValueError):
        return None


def year(v):
    y = num(v)
    return int(y) if y and 1800 < y <= THIS_YEAR + 1 else None


class Layer:
    """A hazard/transit layer with a spatial index. None-safe: missing layer -> 'unknown'."""

    def __init__(self, feats):
        self.ok = feats is not None
        pairs = [(to_shape(f.get("geometry")), f.get("attributes", {})) for f in feats or []]
        pairs = [(s, a) for s, a in pairs if s is not None and not s.is_empty]
        self.shapes = [s for s, _ in pairs]
        self.attrs = [a for _, a in pairs]
        self.tree = STRtree(self.shapes) if self.shapes else None
        self.fields = list(self.attrs[0].keys()) if self.attrs else []

    def hits(self, shape):
        """[(share of site covered, attrs)] for zones covering >= the minimum overlap."""
        if not self.tree:
            return []
        out = []
        for i in self.tree.query(shape):
            inter = shape.intersection(self.shapes[i]).area
            share = inter / shape.area if shape.area else 0
            if share >= A["hazard_min_overlap"]:
                out.append((share, self.attrs[i]))
        return sorted(out, key=lambda t: -t[0])


def check(name, status, detail, source):
    return {"name": name, "status": status, "detail": detail, "source": source}


def overlays(layers, f_fld, f_fire, bbox):
    """Layers already fetched, merged and simplified for drawing. Shapes only; nothing is scored here."""
    clip = box(*bbox)
    tol = 0.00008  # ~8 m: plenty for a city-scale map

    def merged(pairs):
        u = union([s.intersection(clip) for s, _ in pairs])
        return to_polys(u, tol) if u is not None else []

    out = {}
    fl = layers["flood"]
    if fl.ok:
        sfha = [(s, a) for s, a in zip(fl.shapes, fl.attrs) if SFHA.match(str(a.get(f_fld, "")).strip().upper())]
        other = [(s, a) for s, a in zip(fl.shapes, fl.attrs) if not SFHA.match(str(a.get(f_fld, "")).strip().upper())]
        out["flood_sfha"], out["flood_other"] = merged(sfha), merged(other)
    fire_vh, fire_other = [], []
    for k in ("fire_lra", "fire_sra"):
        l = layers[k]
        for s, a in zip(l.shapes, l.attrs):
            (fire_vh if "VERY HIGH" in str(a.get(f_fire[k], "")).upper() else fire_other).append((s, a))
    if layers["fire_lra"].ok or layers["fire_sra"].ok:
        out["fire_vh"], out["fire_other"] = merged(fire_vh), merged(fire_other)
    for k in ("landslide", "hqta"):
        if layers[k].ok:
            out[k] = merged(list(zip(layers[k].shapes, layers[k].attrs)))
    gz = CACHE / "octa_gtfs.zip"
    if gz.exists():
        try:
            out["bus"] = gtfs.routes_in_bbox(gz, bbox)
        except Exception as e:
            print(f"  ! could not read OCTA GTFS ({e})")
    return out


def build_city(slug, meta, notes_all, apr_idx):
    city = CITIES[slug]
    sites = load(f"{slug}_sites")
    if not sites:
        print(f"{city['name']}: no cached sites, skipping (run fetch.py)")
        return None
    notes = []
    sm = meta.get("he_sites", {})
    sf = sm.get("fields") or list(sites[0]["attributes"].keys())
    oid = sm.get("oid", "OBJECTID")
    f_apn = FIELD_OVERRIDES["site_apn"] or find_field(sf, ("Assessor_Parcel_Number",), (("apn",), ("parcel",)))
    f_low = FIELD_OVERRIDES["site_lower_cap"] or find_field(sf, (), (("lower",), ("low", "cap"), ("low", "inc")))
    f_mod = FIELD_OVERRIDES["site_mod_cap"] or find_field(sf, (), (("moderate", "cap"), ("mod", "cap"), ("moderate",)))
    if f_mod and "above" in f_mod.lower():
        f_mod = None
    f_abv = FIELD_OVERRIDES["site_above_cap"] or find_field(sf, (), (("above",),))
    print(f"{city['name']}: site fields -> APN={f_apn} lower={f_low} moderate={f_mod} above={f_abv}")

    # Footprints
    fps = load(f"{slug}_footprints") or {}
    fp_total = sum(len(v or []) for v in fps.values())
    fp_year = None
    if fp_total:
        any_fp = next(f for v in fps.values() if v for f in v)
        fp_year = find_field(list(any_fp["attributes"].keys()), (), (("year",),))
    else:
        notes.append("Building footprints returned nothing for this city, so coverage is unknown.")

    # Parcels: year built by APN
    pm = meta.get("parcels", {})
    parcels = load(f"{slug}_parcels") or []
    p_apn = FIELD_OVERRIDES["parcel_apn"] or find_field(pm.get("fields", []), ("ASSESSMENT_NO",), (("apn",),))
    p_year = FIELD_OVERRIDES["parcel_year"] or find_field(pm.get("fields", []), ("YEAR_BUILT",), (("year",),))
    year_by_apn = {}
    for r in parcels:
        a = r["attributes"]
        y = year(a.get(p_year)) if p_year else None
        k = digits(a.get(p_apn)) if p_apn else ""
        if k:
            year_by_apn.setdefault(k, [])
            if y:
                year_by_apn[k].append(y)
    print(f"  parcels: APN={p_apn} year={p_year} matched={len(year_by_apn)}")
    if not year_by_apn:
        notes.append("Year built did not match any site APN here, so the stale ranking uses building coverage only (weak signal).")

    # Zoning
    zrows = load(f"{slug}_zoning") or []
    zoning = {digits(r["attributes"].get("APN24")): r["attributes"] for r in zrows}

    layers = {k: Layer(load(f"{slug}_{k}")) for k in ("flood", "fire_lra", "fire_sra", "landslide", "hqta")}
    for k, l in layers.items():
        if not l.ok:
            notes.append(f"{SOURCES[k]['label']} did not download, so that check shows unknown.")
    f_fld = FIELD_OVERRIDES["flood_zone"] or find_field(layers["flood"].fields, ("FLD_ZONE",), (("zone",),))
    f_fire = {k: FIELD_OVERRIDES["fire_class"] or find_field(layers[k].fields, ("HAZ_CLASS", "FHSZ_Description"),
                                                             (("haz", "class"), ("fhsz",), ("haz",), ("sev",)))
              for k in ("fire_lra", "fire_sra")}

    out = []
    for s in sites:
        a = s["attributes"]
        shape = to_shape(s.get("geometry"))
        if shape is None or shape.is_empty:
            continue
        key = str(a.get(oid))
        apn = a.get(f_apn) if f_apn else None
        apn_d = digits(apn)
        ft = to_feet(shape)
        acres = ft.area / 43560
        checks = []

        # Coverage
        cov = None
        flist = fps.get(key)
        if fp_total and flist is not None:
            u = union([to_shape(f.get("geometry")) for f in flist])
            cov = 0.0 if u is None else min(to_feet(u).intersection(ft).area / ft.area, 1.0) if ft.area else None
        if cov is None:
            checks.append(check("Building coverage", "unknown", "Footprint data not available for this site.", "footprints"))
        else:
            checks.append(check("Building coverage", "info",
                                f"{cov:.0%} of the site is covered by building footprints.", "footprints"))

        # Year built
        yrs = list(year_by_apn.get(apn_d, []))
        if fp_year and flist:
            yrs += [y for y in (year(f["attributes"].get(fp_year)) for f in flist) if y]
        newest = max(yrs) if yrs else None
        new_build = newest is not None and newest >= A["stale_year_cutoff"]
        if newest is None:
            checks.append(check("Newest building", "unknown", "No year built found for this APN.", "parcels"))
        else:
            checks.append(check("Newest building", "fail" if new_build else "pass",
                                f"Newest year built on the parcel: {newest}." +
                                (f" At or after {A['stale_year_cutoff']} (ASSUMPTION cutoff): the site may already be used."
                                 if new_build else ""), "parcels"))

        # Permit activity reported by the city (HCD APR Table A2)
        acts = [x for x in apr_idx.get(apn_d[:8], []) if x["year"] is None or x["year"] >= A["apr_min_year"]] \
            if apr_idx is not None and len(apn_d) >= 8 else []
        apr_hit = bool(acts)
        if apr_idx is None:
            checks.append(check("Permit activity (APR)", "unknown", "APR data not loaded.", "apr"))
        elif apr_hit:
            yrs_r = sorted({x["year"] for x in acts if x["year"]})
            stg = sorted({s for x in acts for s in x["stages"]})
            checks.append(check("Permit activity (APR)", "fail",
                                f"City reported activity on this APN in {', '.join(map(str, yrs_r)) or 'an APR year'}"
                                + (f" ({', '.join(stg)})" if stg else "") + ". The site may already be in use.", "apr"))
        else:
            checks.append(check("Permit activity (APR)", "pass" if len(apn_d) >= 8 else "unknown",
                                f"No APR row from {A['apr_min_year']} on matched this APN. Cities type APNs by hand, "
                                "so a miss is not proof of no activity." if len(apn_d) >= 8 else "No usable APN.", "apr"))

        # Flood
        fl = layers["flood"]
        if not fl.ok:
            checks.append(check("Flood", "unknown", "Flood layer not loaded.", "flood"))
            sfha = False
        else:
            h = fl.hits(shape)
            zones = [(sh, str(at.get(f_fld, "")).strip().upper()) for sh, at in h]
            sf_hits = [(sh, z) for sh, z in zones if SFHA.match(z)]
            sfha = bool(sf_hits)
            if sf_hits:
                checks.append(check("Flood", "fail", f"FEMA Special Flood Hazard Area, zone {sf_hits[0][1]}, "
                                                     f"{sf_hits[0][0]:.0%} of site.", "flood"))
            elif zones:
                checks.append(check("Flood", "info", f"Mapped flood zone {zones[0][1] or '(blank)'} "
                                                     "(not a Special Flood Hazard Area code).", "flood"))
            else:
                checks.append(check("Flood", "pass", "No mapped flood zone on the site.", "flood"))

        # Fire
        fire_vh, fire_other, fire_known = False, None, False
        for k in ("fire_lra", "fire_sra"):
            l = layers[k]
            if not l.ok:
                continue
            fire_known = True
            for sh, at in l.hits(shape):
                cls = str(at.get(f_fire[k], "")).strip()
                if "VERY HIGH" in cls.upper():
                    fire_vh = True
                else:
                    fire_other = fire_other or (cls or "zone present, class not given")
        if fire_vh:
            checks.append(check("Fire", "fail", "Very High Fire Hazard Severity Zone.", "fire_lra,fire_sra"))
        elif fire_other:
            checks.append(check("Fire", "caution", f"Fire hazard zone: {fire_other}.", "fire_lra,fire_sra"))
        elif fire_known:
            checks.append(check("Fire", "pass", "No fire hazard severity zone on the site.", "fire_lra,fire_sra"))
        else:
            checks.append(check("Fire", "unknown", "Fire layers not loaded.", "fire_lra,fire_sra"))

        # Landslide
        ls = layers["landslide"]
        slide = bool(ls.hits(shape)) if ls.ok else None
        checks.append(check("Landslide", "unknown" if slide is None else "caution" if slide else "pass",
                            "Landslide layer not loaded." if slide is None else
                            "In a CGS landslide zone of required investigation: site study needed." if slide else
                            "Not in a CGS landslide zone.", "landslide"))

        # Transit
        hq = layers["hqta"]
        transit = bool(hq.hits(shape)) if hq.ok else None
        checks.append(check("Transit", "unknown" if transit is None else "pass" if transit else "info",
                            "Transit layer not loaded." if transit is None else
                            "In a High Quality Transit Area." if transit else "Not in a High Quality Transit Area.",
                            "hqta"))

        z = zoning.get(apn_d, {})
        low = num(a.get(f_low)) if f_low else None

        # Scores (weights are ASSUMPTIONS, shown on the page)
        w = A["weights_promising"]
        parts = {}
        if cov is not None:
            parts["open_land"] = w["open_land"] * (1 - min(cov / A["coverage_full"], 1))
        if low is not None:
            parts["lower_income_capacity"] = w["lower_income_capacity"] * min(low / A["capacity_full_units"], 1)
        parts["size"] = w["size"] * min(acres / A["size_full_acres"], 1)
        if transit:
            parts["transit"] = w["transit"]
        if sfha:
            parts["flood_sfha"] = w["flood_sfha"]
        if fire_vh:
            parts["fire_very_high"] = w["fire_very_high"]
        elif fire_other:
            parts["fire_other"] = w["fire_other"]
        if slide:
            parts["landslide"] = w["landslide"]
        promising = round(sum(parts.values()), 3)

        ws = A["weights_stale"]
        stale = None
        if newest is not None or cov is not None or apr_hit:
            stale = round(ws["apr_activity"] * apr_hit + ws["new_building"] * new_build +
                          ws["coverage"] * (min(cov / A["coverage_full"], 1) if cov is not None else 0), 3)

        c = shape.centroid
        out.append({
            "id": key, "apn": apn, "acres": round(acres, 2), "coverage": None if cov is None else round(cov, 3),
            "newest_year": newest, "new_build": new_build, "apr_hit": apr_hit,
            "lower": low, "moderate": num(a.get(f_mod)) if f_mod else None,
            "above": num(a.get(f_abv)) if f_abv else None,
            "zoning_local": z.get("ZN24_CITY"), "zoning_scag": z.get("ZN24_SCAG"), "slope": z.get("SLOPE"),
            "checks": checks, "promising": promising, "promising_parts": {k: round(v, 3) for k, v in parts.items()},
            "stale": stale, "lat": round(c.y, 6), "lon": round(c.x, 6), "polys": to_polys(shape, 0, 6),
        })

    pool = [s for s in out if not s["new_build"] and not s["apr_hit"]]
    for r, s in enumerate(sorted(pool, key=lambda s: -s["promising"])[:5], 1):
        s["promising_rank"] = r
    st = [s for s in out if s["stale"]]
    for r, s in enumerate(sorted(st, key=lambda s: (-s["stale"], -(s["coverage"] or 0)))[:5], 1):
        s["stale_rank"] = r
    if not any(s["new_build"] or s["apr_hit"] for s in out) and st:
        notes.append("No site has a recent building or APR permit activity; the 'stale' list is ranked on coverage only.")

    lat = sum(s["lat"] for s in out) / len(out)
    lon = sum(s["lon"] for s in out) / len(out)
    xs = [x for s in out for poly in s["polys"] for ring in poly for x, _ in ring]
    ys = [y for s in out for poly in s["polys"] for ring in poly for _, y in ring]
    bbox = (min(xs) - 0.01, min(ys) - 0.01, max(xs) + 0.01, max(ys) + 0.01)
    ov = overlays(layers, f_fld, f_fire, bbox)
    print(f"  {len(out)} sites scored; {sum(s['new_build'] for s in out)} with a recent building")
    notes_all[slug] = notes
    return {"name": city["name"], "center": [lat, lon], "notes": notes, "sites": out, "overlays": ov,
            "fields": {"apn": f_apn, "lower": f_low, "moderate": f_mod, "above": f_abv,
                       "parcel_year": p_year, "flood_zone": f_fld, "fire_class": f_fire}}


def main():
    meta = json.loads((CACHE / "meta.json").read_text()) if (CACHE / "meta.json").exists() else {}
    notes = {}
    apr_rows = load("apr_a2")
    apr_idx = None
    if apr_rows is not None:
        apr_idx, info = apr.index_by_apn(apr_rows)
        print(f"APR: {len(apr_rows)} rows, {len(apr_idx)} APNs. Columns used: {info}")
    cities = {slug: c for slug in CITIES if (c := build_city(slug, meta, notes, apr_idx))}
    if not cities:
        raise SystemExit("Nothing to build. Run fetch.py first.")
    sources = {k: {"label": SOURCES[k]["label"], "url": meta.get(k, {}).get("url") or
                   SOURCES[k].get("layer") or SOURCES[k].get("service"),
                   "fetched": meta.get(k, {}).get("fetched", "not fetched")} for k in SOURCES}
    payload = {"built": date.today().isoformat(), "test_data": bool(meta.get("synthetic")),
               "cities": cities, "sources": sources,
               "assumptions": ASSUMPTIONS}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload))
    here = pathlib.Path(__file__).parent
    page = here.joinpath("map_template.html").read_text()
    page = page.replace("/*__LEAFLET_CSS__*/", here.joinpath("findit", "leaflet.css").read_text())
    page = page.replace("/*__DATA__*/null", json.dumps(payload).replace("</", "<\\/"))
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(page)
    # The Artifact host adds its own document skeleton, so strip ours for that copy.
    body = page.split("<!--ARTIFACT-START-->", 1)[1].split("<!--ARTIFACT-END-->", 1)[0]
    OUT_ARTIFACT.write_text(body)
    mb = len(page.encode()) / 1e6
    print(f"\nWrote {OUT_HTML} ({mb:.1f} MB), {OUT_ARTIFACT} and {OUT_JSON}. Open {OUT_HTML} in a browser.")
    if mb > 15:
        print("! The page is over 15 MB; artifacts cap at 16 MB. Raise the simplify tolerance in overlays().")


if __name__ == "__main__":
    main()
