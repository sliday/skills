# Glovo (glovoapp.com)
Markets: 24 countries, including Spain, Italy, Poland, Portugal, Romania, Bulgaria, Ukraine, Croatia, Serbia, Bosnia, Montenegro, Morocco, Georgia, Kazakhstan, Kenya and Nigeria. The full list is the `citiesSlugs` map in any page's payload (country, then city slug, then city code).
Access (tested 2026-10-20): public web pages work with curl and WebFetch. The JSON API at `api.glovoapp.com` works with curl when you send one header. WebFetch can't send headers, so the API gives it HTTP 400.

## Find venues
```
https://glovoapp.com/en/{cc}/{city}/categories/food_1
https://glovoapp.com/en/{cc}/{city}/categories/food_1?type={cuisine}_{id}
https://glovoapp.com/en/{cc}/{city}/categories/groceries_4
https://glovoapp.com/en/{cc}/{city}/categories/shops_22
```
Verified 2026-10-20 (Warsaw, Madrid; curl 200 and WebFetch). The language comes first, then the country: `/en/pl/warszawa`. The city slug is the local name (`warszawa`, `madrid`); the country page `https://glovoapp.com/en/{cc}/` lists them. Cuisine filters such as `pizza_34701` are links on the city page.
The HTML has store cards (`a[data-testid="store-card"]`). Each card gives:
- the link `/en/{cc}/{city}/stores/{store-slug}`, with a city suffix such as `dodo-pizza-waw` or `kfc-madrid`;
- the name (image `alt`);
- promo tags: `span[data-style="promotion"]` ("-30% select items", "2 for 1 select items", "-20% whole menu") and `span[data-style="loyalty"]` ("-40% with Prime");
- the delivery fee text, rating % and number of votes.

A page shows at most 50 cards. Use cuisine filters to see more. Cards have no delivery time, because the page is for the whole city, not an address.

## Menu and prices
**Store page** (verified 2026-10-20, curl and WebFetch):
```
https://glovoapp.com/en/{cc}/{city}/stores/{store-slug}
```
WebFetch reads the visible menu: name, crossed-out price, promo price and labels. The text is over 100,000 characters, so use `offset`.
With curl, the data is in the Next.js payload (no JSON-LD). Join the strings in `self.__next_f.push([1,"..."])`, then search the result:
```python
import re, json, sys
html = open(sys.argv[1], encoding="utf-8").read()
rsc = "".join(json.loads(s) for s in re.findall(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)', html))
```
The payload holds the city code (`"cityCode":"WAW"`), the store and address IDs in paths like `/v4/stores/316571/addresses/474737/...`, and the full restaurant menu. For grocery stores it holds only the first carousels.

**API** (verified 2026-10-20, curl only):
```
https://api.glovoapp.com/v4/stores/{storeId}/addresses/{addressId}/content/main?nodeType=DEEP_LINK&link={collection-slug}
```
Send the header `glovo-location-city-code: WAW` (the 3-letter city code, upper case). No other header, cookie or login is needed. Without it you get 400 "Delivery address out of city".
- Take the `link` values from `"path"` entries in the store payload: `promotions-pr`, `top-sellers-ts`, menu sections such as `sosy-s.6414148495`, and grocery categories such as `mleka-nabialy-jaja-sc.59697688/mleko-i-smietana-c.51160636`.
- Products are at `data.body[].data.elements[]`, with `type` `PRODUCT_ROW` (restaurants) or `PRODUCT_TILE` (groceries). Read `.data.id`, `.name`, `.price`, `.priceInfo`, `.promotions[]` and `.description`.

Money: prices are decimal major units, **not cents** (57 = 57,00 zł; 5.19 = 5,19 zł). `priceInfo.currencyCode` gives the currency (PLN, EUR) and `priceInfo.displayText` the formatted price.

## Discounts
Each product has `promotions[]`; `promotion` repeats the first one.
- `type: PERCENTAGE_DISCOUNT`: `percentage`, `price` (what you pay), `priceInfo`, `title` ("-30%"). Example: TRIFLE EBI 57,00 zł becomes 39,90 zł.
- `type: TWO_FOR_ONE`: `title` "2 for 1". The item price stays the same and the second item is free. Example: Dodo Pizza pizzas.
- `isPrime: true` (with `description: "with Prime"`): a Glovo Prime member price, for example -40% for 34,20 zł. Lead with the non-Prime price and give the Prime price as an extra.
- The fastest way to every promo item is the `promotions-pr` node.
- Store-level labels sit in the payload under `topElements[]` as `LABEL_V2` with `styles.type` `PROMO` or `PRIME`. "select items" means some items; "whole menu" means all of them.
- Grocery promos use the same fields. `promotionId` can be -1 and `percentage` can be fractional (20.03), so report `price` and don't recompute it.

Glovo doesn't show the minimum order, validity dates or payment conditions anywhere in this data. Tell the user to check the terms in the app.

## Fees
The store object in the payload has `deliveryFeeInfo.fee` and `serviceFee`. A tracking event named `Store` has `deliveryFeeValue`, `deliveryFeeCurrency` and `isStoreSurged`. Without an address these are city defaults (4.99 or 7.99 PLN in Warsaw on 2026-10-20).
All 100 cards sampled in Warsaw and Madrid, and the store info badge, showed "Free" delivery while `deliveryFeeValue` stayed 4.99 or 7.99. Treat "Free" as an offer with conditions you can't see (new user, Prime or a basket threshold), and say so. You only see the real fee at checkout with an address.
`serviceFee` equalled the delivery fee in every sample, so check it in the app. The minimum order and small-order fee aren't shown to anonymous users (unverified).

## Groceries
`groceries_4` lists supermarkets (Biedronka, Biedronka Express, Auchan, Carrefour) and bakeries. The store page shows only carousels. Get each category from the API with its deep link from the store payload (verified 2026-10-20).
Names include the size ("Piątnica Śmietana 18 % 400 g"). No unit-price field exists, so work out per-kg or per-litre prices yourself. The tested category had 6 items and no paging fields; paging in large categories is unverified.

## Gotchas
- The old pattern `glovoapp.com/{cc}/{lang}/{city}` redirects to a 404. Use `/{lang}/{cc}/{city}` with the local city slug.
- The API header needs the city code. Find it in the store payload (`cityCode`) or in the `citiesSlugs` map (`barcelona: BCN`, `warszawa: WAW`).
- The crossed-out price is "the lowest price in the last 30 days before reduction" (an EU rule), not always the menu price. Item `price` is the regular price now; promo `price` is what you pay.
- Search autocomplete (`/v1/web/search/autocomplete?query=`) returned 503 to anonymous curl, and the guessed `/v3/feeds/categories/1` returned 404. No address-based venue list with delivery times works without the app (unverified beyond these two tries).
- Store pages are 1 to 2 MB and API nodes up to 1.3 MB. Parse them with a script; don't paste them into context.
