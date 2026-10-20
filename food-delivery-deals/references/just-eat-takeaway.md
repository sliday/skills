# Just Eat Takeaway (Just Eat, Lieferando, Thuisbezorgd, Pyszne.pl, Takeaway.com, 10bis)
Markets: UK, IE, ES, IT, DK (Just Eat); DE, AT (Lieferando); NL (Thuisbezorgd); PL (Pyszne.pl); BE, LU, BG (Takeaway.com); IL (10bis).
Access (tested 2026-10-20): the discovery JSON API works with curl and WebFetch, without login. Menus are not available: every brand website returns a Cloudflare 403 to curl and to WebFetch. Use the user's browser for menus and prices.

## Script first
`scripts/jet.py` (stdlib, GET only, 1 s between requests) picks the right host, reads deals, marks paid placements `[ad]`, and works out the delivery fee from the bands, never from `deliveryCost`.
```
python3 scripts/jet.py venues pl 00-024 --deals --open-only --basket 60 --sort fee
python3 scripts/jet.py venues uk 'EC4M 7RF' --free-delivery --json
```
`--basket` is in major units (60 = 60.00). Without it, the fee shows as a range across bands.

## Find venues
Continental brands (verified 2026-10-20 for `de`, `pl`, `nl` with curl; `pl` also with WebFetch):
```
https://rest.api.eu-central-1.production.jet-external.com/discovery/{cc}/restaurants/enriched/bypostcode/{postcode}
```
UK (verified 2026-10-20, curl):
```
https://uk.api.just-eat.io/discovery/uk/restaurants/enriched/bypostcode/{postcode}
```
Spain (verified 2026-10-20, curl). The JET spec says this host also serves DK, IE, IT and NO (unverified):
```
https://i18n.api.just-eat.io/discovery/{cc}/restaurants/enriched/bypostcode/{postcode}
```
- It needs a postcode, not lat/lon. The `bylatlong` paths return 404 on all hosts. Convert the address to a postcode first.
- Postcode formats: UK `EC4M7RF`, DE `10117`, NL `1012`, ES `28013`, PL `00-024` (with the dash).
- Use a real street postcode. Warsaw `00-001` and `00-950` return 0 restaurants; `00-024` returns 905.
- `Accept-Language: en-GB` turns deal text into English (curl only; WebFetch gets the local language).
- Responses are large (UK 320 KB, DE 255 KB). WebFetch sees about 1.6 MB of text, so page with `offset`. Prefer curl plus a small parser.
- Each venue sits in `restaurants[]`: `id`, `name`, `uniqueName`, `rating.starRating`, `rating.count`, `deliveryEtaMinutes.rangeLower/rangeUpper`, `isOpenNowForDelivery`, `deliveryCost`, `minimumDeliveryValue`, `deals[]`.
- Grocery and convenience partners (Carrefour, Sainsbury's, Co-op, Żabka Jush) appear in the same list. UK has `filters.groceries.restaurantIds` and `filters.convenience.restaurantIds`.
- `promotedPlacement` lists paid placements. List order is not a quality ranking.

Search by name, cuisine or product (UK verified 2026-10-20, curl). It returns IDs and ad flags only, so join the IDs with discovery:
```
https://uk.api.just-eat.io/search/restaurants/uk?searchTerm={term}&latlong={lat},{lon}&limit=20
```

## Menu and prices
No anonymous source works today.
- The brand pages return a Cloudflare 403 to curl and WebFetch (tested `lieferando.de/en/menu/{uniqueName}`, `just-eat.co.uk/restaurants-{uniqueName}/menu`, `pyszne.pl/menu/{uniqueName}`). Open those URLs in the user's own browser (claude-in-chrome) or ask the user to check the app.
- `/restaurants/{tenant}/{id}/catalogue` and `/catalogue/items` return 404 on the public hosts.
- `/restaurants/{tenant}/{id}/menu` needs an `Authorization` partner key per the public JET spec (unverified, not tried).
- The legacy `cw-api.takeaway.com/api/v34/restaurant?slug=` returns 404.

## Discounts
Discounts live in `restaurants[].deals[]` as `{description, offerType}` (verified 2026-10-20 for DE, PL, NL, ES). `offerType` values:
- `Percent`: % off the whole order, often with a minimum spend and a cap in the text ("Spend 50 zł • Pay 30% less", "Rabat 30% (do 20 zł) • Wydaj 50 zł").
- `ItemLevelDiscount`: % or fixed amount off "selected items". The API does not list the items.
- `Bogof`: 2-for-1. `BogofMixMatch`: cheapest item free, or second item half price.
- `FreeItem`: a free product, sometimes above a minimum spend ("Free item • From €20").
- `Notification`: a promo code in the text ("50 zł taniej z kodem PINK50").
- `StampCard`: a loyalty stamp card. The description is empty. It is not an instant discount.

Quick filters, each with `restaurantIds[]`: `filters.with_discounts` (or `offers`), `filters.free_delivery`, `filters.stampcards`, `filters.exclusive_offers` (Just Eat+, Lieferando+, Pyszne.pl+ membership; 0 venues show for anonymous calls).

UK: `deals[]` was empty for all 2,043 venues near EC4M 7RF, and `with_discounts` was 0. UK restaurant deals are not exposed anonymously. Only `free_delivery` works. UK `filters` also hold platform voucher campaigns (`loyalty-offer-*`, `reminder_*-voucher-*`, `repeat-offer-*`, such as "£10 off your next order"). Those target specific accounts. Do not report them as open to everyone.

## Fees
Use `deliveryFees.restaurants["{id}"]`, not `deliveryCost`:
```
{"minimumOrderValue": 1800, "bands": [{"minimumAmount": 1800, "fee": 100}]}
```
- Bands set the delivery fee by basket size. Pick the highest band whose `minimumAmount` is at or below the basket. Example: fee 2.99 from 9.99, free from 40.00.
- UK grocery bands act as a small-order fee: 2.49 under 10.00, 0.49 above.
- Service fee and small-order surcharge are not in discovery. The fees endpoint needs a Bearer token. Say "service fee not checked".

## Gotchas
- `deliveryCost` shows the cheapest band, often 0. A pizzeria with `deliveryCost: 0` really charges 12 zł until 200 zł. Read the bands.
- Units differ. `deliveryCost` and `minimumDeliveryValue` are decimal major units (1.99). `bands[].fee`, `bands[].minimumAmount` and `minimumOrderValue` are minor units (199 = 1.99).
- Discovery has no currency field. Infer it from the country (GBP, EUR, PLN, DKK, NOK). UK search returns `currencyCode`.
- `isOpenNowForDelivery` is false for many venues. Filter on it before you rank.
- Offers depend on the delivery area and change often. Give the date.
