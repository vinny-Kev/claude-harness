#!/usr/bin/env python3
"""Read-only helper for Project Dam plan files (Markdown with YAML frontmatter).

  dam.py check  <plan.md>   validate structure; exit 1 on errors
  dam.py next   <plan.md>   print the single milestone to run next
  dam.py status <plan.md>   progress table

Status is edited by hand in the plan file; this script never writes. Requires PyYAML.
"""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

STATUSES = {"pending", "in_progress", "done", "blocked", "skipped"}
SIZES = {"S", "M", "L"}
REQUIRED = ["id", "title", "status", "size", "depends_on", "goal", "scope_in", "scope_out", "verify", "rollback"]
LISTS = ["depends_on", "scope_in", "scope_out", "verify"]
ID_RE = re.compile(r"^M\d+$")


def load(path):
    text = Path(path).read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        sys.exit(f"{path}: missing YAML frontmatter")
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        sys.exit(f"{path}: invalid YAML: {e}")
    if not isinstance(fm, dict) or not isinstance(fm.get("milestones"), list) or not fm["milestones"]:
        sys.exit(f"{path}: frontmatter needs a non-empty 'milestones' list")
    return fm


def check(fm):
    errs, warns = [], []
    ms = fm["milestones"]
    for key in ("slug", "title", "mode"):
        if not fm.get(key):
            errs.append(f"plan: missing '{key}'")
    if fm.get("mode") not in (None, "gated", "auto"):
        errs.append("plan: mode must be 'gated' or 'auto'")

    seen = []
    for i, m in enumerate(ms):
        label = m.get("id", f"#{i + 1}") if isinstance(m, dict) else f"#{i + 1}"
        if not isinstance(m, dict):
            errs.append(f"{label}: milestone must be a mapping")
            continue
        for k in REQUIRED:
            if k not in m or m[k] in (None, "", []) and k not in ("depends_on",):
                errs.append(f"{label}: missing or empty '{k}'")
        for k in LISTS:
            if k in m and not isinstance(m[k], list):
                errs.append(f"{label}: '{k}' must be a list")
        mid = m.get("id")
        if mid is not None:
            if not ID_RE.match(str(mid)):
                errs.append(f"{label}: id must look like M1, M2, …")
            if mid in seen:
                errs.append(f"{label}: duplicate id")
            seen.append(mid)
        if m.get("status") not in STATUSES:
            errs.append(f"{label}: status must be one of {sorted(STATUSES)}")
        if m.get("size") not in SIZES:
            errs.append(f"{label}: size must be S, M or L")
        elif m["size"] == "L" and m.get("status") in ("pending", "in_progress"):
            errs.append(f"{label}: size L must be split before execution")
        for d in m.get("depends_on") or []:
            if d not in seen[:-1]:
                errs.append(f"{label}: depends_on '{d}' must be an earlier milestone")
        if isinstance(m.get("verify"), list) and any(
            re.fullmatch(r"(works|ok|done|tested)( as expected)?\.?", str(v).strip(), re.I) for v in m["verify"]
        ):
            errs.append(f"{label}: verify must be runnable, not 'works as expected'")
        if isinstance(m.get("scope_in"), list) and len(m["scope_in"]) > 8:
            warns.append(f"{label}: scope_in has {len(m['scope_in'])} items; consider splitting")

    active = [m["id"] for m in ms if isinstance(m, dict) and m.get("status") == "in_progress"]
    if len(active) > 1:
        errs.append(f"more than one milestone in_progress: {active}")
    # Sequential discipline: nothing is done/in_progress after a pending one.
    order = [m for m in ms if isinstance(m, dict)]
    first_open = next((i for i, m in enumerate(order) if m.get("status") in ("pending", "in_progress", "blocked")), None)
    if first_open is not None:
        for m in order[first_open + 1:]:
            if m.get("status") == "done":
                warns.append(f"{m.get('id')}: done while an earlier milestone is still open (out of order)")
    return errs, warns


def next_milestone(fm):
    ms = fm["milestones"]
    status = {m["id"]: m["status"] for m in ms}
    for m in ms:
        if m["status"] == "in_progress":
            return m, "resume (already in progress)"
    for m in ms:
        if m["status"] == "pending" and all(status.get(d) in ("done", "skipped") for d in m.get("depends_on") or []):
            return m, "ready"
    return None, None


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("check", "next", "status"):
        sys.exit(__doc__)
    cmd, path = sys.argv[1], sys.argv[2]
    fm = load(path)

    if cmd == "check":
        errs, warns = check(fm)
        for w in warns:
            print(f"! {w}")
        if errs:
            print("\n".join(f"✗ {e}" for e in errs))
            sys.exit(1)
        print(f"✓ dam check: {len(fm['milestones'])} milestones OK ({fm['slug']})")
    elif cmd == "next":
        m, why = next_milestone(fm)
        if not m:
            blocked = [x["id"] for x in fm["milestones"] if x["status"] == "blocked"]
            print("No runnable milestone." + (f" Blocked: {blocked}" if blocked else " All done."))
            return
        print(f"{m['id']} — {m['title']}  [{m['size']}]  ({why})")
        print(f"Goal: {m['goal']}")
        print("In scope:\n" + "\n".join(f"  - {x}" for x in m["scope_in"]))
        print("Out of scope:\n" + "\n".join(f"  - {x}" for x in m["scope_out"]))
        print("Verify:\n" + "\n".join(f"  - {x}" for x in m["verify"]))
    else:
        icons = {"pending": "·", "in_progress": "▶", "done": "✓", "blocked": "✗", "skipped": "–"}
        done = sum(m["status"] in ("done", "skipped") for m in fm["milestones"])
        print(f"{fm['title']}  ({done}/{len(fm['milestones'])} complete, mode: {fm.get('mode')})")
        for m in fm["milestones"]:
            print(f"  {icons.get(m['status'], '?')} {m['id']:<4} {m['size']}  {m['status']:<11} {m['title']}")


if __name__ == "__main__":
    main()
