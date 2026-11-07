"""Every data source the tool touches, with where it came from.

URLs come from lanes/1-find-it/data/DATA-SOURCES.md in the event repo (checked 2026-11-06).
The date each layer was actually fetched is written to data/cache/meta.json by fetch.py.
"""

# sites: which inventory layer lists the city's housing-element sites. SCAG has no Santa Ana or
# Costa Mesa records, so those cities use HCD's statewide Table A inventory (SB 6 submissions).
# Irvine stays on SCAG so its rankings match earlier runs; HCD lists 117 Irvine sites to SCAG's 44.
# Every other Orange County jurisdiction with a Table A submission is included (checked 2026-11-07).
# Not in either source: Huntington Beach, Tustin, Orange, Laguna Woods, Rancho Santa Margarita.
CITIES = {
    "irvine": {"name": "Irvine", "match": "IRVINE", "sites": "he_sites"},
    "santa-ana": {"name": "Santa Ana", "match": "SANTA ANA", "sites": "hcd_sites"},
    "costa-mesa": {"name": "Costa Mesa", "match": "COSTA MESA", "sites": "hcd_sites"},
    "anaheim": {"name": "Anaheim", "match": "ANAHEIM", "sites": "hcd_sites"},
    "aliso-viejo": {"name": "Aliso Viejo", "match": "ALISO VIEJO", "sites": "hcd_sites"},
    "brea": {"name": "Brea", "match": "BREA", "sites": "hcd_sites"},
    "buena-park": {"name": "Buena Park", "match": "BUENA PARK", "sites": "hcd_sites"},
    "cypress": {"name": "Cypress", "match": "CYPRESS", "sites": "hcd_sites"},
    "dana-point": {"name": "Dana Point", "match": "DANA POINT", "sites": "hcd_sites"},
    "fountain-valley": {"name": "Fountain Valley", "match": "FOUNTAIN VALLEY", "sites": "hcd_sites"},
    "fullerton": {"name": "Fullerton", "match": "FULLERTON", "sites": "hcd_sites"},
    "garden-grove": {"name": "Garden Grove", "match": "GARDEN GROVE", "sites": "hcd_sites"},
    "la-habra": {"name": "La Habra", "match": "LA HABRA", "sites": "hcd_sites"},
    "la-palma": {"name": "La Palma", "match": "LA PALMA", "sites": "hcd_sites"},
    "laguna-beach": {"name": "Laguna Beach", "match": "LAGUNA BEACH", "sites": "hcd_sites"},
    "laguna-hills": {"name": "Laguna Hills", "match": "LAGUNA HILLS", "sites": "hcd_sites"},
    "laguna-niguel": {"name": "Laguna Niguel", "match": "LAGUNA NIGUEL", "sites": "hcd_sites"},
    "lake-forest": {"name": "Lake Forest", "match": "LAKE FOREST", "sites": "hcd_sites"},
    "los-alamitos": {"name": "Los Alamitos", "match": "LOS ALAMITOS", "sites": "hcd_sites"},
    "mission-viejo": {"name": "Mission Viejo", "match": "MISSION VIEJO", "sites": "hcd_sites"},
    "newport-beach": {"name": "Newport Beach", "match": "NEWPORT BEACH", "sites": "hcd_sites"},
    "placentia": {"name": "Placentia", "match": "PLACENTIA", "sites": "hcd_sites"},
    "san-clemente": {"name": "San Clemente", "match": "SAN CLEMENTE", "sites": "hcd_sites"},
    "san-juan-capistrano": {"name": "San Juan Capistrano", "match": "SAN JUAN CAPISTRANO", "sites": "hcd_sites"},
    "seal-beach": {"name": "Seal Beach", "match": "SEAL BEACH", "sites": "hcd_sites"},
    "stanton": {"name": "Stanton", "match": "STANTON", "sites": "hcd_sites"},
    "villa-park": {"name": "Villa Park", "match": "VILLA PARK", "sites": "hcd_sites"},
    "westminster": {"name": "Westminster", "match": "WESTMINSTER", "sites": "hcd_sites"},
    "yorba-linda": {"name": "Yorba Linda", "match": "YORBA LINDA", "sites": "hcd_sites"},
    "orange-county": {"name": "Unincorporated OC", "match": "ORANGE COUNTY", "sites": "hcd_sites"},
}

SOURCES = {
    "boundary": {
        "label": "SCAG city boundaries (2024)",
        "layer": "https://maps.scag.ca.gov/scaggis/rest/services/LDX/City_Boundary_scag/MapServer/0",
    },
    "hcd_sites": {
        "label": "HCD Housing Element Sites Inventory, Table A (SB 6 submissions; state DGS feature service)",
        "layer": "https://services8.arcgis.com/a4GMqC2tQHvYiVtK/arcgis/rest/services/SB6_ParcelsA_Pub_Join/FeatureServer/4",
    },
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
    "gtfs": {
        "label": "OCTA GTFS feed (bus routes)",
        "layer": "https://octa.net/current/google_transit.zip",
    },
    "apr": {
        "label": "HCD Housing Element Annual Progress Report, Table A2 (activity by APN)",
        "layer": "https://data.ca.gov/@california-department-of-housing-and-community-development/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year",
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
    "star_bands": {
        "value": {"5": 0.50, "4": 0.34, "3": 0.20, "2": 0.06, "1": -99},
        "why": "Stars rate a site's score as a share of the points it could earn with the data available (a site with no listed capacity is not penalised for the missing term). Bands follow the county-wide distribution on 2026-11-07: 5 stars is roughly the top 3% of Orange County sites, 4 the next 7%, 3 the next 15%, 2 the next 25%, 1 the bottom half. Likely-used sites get no stars.",
    },
    "use_as_open_land": {
        "value": {"vacant": 1.0, "parking": 0.5, "other": 0.0},
        "why": "When building footprints are unavailable, the open-land score comes from the existing use the city reported in its inventory: vacant counts as fully open, parking as half, anything else as built.",
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
        "value": {"apr_activity": 0.5, "new_building": 0.35, "coverage": 0.15},
        "why": "A city-reported entitlement, permit or completion on the APN is the strongest sign; a recent building is next; coverage alone is weak because many listed sites are intentionally non-vacant.",
    },
    "apr_min_year": {
        "value": 2021,
        "why": "APR rows from report year 2021 on count, matching the stale cutoff. Earlier activity predates the 6th-cycle list.",
    },
}
