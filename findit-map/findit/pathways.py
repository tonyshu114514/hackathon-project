"""Preliminary screening of four California housing laws for one site.

Each law gets a list of tests, each test pass / fail / unknown with a sentence saying why, and an overall result:

  no        at least one test the data could check failed
  unknown   nothing failed, but at least one required fact is not in any dataset we have
  passes    every test we could check passed and nothing required is unknown (never reached in practice: every
            law has facts no public dataset holds, so the page says "unknown, N of M signals pass")

The tests are screening signals taken from HCD's Housing Law Fact Sheets (April 2026), not the statutes' full
legal tests. Nothing here is legal advice. The sources and the date they were checked are returned with every
result so the page can show them. Facts that no free dataset holds (historic status, tenancy, ownership by a
religious institution, street width, adjacent industrial uses, wetlands, fault zones...) stay "unknown"; the
tool never assumes eligibility when a required fact is missing.
"""

CHECKED = "2026-11-09"
FACT_SHEETS = "https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/housing-law-fact-sheets.pdf"
SRC = {
    "sb9": [{"label": "HCD fact sheet: Duplexes and Lot Splits (SB 9), Gov. Code §§ 65852.21, 66411.7",
             "url": "https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/lot-splits-and-duplexes-sb-9.pdf"},
            {"label": "HCD SB 9 implementation fact sheet",
             "url": "https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/sb-9-fact-sheet.pdf"}],
    "sb684": [{"label": "HCD fact sheet: Starter Home Revitalization Act (SB 684 / SB 1123), Gov. Code §§ 65852.28, 65913.4.5, 66499.41",
               "url": FACT_SHEETS}],
    "ab2011": [{"label": "HCD fact sheet: Affordable Housing and High Road Jobs Act (AB 2011), Gov. Code §§ 65912.100-65912.140",
                "url": FACT_SHEETS},
               {"label": "Gov. Code § 65912.101 (leginfo)",
                "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=GOV&sectionNum=65912.101"}],
    "sb4": [{"label": "HCD fact sheet: Affordable Housing on Faith and Higher Education Lands Act (SB 4), Gov. Code § 65913.16",
             "url": "https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/aff-hsg-faith-higher-ed-sb-4.pdf"}],
}

# SCAG land use / zoning code families. Source: SCAG "2012 SCAG General Plan Land Use Codes - Legend"
# (https://maps.scag.ca.gov/2012LandUseCodesLegend.pdf, checked 2026-11-09). The 2024 zoning layer's ZN24_SCAG field
# carries finer four-digit codes (1223, 1122, ...); they are matched to the legend by their first three digits and
# labelled with the family name, because the sub-code names were not verified.
SCAG_CODES = {
    "1110": ("single_family", "Single Family Residential"),
    "1120": ("multi_family", "Multi-Family Residential"),
    "1130": ("mobile_home", "Mobile Homes and Trailer Parks"),
    "1140": ("mixed_residential", "Mixed Residential"),
    "1150": ("rural_residential", "Rural Residential"),
    "1100": ("residential", "Residential"),
    "1200": ("commercial", "General Commercial"),
    "1210": ("commercial", "General Office"),
    "1220": ("commercial", "Retail and Commercial and Services"),
    "1221": ("commercial", "Regional Shopping Center"),
    "1230": ("commercial", "Other Commercial"),
    "1233": ("commercial", "Hotels and Motels"),
    "1240": ("facilities", "Public Facilities"),
    "1250": ("facilities", "Special Use Facilities"),
    "1260": ("education", "Education, K-12"),
    "1265": ("education", "Education, College"),
    "1270": ("military", "Military Installations"),
    "1300": ("industrial", "General Industrial"),
    "1310": ("industrial", "Light Industrial"),
    "1311": ("industrial", "Light Manufacturing, Assembly, and Industrial Services"),
    "1320": ("industrial", "Heavy Industrial"),
    "1321": ("industrial", "Heavy Manufacturing"),
    "1340": ("industrial", "Wholesaling and Warehousing"),
    "1410": ("transport_utilities", "Transportation"),
    "1420": ("transport_utilities", "Communication Facilities"),
    "1430": ("transport_utilities", "Utility Facilities"),
    "1500": ("mixed_com_ind", "Mixed Commercial and Industrial"),
    "1600": ("mixed_res_com", "Mixed Residential and Commercial"),
    "1810": ("open_space", "Golf Courses"),
    "1820": ("open_space", "Local Parks and Recreation"),
    "1830": ("open_space", "State and National Parks and Recreation"),
    "1840": ("open_space", "Cemeteries"),
    "1850": ("open_space", "Wildlife Preserves and Sanctuaries"),
    "1860": ("open_space", "Specimen Gardens and Arboreta"),
    "1870": ("open_space", "Beach Parks"),
    "1880": ("open_space", "Other Open Space and Recreation"),
    "1900": ("vacant", "Urban Vacant"),
    "3000": ("vacant", "Vacant"),
    "2000": ("agriculture", "Agriculture"),
    "4000": ("water", "Water"),
    "7777": ("specific_plan", "Specific Plan"),
    "8888": ("undevelopable", "Undevelopable or Protected Land"),
    "9999": ("unknown", "Unknown"),
}
RESIDENTIAL = {"single_family", "multi_family", "mobile_home", "mixed_residential", "rural_residential", "residential"}
ALLOWS_HOUSING = RESIDENTIAL | {"mixed_res_com"}


