---
name: music-video
description: "Use when producing a finished AI music video from a song (supplied, or generated with Lyria): continuity bibles, storyboard, keyframes, image-to-video plates, a deterministic finishing renderer, QA and delivery gates. Encodes the corrections from four productions (GENIUS/SICK/BOTH, LATEST/OUTDATED/BOTH, BERLOGA v1 and v2): character and prop sheets, location anchors, explicit rule blocks, start/mid/end keyframes, rolling job pools with watchdogs, and the storyboard-to-video validator."
version: 2.0.0
author: Sliday
license: MIT
triggers:
  - "make a music video"
  - "animated music video"
  - "music video from this song"
  - "storyboard to video for a song"
  - "/music-video"
tools:
  - terminal
  - read_file
  - write_file
  - vision_analyze
mutating: true
---

# Music Video

This skill is an end-to-end pipeline. The song is the clock, the bibles carry identity, the storyboard script is the single source of truth, and generative models produce only frames and plates. Everything else is deterministic code.

`scripts/` holds working tools. Copy them into the project's `tools/` folder.

| Script | Role |
|---|---|
| `rep.py` | Replicate runner: version fallback, 504 retry, User-Agent, watchdog `REP_TIMEOUT`, logs `jobs/jobs.jsonl` |
| `fal.py` | fal.ai runner: uploads local files once (sha-cached), watchdog `FAL_TIMEOUT`, same job log |
| `pool.py` | rolling pool: `pool.py N cmd... < ids` gives N in flight, 3 tries each. Never use fixed batches. |
| `storyboard.py` | template source of truth: shots, rule blocks, location anchors, start/mid/end edit prompts, `project.json` and `docs/shots.json` |
| `kf.py` | keyframe generator: `kf.py start\|mid\|end <id>`; mid and end are edits of the start frame |
| `plate.py` | image-to-video (Kling or MiniMax h3) |
| `extract.sh` | plates to 24 fps frames |
| `render_finish.js` | no-text finishing renderer: canvas weave, grain, drift, embers, lightning |
| `vertical.js` | 9:16 recompose with per-shot focal points or pans |
| `gate.py`, `deliver.py` | storyboard-to-video approvals, evidence and final audit (validator at `~/Playground/story-board-reader/storyboard-to-video/scripts/validate_project.py`) |
| `contact.py`, `at.py` | contact sheets for every review |

## 0. Ground rules
- **Song first.** Freeze it with `chmod 444` and record its sha256; never alter it. Measure loudness and beats, then make a Demucs vocal stem and whisperX word onsets from the stem, using plain Whisper slices for intros. The timing map drives every cut.
- **One project folder per attempt** (`<name>2/` for a redo). Re-use accepted assets from the previous attempt explicitly as references.
- **Run long jobs in the background** and keep talking to the user. Poll status in short checks. A job that has made no progress for 2× its typical time is hung: cancel it and retry it, because one stuck job can starve a fixed batch.

## 1. Bibles (lock BEFORE any shot)
Generate one sheet per entity class with the best image model (gpt-image-2.5-sunburst at `xhigh`), with references attached:
1. **Family / cast sheet:** all recurring characters in a row at their **canonical relative heights**, plus head close-ups.
2. **Model sheets for recurring vehicles and objects:** one exact design from several angles, with countable parts named in a rule ("exactly three exhausts"). Mask out off-model characters on the sheet so they don't leak. **Per-object model sheets for anything that recurs in different formats.** One object appears in every panel: the moth as icon, glowing, peeling off, small, super-sized, shy; the samovar as an object, a vehicle fuel tank and a flamethrower; the mortar and its shells. **The user will catch every drift.** Give each recurring object its own sheet.
3. **Vehicle and props sheet.**
4. **World sheet:** secondary characters taken from user reference paintings, plus trees, houses, churches.
- **Crop signatures and lettering** out of every reference before use.
- **Fix sheets by editing them** ("keep everything, change only X") rather than regenerating.
- **Review the sheets** in one contact sheet and confirm them with the user when they are live.

## 2. Rule blocks (append verbatim to EVERY keyframe prompt)
Every user correction becomes a named rule in `rules()`, never a one-off prompt tweak:
- **SCALE CANON** (relative heights; act-based world scale). Only include it when those characters are in the shot: mentioning bears made bears appear in empty landscapes.
- **ABSOLUTELY NO <cast>** clause for empty shots. Drop cast sheets from their references and use cast-free style exemplars.
- **FIRE** = one stylised language (Khokhloma), repeated in the motion prompt so the fire never turns realistic mid-clip.
- **HOUSE** (distorted naive perspective), **CHURCH** (one church type), **TREE**, **SEASON** (one season until the scripted change), **HAT/COSTUME**, **BOTTLE/PROP SIZE**, **ICON/RELIGIOUS** (only the story's icon), **SEATING** (who drives and who sits where on a vehicle; children never drive), **DETAIL** (match the approved exemplars' simplification), **UNIQUENESS** (each character and key prop exactly once per frame; never riding and carrying a vehicle at once), **ANATOMY** (head on neck, limb counts, readable silhouettes; no lying rug-bodies), **VEHICLE/OBJECT** (countable parts), **NO TEXT**.
- **When a rule changes, regenerate the anchors first, then their dependents.** Stop any running batch before changing a rule so you don't pay twice.

