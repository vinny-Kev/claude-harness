---
description: Write a structured handoff so a fresh session (optionally on another model) can resume without re-reading this conversation
argument-hint: "[next-model: opus|sonnet|haiku|fable|opusplan] [optional note]"
disable-model-invocation: true
allowed-tools: Read, Write, Bash(git status:*), Bash(git branch:*), Bash(git log:*), Bash(git rev-parse:*), Bash(git diff --stat:*), Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/switch-finalize.sh:*)
---

# /switch — context handoff

Goal: save everything a new session needs, then **stop**. Do not continue the task after the handoff is written.

Arguments: `$ARGUMENTS` (first word = next model if it is one of `opus|sonnet|haiku|fable|opusplan` or a `[1m]` variant; the rest is a note to include).

## Steps

1. **Collect facts cheaply.** If this is a git repo run `git rev-parse --abbrev-ref HEAD`, `git rev-parse --short HEAD`, `git status --short`, `git log --oneline -5`. Do not re-read files just to summarize them; use what you already know from this session.

2. **Write the handoff** to `.claude/handoff/HANDOFF-<YYYYmmdd-HHMMSS>.md` (project root; create the folder if needed) following the structure in `${CLAUDE_PLUGIN_ROOT}/templates/handoff.template.md`. It must cover, in this order:
   - **What we have** (current state, key files and roles, how to run/test)
   - **What we've accomplished** (with how each item was verified)
   - **What still needs to be accomplished**
   - **The overall plan** (checked/unchecked)
   - **Next up**: one concrete immediate action, then the step after it, plus the check that proves it's done
   - Decisions and rationale, open questions, failed attempts not to retry, verification commands

   Rules:
   - Concise: aim for ≤ 150 lines. A fresh session pays tokens to read this; every line must earn its place.
   - Facts from this session only; mark anything unverified as such. No speculation.
   - **No secrets or private data**: replace tokens, passwords, cookies, keys, OTPs and PII with `<REDACTED>`. Never paste `.env` contents.
   - Reference files by path and line instead of pasting code, except for short, critical snippets.
   - If `$ARGUMENTS` contains a note, put it under "Open questions / gotchas" verbatim.

3. **Pick the next model.** Use the model the user named. Otherwise suggest one and give the reason in a few words in the handoff header:
   - routine implementation / well-specified edits → `sonnet`
   - hard design, debugging, security review → `opus`
   - mechanical / bulk / low-risk work → `haiku`
   - plan hard, execute cheap → `opusplan`

4. **Finalize** by running:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/switch-finalize.sh" ".claude/handoff/HANDOFF-<timestamp>.md" "<model>"
   ```
   It scans the file for secret-shaped strings (if any are found, redact them and re-run), marks the handoff as pending so the next session picks it up automatically, and prints the exact switching steps.

5. **Report.** Show the script's switching steps verbatim, then state plainly: *a slash command cannot run `/model` or `/exit` for you, so those are the manual steps above.* Then stop; make no further changes.

## What the user does next (reference)

| Option | Steps |
|---|---|
| **A. Same window** | `/model <model>` then `/clear`. The plugin's `SessionStart` hook loads the pending handoff into the cleared session automatically. |
| **B. New terminal session** | `/exit`, then `bash <plugin>/scripts/switch-launch.sh <model>` (or `claude --model <model> "Read .claude/handoff/LATEST.md and continue from 'Next up'"`). |
| **C. Plugin not installed** | Same as B; the launch prompt tells the new session to read `.claude/handoff/LATEST.md`. |
