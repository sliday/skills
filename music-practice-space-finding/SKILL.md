---
name: music-practice-space-finding
version: 1.0.0
description: Use when finding recurring rehearsal or music practice spaces.
author: Sliday
license: MIT
triggers:
  - "find a rehearsal room near me"
  - "find a rehearsal point"
  - "репетиционная точка"
  - "standing weekly guitar slot"
  - "shared music practice room"
  - "sala prób with a fixed slot"
mutating: false
---

# Music Practice Space Finding

## Contract

Find a practical place where the user will actually practise repeatedly, not merely a room that can technically be rented. Distinguish the operating model, verify equipment and recurring-slot terms, rank by habit friction, and leave the user with an actionable contact path.

## 1. Resolve the space model before ranking

Treat these as distinct products:

1. **Shared rehearsal point / permanent room** — several musicians or bands share a room, each has a fixed weekly window, and storage may be possible.
2. **Commercial hourly rehearsal room** — equipped room booked by the hour; a recurring reservation or subscription may still make it suitable.
3. **Recording studio** — optimized and priced for recording; do not recommend it merely because it contains instruments.
4. **Music-school room** — include only if independent room rental is allowed without buying lessons.

Important language pitfall: Russian **“репетиционная точка”** often means an equipped rehearsal base or shared room, not a recording studio. Do not silently collapse it into “studio.” Confirm whether the user needs a fixed shared room, an hourly equipped room, or is open to both. If the user is open to both, search both lanes in parallel and label them clearly.

## 2. Build the habit brief

Collect or infer only what changes the search:

- origin address or neighbourhood;
- instrument and whether acoustic or amplified;
- solo, duo, or band;
- desired session length and weekly frequency;
- preferred day/time window;
- fixed recurring slot versus ad-hoc booking;
- required backline;
- storage needs for instrument, amp, pedalboard, or other gear;
- acceptable walking/transit friction and budget.

When a calendar is available, inspect several future weeks before suggesting a recurring slot. Describe it as apparently conflict-free, not guaranteed personal availability.

## 3. Search using local operating-model terms

Search the local language, not just English “rehearsal studio.” Combine:

- ordinary room terms;
- recurring-slot terms;
- shared-room terms;
- storage terms;
- neighbourhood names;
- classifieds and musician groups.

For Poland, useful phrases include:

- `sala prób`, `salka prób`;
- `stały termin`, `stałe terminy`;
- `abonament dla muzyka indywidualnego`;
- `współdzielona sala prób`;
- `miejsce w sali prób`;
- `możliwość zostawienia sprzętu`;
- `przechowywanie sprzętu`;
- `szukam salki`, `wynajmę salkę`.

Shared rehearsal points are often absent from normal maps and websites. Search musician Facebook groups, local classifieds, social posts, and community boards alongside commercial sites.

## 4. Verify candidates from first-party sources

For each candidate verify:

- exact address and realistic door-to-door distance;
- whether solo practice is welcome;
- hourly price, package/discount, and minimum duration;
- guitar amp model, cabinet, PA, microphones, climate/ventilation;
- whether equipment is included or extra;
- fixed weekly term or subscription policy;
- storage policy;
- opening hours and cancellation terms;
- current phone, WhatsApp, email, booking form, or live calendar;
- signs the business is still active.

Never infer storage from “long-term rental,” and never infer a recurring slot from an online calendar. If not published, label it **unknown — ask directly**. Broken booking pages, old copyright dates, or stale social accounts reduce confidence but are not proof of closure.

## 5. Rank for repeated use, not theoretical value

Rank primarily by:

1. proximity and door-to-door friction;
2. ability to lock the same weekly slot;
3. adequate included equipment;
4. storage if needed;
5. atmosphere, access, and cancellation flexibility;
6. price.

Do not optimize away a nearby room to save a modest monthly amount if the extra commute threatens the habit. Show the trade-off explicitly: nearest/easiest, best true shared-room fit, and cheapest viable fallback.

## 5.1 After the room is chosen, minimize the rehearsal rig

When the immediate goal is restarting a restorative music habit—not preparing for a stage—stop designing a concert system. Derive the smallest repeatable bring-list from the room's verified backline and the user's existing gear.

1. Separate **home gear**, **always-bring gear**, and **optional experiment gear**.
2. Remove any personal amp, PA, mixer, or monitor whose role is already covered by the room.
3. For a solo guitarist using electronic drums, prefer one dedicated rhythm/sequencer unit and route it to a separate mixer channel; do not chain it through the guitar processor when the room has spare channels.
4. Verify the exact connector path: processor outputs to mixer/amp, drum-machine stereo breakout, room-supplied versus personally supplied XLR/instrument cables, mains access, and a table/stand.
5. Keep optional samplers, keyboards, secondary instruments, and complex synchronization at home until a specific musical need appears.
6. Make the first-session artifact a saved processor preset, one drum pattern, and a photo/note of working room levels—not a stage-ready set.

Pitfall: do not infer that a powerful equipped room means the user should build a more complex rig. Better backline should reduce what they carry and shorten setup time.

## 6. Use a two-lane acquisition strategy

When no fresh shared-room listing is publicly visible:

- **Lane A — start now:** book one trial at the nearest equipped commercial room and ask for an 8-week fixed slot.
- **Lane B — search for the better base:** post one concise ad in one or two local musician groups asking for a shared room, exact neighbourhood, weekly duration, and storage needs.

Time-box Lane B (normally 48–72 hours). If it produces no materially better option, lock Lane A. The goal is playing music, not indefinitely optimizing rooms.

## 7. Outreach should answer the unknowns

Prepare a local-language message containing:

- solo/band and instrument;
- desired weekly duration and broad time window;
- request for a fixed recurring term;
- trial-session request;
- amp/backline question;
- subscription price;
- storage question;
- easy callback channel.

Do not contact or book without user authorization when the exact time or commitment is consequential. A prefilled WhatsApp/SMS link is a useful low-friction handoff.

## Output Format

1. **Recommendation:** one clear best next move.
2. **Shortlist:** normally 2–4 candidates, each labelled shared point or commercial room.
3. **Habit economics:** weekly and average monthly cost, with package assumptions stated.
4. **Unknowns:** availability, storage, recurring-term terms.
5. **Two-lane plan:** trial now plus shared-room search if applicable.
6. **Copy-ready outreach:** local-language message and direct contact links.

## Anti-Patterns

- Calling every rehearsal room a recording studio.
- Treating “репетиционная точка” as an unambiguous hourly studio.
- Claiming a standing slot or storage without first-party evidence.
- Dumping many distant rooms without ranking commute friction.
- Recommending a music school that rents only with lessons.
- Spending weeks searching for a perfect shared room before beginning to practise.
- Presenting stale directory pages as current availability.

## Verification Checklist

- [ ] Space model is labelled correctly.
- [ ] Origin and realistic travel friction are considered.
- [ ] Solo/band eligibility and required gear are verified.
- [ ] Fixed slot, subscription, and storage are each verified or marked unknown.
- [ ] Prices are converted into weekly/monthly habit cost.
- [ ] At least one immediate-start route exists.
- [ ] Once a room is chosen, the bring-list removes redundant personal amplification and optional gear.
- [ ] Processor, rhythm source, mixer/amp, power, cable, and table/stand paths are explicit or marked unknown.
- [ ] Shared-room groups/classifieds were searched when relevant.
- [ ] User receives copy-ready outreach.