## 3. Location continuity (anchors)
- Group shots by location. The first approved frame of each location is its **anchor**.
- Every other shot in that location gets the anchor as **Image 1**, plus a LOCATION CONTINUITY note naming the fixed objects and where they sit (e.g. "the icon hangs on the plank wall above the bed, between the rug and the elephant shelf").
- Regenerate an anchor FIRST, then everything that depends on it.

## 4. Keyframes: start, mid, end
- Generate the start frame from the full prompt plus its references.
- Generate mid and end frames as **edits of the start frame** ("keep composition, framing, every object; change only: …"). Never generate them independently. In BERLOGA v1 an independent end frame swapped which church flew and broke the clip.
- Check each mid and end frame against its start frame on a contact sheet before animating.
- Plan the frames with a cast/location table so the user can review structure first.

## 5. Plates (video)
- **Choose the model by A/B canary on the riskiest shot.** For painterly and naive styles, MiniMax h3 beat Kling v3, which looked "AI" and drifted designs (exhausts turned into rockets).
- **h3 follows long, specific motion prompts**, so write them richly:
  - name each reference image ("Image 1 is…")
  - give the camera move
  - list the actions in numbered order
  - state the end state, the style of motion and what must NEVER happen
- **fal `minimax/h3-max/reference-to-video`** (tested on BERLOGA 2):
  - first frame plus reference video FAILS (`downstream_service_unavailable`); each works alone, and keyframes win
  - reference-to-video needs at least one reference image
  - output runs about 0.5 s longer than requested; trim in the renderer
  - use `prompt_expansion_mode: disabled` with long prompts
  - inputs: `image_url` (first frame), optional `middle_image_url` plus `middle_frame_time`, `end_image_url`
  - references: `reference_image_urls` (sheets, at most 12 files total), `reference_video_urls` (accepted earlier plates as motion references, 2–15 s)
  - cost and resolution: $0.05/s, 768P native, mid frames need native 480P or 768P
- **Repair, don't regenerate:**
  - use `fix.py` (gpt-image-2.5-flare) for local defects such as a duplicated prop
  - flare won the A/B against sunburst, Qwen-Image-Edit-2511 and FLUX Kontext Max
  - always pass an explicit keep-list, because flare dropped an unlisted Maxim gun
- **Formats:** JPG keyframes (q94) for video work; PNG only for validator evidence frames.
- **Skip lip-sync** unless the user asks. OmniHuman synced, but it looked bad on painted characters.
- **Before regenerating, retime** (0.7–0.9×) to cut a failing last second.

## 6. Finishing (no-text films)
`render_finish.js`: a pure function of `t`, with canvas weave, grain, slow breathing drift, per-shot embers and ash, lightning on beats and a cold grade for winter. Effects only; no typography.

## 7. Review loop
- **Contact sheets for every pass:** keyframes, plates (start/mid/end), the full film every 3 s, and the vertical cut.
- **The user's notes come as single images:** answer each one with a named rule, regenerate exactly the affected shots, and show the before/after.
- **vid2md** (`~/Playground/vid2md`, `uv run video-watch … --provider openrouter --model google/gemini-2.5-flash --skip-audio`) gives an independent timeline at about $0.1. It's good for catching text and blank frames.


## 10. Image-to-video: what works and what doesn't (BERLOGA v1 → v2 → v3, measured)
| Approach | Result |
|---|---|
| **Start frame only + motion prompt** (v1 BERLOGA, Replicate h3) | **Best.** Real movement through time. The default. |
| Start + end frame both pinned (v2, fal h3-max) | **Morph.** When the end frame is an *edit* of the start it is nearly identical, so the model dissolves between two poses. Transient things like mid-air dirt stay frozen while the bears fall asleep. Never default to it. |
| Start + mid + end frames | Worse morphing, more cost. Dropped. |
| End frame as *reference only* | Ideal in principle, but **Replicate h3 rejects first/last frames combined with any reference media** (E006). fal h3-max accepts first frame + reference images, but rejects first frame + reference video. Use only when the end state truly differs. |
| Reference video as motion guide | fal h3-max: incompatible with a first frame. Skip. |
| Pinning the last frame | Only for real state changes the model can't infer (autumn to winter). Even then, describe it in text first. |

**Motion prompt recipe** (`motion.py`, about 2.5–4k chars, h3 follows long prompts):
1. **OPENING FRAME:** a *literal* description of what is painted. Gemini 2.5 Flash via OpenRouter captions every start frame (`caption.py`), left to right: characters, poses, held props, eye colour, objects, light, weather, anything frozen mid-motion. Without it the model guesses and drifts.
2. **CAMERA:** one move. For vehicles, **spell out the parallax**: "the background streams past in the opposite direction, ground rushes by, wheels spin, mud flies backwards". Otherwise h3 renders a parked vehicle in front of a static backdrop.
3. **WHAT HAPPENS over N seconds:** 1–2 actions as continuous real movement ("not a morph, not a dissolve").
4. **By the end:** the end state in words.
5. **Frozen debris continues** (falls, settles).
6. **CONTINUITY:** carried over from the rules: eye state, hats, fire language, "no decorations appear" (h3 painted flowers onto a plain sidecar), nobody enters or leaves.
7. **STYLE:** a painting coming to life; no text, no photorealism.

