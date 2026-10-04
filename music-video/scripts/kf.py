#!/usr/bin/env python3
"""kf.py <start|mid|end> <shot_id> -- keyframe via gpt-image-2.5-sunburst. mid/end are edits of keyframes/<id>_start.png."""
import json, sys, subprocess, pathlib
kind, sid = sys.argv[1], sys.argv[2]
s = next(x for x in json.load(open("docs/shots.json")) if x["id"] == sid)
prompt = s[f"kf_{kind}"]
if not prompt: print('{"status": "succeeded", "skipped": true}'); sys.exit()
imgs = ([f"keyframes/{sid}_start.png"] if kind != "start" else []) + s["refs"]
inp = {"prompt": prompt, "input_images": imgs, "aspect_ratio": "2048x1152", "quality": "high", "output_format": "png", "moderation": "low"}
pathlib.Path(f"keyframes/in_{sid}_{kind}.json").write_text(json.dumps(inp, ensure_ascii=False))
print(subprocess.run(["python3", "tools/rep.py", "openai/gpt-image-2.5-sunburst", f"keyframes/in_{sid}_{kind}.json", f"keyframes/{sid}_{kind}"], capture_output=True, text=True).stdout)
