#!/usr/bin/env python3
"""Tests for knowledge.py. Run: python3 skills/knowledge-placement/scripts/test_knowledge.py"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "knowledge.py"


class Env:
    """A throwaway git repo plus an isolated HOME."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.home, self.repo = t / "home", t / "repo"
        self.home.mkdir()
        (self.repo / "src" / "orders").mkdir(parents=True)
        (self.repo / "docs").mkdir()
        for f in ("src/orders/a.js", "README.md", "docs/guide.md"):
            (self.repo / f).write_text("x")
        (self.repo / "src/orders/OLD_NOTES.md").write_text("old")
        (self.repo / "TEAM_SUMMARY.md").write_text("old")
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.test", "commit", "-qm", "init")

    def git(self, *a, cwd=None):
        return subprocess.run(["git", *a], cwd=cwd or self.repo, check=True, capture_output=True)

    def run(self, *args, stdin=None, env=None, cwd=None):
        e = {**os.environ, "HOME": str(self.home)}
        e.pop("CLAUDE_KNOWLEDGE_MODE", None)
        e.update(env or {})
        return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, text=True, cwd=cwd or self.repo, env=e)

    def guard(self, tool, path, **kw):
        ev = json.dumps({"tool_name": tool, "cwd": str(self.repo), "tool_input": {"file_path": str(path)}})
        r = self.run("guard", stdin=ev, **kw)
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else None

    def write_cfg(self, name, data):
        p = self.repo / ".claude" / name
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(data))

    def close(self):
        self.tmp.cleanup()


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)

    def resolve(self, **kw):
        return json.loads(self.e.run("resolve", "--json", **kw).stdout)

    def test_default_is_external_outside_repo(self):
        r = self.resolve()
        self.assertEqual(r["mode"], "external")
        self.assertFalse(r["configured"])
        self.assertTrue(r["dir"].startswith(str(self.e.home)))
        self.assertFalse(Path(r["dir"]).is_relative_to(self.e.repo))

    def test_config_precedence_and_env(self):
        (self.e.home / ".claude").mkdir()
        (self.e.home / ".claude" / "knowledge.json").write_text(json.dumps({"mode": "repo-docs"}))
        self.assertEqual(self.resolve()["mode"], "repo-docs")
        self.e.write_cfg("knowledge.json", {"mode": "external"})
        self.assertEqual(self.resolve()["mode"], "external")
        self.e.write_cfg("knowledge.local.json", {"mode": "colocated"})
        self.assertEqual(self.resolve()["mode"], "colocated")
        self.assertEqual(self.resolve(env={"CLAUDE_KNOWLEDGE_MODE": "repo-docs"})["mode"], "repo-docs")
        self.assertTrue(self.resolve()["configured"])

    def test_bad_config_errors_for_resolve_but_guard_fails_open(self):
        self.e.write_cfg("knowledge.json", {"mode": "nowhere"})
        self.assertNotEqual(self.e.run("resolve").returncode, 0)
        self.assertIsNone(self.e.guard("Write", self.e.repo / "src" / "NEW.md"))

    def test_worktrees_share_one_project_key(self):
        wt = self.e.repo.parent / "wt"
        self.e.git("worktree", "add", "-q", str(wt))
        self.assertEqual(self.resolve()["project_key"], self.resolve(cwd=wt)["project_key"])

    def test_guard_decisions_default_mode(self):
        r = self.e.repo
        self.assertEqual(self.e.guard("Write", r / "src/orders/SUMMARY.md"), "ask")      # doc in source dir
        self.assertEqual(self.e.guard("Write", r / "ARCH_SUMMARY.md"), "ask")            # stray name at root
        self.assertIsNone(self.e.guard("Write", r / "src/orders/b.js"))                   # code file
        self.assertIsNone(self.e.guard("Write", r / "docs/new-guide.md"))                 # normal docs
        self.assertIsNone(self.e.guard("Write", r / "README.md"))                         # existing file
        self.assertIsNone(self.e.guard("Edit", r / "src/orders/OLD_NOTES.md"))            # edit of existing
        self.assertIsNone(self.e.guard("Read", r / "src/x.md"))                           # other tools
        kdir = self.resolve()["dir"]
        self.assertIsNone(self.e.guard("Write", Path(kdir) / "modules" / "orders.md"))    # knowledge dir
        self.assertIsNone(self.e.guard("Write", r / ".claude" / "dam" / "PLAN.md"))       # .claude ignored

    def test_guard_modes_and_allow_list(self):
        r = self.e.repo
        self.e.write_cfg("knowledge.json", {"mode": "repo-docs", "guard": "deny", "allow": ["docs/adr/**", "CHANGELOG.md"]})
        self.assertEqual(self.e.guard("Write", r / "src/orders/X.md"), "deny")
        self.assertIsNone(self.e.guard("Write", r / "docs/codebase/modules/o.md"))
        self.assertIsNone(self.e.guard("Write", r / "src/CHANGELOG.md"))
        self.e.write_cfg("knowledge.json", {"mode": "repo-docs", "guard": "off"})
        self.assertIsNone(self.e.guard("Write", r / "src/orders/X.md"))

    def test_colocated_allows_only_its_notes_file(self):
        r = self.e.repo
        self.e.write_cfg("knowledge.json", {"mode": "colocated"})
        self.assertIsNone(self.e.guard("Write", r / "src/orders/NOTES.md"))
        self.assertEqual(self.e.guard("Write", r / "src/orders/OTHER.md"), "ask")
        self.assertIsNone(self.e.guard("Write", r / "docs/codebase/INDEX.md"))
        self.assertEqual(self.resolve(cwd=r)["dir"], str(r / "docs/codebase"))

    def test_init_check_adopt(self):
        r = self.e.repo
        out = self.e.run("init", "--mode", "repo-docs", "--gitignore")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue((r / "docs/codebase/INDEX.md").is_file())
        self.assertIn(".claude/knowledge.local.json", (r / ".gitignore").read_text())
        chk = self.e.run("check")
        self.assertEqual(chk.returncode, 1)
        self.assertIn("OLD_NOTES.md", chk.stdout)
        self.assertIn("TEAM_SUMMARY.md", chk.stdout)
        dry = self.e.run("adopt", "TEAM_SUMMARY.md")
        self.assertIn("would move", dry.stdout)
        self.assertTrue((r / "TEAM_SUMMARY.md").exists())
        self.e.run("adopt", "TEAM_SUMMARY.md", "src/orders/OLD_NOTES.md", "--execute")
        self.assertFalse((r / "TEAM_SUMMARY.md").exists())
        self.assertTrue((r / "docs/codebase/notes/OLD_NOTES.md").exists())
        self.assertEqual(self.e.run("check").returncode, 0)
        (r / "X_SUMMARY.md").write_text("y")
        (r / "docs/codebase/notes/X_SUMMARY.md").write_text("z")
        clash = self.e.run("adopt", "X_SUMMARY.md", "--execute")
        self.assertNotEqual(clash.returncode, 0)                          # never overwrites
        self.assertTrue((r / "X_SUMMARY.md").exists())

    def test_init_refuses_overwrite_and_external_hint(self):
        self.assertEqual(self.e.run("init", "--mode", "external").returncode, 0)
        self.assertNotEqual(self.e.run("init", "--mode", "external").returncode, 0)
        out = self.e.run("init", "--mode", "external", "--force")
        self.assertIn("additionalDirectories", out.stdout)

    def test_session_start_context(self):
        out = self.e.run("session-start", stdin=json.dumps({"cwd": str(self.e.repo)})).stdout
        self.assertIn("Codebase knowledge placement", out)
        self.assertIn("ask the user once", out)
        self.e.run("init", "--mode", "repo-docs")
        out = self.e.run("session-start", stdin="{}").stdout
        self.assertIn("Read ", out)
        self.assertNotIn("ask the user once", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
