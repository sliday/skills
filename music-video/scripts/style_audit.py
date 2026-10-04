#!/usr/bin/env python3
"""style_audit.py [ids] -- vision check (Gemini 2.5 Flash via OpenRouter): mid + last frame of each plate vs the start keyframe.
Scores 1-5 how much the frame still looks like a hand-painted naive oil painting (5) vs 3D/CGI/photo (1)."""
import sys, os, json, base64, subprocess, urllib.request, glob
ids = sys.argv[1:] or sorted(os.path.basename(f)[:-4] for f in glob.glob("clips/c*.mp4"))
def b64(path): return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()
res = {}
for sid in ids:
    fs = sorted(f for f in os.listdir(f"frames/{sid}") if f.endswith(".jpg")); mid, last = fs[len(fs) // 2], fs[-1]
    q = ("Image 1 is the approved start frame: a naive hand-painted oil painting on canvas. Images 2 and 3 are later frames of the same animated shot. "
         "For EACH of images 2 and 3, rate 1-5 how well it keeps the SAME hand-painted naive oil-painting look (5 = identical painterly style, 1 = looks like a 3D/CGI render, glossy plastic, or photographic). "
         'Answer ONLY JSON: {"mid": n, "last": n, "issue": "<=12 words or empty"}')
    body = {"model": "google/gemini-2.5-flash", "messages": [{"role": "user", "content": [{"type": "text", "text": q},
            {"type": "image_url", "image_url": {"url": b64(f"keyframes/{sid}_start.jpg")}}, {"type": "image_url", "image_url": {"url": b64(f"frames/{sid}/{mid}")}},
            {"type": "image_url", "image_url": {"url": b64(f"frames/{sid}/{last}")}}]}], "max_tokens": 120, "response_format": {"type": "json_object"}}
    r = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
    try:
        t = json.load(urllib.request.urlopen(r, timeout=120))["choices"][0]["message"]["content"]
        j = json.loads(t[t.index("{"):t.rindex("}") + 1]); res[sid] = j
    except Exception as e: res[sid] = {"error": str(e)[:80]}
    print(sid, res[sid], flush=True)
json.dump(res, open("qa/style_audit.json", "w"), indent=1)
