import unittest

from findit import surplus
from findit.geom import to_shape

CSV = """Parent Case,Local Agency Type,Local Agency,APN,Date Notice Issued,NOA Due Date,NOA Status,Notice Website Link,Consolidated Sites,Address,City,Zip,x,y,Parcel Size (Gross Acres),General Plan/Zoning,Existing Use/Vacancy,Notice Contact Information- Concatenated,Additional Info
SLA0001,City,Santa Ana,405-262-25,02-20-2026,04-20-2026,Archive,,A,917 N. Bristol Street, Santa Ana ,92701,-117.884683,33.753106,"9,005 SF",Open Space with Commercial Option ,Vacant ,"Jane Doe,jane@example.gov,City",
SLA0002,City,Orange Cove,000-000-00,01-01-2025,03-01-2025,Archive,,N/A,1 Main St,Orange Cove,93646,-119.3,36.6,0.5,R-1,Vacant,"x",
SLA0003,District,OCTA,N/A,01-01-2025,03-01-2025,Active,https://example.org/notice,N/A,Lot B,Orange,92866,-117.85,33.79,,PF,Parking,"y",
"""


class ParseAcres(unittest.TestCase):
    def test_square_feet_and_acres(self):
        self.assertAlmostEqual(surplus.parse_acres("9,005 SF"), 0.2067, places=4)
        self.assertEqual(surplus.parse_acres("0.26"), 0.26)
        self.assertEqual(surplus.parse_acres("6.481"), 6.481)
        self.assertEqual(surplus.parse_acres("2 acres"), 2.0)

    def test_blank_and_text(self):
        self.assertIsNone(surplus.parse_acres(""))
        self.assertIsNone(surplus.parse_acres("see notice"))
        self.assertIsNone(surplus.parse_acres(None))


class Rows(unittest.TestCase):
    def test_contact_column_is_dropped(self):
        rows = surplus.read_rows(CSV)
        self.assertEqual(len(rows), 3)
        self.assertNotIn("Notice Contact Information- Concatenated", rows[0])
        self.assertFalse(any("jane@example.gov" in v for v in rows[0].values()))

    def test_city_match_is_exact(self):
        rows = surplus.read_rows(CSV)
        self.assertEqual(len(surplus.rows_for_city(rows, "SANTA ANA")), 1)
        self.assertEqual(len(surplus.rows_for_city(rows, "ORANGE")), 1)  # Orange, not Orange Cove
        self.assertEqual(surplus.rows_for_city(rows, "ORANGE")[0]["Local Agency"], "OCTA")


class ToSite(unittest.TestCase):
    def test_pseudo_site_fields(self):
        row = surplus.rows_for_city(surplus.read_rows(CSV), "SANTA ANA")[0]
        s = surplus.to_site(row, geometry={"rings": [[[-117.885, 33.753], [-117.884, 33.753], [-117.884, 33.754], [-117.885, 33.753]]]})
        a = s["attributes"]
        self.assertEqual(a["Assessor_Parcel_Number"], "405-262-25")
        self.assertAlmostEqual(a["HE_Acres"], 0.2067, places=4)
        self.assertTrue(a["HE_Publicly_Owned"].startswith("YES - Santa Ana"))
        self.assertIn("Archive", a["HE_Status"])
        self.assertFalse(a["SLA_APPROX_OUTLINE"])
        self.assertIsNone(a["Low_Income_HE_Capacity"])

    def test_approximate_circle_when_no_parcel(self):
        row = surplus.rows_for_city(surplus.read_rows(CSV), "ORANGE")[0]
        s = surplus.to_site(row)
        self.assertTrue(s["attributes"]["SLA_APPROX_OUTLINE"])
        self.assertIsNone(s["attributes"]["Assessor_Parcel_Number"])
        shape = to_shape(s["geometry"])
        self.assertTrue(shape.is_valid and shape.area > 0)
        self.assertTrue(shape.contains(to_shape({"x": -117.85, "y": 33.79})))

    def test_circle_area_matches_listed_acres(self):
        rings = surplus.circle_rings(-117.9, 33.7, 1.0)
        from findit.geom import to_feet
        area_acres = to_feet(to_shape({"rings": rings})).area / 43560
        self.assertAlmostEqual(area_acres, 1.0, delta=0.06)  # a 24-gon is a bit smaller than its circle


if __name__ == "__main__":
    unittest.main()
