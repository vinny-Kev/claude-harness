# claude-harness

A public, secret-free harness of **skills, commands and workflows for [Claude Code](https://claude.com/claude-code)**. It keeps agents inside architectural boundaries, hardens request/response paths, hands work between sessions cheaply, slices big tasks into safe milestones, and produces evidence-based QA reports.

> **Status: Phase 2 of 5.** Repo hygiene tooling, the **architecture skill + style registry** and the **request/response hardening skill** are done. The other components are scoped in [docs/ROADMAP.md](docs/ROADMAP.md) and land phase by phase.

## Components

| Component | Path | Status |
|---|---|---|
| Architecture skill (Compose & Register / Read & Enforce) | [`skills/architecture/`](skills/architecture/SKILL.md) | ✅ Phase 1 |
| Architecture style registry (MVC, Layered, Hexagonal, Service–Middleware–Aggregate) | [`registry/architectures/`](registry/architectures/README.md) | ✅ Phase 1 |
| Request & response hardening skill | [`skills/req-res-hardening/`](skills/req-res-hardening/SKILL.md) | ✅ Phase 2 |
| `/switch` context handoff command + hooks | `commands/switch.md`, `hooks/`, `scripts/` | ⏳ Phase 3 |
| Project Dam (incremental milestones) | `skills/project-dam/` | ⏳ Phase 4 |
| QA report generator (Markdown + optional `.docx`) | `skills/qa-report/` | ⏳ Phase 5 |

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
├── commands/                slash commands (Phase 3: switch.md)
├── hooks/                   hook configs (Phase 3)
├── docs/                    ROADMAP.md, conventions.md
├── examples/                sanitized, fictional examples only
├── registry/architectures/  reusable architecture specs
├── scripts/                 check-secrets.sh, validate-registry.py, validate-skills.py
└── skills/
    ├── architecture/        SKILL.md, references/, templates/
    └── req-res-hardening/   SKILL.md, references/, templates/, scripts/scan.sh
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
