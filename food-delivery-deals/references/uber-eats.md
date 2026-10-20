# Uber Eats (ubereats.com, incl. grocery and convenience stores)
Markets: UK, Spain, Poland and many more (tested London GBP, Madrid EUR, Warsaw PLN).
Access (tested 2026-10-20): The web app's JSON API at `/api/{rpc}` works with curl POST and no account. Public HTML pages and `/_p/api/` return a Cloudflare 403 to curl and WebFetch. WebFetch can only GET, so in a WebFetch-only sandbox Uber Eats is out of reach. Use the user's browser or the app.

The official Uber Eats APIs (developer.uber.com) are for merchants and POS partners only. They need written approval and OAuth scopes and have no consumer browsing. Everything below is the undocumented web API, so it can change without notice.

## How to call
Every call is `POST https://www.ubereats.com/api/{rpc}?localeCode={loc}` with these headers:
- `Content-Type: application/json`
- `x-csrf-token: x` (a literal "x")
- a normal desktop User-Agent
- for anything location-based, the cookie `uev2.loc=<url-encoded JSON>`. This is the delivery spot the site stores for anonymous visitors. Minimal JSON that works:
```
{"address":{"address1":"London","address2":"London","aptOrSuite":"","eaterFormattedAddress":"London","subtitle":"London","title":"London","uuid":""},
 "latitude":51.508,"longitude":-0.1281,"reference":"","referenceType":"google_places","type":"google_places",
 "addressComponents":{"city":"London","countryCode":"GB","firstLevelSubdivisionCode":"","postalCode":""},
 "categories":[],"originType":"user_autocomplete","source":"manual_auto_complete","userState":"Unknown"}
```
`localeCode` sets the language of the offer text: `gb`, `es` (Spanish), `es-en` (English in Spain), `pl-en`. Use `{cc}-en` to get English labels.
Without the cookie, getFeedV1 returns "No stores available". Call only the `/api/` paths in this file. Don't fetch store HTML pages.

## Find venues
```
POST /api/getFeedV1
{"userQuery":"","date":"","startTime":0,"endTime":0,"carouselId":"","sortAndFilters":[],"billboardUuid":"",
 "feedProvider":"","promotionUuid":"","targetingStoreTag":"","venueUuid":"","selectedSections":[],"favorites":"",
 "vertical":"","searchSource":"","searchType":"","keyName":"","pageInfo":{"offset":0,"pageSize":80}}
```
Verified 2026-10-20 (London, Madrid, Warsaw). It returns about 2 MB. `data.currencyCode` gives the currency. Store rows are `data.feedItems[]` with `type == "REGULAR_STORE"`. Read `.store`:
- `storeUuid`, `title.text`, `rating.text`, `actionUrl` (`/store/{slug}/{shortId}`)
- `meta[]`: `badgeType` `ETD` is the ETA ("37 min"), `FARE` is the delivery fee ("£1.99 Delivery Fee"; few rows have it), plus `NEW_STORE` and `EXCLUSIVE_STORE`
- `signposts[].text` is the offer badge. Strip leading spaces.

**Offers only (the best starting point).** Put the deals filter in `sortAndFilters`. Read the IDs from `data.sortAndFilters[]` where `type == "dealsFilter"`. These worked in London and Warsaw:
```
"sortAndFilters":[{"uuid":"33e0f7cc-8927-4dac-a92e-19a296aab097","options":[{"uuid":"g996476c-2b1b-4db2-b40a-13d43cb117dc"}]}]
```
Verified 2026-10-20 (Warsaw): 50 of 50 rows had offers, 313 KB. Page with `data.meta.hasMore` and `data.meta.offset`, which goes back into `pageInfo.offset`.

Search by name (small and fast, good for finding the same restaurant on another app):
```
POST /api/getSearchSuggestionsV1
{"userQuery":"burger king","date":"","startTime":0,"endTime":0,"vertical":"ALL"}
```
Verified 2026-10-20. Read `data[].store.{uuid,title,slug}`.

Store URL to UUID: the last path part is the UUID in base64url. `1xRv9jaWTaie_ldX3DWMfA` is `d7146ff6-3696-4da8-9efe-5757dc358c7c`. In Python: `uuid.UUID(bytes=base64.urlsafe_b64decode(s+"=="))`.

