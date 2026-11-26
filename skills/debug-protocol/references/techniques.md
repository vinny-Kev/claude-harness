# Debugging techniques

Pick the cheapest technique that cuts the search space in half.

## Read before running
- Read the **exact error message** and the **first frame in your code** of the stack trace; the last frame is often a library, the first frame in your code is usually where the bad value entered.
- Read the failing test's assertion and the code it exercises. Compare expected and actual character by character (whitespace, case, types, units).
- Check the obvious: typos, wrong variable, wrong file/environment, stale build, wrong branch, cached result.

## Narrowing techniques
| Technique | Use when | How |
|---|---|---|
| **git bisect** | It worked before | `git bisect start; git bisect bad; git bisect good <sha>`, then `git bisect run <repro command>`; exit 0 = good, 1-124 = bad, 125 = skip. Always `git bisect reset` after |
| **Input minimization** | Big input triggers it | Remove half the input; keep the half that still fails; repeat until you cannot remove more |
| **Delete half** | Large code path | Comment out or stub half the steps; the failure tells you which half holds the bug |
| **Differential run** | Works in A, fails in B | Diff versions, config, env vars, data, OS, dependency lock files; change one difference at a time |
| **Targeted logging / asserts** | State is unclear | Log inputs and outputs at boundaries; assert invariants where they should hold; the first violated assertion is closest to the cause |
| **Debugger / REPL** | Need to inspect live state | Breakpoint at the first suspicious frame; inspect values, step to the divergence |
| **Binary search on config/flags** | Many toggles | Enable half the flags; narrow |
| **Rubber-duck** | Stuck | State the failing behavior, the code path and your assumptions line by line; verify each assumption with a check, not memory |
| **Simplify the environment** | Heisenbugs | Remove parallelism, caching, retries, mocks, optimizations to see whether the failure persists |

## Assumption audit
List what you believe is true ("this function is called with a non-empty list", "the DB is migrated", "this env var is set") and **verify each with an observation**. The bug lives in the assumption you did not check.

## Flaky and intermittent failures
1. **Quantify**: `repro-check.sh -n 30 -- <cmd>`; note the failure rate and the distinct failure signatures it prints.
2. **Look for shared state**: test order, leftover files/DB rows, singletons, global config, environment variables, time, randomness, port reuse, caches.
3. **Look for timing**: races, missing awaits, async callbacks, sleeps instead of conditions, slow CI, timeouts, clock/timezone/DST edges.
4. **Make it deterministic**: seed randomness, freeze time, serialize tests, add ordering, run the one test in isolation, then with its neighbors.
5. **Stress it**: run in a loop, under load, with CPU limits, in parallel, to raise the failure rate; a bug you can trigger 1 in 3 times is debuggable.
6. **Fix the cause** (synchronization, isolation, determinism). Never "fix" with retries or longer sleeps without explaining the race.

## Regressions
Find the last good state (`git log`, release tags, CI history), bisect, then read the culprit diff for *why* it breaks, not just *where*.

## Performance problems
Measure first (profiler, timing, query log); change one thing; re-measure. Look for N+1 queries, repeated work in loops, missing indexes, unbounded growth, synchronous I/O in hot paths, and accidental O(n^2).

## Concurrency and ordering
Suspect shared mutable state, check-then-act races, missing locks/transactions, event ordering assumptions, retry/duplicate delivery. Add logging with timestamps and thread/request ids before theorizing.

## Hypothesis log discipline
For every experiment write: hypothesis, prediction, action, observation, verdict. It prevents re-running refuted ideas and makes the report easy ([template](../templates/hypothesis-log.template.md)).

## Evidence hygiene
Capture failing output verbatim (trimmed), with command and commit. Redact tokens, cookies, personal data before pasting into notes, tickets or reports.
