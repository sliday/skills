import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "wolt.py"
spec = importlib.util.spec_from_file_location("wolt_cli", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {MODULE_PATH}")
wolt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wolt)


def campaign(title, effects, conditions=None, points=None, end_date="2050-01-01T00:00:00+00:00", **extra):
    base_conditions = {"basket_contains": [], "delivery_methods": None, "payment_method": None,
                       "has_wolt_plus": None, "weekly_time_restrictions": None}
    base_conditions.update(conditions or {})
    base_effects = {"basket_discount": None, "delivery_discount": None, "free_items": None, "item_discount": None}
    base_effects.update(effects)
    return {"id": "venue_campaign:x", "effects": base_effects, "conditions": base_conditions,
            "description": {"title": title, "points": points or []}, "end_date": end_date, **extra}


class MoneyTests(unittest.TestCase):
    def test_minor_units_for_euro_and_non_euro(self):
        self.assertEqual(wolt.fmt_money(289, "EUR"), "2.89 EUR")
        self.assertEqual(wolt.fmt_money(17500, "KZT"), "175.00 KZT")
        self.assertEqual(wolt.fmt_money(0, "PLN"), "0.00 PLN")
        self.assertEqual(wolt.fmt_money(None, "EUR"), "-")
        self.assertEqual(wolt.fmt_money(150, None), "1.50 ?")

    def test_detect_currency_from_formatted_fee(self):
        self.assertEqual(wolt.detect_currency("€0.00"), "EUR")
        self.assertEqual(wolt.detect_currency("Min. order 6.00 €"), "EUR")
        self.assertEqual(wolt.detect_currency("PLN0.00"), "PLN")
        self.assertEqual(wolt.detect_currency("KZT175.00"), "KZT")
        self.assertEqual(wolt.detect_currency("1 500 ₸"), "KZT")
        self.assertIsNone(wolt.detect_currency("Open until 02:00"))
        self.assertIsNone(wolt.detect_currency(None))


class CityAndVenueTests(unittest.TestCase):
    def test_cities_swap_geojson_lon_lat(self):
        data = {"results": [
            {"name": "Larnaca", "slug": "larnaca", "country_code_alpha3": "CYP",
             "location": {"coordinates": [33.6335, 34.9186], "type": "Point"}},
            {"name": "Warsaw", "slug": "warsaw", "country_code_alpha3": "POL",
             "location": {"coordinates": [21.0111, 52.2301], "type": "Point"}},
        ]}
        rows = wolt.parse_cities(data, "larn")
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["lat"], rows[0]["lon"]), (34.9186, 33.6335))
        self.assertEqual(rows[0]["url"], "https://wolt.com/en/cyp/larnaca")
        self.assertEqual(len(wolt.parse_cities(data, "pol")), 1)

    def test_venues_flag_platform_wide_and_first_order_campaigns(self):
        wide = {"campaign_id": "wide", "text": "15 PLN off (spend 35 PLN)"}
        venues = []
        for n in range(30):
            promos = [wide]
            if n == 0:
                promos = [wide, {"campaign_id": "own", "text": "30% off"}]
            if n == 1:
                promos = [wide, {"campaign_id": "first", "text": "-€5 on your first order"}]
            venues.append({"item": {"venue": {"name": f"V{n}", "slug": f"v{n}", "online": True, "currency": "PLN",
                                              "rating": {"score": 9.0}, "estimate_range": "20-30",
                                              "delivery_price_int": 0, "promotions": [promos[0]],
                                              "promotions_for_telemetry": promos}}})
        page = {"sections": [{"items": [v["item"] for v in venues]}, {"items": [{"title": "category tile"}]}]}
        parsed = wolt.parse_venues(page)
        self.assertEqual(len(parsed), 30)
        first = parsed[0]["promotions"]
        self.assertEqual([p["campaign_id"] for p in first], ["wide", "own"])
        self.assertTrue(first[0]["platform_wide"])
        self.assertFalse(first[1]["platform_wide"])
        self.assertTrue(parsed[1]["promotions"][1]["first_order"])
        self.assertEqual(parsed[0]["rating"], 9.0)

    def test_small_list_still_flags_platform_wide(self):
        wide = {"campaign_id": "wide", "text": "0 € delivery fee"}
        page = {"sections": [{"items": [
            {"venue": {"name": f"V{n}", "slug": f"v{n}", "promotions_for_telemetry": [wide]}} for n in range(15)
        ]}]}
        self.assertTrue(all(v["promotions"][0]["platform_wide"] for v in wolt.parse_venues(page)))