**Keyframe composition for action:** compose the start as the *beginning* of the action, with room for it to happen (trike on the left third with intact houses ahead), never the mid-point.

## 11. Storyboard board (`board.py`)
Build one panel per shot with a **notes strip ABOVE the frame**, never on top of it: id, timecode, lyric under the shot, CAM, ACT, FX (renderer effects, retime), IN (handoff). Review this before any plates. On contact sheets, keep labels tiny in a corner (Menlo 11).

## 12. Continuity handoffs (an improvement on storyboard-to-video's state_in/out)
Scene IDs are not enough. Keep a **HANDOFF** table of physical state per shot: where the characters are (in bed / on the floor by the door / on the trike), what they hold, prop state (icon with moth until c27, **empty** after), eye state (closed asleep, green when hypnotised). Inject "CONTINUITY FROM THE PREVIOUS SHOT: …" into the keyframe prompt and build the rules from story time (`t0 >= …`). Failures it prevented: bears back in bed one shot after leaving it; the moth back in the icon after it flew away.

## 13. Reference stack per keyframe
- **Character library poster** (one sheet, 24 cards, every recurring element) as reference #1, plus 1–2 style paintings, plus the specific model sheets the shot needs.
- **The user's master style bible**, condensed verbatim into STYLE: selective realism, scale dissonance, broken perspective, fewer elements.
- **Anchor frame for the location** ("same place, NEW framing", otherwise it copies the composition: c10 = c11).
- **Model sheets get fixed by whole redraws** when a panel is broken (the moth peel-off panel survived three edits). Fix props by sheet *edits* that keep the layout (mortar shell along the barrel axis).

## 14. Process lessons
- **Run a QA gate per shot before the edit.** BERLOGA 2 failed critique: a successful generation went straight into the cut even when the action didn't happen. Check start, mid and end against the action criteria.
- **One main action per clip**; trim static holds.
- **Keep oil, drop cut-out:** the cut-out/appliqué style produced AI deformation, not puppet motion. If you want real hinged cut-out motion, animate it deterministically in code instead.
- **Stale style words** in actions ("cut-out trees") leak into motion prompts. Grep the shot data when the style changes.
- **Moderation and prompt facts:** Lyria refuses artist names; gpt-image refuses minors in full-body turnarounds; h3 dislikes violent verbs.

## 8. Vertical 9:16 (per-shot hybrid, after the 16:9 cut is final)
1. **Triage:** find the subject box on the 16:9 start frame. If it fits a 9:16 window, use a crop or pan (`vertical.js`). Otherwise recompose.
2. **Recompose:** edit the approved start, mid and end frames to 9:16 with flare or sunburst ("same characters and poses, extend sky and ground, stack vertically"). Check them as triplets, then animate with h3-max using the same motion prompt. That repeats the performance without duplicating the frame.
3. **Re-lay effects and typography** for 9:16 in the renderer; never crop text.
4. **Expect** about 60% of shots to need regeneration, at about 0.6× of the main cut's plate cost.

## 9. Delivery
- **Encode:** H.264 `yuv420p` tv-range BT.709 faststart, a master and a web copy, the song unaltered, plus a **9:16 recompose** (`vertical.js`, per-shot focus or pan).
- **Gates:** draft → render_ready → batch_ready → delivery. Approvals are scope-hashed, and evidence frames are PNG. Re-bind the approvals after any prompt change and prove the shot prompts are unchanged when only the assembly changed.

## 9. Mistakes this skill already prevents
| Mistake (seen) | Rule |
|---|---|
| Moth / samovar / bottle / hats drifted shot to shot | per-object model sheets + rule blocks |
| Bears appeared in "empty" landscapes | scale canon only with cast; NO-cast clause; cast-free exemplars |
| Icon on the wall vs on the rug | location anchors as Image 1 |
| A child bear driving | SEATING rule |
| The vehicle changed shape between shots | a dedicated vehicle MODEL sheet (5 angles, off-model riders masked out) + TRIKE rule listing its countable parts (e.g. exactly three exhausts) |
| Lying bears read as flat rugs with floating heads | ANATOMY rule; restage sleeping or lying poses as slumped sitting |
| Samovar redesigned per scene | object model sheet in every format it appears in (object, fuel tank, weapon) |
| Snow before the ending | SEASON rule |
| Realistic fire mid-clip | fire language repeated in the motion prompt |
| A church spire instead of onion domes | CHURCH rule |
| The wrong object flew in an end frame | mid/end as edits of the start frame |
| One hung job blocked a batch for 25 minutes | rolling pool + watchdog |
| Lip-sync looked bad | off by default |
| Labels covering faces; ♥ rendered as boxes (text films) | face-exclusion zones; fontTools glyph check |
