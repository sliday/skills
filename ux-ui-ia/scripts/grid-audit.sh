#!/usr/bin/env bash
# ux-ui-ia grid audit: flag px values off the 8px grid (4px half-step allowed).
# Usage: grid-audit.sh <file-or-dir> [...]
# Rules (per CSS property, not per line):
#   - 0px, 1px, 2px allowed anywhere (hairlines, borders)
#   - margins/padding/gap/sizes: n % 4 == 0 allowed (4 8 12 16 24 ...)
#   - font-size: checked against type set {12,14,16,18,20,24,30,36,48,60,72}
#   - line-height, letter-spacing: never flagged (readability beats grid)
# Exit 1 when violations found, 0 when clean.
set -u
python3 - "$@" <<'PY'
import re, sys, os

TYPE_SET = {12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72}
SKIP = ("line-height", "letter-spacing")
EXTS = (".css", ".scss", ".less", ".html", ".jsx", ".tsx", ".vue", ".svelte")
DECL = re.compile(r'([a-zA-Z-]+)\s*:\s*([^;:"\'{}]+)')
PX = re.compile(r'(\d+(?:\.\d+)?)px')

def files(targets):
    for t in targets:
        if os.path.isdir(t):
            for root, dirs, names in os.walk(t):
                dirs[:] = [d for d in dirs if d != "node_modules" and not d.startswith(".")]
                for n in names:
                    if n.endswith(EXTS):
                        yield os.path.join(root, n)
        else:
            yield t

violations = []
for f in files(sys.argv[1:]):
    try:
        lines = open(f, errors="replace").read().splitlines()
    except OSError:
        continue
    for i, line in enumerate(lines, 1):
        for prop, value in DECL.findall(line):
            p = prop.lower()
            if p.endswith(SKIP) or p in SKIP:
                continue
            for raw in PX.findall(value):
                v = float(raw)
                if "font-size" in p:
                    if v not in TYPE_SET:
                        violations.append(f"{f}:{i}: font-size {raw}px (not in type set 12/14/16/18/20/24/30/36/48/60/72)")
                elif v not in (0, 1, 2):
                    if v != int(v):
                        violations.append(f"{f}:{i}: {p} {raw}px (fractional, off-grid)")
                    elif int(v) % 4 != 0:
                        violations.append(f"{f}:{i}: {p} {raw}px (off 8px grid)")

for v in violations:
    print(v)
if violations:
    print("---")
    print(f"{len(violations)} off-grid value(s). Fix to scale 4/8/12/16/24/32/48/64/96 or document as a named exception token.")
    sys.exit(1)
print("grid clean")
PY
