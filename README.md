# Find It: Site Screener for Orange County housing planners

> For city housing planners and nonprofit developers: a map that ranks every housing-element site in 30 Orange County jurisdictions by how ready it is for affordable housing, and flags the listed sites that are probably already taken.

**Team:** wadahail
**Members:** Xinyan Shu, Tingxuan Wang
**Lane:** 1 Find it
**Built at:** Claude Impact Lab: UCI × SoCal Affordable Housing, November 7, 2026

## The real user

A city housing planner has a state-mandated list of sites that are supposed to absorb the city's share of new homes, but the list was drawn up years ago from spreadsheets. Some sites have since been permitted or built on; others sit in flood zones, next to cleanup sites, or far from transit. Checking any one site means opening six or seven separate GIS portals.

**Before:** the planner picks sites from the inventory spreadsheet and checks each one by hand across county, state and federal portals, usually only after a developer asks.
**After:** every site in the county is on one map with a 1 to 5 star rating, the reasons behind it, every hazard and context check with its source, and a red marker on sites the state's own permit data says are already in use.

## What we built

A static web map (`findit-map/`) that:

- Pulls each city's housing-element sites from SCAG and HCD's statewide inventory, then joins county parcels (year built, address), SCAG zoning, OC flood, fire and landslide zones, Caltrans transit areas, OCTA bus routes, HCD permit records, the CTCAC/HCD opportunity map, CalEnviroScreen 5.0, HUD tax-credit areas, DTSC cleanup sites and HUD LIHTC properties.
- Validates every record before scoring (duplicates, impossible values, acreage mismatches, pending projects).
- Scores each site, shows the score as a share of attainable points with 1 to 5 stars, and lists the top 10 for whichever cities are selected.
- Marks "likely already used" sites (HCD-reported permit activity since 2021, or a building dated 2021+) and pending projects, with a filter to hide them.
- Draws every check's source and fetch date on the page, and labels every weight and cutoff as an ASSUMPTION.
- Downloads the ranked list for the selected cities as a CSV (rank, stars, score, capacity, failed and unknown checks, flags) for a meeting or a spreadsheet.
- Keeps working when a data server is down (the page says "unknown" and names the layer) and when OpenStreetMap blocks the street map (it switches to Esri tiles and says so).

**Demo video:** [`findit-demo.mp4`](findit-demo.mp4) (40 s, captioned walkthrough of the real-data map)
**Live demo:** open `findit-map/demo/index.html` from this repo in any browser (prebuilt, four cities, real data).

## How Claude is used

- Claude Code wrote and iterated the whole pipeline (data discovery, fetchers, scoring, validation, map UI) in conversation with the team, verifying each public data endpoint live and testing the page in headless Chrome.
- Claude does not run inside the tool. The page is static: every number comes from a public dataset or a labelled ASSUMPTION, and a person reviews each flagged site before acting.

## Try it

```bash
git clone https://github.com/tonyshu114514/hackathon-project.git
cd hackathon-project/findit-map
./run.sh                 # four demo cities, about 10 minutes; opens site/index.html
# ./run.sh --city brea   # one city in a minute or two
# ./run.sh --all         # all 30 jurisdictions, 30 to 60 minutes
```

Needs Python 3.10 or newer (tested on 3.15) and internet access for the first run. No accounts, API keys or environment variables. Dependencies are pinned in `findit-map/requirements.txt`. No time to fetch? Open `findit-map/demo/index.html`. Windows steps, flags and troubleshooting are in [`findit-map/README-findit-map.md`](findit-map/README-findit-map.md).

## Sources and assumptions

| Item | Source or assumption | Date checked |
|---|---|---|
| Housing-element sites (Irvine) | SCAG HousingElementSite_poly_scag | 2026-11-07 |
| Housing-element sites (29 other jurisdictions) | HCD Sites Inventory Table A, state DGS feature service | 2026-11-07 |
| City boundaries | SCAG City_Boundary_scag (2024) | 2026-11-07 |
| Parcels: year built, site address | OC Survey Parcels | 2026-11-07 |
| Building coverage | OC Building Footprints (Irvine only; server failed on event day for the rest) | 2026-11-07 |
| Zoning, slope | SCAG Zoning_poly_OR | 2026-11-07 |
| Flood, fire, landslide | OC Floodplains (FEMA), OC and CAL FIRE severity zones, CGS landslide zones | 2026-11-07 |
| Transit | Caltrans High Quality Transit Areas; OCTA GTFS | 2026-11-07 |
| Permit activity, RHNA progress | HCD Annual Progress Report Table A2; HCD RHNA Progress Report (data.ca.gov) | 2026-11-07 |
| Opportunity area | CTCAC/HCD 2025 Opportunity Map | 2026-11-07 |
| Pollution burden | OEHHA CalEnviroScreen 5.0 (final) | 2026-11-07 |
| Tax-credit areas | HUD 2026 QCTs and DDAs | 2026-11-07 |
| Contamination | DTSC EnviroStor cleanup sites | 2026-11-07 |
| Existing affordable housing | HUD LIHTC database | 2026-11-07 |
| Place names for unaddressed parcels | OpenStreetMap Nominatim | 2026-11-07 |
| Score weights, cutoffs, star bands, open land from reported use, 660 ft cleanup radius, 2021 stale year | ASSUMPTION (team judgment; all listed in `findit/sources.py` and on the page) | 2026-11-07 |

Every number we made up is labelled ASSUMPTION here and in the tool.

## What is real and what is mocked

| Part | Status |
|---|---|
| Site inventories, parcels, hazards, transit, permits, opportunity, pollution, tax-credit, cleanup and LIHTC data | working, real public data, fetched live |
| Scoring and star ratings | working; weights are ASSUMPTIONS |
| Building coverage | working for Irvine; for other cities taken from the city's reported existing use (ASSUMPTION) because the OC footprint server was down |
| Santa Ana capacity by income level | unknown: the city's inventory lists none, so that term is left out of its scores |
| Huntington Beach, Tustin, Orange, Laguna Woods, Rancho Santa Margarita | not covered: in neither statewide inventory |
| Ownership, willingness to sell, utilities, which state law applies | not checked |

Nothing is mocked. Where data is missing the page says "unknown".

## Where it gets things wrong

- Permit matching is by parcel number only; a parcel split or renumbered after listing will look clean.
- Any HCD-reported activity counts as "likely used", including a single ADU permit on a large site.
- Opportunity, pollution and tax-credit values are tract or ZIP level, not parcel level.
- Cities without footprint data score open land from a coarse use label, so a mostly-vacant "Commercial" lot scores as built.
- The cross-city ranking favours Irvine, whose data is most complete.

## Next steps

Fetch footprints when the county server is back; grade permit activity by stage and unit count; add ownership from the assessor roll (not free); let a city upload its own inventory spreadsheet. With one more week: a per-city PDF brief for each top-10 site.

## Data and privacy

This project uses only public or provided data. It contains no personal information about real tenants, buyers or residents. It does not file applications or contact any city or person.

## License

MIT, see the LICENSE file in this repo.
