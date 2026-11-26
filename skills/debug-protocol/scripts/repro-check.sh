#!/usr/bin/env bash
# Run a command N times and report how reliably it fails, grouped by failure signature.
#   repro-check.sh [-n RUNS] [-t TIMEOUT_SECONDS] [-x] [-q] -- <command> [args...]
#     -n  runs (1-200, default 10)      -t  per-run timeout in seconds (default 60, needs coreutils `timeout`)
#     -x  stop at the first failure      -q  do not print the output of the first failing run
# Exit: 0 = every run passed, 1 = at least one run failed, 2 = usage error.
# Output of failing runs is shown trimmed: redact secrets before pasting it elsewhere.
set -uo pipefail

usage() { sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; }
n=10; t=60; stop=0; show=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    -n) n="${2:-}"; shift 2 ;;
    -t) t="${2:-}"; shift 2 ;;
    -x) stop=1; shift ;;
    -q) show=0; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; break ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done
[[ $# -gt 0 ]] || { echo "missing command after --" >&2; usage >&2; exit 2; }
[[ "$n" =~ ^[0-9]+$ && $n -ge 1 && $n -le 200 ]] || { echo "-n must be 1-200" >&2; exit 2; }
[[ "$t" =~ ^[0-9]+$ && $t -ge 1 && $t -le 3600 ]] || { echo "-t must be 1-3600" >&2; exit 2; }

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
have_timeout=0; command -v timeout >/dev/null 2>&1 && have_timeout=1
declare -A count example rcs
pass=0; fail=0; ran=0; first_fail_out=""

for ((i = 1; i <= n; i++)); do
  if [[ $have_timeout -eq 1 ]]; then timeout "$t" "$@" >"$tmp/out" 2>&1; rc=$?; else "$@" >"$tmp/out" 2>&1; rc=$?; fi
  ran=$((ran + 1))
  if [[ $rc -eq 0 ]]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    if [[ $rc -eq 124 && $have_timeout -eq 1 ]]; then
      sig="TIMEOUT"; last="timed out after ${t}s"
    else
      # signature: last 3 lines with numbers/addresses normalized, so ids and timings do not split groups
      sig="rc$rc:$(tail -n 3 "$tmp/out" | sed -E 's/0x[0-9a-fA-F]+/0xH/g; s/[0-9]+/N/g' | tr -s ' ' | sha1sum | cut -c1-8)"
      last="$(grep -v '^[[:space:]]*$' "$tmp/out" | tail -n 1 | cut -c1-160)"
    fi
    count[$sig]=$(( ${count[$sig]:-0} + 1 ))
    [[ -n "${example[$sig]:-}" ]] || example[$sig]="$last"
    rcs[$sig]="$rc"
    if [[ -z "$first_fail_out" ]]; then first_fail_out="$(tail -n 25 "$tmp/out" | cut -c1-200)"; fi
    [[ $stop -eq 1 ]] && break
  fi
done

printf "Command:"; printf " %q" "$@"; echo
echo "Runs: $ran   Passed: $pass   Failed: $fail   (failure rate $(( 100 * fail / ran ))%)"
if [[ $fail -eq 0 ]]; then
  echo "Verdict: PASS (no failure in $ran runs; this does not prove the bug is gone, only that it was not seen)"
  exit 0
fi
if [[ $pass -eq 0 ]]; then echo "Verdict: CONSISTENT FAILURE (reproduces every run)"; else echo "Verdict: FLAKY (fails $fail/$ran): find the variance before fixing"; fi
echo "Failure signatures:"
for sig in "${!count[@]}"; do
  printf '  %3dx  exit %s  [%s]  %s\n' "${count[$sig]}" "${rcs[$sig]}" "$sig" "${example[$sig]}"
done | sort -rn
if [[ $show -eq 1 && -n "$first_fail_out" ]]; then
  echo "--- first failing run (last 25 lines) ---"
  echo "$first_fail_out"
fi
exit 1
