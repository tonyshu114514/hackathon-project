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
- **Left panel** (collapsible, a slide-in drawer on phones): four key numbers (sites, no reported activity, likely
  used, hazard flags) with pending and surplus counts, quick-filter chips and a scenario menu. Collapsed under "More":
  four charts computed from the sites on screen (star ratings, hazard concerns and cautions, pathway screens, SCAG
  zoning families), advanced filters, map layers and legend, RHNA progress, scoring weights, and data notes with the
  data-coverage table by city and the record checks.
- **Map**: numbered pins for the top 10, dots for every other site (clustered into counts when zoomed out; the cluster
  border turns red when it holds a likely-used site), parcel outlines that brighten on hover from the list or the map,
  city borders, context layers, a legend, zoom-home, and the basemap picker. A small status pill under the layers
  button names the basemap in use and says "fallback" when the page has switched basemaps. A pill row over
  the map shows the count and every active filter, each removable with one click.
- **Right panel**: a **Top 10 | Shortlist** switch over the ranked list, or one site's detail. The detail header keeps
  suitability (stars, "Provisional" when data is missing), data confidence and development **Status** apart, shows every
  alert, and says "Eligibility unconfirmed" with the pathway count. Tabs: Overview (key facts, more facts, data notes,
  sources), Score (score ring, share of attainable points, term-by-term bars, the terms not scored for lack of data,
  confidence), Pathways (the four law screens with a pass/fail/unknown meter and expandable tests), Risks (hazard,
  contamination and use checks as cards, then context checks), Checklist (the due-diligence steps below), Report (next
  steps, open or download the report). Back returns to the list. On phones this panel is a bottom sheet: tap the handle
  to open it halfway or fully.

## Finding, filtering, comparing

- **Search** by address, site name, agency or APN (digits only is fine). **Quick filters**: no reported activity, 4+ stars,
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

## Shortlist, sharing and the due-diligence checklist

Nothing here needs an account, and nothing is sent anywhere: the shortlist and checklists are stored in the browser
(`localStorage`, keyed by city and APN so they survive data rebuilds). If the browser blocks storage the page says so.

- **Save** a site with the bookmark button on its card or in its detail header. **Shortlist** (next to Top 10) lists
  saved sites with their rank in the current selection and checklist progress; a saved site in a city that is not
  selected opens with its city added to the map.
- **Share link** copies an address ending in `#shortlist=...`. Whoever opens it sees a "Shared shortlist" banner with
  the sites and can add them to their own list. The link carries site keys only, never checklist notes.
- **CSV** downloads the shortlisted sites with every column of the full export plus `your_checklist_done`,
  `your_checklist_issues` and `your_checklist_notes` (marked as user-entered in the file header).
- **Backup file** downloads a JSON file with the shortlist and every checklist; **Import** merges one back in (newer
  checklist edits win). Use it to move work to another browser or to a colleague.
- **Checklist** tab, per site: ownership and title; owner contacted / willing to sell; zoning and general plan; pathway
  eligibility; environmental review (Phase I); flood, fire and geologic hazards; water, sewer and dry utilities; city or
  agency contact; and, when a project or permit is reported, site status. Each step shows a **Public data** line (what
  the loaded datasets say, or that they say nothing) next to **your** status (not started, in progress, done, issue
  found) and note. Starting a checklist saves the site to the shortlist, and the site report prints the checklist in a
  section headed "entered by you, not verified data".

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
.venv/bin/python -m unittest discover -s tests -t .              # unit tests, a few seconds
.venv/bin/pip install -r requirements-dev.txt                     # Playwright, for the browser tests
.venv/bin/python -m unittest discover -s tests_browser -t .      # browser tests, about a minute
FINDIT_PAGE=site/index.html .venv/bin/python -m unittest discover -s tests_browser -t .   # test your own build
FINDIT_URL=https://tonyshu114514.github.io/hackathon-project/findit-map/demo/index.html \
  .venv/bin/python -m unittest discover -s tests_browser -t .    # test the live GitHub Pages demo
