#!/usr/bin/env bash
# Tests for repro-check.sh. Run: bash skills/debug-protocol/scripts/test_repro_check.sh
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
rc="$here/repro-check.sh"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
fails=0
ok()   { echo "  ok   $1"; }
bad()  { echo "  FAIL $1"; fails=$((fails + 1)); }
expect() { # name expected-exit pattern -- command...
  local name="$1" code="$2" pat="$3"; shift 4
  local out; out="$("$@" 2>&1)"; local got=$?
  if [[ $got -eq $code ]] && grep -qE -- "$pat" <<<"$out"; then ok "$name"; else bad "$name (exit $got, wanted $code, pattern '$pat')"; echo "$out" | sed 's/^/       /'; fi
}

cat >"$tmp/pass.sh" <<'EOF'
#!/bin/bash
exit 0
EOF
cat >"$tmp/fail.sh" <<'EOF'
#!/bin/bash
echo "starting"; echo "Error: boom id=$RANDOM" >&2; exit 3
EOF
cat >"$tmp/flaky.sh" <<EOF
#!/bin/bash
f="$tmp/count"; c=\$(cat "\$f" 2>/dev/null || echo 0); c=\$((c+1)); echo \$c >"\$f"
if (( c % 3 == 0 )); then echo "flaky failure at step \$c" >&2; exit 1; fi
exit 0
EOF
cat >"$tmp/slow.sh" <<'EOF'
#!/bin/bash
sleep 5
EOF
chmod +x "$tmp"/*.sh

expect "all pass"             0 "Verdict: PASS"                 -- bash "$rc" -n 5 -- "$tmp/pass.sh"
expect "consistent failure"   1 "CONSISTENT FAILURE"            -- bash "$rc" -n 4 -- "$tmp/fail.sh"
expect "signatures grouped"   1 "4x  exit 3"                    -- bash "$rc" -n 4 -- "$tmp/fail.sh"
expect "flaky detected"       1 "FLAKY \(fails 3/9\)"           -- bash "$rc" -n 9 -- "$tmp/flaky.sh"
expect "failure rate printed" 1 "failure rate 33%"              -- bash "$rc" -n 9 -- "$tmp/flaky.sh"
rm -f "$tmp/count"
expect "stop at first fail"   1 "Runs: 3 "                      -- bash "$rc" -n 9 -x -- "$tmp/flaky.sh"
if command -v timeout >/dev/null 2>&1; then
  expect "timeout reported"   1 "TIMEOUT"                       -- bash "$rc" -n 1 -t 1 -- "$tmp/slow.sh"
fi
expect "bad -n rejected"      2 "-n must be"                    -- bash "$rc" -n 0 -- true
expect "missing command"      2 "missing command"               -- bash "$rc" -n 2
expect "quiet hides output"   1 "Verdict"                       -- bash "$rc" -q -n 1 -- "$tmp/fail.sh"
out="$(bash "$rc" -q -n 1 -- "$tmp/fail.sh" 2>&1)"; grep -q "first failing run" <<<"$out" && bad "-q still printed output" || ok "-q suppresses first-failure output"

echo
if [[ $fails -eq 0 ]]; then echo "all tests passed"; else echo "$fails test(s) failed"; exit 1; fi
