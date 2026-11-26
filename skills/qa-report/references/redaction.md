# Redaction

Reports get shared (clients, tickets, email). Treat every evidence block as if it will be public.

## What must never appear
Passwords, API keys, bearer/basic tokens, JWTs, refresh/reset/verification tokens, OTPs, cookies and `Set-Cookie` values, session ids, CSRF tokens, private keys, connection strings with credentials, signed URLs, real emails/phones/addresses/names, payment data, government ids.

## Two layers
1. **Don't capture it.** Use placeholders in `request` (`Authorization: Bearer <TOKEN>`), keep credentials in env vars, use `@example.test` fixture emails.
2. **Automatic backstop.** `build-report.py` runs every string through `scripts/redact.py`. It replaces: `Authorization`/`Cookie`/`Set-Cookie` header values, bearer/basic tokens, JWTs, well-known API key formats, URL credentials and sensitive query params, values of sensitive JSON/`key=value` fields (password, token, secret, apikey, otp, session, csrf, …) and non-example emails, with `<REDACTED>`, `<JWT>`, `<API_KEY>`, `<EMAIL>`, `<PRIVATE_KEY>`.
   Emails at `example.*`, `*.test`, `*.invalid`, `localhost` are kept so actors stay readable.

## Verify before sharing
```bash
python3 skills/qa-report/scripts/redact.py --check qa-output/<date>/QA-REPORT.md
```
Exit 0 means nothing redactable remains. Then skim evidence blocks for what patterns can't catch: names in free text, internal hostnames/IPs, customer ids, business-sensitive values, stack traces with paths.

## Limits
Pattern matching misses novel formats and context-dependent secrets (a random-looking string in prose). When in doubt, replace with a typed placeholder and say what it was (`<ORDER_ID>`).

## Keep proof without the secret
Show *that* a secret leaked without showing it: `passwordHash: <REDACTED> (60 chars, bcrypt format)`.
