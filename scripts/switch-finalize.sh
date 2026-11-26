#!/usr/bin/env bash
# Finalize a /switch handoff: secret-scan it, mark it pending, print the switching steps.
#   switch-finalize.sh <handoff-file> [model]
# Exit 1 if the handoff contains secret-shaped strings (nothing is marked pending).
set -euo pipefail

file="${1:-}"; model="${2:-sonnet}"
[[ -f "$file" ]] || { echo "handoff file not found: ${file:-<none>}" >&2; exit 2; }
[[ "$model" =~ ^[A-Za-z0-9._-]+(\[[0-9a-z]+\])?$ ]] || { echo "invalid model alias: $model" >&2; exit 2; }

dir="$(cd "$(dirname "$file")" && pwd)"
abs="$dir/$(basename "$file")"
[[ "$dir" == */.claude/handoff ]] || { echo "handoff must live in <project>/.claude/handoff/ (got $dir)" >&2; exit 2; }
root="${dir%/.claude/handoff}"

# 1. Secret-shape scan (reports line numbers only, never values).
patterns="$(dirname "$0")/lib/secret-patterns.txt"
fail=0
while IFS= read -r p; do
  [[ -z "$p" || "$p" == \#* ]] && continue
  if hits=$(grep -nE -- "$p" "$abs" 2>/dev/null | grep -viE 'REDACTED|placeholder|example|<[A-Z_]+>' ); [[ -n "$hits" ]]; then
    while IFS= read -r l; do echo "SECRET-SHAPED text at ${abs}:${l%%:*} — redact it, then re-run." >&2; done <<< "$hits"
    fail=1
  fi
done < "$patterns"
[[ $fail -eq 0 ]] || { echo "✗ handoff NOT finalized." >&2; exit 1; }

# 2. Size hint (the next session pays tokens to read this).
lines=$(wc -l < "$abs")
[[ $lines -gt 250 ]] && echo "⚠ handoff is $lines lines; consider trimming to ≤ 150 to save tokens."

# 3. Mark pending + stable pointer.
cp "$abs" "$dir/LATEST.md"
printf '%s\n' "$abs" > "$dir/.pending"
rm -f "$dir/.pending.consumed"

# 4. Privacy: handoffs may contain private project details; make sure git ignores them.
if git -C "$root" rev-parse --git-dir >/dev/null 2>&1 && ! git -C "$root" check-ignore -q ".claude/handoff/LATEST.md"; then
  echo "⚠ .claude/handoff/ is not git-ignored in this project. Add it to .gitignore before committing."
fi

launcher="$(cd "$(dirname "$0")" && pwd)/switch-launch.sh"
cat <<EOF
✓ Handoff saved: $abs  ($lines lines)
  Pointer:       $dir/LATEST.md  (pending: the next new/cleared session loads it automatically)

A slash command cannot run /model or /exit for you. Pick one:

  A) Same window (fastest)
       /model $model
       /clear            ← the SessionStart hook loads the handoff into the fresh context

  B) New session
       /exit
       bash "$launcher" $model      (run from: $root)
     or: claude --model $model "Read .claude/handoff/LATEST.md and continue from 'Next up'."

Option A/B auto-load requires the claude-harness plugin to be installed; otherwise use B.
EOF
