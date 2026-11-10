# Find It: Site Screener for Orange County housing planners

> For city housing planners and nonprofit developers: a map that ranks every housing-element site and surplus-land notice in 35 Orange County jurisdictions by how ready it is for affordable housing, flags the listed sites that are probably already taken, and screens each one against SB 9, SB 4, AB 2011 and SB 684 / SB 1123.

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
- Scores each site, shows the score as a share of attainable points with 1 to 5 stars, and lists the top 10 for whichever cities are selected. Rank counts only earned points (missing data earns nothing), and any rating that rests on missing capacity, open-land or opportunity data is labelled **Provisional** with the missing terms named. Suitability (stars), data confidence and development status are shown as three separate things.
- Says **"no reported activity"**, never "available": public data can show permit activity or a pending project, but ownership and willingness to sell are never verified. A **data-coverage table** per city shows which inventory each city comes from (SCAG or HCD) and how much capacity, open-land and opportunity data it has, and flags cities that mark every site "pending" as a reporting convention.
- Marks "likely already used" sites (HCD-reported permit activity since 2021, or a building dated 2021+) and pending projects, with a filter to hide them.
- Draws every check's source and fetch date on the page, and labels every weight and cutoff as an ASSUMPTION.
- Adds public agencies' **Surplus Land Act notices** (HCD's statewide list) as extra candidate sites, drawn in blue, with the agency, status and notice link. Most notices are archived; the page says so and tells the user to ask the agency.
- Grades **permit activity** from HCD's APR Table A2 by stage and unit type: a permit or completion is a strong sign a site is used, an entitlement a moderate one, and ADU-only activity only a caution (it no longer removes the site).
- **Search and filter**: address, site name, agency or APN; minimum acres and lower-income capacity; SCAG zoning family; transit; data confidence; "pathway not ruled out"; hide hazard concerns; include or exclude surplus notices. The ranking, stats, map and CSV follow the filters.
- **Compare** two or three sites side by side (score, stars, size, capacity, every hazard check, permit activity, pathway screens), with the best value in each row highlighted.
- **Development pathway screen** for SB 9, SB 4, AB 2011 and SB 684 / SB 1123: each test is pass, fail or unknown with a sentence and the HCD fact sheet it came from. A law shows **No** when a checkable test fails and **Unknown** otherwise; it never shows "yes", because every law depends on facts no public dataset holds (ownership, tenancy, historic status, street width).
- **Adjustable scoring weights** (sliders, defaults are the ASSUMPTION weights) and a **data-confidence** chip on every site (the share of its checks that have data).
- **Site reports**: a printable, downloadable HTML report per site with facts, checks, score breakdown, pathway screens, data notes, recommended next steps, sources and assumptions.
- **A dashboard layout with progressive disclosure**: top bar with the city picker, search, Compare and CSV; a collapsible left panel that shows only the essentials by default (four key numbers, quick-filter chips and preset scenarios) and keeps charts (star ratings, hazard flags, pathway screens, zoning families), advanced filters, map layers and legend, RHNA progress, scoring weights and data notes in collapsed sections; a large map with marker clustering, hover highlighting, a legend and a home button; and a right panel that shows the ranked list as compact cards (name, city, capacity and acreage, stars, and up to two alerts with hazards first) or one site's detail in tabs (Overview, Score, Pathways, Risks, Report), with hazards and "eligibility unconfirmed" always visible at the top and longer explanations behind tooltips and "More" sections. Light and dark themes; on a phone the panels become a drawer and a bottom sheet.
- **Shortlist**: save any site with the bookmark button; the list survives a reload (stored in the browser, no account), can be shared as a link that opens the same sites for a colleague, downloaded as a CSV (with the user's checklist progress), and backed up or moved with a JSON file.
- **Due-diligence checklist** per site (ownership and title, owner contact, zoning, pathway eligibility, Phase I, hazards, utilities, agency contact, and status when a project or permit is reported): each step shows what the public data says next to the user's own status and notes, clearly labelled as user input, and the site report includes it.
- Downloads the ranked list for the selected cities as a CSV (rank, stars, score, confidence, capacity, zoning, permit grade, pathway screens, failed and unknown checks, flags) for a meeting or a spreadsheet.
- Uses a **public-domain basemap** (USGS The National Map) that needs no API key; USGS imagery, Esri streets, Esri dark gray and (on served pages) OpenStreetMap are in the layers menu. If the active basemap's tiles fail, the map falls back to the next one and says so. Keeps working when a data server is down (the page says "unknown" and names the layer).
- Tested: unit tests for validation, permit grading, pathway rules, the surplus import and payload packing, and browser tests (Playwright, real Chrome) for map rendering, basemap fallback, city selection, filters, site detail, compare, reports, CSV, shortlist sharing, the checklist and overlapping controls on desktop and mobile.

**Demo video:** [`findit-demo.mp4`](findit-demo.mp4) (40 s, captioned walkthrough of the real-data map)
**Live demo:** <https://tonyshu114514.github.io/hackathon-project/> (GitHub Pages; opens the prebuilt map `findit-map/demo/index.html`, built 2026-11-09 for Irvine, Santa Ana, Costa Mesa and Anaheim from real data, including measured building coverage and 46 surplus-land notices). Nothing to install. The same page also works offline: download `findit-map/demo/index.html` (**Download raw file** on GitHub) and open it in any browser. Do not open `map_template.html`; that is the empty template and only says "No data".

### Deploying the live demo (GitHub Pages)

The repository is ready to serve as is: `index.html` at the root forwards to `findit-map/demo/index.html`, and `.nojekyll` tells Pages to serve files untouched. One-time setup by a repository admin: **Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: `main`, folder `/ (root)` → Save**. GitHub publishes in a minute or two at `https://<owner>.github.io/<repo>/`. To update the live demo, change `findit-map/map_template.html`, run `python refresh_demo.py` in `findit-map/` (or rebuild and copy `site/index.html` to `demo/index.html` for new data), and push. Shared shortlist links work on the live site: the `#shortlist=...` part of the address is passed through.

## How Claude is used

- Claude Code wrote and iterated the whole pipeline (data discovery, fetchers, scoring, validation, map UI) in conversation with the team, verifying each public data endpoint live and testing the page in headless Chrome.
- Claude does not run inside the tool. The page is static: every number comes from a public dataset or a labelled ASSUMPTION, and a person reviews each flagged site before acting.

## Try it

```bash
git clone https://github.com/tonyshu114514/hackathon-project.git
cd hackathon-project/findit-map
./run.sh                 # four demo cities, about 10 minutes; opens site/index.html
# ./run.sh --city brea   # one city in two or three minutes
# ./run.sh --all         # all 35 jurisdictions, 30 to 60 minutes
.venv/bin/python -m unittest discover -s tests -t .   # 38 unit tests
.venv/bin/pip install -r requirements-dev.txt && .venv/bin/python -m unittest discover -s tests_browser -t .   # 16 browser tests (uses Google Chrome)
```

Needs Python 3.10 or newer (tested on 3.15) and internet access for the first run. No accounts, API keys or environment variables. Dependencies are pinned in `findit-map/requirements.txt`. No time to fetch? Download `findit-map/demo/index.html` (see Live demo above) and open it. Windows steps, flags and troubleshooting are in [`findit-map/README-findit-map.md`](findit-map/README-findit-map.md).

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
| Surplus public land | HCD Surplus Land Act Notices of Availability (data.ca.gov CSV, modified 2026-11-06) | 2026-11-09 |
| Zoning families | SCAG 2012 General Plan Land Use Codes legend, applied to the zoning layer's SCAG codes | 2026-11-09 |
| SB 9, SB 4, AB 2011, SB 684 / SB 1123 screening tests | HCD Housing Law Fact Sheets (April 2026) and HCD's SB 9 and SB 4 fact sheets; Gov. Code §§ 65852.21, 66411.7, 65913.16, 65912.100-140, 65852.28, 66499.41, 65913.4(a)(6) | 2026-11-09 |
| Permit grades (strong / moderate / weak), ADU rule, surplus outline radius, urbanized-area assumption, confidence bands | ASSUMPTION (team judgment; listed in `findit/sources.py` and on the page) | 2026-11-09 |
| Score weights, cutoffs, star bands, open land from reported use, 660 ft cleanup radius, 2021 stale year | ASSUMPTION (team judgment; all listed in `findit/sources.py` and on the page) | 2026-11-07 |

Every number we made up is labelled ASSUMPTION here and in the tool.

## What is real and what is mocked

| Part | Status |
|---|---|
| Site inventories, parcels, hazards, transit, permits, opportunity, pollution, tax-credit, cleanup and LIHTC data | working, real public data, fetched live |
| Scoring and star ratings | working; weights are ASSUMPTIONS |
| Building coverage | working: measured from OC building footprints for the four demo cities (fetched 2026-11-09); when the county server is down, taken from the city's reported existing use (ASSUMPTION) |
| Santa Ana capacity by income level | unknown: the city's inventory lists none, so that term is left out of its scores |
| Surplus Land Act notices | working, real HCD data; 118 Orange County parcels, nearly all archived notices. Outlines come from county parcels by APN; the few with no match are drawn as a circle of the listed acreage (ASSUMPTION, marked) |
| Permit grading | working from APR stage dates and unit categories; the thresholds are ASSUMPTIONS |
| Pathway screens (SB 9, SB 4, AB 2011, SB 684 / SB 1123) | partly working: screening signals from HCD fact sheets on zoning family, lot size, fire, flood and cleanup data; ownership, tenancy, historic status, street width, industrial neighbors and the other § 65913.4(a)(6) lands are always "unknown" |
| Huntington Beach, Tustin, Orange, Laguna Woods, Rancho Santa Margarita | housing-element sites not in either statewide inventory; the map shows their surplus-land notices and context layers only |
| Ownership, willingness to sell, utilities, which state law applies | not checked |

Nothing is mocked. Where data is missing the page says "unknown".

## Where it gets things wrong

- Permit matching is by parcel number only; a parcel split or renumbered after listing will look clean.
- Permit grades read APR stage dates and unit categories as cities typed them; a project entered without a stage date is graded moderate, and an ADU row with a wrong category would still count.
- Pathway screens can only say No or Unknown. The zoning family comes from a regional SCAG code, not the city's zoning text, and specific-plan areas (code 7777) are unknown for every law.
- Surplus notices with no matching county parcel are drawn as an approximate circle; the listed acreage is sometimes text and parses to nothing.
- Opportunity, pollution and tax-credit values are tract or ZIP level, not parcel level.
- When footprints are unavailable, open land comes from a coarse use label, so a mostly-vacant "Commercial" lot scores as built.
- The cross-city ranking favours Irvine, whose data is most complete.

## Next steps

Add ownership from the assessor roll (not free) and a faith-land proxy (OpenStreetMap places of worship, IRS exempt-organization file) so SB 4 can move past "unknown"; read each city's zoning code so AB 2011 and SB 9 tests use the local zone, not the SCAG family; add the county property list and closed school sites as more surplus candidates; let a city upload its own inventory spreadsheet. With one more week: a per-city PDF brief built from the site reports.

## Data and privacy

This project uses only public or provided data. It contains no personal information about real tenants, buyers or residents. It does not file applications or contact any city or person.

## License

MIT, see the LICENSE file in this repo.
