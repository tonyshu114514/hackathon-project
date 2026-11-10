# Find It: Site Screener map

A map of housing-element sites across 30 Orange County jurisdictions (every city with a statewide
Table A submission, plus unincorporated county land), ranked and starred:

- **Top 10 to check first**: open land, lower-income capacity, size, transit and high-opportunity area,
  minus hazard, contamination and pollution-burden penalties. Ranked across every selected city,
  numbered in green on the map and listed on the right.
- **Likely already used**: listed sites that may no longer be available, drawn as red markers and never
  ranked. A site is marked when the city reported permit activity to HCD on that APN since the cutoff
  year, or a building on it is dated at or after the cutoff year. A switch hides them.

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
./run.sh --all           # all 30 jurisdictions, 30 to 60 minutes
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
Anaheim (real data, built 2026-11-07). Open it in any browser.

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
and switches to Esri street tiles automatically when that happens, with a note in the left panel. You can also pick a
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

With all 30 cities the built page is about 11 MB, mostly hazard-overlay geometry. It opens with four
cities selected; pick more from the city menu. To shrink it, raise the simplify tolerance in
`overlays()` in `build.py`.
