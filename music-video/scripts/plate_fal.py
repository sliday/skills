#!/usr/bin/env python3
"""plate_fal.py c18 [...] -- fal minimax/h3-max/reference-to-video: START FRAME (image_url) + STYLE/CONTEXT REFERENCE IMAGES + full style text.
No end frame, no mid frame. References are named in the prompt as Image 1..N."""
import json, sys, subprocess, pathlib, os
M = json.load(open("docs/motion.json")); STYLE = open("bibles/STYLE.txt").read().strip()
S = {s["id"]: s for s in json.load(open("docs/shots.json"))}
BASE = [("source/refs/style/s2_giant_bears.jpg", "the master STYLE painting: naive oil on woven canvas, giant bears over a tiny naive village"),
        ("source/refs/style/s1_bears_bed.png", "a second STYLE painting of the same bears, smooth glazed oil"),
        ("bibles/char/library.jpeg", "the CHARACTER LIBRARY: the exact look of every character, prop, house and church")]
EXTRA_REFS = {"c18": [("keyframes/c19_start.jpg", "how the tiny village, its crooked houses and onion churches must be painted")],
              "c35": [("keyframes/c19_start.jpg", "how the tiny village must be painted")]}
for sid in [a for a in sys.argv[1:] if not a.startswith("--")]:
    refs = BASE + EXTRA_REFS.get(sid, [])
    names = " ".join(f"Image {i+1} is {d}." for i, (_, d) in enumerate(refs))
    prompt = (M[sid]["prompt"] + f" REFERENCE IMAGES (style and design only, never copy their compositions): {names} "
              f"Everything that appears or changes during the clip, including anything newly revealed, must be painted in exactly this style: {STYLE} "
              "It must look like a hand-painted naive oil painting on canvas in every frame: never a 3D render, never CGI, never glossy, never photographic.")
    inp = {"prompt": prompt, "image_url": f"keyframes/{sid}_start.jpg", "reference_image_urls": [r for r, _ in refs],
           "duration": M[sid]["duration"], "resolution": "1080P", "prompt_expansion_mode": "disabled", "aspect_ratio": "16:9"}
    pathlib.Path(f"clips/{sid}.fal.in.json").write_text(json.dumps(inp, ensure_ascii=False))
    print(subprocess.run([".venv/bin/python", "tools/fal.py", "minimax/h3-max/reference-to-video", f"clips/{sid}.fal.in.json", f"clips/{sid}"], capture_output=True, text=True).stdout)
