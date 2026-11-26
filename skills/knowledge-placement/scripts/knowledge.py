#!/usr/bin/env python3
"""Codebase knowledge placement: resolve where notes live, guard stray docs, adopt strays.

  resolve [--for PATH] [--json]       where should knowledge files go for this repo?
  init    --mode M [--scope S]        write config, create the knowledge dir with INDEX.md
  check   [--json] [--warn]           list stray docs in source dirs / stray-named files
  adopt   PATH... [--execute]         move stray files into the knowledge dir (dry run by default)
  guard                               PreToolUse hook: reads hook JSON on stdin, asks/denies stray doc creation
  session-start                       SessionStart hook: prints the placement rule as context

Modes: external (outside the repo, default), repo-docs (one folder inside the repo), colocated (beside code).
Config precedence (later wins): defaults < ~/.claude/knowledge.json < <repo>/.claude/knowledge.json
< <repo>/.claude/knowledge.local.json < $CLAUDE_KNOWLEDGE_MODE. Standard library only; hooks fail open.
"""
import argparse
import copy
import datetime
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MODES = ("external", "repo-docs", "colocated")
GUARDS = ("ask", "deny", "off")
DEFAULT_ROOT = "~/.local/share/claude-harness/knowledge"
DOC_EXTS = {".md", ".mdx", ".rst", ".adoc"}
DEFAULTS = {
    "schema": 1,
    "mode": "external",
    "external": {"root": DEFAULT_ROOT},
    "repo_docs": {"dir": "docs/codebase"},
    "colocated": {"filename": "NOTES.md", "index_dir": "docs/codebase"},
    "source_dirs": ["src", "lib", "app", "internal", "cmd", "pkg", "packages/*/src", "apps/*/src"],
    "stray_patterns": ["NOTES.md", "*_NOTES.md", "*-notes.md", "*SUMMARY*.md", "*_REPORT.md", "*_ANALYSIS.md", "SCRATCH*.md", "CLAUDE_NOTES*.md", "AGENT_NOTES*.md"],
    "allow": [],
    "guard": "ask",
    "index_file": "INDEX.md",
}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "vendor", "coverage", ".claude"}


class KError(Exception):
    pass


# ───────────── repo + config ─────────────
def git(args, cwd):
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def repo_root(cwd):
    return Path(git(["rev-parse", "--show-toplevel"], cwd) or cwd).resolve()


def project_key(cwd):
    """Stable across worktrees: derived from the shared git dir when there is one."""
    common = git(["rev-parse", "--git-common-dir"], cwd)
    base = (Path(cwd) / common).resolve().parent if common else Path(cwd).resolve()
    slug = re.sub(r"[^a-z0-9]+", "-", base.name.lower()).strip("-") or "project"
    return f"{slug}-{hashlib.sha1(str(base).encode()).hexdigest()[:6]}"


def merge(base, new):
    for k, v in new.items():
        base[k] = merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return base


def load_config(cwd):
    root = repo_root(cwd)
    cfg, sources, configured = copy.deepcopy(DEFAULTS), [], False
    for label, path in (("user", Path.home() / ".claude" / "knowledge.json"), ("project", root / ".claude" / "knowledge.json"),
                        ("local", root / ".claude" / "knowledge.local.json")):
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as e:
                raise KError(f"{path}: invalid config: {e}")
            merge(cfg, data)
            sources.append(f"{label}:{path}")
            configured = configured or "mode" in data
    if os.environ.get("CLAUDE_KNOWLEDGE_MODE"):
        cfg["mode"], configured = os.environ["CLAUDE_KNOWLEDGE_MODE"], True
        sources.append("env:CLAUDE_KNOWLEDGE_MODE")
    if cfg["mode"] not in MODES:
        raise KError(f"mode must be one of {MODES}, got {cfg['mode']!r}")
    if cfg["guard"] not in GUARDS:
        raise KError(f"guard must be one of {GUARDS}, got {cfg['guard']!r}")
    return cfg, root, sources, configured


def knowledge_dir(cfg, root, cwd, for_path=None):
    """Directory for the project-wide knowledge index. In colocated mode, `for_path` gives the module directory instead."""
    mode = cfg["mode"]
    if mode == "external":
        return Path(os.path.expandvars(os.path.expanduser(cfg["external"]["root"]))) / project_key(cwd)
    if mode == "repo-docs":
        return root / cfg["repo_docs"]["dir"]
    if for_path:
        p = Path(for_path).resolve()
        return p if p.is_dir() else p.parent
    return root / cfg["colocated"]["index_dir"]


# ───────────── path rules ─────────────
def inside(path, base):
    try:
        Path(path).resolve().relative_to(Path(base).resolve())
        return True
    except ValueError:
        return False


def rel_parts(path, root):
    try:
        return Path(path).resolve().relative_to(root).parts
    except ValueError:
        return None


def in_source_dir(parts, cfg):
    for pat in cfg["source_dirs"]:
        n = pat.count("/") + 1
        if len(parts) > n and fnmatch.fnmatch("/".join(parts[:n]), pat):
            return True
    return False


def is_allowed(rel, cfg):
    name = Path(rel).name
    return any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(name, g) for g in cfg["allow"])


