---
id: my-style                 # lowercase slug; must equal the filename (my-style.md)
name: My Style
version: 0.1.0
status: draft                # draft | stable
summary: One sentence describing the style.
tags: [backend]
layers:
  - id: edge
    responsibility: Translate external input/output (HTTP, CLI, events) to and from internal calls.
    may_depend_on: [core]
    owns: [routes, controllers]
    must_not: [business rules, direct persistence]
  - id: core
    responsibility: Business rules and orchestration; framework-free.
    may_depend_on: [data]
    must_not: [framework request/response types]
  - id: data
    responsibility: Persistence and external service access behind narrow interfaces.
    may_depend_on: []
---

## Intent

Why this style exists; when to choose it; when not to.

## Layers & Responsibilities

### edge
- Does: …
- Never: …

### core
- Does: …
- Never: …

### data
- Does: …
- Never: …

## Dependency Rules

```
edge → core → data
```

How contracts cross boundaries (DTOs, interfaces, events). Anything not allowed above is forbidden.

## Conventions

- Naming: …
- File placement: …
- Error handling: …
- Transactions: …

## Request / Data Flow

1. …
2. …

## Anti-patterns

- …

### Accepted exceptions

_None._

## Detection Hints

- `edge` files must not import from `data` paths: `grep -rE "from .*/data/" <edge-paths>`
- …

## Planning Checklist

- Which layer owns the new behavior?
- Which contracts cross which boundary?
- …

## Refactoring Playbook

1. …
