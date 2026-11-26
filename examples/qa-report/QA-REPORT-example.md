# QA Verification Report - acme-shop-api v1.4

**Project:** acme-shop-api (fictional)  |  **Date:** 2026-11-26  |  **Tester:** QA agent (Claude) with human reviewer  |  **Build:** commit a1b2c3d (working tree clean)

## 1. Executive Summary

The orders and auth modules behave correctly on all success paths. Authorization testing found one High-severity broken access control defect (any customer can read another customer's order) and one Medium defect (login reveals which emails exist). One earlier High defect (password hash returned by /login) was fixed and retested during this run.

**Overall verdict: FAIL: open defects remain**

| Metric | Value |
|---|---|
| Scenarios total | 15 |
| Passed | 12 |
| Failed | 2 |
| Blocked | 1 |
| Skipped | 0 |
| Pass rate (executed) | 86% |
| Execution coverage | 93% |
| Endpoints/components in inventory | 6 |
| Defects open / fixed | 2 / 1 |

| Scenario type | Total | Pass | Fail | Blocked/Skipped | Pass rate |
|---|---|---|---|---|---|
| success | 5 | 5 | 0 | 0 | 100% |
| negative | 3 | 2 | 0 | 1 | 100% |
| security | 7 | 5 | 2 | 0 | 71% |

| Module | Total | Pass | Fail | Blocked/Skipped | Pass rate |
|---|---|---|---|---|---|
| Auth | 4 | 3 | 1 | 0 | 75% |
| Orders | 9 | 7 | 1 | 1 | 88% |
| Admin | 2 | 2 | 0 | 0 | 100% |

| Severity | Open | Fixed | Won't fix |
|---|---|---|---|
| High | 1 | 1 | 0 |
| Medium | 1 | 0 | 0 |

## 2. Scope

**In scope**

- Auth (login, session), Orders (create, read, list), Admin (user list)
- Request validation and access control on those endpoints

**Out of scope**

- Payment provider integration (stubbed), email delivery, load/performance testing

## 3. Environment & Test Actors/Fixtures

| Item | Value |
|---|---|
| Environment | Local docker-compose |
| Kind | local |
| Target | http://localhost:3000 |
| Build / commit | commit a1b2c3d (working tree clean) |
| Database | PostgreSQL 16, seeded from fixtures/seed.sql |
| Notes | No external services; payment provider stubbed |

**Test actors** (credentials are never recorded in this report)

| ID | Role | Description | Fixture/account (placeholder) |
|---|---|---|---|
| A0 | Anonymous | No credentials | - |
| A1 | Customer (owner of order O-1001) | Regular user | qa_customer1@example.test (password in secret store) |
| A2 | Customer (owner of order O-2001) | Second regular user | qa_customer2@example.test (password in secret store) |
| A3 | Admin | Staff admin | qa_admin@example.test (password in secret store) |

**Fixtures / seed data**

| ID | Description |
|---|---|
| F1 | Orders O-1001 (A1) and O-2001 (A2) seeded with 2 line items each |
| F2 | Product catalog of 25 items |

## 4. Methodology

Execution-based. The API was started locally from the reviewed commit and seeded with fixtures. Each scenario was executed with curl against the running server using the actors below; the observed status code and response body were compared with the expected policy. Negative and security scenarios cover missing/invalid auth, cross-user object access (IDOR), mass assignment, injection probes and oversized input. Evidence is redacted by scripts/redact.py before inclusion. No production systems or real user data were used.

## 5. Endpoint / Component Inventory

| ID | Module | Kind | Name | Method | Path/Location | Auth | Scenarios |
|---|---|---|---|---|---|---|---|
| E1 | Auth | endpoint | Login | POST | /login | public | 4 |
| E2 | Orders | endpoint | Create order | POST | /orders | customer | 3 |
| E3 | Orders | endpoint | Get order | GET | /orders/:id | owner or admin | 4 |
| E4 | Orders | endpoint | List my orders | GET | /orders | customer | 1 |
| E5 | Admin | endpoint | List users | GET | /admin/users | admin | 2 |
| E6 | Orders | endpoint | Update profile | PATCH | /me | customer | 1 |

**Not executed:** E4

## 6. Authentication & Authorization Matrix

| Endpoint | A0 (Anonymous) | A1 (Customer (owner of order O-1001)) | A2 (Customer (owner of order O-2001)) | A3 (Admin) |
|---|---|---|---|---|
| E1 POST /login | - | allow (ok) | - | - |
| E2 POST /orders | deny (ok) | allow (ok) | - | - |
| E3 GET /orders/:id | deny (ok) | allow (ok) | allow (expected deny: FAIL) | allow (ok) |
| E5 GET /admin/users | - | deny (ok) | - | allow (ok) |

Cell = observed outcome for that actor; '(ok)' means it matched the expected policy.

## 7. Module-by-Module Scenarios

### 7.1 Auth

| ID | Type | Scenario | Actor | Expected | Actual | Result |
|---|---|---|---|---|---|---|
| S1 | success | Valid credentials return a session | A1 | 200 with user summary and Set-Cookie; no password hash in body | 200; body has id, email, displayName only | PASS |
| S2 | negative | Wrong password is rejected | A0 | 401 generic message | 401 {"error":"Invalid credentials"} | PASS |
| S3 | security | Unknown email returns the same response as wrong password | A0 | 401 identical to S2 (no account enumeration) | 404 {"error":"No such user"} | FAIL → D2 |
| S4 | security | Password hash is not returned by login (retest of D1) | A1 | No passwordHash or internal fields | Keys are id, email, displayName | PASS → D1 |

#### S2 — Wrong password is rejected [PASS]

Request / steps:

```
POST /login
{"email":"qa_customer1@example.test","password":"<REDACTED>"}
```

Evidence (redacted):

```
HTTP/1.1 401 Unauthorized
{"error":"Invalid credentials"}
```

#### S3 — Unknown email returns the same response as wrong password [FAIL]

Request / steps:

```
POST /login
{"email":"<EMAIL>","password":"<REDACTED>"}
```

Evidence (redacted):

```
HTTP/1.1 404 Not Found
{"error":"No such user"}
```

#### S4 — Password hash is not returned by login (retest of D1) [PASS]

Request / steps:

```
POST /login with valid credentials, inspect response keys
```

Evidence (redacted):

```
keys: ["id","email","displayName"]
```

### 7.2 Orders

| ID | Type | Scenario | Actor | Expected | Actual | Result |
|---|---|---|---|---|---|---|
| S5 | success | Customer creates an order | A1 | 201 with order id and total | 201 {"id":"O-1003","total":"39.98"} | PASS |
| S6 | security | Anonymous cannot create an order | A0 | 401 | 401 | PASS |
| S7 | negative | Negative quantity is rejected | A1 | 400 validation error naming the field | 400 {"error":"items[0].qty must be >= 1"} | PASS |
| S8 | success | Owner reads own order | A1 | 200 | 200 | PASS |
| S9 | security | Customer cannot read another customer's order (IDOR) | A2 | 404 (or 403); order not disclosed | 200 with full order of A1 including shipping address | FAIL → D3 |
| S10 | success | Admin reads any order | A3 | 200 | 200 | PASS |
| S11 | security | Anonymous cannot read an order | A0 | 401 | 401 | PASS |
| S12 | security | Mass assignment of role is ignored | A1 | 200 and role unchanged | 200; subsequent GET /admin/users as A1 returns 403 | PASS |
| S15 | negative | Oversized request body is rejected | A1 | 413 before parsing | Not executed; local proxy limit prevented the test | BLOCKED |

#### S6 — Anonymous cannot create an order [PASS]

Request / steps:

```
POST /orders without cookie
```

Evidence (redacted):

```
HTTP/1.1 401 Unauthorized
```

#### S7 — Negative quantity is rejected [PASS]

Request / steps:

```
POST /orders
{"items":[{"sku":"SKU-1","qty":-5}]}
```

Evidence (redacted):

```
HTTP/1.1 400 Bad Request
{"error":"items[0].qty must be >= 1"}
```

#### S9 — Customer cannot read another customer's order (IDOR) [FAIL]

Request / steps:

```
GET /orders/O-1001
Cookie: <REDACTED>
```

Evidence (redacted):

```
HTTP/1.1 200 OK
{"id":"O-1001","userId":101,"shipping":{"name":"QA One","email":"<EMAIL>"}}
```

#### S11 — Anonymous cannot read an order [PASS]

Request / steps:

```
GET /orders/O-1001
```

Evidence (redacted):

```
HTTP/1.1 401 Unauthorized
```

#### S12 — Mass assignment of role is ignored [PASS]

Request / steps:

```
PATCH /me
{"displayName":"QA One","role":"admin"}
```

Evidence (redacted):

```
HTTP/1.1 200 OK
{"id":101,"displayName":"QA One"}
```

#### S15 — Oversized request body is rejected [BLOCKED]

Request / steps:

```
POST /orders with a 5 MB JSON body
```

### 7.3 Admin

| ID | Type | Scenario | Actor | Expected | Actual | Result |
|---|---|---|---|---|---|---|
| S13 | security | Customer cannot list users | A1 | 403 | 403 | PASS |
| S14 | success | Admin lists users without credential fields | A3 | 200 list with id, email, role only | 200; keys id,email,role | PASS |

#### S13 — Customer cannot list users [PASS]

Request / steps:

```
GET /admin/users as A1
```

Evidence (redacted):

```
HTTP/1.1 403 Forbidden
```

## 8. Security / Access-Control & Defect Findings

### 8.1 Open defects

#### D3 — Any customer can read any order (IDOR) [HIGH / OPEN]

- Location: src/routes/orders.js:33
- Found by: S9
- Description: GET /orders/:id loads the order by id without checking that it belongs to the caller.
- Impact: Customers can read other customers' orders, shipping addresses and emails.
- Fix: Query with the owner filter (id AND userId = caller) unless the caller is admin; return 404 when not found.

#### D2 — Login reveals whether an email is registered [MEDIUM / OPEN]

- Location: src/routes/auth.js:19-21
- Found by: S3
- Description: Unknown email returns 404 "No such user"; wrong password returns 401 "Invalid credentials".
- Impact: Attackers can enumerate registered emails and target them with credential stuffing.
- Fix: Return the same 401 and message for both cases and add per-IP and per-account rate limiting.

### 8.2 Fixed and retested

#### D1 — Login response included the password hash [HIGH / FIXED]

- Location: src/routes/auth.js:22
- Found by: S4
- Description: POST /login returned the whole user model including passwordHash.
- Impact: Offline cracking of the user's password.
- Fix: Return an allow-listed DTO (id, email, displayName); hide passwordHash at model level.
- Retest evidence: S4 re-run on commit a1b2c3d: response keys are id, email, displayName.

## 9. User Remediation Guidance

### Developers

- Fix D3 first: add an owner filter to the order lookup and add regression test S9 to the suite.
- Fix D2: unify the login failure response and add rate limiting; re-run S2 and S3.
- Add a body-size limit (2 MB) and re-run S15 on an environment without the proxy cap.

### Operators / Product owners

- Do not release v1.4 to customers until D3 is fixed and retested.
- If v1.3 has the same order lookup, review access logs for cross-customer reads and notify affected customers per your policy.

### End users

- No action needed yet. If a data exposure is confirmed in production, you will be notified with guidance (e.g. watch for phishing using your order details).

_Report generated by claude-harness qa-report. Redactions applied: 5._
