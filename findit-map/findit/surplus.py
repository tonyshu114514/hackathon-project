"""HCD Surplus Land Act Notices of Availability: public agencies' surplus parcels offered for housing first.

Source: https://data.ca.gov/dataset/surplus-land-act-notices-of-availability-received (CSV, statewide).
Each row is one parcel in a notice: agency, APN, address, city, lon/lat, parcel size, general plan / zoning,
existing use and the notice's status. Nearly every row is "Archive": the 60-day notice window has passed. The
land may still be public and still surplus, so an archived notice is a lead to call the agency about, not a
listing. The contact column (named staff) is dropped: the page shows the agency and the notice link only.

Rows become pseudo housing-element sites so the same validation, checks and scoring apply. Parcel outlines
come from the county parcel layer by APN; when no parcel matches, a circle of the listed acreage (or a small
default) is drawn at the notice's coordinates and marked approximate (ASSUMPTION).
"""
import csv
import io
import math
import re

SQFT_PER_ACRE = 43560.0
PAGE = "https://data.ca.gov/dataset/surplus-land-act-notices-of-availability-received"
PACKAGE = "surplus-land-act-notices-of-availability-received"
KEEP = ("Parent Case", "Local Agency Type", "Local Agency", "APN", "Date Notice Issued", "NOA Due Date", "NOA Status",
        "Notice Website Link", "Consolidated Sites", "Address", "City", "Zip", "x", "y", "Parcel Size (Gross Acres)",
        "General Plan/Zoning", "Existing Use/Vacancy")


def parse_acres(text):
    """'9,005 SF' -> 0.2067; '0.26' -> 0.26; '' -> None. Anything that is not a number is None."""
    t = str(text or "").strip().replace(",", "")
    if not t:
        return None
    m = re.match(r"^([0-9]*\.?[0-9]+)\s*(sf|sq\.?\s*ft\.?|square feet|ac|acres?)?\s*$", t, re.I)
    if not m:
        return None
    v, unit = float(m.group(1)), (m.group(2) or "").lower()
    if unit.startswith("s"):
        return round(v / SQFT_PER_ACRE, 4)
    return round(v, 4)


def read_rows(text):
    """Rows of the statewide CSV with the staff-contact column removed."""
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        out.append({k: (r.get(k) or "").strip() for k in KEEP})
    return out


def rows_for_city(rows, city_match):
    """Rows whose City equals the city (case-insensitive). 'Orange' never matches 'Orange Cove' and so on."""
    want = city_match.strip().upper()
    return [r for r in rows if r["City"].strip().upper() == want]


def circle_rings(lon, lat, acres, default_radius_ft=60.0, n=24):
    """Approximate outline: a circle of the listed acreage (or a default radius) around the notice point."""
    area_ft = (acres or 0) * SQFT_PER_ACRE
    r_ft = math.sqrt(area_ft / math.pi) if area_ft > 0 else default_radius_ft
    r_deg_lat = r_ft / 364000.0  # feet per degree of latitude, roughly, at this latitude
    r_deg_lon = r_deg_lat / math.cos(math.radians(lat))
    ring = [[lon + r_deg_lon * math.cos(2 * math.pi * i / n), lat + r_deg_lat * math.sin(2 * math.pi * i / n)] for i in range(n)]
    ring.append(ring[0])
    return [ring]


def to_site(row, geometry=None):
    """A pseudo housing-element feature (SCAG field names) for one notice row.

    geometry: ArcGIS rings from the parcel layer, or None to draw an approximate circle.
    """
    apn = row["APN"] if row["APN"].upper() not in ("", "N/A", "NA", "NONE", "PENDING") else None
    acres = parse_acres(row["Parcel Size (Gross Acres)"])
    try:
        lon, lat = float(row["x"]), float(row["y"])
    except ValueError:
        lon = lat = None
    approx = geometry is None
    if approx:
        if lon is None or lat is None:
            return None
        geometry = {"rings": circle_rings(lon, lat, acres)}
    status = row["NOA Status"] or "unknown status"
    attrs = {
        "OBJECTID": f"sla-{row['Parent Case']}-{re.sub(r'[^0-9A-Za-z]', '', apn or row['Address'] or 'x')}",
        "Jurisdiction": row["City"], "COUNTY": "Orange",
        "Assessor_Parcel_Number": apn,
        "Low_Income_HE_Capacity": None, "Moderate_Income_HE_Capacity": None,
        "Above_Moderate_Income_HE_Capacity": None, "Total_HE_Capacity": None,
        "HE_Address": row["Address"] or None, "HE_Existing_Use": row["Existing Use/Vacancy"] or None,
        "HE_Status": f"Surplus Land Act notice ({status})",
        "HE_Publicly_Owned": f"YES - {row['Local Agency']}" if row["Local Agency"] else "YES",
        "HE_Zoning": row["General Plan/Zoning"] or None, "HE_Max_Density": None,
        "HE_Acres": acres, "HE_Prior_Cycles": None,
        "SLA_CASE": row["Parent Case"], "SLA_AGENCY": row["Local Agency"], "SLA_AGENCY_TYPE": row["Local Agency Type"],
        "SLA_NOTICE_DATE": row["Date Notice Issued"], "SLA_DUE_DATE": row["NOA Due Date"], "SLA_STATUS": status,
        "SLA_LINK": row["Notice Website Link"] or None, "SLA_CONSOLIDATED": row["Consolidated Sites"],
        "SLA_APPROX_OUTLINE": approx,
    }
    return {"attributes": attrs, "geometry": geometry}
