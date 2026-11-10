# Find It: Site Screener map

A map of housing-element sites and Surplus Land Act notices across 35 Orange County jurisdictions (every city with a
statewide Table A submission, unincorporated county land, and five cities that appear only through their surplus
notices), ranked and starred:

- **Top 10 to check first**: open land, lower-income capacity, size, transit and high-opportunity area,
  minus hazard, contamination and pollution-burden penalties. Ranked across every selected city,
  numbered in green on the map and listed on the right.
- **Likely already used**: listed sites that may no longer be available, drawn as red markers and never
  ranked. A site is marked when the city reported permit activity to HCD on that APN since the cutoff
  year, or a building on it is dated at or after the cutoff year. A switch hides them.

A button above the list downloads every site in the selected cities as a CSV, best first, with stars, score,
confidence, capacity, zoning, permit grade, pathway screens, failed and unknown checks, data flags and coordinates.

## The page

- **Top bar**: city picker (multi-select, with search and a Done button; it floats above the map and scrolls when
  the list is long), site search, Compare (with a count of the sites queued), CSV download, an information button that
  opens **Disclosures & methodology** (the prototype disclaimer, how scoring and likely-used work, the pathway-screen
  caveats, what is not checked, surplus-notice notes, basemap notes, every assumption, every source with its fetch
  date, and the build date), theme switch, and a button that hides or shows the site panel.
- **Left panel** (collapsible, a slide-in drawer on phones): a one-line "Screening tool only · Assumptions apply"
  notice linking to the disclosures, live overview tiles and four small charts
  computed from the sites currently on screen (star ratings of available sites, hazard concerns and cautions by
  hazard, pathway screen results by law, SCAG zoning families), quick-filter chips, a scenario preset menu, advanced
  filters, map layers, RHNA progress, scoring weights, data notes and checks, assumptions, sources.
- **Map**: numbered pins for the top 10, dots for every other site (clustered into counts when zoomed out; the cluster
  border turns red when it holds a likely-used site), parcel outlines that brighten on hover from the list or the map,
  city borders, context layers, a legend, zoom-home, and the basemap picker. A small status pill under the layers
  button names the basemap in use and says "OSM unavailable" when the page has switched to Esri tiles. A pill row over
  the map shows the count and every active filter, each removable with one click.
- **Right panel**: the ranked top-10 list, or one site's detail in tabs: Overview (facts, why it ranks, sources), Score
  (score ring, share of attainable points, term-by-term bars, confidence), Pathways (the four law screens with a
  pass/fail/unknown meter and expandable tests), Risks (hazard, contamination and use checks as cards, then context
  checks), Report (next steps, open or download the report). Back returns to the list. On phones this panel is a bottom
  sheet: tap the handle to open it halfway or fully.

## Finding, filtering, comparing

- **Search** by address, site name, agency or APN (digits only is fine). **Quick filters**: available only, 4+ stars,
  near transit, 1+ acres, no hazard concerns, high confidence, surplus land only. **Scenarios** set several filters at
  once: acquisitions call list, city hazard review, small-lot homes (SB 684 / SB 1123), commercial corridors (AB 2011),
  faith and college land leads (SB 4), public surplus land. **Advanced filters**: minimum acres, minimum lower-income
  capacity, SCAG zoning family, transit area, "pathway not ruled out", data confidence, minimum stars, record type
  (inventory or surplus), hide hazard concerns, hide likely-used sites. The ranking, the statistics, the charts, the
  map and the CSV all follow the filters; the pill row over the map lists what is active.
- **Compare**: "Compare" in a site's detail adds it to a bar at the bottom of the map; with two or three sites,
  "Compare N sites" (or the Compare button in the top bar) opens a side-by-side table grouped into Site, Rating,
  Context, Hazards and use, and Pathway screens. Rows where the sites differ are emphasised and rows that match are
  muted; "Differences only" hides the matching rows. The best value in a row is shaded where "best" is clear.
