import unittest

from findit.pack import pack_payload, unpack_payload


def payload():
    tests = [{"name": 0, "detail": 1, "status": "fail"}, {"name": "Lot size", "detail": "Unknown lot size", "status": "unknown",
                                                          "assumption": True}]
    site = {"id": "1", "checks": [{"name": "Flood", "status": "pass", "detail": "No mapped flood zone.", "source": "flood"},
                                  {"name": "Fire", "status": "caution", "detail": "Zone present.", "source": "fire_lra,fire_sra"}],
            "pathways": [{"id": "sb9", "result": "no", "passes": 0, "fails": 1, "unknowns": 1, "tests": tests}]}
    return {"cities": {"x": {"sites": [site]}}, "pathway_texts": ["Zoning", "Not single-family"]}


class Pack(unittest.TestCase):
    def test_round_trip_is_lossless(self):
        p = payload()
        packed = pack_payload(p)
        self.assertTrue(packed["packed"])
        self.assertIsInstance(packed["cities"]["x"]["sites"][0]["checks"][0], list)
        back = unpack_payload(packed)
        site, orig = back["cities"]["x"]["sites"][0], p["cities"]["x"]["sites"][0]
        self.assertEqual(site["checks"], orig["checks"])
        texts = back["pathway_texts"]
        name = lambda v: texts[v] if isinstance(v, int) else v
        got = [(name(t["name"]), name(t["detail"]), t["status"], t.get("assumption", False)) for t in site["pathways"][0]["tests"]]
        self.assertEqual(got, [("Zoning", "Not single-family", "fail", False), ("Lot size", "Unknown lot size", "unknown", True)])

    def test_input_is_not_modified_and_packing_twice_is_safe(self):
        p = payload()
        packed = pack_payload(p)
        self.assertIsInstance(p["cities"]["x"]["sites"][0]["checks"][0], dict)
        self.assertIs(pack_payload(packed), packed)


if __name__ == "__main__":
    unittest.main()