class DiscountTests(unittest.TestCase):
    ITEMS = {
        "meal1": {"id": "meal1", "name": "Royal Meal for 1", "price": 1290},
        "duo": {"id": "duo", "name": "Whopper Jr Duo Deal", "price": 640},
        "bundle": {"id": "bundle", "name": "Summer Bundle for 2", "price": 2600},
    }

    def test_new_user_basket_offer_is_detected_from_points(self):
        c = campaign("5 € off on orders over 12 €",
                     {"basket_discount": {"amount": 500, "fraction": None}},
                     {"basket_contains": [{"min_amount": 1200}], "delivery_methods": ["homedelivery"]},
                     ["12 € minimum order", "For new users with a local phone number."])
        d = wolt.describe_discount(c, {}, "EUR")
        self.assertEqual((d["kind"], d["value"], d["min_order"]), ("basket", "-5.00 EUR", 1200))
        self.assertTrue(d["new_users_only"])
        self.assertIn("delivery only", d["conditions"])
        self.assertEqual(d["valid_until"], "open-ended")

    def test_item_discount_resolves_names_and_after_price(self):
        c = campaign("2 Whopper Jr for €3.90",
                     {"item_discount": {"fraction": None, "amount_per_item": 250, "include": {"items": ["duo"]}}},
                     {"delivery_methods": ["takeaway"]}, end_date="2026-10-31T21:59:59+00:00")
        d = wolt.describe_discount(c, self.ITEMS, "EUR")
        self.assertEqual(d["items"], [{"id": "duo", "name": "Whopper Jr Duo Deal", "price": 640, "after": 390}])
        self.assertIn("takeaway only", d["conditions"])
        self.assertEqual(d["valid_until"], "2026-10-31")
        self.assertFalse(d["title_mismatch"])

    def test_fraction_discount_and_title_mismatch(self):
        pct = campaign("35% discount on Summer Bundle for 2",
                       {"item_discount": {"fraction": 0.35, "include": {"items": ["bundle"]}}})
        d = wolt.describe_discount(pct, self.ITEMS, "EUR")
        self.assertEqual((d["value"], d["items"][0]["after"]), ("-35%", 1690))
        self.assertFalse(d["title_mismatch"])
        odd = campaign("20% discount on Royal Meal for 1",
                       {"item_discount": {"fraction": None, "amount_per_item": 515, "include": {"items": ["meal1"]}}})
        self.assertTrue(wolt.describe_discount(odd, self.ITEMS, "EUR")["title_mismatch"])

    def test_unknown_item_ids_stay_unnamed(self):
        c = campaign("Halloween: 10% off", {"item_discount": {"fraction": 0.1, "include": {"items": ["zzz"]}}})
        d = wolt.describe_discount(c, {}, "PLN")
        self.assertEqual(d["items"], [{"id": "zzz", "name": None, "price": None}])

    def test_delivery_payment_and_membership_conditions(self):
        free = wolt.describe_discount(campaign("0 € delivery fee", {"delivery_discount": {"amount": 0, "fraction": 1.0}}), {}, "EUR")
        self.assertEqual((free["kind"], free["value"]), ("delivery", "free delivery"))
        card = wolt.describe_discount(campaign(
            "Pay with a Eurobank Card, spend over €25",
            {"basket_discount": {"amount": 1, "fraction": None}},
            {"basket_contains": [{"min_amount": 2500}], "payment_method": "szep_otp", "has_wolt_plus": True},
            ["***SELECT AT CHECKOUT***"]), {}, "EUR")
        self.assertEqual(card["value"], "see title")
        self.assertIn("payment method: szep_otp", card["conditions"])
        self.assertIn("Wolt+ members only", card["conditions"])
        self.assertIn("select at checkout", card["conditions"])
        self.assertFalse(card["new_users_only"])

    def test_one_cent_placeholder_gets_no_after_price(self):
        c = campaign("Card cashback on Royal Meal",
                     {"item_discount": {"fraction": None, "amount_per_item": 1, "include": {"items": ["meal1"]}}})
        d = wolt.describe_discount(c, self.ITEMS, "EUR")
        self.assertNotIn("after", d["items"][0])
        self.assertFalse(d["title_mismatch"])

    def test_coordinates_are_rounded(self):
        self.assertEqual(wolt.coord("34.91674"), 34.917)

    def test_first_order_title_marks_new_users(self):
        c = campaign("-€5 on your first order", {"basket_discount": {"amount": 500, "fraction": None}})
        self.assertTrue(wolt.describe_discount(c, {}, "EUR")["new_users_only"])

    def test_required_items_condition_is_kept(self):
        c = campaign("Free fries with any burger", {"free_items": {"items": ["fries"]}},
                     {"basket_contains": [{"min_amount": None, "any_of_items": ["duo", "zzz"]}]})
        d = wolt.describe_discount(c, self.ITEMS, "EUR")
        self.assertIn("basket must include one of 2 items: Whopper Jr Duo Deal", d["conditions"])


