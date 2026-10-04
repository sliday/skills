# Proposed improvements to story-board-reader and replicate-video

These come from the BERLOGA 1–3 productions. They are not applied yet.

## story-board-reader / storyboard-to-video
1. **Physical handoffs.** `state_in`/`state_out` should carry physical facts, not only scene IDs. Add keys such as `positions`, `held_props`, `prop_states` and `eye_state`, and have the validator check that consecutive shots agree. That would have caught bears back in bed after leaving it, and the moth back in its icon after flying away.
2. **Story-time prop states.** A prop can change state at a story time: the icon is full before c27 and empty after it. Prompt compilation should inject the current state into every shot whose `t0` falls in that range.
3. **Board rendering.** A `render_board.py` should draw a notes strip ABOVE each panel (id, timecode, lyric or VO, CAM, ACT, FX, IN), never over the image. Small corner labels only on contact sheets.
4. **Anchor frames per location**, with the rule "same place, new framing", so a reused location doesn't copy the previous shot's composition.
5. **Action-start composition.** The start frame shows the beginning of the action with room for it (the trike on the left, intact houses ahead), never the mid-point.
6. **A per-shot QA gate before assembly** that checks at least start, mid and end against the action criteria. API success alone shouldn't count.

## replicate-video
1. **Image-to-video default: first frame only.** Put a warning in `h3-quirks.md`:
   - Pinning `last_frame_image` when it's an edit of the start produces morphing.
   - Replicate h3 rejects first or last frames combined with any `reference_*` media (E006).
   - fal h3-max accepts `image_url` with `reference_image_urls`, but not with `reference_video_urls`.
2. **Literal caption grounding.** The motion prompt should start with a vision-model description of what is actually in the first frame (characters, positions, held props, eye colour, frozen debris), then camera, one or two actions, the end state, continuity and style.
3. **Vehicle and tracking parallax wording** must be explicit, or h3 renders a static vehicle against a static backdrop.
4. **A "no decorations appear" invariant** for plain-surfaced props. h3 painted flowers onto a plain sidecar.
5. **GPT Image 2.5 roles.** Sunburst for keyframes and sheets; flare for surgical repairs with an explicit keep-list (flare drops unlisted objects).
