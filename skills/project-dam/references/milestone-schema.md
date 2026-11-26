# Milestone schema and decomposition rules

## Fields (in the plan's YAML frontmatter)

| Field | Required | Meaning |
|---|---|---|
| `id` | ✔ | `M1`, `M2`, … in execution order |
| `title` | ✔ | Short, outcome-focused ("Import endpoint rejects invalid rows") |
| `status` | ✔ | `pending` · `in_progress` · `done` · `blocked` · `skipped` |
| `size` | ✔ | `S` (≤ ~2 files, < 1 hr) · `M` (≤ ~5 files, one sitting) · `L` (**must be split before executing**) |
| `depends_on` | ✔ | List of earlier ids (can be empty). Must point backward. |
| `goal` | ✔ | One sentence: the observable behavior or capability delivered |
| `scope_in` | ✔ | What this milestone may change (files, modules, behaviors) |
| `scope_out` | ✔ | Explicitly excluded neighbors, tempting extras, later milestones' work |
| `verify` | ✔ | Concrete, runnable checks, each with expected result |
| `rollback` | ✔ | How to undo it cleanly (revert commit, flag off, drop migration) |
| `layers` | – | Architecture layers touched (when a spec is in use) |
| `files` | – | Expected paths (a guide for the scope guard, not a cage) |
| `notes` | – | Risks, assumptions to confirm |

## Sizing tests (a milestone passes only if all are true)

1. **One behavior**: you can state its goal in one sentence without "and".
2. **Verifiable alone**: a command or observable result proves it, with no later milestone needed.
3. **Shippable**: build and existing tests stay green when it lands.
4. **Revertible**: undoing it doesn't break earlier milestones.
5. **Reviewable**: a human can review the diff in one sitting.

## Ordering strategies (combine)

- **Walking skeleton first**: the thinnest end-to-end path (even hard-coded) so integration risk shows up early.
- **Vertical slices over horizontal layers**: deliver "create order via API with persistence" before "all validators".
- **Risk-first**: put unknowns (new library, migration, performance) before safe CRUD.
- **Seams before swaps**: introduce the interface/flag, then migrate callers, then delete the old path.
- **Hardening last, but not never**: validation, auth, limits, error mapping, and a `req-res-hardening` pass get their own milestones.
- **Tests with the code**: tests belong to the milestone they verify, not a trailing "testing" milestone.

## Splitting an `L`

Split by: (a) data variations (one case → all cases), (b) workflow steps, (c) interface (read path → write path), (d) happy path → failure paths, (e) spike → implementation. Each part must still pass the sizing tests.

## Anti-patterns

- A "Part 2: finish everything" milestone.
- Milestones named after layers ("Do the backend") instead of behaviors.
- `verify: works as expected` (not runnable).
- A final "testing/cleanup" milestone that hides unverified earlier work.
- `scope_out` left empty (it is where sprawl is prevented).

## Good `verify` entries

- `npm test -- orders` → all pass, including new test "rejects row with negative quantity".
- `curl -s -o /dev/null -w '%{http_code}' -X POST localhost:3000/orders/import -d @bad.csv` → `400`.
- `git diff --stat` touches only paths in `scope_in`.
