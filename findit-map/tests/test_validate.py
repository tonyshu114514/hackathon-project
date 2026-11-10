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
