# Outbound (response) checklist

For each response path (success, list, nested relation, error, redirect, file download, webhook callback, logs/metrics exposed to clients), identify **exactly which fields can leave** and who can receive them.

## A. Confidential data in bodies
| Leak | Look for | Fix |
|---|---|---|
| Password hashes / salts | Returning whole user/account model; ORM `include` of credentials; `toJSON` not overridden | Serializer allow-list; model-level `select: false`/hidden fields |
| Secrets, API keys, tokens | Integration configs, `apiKey`, `refreshToken`, signed URLs, `.env`-derived values in responses or debug endpoints | Never serialize; separate tables; mask (`last4`) |
| OTPs / reset tokens / magic links | OTP or reset token echoed in response "for testing", or returned on "send" endpoints | Return generic ack only; deliver out-of-band |
| Session/JWT internals | Full decoded JWT claims, internal session IDs, refresh tokens in JSON when cookies suffice | Minimal claims; httpOnly cookies |
| PII over-exposure | Email/phone/address/DOB/gov-ID in list views, public profiles, search results, comment authors | Per-audience DTOs; mask; need-to-know fields |
| Internal fields | `isAdmin`, internal IDs, cost/margin, audit fields, soft-delete flags, `__v`, DB column names | Allow-list DTOs |

## B. Error and diagnostics leakage
- Stack traces, file paths, library versions, SQL text, ORM error objects, DB error codes/constraint names in responses.
- `NODE_ENV`/`DEBUG` toggles that enable verbose errors in production; framework debug pages; `/debug`, `/actuator`, `/swagger`, `/graphql` introspection exposed without auth.
- Different error shapes for unexpected exceptions vs validation errors; unhandled rejections returning raw `err`.
- **Fix**: central error handler mapping to `{code, message, requestId}`; log details server-side only.

## C. Cross-tenant and existence leaks
- Queries missing tenant/owner scope in list, detail, export, search, aggregates, and **joined/nested** relations.
- **Enumeration**: `404` vs `403` revealing that an object exists; "email already registered" on signup/reset/login; distinct messages for "user not found" vs "bad password"; timing differences.
- Sequential/guessable IDs combined with weak authorization; counts/totals leaking other tenants' sizes.
- **Fix**: same status/message for "missing" and "forbidden" when existence is sensitive; scope every query by tenant; opaque IDs; constant-time comparisons.

## D. Transport & caching hygiene of responses
- `Cache-Control: no-store` on sensitive responses; no sensitive data in URLs/query strings (logged, cached, referrer-leaked).
- Security headers (`Content-Type` + `nosniff`, CSP, `Referrer-Policy`); correct `Content-Type` on user-supplied downloads; `Content-Disposition` for untrusted files.
- CORS response headers: no wildcard with credentials.
- JSON responses for authenticated data not exposed to JSONP/legacy script-inclusion.

## E. Verification questions per endpoint
1. What is the *complete* set of fields returned? Is it an explicit allow-list?
2. Do nested relations/`include`s widen it?
3. Would a different user/tenant/role see different data from the same call? Is that enforced server-side?
4. What does the caller see on every failure path?
5. Is anything here logged or returned that a client could use to forge identity or guess existence?
