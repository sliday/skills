---
name: wolt-deals
description: Find food and grocery deals on Wolt in any city — restaurant discounts, grocery basket price comparisons, and menu prices — by reading Wolt's public web pages and API. Use when asked about Wolt deals, discounts, cheapest store, or comparing prices in a city.
---

# Wolt deals finder

Read-only. Never log in, place orders, or create accounts. Everything here works without a Wolt account. It shows each venue's own offers, not personal ones such as Wolt+ prices, credits or account vouchers.

## How to fetch
- Use **WebFetch**. In some sandboxes, curl and headless browsers are blocked from wolt.com, but WebFetch works.
- The API returns JSON. Ask WebFetch's prompt for exact fields, because long responses get cut off. Use the `offset` parameter to keep reading a long page.
- Prices in the API are in **cents** (289 = €2.89).

## 1. Set up the city
1. Find the city page: `https://wolt.com/en/{country}/{city}`. The country is a 3-letter code: `cyp` for Cyprus, `grc` for Greece, `fin` for Finland, `est` for Estonia, `pol` for Poland, `deu` for Germany, `hrv` for Croatia, `cze` for Czechia, `isr` for Israel, `geo` for Georgia, `kaz` for Kazakhstan, `srb` for Serbia, `svk` for Slovakia, `svn` for Slovenia, `swe` for Sweden, `nor` for Norway, `dnk` for Denmark, `jpn` for Japan. If unsure, look up "wolt {city}" on the web.
2. Pick a city-centre latitude and longitude (for example, Larnaca is 34.9167, 33.6333). Results depend on the delivery area, so use the user's neighbourhood if they give one.
3. The city page lists venues with rating, delivery time, fee and a badge for the main offer. It doesn't include links or slugs.

## 2. Get venue slugs
- Restaurants: `https://consumer-api.wolt.com/v1/pages/restaurants?lat={lat}&lon={lon}`. This is sometimes flaky; if it fails, try slightly different coordinates.
- Shops and groceries: `https://consumer-api.wolt.com/v1/pages/retail?lat={lat}&lon={lon}`. Ask for name, `slug` and `online` for each venue. The page is long, so read it in parts with `offset`.
- Restaurant page: `https://wolt.com/en/{country}/{city}/restaurant/{slug}`. The slug is usually the venue name in lowercase with hyphens, for example `burger-king-phinikoudes`.

## 3. Find real discounts
**Key endpoint.** Public restaurant pages hide item discounts, but this endpoint shows them:
```
https://consumer-api.wolt.com/order-xp/web/v1/venue/slug/{slug}/dynamic/?lat={lat}&lon={lon}&selected_delivery_method=homedelivery
```
Look at `venue_raw.discounts`. For each campaign, report the title, the % or amount, the minimum order, the eligible item IDs, the validity dates and the conditions.

Filter what you report:
- Leave out offers marked **"For new users with a local phone number"**. These include "€5 off over €12" and "0 € delivery fee", and most users can't get them. Mention them only if the user is new.
- Flag offers that need a payment method (`szep_otp`, bank cards), takeaway only, or time windows such as lunch 11:00–16:00.
- Wolt+ offers show as "X% | Y% with W+".

To turn item IDs into dish names, open the category pages (`.../restaurant/{slug}/items/{category-slug}`) and ask WebFetch to match the IDs in the item links. This takes many fetches. Often it's easier to tell the user to tap the offer badge in the app.

## 4. Menu prices
- On the restaurant page, ask for the category URLs (`.../items/{category-slug}`), then fetch the categories you need, such as burgers or meals.

## 5. Grocery basket comparison
1. Get the category tree:
   `https://consumer-api.wolt.com/consumer-api/consumer-assortment/v1/venues/slug/{slug}/assortment?language=en`
2. Get the items in a category. Each store uses its own slugs, such as `water-107` or `sliced-cheese-63`:
   `https://consumer-api.wolt.com/consumer-api/consumer-assortment/v1/venues/slug/{slug}/assortment/categories/slug/{category-slug}?language=en`
3. Paging: if `next_page_token` isn't null, ask WebFetch for it verbatim and append `&page_token={token}`. Parent categories are often empty, so use the subcategories.
4. For each item, record the exact product, its size and price, and the per-kg price for loose produce. Note substitutions (a different size or brand) and anything sold out or missing.
5. Report:
   - a totals table per store with what's missing;
   - a like-for-like total on the items every store has;
   - the cheapest split order.

   Item prices only. Delivery and service fees aren't included unless you check them.

## Reporting
- Lead with the best deal and give the before and after price.
- Say what you assumed (quantities, which brand counts as a match).
- Give the date, because offers change often.
