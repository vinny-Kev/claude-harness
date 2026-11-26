# Debug report: <short title>

- **Date:** <YYYY-MM-DD>   **Area:** <module/service>   **Commit:** <sha before fix>
- **Severity/impact:** <who or what was affected>

## Symptom
<Exact error or wrong behavior; expected vs actual.>

## Reproduction
```text
<command or steps>
```
Reliability before fix: <k>/<n> runs failed. After fix: <k>/<n>.

## Root cause
<Trigger -> faulty step -> wrong state -> visible symptom, and why it was not caught earlier. Cite `file:line`.>

## Evidence
- <observation that confirmed the cause: output, log line, test result>
- <hypotheses refuted and how>

## Fix
- **Change:** <what and where, `file:line`>
- **Why this addresses the cause (not the symptom):** <...>

## Verification
- Regression test `<name>`: fails before, passes after.
- Original repro: <result>.  Suite/lint/types: <result>.  Edge cases tried: <list>.

## Prevention and follow-ups
- <guard, validation, test, alert, doc, or refactor worth doing separately>
- <same pattern found elsewhere: `file:line`, fixed / not fixed>

> No secrets, tokens or personal data in this report.
