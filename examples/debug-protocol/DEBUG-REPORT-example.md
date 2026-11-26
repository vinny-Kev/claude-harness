# Debug report: order totals off by one cent (fictional example)

- **Date:** 2026-11-26   **Area:** `acme-shop-api` checkout   **Commit:** a1b2c3d (before fix)
- **Severity/impact:** about 1 in 40 orders charged one cent less than the displayed total

## Symptom
Receipt total `39.98` but the payment amount recorded was `39.97` for some carts. Expected: the charged amount equals the displayed total to the cent.

## Reproduction
```text
npm test -- checkout --grep "rounds totals"
```
Reliability before fix: 10/10 runs failed once the failing cart (`qty 3 x 13.33`) was pinned as a fixture. The original report looked flaky (1 in 40) because it depended on which prices were in the cart.

## Root cause
`src/billing/total.js:18` computed `Math.round(price * qty * 100) / 100` per line item, then summed floats. For `13.33 * 3` the intermediate float is `39.989999999999995`, so per-line rounding dropped a cent, while the display code (`src/ui/format.js:7`) rounded the *sum*. The two paths used different rounding points, so they disagreed whenever per-line fractions did not add up. It was not caught earlier because the existing tests used round prices (`10.00`, `20.00`).

## Evidence
- Logged both paths for the failing cart: per-line `13.33, 13.33, 13.32` (sum `39.98`) vs summed-then-rounded `39.99`; the stored amount followed the per-line path.
- Refuted: currency conversion (single currency), tax (tax rate 0), DB column precision (`numeric(10,2)` stores exactly what it is given).

## Fix
- **Change:** compute amounts in integer cents everywhere: `priceCents * qty`, round only at tax/discount steps (`src/billing/total.js:18`), and have the UI format from the same integer.
- **Why this addresses the cause:** one representation and one rounding point, so display and charge cannot diverge.

## Verification
- Regression test `rounds totals consistently for qty 3 x 13.33`: fails before, passes after.
- Original repro: 0/10 failures. Full suite, lint and types pass. Edge cases tried: qty 0, qty 1000, 100% discount, price `0.01`.

## Prevention and follow-ups
- Added a property test: for random carts, displayed total equals charged total.
- Same float pattern in `src/billing/refund.js:44`: **not fixed here**, tracked as a follow-up.

> Fictional example: no real project data.