def zoning_family(code):
    """(family, label, exact) for a SCAG zoning code, or (None, None, False) when blank."""
    c = str(code or "").strip()
    if not c:
        return None, None, False
    if c in SCAG_CODES:
        fam, label = SCAG_CODES[c]
        return fam, label, True
    for n in (3, 2):
        for k, (fam, label) in SCAG_CODES.items():
            if k[:n] == c[:n] and k.endswith("0" * (4 - n)):
                return fam, f"{label} family", False
    return "unknown", f"SCAG code {c} (not in the legend)", False


def _t(name, status, detail, assumption=False):
    t = {"name": name, "status": status, "detail": detail}
    if assumption:
        t["assumption"] = True
    return t


def _tri(flag, name, fail_msg, pass_msg, unknown_msg):
    if flag is None:
        return _t(name, "unknown", unknown_msg)
    return _t(name, "fail" if flag else "pass", fail_msg if flag else pass_msg)


def hazard_tests(site):
    """The shared exclusions from Gov. Code § 65913.4(a)(6), as far as the layers allow."""
    return [
        _tri(site.get("fire_vh"), "Very high fire hazard severity zone",
             "Site is in a Very High Fire Hazard Severity Zone (excluded unless the statute's mitigation exceptions apply).",
             "Not in a Very High Fire Hazard Severity Zone (county LRA and CAL FIRE SRA layers).",
             "Fire hazard layers did not load."),
        _tri(site.get("sfha"), "FEMA special flood hazard area",
             "Site is in a FEMA Special Flood Hazard Area (excluded unless FEMA-compliant exceptions in the statute apply).",
             "Not in a FEMA Special Flood Hazard Area (county floodplain layer).",
             "Flood layer did not load."),
        _tri(site.get("cleanup_on_site"), "Hazardous waste site",
             "A DTSC EnviroStor cleanup site lies on the parcel (excluded unless cleared for residential use).",
             "No DTSC EnviroStor cleanup site on the parcel. The statute uses the broader Cortese list, which was not checked.",
             "EnviroStor layer did not load."),
        _t("Other protected lands", "unknown",
           "Wetlands, prime farmland, earthquake fault zones, regulatory floodways, conservation plan lands, protected-species "
           "habitat and conservation easements (§ 65913.4(a)(6)) are not in the layers loaded."),
    ]


