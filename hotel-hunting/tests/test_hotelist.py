import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "hotelist.py"
spec = importlib.util.spec_from_file_location("hotelist_cli", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {MODULE_PATH}")
hotelist = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hotelist)


class HotelistTests(unittest.TestCase):
    def test_bbox_uses_requested_radius(self):
        lat_min, lat_max, lng_min, lng_max = hotelist._bbox(38.0, 23.7, 10)
        self.assertAlmostEqual(lat_max - lat_min, 20 / 111, places=5)
        self.assertGreater(lng_max - lng_min, lat_max - lat_min)

    def test_dedupe_flags_same_property_name(self):
        rows = [
            {
                "name": "Athens Capital Hotel",
                "hotel_id": "A",
                "hotellist_rating": 8.64,
                "latitude": 37.98,
                "longitude": 23.73,
            },
            {
                "name": "Athens Capital Hotel",
                "hotel_id": "B",
                "hotellist_rating": 8.35,
                "latitude": 37.9801,
                "longitude": 23.7301,
            },
        ]
        kept, warnings = hotelist.dedupe(rows)
        self.assertEqual([h["hotel_id"] for h in kept], ["A"])
        self.assertEqual(warnings[0]["type"], "possible_duplicate")
        self.assertEqual(warnings[0]["other_id"], "B")

    def test_same_name_far_away_is_not_merged(self):
        rows = [
            {"name": "Central Hotel", "hotel_id": "A", "hotellist_rating": 8, "latitude": 0, "longitude": 0},
            {"name": "Central Hotel", "hotel_id": "B", "hotellist_rating": 7, "latitude": 2, "longitude": 2},
        ]
        kept, warnings = hotelist.dedupe(rows)
        self.assertEqual(len(kept), 2)
        self.assertEqual(warnings[0]["type"], "same_name_different_location")

    def test_ambiguous_bare_place_fails_with_candidates(self):
        response = {
            "features": [
                {
                    "properties": {"name": "Springfield", "type": "city", "state": "Illinois", "country": "United States", "countrycode": "US"},
                    "geometry": {"coordinates": [-89.65, 39.78]},
                },
                {
                    "properties": {"name": "Springfield", "type": "city", "state": "Massachusetts", "country": "United States", "countrycode": "US"},
                    "geometry": {"coordinates": [-72.59, 42.10]},
                },
            ]
        }
        with patch.object(hotelist, "_request", return_value=json.dumps(response)):
            with self.assertRaises(hotelist.AmbiguousPlace) as caught:
                hotelist.geocode("Springfield")
        self.assertEqual(len(caught.exception.candidates), 2)

    def test_country_disambiguates(self):
        response = {
            "features": [
                {
                    "properties": {"name": "Athens", "type": "city", "state": "Attica", "country": "Greece", "countrycode": "GR"},
                    "geometry": {"coordinates": [23.72, 37.98]},
                },
                {
                    "properties": {"name": "Athens", "type": "city", "state": "Georgia", "country": "United States", "countrycode": "US"},
                    "geometry": {"coordinates": [-83.37, 33.95]},
                },
            ]
        }
        with patch.object(hotelist, "_request", return_value=json.dumps(response)):
            result = hotelist.geocode("Athens", country="GR")
        self.assertEqual(result["country_code"], "GR")


if __name__ == "__main__":
    unittest.main()
