# AI Music-Video Playbook

Distilled from two finished films: **GENIUS / SICK / BOTH** (`gsb/`, 1080p charcoal rotoscope) and **LATEST / OUTDATED / BOTH** (`lob/`, 720p cyberpunk with the storyboard-to-video skill).

The reusable tools live in `lob/tools/`: `rep.py`, `contact.py`, `at.py`, `plate.py`, `extract.sh`, `storyboard.py`, `gate.py` and `deliver.py`. Copy them into each new project.

---

## 0. Ground rules
- **Freeze the song first.** Copy it to `source/SONG_CANONICAL.mp3`, run `chmod 444`, record its sha256, and never edit it. The master takes the song through its only lossy step, AAC. The mezzanine carries PCM, and its decode must be bit-identical to the source (hash both).
- **One source of truth.** A single storyboard script generates the manifest (`project.json`) and the renderer data (`docs/shots.json`). Nobody hand-edits the derived files.
- **Log every paid call.** `rep.py` appends the prediction ID, input and output files to `jobs/jobs.jsonl`.
- **Do heavy work in the background.** Batch the plates in the background and build the renderer while they run.

## 1. Song
**Works**
- Generate 2–4 takes and score them. Never pick the first take.
- **Lyria 3 Pro** handles full songs up to about 3 minutes and follows section tags ([Verse], [Bridge], [Breakdown]).
- For "X meets Y" styles, describe the sound itself (instruments, textures, vocal attitude). *Lyria refuses prompts that name artists*: it errored with E005 on "Charli XCX / NIN / 100 gecs".
- Put the hook in the first two seconds: a cappella or whispered, then the drop.
- Rhyme check: list every couplet's end-pair before generating.

**Did not help**
- Trusting whisperX on the full mix. It misses 50–80% of sung lines over dense production.

## 2. Timing map (the renderer's clock)
1. Split the vocal stem with **Demucs** (`ryan5453/demucs`, `stem=vocals`).
2. Run **whisperX** on the stem with `align_output`, `vad_onset 0.25`, `vad_offset 0.2` to get word onsets. Save them to `words.json`.
3. For intros, stylised vocals and spot checks, cut a slice and run **openai/whisper** with no VAD gate. That pass caught the hook that whisperX missed.
4. Correct ASR slips against the written lyric, and record deviations *as sung*: dropped lines, changed words.
5. Get beats and envelope from librosa.

**Pitfall:** Whisper hallucinates text over instrumental intros ("born in the mid-1990s"). Cross-check it against the energy map.

## 3. Continuity bibles
- **One character sheet per recurring character**, from gpt-image-2 at high quality in 3:2, as a turnaround sheet with close-ups and hands. Generate the master state first, then condition the other states (ages, personas) on it.
- **Check the sheets by eye**: consistent identity, no text, correct wardrobe.
- **Keep ages at 19 and above** for main-character sheets. A 17-year-old full-body sheet was refused. Keep child states brief, clothed and in memory framing.
- **Treat the sheet as canonical.** When it differs from the written bible (the hair length did once), update the bible to match the sheet.

## 4. Storyboard, keyframes and plates
- **Shot list timed to the lyric lines.** In every shot record, write:
  - the start composition
  - one camera move
  - ordered actions
  - the end state
  - a closed cast list
  - references to the canonical sheet or sheets
- **Keyframes:** gpt-image-2, with the character sheets as `input_images`. Identity holds very well. Medium quality is enough for 720p.
- **Plates:** Kling v3 image-to-video. It holds identity and handles hands well.
  - Use pro mode for 1080p, standard mode for 720p at about half the cost.
  - Keep plate length at `ceil(shot)` seconds, capped at 15.
  - Run 5 in parallel.
- **Canary before batch.** Take the riskiest shot, generate its plate, and look at 2 fps sample frames before paying for the batch.
- **Fix plate artefacts with a retime before regenerating.** Plates often fail in their last second: an eye-roll, a colour drift. Play the plate at 0.68–0.9× so the shot ends before the failure.
- **Look (optional): phot.dev on keyframes.**
  - CineStill 800T and Portra 400 at strength 0.9 are subtle and good.
  - Expired Polaroid is far too strong. Blend it at 30% locally.
  - The public quota is 25 renders a day per address. `/v1/lut` is free.

