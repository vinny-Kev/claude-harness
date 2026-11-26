#!/usr/bin/env bash
# Hook wrapper for knowledge.py: fail open (never block or break a session) if python3 is missing.
#   knowledge-hook.sh guard|session-start
command -v python3 >/dev/null 2>&1 || exit 0
exec python3 "$(dirname "$0")/../skills/knowledge-placement/scripts/knowledge.py" "$@"
