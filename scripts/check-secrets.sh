#!/usr/bin/env bash
# Scan for secret-shaped strings and forbidden filenames.
#   scripts/check-secrets.sh            # scan all tracked + untracked (non-ignored) files
#   scripts/check-secrets.sh --staged   # scan only staged files (pre-commit)
# Exit 1 on any finding. This is a safety net, not a guarantee.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

if [[ "${1:-}" == "--staged" ]]; then
  mapfile -t files < <(git diff --cached --name-only --diff-filter=ACMR)
else
  mapfile -t files < <(git ls-files --cached --others --exclude-standard)
fi
[[ ${#files[@]} -eq 0 ]] && exit 0

fail=0
self="scripts/check-secrets.sh"
libf="scripts/lib/secret-patterns.txt"

# 1. Forbidden filenames (allow explicit example/template files).
name_re='(^|/)(\.env(\..+)?|.*\.(pem|key|p12|pfx|jks|keystore|token)|id_(rsa|ed25519|ecdsa).*|.*credentials.*|\.npmrc|\.pypirc|\.netrc|service-account.*\.json)$'
for f in "${files[@]}"; do
  [[ "$f" =~ \.(example|template|sample)$ ]] && continue
  if [[ "$f" =~ $name_re ]]; then
    echo "FORBIDDEN FILENAME: $f"; fail=1
  fi
done

# 2. Secret-shaped content. Each pattern is ERE.
mapfile -t patterns < <(grep -vE '^(#|$)' "$(dirname "$0")/lib/secret-patterns.txt")
for f in "${files[@]}"; do
  [[ "$f" == "$self" || "$f" == "$libf" || ! -f "$f" ]] && continue
  grep -Iq . "$f" 2>/dev/null || continue            # skip binaries
  for p in "${patterns[@]}"; do
    if hits=$(grep -nE -- "$p" "$f" 2>/dev/null | grep -viE 'REDACTED|placeholder|example|<[A-Z_]+>|xxxx|your[_-]' ); [[ -n "$hits" ]]; then
      while IFS= read -r line; do
        echo "SECRET-SHAPED [$f:${line%%:*}] matches /${p:0:40}…/"
      done <<< "$hits"
      fail=1
    fi
  done
done

if [[ $fail -ne 0 ]]; then
  echo; echo "✗ check-secrets: findings above. Remove/redact them (see SECURITY.md)."; exit 1
fi
echo "✓ check-secrets: clean (${#files[@]} files)"
