#!/usr/bin/env python3
"""motion_profile.py [ids] -- mean abs frame difference per 0.5 s for each plate (from clips/*.mp4 at 160x90)."""
import sys, subprocess, numpy as np, glob, os
ids = sys.argv[1:] or sorted(os.path.basename(f)[:-4] for f in glob.glob("clips/c*.mp4"))
for sid in ids:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"clips/{sid}.mp4", "-vf", "scale=160:90,fps=24", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    F = np.frombuffer(raw, np.uint8).reshape(-1, 90, 160).astype(float); d = np.abs(np.diff(F, axis=0)).mean(axis=(1, 2))
    bins = [d[i:i + 12].mean() for i in range(0, len(d), 12)]
    first_move = next((i * 0.5 for i, b in enumerate(bins) if b > 0.6), None)
    print(f"{sid} {len(F)/24:4.1f}s first>0.6 at {first_move}s | " + " ".join(f"{b:4.1f}" for b in bins))
