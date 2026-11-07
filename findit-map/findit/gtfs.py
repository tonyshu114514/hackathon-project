"""OCTA bus routes from the public GTFS feed: https://octa.net/current/google_transit.zip"""
import csv
import io
import zipfile

from shapely.geometry import LineString, box

URL = "https://octa.net/current/google_transit.zip"


def _read(z, name):
    with z.open(name) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")))


def routes_in_bbox(zip_path, bbox, tol=0.00008):
    """[{route, name, lines:[[ [lon,lat], ... ], ...]}] clipped to bbox. Empty if the feed has no shapes."""
    with zipfile.ZipFile(zip_path) as z:
        names = set(z.namelist())
        if "shapes.txt" not in names:
            return []
        routes = {r["route_id"]: (r.get("route_short_name") or r.get("route_long_name") or r["route_id"])
                  for r in _read(z, "routes.txt")}
        shape_route = {}
        for t in _read(z, "trips.txt"):
            if t.get("shape_id"):
                shape_route.setdefault(t["shape_id"], t["route_id"])
        pts = {}
        for p in _read(z, "shapes.txt"):
            pts.setdefault(p["shape_id"], []).append(
                (int(float(p["shape_pt_sequence"])), float(p["shape_pt_lon"]), float(p["shape_pt_lat"])))
    clip = box(*bbox)
    by_route = {}
    seen = set()
    for sid, ps in pts.items():
        ps.sort()
        if len(ps) < 2:
            continue
        line = LineString([(x, y) for _, x, y in ps]).intersection(clip)
        if line.is_empty:
            continue
        line = line.simplify(tol)
        parts = [line] if line.geom_type == "LineString" else [g for g in getattr(line, "geoms", []) if g.geom_type == "LineString"]
        rid = shape_route.get(sid, "?")
        for g in parts:
            coords = [[round(x, 5), round(y, 5)] for x, y in g.coords]
            key = (rid, tuple(map(tuple, coords[:3])), len(coords))
            if len(coords) < 2 or key in seen:
                continue
            seen.add(key)
            by_route.setdefault(rid, []).append(coords)
    return [{"route": rid, "name": routes.get(rid, rid), "lines": lines} for rid, lines in by_route.items()]
