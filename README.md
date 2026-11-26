# claude-harness

A public, secret-free harness of **skills, commands and workflows for [Claude Code](https://claude.com/claude-code)**. It keeps agents inside architectural boundaries, hardens request/response paths, hands work between sessions cheaply, slices big tasks into safe milestones, and produces evidence-based QA reports.

> **Status: Phase 4 of 5, plus the always-on knowledge-placement rule.** Repo hygiene tooling, the **architecture skill + style registry**, the **request/response hardening skill** the **`/switch` handoff command**, **Project Dam** and **knowledge placement** are done. The other components are scoped in [docs/ROADMAP.md](docs/ROADMAP.md) and land phase by phase.

## Components

| Component | Path | Status |
|---|---|---|
| Architecture skill (Compose & Register / Read & Enforce) | [`skills/architecture/`](skills/architecture/SKILL.md) | ✅ Phase 1 |
| Architecture style registry (MVC, Layered, Hexagonal, Service–Middleware–Aggregate) | [`registry/architectures/`](registry/architectures/README.md) | ✅ Phase 1 |
| Request & response hardening skill | [`skills/req-res-hardening/`](skills/req-res-hardening/SKILL.md) | ✅ Phase 2 |
| `/switch` context handoff command + hooks | [`commands/switch.md`](commands/switch.md), [docs/switch.md](docs/switch.md) | ✅ Phase 3 |
| Project Dam (incremental milestones) | [`skills/project-dam/`](skills/project-dam/SKILL.md) | ✅ Phase 4 |
| **Knowledge placement** (rule + guard; keeps notes out of `src/`) | [`skills/knowledge-placement/`](skills/knowledge-placement/SKILL.md), [docs/knowledge-placement.md](docs/knowledge-placement.md) | ✅ Free tier, always on |
| QA report generator (Markdown + optional `.docx`) | `skills/qa-report/` | ⏳ Phase 5 |

> **Free tier:** everything in this repository is free (MIT). See [docs/tiers.md](docs/tiers.md) for what is always on.

## Install

### As a plugin (recommended)

```text
/plugin marketplace add vinny-Kev/claude-harness
/plugin install claude-harness@claude-harness
```

### Manual (skills only)

```bash
git clone https://github.com/vinny-Kev/claude-harness.git
mkdir -p ~/.claude/skills
cp -r claude-harness/skills/architecture ~/.claude/skills/        # user-wide
# or: cp -r claude-harness/skills/architecture <your-project>/.claude/skills/   # per-project
```

When installed manually, copy `registry/architectures/` next to your project (or reference it by path) so the skill can find the registered styles.

## Usage

**Compose & Register** an architecture style:

```text
Use the architecture skill to compose a layered style for our Node/Express API with
separate DTOs and a unit-of-work in the application layer, then register it project-locally.
```

**Read & Enforce** in an existing project:

```text
Use the architecture skill: infer our architecture from this repo, show drift, then plan
the "bulk order import" feature inside its layer boundaries.
```

**Harden** request/response paths:

```text
Use the req-res-hardening skill to audit src/api for injection, mass assignment and data leaks,
and give me prioritized findings with file:line and fixes. Report only, don't change code.
```

A sample report on a fictional vulnerable app is in [`examples/req-res-hardening/`](examples/req-res-hardening/sample-report.md). The optional candidate scanner is `bash skills/req-res-hardening/scripts/scan.sh <path>`.

**Keep codebase notes tidy** (always on with the plugin):

```bash
python3 skills/knowledge-placement/scripts/knowledge.py init --mode external   # notes outside the repo (default)
python3 skills/knowledge-placement/scripts/knowledge.py init --mode repo-docs  # one folder: docs/codebase/
python3 skills/knowledge-placement/scripts/knowledge.py check                  # list stray *_SUMMARY.md / src/ docs
```
The agent checks your placement preference before writing notes, updates existing files in place, and a guard asks before a stray doc is created in `src/`. Modes, config and permissions: [docs/knowledge-placement.md](docs/knowledge-placement.md).

**Hand off** to a fresh session (cheap, no giant re-read):

```text
/switch sonnet
```
then `/model sonnet` and `/clear` in the same window (the plugin hook loads the handoff), or `/exit` and run `scripts/switch-launch.sh sonnet`. A slash command cannot run `/model` or `/exit` itself; see [docs/switch.md](docs/switch.md).

**Dam** a big task into milestones:

```text
Use the project-dam skill to break "bulk order import" into milestones, then implement M1 only.
```

It writes `.claude/dam/<slug>/PLAN.md` in your project (see [`examples/project-dam/`](examples/project-dam/PLAN-example.md)), runs one gated milestone at a time, and defers anything out of scope to a backlog. Helper: `python3 skills/project-dam/scripts/dam.py check|next|status <plan>`.

**Refactor** toward a style:

```text
Use the architecture skill to refactor src/orders toward the `hexagonal` style, one boundary at a time.
```

The skill resolves a spec (named → project-local → registry → inferred draft), emits an **Architecture Brief** before editing, and finishes with an **Architecture Check** listing introduced and pre-existing violations.

## Repository layout

```
claude-harness/
├── .claude-plugin/          plugin.json, marketplace.json
├── .githooks/pre-commit     secret scan + registry validation
├── .github/workflows/       CI: same checks on every push/PR
├── commands/                switch.md
├── rules/                   knowledge-placement.md (paste into CLAUDE.md if you skip the plugin)
├── hooks/                   hooks.json (SessionStart, UserPromptSubmit, PreCompact, PreToolUse)
├── templates/               handoff.template.md
├── docs/                    ROADMAP.md, conventions.md, switch.md, tiers.md, knowledge-placement.md
├── examples/                sanitized, fictional examples only
├── registry/architectures/  reusable architecture specs
├── scripts/                 check-secrets.sh, validate-*.py, switch-*.sh, hook scripts
└── skills/
    ├── architecture/        SKILL.md, references/, templates/
    ├── req-res-hardening/   SKILL.md, references/, templates/, scripts/scan.sh
    ├── project-dam/         SKILL.md, references/, templates/, scripts/dam.py
    └── knowledge-placement/ SKILL.md, references/, scripts/knowledge.py (+ tests)
```

Each skill is `skills/<name>/SKILL.md` (frontmatter `name` = directory, `description` says *when* to use it) with progressive-disclosure detail in `references/` and `templates/`. See [docs/conventions.md](docs/conventions.md).

## Public-repo rules (read before contributing)

This repository is public. **Never commit** secrets, credentials, tokens, cookies, real project/company data, PII, or output from real runs (QA reports, handoffs). Use fictional examples (`acme-shop`, `example.test`) and `<REDACTED>` placeholders. Full policy: [SECURITY.md](SECURITY.md).

Enable the local guard once per clone:

```bash
git config core.hooksPath .githooks
pip install pyyaml
```

Checks you can run any time:

```bash
scripts/check-secrets.sh            # scan the working tree
python3 scripts/validate-registry.py  # validate architecture specs
python3 scripts/validate-skills.py    # validate skill/command frontmatter and links
```

See [CONTRIBUTING.md](CONTRIBUTING.md) to add a skill or an architecture style.

## License

[MIT](LICENSE)
