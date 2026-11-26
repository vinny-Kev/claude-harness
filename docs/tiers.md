# Free tier

This repository **is the free tier** of the harness: everything here is MIT-licensed and works out of the box.
Each skill declares its tier in its frontmatter (`metadata: {tier: free}`), and `scripts/validate-skills.py` requires it.

| Item | Type | Always on? |
|---|---|---|
| `architecture` + `registry/architectures/` | skill + style registry | on demand |
| `req-res-hardening` | skill | on demand |
| `project-dam` | skill | on demand |
| `/switch` handoff (`commands/switch.md`) | command + hooks | `SessionStart` hook loads a pending handoff |
| **`knowledge-placement`** | **skill + rule + hooks** | **yes: `SessionStart` injects the rule, `PreToolUse` guards stray docs** |

This repository is self-contained: nothing here depends on any other edition.

## How the free rule is wired
1. **Rule text** is injected into every new session by `hooks/hooks.json` (`SessionStart` -> `scripts/knowledge-hook.sh session-start`).
2. **Enforcement**: `PreToolUse` on `Write|Edit` runs `knowledge.py guard`, which asks you before a stray doc is created in `src/` or with a scratch-style name.
3. **Detail** lives in the skill (`skills/knowledge-placement/`), loaded when the agent is about to write notes.
4. **No plugin?** Copy [`rules/knowledge-placement.md`](../rules/knowledge-placement.md) into your `CLAUDE.md` or `.claude/rules/`.

Turn the guard off with `"guard": "off"` in `.claude/knowledge.json`, or set the mode you want (see [knowledge-placement.md](knowledge-placement.md)).
