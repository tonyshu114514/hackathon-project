"""Every data source the tool touches, with where it came from.

URLs come from lanes/1-find-it/data/DATA-SOURCES.md in the event repo (checked 2026-11-06).
The date each layer was actually fetched is written to data/cache/meta.json by fetch.py.
"""

CITIES = {
    "irvine": {"name": "Irvine", "match": "IRVINE"},
    "santa-ana": {"name": "Santa Ana", "match": "SANTA ANA"},
    "costa-mesa": {"name": "Costa Mesa", "match": "COSTA MESA"},
}

SOURCES = {
    "he_sites": {
        "label": "SCAG Housing Element Sites (adopted 6th-cycle inventories)",
        "service": "https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementSite_poly_scag/MapServer",
    },
    "footprints": {
        "label": "OC Building Footprints",
        "layer": "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Building_Footprints/MapServer/0",
    },
    "parcels": {
        "label": "OC Survey Parcels (year built)",
        "layer": "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/FeatureServer/0",
    },
    "zoning": {
        "label": "SCAG Zoning_poly_OR (local zoning, acres, slope)",
        "service": "https://maps.scag.ca.gov/scaggis/rest/services/LDX/Zoning_poly_OR/MapServer",
    },
    "flood": {
        "label": "OC Floodplains (FEMA flood zones, county copy)",
        "layer": "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Floodplains/MapServer/0",
    },
    "fire_lra": {
        "label": "OC Fire Hazard Severity Zones, LRA (county copy)",
        "layer": "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Fire_Hazard_Severity_Zones_LRA/MapServer/0",
    },
    "fire_sra": {
        "label": "CAL FIRE Fire Hazard Severity Zones, SRA (statewide, older vintage)",
        "service": "https://services.gis.ca.gov/arcgis/rest/services/Environment/Fire_Severity_Zones/MapServer",
        "layer_name_contains": "SRA",
    },
    "landslide": {
        "label": "CGS Landslide Zones (zones of required investigation)",
        "layer": "https://services2.arcgis.com/zr3KAIbsRSUyARHG/arcgis/rest/services/CGS_Landslide_Zones/FeatureServer/0",
    },
    "hqta": {
        "label": "Caltrans High Quality Transit Areas",
        "layer": "https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHrailroad/CA_HQ_Transit_Areas/FeatureServer/0",
    },
    "apr_a2": {
        "label": "HCD Housing Element Annual Progress Report, Table A2 (entitlements, permits, completions)",
        "ckan": "fe505d9b-8c36-42ba-ba30-08bc4f34e022",
        "page": "https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year",
    },
    "rhna": {
        "label": "HCD 6th Cycle RHNA Progress Report",
        "ckan": "1e80a9cf-724c-432d-8374-e9708a6a92dc",
        "page": "https://data.ca.gov/dataset/rhna-progress-report",
    },
    "opportunity": {
        "label": "CTCAC/HCD 2025 Opportunity Area Map (statewide copy republished by CA Coastal Commission)",
        "layer": "https://services9.arcgis.com/wwVnNW92ZHUIr0V0/arcgis/rest/services/Opportunity_and_Neighborhood_Change__CTCAC_HCD__2026_/FeatureServer/2",
    },
    "ces": {
        "label": "OEHHA CalEnviroScreen 5.0 (final, census tract)",
        "layer": "https://services1.arcgis.com/PCHfdHz4GlDNAhBb/arcgis/rest/services/calenviroscreen50results_F_070126_gdb/FeatureServer/2",
    },
    "qct": {
        "label": "HUD 2026 Qualified Census Tracts (LIHTC basis boost)",
        "layer": "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/QUALIFIED_CENSUS_TRACTS_2026/FeatureServer/0",
    },
    "dda": {
        "label": "HUD 2026 Difficult Development Areas (LIHTC basis boost)",
        "layer": "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/Difficult_Development_Areas_2026/FeatureServer/0",
    },
    "envirostor": {
        "label": "DTSC EnviroStor cleanup sites",
        "layer": "https://services3.arcgis.com/Oy2JTCD10wkoelxS/arcgis/rest/services/Envirostor_Public_Data_Export/FeatureServer/0",
    },
    "lihtc": {
        "label": "HUD LIHTC properties (existing tax-credit affordable housing)",
        "layer": "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/LIHTC/FeatureServer/0",
    },
    "places": {
        "label": "OpenStreetMap place names (Nominatim reverse geocoding), used only when a site has no assessor address",
        "page": "https://nominatim.openstreetmap.org/",
    },
}

# Tract-level and nearby-point layers, fetched over a wider box than the hazard layers.
AREA_LAYERS = ("opportunity", "ces", "qct", "dda", "envirostor", "lihtc")

# If build.py picks the wrong column, put the exact column name here and re-run build.py.
FIELD_OVERRIDES = {
    "site_apn": None,
    "site_lower_cap": None,
    "site_mod_cap": None,
    "site_above_cap": None,
    "parcel_apn": None,
    "parcel_year": None,
    "fire_class": None,
    "flood_zone": None,
}

# ASSUMPTION values. Every one is shown on the map page under "Assumptions".
ASSUMPTIONS = {
    "stale_year_cutoff": {
        "value": 2021,
        "why": "SCAG region's 6th-cycle housing element planning period starts Oct 2021. A building with year built >= 2021 on a listed site suggests it was built after the inventory was prepared. Check each city's actual adoption date.",
    },
    "coverage_full": {
        "value": 0.6,
        "why": "Building footprint covering 60%+ of the site is treated as fully built-out for scoring.",
    },
    "hazard_min_overlap": {
        "value": 0.01,
        "why": "A hazard zone counts when it covers at least 1% of the site, so mapping slivers do not flag a whole parcel.",
    },
    "weights_promising": {
        "value": {"open_land": 0.35, "lower_income_capacity": 0.25, "size": 0.20, "transit": 0.20,
                  "high_opportunity": 0.15, "tax_credit_boost": 0.05,
                  "flood_sfha": -0.5, "fire_very_high": -0.5, "fire_other": -0.15, "landslide": -0.25,
                  "cleanup_on_site": -0.4, "cleanup_nearby": -0.1, "pollution_burden": -0.1},
        "why": "Team judgment for a first-pass screen. Not a legal eligibility test and not a prediction.",
    },
    "apr_min_units": {
        "value": 5,
        "why": "5+ units permitted or completed on a listed APN (APR Table A2) marks the site as used; fewer (often an ADU) is a caution. Entitled-only sites are left out of 'check first' because a project is already moving.",
    },
    "cleanup_near_feet": {
        "value": 660,
        "why": "An EnviroStor cleanup site within 1/8 mile (660 ft) of the site edge is flagged for a Phase I review.",
    },
    "lihtc_radius_feet": {
        "value": 2640,
        "why": "Existing LIHTC properties within 1/2 mile are counted to show where subsidized housing already clusters.",
    },
    "ces_burden_pctl": {
        "value": 75,
        "why": "CalEnviroScreen percentile 75+ is the state's usual cutoff for a disadvantaged community (SB 535).",
    },
    "size_full_acres": {"value": 3.0, "why": "Sites of 3+ acres get full size credit."},
    "capacity_full_units": {"value": 100, "why": "100+ lower-income units of capacity get full capacity credit."},
    "weights_stale": {
        "value": {"new_building": 0.45, "apr_activity": 0.35, "coverage": 0.2},
        "why": "A recent building or a permit/completion the city reported to HCD is the strong signal; coverage alone is weak because many listed sites are intentionally non-vacant.",
    },
}
