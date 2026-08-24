---
name: hotel-hunting
version: 1.0.0
description: Use when finding hotels. Verifies quality and booking.
author: Sliday
license: MIT
metadata:
  hermes:
    tags: [travel, hotels, reviews, booking, hotelist]
    related_skills: [travel-itinerary-planning]
triggers:
  - "find me a hotel"
  - "hotel hunting"
  - "where should we stay"
  - "compare these hotels"
  - "best hotel in"
  - "boutique hotel"
  - "hotel with parking"
  - "hotel for these dates"
  - "is this hotel actually good"
  - "check hotel reviews"
mutating: false
---

# Hotel Hunting

## When to Use

Use for hotel discovery, comparison, review forensics, exact-date availability checks, and choosing where to stay. Pair it with `travel-itinerary-planning` when the hotel must fit a driving route, EV plan, airport/rail transfer, or multi-day itinerary.

## Contract

This skill turns a destination and stay brief into a **decision-ready hotel shortlist**. It guarantees:

- hard constraints are applied before taste or ratings;
- Hotelist is used as a high-value discovery and normalization layer when it covers the destination, but never as the sole source;
- aggregate ratings are decomposed into source agreement, review recency, recurring complaints, independent trip reports, and visual evidence;
- exact dates, occupancy, room/bed configuration, full price, cancellation, parking, and other decisive operational facts are verified before calling a stay bookable;
- the result contains at most three finalists, one winner, one fallback, explicit uncertainty, and direct links.

The point is not to find the hotel with the highest displayed score. The point is to avoid a stay whose hidden failure mode matters to this traveler.

## Scope and routing

Use this skill for hotel discovery, comparison, quality checks, and exact-stay verification. Invoke `travel-itinerary-planning` as well when hotel choice depends on route geometry, EV driving limits, airport/rail access, or a multi-day itinerary.

The claim that every large platform suppresses negative reviews should be treated as a **reason to triangulate**, not as an established universal fact. A 4.7 is evidence, not truth; Hotelist is evidence, not truth either.

## Phase 1 — Resolve the stay brief

Recover known trip context and ask only for missing facts that materially change the search:

1. exact check-in and check-out dates;
2. travelers, child ages, rooms, and acceptable bed arrangements;
3. destination area plus route anchors or onward destination;
4. total nightly or stay budget, including taxes and parking;
5. hard requirements: parking, EV charging, air conditioning, elevator, accessibility, kitchen, workspace, pool, gym, pet policy, late check-in, etc.;
6. hard exclusions: historic-center driving, nightlife noise, resorts, chains, shared bathrooms, sofa beds, non-refundable rates, and so on;
7. taste: boutique/minimalist, historic, warm, modern, local character, view, breakfast quality;
8. the one failure mode that would ruin the stay.

When a trip is by car, ask whether easy road access, parking, or avoiding restricted historic centers should be a hard gate.

Write a compact brief before searching:

```text
Stay: <dates>, <nights>, <travelers/rooms>
Hard gates: <must-haves and exclusions>
Soft ranking: <taste and nice-to-haves>
Dealbreaker: <single most important failure mode>
Budget basis: <per night or total; taxes/parking included or not>
```

If dates are unknown, discovery can proceed, but price and inventory must be labeled provisional.

## Phase 2 — Build a broad candidate set

Search enough sources to escape the incentives and blind spots of any one platform.

### 2.1 Hotelist pass

Use `https://hotelist.com` or its public MCP endpoint `https://hotelist.com/mcp` when available. The MCP exposes:

- `search_hotels`: top candidates for a city with AI rating, price, pros/cons, and filters;
- `get_hotel`: rating breakdown, consensus, amenities, year built, and photo;
- `list_cities`: destination coverage.

Capture:

- Hotelist Score;
- AI photo and review ratings;
- consensus across sources;
- normalized per-source ratings;
- extracted pros and cons;
- claimed amenities and whether photos appear to support them;
- year built/renovated when available;
- canonical Hotelist URL.

Interpretation:

- high score + high consensus is stronger than high score + low consensus;
- low consensus is not automatic rejection, but it triggers deeper complaint and room-type analysis;
- an “Exceptional” badge or AI vision score is a lead, not proof of exact-room condition, service, quiet, or bookability;
- Hotelist's displayed price is discovery data until the exact stay is checked elsewhere.

If Hotelist has weak or no coverage, say so and continue. Do not quietly shrink the market to what one database contains.

### 2.2 Independent discovery

Add candidates from a mix of:

- official hotel sites and recognized design/boutique collections;
- Google Maps or Apple Maps for geography, volume, recent photos, and recurring operational complaints;
- Booking.com, Expedia, Hotels.com, Agoda, Trip.com, Airbnb, or a relevant local platform;
- recent Reddit threads, travel forums, personal blogs, YouTube room tours, and credible trip reports;
- specialist evidence when relevant: MICHELIN Key, Tablet, Design Hotels, Mr & Mrs Smith, Historic Hotels, family/accessible travel sources.

