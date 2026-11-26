---
name: project-dam
description: >
  Break a big feature or multi-part task into small, sequential milestones with
  clear scope, boundaries and verification criteria, then implement them one at
  a time without sprawling. Writes a plan file, enforces one milestone in
  flight, a scope guard, and a verified gate before the next milestone. Use for
  "break this down", "plan this feature", "milestones", "don't let it sprawl",
  "implement step by step", "this is too big", or any task likely to touch many
  files or take more than one sitting.
metadata:
  tier: free
---

# Project Dam

A dam holds back the flood: the whole project is the reservoir, and only one small, measured
milestone is released at a time. Each milestone must be independently verifiable and leave the
project working.

Two phases: **Plan** (once, read-only) and **Execute** (one milestone per cycle, gated).

## Phase 1 — Plan

1. **Intake.** Restate the goal, the definition of done for the *whole* effort, and constraints in ≤ 6 lines. Ask only what blocks planning (max 3 questions).
2. **Reconnaissance (read-only).** Read just enough code/docs to find the real seams: entry points, existing patterns, tests, build/test commands. If an architecture spec exists (see the `architecture` skill), load it and assign each milestone its layers.
3. **Decompose** using [references/milestone-schema.md](references/milestone-schema.md): vertical slices, walking skeleton first, risky/unknown parts early, each milestone ≤ one verifiable behavior.
4. **Write the plan file** to the *target project*: `.claude/dam/<slug>/PLAN.md` from [templates/dam-plan.template.md](templates/dam-plan.template.md). Every milestone needs: goal, `scope_in`, `scope_out`, `verify`, `depends_on`, `size`, `rollback`.
5. **Check it:** `python3 <harness>/skills/project-dam/scripts/dam.py check .claude/dam/<slug>/PLAN.md` must pass (unique ids, acyclic sequential deps, required fields, no `L` milestones left unsplit).
6. **Present the plan** as a compact table (id, title, size, verify) and wait for the user's approval or edits. Do not start coding in the same turn unless the user already said to proceed.

## Phase 2 — Execute (one milestone per cycle)

Follow [references/execution-protocol.md](references/execution-protocol.md). In short:

1. `dam.py next <plan>` → the one milestone to run. Set its `status: in_progress` (only one at a time).
2. Emit the **Milestone Brief**: goal, in/out of scope, files/layers, verify steps, stop conditions.
3. Implement **only** what `scope_in` allows. Anything else you notice goes to the plan's *Backlog*, not into the code.
4. **Verify** with the milestone's `verify` steps; show the actual command output or evidence.
5. **Gate:** mark `done` and log the result in the plan, or `blocked` with the reason. Report: *done / evidence / backlog added / next milestone*.
6. **Stop** and wait for the user's go-ahead before the next milestone, unless the plan has `mode: auto` and the user chose it.

## Hard rules

- **One milestone in flight.** Never start M(n+1) before M(n) is verified and recorded.
- **Scope guard.** An edit outside `scope_in` (or inside `scope_out`) is a violation: stop, and either amend the plan with the user or defer to Backlog.
- **Always shippable.** Each milestone leaves build and tests green; if it can't, it is too big. Split it.
- **No silent re-planning.** Changing scope, order or verification means proposing a diff to the plan and getting a yes.
- **Evidence over assertion.** "Done" requires the verify steps run, with their result recorded; never claim from memory.
- **Right-sized.** Aim for ≤ ~5 files and one behavior per milestone; `L` must be split before execution.
- **Don't commit or push unless the user asks.** If they do, one commit per milestone, message referencing the milestone id.
- **Context discipline.** When the session gets long, run the `/switch` command at a gate; the plan file plus the handoff is all a new session needs.
- **Public hygiene.** Plans live in the target project, never in the harness repo, and contain no secrets or private data.

## Works with

- `architecture`: milestone `layers` and the Architecture Brief per milestone.
- `req-res-hardening`: add a final hardening milestone for any new/changed endpoint.
- `qa-report`: the milestones' `verify` steps feed the QA scenarios.
