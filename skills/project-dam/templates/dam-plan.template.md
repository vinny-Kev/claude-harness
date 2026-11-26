---
slug: my-feature
title: "<Project or feature title>"
created: 2026-01-01
mode: gated                 # gated = stop after each milestone; auto = continue when verify passes
architecture: ""            # optional: id of the architecture spec in use (e.g. layered)
milestones:
  - id: M1
    title: "<Walking skeleton: thinnest end-to-end path>"
    status: pending
    size: S                 # S | M  (L must be split)
    depends_on: []
    goal: "<One sentence: observable behavior delivered>"
    scope_in:
      - "<what this milestone may change>"
    scope_out:
      - "<tempting neighbors and later work that must NOT change here>"
    layers: []              # optional
    files: []               # optional expected paths
    verify:
      - "<runnable check> → <expected result>"
    rollback: "<how to undo cleanly>"
  - id: M2
    title: "<Next behavior>"
    status: pending
    size: S
    depends_on: [M1]
    goal: "<…>"
    scope_in: ["<…>"]
    scope_out: ["<…>"]
    verify:
      - "<…> → <…>"
    rollback: "<…>"
---

# <Project or feature title> — Dam Plan

## Context
Goal, definition of done for the whole effort, constraints (3–6 lines).

## Assumptions to confirm
- <assumption> (affects M?)

## Risks
- <risk> → mitigation / which milestone addresses it

## Backlog (discovered, out of scope)
<!-- Append: - [M<n>] what / where / why -->

## Progress log
<!-- Append: - M<n> done YYYY-MM-DD: changes, evidence: command → result -->
