# Mode B — Read & Enforce

Goal: work inside an existing architecture contract and prove it.

## 1. Resolve the spec

Order: user-named spec → project-local (`.claude/architectures/*.md`, `ARCHITECTURE.md`,
`docs/architecture*.md`, `CLAUDE.md` reference) → matching registered style → inferred draft.

### Inferring from code (when no spec exists)

1. List top-level source dirs and framework markers (`controllers/`, `routes/`, `services/`, `repositories/`, `domain/`, `adapters/`, `ports/`, `middleware/`, `aggregates/`…).
2. Sample imports from each directory to learn the *actual* dependency direction.
3. Pick the closest registered style, then write the *observed* rules, not the aspirational ones.
4. Mark every observed violation as drift. Present the draft spec + drift list; get confirmation; offer to register (Mode A).

## 2. Map code → layers

Produce a table and keep it in the working notes:

| Layer | Paths | Notes |
|---|---|---|
| presentation | `src/routes/**`, `src/controllers/**` | |
| … | … | … |
| *(unmapped)* | `src/utils/**` | Needs a home or an explicit exception |

## 3. Baseline drift (read-only)

Using the spec's *Detection Hints*, list existing violations: `file:line — layer X imports layer Y (not in may_depend_on)`.
Report counts; do not fix unrelated ones unless asked.

## 4. Architecture Brief (emit before editing)

```
ARCHITECTURE BRIEF
Spec:        <id>@<version> (source: registry | project-local | inferred-draft)
Task:        <one line>
Layers touched: <layer, layer>
Allowed deps:   <layer → [allowed layers]> (only for touched layers)
Changes:
  - <path>  [layer]  <create|modify>  — <what>
Contracts crossing boundaries:
  - <DTO/interface name>: <from layer> → <to layer>
Risks / needs approval: <none | list>
```

If *Risks* is not empty, stop and ask before editing.

## 5. Implement inside the brief

- State each file's layer when you create or edit it.
- Put logic in the lowest layer that legitimately owns it.
- When tempted to import across a forbidden edge, **stop**: add a method on the allowed neighbor, introduce an interface/port, or move the logic. Do not tunnel.
- Do not widen the brief silently; if scope grows, re-issue the brief.

## 6. Verify and report

Re-run detection on touched files (and their importers). Report:

```
ARCHITECTURE CHECK
Compliant:            <files>
Violations introduced: <none | file:line — rule>
Pre-existing (untouched): <count, top offenders>
Exceptions requested:  <none | rule, reason, proposed owner>
```

Zero *Violations introduced* is the bar. If you cannot reach it, say so plainly.

## Cross-layer shortcut cheat-sheet

| Tempting shortcut | Do instead |
|---|---|
| Controller queries the DB directly | Call a service/use case; the repository stays behind it |
| Service reads `req`/`res` or HTTP status | Take plain inputs; return results/domain errors; map in the edge layer |
| Repository contains business rules | Move rules to domain/service; repository only persists |
| Domain imports framework/ORM types | Define a port/interface in domain; implement in adapter/infrastructure |
| Returning ORM entities from an API | Map to a response DTO in the edge layer |
| Middleware does business decisions | Middleware handles cross-cutting policy (auth, validation, tracing) only |