## Menu and prices
```
POST /api/getStoreV1
{"storeUuid":"<uuid>","diningMode":"DELIVERY","time":{"asap":true},"cbType":"EATER_ENDORSED"}
```
Verified 2026-10-20 (300 to 520 KB). It also works without the cookie, but send the cookie so delivery range and fees match the user. Fields:
- `data.title`, `rating.ratingValue`, `rating.reviewCount`, `etaRange.text`, `isOpen`, `location.address`, `currencyCode`
- Items: `data.catalogSectionsMap[sectionUuid][].payload.standardItemsPayload.catalogItems[]` with `uuid`, `title`, `price`, `priceTagline.text`, `isSoldOut`, `isAvailable`
- `price` is in **minor units** (1099 = £10.99). It can be a float (559.3), so round it. `priceTagline.text` is the shown price.
- `metaJson` is a schema.org `Restaurant` JSON-LD string: name, cuisine, address.

## Discounts
Offers show up in three places. Read all three.
1. **Feed badge** (`store.signposts[].text`): "20% off £15+", "£5 off £30+", "£0 Delivery Fee on £15+", "Buy 1, get 1", "30% off select items", "Items on sale", "Free item on £30+". In Spain: "2×1", "20% menos en algunos artículos", "Gasta 25 € y ahorra 5%". Spend-threshold offers ("X% off £Y+") appear **only here**. getStoreV1 does not repeat them (`promotion` is null, `promoTrackings` is empty).
2. **Item BOGO**: `catalogItems[].itemPromotion.buyXGetYItemPromotion` = `{buyQuantity, getQuantity, maxRedemptionCount}`, with `itemPromotion.type == "buyXGetYItemPromotion"`. Here `price` is the full price of one item.
3. **Item % off**: `catalogItems[].promoInfo.promoBadge...text` ("30% off") plus `promoInfo.promotionUUID`. Here `price` is the **already discounted** price. `priceTagline.accessibilityText` gives both: "£5.59, discounted from £7.99".

`data.hasStorePromotion == true` means the store has some offer.
Filter what you report:
- Leave out "(new users)" offers unless the user is new, for example `modalityInfo.modalityOptions[].priceTitleRichText` "£0 Delivery Fee (new users)".
- Uber One prices and perks do not appear when logged out. Say so.

## Fees
- Delivery fee: feed `meta[]` with `badgeType == "FARE"` (shown on few rows), the delivery-fee badges in `signposts`, and `modalityInfo.modalityOptions[]` text in getStoreV1.
- Service fee, small-order fee and minimum order are not shown when logged out (`fareInfo.serviceFeeCents` is null). They appear only at checkout, which is out of scope. Report item prices and say these fees are excluded.

## Groceries
Grocery and convenience stores use the same getStoreV1 call, but it returns only the first page (about 60 items, `catalogSectionPagingInfo.offset`). `data.sections[]` lists every aisle with its `uuid`, `title` and `subsectionUuids`. Ignore `isOnSale`, because every section had it set to true. To read an aisle:
```
POST /api/getCatalogPresentationV2
{"sortAndFilters":null,"storeFilters":{"storeUuid":"<uuid>","sectionUuids":["<sectionUuid>"],
 "subsectionUuids":null,"shouldReturnSegmentedControlData":false},"pagingInfo":{"enabled":true,"offset":0},"source":"NV_L2_CATALOG"}
```
Verified 2026-10-20 (50 Household items). Items are under `data.catalog[].payload.standardItemsPayload.catalogItems[]`, with the same fields as above. Page with `data.pagingInfo.hasMore`.

## Gotchas
- curl or a script only. WebFetch gets 403 on store pages, and the API needs POST.
- If any ubereats.com call returns a 403 or a challenge page, stop using Uber Eats for this task. Don't try another path, client or network, and don't solve the challenge. Use the user's browser or the app.
- Responses are large (feed about 2 MB, store about 0.5 MB). Save the response to a file and parse it with a script. Do not ask an LLM to read the raw JSON.
- Amounts in offer text contain non-breaking spaces ("PLN 60+", "0 €"). Normalize them before matching.
- Keep volume low (a few calls per question). This is an undocumented API, so check field paths again if a call returns `"status":"failure"`.