- **Scoring weights**: the "Scoring weights (adjust)" panel has a slider per weight. Moving one re-scores every site
  from its stored factors and re-ranks; the right panel says "Scored with custom weights" and the CSV header records
  them. Nothing is saved; "Reset to defaults" restores the ASSUMPTION weights.
- **Data confidence**: every card and popup carries a chip (high / medium / low) for the share of the site's checks
  that have data. It describes the data, not the site. Bands are in `ASSUMPTIONS["confidence_bands"]`.
- **Site report**: "Site report" opens a printable page for one site (facts, score breakdown, checks with sources and
  fetch dates, pathway screens, data notes, recommended next steps, sources, assumptions); "Download report" saves it
  as a standalone HTML file. Print to PDF from the browser.
- **⌂** on the map zooms back to the selected cities.

## Permit activity grades

`findit/permits.py` reads the HCD APR Table A2 rows matched to a site's APN (report year 2021 on) and grades them:

| Grade | Meaning | Effect |
|---|---|---|
| strong | building permit issued or certificate of occupancy, non-ADU | marked likely used |
| moderate | entitled (approved) only, or a row with no stage date | marked likely used |
| weak | accessory dwelling units only | caution only; the site stays available and ranked |
| none | no row matched | pass |

The check sentence names the stage, unit categories, unit count and project name. Grades are ASSUMPTIONS
(`permit_grades`). A miss is never proof of no activity: cities type APNs by hand.

## Development pathway screen

`findit/pathways.py` runs each site through screening tests for four laws, using HCD's Housing Law Fact Sheets
(April 2026) as the source for each test and the layers already loaded as the evidence:

| Law | Tests the data can run | Always unknown |
|---|---|---|
| SB 9 (Gov. Code §§ 65852.21, 66411.7) | single-family zone (SCAG family), very high fire zone, FEMA flood zone, DTSC cleanup on parcel, site already used or pending | historic resource, tenant and rent-restriction history, other § 65913.4(a)(6) lands |
| SB 684 / SB 1123 (§§ 65852.28, 65913.4.5, 66499.41) | lot under 5 acres, multifamily zone (or vacant single-family lot for SB 1123), hazards as above | displacement of protected housing |
| AB 2011 (§§ 65912.100-140) | zone allows office, retail or parking (SCAG commercial or mixed families), hazards as above | corridor frontage and street width, adjacent industrial uses, project affordability and labor terms |
| SB 4 (§ 65913.16) | publicly owned land fails (SB 4 needs faith or independent-college ownership), hazards as above | the ownership itself, 75% urban perimeter, industrial neighbors, 100% affordable project |

A law reads **No** when a checkable test fails and **Unknown** otherwise, with "N of M pass" so a user can see how
far it got. It never reads "yes". The urbanized-area test is an ASSUMPTION (every incorporated OC city is treated
as inside a Census urbanized area). Zoning families come from the SCAG code on the parcel (`ZN24_SCAG`) read
against SCAG's 2012 land use code legend; four-digit sub-codes are matched by family and labelled as such, and
specific-plan areas (7777) are unknown for every law. These are screening signals, not legal tests, and never legal
advice. Each test's sentence, the sources and the date checked (2026-11-09) are on the page and in the site report.

## Surplus Land Act notices

