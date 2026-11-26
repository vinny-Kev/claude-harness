---
name: qa-report
description: >
  Produce a thorough, execution-based QA / verification report (Markdown, with
  optional .docx) for an app or API: executive summary with pass/fail metrics,
  scope, environment and test actors/fixtures, methodology, endpoint/component
  inventory, authentication and authorization matrix, module-by-module success
  and negative/security scenarios with redacted evidence, security and access
  control defect findings (open vs fixed, with retest), and remediation
  guidance. Use for "QA report", "verification report", "test the API and
  document it", "regression/retest report", "UAT evidence", "write up the test
  results", or after fixing defects to produce a retest report.
metadata:
  tier: free
---

# QA report

The report is **derived from executed evidence**, never from assumptions. You run scenarios, record what
actually happened in a results file, and a script computes metrics, the auth matrix and tables, applies
redaction, and renders Markdown (and `.docx`).

```
discover → actors/fixtures → design scenarios → EXECUTE → qa-results.yaml → check → render → redaction check → present
```

## Workflow

### 0. Safety gate (always first)
Read [references/methodology.md](references/methodology.md#safety). Establish the **target kind** (`local`, `dev`, `staging`, `test`; `production` only with explicit written user authorization, recorded in `authorization_note`). Use **test accounts and fixtures only**, never real users or data. No load/DoS tests against shared systems.

### 1. Scope and inventory
Confirm scope in/out. Enumerate endpoints/components (use the discovery steps in the `req-res-hardening` skill if installed). Give each an id `E1…`, with module, method, path, and expected auth.

### 2. Actors and fixtures
Define actors `A0…` (anonymous, each role, cross-tenant/second user, admin, expired/invalid session). Record fixture accounts **as placeholders** (`qa_user@example.test`); credentials come from the environment or a secret store and are **never written to the results file or the report**.

### 3. Design scenarios
Follow [references/methodology.md](references/methodology.md#scenario-design): for every endpoint, success + negative + security scenarios; cover the **endpoint × actor** authorization matrix (every actor that should be allowed *and* denied). Each scenario states expected behavior *before* running.

### 4. Execute and record
Run each scenario against the target (curl/httpie, project test runner, or browser tool for UI). Record the real request, observed response excerpt and result. Use `blocked` when it could not be run (say why) and `skipped` when out of scope; never mark `pass` without evidence. Failing scenarios must link to a defect.

### 5. Write `qa-results.yaml`
Schema: [references/results-schema.md](references/results-schema.md). Start from [templates/qa-results.template.yaml](templates/qa-results.template.yaml). Save to the **target project** (e.g. `qa-output/<date>/qa-results.yaml`), not into the harness repo.

### 6. Validate, render
```bash
python3 <harness>/skills/qa-report/scripts/build-report.py check  qa-output/<date>/qa-results.yaml
python3 <harness>/skills/qa-report/scripts/build-report.py render qa-output/<date>/qa-results.yaml --docx
```
`--full` also includes evidence for passing success scenarios. Fix every `✗` error before rendering.

### 7. Redaction check
Redaction is applied automatically; then **verify**: `python3 <harness>/skills/qa-report/scripts/redact.py --check qa-output/<date>/QA-REPORT.md` and skim the evidence blocks. See [references/redaction.md](references/redaction.md).

### 8. Present
Give the verdict, key metrics, open defects by severity, blocked/untested items, and the file paths. Do not paste evidence into chat.

### Retest runs
After fixes: re-execute the linked scenarios, update their `actual/result/evidence`, set the defect `status: fixed` with `retest_evidence`, re-render. Keep prior reports; name by date. See [references/defect-tracking.md](references/defect-tracking.md).

## Report structure (rendered automatically)
1. Executive Summary & pass/fail metrics · 2. Scope · 3. Environment & test actors/fixtures · 4. Methodology · 5. Endpoint/Component Inventory · 6. Auth & Authorization Matrix · 7. Module-by-module success + negative/security scenarios · 8. Security/access-control & defect findings (open vs fixed) · 9. User remediation guidance.

## Hard rules
- **No fabricated results.** Unexecuted = `blocked`/`skipped` with a reason. The verdict follows the data.
- **Secrets never enter the results file or report**: tokens, cookies, passwords, API keys, OTPs, session ids, real PII. Use placeholders; rely on redaction only as a backstop.
- **Non-production by default.** Production only with explicit authorization, read-only unless stated.
- **Disposable data for destructive tests.** Clean up what you create.
- **Every failure has a defect; every fixed defect has retest evidence.**
- **Reports stay in the target project** (private), never committed to a public repo.