## 5. Renderer (Node + @napi-rs/canvas, worker threads)
- **Every frame is a pure function of `t`.** Use a hash PRNG, never `Math.random`. Boil and grain run on twos (12 fps steps). Render resumably through `.tmp` files and rename.
- **Speed:** a heavy charcoal stylisation at 1080p rendered the whole 3-minute film in about 3.5 minutes. A light grade renders in seconds.
- **Tune the stylisation on real frames first.** The first charcoal pass turned dark stages into grey mush.
- **Typography**, when it's allowed:
  - Put paper labels or halos behind text on busy ground.
  - Use at least 21 px at 720p for UI text.
  - Check glyph coverage with fontTools. ♥ ▸ ◡ rendered as empty boxes. Draw symbols as vector paths.
- **Tie text to word onsets**, and keep faces clear of it.
- **The shot index is `ceil(t0·fps)`, not `round`.** Rounding misplaced cuts by a frame.
- **Post can supply actions the model won't perform.** Time-delayed composites (a reflection that lags), local glitches, retimes.

## 6. Review loop
- **Contact sheets everywhere:** `contact.py` for plates (start, mid, end) and `at.py` for rendered frames at chosen times. Review the whole film at 3 s intervals at 320 px, about phone size. That's where readability failures showed up.
- **vid2md** (`~/Playground/vid2md`, `uv run video-watch … --provider openrouter --model google/gemini-2.5-flash --transcript-file lyrics.srt --detail-mode detailed`) costs about $0.11 per film.
  - It's a good independent check of cut count and content.
  - Its report is mostly frame-to-frame deltas.
  - It samples frame 0, so a fade-in reads as "blank".
- **Cut verification:** measure frame difference at every planned boundary against the motion inside the shot. Scene detection undercounts look-alike neighbours and counts glitches as cuts.

## 7. Delivery
- **Encode:** H.264 High, `yuv420p` with `scale=in_range=pc:out_range=tv`, BT.709 tags, faststart. JPEG frames produce `yuvj420p` unless you convert.
- **Loudness:** measure the source and set the delivery profile to it. Don't guess a target and don't normalise.
- **Two copies:** a master (CRF 16–19) and a web copy (CRF 21–24). Per-pixel grain inflates bitrate about 3×.
- **storyboard-to-video gates** (`validate_project.py`): draft → render_ready → batch_ready → delivery, with approvals bound to the validator's own scope hashes. They caught real mistakes, such as a guessed loudness target and an unverifiable cut count.
  - Evidence frames must be **PNG**. The validator seeks with `-ss`, and ffmpeg can't seek inside a single JPEG.
  - Changing `assembly` invalidates the prompts, still and canary approvals. Prove the shot prompts are byte-identical, then re-bind.
  - Approvals signed by a model are not a human sign-off. Say so.

## 8. Shell and API gotchas
- zsh doesn't word-split `$VAR` flags. Inline them or use `${=VAR}`.
- `ls` output can carry a trailing `/` on directories. Strip it before using the names as IDs.
- `xargs -I` chokes on long inline scripts. Use a `while read` loop with `& … wait`.
- Replicate: community models need the version endpoint (404 on `/models/{m}/predictions`). Fall back automatically. Retry on 504. Send a real User-Agent, or Cloudflare answers 403/1010.
- Moderation refusals (E005) cost nothing but time. Rewrite the prompt; don't retry it unchanged.

## 9. Cost and time reference
| Film | Length | Paid calls | Rough spend | Wall-clock |
|---|---|---|---|---|
| GENIUS / SICK / BOTH | 3:01, 1080p | 67 | about $50–70 (mostly Kling pro) | about 1 h |
| LATEST / OUTDATED / BOTH | 2:21, 720p | 93 | about $35–50 (Kling standard, 3 song rounds) | about 2.5 h with gates |

## 10. What didn't pay off
- Heavy full-frame stylisation as the main look. It takes tuning per scene, and dark scenes suffer.
- Running whisperX on the full mix.
- A fixed loudness target.
- Counting shots from scene detection alone.
- Film emulation at full strength on memory or fantasy shots.

## 11. Checklist for the next film
1. Freeze and hash the song, measure its loudness, and get beats.
2. Build the stem, word map and lyric sheet (as sung).
3. Write the bible, then the character sheets (master state first), then a visual check.
4. Write the storyboard script (source of truth), then validate the draft.
5. Generate keyframes, check the contact sheet, then approve the still.
6. Run the canary plate, check it, then approve.
7. Run the plate batch in the background while building the renderer.
8. Plate QA sheets: retime or regenerate the failures.
9. Full render, then the 3 s phone-size sheet, then fixes.
10. vid2md, the cut verification and the audit.
11. Encode the master and web copies, verify the audio hash, and write the QA report.
12. Commit.
