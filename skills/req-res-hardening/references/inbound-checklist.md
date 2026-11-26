# Inbound (request) checklist

For each endpoint: trace every untrusted input (body, query, path params, headers, cookies, files,
webhook payloads, GraphQL args) to where it is used. Mark each item **Pass / Fail / N/A / Unverified**.

## A. Injection (source → sink)
| Check | Look for | Fix |
|---|---|---|
| SQL injection | String concatenation/template literals/f-strings into raw queries; `.raw()`, `.query()`, `execute()`; dynamic `ORDER BY`/column/table names | Parameterized queries/ORM bindings; allow-list sort/column names |
| NoSQL injection | Request body/query objects passed directly as filters (`{$ne}`, `$where`, `$regex`); `find(req.body)` | Cast to primitives, schema-validate types, strip `$`-prefixed keys, disable `$where` |
| Command injection | `exec`, `spawn` with `shell:true`, `os.system`, `subprocess(..., shell=True)`, backticks, `Runtime.exec` with concatenation | Avoid shell; argument arrays; allow-list inputs |
| Path traversal | `path.join/resolve`, `open`, `sendFile`, `readFile` with user input; `..`, absolute paths, encoded separators; archive extraction (zip-slip) | Resolve then assert prefix is inside base dir; generate server-side filenames |
| XSS (stored/reflected/DOM) | `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `|safe`, unescaped templates, user HTML in emails/PDFs; missing CSP | Context-aware escaping, sanitizer allow-list, CSP |
| SSRF / open redirect | Server fetches a user-supplied URL; `redirect(req.query.next)` | Allow-list hosts/schemes, block private ranges, validate redirect targets |
| Template / expression injection | `eval`, `new Function`, server-side template compile of user input | Never evaluate user input |
| Header / log injection | User input in headers, `Set-Cookie`, log lines (CR/LF) | Strip control chars; structured logging |
| XXE / deserialization | XML parsers with external entities; `pickle`, `yaml.load`, Java/PHP native deserialization of input | Disable entities; safe loaders; schema-based formats |

## B. Payload shape & resource limits
- **Malformed payloads**: invalid JSON/content-type mismatch handled with 4xx (not 500/crash); duplicate keys; wrong types.
- **Oversized bodies**: explicit body-size limit per route class (JSON, urlencoded, multipart, raw); upload size/count limits.
- **Deep nesting / wide arrays**: depth and array-length limits; GraphQL depth/complexity/batch limits; prototype-pollution keys (`__proto__`, `constructor`, `prototype`).
- **Pagination / filters**: max page size, bounded offsets, allow-listed sort and filter fields; regex/`LIKE` input bounded (ReDoS).
- **Zip/image bombs, slow requests**: timeouts, decompression limits, streaming for large files.

## C. Access & abuse controls
- **Authentication** on every non-public route; default-deny middleware ordering (auth runs before handlers and before body-heavy work).
- **Authorization**: object-level checks (IDOR/BOLA: does the handler verify the caller owns/can access `:id`?), function-level (role checks), tenant scoping in every query.
- **Rate limiting / brute force**: login, OTP, password reset, signup, search, expensive endpoints; per-IP and per-account; lockout or backoff.
- **CSRF**: cookie-authenticated state-changing routes need CSRF tokens or `SameSite` + origin checks; no state changes on GET.
- **Origin / CORS**: no `*` with credentials; explicit origin allow-list; reflect-origin bugs; WebSocket origin check.
- **Webhooks**: signature verification, timestamp/replay protection, constant-time compare.
- **Cookies/session**: `HttpOnly`, `Secure`, `SameSite`; rotation on login; expiry.
- **Idempotency & replay**: payment-like or one-time actions protected against double submission.

## D. Type & identifier validation
- IDs validated for type/format/length (UUID/int bounds); non-numeric IDs don't reach the DB layer unchecked.
- Numeric ranges (negative quantities, overflow, NaN/Infinity), string length, enum membership, date parsing, email/URL formats.
- Content-Type enforced; file type validated by content (magic bytes), not only extension/MIME header.
- Unicode normalization and case-folding on identifiers (username/email collisions).

## E. Mass assignment / unexpected fields
- Request body spread into models/updates (`Model.create(req.body)`, `{...req.body}`, `update(**data)`, `fill($request->all())`).
- Writable sensitive fields reachable: `role`, `isAdmin`, `tenantId`, `userId`, `balance`, `verified`, `price`, `status`.
- Validators that allow unknown keys (`additionalProperties`, Zod `.passthrough()`, Joi `allowUnknown`).
- **Fix**: explicit allow-list DTOs per operation; reject (not silently drop) unknown keys where feasible; set ownership/tenant server-side.

## Notes
- A missing control at one layer may be covered at another (gateway, service layer). Verify, then state the assumption; don't assume.
