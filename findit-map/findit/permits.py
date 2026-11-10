"""Grade the HCD Annual Progress Report activity matched to a site.

Before this module, any APR row from the cutoff year on marked a site "likely already used", including a
single ADU permit on a large lot. Now each site's rows are graded:

  strong    a building permit was issued or a certificate of occupancy recorded for a non-ADU project
  moderate  a project was entitled (approved) but no permit or completion is reported yet
  weak      only accessory dwelling units (or similar add-ons) were reported: the lot is still mostly available
  none      no row matched

"strong" and "moderate" mark the site likely used; "weak" only adds a caution. The grade thresholds and the
ADU rule are ASSUMPTIONS listed in findit/sources.py and shown on the page. Cities type APNs by hand, so a
miss is never proof of no activity.
"""
import re

# HCD Table A2 unit categories (UNIT_CAT): SFA/SFD single-family attached/detached, 2 to 4, 5+, ADU, MH mobile home.
ADD_ON_CATEGORIES = {"ADU", "JADU"}
STAGE_ORDER = ["completed", "permit issued", "entitled"]
INCOME_COLS = re.compile(r"^(BP_|CO_)?(ACUTELY_LOW|EXTREMELY_LOW|VLOW|LOW|MOD|ABOVE_MOD)_INCOME(_DR|_NDR)?$", re.I)


def _num(v):
    try:
        x = float(str(v).replace(",", ""))
        return x if x == x else 0.0
    except (TypeError, ValueError):
        return 0.0


def row_units(row):
    """Units by stage from one Table A2 row: {'entitled': n, 'permitted': n, 'completed': n}."""
    out = {"entitled": 0.0, "permitted": 0.0, "completed": 0.0}
    for k, v in row.items():
        m = INCOME_COLS.match(str(k))
        if not m:
            continue
        stage = {"BP_": "permitted", "CO_": "completed", None: "entitled"}[m.group(1).upper() if m.group(1) else None]
        out[stage] += _num(v)
    return {k: int(v) for k, v in out.items()}


def grade(acts):
    """Grade a site's matched APR entries (as built by apr.index_by_apn, with unit_cat and units).

    Returns a dict the page can show:
      level       strong | moderate | weak | none
      likely_used True for strong and moderate
      stage       best stage reached across the rows (completed > permit issued > entitled > reported)
      units       units at that best stage, summed over rows that reached it
      categories  sorted unit categories seen (e.g. ['5+', 'ADU'])
      years       sorted report years
      projects    distinct project names, if any
    """
    if not acts:
        return {"level": "none", "likely_used": False, "stage": None, "units": 0, "categories": [], "years": [],
                "projects": [], "adu_only": False}
    cats = sorted({str(a.get("unit_cat") or "").strip().upper() for a in acts if str(a.get("unit_cat") or "").strip()})
    years = sorted({a["year"] for a in acts if a.get("year")})
    projects = sorted({str(a.get("project") or "").strip() for a in acts if str(a.get("project") or "").strip()})
    main_acts = [a for a in acts if str(a.get("unit_cat") or "").strip().upper() not in ADD_ON_CATEGORIES]
    adu_only = bool(cats) and not main_acts
    pool = main_acts or acts
    stage = next((st for st in STAGE_ORDER if any(st in (a.get("stages") or []) for a in pool)), "reported")
    ukey = {"completed": "completed", "permit issued": "permitted", "entitled": "entitled"}.get(stage)
    units = sum(int((a.get("units") or {}).get(ukey) or 0) for a in pool if ukey and stage in (a.get("stages") or []))
    if adu_only:
        level = "weak"
    elif stage in ("completed", "permit issued"):
        level = "strong"
    elif stage == "entitled":
        level = "moderate"
    else:
        level = "moderate"  # a row with no stage date is still a city-reported project on this APN
    return {"level": level, "likely_used": level in ("strong", "moderate"), "stage": stage, "units": units,
            "categories": cats, "years": years, "projects": projects, "adu_only": adu_only}


def describe(g, min_year):
    """One sentence for the 'Permit activity (APR)' check."""
    if g["level"] == "none":
        return (f"No APR row from {min_year} on matched this APN. Cities type APNs by hand, "
                "so a miss is not proof of no activity.")
    yrs = ", ".join(map(str, g["years"])) or "an APR year"
    cats = ", ".join(g["categories"]) if g["categories"] else "units"
    units = f"{g['units']} unit{'s' if g['units'] != 1 else ''}" if g["units"] else "unit count not reported"
    proj = f" Project: {g['projects'][0]}." if g["projects"] else ""
    if g["level"] == "weak":
        return (f"Only accessory dwelling units were reported on this APN in {yrs} ({units}). "
                f"An ADU permit does not take the whole site, so it is not marked likely used (ASSUMPTION).{proj}")
    stage = {"completed": "completed (certificate of occupancy)", "permit issued": "building permit issued",
             "entitled": "entitled (approved, no permit reported yet)", "reported": "reported without a stage date"}[g["stage"]]
    strength = "strong" if g["level"] == "strong" else "moderate"
    return (f"City reported a project on this APN in {yrs}: {stage}, {cats}, {units}. "
            f"{strength.title()} sign the site is already in use.{proj}")
