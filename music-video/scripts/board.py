#!/usr/bin/env python3
"""board.py -> boards/storyboard_<n>.jpg : one panel per shot, NOTES STRIP ABOVE the frame (never over it):
id · timecode · duration · lyric | CAM | ACTION | FX (renderer) | IN (continuity handoff)."""
import json, re, textwrap
from PIL import Image, ImageDraw, ImageFont
P = json.load(open("project.json")); S = {s["id"]: s for s in json.load(open("docs/shots.json"))}
W = json.load(open("sound/words.json")); W = W["words"] if isinstance(W, dict) else W
src = open("tools/storyboard.py").read(); HO = {}
m = re.search(r"HANDOFF = \{(.*?)\n\}", src, re.S)
for k, v in re.findall(r'"(c\d+)": "([^"]+)"', m.group(1)): HO[k] = v
fxsrc = open("render/render.js").read(); FX = dict(re.findall(r"(c\d+): \{([^}]*)\}", fxsrc[fxsrc.index("const FX"):fxsrc.index("};", fxsrc.index("const FX"))]))
RT = dict(re.findall(r"(c\d+): ([\d.]+)", fxsrc[fxsrc.index("const RETIME"):fxsrc.index(";", fxsrc.index("const RETIME"))]))
F = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 12); FB = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 14)
PW, IH, NH, COLS = 520, 292, 150, 4
shots = P["shots"]
for part in range(0, len(shots), 12):
    rr = shots[part:part + 12]; rows = -(-len(rr) // COLS)
    c = Image.new("RGB", (PW * COLS, (IH + NH) * rows), (238, 233, 222)); d = ImageDraw.Draw(c)
    for i, sh in enumerate(rr):
        sid = sh["id"]; s = S[sid]; x, y = (i % COLS) * PW, (i // COLS) * (IH + NH)
        lyr = " ".join(w[2] for w in W if s["t0"] <= w[0] < s["t1"])
        fx = ", ".join([FX[sid].strip()] if sid in FX else []) + (f" retime×{RT[sid]}" if sid in RT else "")
        notes = [(f"{sid}  {s['t0']:.1f}–{s['t1']:.1f}s  ({s['dur']:.1f}s)", FB),
                 (f"♪ {lyr or '— instrumental —'}", F),
                 (f"CAM: {sh['prompt']['camera']['operation']} — {sh['prompt']['camera']['instruction']}", F),
                 ("ACT: " + "; ".join(sh["prompt"]["action"][:2]), F),
                 (f"FX: {fx or 'grain, canvas weave, drift'}", F)]
        if sid in HO: notes.append((f"IN: {HO[sid]}", F))
        ty = y + 6
        for txt, font in notes:
            for line in textwrap.wrap(txt, 70 if font is F else 60)[:2]:
                if ty < y + NH - 12: d.text((x + 8, ty), line, fill=(30, 26, 22), font=font); ty += 15 if font is F else 18
        im = Image.open(f"keyframes/{sid}_start.jpg").convert("RGB").resize((PW - 8, IH - 8)); c.paste(im, (x + 4, y + NH))
        d.rectangle([x, y, x + PW - 1, y + IH + NH - 1], outline=(150, 140, 120))
    c.save(f"boards/storyboard_{part // 12 + 1}.jpg", quality=86); print("boards/storyboard_%d.jpg" % (part // 12 + 1))