def classify(path, cfg, root, kdir):
    """Return a violation reason or None for a doc-like path."""
    p = Path(path)
    if p.suffix.lower() not in DOC_EXTS:
        return None
    if kdir and inside(p, kdir):
        return None
    parts = rel_parts(p, root)
    if parts is None or any(x in SKIP_DIRS for x in parts[:-1]):
        return None
    rel = "/".join(parts)
    if is_allowed(rel, cfg):
        return None
    name = p.name
    if cfg["mode"] == "colocated" and name == cfg["colocated"]["filename"]:
        return None
    if in_source_dir(parts, cfg):
        return "doc file inside a source directory"
    if any(fnmatch.fnmatch(name.lower(), pat.lower()) for pat in cfg["stray_patterns"]):
        return "scratch/summary-style doc outside the knowledge location"
    return None


def location_text(cfg, kdir):
    if cfg["mode"] == "colocated":
        return f"{kdir}/ for the project index, plus module notes in {cfg['colocated']['filename']} beside the code"
    return f"{kdir}/"


# ───────────── commands ─────────────
def cmd_resolve(a):
    cwd = os.getcwd()
    cfg, root, sources, configured = load_config(cwd)
    kdir = knowledge_dir(cfg, root, cwd, a.for_path)
    out = {"mode": cfg["mode"], "dir": str(kdir), "index": str(kdir / cfg["index_file"]),
           "project_root": str(root), "project_key": project_key(cwd), "configured": configured, "guard": cfg["guard"], "config_sources": sources}
    if a.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"mode:       {out['mode']}{'' if configured else '  (default: not configured yet)'}")
        print(f"directory:  {out['dir']}" + ("  (project index; module notes go beside the code: pass --for PATH)" if cfg["mode"] == "colocated" else ""))
        print(f"index:      {out['index'] or '-'}")
        print(f"guard:      {cfg['guard']}")
        print(f"config:     {', '.join(sources) or 'none (defaults)'}")
    return 0


INDEX_TEMPLATE = """# {name}: codebase knowledge

_Single source of truth for agents. Update in place; do not create parallel summaries elsewhere._

- Updated: {date}

## Purpose
(one paragraph)

## Stack and commands
- Language/runtime:
- Run / test / lint:

## Entry points
-

## Map (module -> notes)
| Module | Path | Notes |
|---|---|---|

## Decisions and conventions
(link to decisions.md when it exists)

## Open questions
-
"""


def cmd_init(a):
    cwd = os.getcwd()
    root = repo_root(cwd)
    if a.mode not in MODES:
        raise KError(f"--mode must be one of {MODES}")
    data = {"schema": 1, "mode": a.mode}
    if a.mode == "external" and a.root:
        data["external"] = {"root": a.root}
    if a.mode == "repo-docs" and a.dir:
        data["repo_docs"] = {"dir": a.dir}
    target = {"user": Path.home() / ".claude" / "knowledge.json", "project": root / ".claude" / "knowledge.json",
              "local": root / ".claude" / "knowledge.local.json"}[a.scope]
    if target.exists() and not a.force:
        raise KError(f"{target} exists; pass --force to overwrite")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"✓ wrote {target}")
    cfg, root, _, _ = load_config(cwd)
    kdir = knowledge_dir(cfg, root, cwd)
    if kdir:
        kdir.mkdir(parents=True, exist_ok=True)
        idx = kdir / cfg["index_file"]
        if not idx.exists():
            idx.write_text(INDEX_TEMPLATE.format(name=root.name, date=datetime.date.today().isoformat()), encoding="utf-8")
        print(f"✓ knowledge directory: {kdir}")
    if a.gitignore:
        gi = root / ".gitignore"
        lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
        want = [".claude/knowledge.local.json"] + ([f"{cfg['repo_docs']['dir'].rstrip('/')}/"] if a.mode == "repo-docs" and a.untracked else [])
        add = [w for w in want if w not in lines]
        if add:
            gi.write_text("\n".join(lines + [""] * bool(lines and lines[-1]) + add) + "\n", encoding="utf-8")
            print(f"✓ added to .gitignore: {', '.join(add)}")
    if a.mode == "external":
        root_s = cfg["external"]["root"]
        print("\nThe external store is outside the repo, so Claude Code may prompt for access. To allow it without prompts, add one of these to your OWN settings.json (this tool does not edit your settings):\n"
              f'  "permissions": {{ "additionalDirectories": ["{root_s}"] }}\n'
              f'  or rules: "Read({root_s}/**)", "Edit({root_s}/**)"\n'
              "(see docs/knowledge-placement.md)")
    return 0


def iter_files(root):
    out = git(["ls-files", "--cached", "--others", "--exclude-standard"], str(root))
    if out is not None:
        for line in out.splitlines():
            yield root / line
        return
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            yield Path(dp) / f


def scan(cfg, root, kdir):
    found = []
    for p in iter_files(root):
        if p.suffix.lower() in DOC_EXTS and p.is_file():
            why = classify(p, cfg, root, kdir)
            if why:
                found.append({"path": str(p.relative_to(root)), "reason": why})
    return found


