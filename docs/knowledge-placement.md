# Knowledge placement (free tier)

Keeps codebase notes in **one predictable place that follows your preference**, and `src/` clean.

## Choose a mode

| Mode | Notes live | Git impact | Pick it when |
|---|---|---|---|
| `external` (default) | `~/.local/share/claude-harness/knowledge/<repo>-<hash>/` | none | you never want agent notes in the repo |
| `repo-docs` | `docs/codebase/` (configurable) | tracked, or git-ignored with `--untracked` | the team should share the notes |
| `colocated` | `NOTES.md` beside the code, index in `docs/codebase/` | tracked | you want module notes next to each module |

```bash
python3 skills/knowledge-placement/scripts/knowledge.py init --mode external                 # this repo
python3 skills/knowledge-placement/scripts/knowledge.py init --mode external --scope user    # every repo
python3 skills/knowledge-placement/scripts/knowledge.py init --mode repo-docs --untracked --gitignore
CLAUDE_KNOWLEDGE_MODE=colocated claude                                                       # one session
```
Schema and precedence: [references/config-schema.md](../skills/knowledge-placement/references/config-schema.md).

## What the agent does
1. Resolves the mode (session-start context or `knowledge.py resolve`). If nothing is configured it asks you **once**, defaulting to `external`.
2. Reads `INDEX.md` in the knowledge directory, updates the matching file **in place**, and registers any new file in the index. No duplicate `*_SUMMARY.md` / `NOTES.md`.
3. Never creates docs in `src/`, `lib/`, `app/`, `internal/`, `cmd/`, `pkg/`, `packages/*/src`, `apps/*/src` unless the mode is `colocated` or you explicitly ask for that file.

## The guard (PreToolUse hook)
Only **new** doc files (`.md`, `.mdx`, `.rst`, `.adoc`) created with Write are checked. It triggers for a doc in a source directory, or a scratch-style name (`*_SUMMARY.md`, `NOTES.md`, `*_REPORT.md`, ...) outside the knowledge location. Existing files, code, edits, `.claude/` and the knowledge directory are never touched.

| `guard` | Effect |
|---|---|
| `ask` (default) | you get a permission prompt with the reason; approving means "yes, I asked for this file here" |
| `deny` | blocked; the agent is told where to write instead |
| `off` | disabled |

Caveats from the Claude Code docs: in `dontAsk` mode and non-interactive `-p` runs, a prompt becomes a denial; hook `ask` behavior under `bypassPermissions` is not documented. The hook fails open on any error.

## External store permissions
Claude Code may prompt for paths outside the repo. Allow the store in **your own** settings; see [external-store.md](../skills/knowledge-placement/references/external-store.md) (`additionalDirectories`, or `Read(...)`/`Edit(...)` rules).

## Commit hygiene
- `external`: nothing to ignore.
- `repo-docs`: decide whether notes are shared. Not shared: `init --mode repo-docs --untracked --gitignore`.
- Keep knowledge changes out of feature commits (separate commit, or none).
- `knowledge.py check` lists stray docs (exit 1 when found); wire it into CI if you want a hard gate. `knowledge.py adopt <file> --execute` moves strays into the store without overwriting.

## Rule without the plugin
Copy [`rules/knowledge-placement.md`](../rules/knowledge-placement.md) into `CLAUDE.md` or `.claude/rules/`.
