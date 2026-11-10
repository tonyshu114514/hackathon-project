import unittest

from findit import apr, permits


def act(stages, cat="5+", year=2023, units=None, project=None):
    return {"year": year, "stages": stages, "unit_cat": cat, "project": project,
            "units": units or {"entitled": 0, "permitted": 0, "completed": 0}}


class RowUnits(unittest.TestCase):
    def test_sums_by_stage(self):
        row = {"VLOW_INCOME_DR": "3", "LOW_INCOME_NDR": 2, "BP_ABOVE_MOD_INCOME": "10", "CO_MOD_INCOME_DR": "1",
               "EXTR_LOW_INCOME_UNITS": "99", "NOTES": "x"}
        self.assertEqual(permits.row_units(row), {"entitled": 5, "permitted": 10, "completed": 1})


class Grade(unittest.TestCase):
    def test_none(self):
        g = permits.grade([])
        self.assertEqual(g["level"], "none")
        self.assertFalse(g["likely_used"])

    def test_permit_issued_is_strong(self):
        g = permits.grade([act(["permit issued"], units={"entitled": 0, "permitted": 24, "completed": 0})])
        self.assertEqual((g["level"], g["likely_used"], g["stage"], g["units"]), ("strong", True, "permit issued", 24))

    def test_entitled_only_is_moderate(self):
        g = permits.grade([act(["entitled"], units={"entitled": 40, "permitted": 0, "completed": 0})])
        self.assertEqual((g["level"], g["likely_used"], g["units"]), ("moderate", True, 40))

    def test_adu_only_is_weak_and_not_used(self):
        g = permits.grade([act(["permit issued"], cat="ADU", units={"entitled": 0, "permitted": 1, "completed": 0}),
                           act(["completed"], cat="ADU", year=2024)])
        self.assertEqual(g["level"], "weak")
        self.assertFalse(g["likely_used"])
        self.assertTrue(g["adu_only"])
        self.assertIn("accessory dwelling", permits.describe(g, 2021))

    def test_adu_plus_main_project_counts_the_project(self):
        g = permits.grade([act(["permit issued"], cat="ADU"), act(["entitled"], cat="5+", units={"entitled": 12, "permitted": 0, "completed": 0})])
        self.assertEqual((g["level"], g["stage"], g["units"]), ("moderate", "entitled", 12))
        self.assertEqual(g["categories"], ["5+", "ADU"])

    def test_row_without_stage_dates_is_moderate(self):
        g = permits.grade([act([], cat="2 to 4")])
        self.assertEqual(g["level"], "moderate")
        self.assertEqual(g["stage"], "reported")

    def test_describe_grammar(self):
        g = permits.grade([act(["permit issued"], cat="ADU", units={"entitled": 0, "permitted": 1, "completed": 0})])
        self.assertIn("(1 unit)", permits.describe(g, 2021))


class IndexByApn(unittest.TestCase):
    def test_entries_carry_category_units_and_project(self):
        rows = [{"APN": "123-456-78", "PRIOR_APN": "", "YEAR": "2022", "UNIT_CAT": "ADU", "PROJECT_NAME": "Casita",
                 "ENT_APPROVE_DT1": "", "BP_ISSUE_DT1": "2022-03-01", "CO_ISSUE_DT1": "", "BP_ABOVE_MOD_INCOME": "1"}]
        idx, info = apr.index_by_apn(rows)
        e = idx["12345678"][0]
        self.assertEqual(e["unit_cat"], "ADU")
        self.assertEqual(e["units"]["permitted"], 1)
        self.assertEqual(e["project"], "Casita")
        self.assertEqual(e["stages"], ["permit issued"])


if __name__ == "__main__":
    unittest.main()
