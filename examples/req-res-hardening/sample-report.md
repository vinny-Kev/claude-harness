# Request/Response Hardening Report — acme-shop-api (fictional demo)

- **Scope:** `examples/req-res-hardening/acme-shop-api/src/`
- **Method:** static review + candidate scan; no live attacks

## 1. Executive summary

| Critical | High | Medium | Low | Info |
|---|---|---|---|---|
| 3 | 3 | 3 | 0 | 0 |

**Top risks:** SQL injection on `/products`; command injection on `/ping`; password hash returned by `/login`.

## 2. Endpoint inventory

| Method | Path | Handler | Auth | Validation | Returns raw model? |
|---|---|---|---|---|---|
| POST | /login | server.js:18 | public | none | **yes** |
| GET | /products | server.js:26 | **none/?** | none | rows as-is |
| GET | /orders/:id | server.js:32 | `req.user` assumed, no middleware seen | none | **yes** |
| PATCH | /me | server.js:38 | `req.user` assumed | none | **yes** |
| GET | /invoices | server.js:44 | none | none | file |
| GET | /ping | server.js:49 | none | none | command output |

Global controls: `cors({origin:true, credentials:true})`, `express.json()` with default limit, no rate limiter, no auth middleware registered.

## 3. Findings

### RRH-001: SQL injection in product search
- Severity: **Critical**  Confidence: Confirmed  Category: Inbound / SQL injection
- Location: `server.js:27`
- Evidence: `db.query("SELECT ... LIKE '%" + req.query.q + "%' ORDER BY " + req.query.sort)`
- Impact: Arbitrary SQL via `q` and `sort`; data theft/modification.
- Fix:
  ```js
  const SORTS = { name: 'name', price: 'price' };
  const order = SORTS[req.query.sort] ?? 'name';
  const rows = await db.query(`SELECT * FROM products WHERE name LIKE ? ORDER BY ${order}`, [`%${req.query.q}%`]);
  ```
- Verify: `q=' OR 1=1 --` returns normal results; `sort=name;DROP` is rejected/defaulted.

### RRH-002: OS command injection in `/ping`
- Severity: **Critical**  Confidence: Confirmed  Category: Inbound / Command injection
- Location: `server.js:50`
- Impact: Remote code execution as the app user.
- Fix: remove the endpoint, or validate `host` against a strict hostname/IP regex and use `execFile('ping', ['-c','1', host])` (no shell), behind admin auth.
- Verify: `host=a;id` → 400.

### RRH-003: Password hash returned on login
- Severity: **Critical**  Confidence: Confirmed  Category: Outbound / Credential leak
- Location: `server.js:22`
- Impact: Offline cracking of the user's password; any stored internal fields also leak.
- Fix: return an allow-listed DTO `{ id, email, displayName }`; mark `passwordHash` as hidden at the model level.
- Verify: response JSON has no `passwordHash`.

### RRH-004: IDOR on `/orders/:id`
- Severity: **High**  Confidence: Confirmed  Category: Inbound / Authorization
- Location: `server.js:33`
- Fix: `Order.findOne({ _id: id, userId: req.user.id })`; return 404 when not found.
- Verify: user A requesting user B's order → 404.

### RRH-005: Mass assignment on `/me`
- Severity: **High**  Confidence: Confirmed  Category: Inbound / Mass assignment
- Location: `server.js:39`
- Impact: Client can set `role`, `tenantId`, `emailVerified`.
- Fix: `const { displayName, phone } = schema.strict().parse(req.body)` and update only those fields.

### RRH-006: Path traversal in invoice download
- Severity: **High**  Confidence: Confirmed  Category: Inbound / Path traversal
- Location: `server.js:45`
- Fix: `const p = path.resolve(base, name); if (!p.startsWith(base + path.sep)) return res.sendStatus(400);` and restrict `name` to `/^[\w-]+\.pdf$/`.

### RRH-007: Stack traces in error responses
- Severity: **Medium**  Confidence: Confirmed  Category: Outbound / Diagnostics leak
- Location: `server.js:55`
- Fix: respond `{ code: 'INTERNAL', requestId }`; log `err` server-side.

### RRH-008: User enumeration and no brute-force protection on `/login`
- Severity: **Medium**  Confidence: Confirmed  Category: Outbound existence leak + Inbound rate limit
- Location: `server.js:19-21`
- Fix: single message "Invalid credentials" with identical status; add per-IP and per-account rate limiting.

### RRH-009: CORS reflects any origin with credentials
- Severity: **Medium**  Confidence: Confirmed  Category: Inbound / Origin control
- Location: `server.js:12`
- Impact: Any website can make credentialed cross-origin requests as the visitor and read responses.
- Fix: `cors({ origin: ['https://shop.example.com'], credentials: true })`.
- Verify: request with `Origin: https://evil.example` receives no `Access-Control-Allow-Origin`.

## 4. Systemic fixes

| Fix | Closes | Effort |
|---|---|---|
| Auth middleware registered globally (default-deny) | RRH-001, 002, 004, 006 | S |
| Strict schema validation (unknown keys rejected) | RRH-001, 005, 006 | M |
| Response serializers with allow-lists | RRH-003 | M |
| Central error handler without internals | RRH-007 | S |
| CORS origin allow-list instead of `origin: true` | RRH-009 | S |

## 5. Coverage & assumptions

- Only `src/server.js` exists in this demo; models and `db` are not shown.
- `req.user` is assumed to be set by middleware that is not registered here.
