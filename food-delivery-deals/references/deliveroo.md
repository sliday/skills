# Deliveroo (deliveroo.co.uk, .ie, .fr, .be, .it, .ae, .com.kw, .qa, .com.sg)
Markets: UK, Ireland, France, Belgium, Italy, UAE, Kuwait, Qatar, Singapore. DoorDash owns Deliveroo since 2025, and Deliveroo has left several markets (Australia, Spain, Netherlands, Hong Kong). Both facts are from memory, not checked today; open the country site to confirm.
Access (tested 2026-10-20): public HTML pages work with curl and carry the full app state in `__NEXT_DATA__`. WebFetch returns menu names and prices but drops offers, ratings and fees. Tested in London, Paris and Dubai.

## Find venues
```
https://deliveroo.co.uk/restaurants/{city}/{area}?geohash={geohash}
```
Verified 2026-10-20 (curl 200, 2.8 MB; same on `deliveroo.fr/en/restaurants/paris/...` and `deliveroo.ae/en/restaurants/dubai/...`).
- The geohash sets the location. The city and area in the path don't matter; the site redirects to the right area. Six characters (about 1 km) is enough. Compute it from lat/lon:
  ```python
  def geohash(lat, lon, n=6):
      b32, rng, out, val = "0123456789bcdefghjkmnpqrstuvwxyz", {0: [-180.0, 180.0], 1: [-90.0, 90.0]}, "", 0
      for i in range(n * 5):
          r, v = rng[i % 2], (lon, lat)[i % 2]
          mid = (r[0] + r[1]) / 2
          val = val * 2 + (v >= mid)
          r[0 if v >= mid else 1] = mid
          if i % 5 == 4:
              out, val = out + b32[val], 0
      return out
  ```
- Parse the JSON in `<script id="__NEXT_DATA__" type="application/json">`. Venue cards are dicts under `props.initialState.home.feed.results.data[]` that have the key `partner-name.content`. Walk the tree and collect them.
- Card fields: `partner-rating.content`, `partner-rating-count.content`, `home-units-delivery-time.content` (minutes), `distance-presentational.content`, offer badge `promotional-tag-1-main-tag-label.content` (large cards) or `tag-text.content` (small cards). Link and ID: `partner-card.on-tap.action.parameters.restaurant_href` and `.restaurant_id`.
- The same venue shows up in many carousels. Dedupe by `restaurant_id`. London (Soho) gave 215 cards.
- Cards don't show the delivery fee. Pick-up cards (`pick-up.content`) are takeaway, not delivery.

## Menu and prices
```
https://deliveroo.co.uk{restaurant_href}
e.g. https://deliveroo.co.uk/menu/London/soho/shake-shack-oxford-street?day=today&geohash=gcpvhdebpbht&time=ASAP
```
Verified 2026-10-20 (curl 200, 1.2-3.3 MB; WebFetch also works).
- Use the exact `restaurant_href` from the listing. A guessed slug returned a Cloudflare "Just a moment" page (403).
- State path: `props.initialState.menuPage.menu.metas.root`.
  - `restaurant`: `id`, `name`, `currencyCode`, `branchType` (`RESTAURANT`, `ON_DEMAND_CONVENIENCE` for shops).
  - `categories[]`: `id`, `name`.
  - `items[]`: `name`, `categoryId`, `available`, `price.fractional` (minor units: 1615 = £16.15), `price.code`, `price.formatted`, `priceDiscounted` (same shape or null), `offerText`, `unitOfMeasurementPricing`.
  - `customerLocation`: lat, lon and geohash the page used.
- WebFetch on this URL gave item names and prices, but no delivery fee and no offer.