`fetch.py` downloads HCD's statewide Notices of Availability CSV once (`data/cache/surplus_noa.json`, with the
staff-contact column dropped) and, per city, turns the rows whose City matches into pseudo sites
(`findit/surplus.py`): APN, address, listed acreage (text like "9,005 SF" is converted), general plan or zoning,
existing use, the agency and the notice's status, date and link. Outlines come from the county parcel layer by
APN; when nothing matches, a circle of the listed acreage (or a 60 ft radius, `surplus_outline_radius_ft`) is drawn at
the notice's coordinates and marked approximate. The sites then go through the same validation, checks and scoring;
they have no listed capacity, so that term is left out. Blue squares on the map; "surplus" chips in the lists; a
banner in the popup. Nearly every notice is "Archive" (the 60-day window passed): treat it as a lead and ask the
agency. `fetch.py --skip surplus` leaves them out.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -t .
```

Unit tests cover record validation, permit grading (including the ADU rule), pathway rules (no law ever returns
"yes"; hazards fail every law; unknown layers stay unknown) and the surplus import (acreage parsing, exact city
match, contact column dropped, approximate outlines). A browser smoke test of the page lives outside the repo in the
team's tooling; the demo page was checked in Chromium on 2026-11-09 with no console errors.

The map also draws context layers you can switch on and off: OCTA bus routes, FEMA flood zones,
fire hazard zones, landslide zones, high-quality transit areas, DTSC cleanup sites and existing LIHTC
housing. Each city shows its RHNA progress, and each site is named by its HCD project name, county
assessor address or, failing those, an OpenStreetMap place name.

Prototype for screening only. Not legal, zoning or real estate advice. Every weight and cutoff is an
ASSUMPTION listed in `findit/sources.py` and on the map page.

## Try it

Python 3.10+ and internet access for the first run. No accounts or API keys.

```bash
cd findit-map
./run.sh                 # four demo cities, about 10 minutes; opens site/index.html when done
./run.sh --city brea     # one city, a minute or two
./run.sh --all           # all 35 jurisdictions, 30 to 60 minutes
```

`run.sh` creates `.venv`, installs the pinned requirements, runs `fetch.py` then `build.py`.
On Windows, or to run the steps by hand:

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # macOS/Linux: .venv/bin/pip
python fetch.py --city irvine --skip footprints   # downloads public layers into data/cache/ (resumable)
python build.py                                   # scores sites, writes site/index.html and data/results.json
start site\index.html                             # macOS: open site/index.html
```

No time to fetch? `demo/index.html` is a prebuilt page for Irvine, Santa Ana, Costa Mesa and
Anaheim (real data, built 2026-11-09, with measured building coverage and 46 surplus-land notices). Open it in any browser.

`--skip footprints` leaves out the OC building-footprint layer, whose server was returning errors on
event day; open land is then scored from the existing use each city reported (an ASSUMPTION shown on
the page). Drop the flag to try the footprints. `fetch.py --skip-apr` skips the statewide permit
download if it is slow; the permit check then shows "unknown". Re-running skips anything cached; delete
a file in `data/cache/` to refresh it.

`build.py --city X --city Y --out demo/index.html` builds a page for a subset of cached cities.

## Check these after the first run

`build.py` guesses column names from each layer and prints what it picked, for example
`APN=Assessor_Parcel_Number lower=...`. If a column is wrong or `None`, set it in
`FIELD_OVERRIDES` in `findit/sources.py` and re-run `build.py`. No re-fetch is needed.

Also watch for these lines from `fetch.py`:

- `matched N/M site APNs` for parcels and zoning. A low match rate means year built or zoning will
  show "unknown" for most sites.
- `zero footprints for every site`. The spatial query may be failing, and coverage will be unknown.

## If the street map says "Access blocked"

The grey-and-yellow "Access blocked" tiles come from OpenStreetMap's volunteer tile servers, which refuse some
connections (VPNs and shared or flagged IP addresses are the usual reason). The page checks one tile when it opens
and switches to Esri street tiles automatically when that happens; the status pill on the map then reads
"Basemap: Esri streets · OSM unavailable" and the Disclosures dialog explains why. You can also pick a
basemap yourself with the layers button at the top right of the map, or turn the VPN off and reload.

## Data sources

