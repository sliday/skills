#!/usr/bin/env bash
# ux-ui-ia craft audit: flag mechanical animation/craft defects.
# Usage: craft-audit.sh <file> [...]
# Checks (see SKILL.md 5d/5e):
#   - transition: all / Tailwind transition-all  -> list exact properties
#   - scale(0) entrance                          -> start at 0.95 + opacity 0
#   - transition/animation duration >= 400ms     -> UI ceiling is 300ms
#   - will-change with non-compositable props    -> transform/opacity only
# Exit 1 when violations found, 0 when clean.
set -u
found=0
check() { # $1 file, $2 regex, $3 message
  local out
  out=$(grep -nE "$2" "$1" 2>/dev/null)
  if [ -n "$out" ]; then
    printf '%s\n' "$out" | sed "s|^|$1:|;s|\$| -> $3|"
    found=1
  fi
}
for f in "$@"; do
  [ -f "$f" ] || continue
  check "$f" 'transition[[:space:]]*:[[:space:]]*all|[["'"'"' ]transition-all[]"'"'"' ]' 'transition: all (list exact properties: transform, opacity, ...)'
  check "$f" 'scale\([[:space:]]*0(\.0+)?[[:space:]]*\)' 'scale(0) start (use scale(0.95) + opacity: 0)'
  check "$f" '(transition|animation)[^;}]*[^0-9]([4-9][0-9][0-9]|[0-9]{4,})ms' 'duration >=400ms (UI ceiling 300ms; exits ~150ms)'
  check "$f" 'will-change[[:space:]]*:[^;}]*(all|width|height|top|left|padding|background)' 'will-change on non-compositable property (transform/opacity only)'
done
if [ "$found" = 1 ]; then
  echo "---"
  echo "craft violations. Animate only transform/opacity/filter/clip-path; enters ease-out <=300ms from scale(0.95); exits shorter."
  exit 1
fi
echo "craft clean"