def urban_test():
    return _t("Urbanized area", "pass",
              "Orange County's incorporated cities are treated as inside a Census urbanized area (ASSUMPTION; confirm on the "
              "Census urban area map for unincorporated sites).", assumption=True)


def activity_test(site):
    if site.get("likely_used"):
        return _t("Site activity", "fail", "The city already reported permit activity or a new building on this APN, so the site "
                                           "is probably spoken for whatever the law allows.")
    if site.get("pending"):
        return _t("Site activity", "fail", "The city lists a pending project on this site.")
    return None


def _result(tests):
    statuses = [t["status"] for t in tests]
    if "fail" in statuses:
        res = "no"
    elif "unknown" in statuses:
        res = "unknown"
    else:
        res = "passes"
    return res, statuses.count("pass"), statuses.count("unknown"), statuses.count("fail")


def _pack(id_, law, opens, tests, note=None):
    res, p, u, f = _result(tests)
    return {"id": id_, "law": law, "opens": opens, "result": res, "passes": p, "unknowns": u, "fails": f,
            "tests": tests, "sources": [dict(s, checked=CHECKED) for s in SRC[id_]], "note": note}


def sb9(site):
    fam = site.get("zoning_family")
    if fam is None or fam in ("unknown", "specific_plan"):
        z = _t("Single-family residential zone", "unknown",
               "Zoning family unknown" + (" (specific plan area: read the plan's zoning)." if fam == "specific_plan" else
                                          " (no SCAG zoning code matched this parcel)."))
    elif fam == "single_family":
        z = _t("Single-family residential zone", "pass", f"SCAG zoning: {site.get('zoning_label')}.")
    else:
        z = _t("Single-family residential zone", "fail",
               f"SB 9 applies in single-family residential zones; SCAG zoning here is {site.get('zoning_label')}.")
    tests = [z, urban_test()] + hazard_tests(site) + [
        _t("Historic district or resource", "unknown", "No historic-resource layer loaded; excluded if the parcel is a contributing structure."),
        _t("Tenant and rent-restriction history", "unknown",
           "Housing occupied by a tenant in the last 3 years, rent-restricted units or an Ellis Act withdrawal in 15 years are excluded; not in public parcel data."),
    ]
    act = activity_test(site)
    if act:
        tests.append(act)
    return _pack("sb9", "SB 9", "Up to two primary units, or a lot split, on a single-family lot by right", tests,
                 "Aimed at owners of single-family lots. The owner of a split lot must sign an intent to live there for three "
                 "years unless the applicant is a community land trust or nonprofit.")


def sb684(site):
    acres = site.get("acres")
    size = (_t("Lot under 5 acres", "unknown", "Lot size unknown.") if acres is None else
            _t("Lot under 5 acres", "pass" if acres < 5 else "fail", f"Site measures {acres:.2f} acres."))
    fam, vacant = site.get("zoning_family"), site.get("vacant")
    if fam in ("multi_family", "mixed_residential", "mixed_res_com", "residential"):
        z = _t("Zoned for multifamily residential use", "pass", f"SCAG zoning: {site.get('zoning_label')}.")
    elif fam == "single_family":
        if vacant is True:
            z = _t("Zoned for multifamily residential use", "pass",
                   "Single-family zone, but the lot appears vacant: SB 1123 (effective July 1, 2025) extends the process to vacant "
                   "single-family lots.")
        elif vacant is False:
            z = _t("Zoned for multifamily residential use", "fail",
                   "Single-family zone and the lot is built on; SB 1123 covers only vacant single-family lots.")
        else:
            z = _t("Zoned for multifamily residential use", "unknown",
                   "Single-family zone: SB 1123 applies only if the lot is vacant, and vacancy is unknown here.")
    elif fam is None or fam in ("unknown", "specific_plan"):
        z = _t("Zoned for multifamily residential use", "unknown", "Zoning family unknown for this parcel.")
    else:
        z = _t("Zoned for multifamily residential use", "fail",
               f"SCAG zoning here is {site.get('zoning_label')}, not a residential zone.")
    tests = [size, z, urban_test()] + hazard_tests(site) + [
        _t("No displacement of protected housing", "unknown",
           "Rent-controlled or tenant-occupied housing on the site would make it ineligible; tenancy is not in public parcel data."),
    ]
    act = activity_test(site)
    if act:
        tests.append(act)
    return _pack("sb684", "SB 684 / SB 1123", "Up to 10 homes on an urban lot under 5 acres, approved ministerially", tests)


