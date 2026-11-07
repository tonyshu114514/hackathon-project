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
}

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
                  "flood_sfha": -0.5, "fire_very_high": -0.5, "fire_other": -0.15, "landslide": -0.25},
        "why": "Team judgment for a first-pass screen. Not a legal eligibility test and not a prediction.",
    },
    "size_full_acres": {"value": 3.0, "why": "Sites of 3+ acres get full size credit."},
    "capacity_full_units": {"value": 100, "why": "100+ lower-income units of capacity get full capacity credit."},
    "weights_stale": {
        "value": {"new_building": 0.7, "coverage": 0.3},
        "why": "A recent building is the strong signal; coverage alone is weak because many listed sites are intentionally non-vacant.",
    },
}
