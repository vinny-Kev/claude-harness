#!/usr/bin/env bash
# UserPromptSubmit hook (optional). If the statusline helper recorded high context usage for this
# session, add a one-line reminder that /switch exists. Rate-limited. Never fails the prompt.
# Hook stdin has no context-usage field, so this depends on scripts/statusline-context.sh.
set -u
input="$(cat 2>/dev/null || true)"
sid="$(printf '%s' "$input" | sed -n 's/.*"session_id" *: *"\([^"]*\)".*/\1/p' | head -n1)"
[[ "$sid" =~ ^[A-Za-z0-9_-]+$ ]] || exit 0

state="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}/claude-harness-$(id -u)"
marker="$state/ctx-$sid"; nudged="$state/nudged-$sid"
[[ -f "$marker" ]] || exit 0

pct="$(cut -d. -f1 "$marker" 2>/dev/null)"
[[ "$pct" =~ ^[0-9]+$ ]] || exit 0
threshold="${SWITCH_NUDGE_PCT:-70}"
cooldown_min="${SWITCH_NUDGE_COOLDOWN_MIN:-15}"
[[ $pct -ge $threshold ]] || exit 0
[[ -z "$(find "$nudged" -mmin -"$cooldown_min" 2>/dev/null)" ]] || exit 0

touch "$nudged"
echo "[claude-harness] The context window is about ${pct}% full. At a natural stopping point, tell the user once, in one sentence, that /switch can save a handoff for a fresh session. Do not interrupt the current task."
exit 0
