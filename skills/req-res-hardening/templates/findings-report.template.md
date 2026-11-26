# Request/Response Hardening Report — <project>

- **Date:** <YYYY-MM-DD>
- **Scope:** <paths / services>
- **Method:** static review of code + optional candidate scan; no live attacks
- **Commit reviewed:** <sha>

## 1. Executive summary

| Critical | High | Medium | Low | Info |
|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 |

**Top risks:**
1. …
2. …
3. …

## 2. Endpoint inventory

| Method | Path | Handler | Auth | Validation | Returns raw model? | Notes |
|---|---|---|---|---|---|---|

Global controls: middleware order `…`; body limit `…`; CORS `…`; error handler `…`.

## 3. Findings

<!-- One block per finding, using the format in references/severity-and-format.md -->

### RRH-001: <title>
- Severity: … Confidence: … Category: …
- Location: `file:line`
- Evidence:
- Impact:
- Fix:
- Verify:

## 4. Systemic fixes

| Fix | Closes findings | Effort |
|---|---|---|
| Central input schema + `strict` unknown-key rejection | RRH-… | S |
| Response serializers with allow-lists | RRH-… | M |

## 5. Coverage & assumptions

- Not reviewed: …
- Assumed (unverified): …

> Redaction: no secrets, tokens, cookies, or real PII appear in this report.
