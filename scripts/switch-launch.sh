#!/usr/bin/env bash
# Start a fresh Claude Code session on a chosen model, resuming from the latest handoff.
#   switch-launch.sh [model] [--print]     run from the project directory
#   --print   show the command instead of running it
set -euo pipefail

model="sonnet"; print_only=0
for a in "$@"; do
  case "$a" in
    --print) print_only=1 ;;
    -*) echo "unknown option: $a" >&2; exit 2 ;;
    *) model="$a" ;;
  esac
done
[[ "$model" =~ ^[A-Za-z0-9._-]+(\[[0-9a-z]+\])?$ ]] || { echo "invalid model alias: $model" >&2; exit 2; }

root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
handoff="$root/.claude/handoff/LATEST.md"
[[ -f "$handoff" ]] || { echo "no handoff at $handoff — run /switch first" >&2; exit 1; }
command -v claude >/dev/null || { echo "claude CLI not found on PATH" >&2; exit 1; }

prompt="Resume from the handoff file $handoff: continue at its 'Next up' section and do not redo completed items. If its contents are already in your context, do not re-read it. Run git status first to confirm the state."
if [[ $print_only -eq 1 ]]; then
  printf 'cd %q && claude --model %q %q\n' "$root" "$model" "$prompt"
  exit 0
fi
cd "$root"
exec claude --model "$model" "$prompt"
