from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "jet.py"
spec = importlib.util.spec_from_file_location("jet_cli", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {MODULE_PATH}")
jet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jet)


def fixture():
    return {
        "restaurants": [
            {"id": 1, "name": "Pizza\u00a0One", "uniqueName": "pizza-one",
             "rating": {"starRating": 4.5, "count": 20},
             "deliveryEtaMinutes": {"rangeLower": 30, "rangeUpper": 45},
             "isOpenNowForDelivery": True, "deliveryCost": 0, "minimumDeliveryValue": 18,
             "deals": [{"offerType": "Percent", "description": "30% off"}]},
            {"id": "2", "name": "Two", "uniqueName": "two",
             "rating": {"starRating": 5, "count": 10},
             "deliveryEtaMinutes": {"rangeLower": 15, "rangeUpper": 25},
             "isOpenNowForDelivery": False, "deliveryCost": 1.99, "minimumDeliveryValue": 9.99,
             "deals": [{"offerType": "StampCard", "description": ""}]},
            {"id": 3, "name": "Three", "isOpenNowForDelivery": True, "deals": []},
        ],
        "deliveryFees": {"restaurants": {"1": {"minimumOrderValue": 1800, "bands": [
            {"minimumAmount": 20000, "fee": 0}, {"minimumAmount": 1800, "fee": 1200},
            {"minimumAmount": 10000, "fee": 500},
        ]}}},
        "filters": {"free_delivery": {"restaurantIds": [2]},
                    "loyalty-offer-test": {"restaurantIds": [3]},
                    "reminder_voucher": {"restaurantIds": [3]},
                    "repeat-offer-test": {"restaurantIds": [3]}},
        "promotedPlacement": {"filteredSearchPromotedLimit": 0, "rankedIds": ["1"],
                              "restaurants": {"1": {"restaurantId": "1", "defaultPromoted": True}}},
    }


class UrlTests(unittest.TestCase):
    def test_hosts_and_postcodes(self):
        self.assertEqual(jet.discovery_url("UK", "EC4M 7RF"),
                         "https://uk.api.just-eat.io/discovery/uk/restaurants/enriched/bypostcode/EC4M7RF")
        for country in ("es", "ie", "it", "dk", "no"):
            self.assertTrue(jet.discovery_url(country, "1234").startswith("https://i18n.api.just-eat.io/"))
        for country in ("de", "at", "pl", "nl", "be", "lu", "bg"):
            self.assertTrue(jet.discovery_url(country, "00-024").startswith(
                "https://rest.api.eu-central-1.production.jet-external.com/"))
        self.assertTrue(jet.discovery_url("pl", "00-024").endswith("/00-024"))
        self.assertTrue(jet.discovery_url("nl", "1234 AB/a?").endswith("/1234%20AB%2Fa%3F"))

    def test_currency(self):
        for country, currency in (("UK", "GBP"), ("pl", "PLN"), ("dk", "DKK"),
                                  ("no", "NOK"), ("de", "EUR"), ("es", "EUR")):
            self.assertEqual(jet.currency_for(country), currency)


