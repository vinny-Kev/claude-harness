# Handoff — <short task title>

- **Created:** <YYYY-MM-DD HH:MM>
- **Project dir:** <absolute path, or `.` if unambiguous>
- **Branch / commit:** <branch @ short-sha, clean|dirty>
- **Prior session model:** <model>   **Suggested next model:** <model + why in a few words>

> A fresh session should be able to continue from this file alone. Do **not** re-read the old
> conversation. Contains no secrets: tokens, passwords, cookies and PII are `<REDACTED>`.

## 1. Goal (one paragraph)
What the user is ultimately trying to achieve, in their terms.

## 2. What we have (current state)
- Repo/system state, key files and their roles (`path` — purpose).
- Environment facts that matter (runtime versions, how to run/test, services needed). No credentials.
- Relevant constraints and user preferences stated in the session.

## 3. What we've accomplished
- [x] <done item> — `path/to/file` (verified by: <test/command/result>)
- [x] …

## 4. Decisions & rationale
| Decision | Why | Alternatives rejected |
|---|---|---|

## 5. Overall plan
1. [x] <step> 
2. [ ] <step>
3. [ ] <step>

## 6. What still needs to be accomplished
- [ ] <item> (blocked by: …)

## 7. Next up (start here)
**Immediate next action:** <one concrete step: file, function, command>
**Then:** <step after that>
**Definition of done for the next step:** <verification>

## 8. Open questions / risks / gotchas
- <unresolved question for the user>
- <thing that failed and why; dead ends not to retry>

## 9. Verification commands
```bash
<test command>
<lint/build command>
```

## 10. Resume prompt (paste into the new session)
```text
Read <handoff path>. Continue from section 7 ("Next up"). Do not redo completed items.
Confirm the current state with `git status` first, then proceed.
```
