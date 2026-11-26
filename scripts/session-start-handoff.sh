#!/usr/bin/env bash
# SessionStart hook (matcher: startup|clear). If /switch left a pending handoff, print it so it is
# added to the new session's context, then mark it consumed so it loads only once.
# Plain stdout from SessionStart is added as context. Never fails the session.
set -u
cat >/dev/null 2>&1 || true            # drain hook JSON on stdin

root="${CLAUDE_PROJECT_DIR:-$PWD}"
pending="$root/.claude/handoff/.pending"
max_age_min="${SWITCH_HANDOFF_MAX_AGE_MIN:-4320}"    # ignore handoffs older than 72h
max_chars="${SWITCH_HANDOFF_MAX_CHARS:-12000}"

[[ -f "$pending" ]] || exit 0
path="$(head -n1 "$pending")"
# Only load files inside this project's handoff directory.
case "$path" in "$root"/.claude/handoff/HANDOFF-*.md) ;; *) exit 0 ;; esac
[[ -f "$path" ]] || exit 0
[[ -n "$(find "$path" -mmin -"$max_age_min" 2>/dev/null)" ]] || exit 0

echo "## Handoff from a previous session (loaded by claude-harness)"
echo "Source: $path"
echo "Resume from the \"Next up\" section. Do not redo completed items. If the user's request is clearly unrelated to this handoff, say so briefly and follow the user."
echo
head -c "$max_chars" "$path"
if [[ $(wc -c < "$path") -gt $max_chars ]]; then
  echo; echo "[handoff truncated at $max_chars chars; full file: $path]"
fi

mv -f "$pending" "$root/.claude/handoff/.pending.consumed" 2>/dev/null || true
exit 0
