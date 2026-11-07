# Find It: Site Screener map

A map of Irvine, Santa Ana and Costa Mesa housing-element sites, ranked two ways:

- **Top 5 to check first**: open land, lower-income capacity, size and transit, minus hazard penalties.
- **Top 5 likely already used**: listed sites that may no longer be available. The signals are, in
  order of weight: permit activity the city reported to HCD on that APN, a building dated at or
  after the cutoff year, then high footprint coverage.

The map also draws context layers you can switch on and off: OCTA bus routes, FEMA flood zones,
fire hazard zones, landslide zones and high-quality transit areas.

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
| Housing-element sites | SCAG HousingElementSite_poly_scag |
| Building coverage | OC Building Footprints |
| Year built | OC Survey Parcels |
| Zoning, slope | SCAG Zoning_poly_OR |
| Flood | OC Floodplains (FEMA zones, county copy) |
| Fire | OC Fire Hazard Severity Zones LRA; CAL FIRE SRA (statewide, older vintage) |
| Landslide | CGS Landslide Zones |
| Transit | Caltrans High Quality Transit Areas |
| Bus routes | OCTA GTFS feed |
| Permit activity | HCD Housing Element Annual Progress Report, Table A2 (data.ca.gov) |

URLs and fetch dates are in `data/cache/meta.json` and on the page under "Sources and dates".

## What it does not check

- Ownership or willingness to sell.
- Which law (SB 9 / SB 684 / AB 2011 / SB 4) applies. Hazard flags are screening signals, not
  legal tests.
- Contamination, utilities, or city objective standards.
- APR rows are typed in by city staff, so an APN that does not match is not proof of no activity.

## Third-party code

Leaflet 1.9.4 (BSD 2-Clause, see `findit/LEAFLET-LICENSE`). Its stylesheet is bundled in
`findit/leaflet.css`; the script loads from cdnjs.
