from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "efood.py"
spec = importlib.util.spec_from_file_location("efood_cli", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {MODULE_PATH}")
efood = importlib.util.module_from_spec(spec)
spec.loader.exec_module(efood)


def venue(**extra):
    row = {"id": 1, "title": "Greek\u00a0Cafe", "slug": "/delivery/athina/cafe", "average_rating": 4.5,
           "num_ratings": 100, "delivery_cost": 1.5, "minimum_order": 10, "delivery_eta": 25,
           "distance": 700, "is_open": True, "has_offers": True, "has_free_delivery": False,
           "has_delivery_cost_tiers": True, "has_minimum_order_tiers": True,
           "offers": [{"title": "Καφές\u202fδώρο", "tag": "one plus one", "discount_pct": 50,
                       "price": 3, "full_price": 6}], "offer_tags": ["Coca Cola Deal"]}
    row.update(extra)
    return row


def payload(*rows):
    return {"data": {"region": "Αθήνα", "filters": [{"key": "has_offers"}, {"key": "has_student_deals"}],
                     "restaurants": list(rows)}}


class OfferTests(unittest.TestCase):
    def test_all_size_cases_and_precedence(self):
        cases = [({"discount_pct": 25, "price": 1, "full_price": 10}, 10, 25),
                 ({"discount_pct": 0, "discount_fixed": 5}, 10, 50.0),
                 ({"discount_pct": 0, "title": "20% Έκπτωση σε 1 πιάτο"}, 10, 20.0),
                 ({"discount_fixed": 15}, 10, None),
                 ({"price": 3, "full_price": 12, "discount_fixed": 1}, 10, 75),
                 ({"price": 0, "full_price": 4}, 10, None),
                 ({"tag": "one plus one", "discount_pct": 100, "price": 0}, 10, 50.0),
                 ({"tag": "offer-badge:2+1", "price": 0, "full_price": 4.38}, 10, 33.3),
                 ({"tag": "alfa deals", "title": "20% Έκπτωση σε 2 μερίδες", "price": 0}, 10, 20.0),
                 ({"tag": "heineken_deals", "title": "Έκπτωση 15% σε 1 πιάτο", "price": 0}, 10, 15.0),
                 ({"tag": "efood Deals", "title": "Krombacher Pils 0.0% 330ml", "price": 0}, 10, None),
                 ({"discount_fixed": 3}, 12, 25),
                 ({"discount_fixed": 0}, 12, None),
                 ({"price": 3, "full_price": 0}, 10, None),
                 ({"discount_fixed": 3}, 0, None),
                 ({"discount_fixed": 3}, None, None),
                 ({"price": 3}, 10, None), ({}, 10, None)]
        for offer, minimum, expected in cases:
            with self.subTest(offer=offer, minimum=minimum):
                self.assertEqual(efood.offer_size(offer, minimum), expected)

    def test_parse_and_format(self):
        row = efood.parse_venues(payload(venue()))[0]
        self.assertEqual(row["url"], "https://www.e-food.gr/delivery/athina/cafe")
        self.assertEqual(row["title"], "Greek Cafe")
        self.assertEqual(row["best_offer_pct"], 50)
        self.assertEqual(efood.format_offer(row["offers"][0]),
                         "-50% | one plus one | Καφές δώρο | price 3.00 EUR (was 6.00 EUR)")
        line = efood.format_venue(row)
        self.assertIn("delivery 1.50 EUR tiered", line)
        self.assertIn("min order 10.00 EUR tiered", line)
        self.assertIn("4.5 (100) | 25 min | 700 m", line)
        self.assertIn("| open | -50%", line)

    def test_optional_offer_parts_and_unknown_size(self):
        row = efood.parse_venues(payload(venue(offers=[{"title": "Gift"}])))[0]
        self.assertIsNone(row["best_offer_pct"])
        self.assertEqual(efood.format_offer(row["offers"][0]), "Gift")
        row = efood.parse_venues(payload(venue(offers=[], is_open=False,
                                               has_delivery_cost_tiers=False,
                                               has_minimum_order_tiers=False)))[0]
        self.assertNotIn("tiered", efood.format_venue(row))
        self.assertIn("closed | -", efood.format_venue(row))


class FilterAndSortTests(unittest.TestCase):
    def setUp(self):
        self.rows = efood.parse_venues(payload(
            venue(id=1),
            venue(id=2, offers=[], has_offers=True, has_free_delivery=True, is_open=False,
                  offer_tags=["STUDENT"]),
            venue(id=3, has_free_delivery=True, has_offers=False),
        ))

    def test_each_filter(self):
        for kwargs, ids in [({"offers": True}, [1, 3]),
                            ({"free_delivery": True}, [2, 3]),
                            ({"open_only": True}, [1, 3]),
                            ({"tag": "PLUS ONE"}, [1, 3]),
                            ({"tag": "cola"}, [1, 3]),
                            ({"tag": "student"}, [2]),
                            ({"tag": "missing"}, []),
                            ({"offers": True, "free_delivery": True, "open_only": True}, [3])]:
            with self.subTest(kwargs=kwargs):
                self.assertEqual([r["id"] for r in efood.filter_venues(self.rows, **kwargs)], ids)

    def test_tag_keeps_only_matching_offers_and_reranks(self):
        rows = efood.parse_venues(payload(venue(id=9, offers=[
            {"title": "Με 1 καφέ, δώρο ακόμη 1", "tag": "one plus one", "price": 0},
            {"title": "20% Έκπτωση σε 1 πιάτο", "tag": "heineken_deals", "price": 0},
        ])))
        self.assertEqual(rows[0]["best_offer_pct"], 50.0)
        tagged = efood.filter_venues(rows, tag="heineken")[0]
        self.assertEqual([o["tag"] for o in tagged["offers"]], ["heineken_deals"])
        self.assertEqual(tagged["best_offer_pct"], 20.0)
        self.assertEqual(len(rows[0]["offers"]), 2)

    def test_all_sort_keys_missing_last(self):
        for key, field in [("offer", "best_offer_pct"), ("rating", "average_rating"),
                           ("eta", "delivery_eta"), ("fee", "delivery_cost"), ("distance", "distance")]:
            rows = [{"id": "missing", field: None}, {"id": "zero", field: 0},
                    {"id": "high", field: 9}, {"id": "absent"}]
            expected = ["high", "zero", "missing", "absent"] if key in ("offer", "rating") else [
                "zero", "high", "missing", "absent"]
            with self.subTest(key=key):
                self.assertEqual([r["id"] for r in efood.sort_venues(rows, key)], expected)
        self.assertIs(efood.sort_venues(self.rows, None), self.rows)


class CliTests(unittest.TestCase):
    def test_from_file_no_coordinates_or_network_and_json_notice(self):
        raw = json.dumps(payload(venue())).encode()
        with patch.object(efood.Path, "read_bytes", return_value=raw) as read, \
                patch.object(efood, "_get") as get, contextlib.redirect_stdout(io.StringIO()) as out:
            status = efood.main(["venues", "--from-file", "cached.json", "--json"])
        self.assertEqual(status, 0)
        read.assert_called_once_with()
        get.assert_not_called()
        result = json.loads(out.getvalue())
        self.assertEqual(result["_notice"], efood.UNTRUSTED_NOTICE)
        self.assertEqual(result["venues"][0]["url"], "https://www.e-food.gr/delivery/athina/cafe")

    def test_offers_default_sort_limit_and_save_exact_bytes(self):
        raw = json.dumps(payload(venue(id=1), venue(id=2, offers=[{"discount_pct": 80}]))).encode()
        args = efood.build_parser().parse_args([
            "venues", "--lat", "37.98449", "--lon", "23.72849", "--offers", "--limit", "1", "--save", "cache.json"])
        with patch.object(efood, "_get", return_value=raw) as get, \
                patch.object(efood.Path, "write_bytes") as write:
            result = efood.cmd_venues(args)
        get.assert_called_once_with(efood.API + "?latitude=37.984&longitude=23.728")
        write.assert_called_once_with(raw)
        self.assertEqual([r["id"] for r in result["venues"]], [2])

    def test_header_human_footer_and_no_raw_dump(self):
        fixture = payload(venue())
        fixture["secret_unused_field"] = "DO NOT PRINT RAW"
        args = efood.build_parser().parse_args(["venues", "--from-file", "cache.json"])
        with patch.object(efood.Path, "read_bytes", return_value=json.dumps(fixture).encode()):
            result = efood.cmd_venues(args)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            efood._print_human(result)
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[0], "Region: Αθήνα | deal types: has_offers, has_student_deals")
        self.assertIn(efood.STUDENT_NOTICE, lines)
        self.assertEqual(lines[-1], efood.MENU_NOTICE)
        self.assertNotIn("DO NOT PRINT RAW", out.getvalue())

    def test_live_region_object_and_bogo_ranking_inputs(self):
        fixture = payload(venue(offers=[{"title": "1+1 Προσφορά", "tag": "one plus one",
                                        "discount_pct": 100, "discount_fixed": 0,
                                        "price": None, "full_price": None}]))
        fixture["data"]["region"] = {"city": "Αθήνα", "area": "Ομόνοια", "latitude": 37.984069}
        header = efood.parse_header(fixture)
        self.assertEqual(header["region"], fixture["data"]["region"])
        self.assertEqual(efood.format_region(header["region"]), "Αθήνα, Ομόνοια")
        self.assertEqual(efood.format_region({}), "-")
        self.assertEqual(efood.format_region(None), "-")
        self.assertEqual(efood.parse_venues(fixture)[0]["best_offer_pct"], 50.0)
        placeholder = {"title": "Pils", "tag": "offer-badge:1+1", "price": 0, "full_price": 2.8, "size_pct": 50.0}
        self.assertEqual(efood.format_offer(placeholder), "-50% | offer-badge:1+1 | Pils | regular price 2.80 EUR")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            efood._print_human({**header, "venues": []})
        self.assertTrue(out.getvalue().startswith("Region: Αθήνα, Ομόνοια | deal types:"))

    def test_coordinates(self):
        self.assertEqual(efood.coord("37.98449"), 37.984)
        self.assertEqual(efood.coord("23.7286"), 23.729)
        self.assertEqual(efood.coord("-23.7286"), -23.729)
        with self.assertRaises(ValueError):
            efood.coord("nan")

    def test_missing_coordinates_and_bad_file_errors(self):
        with patch.object(efood, "_get") as get, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(efood.main(["venues"]), 2)
        get.assert_not_called()
        with patch.object(efood.Path, "read_bytes", side_effect=OSError("missing file")), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(efood.main(["venues", "--from-file", "missing"]), 2)

    def test_bad_json_not_echoed(self):
        for raw in (b"not json SECRET", b"[]", b'{"data": null}', b"\xff"):
            with self.subTest(raw=raw), self.assertRaises(efood.EfoodError) as caught:
                efood.decode_response(raw)
            self.assertNotIn("SECRET", str(caught.exception))


