#!/usr/bin/env python3
"""plate.py c09 [...] -- fal minimax/h3-max/reference-to-video: start (+mid) (+end) frames, sheets as reference images, optional motion-reference video."""
import json, sys, subprocess, pathlib, os
S = {s["id"]: s for s in json.load(open("docs/shots.json"))}
for sid in sys.argv[1:]:
    s = S[sid]; mid = os.path.exists(f"keyframes/{sid}_mid.jpg") and s["mid_frac"]
    inp = {"prompt": s["motion"], "image_url": f"keyframes/{sid}_start.jpg", "reference_image_urls": s["refs"][:11],
           "duration": round(s["dur"], 2), "resolution": "768P" if mid else "1080P", "prompt_expansion_mode": "disabled", "aspect_ratio": "16:9"}
    if os.path.exists(f"keyframes/{sid}_end.jpg"): inp["end_image_url"] = f"keyframes/{sid}_end.jpg"
    if mid: inp["middle_image_url"] = f"keyframes/{sid}_mid.jpg"; inp["middle_frame_time"] = round(s["dur"] * s["mid_frac"], 2)
    # NOTE: h3-max rejects (downstream_service_unavailable) first-frame image_url + reference_video_urls together; keyframes win.
    pathlib.Path(f"clips/{sid}.in.json").write_text(json.dumps(inp, ensure_ascii=False))
    print(subprocess.run([".venv/bin/python", "tools/fal.py", "minimax/h3-max/reference-to-video", f"clips/{sid}.in.json", f"clips/{sid}"], capture_output=True, text=True).stdout)
