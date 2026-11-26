# Using the external knowledge store smoothly

The default store is `~/.local/share/claude-harness/knowledge/<project-key>/`, outside every repo. That keeps notes out of git, but Claude Code treats paths outside the working directory as outside its normal access, so it may prompt. There are three ways to avoid prompts; **you** choose and edit your own settings (the harness never edits them).

Verified against the Claude Code docs (permissions, 2026-11-26); re-check the exact syntax for your version.

## Option 1: additional directory (simple)
In `~/.claude/settings.json` (all projects) or `.claude/settings.local.json` (one repo):

```json
{ "permissions": { "additionalDirectories": ["~/.local/share/claude-harness/knowledge"] } }
```
Files there become readable without prompts; edits follow your permission mode. `/add-dir <path>` or `claude --add-dir <path>` does the same for one session.

## Option 2: explicit allow rules (precise)
```json
{ "permissions": { "allow": [
  "Read(~/.local/share/claude-harness/knowledge/**)",
  "Edit(~/.local/share/claude-harness/knowledge/**)"
] } }
```
Rule paths are gitignore-style: `~/...` is home-relative, `//abs/path` is absolute from the filesystem root, `/path` is relative to the settings file's anchor, `path` or `./path` is relative to the working directory. Use `Edit(...)` to cover Write, and `Read(...)` to cover Glob and Grep. Read/Edit rules also cover recognized shell file commands (`cat`, `head`, `tail`, `sed`, `tee`, redirects) but not indirect access such as `grep -r` from a directory or scripts that open files themselves.

## Option 3: choose a different location
Set `external.root` to anywhere you already trust, such as a folder inside an additional directory you use for notes. Avoid `~/.claude/...`: some `.claude` paths are protected and the docs do not say which subfolders.

## Things to know
- The hard switches `permissions.blockReadsOutsideWorkingDirectories` / `blockWritesOutsideWorkingDirectories` (if you set them) would block this store; allow-list it or use `repo-docs` mode.
- In non-interactive runs (`-p`) or `dontAsk` mode, unapproved access is denied; pre-allow the paths.
- The store is plain files: back it up or sync it like any notes folder. Deleting it only loses notes, never code.
- Worktrees of one repo share a store (the key comes from the shared git dir).
- Windows: paths use the user profile; the scripts are tested on Linux/macOS.

## If you'd rather keep notes in the repo
`knowledge.py init --mode repo-docs --untracked --gitignore` keeps one folder (`docs/codebase/`) git-ignored, with no outside-the-repo permissions needed.
