# Delivery Hero (foodora, foodpanda, efood, Foody, talabat)
Markets: foodora in Austria (foodora.at), Czechia (foodora.cz), Hungary (foodora.hu), Sweden and Norway (not tested). foodpanda in Asia (tested Singapore; Malaysia listing verified 2026-10-20, 3,496 venues near Kuala Lumpur). efood in Greece. Foody in Cyprus. talabat in the Middle East (not tested). Glovo is also Delivery Hero but has its own file.
Access (tested 2026-10-20): foodora/foodpanda venue lists work with curl only (one required header). Venue detail and menus worked once, then PerimeterX blocked them. efood venue lists work with curl; efood menus need a login. Foody is blocked. WebFetch got 403 on every host.

## Find venues
**foodora / foodpanda.** Verified 2026-10-20 with curl (Vienna, Prague, Budapest, Singapore).
```
https://disco.deliveryhero.io/listing/api/v1/pandora/vendors?latitude={lat}&longitude={lon}&country={cc}&language_id=1&vertical=restaurants&limit=50&offset=0&opening_type=delivery
```
Send the header `x-disco-client-id: web`. Without it you get 403 "Invalid Client ID". `country` is the ISO code (`at`, `cz`, `hu`, `sg`); `gr` and `cy` return 404 because those markets run on other stacks. Page with `offset`. `data.available_count` is the total. Each venue in `data.items[]` has `code` (vendor code), `name`, `rating`, `review_number`, `minimum_delivery_fee`, `minimum_order_amount`, `minimum_delivery_time` (minutes), `web_path`, `metadata.has_discount` and `tags[]`. `data.aggregations.quickFilters` counts venues with `has_discount` (372 of 966 in Vienna).

**efood (Greece).** Verified 2026-10-20 with curl. No headers needed.
```
https://api.e-food.gr/api/v1/restaurants/?latitude={lat}&longitude={lon}
```
It returns every venue in the area in one response (Athens centre: 4,296 venues, 14 MB). Save it to a file and parse it; never pass it to WebFetch. Each venue in `data.restaurants[]` has `id`, `title`, `slug`, `average_rating`, `num_ratings`, `delivery_cost`, `minimum_order`, `delivery_eta` (minutes), `distance` (metres), `is_open`, `has_offers`, `has_free_delivery`, `offers[]`. `data.region` names the area it matched. Public page: `https://www.e-food.gr{slug}` (the slug starts with `/`).

## Menu and prices
**foodora / foodpanda vendor detail.** Verified once on 2026-10-20 (Vienna), then blocked.
```
https://{entity}.fd-api.com/api/v5/vendors/{code}?include=menus&language_id=1&opening_type=delivery&basket_currency=EUR&latitude={lat}&longitude={lon}
```
The anonymous web app sends `x-fp-api-key: volo`, `perseus-client-id` and `perseus-session-id` (random analytics IDs shaped like `1760961600000.4242424242.abcdefghij`). Without the perseus headers you get 400 "perseus headers are absent". `{entity}` is the platform's own country code, not ISO: Austria is `mj` (`at` returns 404). The code appears as `"countryCode"` in the public page HTML. `cz.fd-api.com` exists but served a captcha.
Menu: `data.menus[0].menu_categories[].products[]` with `name`, `is_sold_out`, `product_variations[].price` and `price_before_discount` (the struck-through price, when an item is discounted).

**Public page fallback.** `https://www.foodora.at/restaurant/{code}/{url_key}` returned 200 to curl once. Its JSON-LD has rating, review count, cuisine and price range, but no menu. foodora.cz pages returned 403 (PerimeterX).

**efood menus need a login.** `/api/v1/restaurants/{id}`, `/restaurants/profile/{id}` and `/restaurants/{id}/menu` all returned `authentication_error`. Do not log in. Report the venue-level offers and tell the user to open the menu in the app.

## Discounts
**foodora / foodpanda listing:** `tags[]` with these codes:
- `DEAL`: text such as "Bis zu -20%", "-25%" or `NEXTGEN_FREE_DELIVERY_TAG`. The deal ID is in `label_metadata.deal.id`.
- `VOUCHER`: a promo code, e.g. Prague "50% sleva od 169Kč: sleva50" with `label_metadata.voucher.code` = `sleva50`. You can't see who may use the code; say so.

