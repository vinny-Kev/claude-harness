#!/usr/bin/env python3
"""Redact secrets, tokens, cookies and PII-shaped strings from text.

  redact.py < in.txt > out.txt        redact stdin to stdout
  redact.py --check FILE [FILE...]    exit 1 if any file still contains redactable text
  from redact import redact           use as a library (returns text, count)

Pattern-based and conservative: it is a safety net, not a guarantee. Always skim evidence
before sharing a report. Hosts ending in example.*/.test/.invalid emails are kept.
"""
import re
import sys

PLACEHOLDER = "<REDACTED>"

_SENSITIVE_KEYS = (
    r"password|passwd|pwd|secret|client_secret|token|access_token|refresh_token|id_token|"
    r"api[_-]?key|apikey|auth|authorization|otp|otp_code|verification_code|reset_token|"
    r"session|session_id|sid|csrf|xsrf|private_key|signature"
)

RULES = [
    # (name, compiled regex, replacement)
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "<PRIVATE_KEY>"),
    ("auth-header", re.compile(r"(?im)^(\s*authorization\s*:\s*)(?:(?:bearer|basic|token|digest)\s+)?\S.*$"), r"\1" + PLACEHOLDER),
    ("cookie-header", re.compile(r"(?im)^(\s*(?:set-)?cookie\s*:\s*).+$"), r"\1" + PLACEHOLDER),
    ("bearer-inline", re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"), r"\1 " + PLACEHOLDER),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}\b"), "<JWT>"),
    ("known-keys", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b|"
                              r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}\b|\bxox[baprs]-[A-Za-z0-9-]{10,}\b|\bAIza[0-9A-Za-z_-]{30,}\b"), "<API_KEY>"),
    ("url-userinfo", re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)[^/\s:@]+:[^/\s@]+@"), r"\1" + PLACEHOLDER + "@"),
    ("url-query", re.compile(r"(?i)([?&](?:" + _SENSITIVE_KEYS + r"|key|code|sig)=)[^&\s\"']+"), r"\1" + PLACEHOLDER),
    # "key": "value"  /  key=value  /  key: value  for sensitive keys (value quoted or bare)
    ("kv-quoted", re.compile(r"(?i)([\"']?\b(?:" + _SENSITIVE_KEYS + r")[\"']?\s*[:=]\s*)([\"'])(?!<REDACTED>)[^\"'\n]*\2"), r"\1\2" + PLACEHOLDER + r"\2"),
    ("kv-bare", re.compile(r"(?i)(\b(?:" + _SENSITIVE_KEYS + r")\s*[=:]\s*)(?![\"'<])[^\s,;&}\]\"']{4,}"), r"\1" + PLACEHOLDER),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@(?!(?:[A-Za-z0-9-]+\.)*(?:example\.[a-z]+|[a-z0-9-]+\.test|invalid|localhost)\b)[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b"), "<EMAIL>"),
]


def redact(text):
    """Return (redacted_text, number_of_substitutions)."""
    total = 0
    for _, rx, rep in RULES:
        text, n = rx.subn(rep, text)
        total += n
    return text, total


def needs_redaction(text):
    """True only if redaction changes the text (already-redacted placeholders don't count)."""
    return redact(text)[0] != text


def main(argv):
    if argv and argv[0] == "--check":
        bad = 0
        for f in argv[1:]:
            with open(f, encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh, 1):
                    if needs_redaction(line):
                        print(f"{f}:{i}: contains secret/PII-shaped text")
                        bad += 1
        if bad:
            sys.exit(1)
        print("✓ redact --check: clean")
        return
    out, n = redact(sys.stdin.read())
    sys.stdout.write(out)
    print(f"[redact] {n} substitution(s)", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
