# Conventions

## Skill anatomy

```
skills/<name>/
├── SKILL.md          # frontmatter + workflow (short, imperative)
├── references/       # deep detail loaded on demand
└── templates/        # fill-in files the skill copies or emits
```

`SKILL.md` frontmatter:

```yaml
---
name: <directory-name>
description: >
  What it does. When to use it (trigger phrases). Keep ≤ 1024 chars.
---
```

Principles: workflow in `SKILL.md`, depth in `references/` (progressive disclosure); every skill states
its **inputs, outputs, hard rules and verification step**; outputs have a fixed, named format
(e.g. *Architecture Brief*) so results are comparable and reviewable.

## Commands

`commands/<name>.md` with `description` frontmatter; body is the prompt. Arguments via `$ARGUMENTS`.

## Hooks

Declared in `hooks/hooks.json`; scripts live in `scripts/` and are invoked with `${CLAUDE_PLUGIN_ROOT}`.

## Naming & output locations

- Skill/command ids: lowercase kebab-case.
- Generated artifacts (handoffs, reports) are written to the **target project** (default `.claude/handoff/`, `qa-output/`), never into this repo; both paths are git-ignored here.

## Redaction standard (all skills that emit reports)

Replace secrets, tokens, cookies, API keys, OTPs, session IDs and real PII with `<REDACTED>` or a
typed placeholder (`<JWT>`, `<EMAIL>`). Show at most the first 4 chars of an identifier when a
reader must correlate it, never a full credential.
