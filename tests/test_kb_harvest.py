"""kb_harvest.py (issue #681): the knowledge-base skill's transcript
miner — check-failed -> fix -> check-passed arcs and recurring tool
errors from Claude Code session transcripts, proposed for review.

Every transcript here is synthetic: a fixture tree that mimics the
harness's JSONL shape (assistant tool_use, user tool_result) under a
temporary projects directory. No real session content is read or
copied by the suite.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kb  # noqa: E402
import kb_harvest  # noqa: E402

REPO = "/work/acme.app"
DAY = 86400


class Session:
    """Builds one synthetic transcript, a JSONL record per line."""

    def __init__(self, sid="s1", cwd=REPO):
        self.sid, self.cwd, self.lines, self.n = sid, cwd, [], 0

    def _record(self, kind, content):
        self.lines.append(json.dumps({
            "type": kind, "sessionId": self.sid, "cwd": self.cwd,
            "timestamp": f"2026-10-01T00:00:{len(self.lines):02d}Z",
            "message": {"role": kind, "content": content}}))

    def tool(self, name, inputs, result, error=False):
        self.n += 1
        use_id = f"toolu_{self.n}"
        self._record("assistant", [{"type": "tool_use", "id": use_id,
                                    "name": name, "input": inputs}])
        item = {"type": "tool_result", "tool_use_id": use_id,
                "content": result}
        if error:
            item["is_error"] = True
        self._record("user", [item])
        return self

    def bash(self, command, result="ok", error=False):
        return self.tool("Bash", {"command": command}, result, error)

    def edit(self, path):
        return self.tool("Edit", {"file_path": path, "old_string": "a",
                                  "new_string": "b"}, "updated")

    def text(self):
        return "\n".join(self.lines) + "\n"


class Tree(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.projects = Path(self._tmp.name) / "projects"
        self.slug = "-work-acme-app"
        self.dir = self.projects / self.slug
        self.dir.mkdir(parents=True)
        self.now = time.time()

    def save(self, session, name=None, age_days=0, where=None):
        path = (where or self.dir) / (name or f"{session.sid}.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(session.text(), encoding="utf-8")
        stamp = self.now - age_days * DAY
        os.utime(path, (stamp, stamp))
        return path

    def harvest(self, **kwargs):
        return kb_harvest.harvest(REPO, self.projects, now=self.now,
                                  **kwargs)


class TestLocate(Tree):
    def test_slug_replaces_every_non_alphanumeric(self):
        self.assertEqual(kb_harvest.slug("/work/acme.app/x_y"),
                         "-work-acme-app-x-y")

    def test_legacy_slug_keeps_dots(self):
        self.assertEqual(kb_harvest.legacy_slug("/work/acme.app"),
                         "-work-acme.app")

    def test_finds_the_project_and_its_worktree_dirs(self):
        worktree = self.projects / f"{self.slug}--claude-worktrees-w1"
        worktree.mkdir()
        (self.projects / f"{self.slug}-other").mkdir()
        self.assertEqual(kb_harvest.project_dirs(REPO, self.projects),
                         [self.dir, worktree])

    def test_falls_back_to_the_legacy_slug(self):
        self.dir.rmdir()
        legacy = self.projects / "-work-acme.app"
        legacy.mkdir()
        self.assertEqual(kb_harvest.project_dirs(REPO, self.projects),
                         [legacy])

    def test_a_long_path_matches_its_truncated_prefix(self):
        long_repo = "/" + "a" * 230
        hashed = self.projects / (kb_harvest.slug(long_repo)[:200] + "-1x2y")
        hashed.mkdir()
        self.assertEqual(kb_harvest.project_dirs(long_repo, self.projects),
                         [hashed])

    def test_no_project_dir_is_one_problem(self):
        self.dir.rmdir()
        result, problems = self.harvest()
        self.assertIsNone(result)
        self.assertEqual(problems, [
            f"harvest: no Claude Code transcripts for {REPO} under"
            f" {self.projects} (looked for {self.slug})"])


class TestSelect(Tree):
    def test_default_is_the_newest_top_level_session(self):
        self.save(Session("old"), age_days=2)
        newest = self.save(Session("new"))
        self.save(Session("agent"), name="agent-x.jsonl")
        self.assertEqual(kb_harvest.select(
            [self.dir], days=None, session=None, now=self.now), [newest])

    def test_days_takes_every_transcript_in_the_window(self):
        inside = self.save(Session("a"), age_days=1)
        nested = self.save(Session("b"), name="subagents/agent-b.jsonl",
                           where=self.dir / "a")
        self.save(Session("c"), age_days=9)
        self.assertEqual(kb_harvest.select(
            [self.dir], days=7, session=None, now=self.now),
            sorted([inside, nested]))

    def test_session_by_id(self):
        wanted = self.save(Session("abc"), age_days=3)
        self.save(Session("new"))
        self.assertEqual(kb_harvest.select(
            [self.dir], days=None, session="abc", now=self.now), [wanted])

    def test_unknown_session_is_a_problem(self):
        self.save(Session("new"))
        result, problems = self.harvest(session="nope")
        self.assertEqual(problems, [
            f"harvest: no session transcript 'nope' in {self.dir}"])


class TestMine(Tree):
    def test_failed_edit_passed_is_an_arc(self):
        self.save(Session()
                  .bash("cd /work/acme.app && python3 -m unittest discover"
                        " tests", "Exit code 1\nFAILED (failures=1)",
                        error=True)
                  .edit(f"{REPO}/src/a.py")
                  .edit(f"{REPO}/tests/test_a.py")
                  .bash("python3 -m unittest discover tests -q", "OK"))
        result, problems = self.harvest()
        self.assertEqual(problems, [])
        self.assertEqual(result["arcs"], [{
            "check": "python3 -m unittest",
            "failure": "FAILED (failures=1)",
            "fixed_by": ["src/a.py", "tests/test_a.py"],
            "attempts": 1,
            "session": "s1",
            "failed_at": "2026-10-01T00:00:01Z",
            "passed_at": "2026-10-01T00:00:07Z",
        }])

    def test_a_retry_with_no_edit_between_is_not_an_arc(self):
        self.save(Session()
                  .bash("make check", "Exit code 2\nboom", error=True)
                  .bash("make check", "ok"))
        result, _ = self.harvest()
        self.assertEqual(result["arcs"], [])

    def test_repeated_failures_count_as_attempts(self):
        self.save(Session()
                  .bash("make check", "Exit code 2\nlint: 3 problem(s)",
                        error=True)
                  .edit(f"{REPO}/a.py")
                  .bash("make check", "Exit code 2\nlint: 1 problem(s)",
                        error=True)
                  .edit(f"{REPO}/b.py")
                  .bash("make check", "ok"))
        arc, = self.harvest()[0]["arcs"]
        self.assertEqual((arc["check"], arc["attempts"], arc["fixed_by"],
                          arc["failure"]),
                         ("make check", 2, ["a.py", "b.py"],
                          "lint: 3 problem(s)"))

    def test_list_content_and_env_prefix_are_read(self):
        self.save(Session()
                  .bash("CI=1 npm test", [{"type": "text",
                                           "text": "Error: x broke"}],
                        error=True)
                  .edit("/elsewhere/z.ts")
                  .bash("npm test", [{"type": "text", "text": "pass"}]))
        arc, = self.harvest()[0]["arcs"]
        self.assertEqual((arc["check"], arc["failure"], arc["fixed_by"]),
                         ("npm test", "Error: x broke", ["/elsewhere/z.ts"]))

    def test_recurring_errors_cluster_across_sessions(self):
        for sid in ("s1", "s2"):
            self.save(Session(sid)
                      .bash("pnpm build", "Exit code 1\nmodule @x/core at"
                            f" line {len(sid) * 7} not built", error=True)
                      .bash("ls", "a b"), age_days=1)
        self.save(Session("s3").bash("pnpm lint", "Exit code 1\nonce",
                                     error=True), age_days=1)
        result, _ = self.harvest(days=7)
        self.assertEqual(result["recurring_errors"], [{
            "tool": "Bash", "error": "module @x/core at line N not built",
            "count": 2, "sessions": 2, "example": "pnpm build"}])

    def test_user_rejections_are_not_errors(self):
        for sid in ("s1", "s2"):
            self.save(Session(sid).bash(
                "rm -rf x", "The user doesn't want to proceed with this"
                " tool use.", error=True))
        result, _ = self.harvest(days=7)
        self.assertEqual(result["recurring_errors"], [])

    def test_malformed_lines_are_counted_not_fatal(self):
        path = self.save(Session().bash("ls", "a"))
        path.write_text(path.read_text(encoding="utf-8") + "{not json\n",
                        encoding="utf-8")
        result, problems = self.harvest()
        self.assertEqual(problems, [])
        self.assertEqual(result["scanned"]["skipped_lines"], 1)
        self.assertEqual(result["scanned"]["transcripts"], 1)


class TestMain(Tree):
    def run_main(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = kb.main(argv)
        return code, out.getvalue()

    def test_harvest_prints_json(self):
        self.save(Session().bash("ls", "a"))
        code, out = self.run_main(["harvest", REPO, "--projects-dir",
                                   str(self.projects)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["arcs"], [])

    def test_bad_days_is_a_problem(self):
        code, out = self.run_main(["harvest", REPO, "--days", "zero",
                                   "--projects-dir", str(self.projects)])
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            "harvest: --days must be a positive whole number, got 'zero'",
            "harvest: 1 problem(s)"])


if __name__ == "__main__":
    unittest.main()
