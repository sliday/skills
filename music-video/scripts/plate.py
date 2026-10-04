#!/usr/bin/env python3
"""plate.py c09 [...] -- Replicate minimax/h3, START FRAME ONLY (the BERLOGA v1 flow) + caption-grounded motion prompt (docs/motion.json)."""
import json, sys, subprocess, pathlib
M = json.load(open("docs/motion.json"))
for sid in [a for a in sys.argv[1:] if not a.startswith("--")]:
    inp = {"prompt": M[sid]["prompt"], "first_frame_image": f"keyframes/{sid}_start.jpg", "duration": M[sid]["duration"], "ratio": "16:9", "resolution": "2K"}
    pathlib.Path(f"clips/{sid}.in.json").write_text(json.dumps(inp, ensure_ascii=False))
    print(subprocess.run(["python3", "tools/rep.py", "minimax/h3", f"clips/{sid}.in.json", f"clips/{sid}"], capture_output=True, text=True).stdout)
