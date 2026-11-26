# Severity and finding format

## Severity

| Level | Meaning | Examples |
|---|---|---|
| **Critical** | Exploitable now without special access; full compromise, mass data exposure, or auth bypass | SQL injection on a public endpoint; password hashes returned by user API; live secret in repo; unauthenticated admin route |
| **High** | Exploitable with ordinary account/low effort; significant data or integrity impact | IDOR on orders; mass assignment of `role`; stored XSS; missing tenant scope; OTP returned in response |
| **Medium** | Needs conditions/chaining, or limited impact | Missing rate limit on login; user enumeration; stack traces in 500 responses; no body-size limit |
| **Low** | Hardening/defense-in-depth | Missing `nosniff`; verbose validation messages; cache headers |
| **Info** | Observation, no direct risk | Inconsistent error shape; dead route |

Raise one level when the endpoint is unauthenticated or internet-facing and handles money, credentials, or PII. Lower one level when a verified compensating control exists (cite it).

## Confidence
`Confirmed` (traced source→sink / field→response), `Likely` (pattern + partial trace), `Needs verification` (state exactly what to check).

## Finding format

```
### <ID>: <title>                      (e.g. RRH-003: Order lookup lacks ownership check)
- Severity: High      Confidence: Confirmed      Category: Inbound / Authorization (IDOR)
- Location: src/routes/orders.js:42 (handler), src/services/orders.js:17 (query)
- Evidence:
    ```js
    const order = await Order.findById(req.params.id);   // no owner/tenant filter
    ```
- Impact: Any authenticated user can read any order by guessing/enumerating IDs.
- Fix:
    ```js
    const order = await Order.findOne({ _id: id, tenantId: req.user.tenantId, userId: req.user.id });
    if (!order) return res.status(404).json({ code: 'NOT_FOUND' });
    ```
- Verify: request /orders/<id of another user> as user A → expect 404.
- References: OWASP API1 (BOLA)
```

Rules: one root cause per finding (list all locations); concrete code, not "sanitize input"; fixes are allow-list based; evidence snippets must not contain real secrets (redact).

## Report ordering
1. Executive summary: counts by severity, top 3 risks, coverage statement.
2. Endpoint inventory (with Auth / Validation / Returns-raw-model flags).
3. Findings, Critical → Low.
4. Systemic fixes (central validators, serializers, middleware order) that remove whole classes of findings.
5. Not covered / assumptions.