Do not assume editorial inclusion proves current quality, or that affiliate content is independent. Record the date and likely incentive of each source.

Aim for 8–15 raw candidates, then gate them down. Do not deeply investigate dozens of hotels.

## Phase 3 — Apply hard gates before scoring

Reject or quarantine any candidate that fails a hard requirement. Verify the gate at the source best positioned to know it:

- **Location:** map geometry and actual approach, not neighborhood marketing language.
- **Parking:** official terms; distinguish on-site, off-site, valet, public garage, reservation required, vehicle-size limit, price, and whether access crosses a restricted zone.
- **EV charging:** on-site versus nearby public charging; connector, power, guest access, reservation, price, and non-Tesla compatibility.
- **Occupancy:** exact room capacity and child-age policy, not a generic “family-friendly” badge.
- **Beds:** actual bed and sofa-bed arrangement; a cot is not a bed for an older child.
- **Accessibility:** room-specific and route-specific details, not an accessibility icon alone.
- **Air conditioning:** room-level availability and seasonal operation; “climate control” may not mean guest-controlled cooling.
- **Late arrival:** staffed desk or explicit self-check-in procedure.

Use evidence labels:

- **confirmed** — explicit current source or exact-stay result;
- **likely** — strong indirect evidence, but not the decisive final state;
- **unverified** — claim exists but cannot be validated;
- **conflicting** — credible sources disagree;
- **failed** — hard gate is not met.

A high rating never rescues a failed hard gate.

## Phase 4 — Audit quality beyond the headline score

### 4.1 Rating and source triangulation

For each surviving candidate, collect current rating, review count, and recency from at least two materially independent sources when possible. Avoid double-counting syndicated reviews as independent evidence.

Prefer:

- a stable pattern across sources;
- substantial recent review volume;
- agreement on the hotel's specific strengths and weaknesses;
- owner responses that address problems concretely rather than attacking guests.

Do not compare raw 4.7/5 with 9.0/10 as if the scales and populations are equivalent. Use Hotelist's normalized score when available. If normalizing manually, compare the hotel with a **same-city, same-platform candidate set** and report rank/percentile or relative position; never invent a global conversion from a tiny sample.

### 4.2 Complaint mining

Search candidate name plus concrete failure terms in English and the local language when useful:

```text
"<hotel>" noise OR loud OR nightclub OR construction
"<hotel>" dirty OR mold OR smell OR bedbugs
"<hotel>" air conditioning OR AC OR hot room
"<hotel>" wifi OR internet OR desk
"<hotel>" parking OR garage OR narrow OR restricted zone
"<hotel>" breakfast OR coffee
"<hotel>" renovated OR old room OR worn
"<hotel>" reddit
"<hotel>" room tour
```

Classify each complaint:

- **recurring structural:** street noise, thin walls, tiny rooms, bad access, weak HVAC;
- **room-type/floor-specific:** courtyard rooms, annex, basement, top floor, old wing;
- **seasonal/temporary:** construction, pool closure, summer AC load;
- **service variance:** check-in, housekeeping, breakfast queues;
- **isolated/unverifiable:** one unsupported report.

A repeated specific complaint across sources matters more than dozens of generic “amazing stay” reviews. Quote or paraphrase representative evidence with source/date links. Do not treat one dramatic anecdote as consensus.

### 4.3 Photo forensics

Inspect official photos, recent guest photos, map uploads, and video tours. Prefer room-type-specific recent guest media. Check:

- room and bathroom wear, grout, mold, stains, damaged furniture;
- natural light, window size, privacy, and actual view;
- bed clearance, luggage space, desk ergonomics, sockets;
- whether wide-angle photography masks room size;
- shower design, ventilation, storage, and water-damage clues;
- road, tram, bar, elevator, plant-room, or construction proximity;
- breakfast freshness and seating, not only buffet abundance;
- whether “gym,” “pool,” “kitchen,” “balcony,” or “workspace” exists in usable form;
- mismatch between renovated hero rooms and older room categories.

AI vision is useful for consistency and amenity checks, but it cannot reliably prove quiet, smell, mattress quality, water pressure, temperature control, or staff behavior.

### 4.4 Independent traveler evidence

Use Reddit, forums, blogs, and videos to answer questions platforms often flatten:

- What was unexpectedly bad?
- Which room/floor/wing should be requested or avoided?
- Is the area pleasant after dark?
- Is the hotel still good after a renovation, ownership change, or rapid expansion?
- Does the breakfast/coffee/workspace/pool actually justify choosing the property?

Check dates. A detailed 2019 post can explain building geometry but not current maintenance or management.

## Phase 5 — Verify the exact stay

For the top three only, open the official booking engine and one major booking platform with explicit:

