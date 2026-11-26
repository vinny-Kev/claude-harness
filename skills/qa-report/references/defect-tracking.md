# Defect tracking (open vs fixed)

## Lifecycle
`open` → (fix applied) → `retest` → `fixed` (with `retest_evidence`) · or `wont_fix` (accepted risk, with reason in `description`).

- A defect is created when a scenario **fails**: set the scenario's `defect` to its id.
- Severity uses the scale from the `req-res-hardening` skill: **critical** (exploitable now, mass exposure/auth bypass) · **high** (ordinary-account exploit, significant impact) · **medium** (needs conditions/limited impact) · **low** (hardening) · **info**.
- Group symptoms with one root cause under one defect; list every failing scenario it explains (the report derives "Found by").

## Retest procedure
1. Developer applies the fix; note the build/commit in `meta.environment.build`.
2. Re-run **the same scenarios** that exposed the defect, plus neighbors that could regress (other actors, other endpoints sharing the code).
3. Update each scenario's `actual`, `result`, `evidence`. Keep `defect:` on a now-passing scenario so the link is visible.
4. Set the defect `status: fixed` and write `retest_evidence` (which scenarios, on which build, what was observed).
5. If still failing, keep `open` and add what changed.
6. Re-render under a new date folder; keep the previous report for history.

## Open vs fixed in the report
Section 8 lists **8.1 Open** (including `retest`), **8.2 Fixed and retested**, and **8.3 Won't fix**. The executive summary counts them by severity.

## Verdict impact
Open critical/high defects make the verdict **FAIL** regardless of pass rate.

## Hygiene
- IDs are stable across runs (D1 stays D1) so progress is traceable.
- Don't delete fixed defects; they document what was verified.
- `fix` must be concrete (code-level or config-level), not "sanitize input".
