import json
import time

import requests

UA = {"User-Agent": "findit-hackathon-prototype (UCI Claude Impact Lab)"}
PAUSE = 0.15


def _call(url, params, retries=3):
    params = {**params, "f": "json"}
    last = None
    for i in range(retries):
        try:
            r = requests.post(url, data=params, headers=UA, timeout=90)
            r.raise_for_status()
            j = r.json()
            if "error" in j:
                raise RuntimeError(f"{url}: {j['error']}")
            time.sleep(PAUSE)
            return j
        except Exception as e:
            last = e
            time.sleep(3 * (i + 1))
    raise last


def info(url):
    return _call(url, {})


def resolve_layer(src):
    if "layer" in src:
        return src["layer"]
    svc = info(src["service"])
    layers = svc.get("layers", [])
    want = src.get("layer_name_contains")
    if want:
        hits = [l for l in layers if want.lower() in l["name"].lower()]
        if not hits:
            raise RuntimeError(f"No layer with '{want}' in {src['service']}: {[l['name'] for l in layers]}")
        return f"{src['service']}/{hits[-1]['id']}"
    return f"{src['service']}/{layers[0]['id']}"


def field_names(layer_info):
    return [f["name"] for f in layer_info.get("fields", [])]


def find_field(names, exact=(), contains=()):
    low = {n.lower(): n for n in names}
    for e in exact:
        if e.lower() in low:
            return low[e.lower()]
    for group in contains:
        for n in names:
            if all(s in n.lower() for s in group):
                return n
    return None


def envelope(bounds):
    xmin, ymin, xmax, ymax = bounds
    return {"geometry": json.dumps({"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax,
                                    "spatialReference": {"wkid": 4326}}),
            "geometryType": "esriGeometryEnvelope", "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects"}


def polygon_filter(rings):
    return {"geometry": json.dumps({"rings": rings, "spatialReference": {"wkid": 4326}}),
            "geometryType": "esriGeometryPolygon", "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects"}


def query_all(layer_url, where="1=1", spatial=None, out_fields="*", geometry=True,
              max_offset=None, batch=500):
    """All matching features, paged by object id so it works on any ArcGIS server."""
    base = {"where": where, **(spatial or {})}
    ids = _call(f"{layer_url}/query", {**base, "returnIdsOnly": "true"}).get("objectIds") or []
    feats = []
    for i in range(0, len(ids), batch):
        p = {"objectIds": ",".join(map(str, ids[i:i + batch])), "outFields": out_fields,
             "returnGeometry": "true" if geometry else "false", "outSR": 4326}
        if max_offset:
            p["maxAllowableOffset"] = max_offset
        feats += _call(f"{layer_url}/query", p).get("features", [])
    return feats


def query_once(layer_url, where="1=1", spatial=None, out_fields="*", geometry=True, count=None):
    p = {"where": where, **(spatial or {}), "outFields": out_fields,
         "returnGeometry": "true" if geometry else "false", "outSR": 4326}
    if count:
        p["resultRecordCount"] = count
    return _call(f"{layer_url}/query", p).get("features", [])
