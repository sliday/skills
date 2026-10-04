#!/usr/bin/env python3
"""caption.py <id> -- literal description of keyframes/<id>_start.jpg via OpenRouter (Gemini 2.5 Flash) -> keyframes/<id>_start.caption.txt"""
import sys, os, json, base64, urllib.request
sid = sys.argv[1]; img = f"keyframes/{sid}_start.jpg"
b64 = base64.b64encode(open(img, "rb").read()).decode()
q = ("Describe this painting LITERALLY for an animator who must animate it without seeing it, in 120-180 words. "
     "List left-to-right: every character (species, size in frame, pose, what each holds, where each faces, eye colour), every vehicle and object with its exact position, "
     "the setting, the light sources, the weather, what is in the sky, and anything frozen mid-motion (splashes, flying debris, smoke). "
     "No interpretation, no story, no style talk; only what is visibly there and where.")
body = {"model": "google/gemini-2.5-flash", "messages": [{"role": "user", "content": [{"type": "text", "text": q}, {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}], "max_tokens": 600}
r = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
    headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
for i in range(3):
    try:
        out = json.load(urllib.request.urlopen(r, timeout=120))["choices"][0]["message"]["content"].strip(); break
    except Exception as e: out = None; err = e
if not out: raise SystemExit(f"caption failed: {err}")
open(f"keyframes/{sid}_start.caption.txt", "w").write(out); print('"succeeded"', sid, len(out))
