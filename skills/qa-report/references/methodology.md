# Methodology

## Safety
1. **Target kind** decides what is allowed:
   | Kind | Allowed |
   |---|---|
   | `local` / `dev` / `test` | Full functional, negative and security scenarios; destructive tests on disposable data |
   | `staging` | As above on seeded data; avoid heavy load; coordinate shared resources |
   | `production` | Only with explicit written authorization from the user (recorded in `environment.authorization_note`), read-only scenarios, no brute force, no destructive writes |
2. **Test accounts only.** Create/seed accounts such as `qa_user@example.test`. Never log into real accounts, never use real customer data.
3. **No credentials on disk in the report pipeline.** Read them from environment variables or a secret store at execution time; the results file refers to actors by id and fixture label only.
4. **Rate and blast radius.** Brute-force/rate-limit probes use a handful of requests against local/dev instances; no load or DoS tests on shared systems.
5. **Clean up** created records when practical; note leftovers in the report.

## Environment record
Capture: environment name/kind, target URL, build/commit, DB/seed version, relevant flags (feature toggles, stubbed services), tool versions. Put extra items under `environment` (they appear in the report).

## Scenario design
For **every** inventory item create at least:

| Type | What | Examples |
|---|---|---|
| `success` | Documented happy path works for an authorized actor | Valid create/read/update/delete; pagination; correct response shape |
| `negative` | Bad input or state is rejected cleanly (4xx, no 500, no leak) | Missing/invalid fields, wrong types, negative/huge numbers, malformed JSON, wrong content type, oversized body, duplicate create, not-found, conflict |
| `security` | Access control and abuse resistance | Anonymous access, wrong role, **other user's object (IDOR)**, expired/invalid token, mass assignment (`role`, `tenantId`), injection probes (`' OR 1=1--`, `{"$ne":null}`, `../../`), XSS payload stored and rendered, enumeration (same response for existing/non-existing), rate limit on login/OTP/reset, CSRF/origin on state changes, verbose errors |

### Authorization matrix coverage
Build the grid **inventory × actors**. For each cell decide expected `allow`/`deny` from the intended policy (not from current behavior). Create a scenario per interesting cell and set `authz: {expected, actual}`. Minimum: anonymous, each role, and a second same-role user for every object-level endpoint.

### Writing a good scenario
- `expected` is written before execution, from the requirement or policy.
- `request` is reproducible (method, path, relevant headers/body with placeholders).
- `actual` is one factual sentence (status + notable fields).
- `evidence` is the trimmed real response/command output, enough to prove the result.
- One behavior per scenario; one result per scenario.

## Execution notes
- Prefer scripted, repeatable commands (curl, httpie, the project's test runner). For UI components use the browser tooling and record the observed state.
- Check side effects: DB/state changed or not (for denied writes especially).
- Re-run flaky results once; record both if they differ and mark `blocked` if unresolved.
- Use `blocked` (cannot run: missing dependency, environment limit) vs `skipped` (deliberately out of scope), always with a reason in `actual`.

## Verdict logic (computed by the script)
- **FAIL**: any open/retest defect of severity critical or high.
- **PASS WITH ISSUES**: open lower-severity defects, failures or blocked scenarios remain.
- **PASS**: all executed scenarios pass, no open defects, nothing blocked.
