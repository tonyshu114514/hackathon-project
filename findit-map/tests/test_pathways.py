import unittest

from findit import pathways


def site(**kw):
    base = {"zoning_code": None, "acres": 1.0, "fire_vh": False, "sfha": False, "cleanup_on_site": False,
            "vacant": None, "publicly_owned": None, "likely_used": False, "pending": False}
    base.update(kw)
    return base


def by_id(results, id_):
    return next(r for r in results if r["id"] == id_)


def test_named(result, name):
    return next(t for t in result["tests"] if t["name"] == name)


class ZoningFamily(unittest.TestCase):
    def test_exact_codes(self):
        self.assertEqual(pathways.zoning_family("1110"), ("single_family", "Single Family Residential", True))
        self.assertEqual(pathways.zoning_family("7777"), ("specific_plan", "Specific Plan", True))

    def test_subcodes_match_their_family(self):
        fam, label, exact = pathways.zoning_family("1223")
        self.assertEqual(fam, "commercial")
        self.assertFalse(exact)
        self.assertIn("family", label)
        self.assertEqual(pathways.zoning_family("1122")[0], "multi_family")
        self.assertEqual(pathways.zoning_family("1113")[0], "single_family")

    def test_blank_and_unknown(self):
        self.assertEqual(pathways.zoning_family(""), (None, None, False))
        self.assertEqual(pathways.zoning_family(None), (None, None, False))
        self.assertEqual(pathways.zoning_family("5555")[0], "unknown")


class Screening(unittest.TestCase):
    def test_never_claims_yes(self):
        # Even a perfect-looking lot has facts no dataset holds, so the result is unknown, not a yes.
        res = pathways.screen(site(zoning_code="1110", vacant=True))
        for r in res:
            self.assertIn(r["result"], ("no", "unknown"))
            self.assertTrue(r["sources"])
            self.assertTrue(all(s["checked"] for s in r["sources"]))

    def test_sb9_needs_single_family_zone(self):
        res = pathways.screen(site(zoning_code="1223"))
        sb9 = by_id(res, "sb9")
        self.assertEqual(sb9["result"], "no")
        self.assertEqual(test_named(sb9, "Single-family residential zone")["status"], "fail")
        sb9 = by_id(pathways.screen(site(zoning_code="1110")), "sb9")
        self.assertEqual(test_named(sb9, "Single-family residential zone")["status"], "pass")
        self.assertEqual(sb9["result"], "unknown")

    def test_hazard_fails_every_law(self):
        for key in ("fire_vh", "sfha", "cleanup_on_site"):
            res = pathways.screen(site(zoning_code="1600", **{key: True}))
            for r in res:
                self.assertEqual(r["result"], "no", (key, r["id"]))

    def test_unknown_hazard_layer_stays_unknown(self):
        res = pathways.screen(site(zoning_code="1600", fire_vh=None))
        ab = by_id(res, "ab2011")
        self.assertEqual(test_named(ab, "Very high fire hazard severity zone")["status"], "unknown")
        self.assertEqual(ab["result"], "unknown")

    def test_sb684_size_and_zoning(self):
        res = pathways.screen(site(zoning_code="1120", acres=6.0))
        self.assertEqual(test_named(by_id(res, "sb684"), "Lot under 5 acres")["status"], "fail")
        res = pathways.screen(site(zoning_code="1110", acres=0.5, vacant=False))
        self.assertEqual(by_id(res, "sb684")["result"], "no")
        res = pathways.screen(site(zoning_code="1110", acres=0.5, vacant=True))
        self.assertEqual(test_named(by_id(res, "sb684"), "Zoned for multifamily residential use")["status"], "pass")
        res = pathways.screen(site(zoning_code="1110", acres=0.5, vacant=None))
        self.assertEqual(test_named(by_id(res, "sb684"), "Zoned for multifamily residential use")["status"], "unknown")

    def test_ab2011_zoning(self):
        self.assertEqual(test_named(by_id(pathways.screen(site(zoning_code="1222")), "ab2011"),
                                    "Zone allows office, retail or parking")["status"], "pass")
        self.assertEqual(test_named(by_id(pathways.screen(site(zoning_code="1120")), "ab2011"),
                                    "Zone allows office, retail or parking")["status"], "fail")
        self.assertEqual(test_named(by_id(pathways.screen(site(zoning_code="1300")), "ab2011"),
                                    "Zone allows office, retail or parking")["status"], "unknown")

    def test_sb4_ownership(self):
        res = pathways.screen(site(zoning_code="1110", publicly_owned=True))
        self.assertEqual(by_id(res, "sb4")["result"], "no")
        res = pathways.screen(site(zoning_code="1110", publicly_owned=None))
        self.assertEqual(test_named(by_id(res, "sb4"), "Owned by a religious institution or independent college")["status"], "unknown")

    def test_used_site_fails_activity(self):
        res = pathways.screen(site(zoning_code="1600", likely_used=True))
        for r in res:
            self.assertEqual(test_named(r, "Site activity")["status"], "fail")
            self.assertEqual(r["result"], "no")

    def test_assumptions_are_marked(self):
        res = pathways.screen(site(zoning_code="1110"))
        urban = test_named(by_id(res, "sb9"), "Urbanized area")
        self.assertTrue(urban.get("assumption"))
        self.assertIn("ASSUMPTION", urban["detail"])


if __name__ == "__main__":
    unittest.main()