class FeeTests(unittest.TestCase):
    def setUp(self):
        data = fixture()
        self.venue = data["restaurants"][0]
        self.fees = data["deliveryFees"]["restaurants"]["1"]

    def test_bands_are_minor_units_and_not_list_cost(self):
        for basket, expected in ((1800, 1200), (6000, 1200), (10000, 500), (19999, 500), (20000, 0)):
            result = jet.delivery_fee(self.venue, self.fees, basket)
            self.assertEqual(result["fee"], expected)
            self.assertFalse(result["fallback"])
        self.assertEqual(jet.format_fee(jet.delivery_fee(self.venue, self.fees, 6000), "PLN", 6000), "12.00 PLN")

    def test_below_minimum(self):
        result = jet.delivery_fee(self.venue, self.fees, 1799)
        self.assertTrue(result["below_minimum"])
        self.assertIsNone(result["fee"])
        self.assertEqual(jet.format_fee(result, "PLN", 1799), "below minimum order")

    def test_range_without_basket(self):
        result = jet.delivery_fee(self.venue, self.fees)
        self.assertEqual((result["minimum"], result["low"], result["high"]), (1800, 0, 1200))
        self.assertEqual(jet.format_fee(result, "PLN", None), "0.00 PLN to 12.00 PLN")

    def test_missing_bands_fallback_converts_major_units(self):
        venue = fixture()["restaurants"][1]
        for fees in ({}, {"bands": []}):
            result = jet.delivery_fee(venue, fees, 6000)
            self.assertEqual((result["minimum"], result["fee"]), (999, 199))
            self.assertIn("fee from list, may be the cheapest band", jet.format_fee(result, "EUR", 6000))
        result = jet.delivery_fee(venue, {"minimumOrderValue": 1800}, 1000)
        self.assertEqual(result["minimum"], 1800)
        self.assertTrue(result["below_minimum"])

    def test_unknown_and_uncovered_basket(self):
        self.assertIsNone(jet.delivery_fee({}, {})["fee"])
        result = jet.delivery_fee(self.venue, {"minimumOrderValue": 0, "bands": [
            {"minimumAmount": 1000, "fee": 200}]}, 500)
        self.assertIsNone(result["fee"])
        self.assertIn("unavailable", jet.format_fee(result, "PLN", 500))

    def test_money_and_basket(self):
        self.assertEqual(jet.fmt_money(199, "EUR"), "1.99 EUR")
        self.assertEqual(jet.fmt_money(0, "PLN"), "0.00 PLN")
        self.assertEqual(jet.fmt_money(None, "GBP"), "-")
        self.assertEqual(jet.basket_amount("60"), 6000)
        self.assertEqual(jet.basket_amount("1.99"), 199)
        for text in ("-1", "nan", "Infinity", "1.001", "oops"):
            with self.assertRaises(jet.argparse.ArgumentTypeError):
                jet.basket_amount(text)


class VenueTests(unittest.TestCase):
    def test_deal_formatting(self):
        self.assertEqual(jet.format_deal({"offerType": "StampCard", "description": ""}),
                         "StampCard: stamp card (loyalty, not an instant discount)")
        self.assertEqual(jet.format_deal({"offerType": "Notification", "description": "Use PINK50"}),
                         "Notification: Use PINK50 (promo code, eligibility unknown)")
        self.assertEqual(jet.format_deal({"offerType": "Percent", "description": "Spend\u202f50"}),
                         "Percent: Spend 50")

    def test_filters_ignore_account_vouchers_and_stampcards(self):
        rows = jet.parse_venues(fixture(), "pl")
        self.assertEqual([r["id"] for r in jet.filter_venues(rows, deals=True)], ["1"])
        self.assertEqual([r["id"] for r in jet.filter_venues(rows, free_delivery=True)], ["2"])
        self.assertEqual([r["id"] for r in jet.filter_venues(rows, open_only=True)], ["1", "3"])
        self.assertEqual(jet.filter_venues(rows, deals=True, free_delivery=True), [])
        self.assertEqual(jet.filter_venues(rows, free_delivery=True, open_only=True), [])
        data = fixture()
        del data["filters"]["free_delivery"]
        self.assertEqual(jet.filter_venues(jet.parse_venues(data, "pl"), free_delivery=True), [])

    def test_sorting_and_missing_values(self):
        rows = jet.parse_venues(fixture(), "pl", 6000)
        self.assertEqual([r["id"] for r in jet.sort_venues(rows, "rating")], ["2", "1", "3"])
        self.assertEqual([r["id"] for r in jet.sort_venues(rows, "eta")], ["2", "1", "3"])
        self.assertEqual([r["id"] for r in jet.sort_venues(rows, "fee", 6000)], ["2", "1", "3"])
        self.assertEqual([r["id"] for r in jet.sort_venues(rows, "fee")], ["1", "2", "3"])
        self.assertEqual(jet.sort_venues(rows, None), rows)
        below = jet.parse_venues(fixture(), "pl", 1000)
        self.assertEqual([r["id"] for r in jet.sort_venues(below, "fee", 1000)], ["2", "1", "3"])

    def test_ad_and_venue_line(self):
        data = fixture()
        original = copy.deepcopy(data)
        rows = jet.parse_venues(data, "pl", 6000)
        line = jet.venue_line(rows[0], 6000)
        for text in ("[ad] Pizza One", "pizza-one", "4.5 (20)", "30-45 min", "open",
                     "min order 18.00 PLN", "fee 12.00 PLN", "Percent: 30% off"):
            self.assertIn(text, line)
        self.assertNotIn("[ad]", jet.venue_line(rows[1], 6000))
        self.assertEqual(data, original)
        self.assertEqual(jet.promoted_ids([{"restaurantId": 1}, "2"]), {"1", "2"})
        self.assertEqual(jet.promoted_ids(data["promotedPlacement"]), {"1"})
        self.assertEqual(jet.promoted_ids({"rankedIds": ["1"], "filteredSearchPromotedLimit": 99,
                                          "restaurants": {"2": {"restaurantId": "2", "defaultPromoted": True}}}),
                         {"1", "2"})
        self.assertEqual(jet.promoted_ids({"filteredSearchPromotedLimit": 99}), set())


