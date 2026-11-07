# Find It: Site Screener map

A map of Irvine, Santa Ana, Costa Mesa and Anaheim housing-element sites, ranked two ways:

- **Top 5 to check first**: open land, lower-income capacity, size, transit and high-opportunity area,
  minus hazard, contamination and pollution-burden penalties.
- **Top 5 likely already used**: listed sites that may no longer be available. The signals are, in
  order of weight: permit activity the city reported to HCD on that APN, a building dated at or
  after the cutoff year, then high footprint coverage.

The map also draws context layers you can switch on and off: OCTA bus routes, FEMA flood zones,
fire hazard zones, landslide zones, high-quality transit areas, DTSC cleanup sites and existing LIHTC
housing. Each city shows its RHNA progress, and each site is named by its HCD project name, county
assessor address or, failing those, an OpenStreetMap place name.

Prototype for screening only. Not legal, zoning or real estate advice. Every weight and cutoff is an
ASSUMPTION listed in `findit/sources.py` and on the map page.

## Try it

Python 3.10+.

```bash
pip install -r requirements.txt
python fetch.py          # downloads public layers into data/cache/ (a few minutes; resumable)
python build.py          # scores sites, writes site/index.html, site/artifact.html, data/results.json
open site/index.html     # macOS; on Windows: start site\index.html
```

`fetch.py --skip-apr` skips the statewide permit download if it is slow. The permit check then
shows "unknown".

`site/index.html` is the version to demo: it adds an OpenStreetMap street basemap. `site/artifact.html`
is the same page without the document wrapper, for publishing as a Claude artifact (artifacts block
map tiles, so the drawn layers give the geography there).

`fetch.py` only reads public ArcGIS services and caches everything. Re-running skips what is cached.
To refresh one layer, delete its file in `data/cache/`.

## Check these after the first run

`build.py` guesses column names from each layer and prints what it picked, for example
`APN=Assessor_Parcel_Number lower=...`. If a column is wrong or `None`, set it in
`FIELD_OVERRIDES` in `findit/sources.py` and re-run `build.py`. No re-fetch is needed.

Also watch for these lines from `fetch.py`:

- `matched N/M site APNs` for parcels and zoning. A low match rate means year built or zoning will
  show "unknown" for most sites.
- `zero footprints for every site`. The spatial query may be failing, and coverage will be unknown.

## Data sources

| Layer | Source |
|---|---|
| Housing-element sites (Irvine) | SCAG HousingElementSite_poly_scag |
| Housing-element sites (Santa Ana, Costa Mesa, Anaheim) | HCD Sites Inventory Table A, state DGS feature service `SB6_ParcelsA_Pub_Join` |
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
those cities, and Anaheim, read HCD's statewide Table A inventory instead. `fetch.py` renames its fields to
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
