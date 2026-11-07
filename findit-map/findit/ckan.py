"""Read tables from the California Open Data portal (data.ca.gov, CKAN datastore API)."""
import json
import time

import requests

from findit.arcgis import UA

API = "https://data.ca.gov/api/3/action/datastore_search"


def search_all(resource_id, filters, fields=None, batch=5000):
    """All rows matching exact-value filters, paged."""
    out, offset = [], 0
    while True:
        p = {"resource_id": resource_id, "filters": json.dumps(filters), "limit": batch, "offset": offset}
        if fields:
            p["fields"] = ",".join(fields)
        r = requests.get(API, params=p, headers=UA, timeout=120)
        r.raise_for_status()
        res = r.json()["result"]
        out += res["records"]
        offset += len(res["records"])
        if not res["records"] or offset >= res.get("total", 0):
            return out
        time.sleep(0.2)
