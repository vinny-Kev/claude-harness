---
name: architecture
description: >
  Define, register, read and enforce a project's architecture style (MVC,
  layered, hexagonal, Service–Middleware–Aggregate, or custom). Two modes:
  Compose & Register (author a reusable architecture spec and save it to the
  registry) and Read & Enforce (analyze a codebase or load a spec, then plan,
  build or refactor strictly within its layer boundaries). Use when the user
  says "architecture", "layers", "where should this code live", "refactor to
  <style>", "enforce boundaries", "register this architecture", or before
  planning any non-trivial feature in a layered codebase.
metadata:
  tier: free
---

# Architecture skill

Treat the architecture spec as a contract. Code you write or change must satisfy it, and
you must say so explicitly. No cross-layer shortcuts, even when "it's only one line".

## Step 0 — Pick the mode

| User intent | Mode |
|---|---|
| "design / define / create / register an architecture", "make this style reusable" | **A. Compose & Register** |
| "follow / enforce / check / plan / refactor / add feature in this project" | **B. Read & Enforce** |
| Unclear, and no spec exists yet | Ask one question: *compose a new style, or infer one from the code?* |

## Mode A — Compose & Register

Read [references/compose-mode.md](references/compose-mode.md) and
[references/spec-schema.md](references/spec-schema.md), then:

1. **Clarify** only what is missing: project type, language/framework, must-have constraints.
2. **Start from a registered style** if one fits (list `registry/architectures/*.md`), and fork it; otherwise start from [templates/architecture-spec.template.md](templates/architecture-spec.template.md).
3. **Write the spec** with machine-checkable frontmatter (`layers`, `may_depend_on`) and every required section.
4. **Validate**: run `python3 scripts/validate-registry.py` if inside the harness repo; otherwise self-check against the schema checklist.
5. **Register** (ask the user which target):
   - *Project-local (default, private):* `.claude/architectures/<id>.md` in the target project.
   - *Harness registry (public):* `registry/architectures/<id>.md`. Specs there **must be generic**: no private project names, hostnames, or code. See `SECURITY.md`.
6. **Report** the id, layers, dependency rules, and where it was saved.

## Mode B — Read & Enforce

Read [references/enforce-mode.md](references/enforce-mode.md), then:

1. **Resolve the spec**, first match wins:
   1. A spec the user named (registry id or file path).
   2. Project-local: `.claude/architectures/*.md`, `ARCHITECTURE.md`, `docs/architecture*.md`, or a spec referenced from `CLAUDE.md`.
   3. A registered style the codebase clearly follows (`registry/architectures/`).
   4. **Infer** from the code (directory layout, import graph, naming). Present the inferred spec as a *draft*, get confirmation, and offer to register it via Mode A. Never silently treat an inference as authoritative.
2. **Map the code to layers**: produce a layer → paths table. Flag paths that fit no layer.
3. **Baseline drift**: report existing violations *before* changing anything. Do not fix unrelated violations unless asked; list them.
4. **Issue an Architecture Brief** (format in `enforce-mode.md`) before any edit: layers touched, allowed dependencies, files to create or change, and contracts crossing boundaries.
5. **Work inside the brief.** Each edit states its layer. New dependencies must follow `may_depend_on`.
6. **Verify**: re-scan imports/calls for the touched files using the spec's *Detection Hints*, then report *Compliant / Violations introduced / Pre-existing*.

### Planning workflow
Follow [references/planning-and-refactoring.md](references/planning-and-refactoring.md#planning). Output a plan where every step names its layer, files, and dependency direction. For large plans, hand the result to the `project-dam` skill (when installed) for milestone slicing.

### Refactoring workflow
Follow [references/planning-and-refactoring.md](references/planning-and-refactoring.md#refactoring). Never mix refactor with feature work; lock behavior with tests first; move one boundary at a time.

## Hard rules

- **Spec wins over convenience.** If a task seems to require a boundary violation, stop and present options: (a) restructure to comply, (b) propose a spec amendment, (c) log an explicit, user-approved exception. Never violate silently.
- **No invented layers.** Add a layer only through a spec change the user approves.
- **Contracts cross boundaries, internals don't.** Pass DTOs/interfaces across layers, never ORM entities, request objects, or framework types into inner layers.
- **Deviations are recorded.** Approved exceptions go in the spec's `## Anti-patterns` → "Accepted exceptions" or the project's ADRs, with a reason and an owner.
- **Public hygiene.** Anything written to the harness registry is sanitized and generic.
