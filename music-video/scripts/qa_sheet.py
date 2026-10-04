#!/usr/bin/env python3
"""qa_sheet.py out.jpg id [id...] -- per shot one row: 5 evenly spaced frames from frames/<id>, tiny corner label"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
out, ids = sys.argv[1], sys.argv[2:]; W, H, N = 320, 180, 5
f = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 11); c = Image.new("RGB", (W * N, H * len(ids)), "black"); d = ImageDraw.Draw(c)
for r, sid in enumerate(ids):
    fs = sorted(x for x in os.listdir(f"frames/{sid}") if x.endswith(".jpg"))
    for k in range(N):
        im = Image.open(f"frames/{sid}/{fs[int((len(fs) - 1) * k / (N - 1))]}").convert("RGB").resize((W, H)); c.paste(im, (k * W, r * H))
    d.rectangle([0, r * H + H - 14, 34, r * H + H], fill="black"); d.text((2, r * H + H - 13), sid, fill="yellow", font=f)
c.save(out, quality=85)
