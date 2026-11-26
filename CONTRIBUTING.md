# Contributing

1. Read [SECURITY.md](SECURITY.md): this repo is public; nothing private goes in.
2. `git config core.hooksPath .githooks && pip install pyyaml`
3. Keep changes small and scoped to one component.

## Add an architecture style
Follow [registry/architectures/README.md](registry/architectures/README.md). Must pass `scripts/validate-registry.py`.

## Add a skill
- `skills/<name>/SKILL.md` with frontmatter `name` (= directory) and a `description` that says **what it does and when to trigger** (≤ 1024 chars).
- Keep `SKILL.md` to the workflow; push depth into `references/` and reusable files into `templates/`. Link them with relative paths.
- Add sanitized, fictional examples under `examples/<skill>/`.
- `python3 scripts/validate-skills.py` must pass.

## Add a command or hook
- Commands: `commands/<name>.md` with frontmatter (`description`, optional `argument-hint`, `allowed-tools`).
- Hooks: `hooks/hooks.json` entries call scripts via `${CLAUDE_PLUGIN_ROOT}`; scripts must be POSIX/bash, never write outside the project, and never log secrets.

## Pull requests
Describe the component, the phase, and how you verified it. CI runs the secret scan and validators.
