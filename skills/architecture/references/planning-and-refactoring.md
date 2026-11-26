# Planning & Refactoring under an architecture spec

## Planning

Use for new features or any change touching more than one file.

1. **Resolve the spec** and emit the *Architecture Brief* shape for the whole feature (see `enforce-mode.md`).
2. **Walk the spec's Planning Checklist** and answer each item in one line.
3. **Decompose by layer**, innermost first (domain/service → persistence → edge), so each step compiles and is testable:

   | # | Step | Layer | Files | Depends on (allowed?) | Test |
   |---|---|---|---|---|---|

4. **Declare contracts** (DTOs, interfaces, events) crossing each boundary before writing code.
5. **List risks**: needs a boundary exception? needs a spec amendment? migrations? Ask before proceeding.
6. **Hand off large plans** to `project-dam` (if installed) for milestone slicing with verification criteria.

A good plan could be implemented by someone who has never seen the repo, and every row can be
checked against `may_depend_on`.

## Refactoring

Use to move an existing codebase toward a spec, or to fix drift.

**Ground rules**
- Refactor **or** add features, never both in one change.
- Behavior-preserving: characterize with tests first. If none exist, write thin characterization tests around the area, or get explicit sign-off to proceed without.
- One boundary per step; each step leaves the build green.

**Procedure**
1. **Baseline**: list violations (`file:line — rule`), group by rule and by layer pair; rank by blast radius (how many files depend on it).
2. **Pick the seam**: the smallest edge where a violation can be removed without touching callers elsewhere.
3. **Apply a standard move** (see the spec's *Refactoring Playbook*): extract interface/port, move logic down a layer, introduce a mapper/DTO, invert a dependency, split a fat module.
4. **Verify**: tests pass; violation count for the targeted rule strictly decreases; no new violations.
5. **Repeat** by rank. Use the strangler pattern (new path beside old, then switch callers) for large moves.
6. **Close**: update the spec if reality legitimately changed (user-approved amendment, version bump); record leftover exceptions.

**Report per step**: rule targeted, files moved/changed, violations before → after, tests run.
