# Config schema

JSON, any of these files (later wins; objects merge, lists replace):

| Order | File | Purpose |
|---|---|---|
| 1 | defaults | built in |
| 2 | `~/.claude/knowledge.json` | your global preference |
| 3 | `<repo>/.claude/knowledge.json` | shared with the team (can be committed) |
| 4 | `<repo>/.claude/knowledge.local.json` | personal override (git-ignore it) |
| 5 | `$CLAUDE_KNOWLEDGE_MODE` | one-off override of `mode` |

```json
{
  "schema": 1,
  "mode": "external",
  "external":  { "root": "~/.local/share/claude-harness/knowledge" },
  "repo_docs": { "dir": "docs/codebase" },
  "colocated": { "filename": "NOTES.md", "index_dir": "docs/codebase" },
  "source_dirs": ["src", "lib", "app", "internal", "cmd", "pkg", "packages/*/src", "apps/*/src"],
  "stray_patterns": ["NOTES.md", "*_NOTES.md", "*-notes.md", "*SUMMARY*.md", "*_REPORT.md", "*_ANALYSIS.md", "SCRATCH*.md", "CLAUDE_NOTES*.md", "AGENT_NOTES*.md"],
  "allow": [],
  "guard": "ask",
  "index_file": "INDEX.md"
}
```

| Key | Meaning |
|---|---|
| `mode` | `external` (outside the repo), `repo-docs` (one folder in the repo), `colocated` (module notes beside code) |
| `external.root` | Parent of per-project folders. The project folder is `<repo-name>-<hash>`, derived from the shared git dir, so **all worktrees of a repo share one folder** |
| `repo_docs.dir` | Folder inside the repo for `repo-docs` mode |
| `colocated.filename` | Allowed note file name beside code (colocated mode) |
| `colocated.index_dir` | Where the project-wide `INDEX.md` lives in colocated mode |
| `source_dirs` | Protected directories (globs on leading path segments). Doc files are not created here unless the mode or the user allows |
| `stray_patterns` | File-name globs (case-insensitive) for scratch/summary docs that must not appear outside the knowledge location |
| `allow` | Globs (on the relative path or file name) that are always fine, e.g. `["docs/adr/**", "CHANGELOG.md"]` |
| `guard` | `ask` prompt the user (default), `deny` block, `off` disabled |
| `index_file` | Name of the map file |

Doc-like means `.md`, `.mdx`, `.rst`, `.adoc`. The guard only looks at **creating new files** via Write; edits to existing files and non-doc files are never touched. Paths under `.git`, `.claude`, `node_modules`, `dist`, `build`, `vendor`, virtualenvs are ignored.

## Quick starts

```bash
knowledge.py init --mode external                          # project default, nothing in the repo
knowledge.py init --mode external --scope user             # global preference
knowledge.py init --mode repo-docs --dir docs/codebase --untracked --gitignore
knowledge.py init --mode colocated --scope local           # only for me
CLAUDE_KNOWLEDGE_MODE=repo-docs claude                     # one session
```
