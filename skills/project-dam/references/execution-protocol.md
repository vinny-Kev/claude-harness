# Execution protocol

One milestone per cycle. The plan file is the single source of truth for state.

## 0. Preconditions
- Plan passes `dam.py check`.
- Working tree state noted (`git status`); unrelated dirty files are called out, not touched.
- User approved the plan (or chose `mode: auto`).

## 1. Start
```
dam.py next .claude/dam/<slug>/PLAN.md       # prints the milestone to run
```
Edit the plan: set that milestone `status: in_progress`. If `in_progress` already exists, resume it instead of starting another.

## 2. Milestone Brief (emit before editing)

```
MILESTONE BRIEF  M<n> — <title>   [size S|M]
Goal:        <one sentence>
In scope:    <list>
Out of scope:<list>
Files/layers:<paths and architecture layers>
Verify:      <runnable checks with expected results>
Stop if:     <conditions below that apply>
```

## 3. Implement
- Touch only `scope_in`. Keep changes minimal and consistent with existing patterns.
- Found something else (bug, cleanup, missing validation)? Append one line to the plan's **Backlog**: `- [M<n>] <what / where / why>`. Do not fix it now.
- If an architecture spec is active, follow it (issue the Architecture Brief per milestone).

## 4. Verify
Run every `verify` step. Capture the real output (trimmed). Also run the project's existing tests/lint/build so "always shippable" is proven. A failing verify means the milestone is not done: fix within scope or stop.

## 5. Gate
On success, edit the plan: `status: done`, and append to **Progress log**:
`- M<n> done <date>: <what changed, files>, evidence: <command → result>`.
Report to the user:

```
MILESTONE REPORT  M<n> — done | blocked
Changed:   <files>
Evidence:  <command → result>
Backlog added: <n items | none>
Next:      M<n+1> — <title> (needs your go)
```

Then **stop**. Continue only on the user's go (or `mode: auto`).

## Stop conditions (halt and ask)
- An edit would fall outside `scope_in` or inside `scope_out`.
- A verify step fails twice for the same reason, or the cause is unclear.
- An assumption in the plan turned out false (API differs, test absent, dependency missing).
- The milestone is growing beyond its size (> ~5 files, or a second behavior appears).
- A decision with security, data-loss or irreversible consequences is needed.
- The user's instructions conflict with the plan.

## Re-planning
Propose a **plan diff** (add/split/reorder/skip milestone, change scope or verify), explain why in two lines, apply it only after a yes. Never edit the scope of a `done` milestone; add a new one.

## Blocked
Set `status: blocked`, write the reason and what unblocks it under Progress log, and propose either a reorder (next unblocked milestone with satisfied deps) or the question for the user.

## Long sessions
At a gate, if the session is long, suggest `/switch`. The handoff only needs: path of the plan, current milestone, and any unrecorded decisions. Everything else is in the plan file.

## Commits
Only when the user asked. One commit per milestone: `M<n>: <title>`; never bundle milestones.
