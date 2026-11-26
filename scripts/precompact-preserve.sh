#!/usr/bin/env bash
# PreCompact hook (matcher: auto|manual). Stdout becomes extra instructions for the compaction
# summary, so the summary keeps what a handoff would need.
cat >/dev/null 2>&1 || true
cat <<'EOF'
When summarizing, preserve: the user's overall goal; the plan with checked/unchecked steps; key files and their roles;
decisions and why; the exact next action; failed attempts not to retry; verification commands. Omit raw tool output.
Never include secrets, tokens, cookies or personal data in the summary.
EOF
exit 0
