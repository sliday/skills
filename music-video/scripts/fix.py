#!/usr/bin/env python3
"""fix.py <image> "<fix instruction>" "<keep list>" -- surgical repair with gpt-image-2.5-flare (won the c23 A/B vs sunburst, Qwen-Edit-2511, FLUX Kontext Max).
Keeps the original as <image>.bak.jpg, writes the repaired JPEG in place."""
import sys, json, subprocess, shutil, os, pathlib
img, fix, keep = sys.argv[1], sys.argv[2], sys.argv[3]
base = os.path.splitext(img)[0]
shutil.copy(img, base + ".bak" + os.path.splitext(img)[1])
p = (f"Edit this image. Keep EVERYTHING exactly the same: composition, every character, every object, colours, painted cut-out canvas style. "
     f"Explicitly keep: {keep}. Fix only this mistake: {fix}. No other changes. No text.")
inp = {"prompt": p, "input_images": [base + ".bak" + os.path.splitext(img)[1]], "aspect_ratio": "16:9", "quality": "high", "output_format": "jpeg", "moderation": "low"}
pathlib.Path(base + ".fix.json").write_text(json.dumps(inp, ensure_ascii=False))
out = subprocess.run(["python3", "tools/rep.py", "openai/gpt-image-2.5-flare", base + ".fix.json", base + ".fixed"], capture_output=True, text=True).stdout
print(out)
if '"succeeded"' in out:
    f = next(x for x in os.listdir(os.path.dirname(img) or ".") if os.path.basename(base) + ".fixed" in x)
    subprocess.run(["sips", "-s", "format", "jpeg", os.path.join(os.path.dirname(img), f), "--out", base + ".jpg"], capture_output=True)
