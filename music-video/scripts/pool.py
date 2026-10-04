#!/usr/bin/env python3
"""pool.py N cmd... -- run 'cmd ID' for each ID on stdin, rolling pool of N, up to 3 attempts each"""
import sys, subprocess, concurrent.futures as cf, time
n = int(sys.argv[1]); cmd = sys.argv[2:]; ids = [l.strip() for l in sys.stdin if l.strip()]
def run(i):
    for k in range(3):
        out = subprocess.run(cmd + [i], capture_output=True, text=True).stdout
        if '"succeeded"' in out: return f"{i} ok (try {k+1})"
        time.sleep(20)
    return f"{i} FAILED: {out[-200:]}"
with cf.ThreadPoolExecutor(n) as ex:
    for r in ex.map(run, ids): print(r, flush=True)
