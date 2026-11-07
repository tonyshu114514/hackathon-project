from pyproj import Transformer
from shapely.geometry import LinearRing, MultiPolygon, Point, Polygon
from shapely.ops import transform, unary_union

# EPSG:2230 = NAD83 / California zone 6 (US feet), the county's native projection.
_to_ft = Transformer.from_crs(4326, 2230, always_xy=True).transform


def to_shape(g):
    if not g:
        return None
    if "x" in g:
        return Point(g["x"], g["y"])
    rings = [r for r in g.get("rings", []) if len(r) >= 4]
    if not rings:
        return None
    shells, holes = [], []
    for r in rings:
        (holes if LinearRing(r).is_ccw else shells).append(r)
    if not shells:
        shells, holes = holes, []
    polys = [Polygon(s) for s in shells]
    for h in holes:
        hp = Polygon(h).representative_point()
        for i, p in enumerate(polys):
            if p.contains(hp):
                polys[i] = Polygon(p.exterior.coords, [list(x.coords) for x in p.interiors] + [h])
                break
    shape = polys[0] if len(polys) == 1 else MultiPolygon(polys)
    return shape if shape.is_valid else shape.buffer(0)


def to_feet(shape):
    return transform(_to_ft, shape)


def union(shapes):
    shapes = [s for s in shapes if s is not None and not s.is_empty]
    return unary_union(shapes) if shapes else None


def to_rings(shape, ndigits=6):
    polys = [shape] if shape.geom_type == "Polygon" else list(getattr(shape, "geoms", []))
    out = []
    for p in polys:
        if p.geom_type != "Polygon":
            continue
        out.append([[round(x, ndigits), round(y, ndigits)] for x, y in p.exterior.coords])
    return out


def to_polys(shape, tol=0.0, ndigits=5):
    """Leaflet multipolygon: [[outer, hole, ...], ...] as [lon, lat] pairs."""
    if shape is None or shape.is_empty:
        return []
    if tol:
        shape = shape.simplify(tol, preserve_topology=True)
    polys = [shape] if shape.geom_type == "Polygon" else [g for g in getattr(shape, "geoms", []) if g.geom_type == "Polygon"]
    out = []
    for p in polys:
        rings = [p.exterior] + list(p.interiors)
        out.append([[[round(x, ndigits), round(y, ndigits)] for x, y in r.coords] for r in rings])
    return out
