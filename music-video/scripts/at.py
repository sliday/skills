#!/usr/bin/env python3
"""at.py out.jpg cols w dir t1 t2 ... -- contact sheet of rendered frames at times (s)"""
import sys, subprocess
out, cols, w, d = sys.argv[1:5]; ts = [float(x) for x in sys.argv[5:]]
subprocess.run([sys.executable, "tools/contact.py", out, cols, w] + [f"{d}/{int(t*24):05d}.jpg" for t in ts], check=True)