- check-in and check-out;
- adults, child ages, rooms;
- currency and destination market;
- chosen room type and bed configuration.

Capture:

1. exact room/rate or explicit sold-out state;
2. total price including mandatory taxes and resort/destination fees;
3. parking, breakfast, and other unavoidable extras;
4. cancellation deadline, prepayment, and no-show terms;
5. bed configuration and room size;
6. check-in/out and late-arrival procedure;
7. whether the room shown in the rate matches the media reviewed;
8. official direct-booking benefits or material platform differences.

An enabled calendar day, “from” price, flexible-date carousel, search-result card, or scarcity banner is not confirmed inventory. Continue until the exact room table or checkout summary appears. Do not book or submit payment unless explicitly asked.

If two channels conflict, prefer the narrower claim and explain the conflict. Preserve a clean direct hotel/property URL rather than a session-heavy affiliate link where possible.

## Phase 6 — Rank on a transparent decision surface

Use hard gates first, then a compact scorecard. Suggested weights are adjustable, not universal:

| Dimension | Default weight |
|---|---:|
| Exact fit and operational certainty | 25% |
| Recurring complaint risk / sleep quality | 20% |
| Location and access friction | 15% |
| Room and visual quality | 15% |
| Independent traveler consensus | 10% |
| Service and breakfast | 5% |
| Value at exact total price | 10% |

For a one-night road trip, access and parking may outweigh visual distinction. For a long city stay, room ergonomics, neighborhood, laundry, kitchen, and workspace may dominate. For a restorative trip, quiet, bed, climate control, and natural light should dominate.

Apply explicit risk penalties for:

- source disagreement or low consensus;
- recent recurring structural complaints;
- unverified decisive amenities;
- the desired room category being different from the one reviewed;
- old/low-volume evidence;
- hidden mandatory fees or restrictive cancellation;
- a beautiful property that creates daily route friction.

Do not let ten weak positives average away one credible dealbreaker.

## Output format

Lead with the decision, not the research diary.

```text
Best move: <hotel> — <one-line reason>
Exact stay: <room, bed setup, total price, cancellation, verification status>
Why it wins: <3 specific strengths>
Watch-out: <most credible downside and mitigation/room request>
Links: <official> · <Hotelist> · <map> · <booking>

Fallback: <hotel> — <when it is the better choice>
Wildcard: <hotel> — <only if genuinely distinct>

Rejected after checking:
- <hotel>: <failed gate or recurring dealbreaker>

Confidence: <high/medium/low>
Still unverified: <single fact that could change the choice>
```

At most three finalists. Include a compact comparison table only when it helps the decision:

| Hotel | Exact total | Hard gates | Hotelist/consensus | Main risk | Verdict |

Cite current source links for decisive claims.

## Verification checklist

- [ ] Exact stay brief and dealbreaker are clear.
- [ ] Hotelist checked or coverage limitation stated.
- [ ] Broad set came from more than one incentive system.
- [ ] Hard gates applied before ratings.
- [ ] At least two materially independent review sources checked for finalists when available.
- [ ] Recent negative reviews and recurring complaint patterns inspected.
- [ ] Official and recent guest photos inspected for the actual room category.
- [ ] Exact dates, occupancy, bed setup, room/rate, and total price verified.
- [ ] Parking/EV/access terms verified when relevant.
- [ ] Winner, fallback, rejected candidates, and uncertainty are explicit.
- [ ] No booking/payment was submitted without explicit permission.

## Anti-patterns

- Sorting Booking.com or Google Maps by score and calling the first result “best.”
- Treating Hotelist, an AI summary, or a normalized score as an oracle.
- Repeating broad allegations about review deletion as established fact without evidence.
- Comparing raw ratings across incompatible platforms.
- Counting syndicated copies of the same review corpus as independent consensus.
- Reading only positive reviews or only the most dramatic one-star review.
- Ignoring review dates, room category, floor, wing, season, or ownership changes.
- Trusting marketing photos when recent guest photos show another product.
- Calling parking “on-site” when it is a public garage nearby.
- Calling a room available from a calendar, teaser price, or search card.
- Hiding taxes, parking, breakfast, resort fees, or non-refundable terms.
- Offering ten plausible hotels instead of choosing.
- Optimizing aesthetics while ignoring sleep, HVAC, access, beds, or route friction.

## Tools used

- Memory or profile lookup when available: recover traveler preferences and current trip context without exposing private details.
- `web_search` / `web_extract`: discover official pages, independent reports, and indexed complaints.
- Browser tools: inspect Hotelist, maps, dynamic booking engines, exact rates, recent reviews, and photos.
- `vision_analyze`: inspect screenshots or room/amenity photos when visual evidence is decisive.
- Hotelist MCP (`https://hotelist.com/mcp`) when connected: structured hotel discovery and detail retrieval.