class NetworkTests(unittest.TestCase):
    def test_get_timeout_ua_spacing_and_raw_bytes(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"data": {}}'
        with patch.object(efood, "_LAST_REQUEST", 10.0), \
                patch.object(efood.time, "monotonic", return_value=10.25), \
                patch.object(efood.time, "sleep") as sleep, \
                patch.object(efood.urllib.request, "urlopen", return_value=response) as open_url:
            self.assertEqual(efood._get(efood.API), b'{"data": {}}')
        sleep.assert_called_once_with(0.75)
        request = open_url.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertIn("Chrome/", request.get_header("User-agent"))
        self.assertEqual(open_url.call_args.kwargs, {"timeout": 60})

    def test_http_refusals_status_no_retries(self):
        for status in (403, 429):
            error = urllib.error.HTTPError(efood.API, status, "blocked", {}, None)
            with self.subTest(status=status), patch.object(efood.time, "sleep"), \
                    patch.object(efood.urllib.request, "urlopen", side_effect=error) as get:
                with self.assertRaises(efood.EfoodError) as caught:
                    efood._get(efood.API)
                self.assertEqual(caught.exception.status, status)
                self.assertIn("stop calling efood for this task", str(caught.exception))
                self.assertIn("user's browser or the app", str(caught.exception))
                self.assertEqual(get.call_count, 1)

    def test_network_error(self):
        with patch.object(efood.time, "sleep"), patch.object(
                efood.urllib.request, "urlopen", side_effect=urllib.error.URLError("offline")):
            with self.assertRaises(efood.EfoodError):
                efood._get(efood.API)


if __name__ == "__main__":
    unittest.main()
