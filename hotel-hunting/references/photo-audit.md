# Hotel photo evidence audit

Use this protocol when visible condition, room design, promised atmosphere, or an amenity can change the decision.

## Evidence ladder

Attempt sources in this order, recording failures rather than silently shrinking the evidence set:

1. Hotelist photo and AI-photo fields for discovery only.
2. Official hotel gallery for the exact room category being considered.
3. Google Places API (New) when a configured key and billing are available.
4. Public Google Maps guest-photo gallery when browser access and consent state permit it.
5. Booking-platform guest photos, Tripadvisor traveler photos, independent room tours, and dated trip reports.

Do not interpret a consent wall, WAF, login wall, missing API key, empty gallery, or expired photo resource as evidence that no visual problem exists.

## Google Places photos

Use Places API (New), not the legacy endpoint, for new integrations:

1. Resolve the exact property to a stable place ID; verify name, address, and coordinates.
2. Request `photos` in the Place Details field mask. A place can return up to ten photo resources.
3. Retrieve selected images through `places/<PLACE_ID>/photos/<PHOTO_RESOURCE>/media` with `maxHeightPx` or `maxWidthPx` (1–4800).
4. Preserve `authorAttributions` and a direct Google Maps source path when reporting evidence.
5. Follow Google Maps Platform attribution and storage rules. Do not cache photo resource names or persist Places content beyond allowed exceptions; photo names can expire. A place ID may be stored.
6. Load photos on demand and stop after the evidence set is sufficient; do not bulk mirror the gallery.

Google Places photos can mix owner, visitor, exterior, food, and unrelated room categories. Attribution does not guarantee that an image is recent, guest-authored, or relevant to the exact room. Classify provenance and applicability explicitly.

## Minimum useful evidence set

For each finalist, attempt:

- two official photos of the exact room category;
- three recent materially independent guest photos, preferably room and bathroom;
- one image of any decisive shared amenity or access claim;
- additional exterior/map context only when noise, view, parking, or approach matters.

If the minimum cannot be met, continue with a smaller set but label visual confidence low and name what is missing. Never pad the set with duplicate crops or syndicated copies.

## Inspection schema

For every image record:

```text
source URL · source type · author attribution · image/stay date if known
property identity · room category/floor/wing if known · official or guest
visible claim · contradiction · applicability · confidence
```

Inspect only what pixels can support:

- wear, stains, grout, mold-like discoloration, water damage, broken fixtures;
- room geometry, circulation, luggage clearance, workspace, sockets, storage;
- window size, visible light, privacy treatment, and view;
- coherent versus generic, dated, kitschy, or mismatched design language;
- wide-angle distortion, staged lighting, repeated hero-room imagery;
- renovated-room versus old-wing mismatch;
- whether a pool, gym, kitchen, balcony, bath, parking entrance, or workspace appears usable;
- nearby roads, bars, lifts, plant rooms, construction, or event spaces when visible.

Pixels cannot establish quiet, smell, mattress quality, water pressure, working or guest-controlled AC, blackout performance, Wi-Fi, cleanliness over time, or service. Seek traveler evidence for those claims.

## Promise audit

Extract experience promises from the property name and official copy: `boutique`, `design`, `luxury`, `historic`, `spa`, `resort`, `romantic`, `minimalist`, or similar. For promises material to the brief, classify:

- **substantiated** — multiple applicable images consistently support it;
- **partial** — some images support it, but category/wing inconsistency remains;
- **marketing-only** — the label is asserted but the visual set does not provide persuasive support;
- **contradicted** — applicable current imagery directly conflicts with it;
- **unknown** — coverage is insufficient.

Keep operational quality separate from promise fidelity. A clean, friendly guesthouse may be a good stay while failing a design-led boutique brief.

## Output

```text
Visual verdict: <supported | conditional | contradicted | unknown>
Coverage: <official N · guest N · exact-room N · newest known date>
Visible strengths: <specific observations>
Visible concerns: <specific observations>
Promise audit: <promise → status and reason>
Cannot establish from photos: <important nonvisual claims>
```
