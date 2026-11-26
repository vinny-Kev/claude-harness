#!/usr/bin/env bash
# Optional statusLine helper: shows "<model> · ctx N%" and records N for nudge-low-context.sh.
# Enable in ~/.claude/settings.json (user settings; do not commit):
#   "statusLine": { "type": "command", "command": "bash /path/to/claude-harness/scripts/statusline-context.sh" }
# Already have a statusline? Copy the 4 lines that write the marker into yours.
# Context usage is only exposed to statusline scripts (not hooks) per the Claude Code docs.
input="$(cat 2>/dev/null || true)"
sid="$(printf '%s' "$input" | sed -n 's/.*"session_id" *: *"\([^"]*\)".*/\1/p' | head -n1)"
pct="$(printf '%s' "$input" | sed -n 's/.*"used_percentage" *: *\([0-9.]*\).*/\1/p' | head -n1)"
model="$(printf '%s' "$input" | sed -n 's/.*"display_name" *: *"\([^"]*\)".*/\1/p' | head -n1)"

if [[ "$sid" =~ ^[A-Za-z0-9_-]+$ && -n "$pct" ]]; then
  state="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}/claude-harness-$(id -u)"
  mkdir -p "$state" && chmod 700 "$state"
  printf '%s\n' "$pct" > "$state/ctx-$sid"
fi

if [[ -n "$pct" ]]; then
  p="${pct%.*}"; flag=""
  [[ "$p" =~ ^[0-9]+$ && $p -ge ${SWITCH_NUDGE_PCT:-70} ]] && flag=" ⚠ /switch"
  printf '%s · ctx %s%%%s' "${model:-claude}" "$p" "$flag"
else
  printf '%s' "${model:-claude}"
fi
