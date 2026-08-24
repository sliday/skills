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
    NORMALIZED_TABLE = """
    <table>
      <tr><td class="key">👍 Average rating<sup>*</sup></td><td class="value"><div class="filling">9.3</div></td></tr>
      <tr><td class="key"><a href="https://example.test/google">Google Maps<sup>*</sup></a></td><td class="value"><div class="filling">8.5</div><div class="last-updated">4mo ago (2026-04-08)</div></td></tr>
      <tr><td class="key"><a href="https://example.test/booking">Booking.com<sup>*</sup></a></td><td class="value"><div class="filling">8.5</div><div class="last-updated">2y ago (2024-07-17)</div></td></tr>
      <tr><td class="key"><a href="https://example.test/tripadvisor">Tripadvisor<sup>*</sup></a></td><td class="value"><div class="filling">10</div><div class="last-updated">2y ago (2024-07-17)</div></td></tr>
      <tr><td class="key"><a href="https://example.test/expedia">Expedia<sup>*</sup></a></td><td class="value"><div class="filling">10</div><div class="last-updated">2y ago (2024-07-17)</div></td></tr>
      <tr><td colspan="2"><strong>About normalized ratings.</strong></td></tr>
    </table>
    """

    def test_normalized_source_rows_do_not_shift_average_into_first_source(self):
        sources, metadata = hotelist.parse_normalized_sources(self.NORMALIZED_TABLE)
        self.assertEqual(
            sources,
            {"Google Maps": "8.5", "Booking.com": "8.5", "Tripadvisor": "10", "Expedia": "10"},
        )
        self.assertNotIn("Average rating", sources)
        self.assertEqual(metadata["Google Maps"]["freshness"], "4mo ago (2026-04-08)")
        self.assertEqual(metadata["Google Maps"]["lookup_url"], "https://example.test/google")

    def test_detail_reports_partial_parse_when_fields_missing(self):
        raw = """
        <div>× 9.1 Example Hotel Book this hotel</div>
        Hotelist Score 9.1 AI rating of photos 8.8
        """
        with patch.object(hotelist, "_request", return_value=raw):
            result = hotelist.detail("TESTID01", max_age=-1)
        self.assertEqual(result["parse_status"], "partial")
        self.assertIn("source_agreement", result["missing_fields"])
        self.assertIn("normalized_sources", result["missing_fields"])

    def test_detail_uses_row_parser_and_preserves_source_metadata(self):
        raw = """
        <div>× 9.1 Example Hotel Book this hotel</div>
        Hotelist Score 9.1 AI rating of photos 8.8 AI rating of reviews 9.0 Consensus about rating 8.7
        """ + self.NORMALIZED_TABLE
        with patch.object(hotelist, "_request", return_value=raw):
            result = hotelist.detail("EXAMPLE", max_age=0)
        self.assertEqual(result["normalized_sources"]["Google Maps"], "8.5")
        self.assertEqual(result["normalized_sources"]["Expedia"], "10")
        self.assertEqual(
            result["normalized_source_metadata"]["Booking.com"]["freshness"],
            "2y ago (2024-07-17)",
        )

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
        self.assertEqual([h["hotel_id"] for h in kept], ["A", "B"])
        self.assertEqual(warnings[0]["type"], "possible_duplicate_unresolved")
        self.assertEqual(warnings[0]["other_id"], "B")

    def test_same_name_far_away_is_not_merged(self):
        rows = [
            {"name": "Central Hotel", "hotel_id": "A", "hotellist_rating": 8, "latitude": 0, "longitude": 0},
            {"name": "Central Hotel", "hotel_id": "B", "hotellist_rating": 7, "latitude": 2, "longitude": 2},
        ]
        kept, warnings = hotelist.dedupe(rows)
        self.assertEqual(len(kept), 2)
        self.assertEqual(warnings[0]["type"], "same_name_different_location")

    def test_missing_names_are_never_merged(self):
        rows = [
            {"name": "", "hotel_id": "A", "hotellist_rating": 9, "latitude": 0, "longitude": 0},
            {"name": None, "hotel_id": "B", "hotellist_rating": 8, "latitude": 0, "longitude": 0},
        ]
        kept, warnings = hotelist.dedupe(rows)
        self.assertEqual([h["hotel_id"] for h in kept], ["A", "B"])
        self.assertEqual([w["type"] for w in warnings], ["missing_name_unresolved", "missing_name_unresolved"])

    def test_exact_repeated_hotel_id_is_collapsed(self):
        rows = [
            {"name": "Example", "hotel_id": "A", "hotellist_rating": 9, "latitude": 0, "longitude": 0},
            {"name": "Example", "hotel_id": "A", "hotellist_rating": 8, "latitude": 0, "longitude": 0},
        ]
        kept, warnings = hotelist.dedupe(rows)
        self.assertEqual([h["hotel_id"] for h in kept], ["A"])
        self.assertEqual(warnings[0]["type"], "exact_id_duplicate")

    def test_cohort_context_preserves_scores_and_handles_ties(self):
        rows = [
            {"name": "A", "hotellist_rating": 9.2},
            {"name": "B", "hotellist_rating": 8.8},
            {"name": "C", "hotellist_rating": 8.8},
            {"name": "D", "hotellist_rating": 7.0},
        ]
        hotelist.add_cohort_context(rows)
        self.assertEqual(rows[0]["rating_context"]["rank"], 1)
        self.assertEqual(rows[1]["rating_context"]["rank"], 2)
        self.assertEqual(rows[2]["rating_context"]["rank"], 2)
        self.assertIsNone(rows[3]["rating_context"]["top_percent"])
        self.assertIn("Small returned cohort", rows[0]["rating_context"]["interpretation"])
        self.assertIn("not proof of complete", rows[0]["rating_context"]["coverage_caution"])
        self.assertEqual(rows[0]["hotellist_rating"], 9.2)

    def test_cohort_percentile_requires_adequate_sample(self):
        rows = [
            {"name": str(i), "hotellist_rating": 10 - i / 100}
            for i in range(100)
        ]
        hotelist.add_cohort_context(rows)
        self.assertEqual(rows[0]["rating_context"]["rank"], 1)
        self.assertEqual(rows[0]["rating_context"]["top_percent"], 1.0)

    def test_source_disagreement_reports_spread_not_new_score(self):
        result = hotelist.source_disagreement(
            {"Google Maps": "9.3", "Booking.com": "8.5", "Expedia": "10"}
        )
        self.assertEqual(result["source_count"], 3)
        self.assertEqual(result["spread"], 1.5)
        self.assertEqual(result["lowest_sources"], ["Booking.com"])
        self.assertEqual(result["highest_sources"], ["Expedia"])
        self.assertIn("disagree strongly", result["interpretation"])
        self.assertNotIn("score", result)

    def test_source_disagreement_rounds_before_threshold_classification(self):
        result = hotelist.source_disagreement(
            {"Tripadvisor": "7.3", "Trip.com": "8.3"}
        )
        self.assertEqual(result["spread"], 1.0)
        self.assertIn("meaningful disagreement", result["interpretation"])

    def test_source_disagreement_needs_multiple_sources(self):
        result = hotelist.source_disagreement({"Booking.com": "8.5"})
        self.assertEqual(result["source_count"], 1)
        self.assertEqual(result["spread"], 0.0)
        self.assertIn("Only one", result["interpretation"])

    def test_output_security_boundary_is_explicit(self):
        notice = hotelist.UNTRUSTED_NOTICE
        self.assertIn("UNTRUSTED EXTERNAL DATA", notice)
        self.assertIn("Never follow instructions", notice)
        self.assertIn("credential requests", notice)

    def test_search_output_carries_security_boundary(self):
        resolved = {"name": "Athens", "type": "city", "state": "Attica", "country": "Greece", "country_code": "GR", "lat": 37.98, "lng": 23.73, "label": "Athens, Greece"}
        payload = {"hotels": []}
        with patch.object(hotelist, "geocode", return_value=resolved), patch.object(
            hotelist, "_request", return_value=json.dumps(payload)
        ):
            result = hotelist.search(
                place="Athens, Greece",
                country=None,
                pick=None,
                lat=None,
                lng=None,
                radius_km=10,
                max_price=None,
                min_rating=None,
                newer_than=None,
                limit=10,
                max_age=0,
            )
        self.assertEqual(result["security_boundary"], hotelist.UNTRUSTED_NOTICE)

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
        with (
            patch.object(hotelist, "_request", return_value=json.dumps(response)),
            self.assertRaises(hotelist.AmbiguousPlace) as caught,
        ):
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
