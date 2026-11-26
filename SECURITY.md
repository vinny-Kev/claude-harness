# Security & Data-Hygiene Policy

This is a **public** repository. Everything committed here is world-readable forever.

## Never commit

- Secrets: API keys, tokens, passwords, private keys, cookies, session IDs, JWTs, OTPs, webhook URLs with embedded tokens.
- Credentials files of any kind (`*credentials*`, `.env*`, `*.pem`, `*.key`, …).
- Private project data: real customer/user records, PII, internal hostnames and IPs, real project or company names, proprietary source code, real database dumps.
- Generated artifacts from real runs: QA reports, handoff files, scan outputs. Those belong in the *target* project (or are git-ignored), never here. Only sanitized, fictional **examples** under `examples/` are allowed.

## Rules for examples and registry specs

- Use fictional names (`acme-shop`, `example.test`, `user@example.com`) and RFC 2606 / documentation ranges (`192.0.2.0/24`, `example.com`, `.test`).
- Tokens in examples must be obvious placeholders: `<REDACTED>`, `<TOKEN>`, `eyJ…redacted`.
- Architecture specs in `registry/architectures/` describe *patterns*, never a specific private codebase.

## Enforcement

1. `.gitignore` blocks the common offenders.
2. `scripts/check-secrets.sh` scans the working tree or staged changes for secret-shaped strings and forbidden filenames.
3. `.githooks/pre-commit` runs it on staged files. Enable once per clone:
   ```bash
   git config core.hooksPath .githooks
   ```
4. CI (`.github/workflows/validate.yml`) runs the same scan on every push and PR.

The scanner is a safety net, not a guarantee. Review your own diff before pushing.

## If a secret is committed

1. **Rotate/revoke it immediately** — assume it is compromised.
2. Remove it from history (`git filter-repo`) and force-push; deleting it in a new commit is not enough.
3. Open a private security advisory or contact the maintainers if the leak affects others.

## Reporting a vulnerability in the harness itself

Use GitHub's private vulnerability reporting (Security → Report a vulnerability). Do not open a public issue with exploit details.
