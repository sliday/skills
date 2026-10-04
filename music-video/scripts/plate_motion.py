#!/usr/bin/env python3
"""plate_motion.py -> docs/plate_motion.json : per-frame motion energy of frames/<id>/ (24 fps), for active-window trimming in the renderer."""
import json, os, numpy as np
from PIL import Image
out = {}
for sid in sorted(os.listdir("frames")):
    fs = sorted(f for f in os.listdir(f"frames/{sid}") if f.endswith(".jpg"))
    if not fs: continue
    prev, e = None, [0.0]
    for f in fs:
        a = np.asarray(Image.open(f"frames/{sid}/{f}").convert("L").resize((160, 90)), dtype=float)
        if prev is not None: e.append(float(np.abs(a - prev).mean()))
        prev = a
    out[sid] = [round(x, 3) for x in e]
json.dump(out, open("docs/plate_motion.json", "w")); print(len(out), "plates profiled")
# ---- plan: trim only the static head and frozen tail; keep the whole active span; fit it to the slot ----
S = json.load(open("docs/shots.json")); plan = {}
for s in S:
    e = out.get(s["id"]); slot = s["t1"] - s["t0"]
    if not e: continue
    e = np.array(e); n = len(e)
    sm = np.convolve(e, np.ones(6) / 6, mode="same")
    thr = max(0.25, 0.35 * np.percentile(sm, 80))
    act = np.where(sm > thr)[0]
    a0, a1 = (int(act[0]), int(act[-1])) if len(act) else (0, n - 1)
    A = (a1 - a0 + 1) / 24
    k = min(1.35, max(0.85, A / slot))
    W = min(n, int(round(slot * k * 24)))
    if W >= n: k, o = n / (slot * 24) if n / (slot * 24) < 0.85 else k, 0
    else: o = int(min(max(0, a0 - (W - (a1 - a0 + 1)) / 2), n - W))
    plan[s["id"]] = {"k": round(k, 3), "offset": round(o / 24, 3), "active": [round(a0 / 24, 2), round(a1 / 24, 2)], "plate": round(n / 24, 2), "slot": round(slot, 2)}
json.dump(plan, open("docs/plate_plan.json", "w"), indent=1)
for k, v in plan.items():
    if v["offset"] > 0.2 or abs(v["k"] - 1) > 0.05: print(k, v)
