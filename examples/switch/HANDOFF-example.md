# Handoff — add bulk order import to acme-shop-api (fictional example)

- **Created:** 2026-11-26 14:10
- **Project dir:** `.`
- **Branch / commit:** `feat/bulk-import @ a1b2c3d`, dirty (2 files)
- **Prior session model:** opus   **Suggested next model:** sonnet — remaining work is well-specified edits

> Contains no secrets. Fictional example for the claude-harness repo.

## 1. Goal
Let admins upload a CSV of up to 5,000 orders and import them in one request, validated and transactional.

## 2. What we have
- `src/application/importOrders.js` — use case (new, draft)
- `src/presentation/ordersRoutes.js` — route `POST /orders/import` (stub)
- `src/domain/Order.js` — invariants (`validate()`); unchanged
- Run tests: `npm test -- orders`. Needs Node 20; no external services.
- Preference: follow the `layered` architecture spec (`.claude/architectures/layered.md`).

## 3. What we've accomplished
- [x] CSV row → `OrderInput` mapper — `src/application/csvMapper.js` (verified: 6 unit tests pass)
- [x] Chose all-or-nothing transaction (see §4)

## 4. Decisions & rationale
| Decision | Why | Alternatives rejected |
|---|---|---|
| One transaction per import | Partial imports are hard to reason about for admins | Per-row commit; chunked commit |
| Max 5,000 rows, 2 MB body | Bounds memory and request time | Streaming parser (later, if needed) |

## 5. Overall plan
1. [x] CSV mapper
2. [ ] `importOrders` use case with validation + transaction
3. [ ] Route + body-size limit + admin-only auth
4. [ ] Error report (row number → message), no stack traces
5. [ ] Tests: happy path, invalid row, oversize, unauthorized

## 6. What still needs to be accomplished
- [ ] Steps 2–5 above
- [ ] Run `req-res-hardening` over the new route before merge

## 7. Next up (start here)
**Immediate next action:** implement `importOrders(rows, unitOfWork)` in `src/application/importOrders.js`; validate every row with `Order.validate()` before opening the transaction.
**Then:** wire `POST /orders/import` in `ordersRoutes.js` with `express.json({ limit: '2mb' })` and the admin guard.
**Done when:** `npm test -- orders` passes including a new "one bad row rolls back everything" test.

## 8. Open questions / risks / gotchas
- Question for user: should duplicate order numbers be skipped or rejected?
- Tried returning per-row errors from the repository layer; it leaked SQL text. Map errors in the use case instead.

## 9. Verification commands
```bash
npm test -- orders
npm run lint
```

## 10. Resume prompt
```text
Read .claude/handoff/LATEST.md. Continue from section 7 ("Next up"). Do not redo completed items.
Confirm the current state with `git status` first, then proceed.
```
