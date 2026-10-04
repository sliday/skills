#!/usr/bin/env python3
"""plate.py [--h3] b09 ... -- Kling v3 pro (default) or MiniMax h3 image-to-video from keyframes/"""
import json, sys, subprocess, pathlib
h3 = "--h3" in sys.argv; ids = [a for a in sys.argv[1:] if not a.startswith("--")]
shots = {s["id"]: s for s in json.load(open("docs/shots.json"))}
for sid in ids:
    s = shots[sid]; out = f"clips/{sid}" + ("_h3" if h3 else "")
    if h3:
        inp = {"prompt": s["motion_prompt"], "first_frame_image": f"keyframes/{sid}.png", "duration": min(10, max(5, s["plate_dur"])), "ratio": "16:9", "resolution": "2K"}
        if sid == "b39": inp["last_frame_image"] = f"keyframes/{sid}_end.png"
        model = "minimax/h3"
    else:
        inp = {"prompt": s["motion_prompt"], "start_image": f"keyframes/{sid}.png", "duration": s["plate_dur"], "mode": "pro", "generate_audio": False, "negative_prompt": s["negative"]}
        model = "kwaivgi/kling-v3-video"
    pathlib.Path(out + ".in.json").write_text(json.dumps(inp))
    subprocess.run(["python3", "tools/rep.py", model, out + ".in.json", out])
