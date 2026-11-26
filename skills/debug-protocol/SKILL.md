---
name: debug-protocol
description: >
  Debug systematically instead of guessing: reproduce first, isolate, form
  ranked hypotheses with predictions, test one change at a time, prove the root
  cause, make the smallest fix, add a regression test, and report with
  evidence. Includes a stop rule after repeated failed hypotheses and a helper
  that measures how reliably a failure reproduces. Use for "fix this bug",
  "why is this failing", "tests are failing", "it works on my machine", "flaky
  test", "regression", "stack trace", "debug this", or any time a fix attempt
  has failed once already.
metadata:
  tier: free
---

# Debug protocol

Most wasted debugging time comes from changing code before understanding the failure. This protocol makes
the agent **observe, then explain, then fix**, and prove each step with evidence.

```
facts -> reproduce -> isolate -> hypothesize -> test -> root cause -> smallest fix -> verify -> report
```

## 0. Intake (≤ 2 minutes)
Collect, don't assume: the exact error/stack trace, **expected vs actual** behavior, how to trigger it, environment (versions, OS, config, data), when it last worked, and what changed since (`git log`, dependency or config changes). Ask the user only for what you cannot find yourself. Do **not** edit code yet.

## 1. Reproduce
Get a **deterministic, minimal** reproduction before any fix: a failing test is best, otherwise a script or exact command. Measure reliability with the helper:
```bash
bash <harness>/skills/debug-protocol/scripts/repro-check.sh -n 10 -- <command that triggers it>
```
- Fails every time: good; shrink it (fewer inputs, smaller data, fewer steps).
- Fails sometimes (flaky): that is the bug's first symptom; see [flaky tests](references/techniques.md#flaky-and-intermittent-failures). Do not "fix" until you can raise the failure rate or explain the variance.
- Cannot reproduce: say so. Gather evidence (logs, versions, data shape) and propose what to capture; **never ship a guess as a fix**.

## 2. Isolate
Shrink the search space with the cheapest tool that fits ([techniques](references/techniques.md)): read the failing line and its caller first, then `git bisect` for regressions, input minimization, "delete half", differential runs (working vs broken environment, commit, input), targeted logging. Record what is ruled out.

## 3. Hypothesize
Write 2-5 hypotheses ranked by likelihood x cheapness to test. Each must **predict something observable** that would distinguish it from the others (a value, a log line, a test outcome). Use [failure patterns](references/failure-patterns.md) for candidates. Keep them in the hypothesis log ([template](templates/hypothesis-log.template.md)); do not keep it in the repo's code directories (follow the project's knowledge-placement setting if present).

## 4. Test hypotheses
One experiment at a time: add a log/assert, print the value, change one input, or stub one dependency. Compare the observation with the prediction and mark the hypothesis **confirmed / refuted / unclear**. Revert experiments (debug prints, temp edits) before moving on.

**Stop rule:** after **3 refuted hypotheses** (or 30 minutes with no progress), stop and re-evaluate: re-read the error, list your assumptions and verify each, widen the scope (caller, config, data, environment, dependency), or ask the user for access/information. Do not start a 4th guess at the same layer.

## 5. Root cause
Explain the failure end to end: *trigger -> faulty step -> wrong state -> visible symptom*, and why it did not fail earlier. Distinguish **cause** from **symptom** (ask "why?" until the answer is a decision or a missing check you can change). Confirm with a prediction you can still falsify: "if this is the cause, then X will also fail / this input will pass".

## 6. Fix
Smallest change that removes the **cause**. No drive-by refactors, formatting churn or unrelated cleanups in the same change. Prefer fixing the invariant (validate at the boundary, make the state impossible) over patching the symptom (try/except, retry, sleep, `if x is None: return`). Check whether the same mistake exists elsewhere (`grep` the pattern) and report, or fix if in scope.

## 7. Verify
1. The regression test **fails before** the fix and **passes after** (show both when feasible).
2. The original reproduction no longer fails; re-run `repro-check.sh` with the same `-n`.
3. The relevant test suite, linter and type-check pass; no tests disabled, skipped or weakened.
4. Nearby edge cases tried (empty, null, boundary, large, concurrent).

## 8. Report
Use [templates/debug-report.template.md](templates/debug-report.template.md): symptom, reproduction, root cause, fix, evidence, prevention, follow-ups. Keep it factual and short; example: [examples/debug-protocol/DEBUG-REPORT-example.md](../../examples/debug-protocol/DEBUG-REPORT-example.md).

## Hard rules
- **No fix before reproduction**, unless reproduction is impossible, and then say so and label the fix as unverified.
- **One change per experiment.** No shotgun edits ("try a bunch of things"). Keep a log of what each experiment showed.
- **Never mask the failure**: no swallowing exceptions, retries or sleeps as the "fix", no deleting or weakening the failing test, no `@skip`.
- **Evidence over narrative.** Every claim ("the cause is X") cites an observation: output, log line, test result, `file:line`.
- **Don't blame the environment, a library or "flakiness"** without evidence (version diff, minimal repro, upstream issue).
- **Safety**: don't run destructive commands, don't touch production or real data, don't print secrets (redact tokens, cookies, personal data in logs and reports).
- **Leave no debris**: remove debug prints, temp files and experiment edits; keep only the fix and the regression test.
- **Ask when blocked** with a specific request (log, access, data sample), not "any ideas?".