## Discounts
1. **Area scan:** read the badges on the listing. London, 2026-10-20: "Spend £10, Get £0 delivery fee" (114 of 150 large cards), "Buy 1, get 1 free", "Spend £15, get 25% off", "Free item on £25+", "30% off selected items on £20+", "20% off entire menu".
2. **Venue offers:** `metas.root.offer.offers[]`, each with `typeName` (`FreeDeliveryOffer`, `ItemSpecificPercentOffOffer`, `AmountOffOnMultipleItemMultibuyOffer`), `percentageDiscount`, `minimumOrderValue.fractional` and `itemIds`. `offer.progressBar.offer` holds the free-delivery threshold ("Spend £10.00 to get free delivery").
3. **Item level:** `items[].priceDiscounted` and `items[].offerText`. Grocery venues fill these well: Waitrose had 137 of 247 items marked, for example eggs £4.10 → £3.08 "25% off" and milk "2 for £4.80".
- "Selected items" offers can leave `itemIds` empty with no item marked in the HTML (Pasta Evangelists, 30% off on £20+). Report the offer and tell the user to open the offer section in the app to see the items.
- New-user offers: the menu banner text in `menu.layoutGroups[].layouts[].carouselBlocks[].lines[].spans[].text` says "New users only. Min spend £10. Fees apply." Leave these out unless the user is new.
- Deliveroo Plus lowers delivery fees ("Plus members get a discount" in the fee modal, `menu.uiTargetModals`). Pages without login show prices for non-members.

## Fees
- `menuPage.menu.header.uiRows[].data`:
  - `delivery-fee.content`: "£0.49 delivery fee"
  - `small-order-fee.content`: "£8.00 minimum" (minimum spend)
  - `strikethrough-delivery-fee.content`: the fee before a free-delivery offer
  - `pricing-education.content`: "Other fees apply"
- The service fee shows only at checkout. Say so in the report. The delivery fee depends on distance, so use the user's own geohash.

## Groceries
- Same listing and menu URLs. Waitrose, Co-op and others appear as normal cards. Deliveroo HOP (own grocery) is a tile with `menu_tag` "deliveroo hop".
- Items carry `unitOfMeasurementPricing` ("2L · £1.75/L") for per-unit comparison. Categories include "Offers" and loyalty-card ones such as "My Waitrose", which need the store's card.
- The HTML held 247 items in 44 categories for Waitrose. The app loads more as you scroll, so a missing item may still be in stock.

## Consumer API (unverified)
```
POST https://api.uk.deliveroo.com/consumer/graphql/
```
A GET returned 422, so the endpoint exists and wants a GraphQL POST. The query shape wasn't tested, and WebFetch can't POST. Use the HTML pages instead.

## Gotchas
- Money: divide `fractional` by 100 for GBP, EUR, AED, QAR and SGD. KWD has 3 decimals, so divide by 1000 or read `formatted` (Kuwait not tested).
- Offer text can hold invisible Unicode marks (U+202C seen after "20%" in "20% off"). Strip them before matching.
- Pages are 1-3 MB. Fetch with curl, parse with a script, and wait about 1 s between requests.
- Offers change during the day (lunch deals, timed items). Give the time of the check.

## Other platforms
### DoorDash (US, Canada, Australia, New Zealand, Japan, Germany)
- Access: blocked. curl and WebFetch both got 403 on `doordash.com` home and `/food-delivery/{city}-restaurants/` pages (Cloudflare `challenge-platform`). Tested 2026-10-20.
- No working path without a browser. Use the user's own browser (claude-in-chrome) or ask them to check the app.
- DoorDash also owns Wolt and Deliveroo. Where those operate, use their files instead.

### Box (box.gr, Greece)
- Access: partial. box.gr is a client-side app. Its JSON API lives at `https://consumer.box.gr/api`.
- `https://consumer.box.gr/api/promos/campaigns`: verified 2026-10-20 (curl 200, no login). `payload.promoCampaigns[]` lists platform campaigns with `title`, `type` (for example `payment` for bank-card deals), `enabled`, `beginDate` and `endDate` (Unix seconds).
- Shops and menus: `/api/shops/getItems` returned 400 without `collectionType` and a postal code. The app looks a shop up by its vanity URL with `lat`, `lng` and `postalCodes`. Unverified; fall back to the user's browser.

### Poland, beyond Pyszne.pl
- Restaurant delivery in Poland runs on Pyszne.pl, Wolt, Glovo, Uber Eats and Bolt Food. See their files.
- For groceries, Frisco.pl serves its homepage to curl (200, 1.7 MB). Its product and price data is unverified.
