import unittest

from findit.validate import validate_sites

SQ = [[[-117.90, 33.70], [-117.899, 33.70], [-117.899, 33.701], [-117.90, 33.701], [-117.90, 33.70]]]
FIELDS = {"apn": "APN", "lower": "LOW", "moderate": "MOD", "above": "ABV", "total": "TOT"}


def feat(oid, apn="123-456-78", rings=SQ, **attrs):
    a = {"OBJECTID": oid, "APN": apn, "LOW": None, "MOD": None, "ABV": None, "TOT": None}
    a.update(attrs)
    return {"attributes": a, "geometry": {"rings": rings} if rings else None}


class Validate(unittest.TestCase):
    def test_drops_records_without_outline(self):
        kept, flags, report = validate_sites([feat(1, rings=None), feat(2)], FIELDS, "OBJECTID")
        self.assertEqual(len(kept), 1)
        self.assertEqual(report["dropped"], 1)
        self.assertEqual(report["counts"]["no_geometry"], 1)

    def test_duplicate_apn_keeps_largest_capacity(self):
        kept, flags, report = validate_sites([feat(1, TOT=10), feat(2, TOT=50)], FIELDS, "OBJECTID")
        self.assertEqual([s["attributes"]["OBJECTID"] for s in kept], [2])
        self.assertEqual(report["counts"]["duplicate_apn"], 1)

    def test_same_outline_merged_once_with_capacities_added(self):
        a = feat(1, apn="590-171-02", LOW=0, MOD=71, ABV=639, TOT=710, HE_Existing_Use="Vacant")
        b = feat(2, apn="590-171-03", LOW=289, MOD=0, ABV=0, TOT=289)
        kept, flags, report = validate_sites([a, b], FIELDS, "OBJECTID")
        self.assertEqual(len(kept), 1)
        k = kept[0]["attributes"]
        self.assertEqual(k["OBJECTID"], 1)  # the listing with more total capacity is kept
        self.assertEqual((k["LOW"], k["MOD"], k["ABV"], k["TOT"]), (289, 71, 639, 999))
        self.assertEqual(k["HE_Existing_Use"], "Vacant")
        self.assertEqual(report["counts"]["duplicate_outline"], 1)
        self.assertEqual(report["dropped"], 1)

    def test_same_outline_carries_existing_use_to_the_kept_listing(self):
        a = feat(1, apn="590-171-02", TOT=10, HE_Existing_Use="Parking")
        b = feat(2, apn="590-171-03", TOT=50)
        kept, flags, report = validate_sites([a, b], FIELDS, "OBJECTID")
        self.assertEqual([s["attributes"]["OBJECTID"] for s in kept], [2])
        self.assertEqual(kept[0]["attributes"]["HE_Existing_Use"], "Parking")
        self.assertEqual(kept[0]["attributes"]["TOT"], 60)

    def test_different_outlines_both_kept(self):
        other = [[[-117.80, 33.70], [-117.799, 33.70], [-117.799, 33.701], [-117.80, 33.701], [-117.80, 33.70]]]
        kept, flags, report = validate_sites([feat(1, apn="111-111-11"), feat(2, apn="222-222-22", rings=other)],
                                             FIELDS, "OBJECTID")
        self.assertEqual(len(kept), 2)
        self.assertNotIn("duplicate_outline", report["counts"])

    def test_negative_capacity_blanked_and_flagged(self):
        kept, flags, report = validate_sites([feat(1, LOW=-5, TOT=10)], FIELDS, "OBJECTID")
        self.assertIsNone(kept[0]["attributes"]["LOW"])
        self.assertEqual(report["counts"]["negative_capacity"], 1)

    def test_pending_status_is_a_flag_not_a_drop(self):
        kept, flags, report = validate_sites([feat(1, HE_Status="Pending Project")], FIELDS, "OBJECTID")
        self.assertEqual(len(kept), 1)
        f = next(x for x in flags["1"] if x["code"] == "pending_project")
        self.assertEqual(f["level"], "flag")

    def test_short_apn_warns(self):
        kept, flags, report = validate_sites([feat(1, apn="12")], FIELDS, "OBJECTID")
        self.assertEqual(report["counts"]["bad_apn"], 1)
        self.assertEqual(len(kept), 1)


if __name__ == "__main__":
    unittest.main()
