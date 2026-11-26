#!/usr/bin/env python3
"""Validate every skills/*/SKILL.md and commands/*.md.

Checks: frontmatter present; skill `name` equals its directory; `description`
non-empty and <= 1024 chars; `metadata.tier` is free or pro; relative markdown links resolve to real files.
Requires PyYAML. Exit 1 on any error.
"""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\]\((?!https?://|#|mailto:)([^)\s#]+)")


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return yaml.safe_load(m.group(1)) if m else None


def check_links(path, text, errs):
    for target in LINK.findall(text):
        if not (path.parent / target).exists():
            errs.append(f"{path.relative_to(ROOT)}: broken link '{target}'")


def main():
    errs, n = [], 0
    for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
        n += 1
        text = skill.read_text(encoding="utf-8")
        fm = frontmatter(text)
        rel = skill.relative_to(ROOT)
        if not isinstance(fm, dict):
            errs.append(f"{rel}: missing frontmatter")
            continue
        if fm.get("name") != skill.parent.name:
            errs.append(f"{rel}: name '{fm.get('name')}' != directory '{skill.parent.name}'")
        desc = fm.get("description") or ""
        if not desc.strip():
            errs.append(f"{rel}: empty description")
        elif len(desc) > 1024:
            errs.append(f"{rel}: description > 1024 chars")
        tier = (fm.get("metadata") or {}).get("tier") if isinstance(fm.get("metadata"), dict) else None
        if tier not in ("free", "pro"):
            errs.append(f"{rel}: declare metadata.tier: free|pro in the frontmatter")
        check_links(skill, text, errs)
    for cmd in sorted((ROOT / "commands").glob("*.md")):
        n += 1
        text = cmd.read_text(encoding="utf-8")
        if frontmatter(text) is None:
            errs.append(f"{cmd.relative_to(ROOT)}: missing frontmatter")
        check_links(cmd, text, errs)
    if errs:
        print("\n".join(f"✗ {e}" for e in errs))
        sys.exit(1)
    print(f"✓ validate-skills: {n} skill/command files OK")


if __name__ == "__main__":
    main()
