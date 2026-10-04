#!/usr/bin/env python3
"""plate_refs.py c26 [...] -- fal minimax/h3-max/reference-to-video with references chosen from WHAT IS IN THE FRAME.
Start frame: handoff keyframes/<id>_start.jpg if present, else berloga3's. Caption: handoff caption if present, else berloga3's.
References: 2 style paintings + one model sheet per entity detected in the cast list or the frame caption (bears, cat, trike, moth/icon,
samovar/flamethrower/mortar, Rozh/Jesus-airplane/flying men/churches/village). Full STYLE text appended. No end/mid frames."""
import json, sys, os, re, subprocess
B = "/Users/stas/Playground/slopcore/berloga3"
M = json.load(open(B + "/docs/motion.json")); SH = {s["id"]: s for s in json.load(open(B + "/docs/shots.json"))}
STYLE = open("bibles/STYLE.txt").read().strip()
SHEETS = [  # (keywords, path, description)
 (("bear", "cub", "father", "mother"), B + "/bibles/char/oil_family.jpeg", "the FAMILY SHEET: exact father, mother and cub bears and the striped cat"),
 (("motorcycle", "trike", "sidecar"), B + "/bibles/char/trike_khokh.jpeg", "the WAR-TRIKE MODEL SHEET: the one exact vehicle (olive riveted body, Khokhloma samovar fuel tank, Khokhloma sidecar panel, one eye-like headlamp, three exhaust pipes, red banner) from five angles"),
 (("moth", "icon", "framed picture", "framed image", "butterfly"), B + "/bibles/char/moth_v3.jpeg", "the MOTH MODEL SHEET: the one moth and its icon in every format"),
 (("samovar", "flamethrower", "mortar", "spinning top", "fire", "flame", "burst", "explos"), B + "/bibles/char/samovar_v2.jpeg", "the SAMOVAR / TOP-MORTAR / KHOKHLOMA FIRE sheet: fire and bursts are flat Khokhloma lacquer ornament"),
 (("rozh", "jesus", "airplane", "angel", "wings", "church", "onion", "dome", "village", "house"), B + "/bibles/char/oil_world.jpeg", "the WORLD SHEET: Rozh, the Jesus-airplane, the flying men, onion churches, crooked naive houses"),
]
CASTKW = {"big": "bear", "she": "bear", "cub": "bear", "cat": "bear", "moth": "moth", "rozh": "rozh", "jesus_plane": "jesus", "winged": "angel"}
for sid in [a for a in sys.argv[1:] if not a.startswith("--")]:
    start = f"keyframes/{sid}_start.jpg" if os.path.exists(f"keyframes/{sid}_start.jpg") else f"{B}/keyframes/{sid}_start.jpg"
    capf = f"keyframes/{sid}_start.caption.txt" if os.path.exists(f"keyframes/{sid}_start.caption.txt") else f"{B}/keyframes/{sid}_start.caption.txt"
    cap = re.sub(r"\s+", " ", open(capf).read().strip()); low = (cap + " " + " ".join(CASTKW.get(c, "") for c in SH[sid]["cast"]) + (" trike" if SH[sid]["trike"] else "")).lower()
    refs = [(B + "/source/refs/style/s2_giant_bears.jpg", "the master STYLE painting: naive oil on woven canvas"),
            (B + "/source/refs/style/s1_bears_bed.png", "a second STYLE painting, smooth glazed oil")]
    refs += [(p, d) for kws, p, d in SHEETS if any(k in low for k in kws)]
    p = M[sid]["prompt"]
    i = p.index("THE OPENING FRAME shows: "); j = p.index("Anything frozen mid-motion")
    p = p[:i] + "THE OPENING FRAME shows: " + (cap if len(cap) <= 900 else cap[:900].rsplit(" ", 1)[0] + "...") + " " + p[j:]
    names = " ".join(f"Image {k+1} is {d}." for k, (_, d) in enumerate(refs))
    p += (f" REFERENCE IMAGES (design and style only, never copy their compositions): {names} Every character, vehicle and prop that is visible keeps exactly its design from its sheet, in every frame, however small it is in the picture. "
          f"Everything in every frame is painted in exactly this style: {STYLE} It must look like a hand-painted naive oil painting on canvas in every frame.")
    inp = {"prompt": p, "image_url": start, "reference_image_urls": [r for r, _ in refs], "duration": M[sid]["duration"],
           "resolution": "1080P", "prompt_expansion_mode": "disabled", "aspect_ratio": "16:9"}
    json.dump(inp, open(f"clips/{sid}.fal.in.json", "w"), ensure_ascii=False)
    print(sid, "refs:", [os.path.basename(r) for r, _ in refs], flush=True)
    print(subprocess.run([".venv/bin/python", "tools/fal.py", "minimax/h3-max/reference-to-video", f"clips/{sid}.fal.in.json", f"clips/{sid}"], capture_output=True, text=True).stdout, flush=True)
