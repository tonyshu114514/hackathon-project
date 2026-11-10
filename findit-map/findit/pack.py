"""Pack the page payload: shared text table plus index arrays for checks and pathway tests (lossless).

Used by build.py for site/index.html and by refresh_demo.py for demo/index.html. No GIS dependencies.
"""
import copy


def pack_payload(payload):
    """A smaller copy of the payload for the page; data/results.json keeps the readable form.

    Checks and pathway tests repeat the same few hundred sentences and the same keys thousands of times. Each distinct
    string goes into one shared table (pathway_texts) and each check or test becomes a short array of indexes:
        check -> [name, status, detail, source]          test -> [name, detail, status] (+ [1] when it is an ASSUMPTION)
    The page rebuilds the original objects at load (see "packed" in map_template.html), so nothing else changes.
    """
    if payload.get("packed"):
        return payload
    p = copy.deepcopy(payload)
    texts = p.setdefault("pathway_texts", [])
    index = {t: i for i, t in enumerate(texts)}
    statuses = ["pass", "fail", "unknown", "caution", "info"]
    sidx = {s: i for i, s in enumerate(statuses)}

    def intern(v):
        v = "" if v is None else str(v)
        if v not in index:
            index[v] = len(texts)
            texts.append(v)
        return index[v]

    def stat(s):
        if s not in sidx:
            sidx[s] = len(statuses)
            statuses.append(s)
        return sidx[s]

    for c in p["cities"].values():
        for st in c["sites"]:
            st["checks"] = [[intern(k["name"]), stat(k["status"]), intern(k["detail"]), intern(k["source"])] for k in st["checks"]]
            for pw in st.get("pathways") or []:
                pw["tests"] = [[t["name"] if isinstance(t["name"], int) else intern(t["name"]),
                                t["detail"] if isinstance(t["detail"], int) else intern(t["detail"]), stat(t["status"])]
                               + ([1] if t.get("assumption") else []) for t in pw["tests"]]
    p["packed"] = {"version": 1, "statuses": statuses}
    return p



def unpack_payload(p):
    """Inverse of pack_payload, mirroring the page's loader; used by the tests."""
    if not p.get("packed"):
        return p
    p = copy.deepcopy(p)
    T, S = p["pathway_texts"], p["packed"]["statuses"]
    for c in p["cities"].values():
        for st in c["sites"]:
            st["checks"] = [{"name": T[a[0]], "status": S[a[1]], "detail": T[a[2]], "source": T[a[3]]} for a in st["checks"]]
            for pw in st.get("pathways") or []:
                pw["tests"] = [dict({"name": a[0], "detail": a[1], "status": S[a[2]]}, **({"assumption": True} if len(a) > 3 and a[3] else {})) for a in pw["tests"]]
    del p["packed"]
    return p
