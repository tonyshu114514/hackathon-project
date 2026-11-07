"""HCD Housing Element Annual Progress Report (APR), Table A2: housing development activity by APN.

Source: https://data.ca.gov/@california-department-of-housing-and-community-development/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year
Cities type APNs in by hand, so a row can hold several APNs or odd formatting. Matching is
by digits only, and a miss means "not found", never "no activity".
"""
import csv
import io
import json
import re

import requests

API = "https://data.ca.gov/api/3/action/"
PACKAGE = "housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year"
PAGE = "https://data.ca.gov/dataset/" + PACKAGE
UA = {"User-Agent": "findit-hackathon-prototype (UCI Claude Impact Lab)"}
# Set to a resource id if the automatic pick below chooses the wrong file.
RESOURCE_ID = None


def _ckan(action, **params):
    r = requests.get(API + action, params=params, headers=UA, timeout=120)
    r.raise_for_status()
    j = r.json()
    if not j.get("success"):
        raise RuntimeError(j.get("error"))
    return j["result"]


def pick_resource():
    pkg = _ckan("package_show", id=PACKAGE)
    res = pkg.get("resources", [])
    print("  APR resources: " + "; ".join(f"{r.get('name')} [{r.get('format')}]" for r in res))
    if RESOURCE_ID:
        return next(r for r in res if r["id"] == RESOURCE_ID)
    a2 = [r for r in res if re.search(r"\ba2\b|table\s*a2", (r.get("name") or "").lower())]
    a2.sort(key=lambda r: (r.get("format", "").upper() != "CSV"))
    if not a2:
        raise RuntimeError("No 'Table A2' resource found. Set RESOURCE_ID in findit/apr.py.")
    return a2[0]


def fetch_rows(city_names):
    """Rows of Table A2 for the given cities (upper-case names). Tries the API, then streams the CSV."""
    res = pick_resource()
    print(f"  using APR resource: {res.get('name')} ({res['id']})")
    want = {c.upper() for c in city_names}
    rows = []
    if res.get("datastore_active"):
        sample = _ckan("datastore_search", resource_id=res["id"], limit=1)
        fields = [f["id"] for f in sample["fields"]]
        jf = next((f for f in fields if "juris" in f.lower()), None)
        if jf:
            for city in want:
                for val in (city, city.title()):
                    off, got = 0, []
                    while True:
                        page = _ckan("datastore_search", resource_id=res["id"], limit=5000, offset=off,
                                     filters=json.dumps({jf: val}))
                        got += page["records"]
                        off += 5000
                        if len(page["records"]) < 5000:
                            break
                    if got:
                        rows += got
                        break
            if rows:
                return res, rows
    # Fallback: stream the whole CSV and keep only our cities.
    print("  streaming the full APR CSV (statewide; this can take a few minutes)")
    with requests.get(res["url"], headers=UA, stream=True, timeout=600) as r:
        r.raise_for_status()
        lines = io.TextIOWrapper(r.raw, encoding="utf-8-sig", errors="replace")
        reader = csv.DictReader(lines)
        jf = next((f for f in reader.fieldnames if "juris" in f.lower()), None)
        if not jf:
            raise RuntimeError(f"No jurisdiction column in APR CSV: {reader.fieldnames[:15]}")
        for row in reader:
            if (row.get(jf) or "").strip().upper() in want:
                rows.append(row)
    return res, rows


def index_by_apn(rows):
    """{8-digit APN: [ {year, stages:[...]} ]} from Table A2 rows."""
    if not rows:
        return {}, {}
    keys = list(rows[0].keys())
    f_apn = next((k for k in keys if "apn" in k.lower()), None)
    f_year = next((k for k in keys if k.lower() in ("year", "rpt_year", "report_year")), None) or \
        next((k for k in keys if "year" in k.lower()), None)
    stage_cols = {
        "entitled": [k for k in keys if re.search(r"ent", k, re.I) and re.search(r"dt|date", k, re.I)],
        "permit issued": [k for k in keys if re.search(r"(^|_)bp", k, re.I) and re.search(r"dt|date", k, re.I)],
        "completed": [k for k in keys if re.search(r"(^|_)co(_|\d)", k, re.I) and re.search(r"dt|date", k, re.I)],
    }
    out = {}
    for r in rows:
        raw = str(r.get(f_apn) or "") if f_apn else ""
        y = None
        try:
            y = int(float(str(r.get(f_year)))) if f_year else None
        except (TypeError, ValueError):
            pass
        stages = [s for s, cols in stage_cols.items() if any(str(r.get(c) or "").strip() for c in cols)]
        for part in re.split(r"[,;/&]|\band\b|\s{2,}", raw):
            d = re.sub(r"\D", "", part)
            if len(d) >= 8:
                out.setdefault(d[:8], []).append({"year": y, "stages": stages})
    info = {"apn_field": f_apn, "year_field": f_year,
            "stage_columns": {k: v for k, v in stage_cols.items() if v}}
    return out, info
