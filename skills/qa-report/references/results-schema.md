# `qa-results.yaml` schema

Validated by `build-report.py check`. Quote any value containing `: ` or starting with a special character.

```yaml
meta:
  title: QA Verification Report - <project> <version>
  project: <name>
  date: 2026-11-26
  tester: <who ran it>
  environment:
    name: Local docker-compose
    kind: local              # local | dev | staging | test | production
    target: http://localhost:3000
    build: "commit abc1234"
    authorization_note: ""   # REQUIRED if kind: production
    # any extra keys (database, notes, tool versions) are listed in the report

summary: >                   # 3-6 sentences: what was tested, headline result, top risks
scope: { in: [..], out: [..] }
methodology: >               # optional; sensible default if omitted

actors:                      # no credentials, ever
  - {id: A0, role: Anonymous, description: "", fixture: "-"}
  - {id: A1, role: Customer, description: "", fixture: "qa_user@example.test (password in secret store)"}
fixtures:
  - {id: F1, description: "seed data description"}

inventory:
  - {id: E1, module: Auth, kind: endpoint, name: Login, method: POST, path: /login, auth: public}

scenarios:
  - id: S1
    module: Auth                 # groups section 7
    inventory: E1                # must exist
    type: success                # success | negative | security
    title: Valid credentials return a session
    actor: A1                    # must exist
    request: |                   # reproducible steps (placeholders, no secrets)
    expected: 200 and no password hash
    actual: 200; keys id,email
    result: pass                 # pass | fail | blocked | skipped
    evidence: |                  # real, trimmed output; required for pass/fail
    defect: D1                   # REQUIRED when result is fail; optional on retest passes
    authz: {expected: allow, actual: allow}   # optional; feeds the auth matrix

defects:
  - id: D1
    title: ...
    severity: high               # critical | high | medium | low | info
    status: open                 # open | retest | fixed | wont_fix
    location: src/file.js:42
    description: ...
    impact: ...
    fix: ...                     # concrete remediation
    retest_evidence: ""          # REQUIRED when status: fixed

remediation:                     # section 9; group by audience
  - audience: Developers
    steps: ["..."]
  - audience: Operators / Product owners
    steps: ["..."]
  - audience: End users
    steps: ["..."]
```

## Computed, not written
Totals, pass rates (executed = pass + fail), coverage, per-type and per-module tables, severity × status table, the auth matrix, the verdict, and the "not executed" list.

## Validation errors you may see
Missing required fields; unknown `inventory`/`actor`/`defect` ids; `fail` without defect; `pass`/`fail` without evidence; `fixed` without `retest_evidence`; `production` without `authorization_note`; invalid enum values.