class CliAndNetworkTests(unittest.TestCase):
    def test_json_envelope_and_human_footer(self):
        output = io.StringIO()
        with patch.object(jet, "_get", return_value=fixture()), contextlib.redirect_stdout(output):
            self.assertEqual(jet.main(["venues", "pl", "00-024", "--basket", "60", "--deals", "--json"]), 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data["notice"], jet.UNTRUSTED_NOTICE)
        self.assertEqual(data["basket_minor"], 6000)
        self.assertEqual(len(data["venues"]), 1)
        output = io.StringIO()
        with patch.object(jet, "_get", return_value=fixture()), contextlib.redirect_stdout(output):
            self.assertEqual(jet.main(["venues", "pl", "00-024", "--limit", "1"]), 0)
        self.assertTrue(output.getvalue().endswith(jet.MENU_NOTICE + "\n"))
        self.assertIn(jet.FEE_NOTICE, output.getvalue())

    def test_blocking_http_errors_no_retry(self):
        for status in (403, 429):
            error = urllib.error.HTTPError("https://example.test", status, "blocked", {}, None)
            with patch.object(jet.urllib.request, "urlopen", side_effect=error) as request, \
                    patch.object(jet.time, "sleep"):
                with self.assertRaises(jet.JetError) as caught:
                    jet._get("https://example.test")
            self.assertEqual(caught.exception.status, status)
            self.assertIn("stop calling Just Eat Takeaway for this task", str(caught.exception))
            self.assertIn("user's browser or the app", str(caught.exception))
            request.assert_called_once()

    def test_get_headers_timeout_and_spacing(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"restaurants": []}'
        with patch.object(jet, "_LAST_REQUEST", 100.0), patch.object(jet.time, "monotonic", return_value=100.25), \
                patch.object(jet.time, "sleep") as sleep, \
                patch.object(jet.urllib.request, "urlopen", return_value=response) as urlopen:
            self.assertEqual(jet._get("https://example.test"), {"restaurants": []})
        sleep.assert_called_once_with(0.75)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.get_header("Accept-language"), "en-GB")
        self.assertIn("Chrome/", request.get_header("User-agent"))
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 30)

    def test_source_has_no_forbidden_characters(self):
        for path in (MODULE_PATH, Path(__file__)):
            text = path.read_text()
            for codepoint in (0x2014, 0x00A0, 0x202F):
                self.assertNotIn(chr(codepoint), text)


if __name__ == "__main__":
    unittest.main()
