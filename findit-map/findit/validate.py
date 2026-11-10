"""Validate housing-element site records before any scoring.

Runs once per city on the raw site features. It fixes only what is safe to fix (drops records with no
usable shape, keeps one record per APN, merges records that share one outline, blanks impossible capacity
values) and records every issue,
so the page can show what was changed and which sites need a closer look.

Issue levels:
  error   the record was dropped or a value was blanked
  warning the record is kept but a value looks wrong
  flag    the record is valid but a planner should know before choosing it (e.g. a pending project)
"""
import re

from findit.geom import to_feet, to_shape

CAPACITY_KEYS = ("lower", "moderate", "above", "total")


def _num(v):
    try:
        x = float(str(v).replace(",", ""))
        return x if x == x else None
    except (TypeError, ValueError):
        return None


def _digits(s):
    return re.sub(r"\D", "", str(s or ""))


def validate_sites(sites, fields, oid, boundary=None, acres_tolerance=0.5, boundary_buffer_deg=0.005):
    """Return (kept_sites, flags_by_site_id, report).

    fields: {"apn": ..., "lower": ..., "moderate": ..., "above": ..., "total": ...} attribute names (None if absent).
    boundary: the city's shapely boundary, or None to skip the location check.
    """
    flags = {}
    report = {"input": len(sites), "dropped": 0, "counts": {}}

    def add(key, level, code, msg):
        flags.setdefault(key, []).append({"level": level, "code": code, "msg": msg})
        report["counts"][code] = report["counts"].get(code, 0) + 1

    kept, by_apn, by_outline = [], {}, {}
    near_city = boundary.buffer(boundary_buffer_deg) if boundary is not None else None
    for s in sites:
        a = s.get("attributes", {})
        key = str(a.get(oid))
        shape = to_shape(s.get("geometry"))

        # Geometry: no shape means no map, no overlap checks and no score.
        if shape is None or shape.is_empty or shape.area == 0:
            add(key, "error", "no_geometry", "No usable site outline; dropped.")
            report["dropped"] += 1
            continue

        # APN: needed to join year built, zoning and HCD permits.
        apn = _digits(a.get(fields.get("apn"))) if fields.get("apn") else ""
        if len(apn) < 8:
            add(key, "warning", "bad_apn", f"APN '{a.get(fields.get('apn'))}' is missing or short; parcel data cannot be joined.")

        # Duplicate APN: keep the record with the most listed capacity, drop the rest.
        if len(apn) >= 8 and apn in by_apn:
            prev = by_apn[apn]
            cap = lambda x: _num(x["attributes"].get(fields.get("total"))) or 0
            winner, loser = (s, prev) if cap(s) > cap(prev) else (prev, s)
            lkey = str(loser["attributes"].get(oid))
            add(lkey, "error", "duplicate_apn", f"Same APN as site {winner['attributes'].get(oid)}; dropped to avoid counting it twice.")
            report["dropped"] += 1
            if winner is s:
                kept[kept.index(prev)] = s
                by_apn[apn] = s
            continue

        # Duplicate outline: some inventories list one site under two APNs with the same outline, splitting its
        # capacity by income level. Count the land once: keep the record with the most total capacity, add the
        # other's capacities to it, carry over a missing existing use, and drop the other.
        okey = shape.normalize().wkb
        if okey in by_outline:
            prev = by_outline[okey]
            cap = lambda x: _num(x["attributes"].get(fields.get("total"))) or 0
            winner, loser = (s, prev) if cap(s) > cap(prev) else (prev, s)
            wa, la = winner["attributes"], loser["attributes"]
            for k in CAPACITY_KEYS:
                f = fields.get(k)
                vals = [v for v in (_num(wa.get(f)), _num(la.get(f))) if f and v is not None and v >= 0]
                if vals:
                    wa[f] = sum(vals)
            for f in ("HE_Existing_Use", "HE_Use_Source"):
                if not wa.get(f) and la.get(f):
                    wa[f] = la[f]
            wkey, lkey = str(wa.get(oid)), str(la.get(oid))
            lapn, wapn = la.get(fields.get("apn")), wa.get(fields.get("apn"))
            add(lkey, "error", "duplicate_outline",
                f"Same outline as site {wkey} (APN {wapn}); dropped and its capacity added to that site so the land is counted once.")
            add(wkey, "warning", "merged_outline",
                f"Also listed under APN {lapn} with the same outline; capacities of both listings are added here.")
            report["dropped"] += 1
            if winner is s:
                kept[kept.index(prev)] = s
                by_outline[okey] = s
                papn = _digits(prev["attributes"].get(fields.get("apn"))) if fields.get("apn") else ""
                if by_apn.get(papn) is prev:
                    by_apn[papn] = s
            if len(apn) >= 8 and apn not in by_apn:
                by_apn[apn] = winner
            continue
        by_outline[okey] = s
        if len(apn) >= 8:
            by_apn[apn] = s

        # Capacity: negative values are impossible; parts larger than the total are inconsistent.
        caps = {k: _num(a.get(fields[k])) if fields.get(k) else None for k in CAPACITY_KEYS}
        for k, v in caps.items():
            if v is not None and v < 0:
                a[fields[k]] = None
                add(key, "error", "negative_capacity", f"{k.title()} capacity was {v:g}; blanked.")
        parts = sum(v for k, v in caps.items() if k != "total" and v and v > 0)
        if caps["total"] is not None and caps["total"] > 0 and parts > caps["total"] + 0.5:
            add(key, "warning", "capacity_mismatch",
                f"Income-level capacities add to {parts:g} but total capacity is {caps['total']:g}.")
        if all(v is None for v in caps.values()):
            add(key, "warning", "no_capacity", "No capacity listed by income level; the capacity term is left out of its score.")

        # Acreage: compare the outline's area with the acreage the city listed.
        listed = _num(a.get("HE_Acres"))
        mapped = to_feet(shape).area / 43560
        if listed and listed > 0 and abs(mapped - listed) / listed > acres_tolerance:
            add(key, "warning", "acres_mismatch",
                f"Outline measures {mapped:.2f} acres but the city listed {listed:.2f}; the site may be part of a "
                "consolidated site or the outline may be off.")

        # Location: the site should sit inside (or just at the edge of) its city.
        if near_city is not None and not near_city.contains(shape.representative_point()):
            add(key, "warning", "outside_city", "Site falls outside the city boundary.")

        # Status: a pending project means the site is already spoken for, even if it is still listed.
        status = str(a.get("HE_Status") or "").strip()
        if "pending" in status.lower():
            add(key, "flag", "pending_project",
                f"City lists this site as '{status}': a project is already proposed here.")

        kept.append(s)

    report["kept"] = len(kept)
    return kept, flags, report
