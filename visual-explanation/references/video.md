# Explainer video production

## Earn the motion

Use video when seeing stages, movement, or a derivation reduces confusion. Before rendering, state what motion teaches that a static diagram would not. If there is no clear answer, use static panels unless the user explicitly requests video.

## Teaching sequence

1. Name the question and show a concrete starting state.
2. Introduce only the entities needed for the example.
3. Animate one meaningful change at a time.
4. Pause on important results long enough to read them.
5. State where the model or analogy stops applying.
6. Summarize the result and a useful next step.

Use a scene table: scene, teaching point, visual state/change, narration, on-screen labels, evidence, duration. Keep the same visual positions and vocabulary across scenes. Do not let transitions, camera motion, or decorative effects compete with the mechanism.

## Use real capabilities

Inspect installed renderers and load their production skill if available. Deterministic SVG/canvas, a local frame renderer, or Manim can be suitable; none is required. Generated footage is useful for illustration but unreliable for exact math, text, or diagrams. Obtain approval for paid calls. Never invent API keys or credentials.

Use configured narration when available. If it fails, check suitable installed local or free alternatives and disclose the fallback. Do not clone a person's voice without authorization. Render actual narration before finalizing scene durations. Measure audio with a media tool; do not guess timing from word count.

## Sound, captions, and packaging

- Keep speech clear. Music is optional and must not mask narration.
- Use captions timed to the actual audio. Include meaningful non-speech sounds when needed.
- Supply a text transcript even when captions are burned in.
- Keep labels in safe visible areas and readable at the delivery size. Avoid rapid flashes.
- Narrate the important visual changes so the audio carries the explanation where possible.
- Prefer a broadly playable delivery format such as MP4 with H.264 video, AAC audio, and fast-start metadata, unless the target needs something else.
- Preserve editable source and caption/transcript files beside the final media. A wrapper HTML page may use relative video paths; call it a bundle, not a self-contained file.

## Verify the rendered file

Probe actual codec, dimensions, duration, and audio streams. Decode the whole file; for a supported FFmpeg installation, a typical check is:

```sh
ffprobe -v error -show_format -show_streams -of json /absolute/path/explainer.mp4
ffmpeg -v error -i /absolute/path/explainer.mp4 -f null -
```

These are integrity checks, not listening or visual checks. Inspect representative frames from every scene and across transitions. Play/check narration and caption synchronization; for a short explainer, review the full clip. Check missing audio, sudden volume changes, cropped labels, visual/narration disagreement, and the final summary. Fix and rerender before delivery. If playback cannot be checked, label that gap; do not call the video fully verified.
