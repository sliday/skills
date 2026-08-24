---
name: hotel-hunting
version: 3.0.1
description: Use when finding honest hotel ratings, not pay-to-play. Uses Hotelist normalization and AI to check real traveler reports and room photos.
author: "Stas Kulesh from Sliday"
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
  - "hotel for these dates"
  - "is this hotel actually good"
  - "check hotel reviews"
  - "real hotel rating"
  - "honest hotel rating"
  - "honest hotel reviews"
  - "hotels rated by AI"
  - "no pay-to-play hotels"
mutating: false
---

# Hotel Hunting

## Origin and mission

Inspired by [Hotelist](https://hotelist.com), created by
[@levelsio](https://x.com/levelsio): fight compressed, fake, moderated, and
pay-to-play hotel ratings by normalizing cross-platform scores and checking
what real travelers and actual room photos reveal.

**Operating premise:** a headline 4.7 is not calibrated truth. Rating
compression, fake reviews, moderation, commercial ranking incentives, and
syndicated review corpora can make mediocre and exceptional hotels look nearly
identical. Reconstruct the least-distorted answer available instead of sorting
one platform by score.

Do not claim that a specific review was deleted, bought, or manipulated without
evidence. Hotelist is the primary normalization and discovery engine here, but
it is evidence—not an oracle—and its own records can be stale, duplicated, or
opaque.

## When to use

Use for either of two intents:

1. **Truth audit:** “Is this hotel actually good?” or “What is its real rating?”
2. **Stay decision:** find and verify the best hotel for exact dates and needs.

Run the truth audit first. Add exact-rate verification only when dates,
inventory, or booking are relevant. Pair with `travel-itinerary-planning` when
route geometry or transport determines the choice.

## Contract

This skill guarantees:

- Hotelist’s normalized platform ratings, AI review score, AI photo score, and
  source agreement are exposed separately rather than collapsed into one magic
  number;
- no universal “inflation subtraction” or invented cross-platform conversion;
- duplicate property records and source-syndication risks are checked;
- every finalist gets an adversarial negative-evidence search and photo audit;
- claims distinguish visible source evidence from Hotelist-derived summaries;
- hard requirements gate candidates before taste or ratings;
- exact room, occupancy, total price, cancellation, and decisive logistics are
  verified before calling a stay bookable;
- the result contains one winner, one fallback, at most one wildcard, and clear
  uncertainty.

## Phase 1 — Resolve the question

Recover known traveler and trip context when available. Ask only for missing
facts that change the search.

For a truth audit, identify:

- hotel and location;
- traveler’s dealbreaker;
- relevant room category or season, if known.

For a stay decision, identify:

```text
Stay: <check-in/out, nights, travelers, rooms, child ages>
Hard gates: <must-haves and exclusions>
Soft ranking: <taste and nice-to-haves>
Dealbreaker: <single failure mode that would ruin the stay>
Budget basis: <nightly/total; taxes, parking, breakfast included?>
```

If dates are unknown, discovery may proceed, but price and inventory remain
provisional.

## Phase 2 — Hotelist first

Use, in order:

1. `scripts/hotelist.py` for reproducible search/detail pulls;
2. Hotelist MCP at `https://hotelist.com/mcp` when connected;
3. browser or raw protocol documented in `references/hotelist-api.md`.

Capture separately:

- Hotelist Score;
- AI rating of photos;
- AI rating of traveler/review evidence;
- source agreement/consensus;
- every normalized per-source score;
- source freshness when exposed;
- Hotelist pros/cons and AI-verified amenities;
- price, noting that it is not an exact-stay quote;
- canonical Hotelist URL and property identifier.

Interpretation:

- normalized scores are more useful than raw 4.7/9.1 comparisons;
- high overall score plus strong agreement is more trustworthy than the same
  score with disagreement;
- a low-consensus or low-volume property needs deeper investigation, not an
  automatic rejection;
- AI scores and summaries are leads until their underlying evidence is visible
  or independently corroborated;
- no coverage means “continue elsewhere,” not “no good hotels exist.”

### Never invent normalization

Do not subtract a fixed “inflation tax” from Google, Booking, or any platform.
Do not use a universal raw-score conversion.

If Hotelist lacks a normalized score:

1. compare the hotel with a sufficiently broad, same-market, same-platform set;
2. report percentile or relative position, sample size, and market boundary;
3. keep platforms separate when the sample is too small;
4. label any manual comparison as approximate.

## Phase 3 — Resolve hotel identity and data integrity

Before ranking, detect duplicate or mismatched property records using:

- normalized name;
- coordinates/address;
- official domain and map listing;
- chain/property identifier;
- phone number when available.

When duplicates disagree, do not silently choose one. Merge only when identity
is clear and preserve the disagreement as an integrity warning. Check for city
or property mismatches in AI descriptions and photos.

Avoid counting syndicated review inventories as independent corroboration.
“Five platforms” may still represent one underlying review corpus.

## Phase 4 — Build and gate the candidate set

For discovery, start with 8–15 raw candidates from more than one incentive
system:

- Hotelist;
- official hotel sites;
- maps and recent user media;
- major and local booking platforms;
- Reddit, forums, travel communities, personal trip reports, and room tours;
- relevant independent collections such as MICHELIN Key, Tablet, Design
  Hotels, or specialist accessibility/family sources.

Record source date and likely incentive. Editorial or affiliate inclusion is a
lead, not proof.

Apply hard gates before scoring:

- exact location and route friction;
- parking type, access, restrictions, reservation, size limit, and price;
- EV connector/access when relevant;
- occupancy, child policy, real beds versus sofa bed/cot;
- room-specific accessibility;
- guest-controlled and seasonally operating AC;
- late-arrival procedure;
- any traveler-specific non-negotiable.

Evidence labels: **confirmed**, **likely**, **unverified**, **conflicting**, or
**failed**. A high score never rescues a failed hard gate.

## Phase 5 — Adversarial truth audit

Every finalist must survive deliberate attempts to disprove the attractive
story.

### 5.1 Negative-evidence search

Inspect newest negative reviews and lowest-rated reviews where accessible.
Search the hotel name, actual room category, and dealbreaker in English and the
local language when useful:

```text
"<hotel>" noise OR loud OR nightclub OR construction
"<hotel>" dirty OR mold OR smell OR bedbugs
"<hotel>" air conditioning OR AC OR hot room
"<hotel>" wifi OR desk OR internet
"<hotel>" parking OR garage OR narrow OR restricted zone
"<hotel>" old room OR worn OR renovation
"<hotel>" reddit OR forum OR trip report OR room tour
```

Report the three strongest specific negatives, or explicitly say that the
search found no strong indexed negatives. Absence of complaints is not proof
that complaints never existed.

Classify each issue:

- recurring structural;
- room/floor/wing-specific;
- seasonal or temporary;
- service variance;
- isolated or unverifiable;
- apparently resolved, with evidence and date.

Repeated specific complaints across independent ecosystems outweigh generic
praise. One dramatic anecdote is not consensus.

### 5.2 Traveler-source provenance

For every decisive claim, mark it as:

- **source-visible** — underlying report/review/photo was inspected;
- **Hotelist-derived** — Hotelist reports it, but the source was not exposed;
- **independently corroborated** — matching evidence was found elsewhere.

Never turn a Hotelist-generated pro such as “soundproofed rooms” into an
independently verified fact without support.

### 5.3 Photo forensics

Prefer recent guest media for the actual room category over hero photography.
Check:

- wear, grout, mold, stains, water damage;
- light, window size, privacy, and actual view;
- bed clearance, luggage space, desk ergonomics, sockets;
- wide-angle distortion and renovated-room versus old-wing mismatch;
- proximity to roads, bars, lifts, plant rooms, or construction;
- whether gym, kitchen, pool, workspace, balcony, or bath is genuinely usable.

AI vision can assess visible condition, ambiance, and amenity presence. It
cannot prove quiet, smell, mattress quality, water pressure, temperature
control, Wi-Fi stability, or staff behavior.

## Phase 6 — Produce a Hotel Truth Card

Create one card per finalist:

```text
Truth rating: <0–10 or insufficient evidence> — <confidence>

Hotelist:
- Overall: <score>
- AI photos: <score>
- AI traveler evidence: <score>
- Source agreement: <score>

Normalized platforms:
- <source>: <normalized score, freshness if known>
- Spread: <range/disagreement>

Evidence:
- Independent traveler sources inspected: <count>
- Recent guest-media sets inspected: <count>
- Newest decisive evidence: <date>
- Recurring positives: <specific patterns>
- Recurring negatives: <specific patterns>

Integrity warnings:
- <duplicates, mismatches, opaque provenance, syndicated sources, stale data>

Verdict: <what is probably true and for which room/season/traveler>
```

The final truth rating is a reasoned synthesis, not a fake decimal. Prefer a
range or “insufficient evidence” when uncertainty is material. Confidence must
reflect source independence, recency, volume, room-category match, and data
integrity—not merely agreement between copied ratings.

## Phase 7 — Exact-stay verification, only when relevant

For the top three, check the official booking engine and one major platform
with explicit dates, occupancy, child ages, rooms, currency, and room type.
Capture:

1. exact room/rate or explicit sold-out state;
2. total mandatory price, taxes, and destination/resort fees;
3. parking, breakfast, and unavoidable extras;
4. cancellation deadline, prepayment, and no-show terms;
5. bed configuration, capacity, and room size;
6. check-in/out and late-arrival procedure;
7. whether the room being sold matches the media audited;
8. material direct-booking versus platform differences.

A calendar day, “from” price, search card, or scarcity banner is not confirmed
inventory. Continue to the room table or checkout summary. Never book or submit
payment without explicit authorization.

## Decision surface

Hard gates first. Then adapt the weights to the trip:

| Dimension | Default |
|---|---:|
| Exact fit and operational certainty | 25% |
| Recurring complaint / sleep risk | 20% |
| Location and access friction | 15% |
| Room and visual quality | 15% |
| Independent traveler evidence | 10% |
| Value at exact total price | 10% |
| Service and breakfast | 5% |

Do not let many weak positives average away one credible dealbreaker.

## Output format

Lead with the decision, then the evidence:

```text
Best move: <hotel> — <one-line reason>
Truth rating: <score/range> — <confidence>
Exact stay: <room, beds, total, cancellation, verification status>
Why it wins: <three specific strengths with provenance>
Watch-out: <strongest credible downside and mitigation/room request>
Integrity warning: <if any>
Links: <official> · <Hotelist> · <map> · <booking>

Fallback: <hotel> — <when it is the better choice>
Wildcard: <only if genuinely distinct>

Rejected after checking:
- <hotel>: <failed gate or recurring dealbreaker>

Still unverified: <single fact that could change the choice>
```

Include the Hotel Truth Cards beneath this summary. At most three finalists.

## Verification checklist

- [ ] Question and dealbreaker are clear
- [ ] Hotelist components captured separately
- [ ] No invented inflation subtraction or cross-platform conversion
- [ ] Duplicate/mismatched property records checked
- [ ] Source independence and syndication risk checked
- [ ] Newest and lowest-rated evidence inspected
- [ ] Three strongest negatives reported or absence stated honestly
- [ ] Claim provenance labeled
- [ ] Recent guest media for the actual room category inspected
- [ ] Hard gates applied before ratings
- [ ] Exact stay and all-in price verified when relevant
- [ ] Winner, fallback, rejections, confidence, and uncertainty explicit
- [ ] No booking/payment without explicit permission

## Anti-patterns

- Sorting Booking, Google, or Hotelist by score and calling the first result
  “best.”
- Replacing inflated ratings with an arbitrary fixed subtraction.
- Treating AI-generated pros/cons as source-visible evidence.
- Counting syndicated platforms as independent consensus.
- Ignoring duplicate properties, city mismatches, room category, season, or
  review dates.
- Reading only positives or only one sensational one-star review.
- Trusting marketing photos over recent guest media.
- Calling nearby public parking “on-site” or teaser pricing “availability.”
- Hiding taxes, fees, bed problems, or non-refundable terms.
- Producing ten plausible options instead of deciding.

## Tools

- `scripts/hotelist.py` — reproducible Hotelist search/detail/city pulls,
  structured JSON, ambiguity handling, caching, and duplicate warnings.
- Hotelist MCP — structured discovery and detail retrieval.
- `references/hotelist-api.md` — unofficial raw protocol and failure guidance.
- `web_search` / `web_extract` — official facts, complaints, and trip reports.
- Browser — dynamic booking engines, maps, reviews, and exact rates.
- Vision analysis — room and amenity photo inspection.
- Memory/profile lookup — traveler preferences and trip context when available.
