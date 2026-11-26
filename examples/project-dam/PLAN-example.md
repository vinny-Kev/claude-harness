---
slug: bulk-order-import
title: Bulk order import for acme-shop-api (fictional example)
created: 2026-11-26
mode: gated
architecture: layered
milestones:
  - id: M1
    title: Walking skeleton - POST /orders/import accepts one CSV row and creates one order
    status: done
    size: S
    depends_on: []
    goal: An admin can POST a one-row CSV and the order exists afterwards.
    scope_in:
      - src/presentation/ordersRoutes.js (new route, no validation yet)
      - src/application/importOrders.js (single-row path)
      - src/application/csvMapper.js
    scope_out:
      - multi-row handling, transactions, validation rules, auth hardening, UI
    layers: [presentation, application]
    verify:
      - "npm test -- importOrders → new test 'imports one row' passes, existing tests still pass"
      - "curl -s -o /dev/null -w '%{http_code}' -X POST localhost:3000/orders/import --data-binary @one.csv → 201"
    rollback: Revert the milestone commit; the route is unreferenced elsewhere.
  - id: M2
    title: Import many rows in one all-or-nothing transaction
    status: in_progress
    size: M
    depends_on: [M1]
    goal: Up to 5,000 rows import atomically; one failing row rolls back the whole import.
    scope_in:
      - src/application/importOrders.js
      - src/domain/Order.js (use existing validate() only)
      - unit-of-work interface in src/domain
    scope_out:
      - body-size limit, auth guard, error report format (M3/M4)
      - changing Order invariants
    layers: [application, domain, infrastructure]
    verify:
      - "npm test -- importOrders → 'one bad row rolls back everything' passes"
      - "git diff --stat → only paths listed in scope_in"
    rollback: Revert the commit; M1 single-row path remains.
  - id: M3
    title: Admin-only access, 2 MB body limit and 5,000-row cap
    status: pending
    size: S
    depends_on: [M2]
    goal: Non-admins get 403 and oversized uploads get 413 before parsing.
    scope_in:
      - src/presentation/ordersRoutes.js
      - middleware configuration for this route only
    scope_out:
      - global middleware changes, other routes
    layers: [presentation]
    verify:
      - "request as non-admin → 403"
      - "3 MB body → 413; 5,001 rows → 400"
    rollback: Revert the commit.
  - id: M4
    title: Row-level error report without internals
    status: pending
    size: S
    depends_on: [M3]
    goal: A failed import returns row numbers and messages, never SQL text or stack traces.
    scope_in:
      - src/application/importOrders.js (error mapping)
      - src/presentation/ordersRoutes.js (response shape)
    scope_out:
      - changing the global error handler
    layers: [application, presentation]
    verify:
      - "bad.csv → 400 with {errors:[{row, message}]} and no 'stack' or SQL keywords"
    rollback: Revert the commit.
  - id: M5
    title: Hardening pass on the new endpoint
    status: pending
    size: S
    depends_on: [M4]
    goal: The req-res-hardening skill reports no High or Critical findings for POST /orders/import.
    scope_in:
      - fixes limited to the new route and its use case
    scope_out:
      - findings in unrelated endpoints (go to Backlog)
    verify:
      - "req-res-hardening report for src/presentation/ordersRoutes.js → 0 Critical, 0 High"
    rollback: Revert the fix commits.
---

# Bulk order import — Dam Plan (fictional example)

## Context
Admins need to import up to 5,000 orders from CSV in one request. Follows the `layered` architecture spec.

## Assumptions to confirm
- Duplicate order numbers are rejected, not skipped (affects M2).

## Risks
- Large transactions may lock tables; M2 measures a 5,000-row run.

## Backlog (discovered, out of scope)
- [M1] `GET /orders/:id` lacks an ownership check (see hardening report).

## Progress log
- M1 done 2026-11-26: added route, single-row use case, mapper; evidence: `npm test -- importOrders` → 7 passed.
