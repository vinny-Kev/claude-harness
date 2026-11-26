---
name: req-res-hardening
description: >
  Audit a web/API codebase's request and response paths for security gaps and
  produce prioritized findings with exact file:line locations and concrete
  fixes. Scans endpoints, routes, validators, middleware and serializers.
  Inbound: injection (SQL/NoSQL/command/path/XSS), malformed or oversized
  payloads, deep nesting, missing rate limits/auth/origin/CSRF, ID and type
  validation gaps, mass assignment. Outbound: leaked password hashes, secrets,
  tokens, OTPs, PII, stack traces, DB error codes, cross-tenant and existence
  leaks. Use for "harden the API", "security review of endpoints", "check what
  we return to clients", "mass assignment / IDOR / injection audit".
---

# Request & Response hardening

Read-only audit by default: **report, don't patch**, unless the user asks you to apply fixes.
Every finding must be backed by code you actually read (`file:line`), not by pattern matching alone.

## Workflow

### 1. Scope (one short message, only if unclear)
Target path(s), framework, and whether fixes should be applied after the report. Default: whole repo, report only.

### 2. Discover the attack surface
Follow [references/discovery.md](references/discovery.md). Build an **endpoint inventory**:

| Method | Path | Handler `file:line` | Auth | Validation | Middleware chain | Response shape |
|---|---|---|---|---|---|---|

Also record the global middleware chain (order matters), body-parser limits, CORS config,
error handler, and serializers/DTOs. Mark unknowns as `?`; do not guess.

### 3. Run the candidate scanner (optional accelerator)
```bash
bash skills/req-res-hardening/scripts/scan.sh <path>
```
It prints `file:line [RULE] text` **candidates only**. Each must be triaged: read the code, confirm
data flow from an untrusted source to the sink (or a sensitive field to the response), and discard false positives.

### 4. Inbound checks
Walk every endpoint through [references/inbound-checklist.md](references/inbound-checklist.md).

### 5. Outbound checks
Walk every response path (success, error, list, nested) through
[references/outbound-checklist.md](references/outbound-checklist.md).

### 6. Prioritize and report
Use [references/severity-and-format.md](references/severity-and-format.md) and
[templates/findings-report.template.md](templates/findings-report.template.md). Order: Critical → Low, then by exploitability.

Each finding has: **ID, title, severity, category, location(s) `file:line`, evidence (short snippet), impact, concrete fix (code), and verification step**.

### 7. Fix (only if asked)
Apply one finding per change, smallest fix first, with a test or repro per fix. Prefer central fixes
(shared validator, serializer allow-list, middleware) over per-route patches. Re-run the scanner and re-verify.

## Hard rules

- **Evidence or it's a hypothesis.** Label unconfirmed items `Needs verification` with what to check.
- **Allow-list over deny-list** in every recommendation (fields, origins, content types, sort/filter keys).
- **Never print real secrets** you encounter: redact (`<REDACTED>`), cite `file:line` only. A live-looking credential in the repo is a Critical finding; advise rotation.
- **No attacks on live/production systems.** Static analysis and local/dev test runs only; dynamic probes only with the user's go-ahead.
- **Scope honesty.** State what you did not cover (unread modules, generated code, gateway/WAF-level controls).
- **Public hygiene.** Reports go to the target project (e.g. `.claude/reports/`), never into the harness repo.
