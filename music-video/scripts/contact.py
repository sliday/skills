#!/usr/bin/env python3
"""contact.py out.jpg cols w img1 [img2...] -- labeled contact sheet"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
out, cols, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); ims = sys.argv[4:]
h = w * 9 // 16; rows = -(-len(ims) // cols)
sheet = Image.new("RGB", (cols * w, rows * h), "black"); d = ImageDraw.Draw(sheet)
try: f = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 22)
except Exception: f = None
for i, p in enumerate(ims):
    im = Image.open(p).convert("RGB").resize((w, h)); x, y = (i % cols) * w, (i // cols) * h
    sheet.paste(im, (x, y)); lab = os.path.splitext(os.path.basename(p))[0]
    d.rectangle([x, y, x + 130, y + 30], fill="black"); d.text((x + 6, y + 3), lab, fill="yellow", font=f)
sheet.save(out, quality=85)
