#!/usr/bin/env bash
# ux-ui-ia design guard: PostToolUse hook for Edit|Write|MultiEdit.
# After a style-bearing file is edited, runs the 8px grid audit and the
# craft audit, and feeds violations back to the agent as a fix prompt
# ("block" only surfaces the reason; the edit itself already landed).
# Never fails hard, never retries, no tool calls. Exit 0 always.
set -u
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"

payload=$(cat 2>/dev/null) || exit 0
file=$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get("tool_input", {}).get("file_path", ""))
except Exception:
    pass
' 2>/dev/null) || exit 0

case "$file" in
  *.css|*.scss|*.less|*.html|*.jsx|*.tsx|*.vue|*.svelte) ;;
  *) exit 0 ;;
esac
[ -f "$file" ] || exit 0

report=""
for audit in grid-audit craft-audit; do
  s="$SELF_DIR/../scripts/$audit.sh"
  [ -x "$s" ] || continue
  out=$("$s" "$file" 2>/dev/null)
  if [ $? -ne 0 ]; then report="$report$out"$'\n'; fi
done
[ -n "$report" ] || exit 0

printf '%s' "$report" | head -14 | python3 -c '
import json, sys
reason = sys.stdin.read()
print(json.dumps({
    "decision": "block",
    "reason": "ux-ui-ia design guard: defects in the file you just edited.\n"
              + reason
              + "\nGrid: 4/8/12/16/24/32/48/64/96, type 12/14/16/20/24/32, or a named exception token. Craft: exact transition properties, <=300ms, scale(0.95) enters."
}))
' 2>/dev/null || exit 0
exit 0
