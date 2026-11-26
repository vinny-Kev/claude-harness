---
name: knowledge-placement
description: >
  Decide where codebase knowledge lives and keep it tidy: check the user's
  placement preference (external store outside the repo, one central docs folder
  in the repo, or colocated beside the code) before creating or updating any
  codebase map, architecture summary, module note or working note; update the
  existing file in place instead of creating duplicates; keep src/ and normal
  code commits clean. Use whenever you are about to write notes, summaries or
  docs about the codebase, when asked to "document the codebase", "write a
  summary", "remember this about the repo", "set where notes go", or "clean up
  stray notes/markdown files".
metadata:
  tier: free
---

# Knowledge placement

Agents tend to scatter `*_SUMMARY.md`, `NOTES.md` and architecture write-ups across the repo, including
`src/`. This rule keeps codebase knowledge in **one predictable place that follows the user's preference**.

> Free-tier rule: loaded by the `SessionStart` hook and enforced by a `PreToolUse` guard in this plugin.

## Step 1: resolve the preference (always first)

```bash
python3 <harness>/skills/knowledge-placement/scripts/knowledge.py resolve [--for path/to/file]
```
Or read the "Codebase knowledge placement" block the session-start hook already printed. It gives the **mode**, the **knowledge directory** and whether the preference is **configured**.

| Mode | Where notes go | Repo impact |
|---|---|---|
| `external` (default) | `~/.local/share/claude-harness/knowledge/<project-key>/` (outside the repo) | None: never in git |
| `repo-docs` | one folder in the repo, default `docs/codebase/` | Tracked unless the user git-ignores it |
| `colocated` | module notes in `NOTES.md` beside the code; project index in `docs/codebase/` | Only when the user chose it or asked for a file there |

Config files (later wins): `~/.claude/knowledge.json` (global) < `<repo>/.claude/knowledge.json` (shared) < `<repo>/.claude/knowledge.local.json` (personal, git-ignored) < `$CLAUDE_KNOWLEDGE_MODE`. Schema: [references/config-schema.md](references/config-schema.md).

### If not configured
Ask **once**: *"Where should I keep codebase notes: outside the repo (default), in `docs/codebase/`, or beside the code?"* and whether it applies to this repo or globally. Then run `knowledge.py init --mode <m> [--scope project|local|user]`. If the user doesn't answer or says "whatever", use `external` and say so. Never ask again for the same repo.

## Step 2: write into the single source of truth

1. **Read `INDEX.md`** in the knowledge directory first (it is the map of everything else).
2. **Search before creating**: `ls`/grep the knowledge directory for the topic. If a file covers it, **update that file in place** and bump its `Updated:` line.
3. **Create a new file only if no existing one fits**, using the layout below, and **add it to the INDEX map** in the same edit.
4. Keep files short and factual: what/where/why, with `path:line` pointers; no pasted code dumps; no secrets or personal data.

```
<knowledge dir>/
├── INDEX.md          purpose, stack/commands, entry points, map (module → notes), open questions
├── architecture.md   layers/modules and the rules (link the architecture spec if one exists)
├── decisions.md      append-only decision log (date, decision, why)
├── modules/<name>.md one per module/package
└── notes/<topic>.md  working notes; prune when stale
```

## Step 3: keep src/ and commits clean

- **Never create docs, summaries or scratch notes inside source directories** (`src/`, `lib/`, `app/`, `internal/`, `cmd/`, `pkg/`, `packages/*/src`, `apps/*/src`) unless the mode is `colocated` or the user explicitly asks for a file at that path.
- **Never create** `*_SUMMARY.md`, `*_NOTES.md`, `NOTES.md`, `*_REPORT.md`, `*_ANALYSIS.md`, `SCRATCH*.md` outside the knowledge location.
- The `PreToolUse` guard asks the user to confirm when you try. A prompt is the user's explicit decision: if they approve, proceed; if they decline, put the content in the knowledge directory instead.
- **Product documentation is different**: a README, API docs or ADRs the user wants shipped go where the user says (usually `docs/`), not in the knowledge store.
- Using `external` mode needs no `.gitignore`. For `repo-docs` mode, ask whether notes should be tracked; if not, `init --mode repo-docs --untracked --gitignore`. Keep knowledge changes out of feature commits: commit them separately, or not at all.

## Step 4: clean up existing sprawl (only when asked)

```bash
python3 <harness>/skills/knowledge-placement/scripts/knowledge.py check            # list strays
python3 <harness>/skills/knowledge-placement/scripts/knowledge.py adopt <file>...  # dry run
python3 <harness>/skills/knowledge-placement/scripts/knowledge.py adopt <file>... --execute
```
`adopt` moves files into `notes/` in the knowledge directory (never overwrites, never deletes content). Review `git status` afterward; the user commits the removals. Merge duplicate summaries into the right file by hand.

## External store access
The external store is outside the repo, so Claude Code may prompt for access. Tell the user once how to allow it (they edit their own settings; do not edit settings yourself): [references/external-store.md](references/external-store.md). Until allowed, accept the prompts normally.

## Hard rules
- **Check the preference before creating or updating any knowledge file.**
- **One home, no duplicates**: update in place; register new files in `INDEX.md`.
- **Respect the mode**: external means nothing in the repo; repo-docs means one folder; colocated means only `NOTES.md` beside the code.
- **Explicit request wins**: when the user asks for a file at a specific path, create it there, and mention that it bypasses their placement setting.
- **No secrets, tokens or personal data** in knowledge files.
- **Don't change the user's settings or `.gitignore`** without being asked (the `init --gitignore` flag exists for when they say yes).
