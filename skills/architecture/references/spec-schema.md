# Architecture spec schema

An architecture spec is one Markdown file: YAML frontmatter (machine-checkable) plus
required prose sections (human + agent guidance). `scripts/validate-registry.py` enforces this.

## Frontmatter

```yaml
---
id: layered                 # lowercase slug; MUST equal the filename stem
name: Layered (N-tier)
version: 1.0.0              # semver; bump MINOR for added rules, MAJOR for changed boundaries
status: stable              # draft | stable
summary: One sentence.
tags: [backend, web]
layers:                     # ordered outermost → innermost where that makes sense
  - id: presentation
    responsibility: HTTP/UI concerns only; maps requests to application calls.
    may_depend_on: [application]      # the ONLY layers this one may import/call
    owns: [routes, controllers, view-models]   # optional: what lives here
    must_not: [business rules, direct DB access]   # optional: explicit prohibitions
---
```

Required per layer: `id`, `responsibility`, `may_depend_on`.
Optional per layer: `owns`, `must_not`, `paths` (glob hints, e.g. `src/controllers/**`).

Rules the validator enforces:
- every `may_depend_on` entry names an existing layer; no self-dependency;
- the dependency graph is **acyclic**;
- `id` is unique and equals the filename.

> `may_depend_on` is an allow-list. Anything not listed is forbidden. Cross-cutting
> concerns (logging, config) should be modelled as their own low layer or via injected
> interfaces, not exempted ad hoc.

## Required body sections (`##` headings, exact titles)

| Section | Purpose |
|---|---|
| `Intent` | Why this style; when to choose / not choose it. |
| `Layers & Responsibilities` | Each layer: what it does, what it must never do. |
| `Dependency Rules` | The allowed-direction diagram + prose, incl. how contracts cross boundaries. |
| `Conventions` | Naming, file placement, DTO/entity rules, error handling, transactions. |
| `Request / Data Flow` | A numbered happy-path lifecycle through the layers. |
| `Anti-patterns` | Common shortcuts to reject; ends with an `Accepted exceptions` list (may be empty). |
| `Detection Hints` | How to *check* compliance: import patterns, grep/glob rules per layer. |
| `Planning Checklist` | Questions to answer before adding a feature. |
| `Refactoring Playbook` | Ordered moves for migrating a violating codebase toward this style. |

## Writing good specs

- **Be checkable.** "Controllers must not import from `repositories/`" beats "keep controllers thin".
- **Be generic.** Describe the pattern, not a private codebase.
- **Name the escape hatch.** Say how an exception is recorded, so agents don't invent one.
