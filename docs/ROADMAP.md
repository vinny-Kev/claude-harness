# Roadmap

| Phase | Deliverable | Done when |
|---|---|---|
| **1** ✅ | Repo skeleton, standards, `architecture` skill, 4 registry styles, validators | `validate-registry`, `validate-skills`, `check-secrets` pass |
| **2** ✅ | `skills/req-res-hardening/` | Scans routes/validators/middleware/serializers; prioritized findings with `file:line` and concrete fixes; checklists for inbound + outbound; sample finding report |
| **3** ✅ | `/switch` command, hooks, scripts | See design below; handoff file is self-sufficient in a fresh session |
| **4** ✅ | `skills/project-dam/` | Turns a big task into ordered milestones (scope, boundaries, verification, stop conditions) |
| **5** ✅ | `skills/qa-report/` | Markdown report template + optional `.docx` generation; redaction enforced |

## Always-on rules (free tier)

- **debug-protocol** (on demand): reproduce-first debugging with a stop rule and a flakiness helper. See [`skills/debug-protocol/`](../skills/debug-protocol/SKILL.md).
- **knowledge-placement**: where codebase notes live (external / repo-docs / colocated), update-in-place, stray-doc guard. See [knowledge-placement.md](knowledge-placement.md).

## Phase 2 — req-res-hardening (outline)

- **Discovery**: find endpoints/routes, validators/schemas, middleware chain, serializers/DTOs per framework.
- **Inbound**: SQL/NoSQL/command/path/XSS injection sinks; body size & nesting limits; malformed payload handling; rate limit/auth/origin/CSRF; ID & type validation; mass assignment / unexpected fields.
- **Outbound**: password hashes, secrets/tokens/OTPs, PII, stack traces and DB error codes, cross-tenant and existence leaks (404 vs 403, timing, verbose errors).
- **Output**: findings ranked Critical → Low, each with `file:line`, evidence, exploit sketch, and a concrete patch.

## Phase 3 — `/switch` (built; see [switch.md](switch.md) for verified capabilities)

Known constraints to confirm: a slash command cannot invoke another slash command or built-ins like `/model` / `/exit`.

Planned flow:
1. `/switch [target-model]` runs `commands/switch.md`: Claude writes a structured handoff (`.claude/handoff/HANDOFF-<timestamp>.md`): *what we have, accomplished, remaining, overall plan, next up*, plus files/commands/decisions and a ready-to-paste "resume prompt". No secrets.
2. A `SessionStart` hook detects an unconsumed handoff and injects a pointer so the new session resumes immediately.
3. Final message prints the exact manual steps (`/exit`, then `claude --model <model>` or `/model <model>` and `resume` prompt) and, where available, a launcher script (`scripts/switch.sh`) that starts the new session with the handoff preloaded.
4. Low-context trigger: documented guidance plus an optional `PreCompact`/`UserPromptSubmit` hook that nudges toward `/switch`.

## Phase 4 — project-dam (built)

Milestone schema: id, goal, in-scope, out-of-scope, files/layers touched, dependencies, verification criteria, rollback, "stop here" gate. Integrates with `architecture` for layer placement.

## Phase 5 — qa-report (built)

Sections: Executive Summary & pass/fail metrics · Scope · Environment & actors/fixtures · Methodology · Endpoint/Component Inventory · Auth & Authorization Matrix · Module-by-module success + negative/security scenarios · Security/Access findings (open vs fixed) · User remediation. Markdown template first; `.docx` via a script, with mandatory redaction pass.