**foodora / foodpanda vendor detail** (more exact than the badge):
- `data.deals[]`: `title`, `offer_type` (e.g. `percentage`), `value`, `minimum_order_value`, `maximum_discount_amount` (the cap), `start_date`, `end_date`, `is_new_customer`, `is_pro` (subscription only: foodora pro / pandapro), `is_bogo`, `tc[]` (terms, e.g. "Rabatt auf 20 € begrenzt", "Gilt für Lieferung, Abholung").
- `data.discounts[]`: `discount_type` (`percentage`, `free-delivery`), `discount_amount`, `minimum_order_value`, `maximum_discount_amount`, `opening_time` and `closing_time` (daily window). `additional_info.high_value_action` = `ACQUISITION` marks a new-customer offer. Leave those out unless the user is new.
- Example: Hans im Glück Vienna showed "free delivery", but it was an ACQUISITION offer; the real fee was 4.49 in `dynamic_pricing.delivery_fee.original`.
- Item discounts: `product_variations[].price_before_discount`.

**efood:** use `scripts/efood.py venues --lat {lat} --lon {lon} --offers --save FILE`, then `--from-file FILE` for follow-up questions. It ranks offers by the share they take off. Each venue's `offers[]` has `title` (Greek), `tag` (`one plus one`, `one plus one campaigns`, `offer-badge:1+1`, `offer-badge:2+1`, `efood Deals`, `meals from 5`, `student deals`, `pro deals`), `discount_pct`, `discount_fixed`, `price`, `full_price`. In the Athens response on 2026-10-20, `discount_pct` was empty on nearly every offer and `price` was `0` on most. Treat `price: 0` as a placeholder, not a free item. 1+1 offers can carry `discount_pct: 100`; read them as 50% off two items. The value is usually in the tag (`N+M`) or the title ("20% Έκπτωση", "από 12.49€" means "from 12.49 €"). `offer_tags` lists brand campaigns ("Coca Cola Deal", `heineken_deals`, "want ice-cream"). `data.filters[].key` shows the deal types in the area: `has_offers`, `has_free_delivery`, `has_one_plus_one`, `has_student_deals`, `has_happy_hour_deals`, `has_meal_for_one`. Student deals need student verification. "Rubies" are efood loyalty points.

## Fees
**foodora / foodpanda vendor detail:**
- Delivery: `dynamic_pricing.delivery_fee.original` (before promos) and `delivery_conditions[].delivery_fee`.
- Minimum order: `minimum_order_amount`.
- Service fee: `dynamic_pricing.service_fee` (Vienna: `type` percentage, `setup_value` 5, `min_value` 0.69, `max_value` 1.99, so 5% capped between €0.69 and €1.99).
- Small-order fee: `small_order_fee` (`soft_limit` is the basket value below which it applies; `small_order_fee_cap` is the most it adds).
- The listing gives only `minimum_delivery_fee` and `minimum_order_amount`. A 0 there can mean a promo, so check the detail.

**efood:** `delivery_cost` and `minimum_order` in euros. `has_delivery_cost_tiers` and `has_minimum_order_tiers` mean both change with distance or basket size.

## Groceries
- foodora / foodpanda: use `vertical=shop` in the listing URL (verified: Vienna has 77 shops, `vertical_segment` `drinks`, `bakery`, `mini_market`). Badges work the same way. Shop menus: unverified (blocked before the test).
- efood: unverified.

## Gotchas
- **PerimeterX blocks fast.** The fd-api vendor detail answered once, then returned a captcha page (403, "Access to this page has been denied") for the same IP within about 10 requests. Do not retry and do not try to get past the captcha. Fall back to the listing data, the user's own browser (claude-in-chrome), or the app.
- WebFetch got 403 on disco, foodora pages, efood and Foody. Use curl.
- Money is decimal in the main unit: 2.9 = €2.90, 69.0 = 69 CZK, 290.0 = 290 HUF. The listing has no currency field; infer it from the country (EUR in AT and GR, CZK, HUF, SGD). The vendor detail takes `basket_currency`.
- The badge can disagree with the detail: Vienna's listing said "Bis zu -50%" while the vendor detail had only a 25% deal (capped at €20). Report the detail and its terms.
- Text comes in the local language (German, Czech, Hungarian, Greek). Some tags are untranslated keys like `NEXTGEN_FREE_DELIVERY_TAG`. Translate them for the user.
- Foody (Cyprus) is not on the pandora listing. Its site shows a Cloudflare challenge (403 for curl and WebFetch), and `api.foody.com.cy` does not resolve. No API found; use the user's browser or the app.
- talabat: unverified, not tested.