def cmd_check(a):
    cwd = os.getcwd()
    cfg, root, _, _ = load_config(cwd)
    kdir = knowledge_dir(cfg, root, cwd)
    found = scan(cfg, root, kdir)
    if a.json:
        print(json.dumps({"mode": cfg["mode"], "dir": str(kdir) if kdir else None, "stray": found}, indent=2))
    elif not found:
        print(f"✓ no stray docs (mode: {cfg['mode']})")
    else:
        print(f"✗ {len(found)} stray doc(s) (mode: {cfg['mode']}, knowledge location: {location_text(cfg, kdir)})")
        for f in found:
            print(f"  {f['path']}  ({f['reason']})")
        print("Move them with:  knowledge.py adopt <path> [--execute]   (dry run by default)")
    return 0 if (not found or a.warn) else 1


def cmd_adopt(a):
    cwd = os.getcwd()
    cfg, root, _, _ = load_config(cwd)
    kdir = knowledge_dir(cfg, root, cwd)
    if cfg["mode"] == "colocated":
        raise KError("adopt needs external or repo-docs mode (colocated mode keeps module notes beside the code)")
    dest_dir = kdir / (a.to or "notes")
    for src in a.paths:
        s = Path(src).resolve()
        if not s.is_file():
            raise KError(f"not a file: {src}")
        d = dest_dir / s.name
        if d.exists():
            raise KError(f"{d} already exists; merge by hand instead of overwriting")
        print(f"{'MOVE' if a.execute else 'would move'}: {s} -> {d}")
        if a.execute:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(s), str(d))
    print("Done. Review `git status`; commit the removal yourself." if a.execute else "Dry run. Re-run with --execute to move.")
    return 0


def decision(kind, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": kind, "permissionDecisionReason": reason}}))


def cmd_guard(a):
    try:
        ev = json.load(sys.stdin)
        if ev.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
            return 0
        fp = (ev.get("tool_input") or {}).get("file_path")
        if not fp:
            return 0
        cwd = ev.get("cwd") or os.getcwd()
        cfg, root, _, _ = load_config(cwd)
        if cfg["guard"] == "off" or os.path.exists(fp):  # only creation of new files is guarded
            return 0
        kdir = knowledge_dir(cfg, root, cwd)
        why = classify(fp, cfg, root, kdir)
        if not why:
            return 0
        msg = (f"Knowledge placement ({cfg['mode']} mode): {why}. Codebase notes belong in {location_text(cfg, kdir)}, "
               f"updated in place via its {cfg['index_file']}. Create '{Path(fp).name}' here only if the user explicitly asked for a file at this path.")
        decision("deny" if cfg["guard"] == "deny" else "ask", msg)
    except Exception:  # hooks must never break the session
        return 0
    return 0


def cmd_session_start(a):
    try:
        try:
            cwd = json.load(sys.stdin).get("cwd") or os.getcwd()
        except Exception:
            cwd = os.getcwd()
        cfg, root, sources, configured = load_config(cwd)
        kdir = knowledge_dir(cfg, root, cwd)
        lines = ["## Codebase knowledge placement (claude-harness, free tier)"]
        lines.append(f"- Mode: {cfg['mode']}{'' if configured else ' (default, not configured: ask the user once whether to keep it or choose repo-docs/colocated)'}.")
        lines.append(f"- Knowledge location: {location_text(cfg, kdir)}")
        if kdir and (kdir / cfg["index_file"]).is_file():
            lines.append(f"- Read {kdir / cfg['index_file']} first when you need codebase context.")
        elif kdir:
            lines.append(f"- No {cfg['index_file']} yet: create it there when you first record codebase knowledge.")
        lines.append("- Update existing knowledge files in place; do not create new *_SUMMARY.md/NOTES.md files or put notes in src/ unless the user explicitly asks.")
        lines.append("- Details: use the knowledge-placement skill.")
        print("\n".join(lines))
    except Exception:
        pass
    return 0


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("resolve"); p.add_argument("--for", dest="for_path"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("init"); p.add_argument("--mode", required=True)
    p.add_argument("--scope", choices=("project", "local", "user"), default="project")
    p.add_argument("--root", help="external store root (external mode)"); p.add_argument("--dir", help="docs folder inside the repo (repo-docs mode)")
    p.add_argument("--gitignore", action="store_true", help="add the local config (and untracked docs) to .gitignore")
    p.add_argument("--untracked", action="store_true", help="with repo-docs: also git-ignore the docs folder")
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("check"); p.add_argument("--json", action="store_true"); p.add_argument("--warn", action="store_true", help="exit 0 even when strays exist")
    p = sub.add_parser("adopt"); p.add_argument("paths", nargs="+"); p.add_argument("--to", help="subfolder in the knowledge dir (default notes)"); p.add_argument("--execute", action="store_true")
    sub.add_parser("guard")
    sub.add_parser("session-start")
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    h = {"resolve": cmd_resolve, "init": cmd_init, "check": cmd_check, "adopt": cmd_adopt, "guard": cmd_guard, "session-start": cmd_session_start}
    try:
        return h[a.cmd](a)
    except KError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