| Layer | Source |
|---|---|
| Housing-element sites (Irvine) | SCAG HousingElementSite_poly_scag |
| Housing-element sites (all other jurisdictions) | HCD Sites Inventory Table A, state DGS feature service `SB6_ParcelsA_Pub_Join` |
| Building coverage | OC Building Footprints |
| Year built | OC Survey Parcels |
| Zoning, slope | SCAG Zoning_poly_OR |
| Flood | OC Floodplains (FEMA zones, county copy) |
| Fire | OC Fire Hazard Severity Zones LRA; CAL FIRE SRA (statewide, older vintage) |
| Landslide | CGS Landslide Zones |
| Transit | Caltrans High Quality Transit Areas |
| Bus routes | OCTA GTFS feed |
| Permit activity | HCD Housing Element Annual Progress Report, Table A2 (data.ca.gov) |
| City RHNA progress | HCD 6th Cycle RHNA Progress Report (data.ca.gov) |
| Opportunity area | CTCAC/HCD 2025 Opportunity Map (statewide copy, CA Coastal Commission) |
| Pollution burden | OEHHA CalEnviroScreen 5.0 (final) |
| Tax credit boost | HUD 2026 Qualified Census Tracts and Difficult Development Areas |
| Contamination | DTSC EnviroStor cleanup sites |
| Existing affordable | HUD LIHTC properties |
| Site names | OC Survey Parcels site address; OpenStreetMap Nominatim for unaddressed parcels |

URLs and fetch dates are in `data/cache/meta.json` and on the page under "Sources and dates".

## What it does not check

- Ownership or willingness to sell.
- Which law (SB 9 / SB 684 / AB 2011 / SB 4) applies. Hazard flags are screening signals, not
  legal tests.
- GeoTracker leak sites, utilities, or city objective standards.
- APR rows are typed in by city staff, so an APN that does not match is not proof of no activity.

## Third-party code

Leaflet 1.9.4 (BSD 2-Clause, see `findit/LEAFLET-LICENSE`). Its stylesheet is bundled in
`findit/leaflet.css`; the script loads from cdnjs.

## Which inventory each city uses

SCAG's HousingElementSite_poly_scag layer has no Santa Ana or Costa Mesa records (checked 2026-11-07), so
every other jurisdiction reads HCD's statewide Table A inventory instead (26 more cities plus
unincorporated county land; Huntington Beach, Tustin, Orange, Laguna Woods and Rancho Santa Margarita
are in neither source). `fetch.py` renames its fields to
the SCAG names `build.py` expects and keeps HCD's extras (site status, existing use, public ownership).
Irvine stays on SCAG so its rankings match earlier runs; HCD lists 117 Irvine sites to SCAG's 44.
Set `sites` per city in `findit/sources.py` to switch.

Santa Ana's inventory marks every site "Pending Project" with no capacity by income level, so its
"check first" scores leave the capacity term out. Max density and acreage are present if a team wants
to estimate capacity (label it as an estimate).

## Data checks before ranking

`findit/validate.py` runs on every city's site records before anything is scored:

| Check | What happens |
|---|---|
| No usable outline | Dropped |
| Duplicate APN | One record kept (the one with the most listed capacity), the rest dropped |
| Negative capacity | Value blanked |
| Income-level capacities exceed the total | Warning |
| No capacity listed | Warning; the capacity term is left out of that site's score |
| Listed acres differ from the outline by more than 50% | Warning (often a consolidated multi-parcel site) |
| Site outside the city boundary | Warning |
| Missing or short APN | Warning (parcel data cannot be joined) |
| Status "Pending Project" | Flag: shown on the site and in the lists; a switch on the page leaves these out of "check first" |

Counts per city print during `build.py` and appear on the page under "Data checks".

## Stars

Each available site gets 1 to 5 stars from its screen score as a share of the points it could earn
with the data it has (so a site with no listed capacity is not penalised for the missing term). The
bands are set at county-wide percentiles and listed in `ASSUMPTIONS["star_bands"]`: 5 stars is roughly
the top 3% of Orange County sites, 1 star the bottom half. Likely-used sites get no stars.

## Page size

With all 35 jurisdictions the built page is roughly 15 MB (hazard-overlay geometry plus the per-site checks and
pathway screens; repeated pathway sentences are stored once). It opens with four
cities selected; pick more from the city menu. To shrink it, raise the simplify tolerance in
`overlays()` in `build.py`.
