#!/usr/bin/env python3
import sys, json, subprocess, os, shutil
sid = sys.argv[1]; src = f"keyframes/{sid}_start.jpg"; bak = f"keyframes/v4_trike/{sid}_start.jpg"
os.makedirs("keyframes/v4_trike", exist_ok=True)
if not os.path.exists(bak): shutil.copy(src, bak)
p = ("Edit the first image. Keep EVERYTHING exactly the same: composition, camera framing, every bear, the cat, their poses, faces, green eyes, hats, bagels, bottles, the icon, the samovar, the headlamp, the pipes, the banner, the crate, the wheels, the background, the lighting, the oil-painting style. "
     "Change ONLY the decoration of the war-trike's body to match the second image (the trike model sheet): remove any stars painted on the body, and paint the sidecar's visible outer side panel and the front mudguard with a Khokhloma ornament panel: black lacquer ground with scarlet berries and curling golden leaves, edged with a thin gold line; the rest of the body stays plain olive riveted steel with rust. No text.")
json.dump({"prompt": p, "input_images": [bak, "bibles/char/trike_khokh.jpeg"], "aspect_ratio": "16:9", "quality": "high", "output_format": "jpeg", "moderation": "low"}, open(f"keyframes/in_{sid}_trikeedit.json", "w"))
out = subprocess.run(["python3", "tools/rep.py", "openai/gpt-image-2.5-flare", f"keyframes/in_{sid}_trikeedit.json", f"keyframes/{sid}_tk"], capture_output=True, text=True).stdout
if '"succeeded"' in out:
    from PIL import Image
    f = next(x for x in os.listdir("keyframes") if x.startswith(f"{sid}_tk."))
    Image.open(f"keyframes/{f}").convert("RGB").resize((2048, 1152)).save(src, quality=94); os.remove(f"keyframes/{f}")
print(out)
