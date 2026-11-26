# `/switch` — context handoff

Saves a structured handoff so a fresh session (optionally on a different model) resumes instantly without re-reading a long conversation.

## Use

```text
/switch                 # handoff, recommend a model
/switch sonnet          # handoff, next model = sonnet
/switch opus watch out for the flaky payment test
```

`/switch` writes `.claude/handoff/HANDOFF-<timestamp>.md` in your **project** (not this repo), scans it for secret-shaped text, marks it pending, and prints the steps below. Then it stops.

## Switching: what a plugin can and cannot do

Verified against the Claude Code docs (code.claude.com, checked 2026-11-26):

| Wish | Possible? | What we do instead |
|---|---|---|
| Slash command runs `/model` | **No** (not documented as invokable by commands or the model) | Prints `/model <alias>` for you to type |
| Slash command / hook ends the session | **No** (no documented hook or tool exits the CLI) | Prints `/exit`, or use option A so no exit is needed |
| Load handoff into a new session automatically | **Yes** — `SessionStart` hook, `startup` and `clear` sources | `scripts/session-start-handoff.sh` |
| Start a new session on a chosen model with a prompt | **Yes** — `claude --model <alias> "<prompt>"` | `scripts/switch-launch.sh` |
| Detect "context nearly full" in a hook | **No** (hook input has no usage field; no such event) | Optional statusline helper records usage; a `UserPromptSubmit` hook reads it |

### Option A — same window (no restart)
```text
/model sonnet
/clear
```
`/clear` fires `SessionStart` (source `clear`); the hook injects the pending handoff (once) into the new context.

### Option B — new terminal session
```text
/exit
```
```bash
bash /path/to/claude-harness/scripts/switch-launch.sh sonnet     # from the project directory
bash /path/to/claude-harness/scripts/switch-launch.sh sonnet --print   # show the command only
```
Model aliases: `opus`, `sonnet`, `haiku`, `fable`, `opusplan`, plus `[1m]` variants (e.g. `sonnet[1m]`).

### Without the plugin installed
Copy `commands/switch.md` and `templates/handoff.template.md`, point the command at the template path, and use option B; the launch prompt makes the new session read `.claude/handoff/LATEST.md`.

## Low-context / low-credit nudges (optional, best-effort)

- `PreCompact` hook: when compaction runs (auto or manual), tells the summarizer to keep goal, plan, decisions and next action.
- Context-usage nudge: Claude Code exposes usage only to the **statusline**, so enable `scripts/statusline-context.sh` in your *user* settings:
  ```json
  { "statusLine": { "type": "command", "command": "bash /path/to/claude-harness/scripts/statusline-context.sh" } }
  ```
  It shows `Model · ctx N%` and records N under `$XDG_RUNTIME_DIR` (or `/tmp`) per session; `nudge-low-context.sh` then adds a one-line reminder to run `/switch` at ≥ 70% (`SWITCH_NUDGE_PCT`), at most every 15 min (`SWITCH_NUDGE_COOLDOWN_MIN`).
- Credits/billing are not exposed to hooks; run `/switch` yourself when you are running low.

## Files

| File | Role |
|---|---|
| `commands/switch.md` | The command prompt (user-invocable only) |
| `templates/handoff.template.md` | Handoff structure |
| `scripts/switch-finalize.sh` | Secret scan, mark pending, print steps |
| `scripts/session-start-handoff.sh` | Hook: load pending handoff once (≤ 12k chars, ≤ 72h old) |
| `scripts/switch-launch.sh` | Start a new session on a model with the handoff |
| `scripts/nudge-low-context.sh`, `scripts/statusline-context.sh` | Optional usage nudge |
| `scripts/precompact-preserve.sh` | Hook: guide compaction summaries |
| `hooks/hooks.json` | Hook wiring (`${CLAUDE_PLUGIN_ROOT}`) |
| `scripts/lib/secret-patterns.txt` | Patterns shared with `check-secrets.sh` |

## Privacy

Handoffs live in the target project's `.claude/handoff/` and can contain project details. Keep that folder git-ignored (finalize warns if it isn't). The secret scan is a safety net; review the file if the work was sensitive. Tunables: `SWITCH_HANDOFF_MAX_AGE_MIN`, `SWITCH_HANDOFF_MAX_CHARS`.