def ab2011(site):
    fam = site.get("zoning_family")
    if fam in ("commercial", "mixed_res_com", "mixed_com_ind"):
        z = _t("Zone allows office, retail or parking", "pass", f"SCAG zoning: {site.get('zoning_label')}.")
    elif fam in RESIDENTIAL:
        z = _t("Zone allows office, retail or parking", "fail",
               f"SCAG zoning here is {site.get('zoning_label')}; AB 2011 is for commercially zoned sites.")
    elif fam is None or fam in ("unknown", "specific_plan", "industrial", "facilities", "education", "vacant",
                                "open_space", "transport_utilities", "agriculture", "undevelopable", "military", "water"):
        z = _t("Zone allows office, retail or parking", "unknown",
               f"SCAG zoning here is {site.get('zoning_label') or 'unknown'}; whether the zone allows office, retail or parking "
               "as a principal use has to be read from the city's zoning code.")
    else:
        z = _t("Zone allows office, retail or parking", "unknown", "Zoning family unknown for this parcel.")
    tests = [z] + hazard_tests(site) + [
        _t("Commercial corridor frontage", "unknown",
           "The statute's street-width and frontage rules for the mixed-income pathway need a right-of-way measurement that is not loaded."),
        _t("Not adjacent to industrial uses", "unknown", "Adjacent and nearby industrial uses were not checked."),
        _t("Affordability and labor standards", "unknown",
           "Project-level: 100% affordable or mixed-income set-asides, prevailing wage, and for 50+ units apprenticeship and health care."),
    ]
    act = activity_test(site)
    if act:
        tests.append(act)
    return _pack("ab2011", "AB 2011", "By-right multifamily housing on commercially zoned sites", tests)


def sb4(site):
    owned = site.get("publicly_owned")
    if owned is True:
        o = _t("Owned by a religious institution or independent college", "fail",
               "The site is publicly owned; SB 4 needs land owned by a religious institution or an independent institution of "
               "higher education as of January 1, 2024.")
    else:
        o = _t("Owned by a religious institution or independent college", "unknown",
               "No free dataset records religious or college ownership. The assessor roll or a title search would confirm it.")
    tests = [o, _t("Allowed in any zone", "pass", "SB 4 developments are permitted in all zones, including single-family and non-residential zones."),
             urban_test()] + hazard_tests(site) + [
        _t("75% of the perimeter adjoins urban uses", "unknown", "Perimeter land uses were not checked."),
        _t("Not adjacent to industrial uses", "unknown", "Light and heavy industrial neighbors, Title V facilities and refineries were not checked."),
        _t("100% affordable project", "unknown", "Project-level: all units (except managers') for lower-income households, with the allowed moderate-income share."),
    ]
    act = activity_test(site)
    if act:
        tests.append(act)
    return _pack("sb4", "SB 4", "100% affordable housing by right on faith and nonprofit-college land", tests)


def screen(site):
    """All four laws for one site. `site` holds: zoning_code, acres, fire_vh, sfha, cleanup_on_site, vacant,
    publicly_owned, likely_used, pending (None where unknown)."""
    fam, label, exact = zoning_family(site.get("zoning_code"))
    s = dict(site, zoning_family=fam, zoning_label=label)
    return [sb9(s), sb684(s), ab2011(s), sb4(s)]
