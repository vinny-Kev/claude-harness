# Rule: codebase knowledge placement (claude-harness, free tier)

Paste this into a project `CLAUDE.md`, or save it as `.claude/rules/knowledge-placement.md`
(or `~/.claude/rules/` for all projects). The plugin's `SessionStart` hook injects the same rule automatically; this
file is for people who prefer an explicit rule or do not install the plugin.

- Before creating or updating any file that records knowledge about this codebase (maps, summaries, module notes, working notes), check the placement preference: run `python3 <harness>/skills/knowledge-placement/scripts/knowledge.py resolve`, or read the preference from `.claude/knowledge.json`. If none is configured, ask the user once, defaulting to **outside the repo**.
- Write only to the resolved knowledge location. Read its `INDEX.md` first, update existing files in place, and register any new file in `INDEX.md`.
- Never create docs, summaries or scratch notes inside `src/` or other source directories, and never create `*_SUMMARY.md`, `NOTES.md`, `*_REPORT.md` or similar files elsewhere in the repo, unless the placement mode is `colocated` or the user explicitly asks for a file at that path.
- Keep generated notes out of normal code commits.
- Product documentation the user wants shipped (README, API docs) goes where the user says.