class FeeAndItemTests(unittest.TestCase):
    def test_parse_fees_reads_specs_and_header(self):
        dynamic = {
            "order_minimum": 600,
            "venue_raw": {"delivery_specs": {"order_minimum_no_surcharge": 600, "original_delivery_price": 125,
                                             "delivery_pricing": {"distance_ranges": [
                                                 {"min": 0, "max": 467, "a": 0}, {"min": 467, "max": 0, "a": 150}]}},
                          "discounts_restrictions_text": "tobacco excluded"},
            "venue": {"header": {"delivery_method_statuses": [
                {"delivery_method": "DELIVERY", "metadata": [
                    {"meaning": "ORDER_MINIMUM", "value": "Min. order 6.00 €"},
                    {"meaning": "DELIVERY_FEE", "value": "€0.00"}]},
                {"delivery_method": "PICKUP", "metadata": [{"meaning": "DELIVERY_FEE", "value": "pickup"}]},
            ]}},
        }
        fees = wolt.parse_fees(dynamic)
        self.assertEqual(fees["order_minimum"], 600)
        self.assertEqual(fees["base_delivery_price"], 125)
        self.assertEqual(fees["max_distance_surcharge"], 150)
        self.assertEqual(fees["shown_delivery_fee"], "€0.00")
        self.assertEqual(fees["shown_order_minimum"], "Min. order 6.00 €")

    def test_items_parse_filter_and_paging_token(self):
        data = {"items": [
            {"id": "a", "name": "Hochland Cheddar Slices", "price": 239, "original_price": 299,
             "unit_price": {"price": 1195, "unit": "kilogram"}, "unit_info": "200 g", "disabled_info": None},
            {"id": "b", "name": "Gouda", "price": 639, "original_price": None,
             "unit_price": {"price": 4733, "unit": "kilogram"}, "unit_info": "135 g",
             "disabled_info": {"disable_text": "Sold out"}, "is_wolt_plus_only": True},
        ], "metadata": {"next_page_token": "abc", "page": 1}}
        rows = wolt.parse_items(data)
        self.assertTrue(rows[1]["sold_out"])
        self.assertTrue(rows[1]["wolt_plus_only"])
        self.assertEqual([r["id"] for r in wolt.filter_items(rows, None, True)], ["a"])
        self.assertEqual([r["id"] for r in wolt.filter_items(rows, "GOUDA", False)], ["b"])
        self.assertEqual(wolt.next_page_token(data), "abc")
        self.assertIsNone(wolt.next_page_token({"metadata": {"next_page_token": None}}))

    def test_assortment_url_adds_category_and_token(self):
        url = wolt._assortment_url("auchan-pokorna", "cheese-37", "eyJ=")
        self.assertTrue(url.endswith("/venues/slug/auchan-pokorna/assortment/categories/slug/cheese-37?language=en&page_token=eyJ%3D"))


if __name__ == "__main__":
    unittest.main()