FINDIT_BROWSER=chromium ...                                       # use Playwright's Chromium (playwright install chromium)
```

Unit tests cover record validation, permit grading (including the ADU rule), pathway rules (no law ever returns
"yes"; hazards fail every law; unknown layers stay unknown), the surplus import (acreage parsing, exact city
match, contact column dropped, approximate outlines) and payload packing (lossless round trip).

Browser tests (`tests_browser/test_ui.py`) open the page in real Chrome from a local server (and once from `file://`)
and check: the page loads with sites, the USGS basemap and no console errors; the basemap falls back when its tiles
fail; OpenStreetMap is not offered on `file://`; city selection, quick filters, pills and reset; the six detail tabs and
the provisional rating; compare; the site report; the CSV columns; shortlist persistence, share link and backup import;
checklist persistence and labelling; no overlapping map controls at 1440×900, 1280×640 and 1024×700 with each
combination of panels open and closed; the phone drawer, sheet and detail; and load and redraw time. Map tiles are
answered with a blank image so the tests do not depend on tile servers; Leaflet loads from cdnjs, so they need internet.

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

## Basemap

The default basemap is **USGS The National Map, Topo** (`basemap.nationalmap.gov`): a U.S. government service in the
public domain, with no API key, CORS enabled and no Referer rule. Its tiles stop at zoom 16 and are upscaled beyond
that. The layers button offers USGS Imagery (aerial, public domain), Esri streets and Esri dark gray (Esri terms of
use; attribution shown) and, when the page is served over http(s), OpenStreetMap.

Why not OpenStreetMap by default: its volunteer tile servers answer any request without a `Referer` header with an
"Access blocked" picture **and HTTP 200** (checked 2026-11-09: 6.7 KB blocked image instead of the 47.8 KB tile). Pages
opened from a file (`run.sh` opens `site/index.html` that way, and so does a downloaded demo) send no Referer, so every
tile was blocked and Leaflet saw no error. OSM is therefore not offered on `file://` pages; on served pages a one-tile
probe still detects the blocked picture. CARTO's free tiles now return "API key required", so they are not used.

Fallback: each basemap is watched per map view. If the active one fails (three tile errors with none loaded, or
failures outnumbering loads two to one), the map switches along USGS Topo → Esri streets → USGS Imagery → no basemap,
and the status pill and the Disclosures dialog say which and why. No API keys are used anywhere, so none can leak.

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

## Stars, rank and "provisional"

Each site that is not likely used gets 1 to 5 stars from its screen score as a share of the points it could earn
with the data it has (so a site with no listed capacity is not penalised for the missing term). The
bands are set at county-wide percentiles and listed in `ASSUMPTIONS["star_bands"]`: 5 stars is roughly
the top 3% of Orange County sites, 1 star the bottom half. Likely-used sites get no stars.

The **rank** (top 10) is stricter: it orders by earned points, so a missing term earns nothing, then by fewer data
gaps, share of attainable points and name (ties never depend on data order). Because the two can disagree, any rating
missing open-land, lower-income capacity or opportunity-area data is labelled **Provisional**: the stars are dimmed, the
label says so, and the Score tab lists each term not scored and its maximum points. In the 2026-11-09 demo this is
mostly Santa Ana, whose HCD inventory lists no capacity by income level for any site.

**Status** is separate from both: "likely used", "pending", "surplus notice" or "no reported activity". The last never
means available: ownership and willingness to sell are not in public data. When a city marks (nearly) every inventory
site "pending", as Santa Ana does, the page treats it as a reporting convention and says to verify each site. The
**data-coverage table** (Data notes, and the Disclosures dialog) shows, per selected city, the inventory source, sites,
and the share with listed capacity, open land (measured from footprints or from reported use), opportunity data and
pending status.

## Page size and speed

`build.py` packs the page payload (`findit/pack.py`): every distinct check and pathway sentence is stored once and each
check or test becomes a short array of indexes; the page rebuilds the objects at load. It is lossless (a unit test and
a full comparison of the four-city build against `data/results.json` confirm it) and cut the four-city page from
3.3 MB to 1.9 MB. `data/results.json` keeps the readable form.

Scale check (2026-11-10, Chrome on a MacBook): a synthetic page with the four cities copied 8× (3,752 sites, 32 cities,
13 MB) showed its ranked list 0.6 s after navigation, drew every city at once in 0.21 s, applied a filter in 0.16 s and
opened a site in 9 ms. The page opens with four cities selected; pick more from the city menu. GitHub Pages serves it
gzip-compressed. To shrink it further, raise the simplify tolerance in `overlays()` in `build.py`.

`python refresh_demo.py` re-applies `map_template.html` to `demo/index.html` (packing it the same way) without
touching its data; `--check` reports whether the demo is current.
