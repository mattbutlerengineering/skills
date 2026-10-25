"""trace.py (ADR-0092, issue #878): the derived, never-committed trace
view of ticket -> requirement -> decision -> feedback for one key.

Pinned through its public interface — main(argv, run, environ) and the
CLI — against a real throwaway git repo with dated commits (the history
under test is git's), and with the gh port stubbed by tests/fake_gh.py
so no test touches the network.
"""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fake_gh import FakeGh  # noqa: E402
import git_repo  # noqa: E402

# Loaded by path: the stdlib has a `trace` module, and a plain import
# would take whichever one sys.path or sys.modules reached first.
_SPEC = importlib.util.spec_from_file_location("trace_view",
                                               ROOT / "trace.py")
trace_view = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(trace_view)

CI = {"CI": "true"}
TIMELINE = "repos/{owner}/{repo}/issues/12/timeline"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit(root, when, message):
    env = {**os.environ, "GIT_AUTHOR_DATE": when,
           "GIT_COMMITTER_DATE": when}
    for args in (["add", "-A"],
                 ["-c", "user.email=t@example.com", "-c", "user.name=T",
                  "-c", "commit.gpgsign=false", "commit", "-q", "-m",
                  message]):
        subprocess.run(["git", "-C", str(root), *args], check=True,
                       capture_output=True, env=env)
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
        check=True, capture_output=True, text=True).stdout.strip()


def adr(status, date, title):
    return f"# {title}\n\n- Status: {status}\n- Date: {date}\n\nBody.\n"


class Repo(unittest.TestCase):
    """One feature run and one maintenance run, four dated commits."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        git_repo.init(self.root)
        run = self.root / "docs" / "features" / "demo"
        self.run_dir = run
        write(run / "idea.md", "---\nstage: idea\n---\n\n# Idea\n")
        write(run / "prd.md", "---\nstage: prd\nid: PRD-0001\n---\n\n# P\n")
        write(self.root / "docs" / "adr" / "0001-old.md",
              adr("superseded by ADR-0002", "2025-12-01", "Old"))
        write(self.root / "docs" / "adr" / "0002-new.md",
              adr("accepted", "2026-01-02", "New"))
        write(self.root / "docs" / "fixes" / "bug" / "defect.md",
              "# Defect\n\nSee ADR-0002.\n")
        write(self.root / "docs" / "kb" / "page.md",
              "---\nsummary: A fact.\nsources: docs/adr/0002-new.md\n"
              "verified: abc\nrelated:\n---\n\n# Page\n")
        self.a = commit(self.root, "2026-01-01T10:00:00+00:00",
                        "add idea and prd")
        write(run / "architecture.md",
              "# Arch\n\nPer ADR-0001 and ADR-0002.\n\n```\nADR-0003\n```\n")
        write(run / "breakdown.md",
              "# Breakdown\n\n- [x] **WO-0001** Build it (tracker: #12)\n")
        self.b = commit(self.root, "2026-01-02T10:00:00+00:00", "design")
        write(run / "prd.md",
              "---\nstage: prd\nid: PRD-0001\n---\n\n# P\n\nMore.\n")
        self.c = commit(self.root, "2026-01-04T10:00:00+00:00", "tweak prd")
        write(run / "release.md", "# Release\n\nCloses #13\n")
        write(run / "retro.md", "# Retro\n")
        self.d = commit(self.root, "2026-01-05T10:00:00+00:00", "ship")

    def trace(self, *argv, run=None, environ=CI):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = trace_view.main([*argv, "--root", str(self.root)],
                                   run=run or FakeGh(), environ=environ)
        return code, out.getvalue()

    def offline_report(self, header, since="2026-01-01"):
        return "\n".join([
            f"{header} as of {self.d}",
            "note: issue history not read (CI is set)",
            "TICKETS",
            "  ----------  #12 tracker of WO-0001",
            "  ----------  #13 Closes line in release.md",
            "REQUIREMENTS",
            f"  2026-01-01  idea.md created  {self.a}",
            f"  2026-01-01  prd.md created (PRD-0001)  {self.a}",
            f"  2026-01-02  breakdown.md created  {self.b}",
            f"  2026-01-04  prd.md changed, 2 commits  {self.c}",
            "DECISIONS",
            "  2025-12-01  ADR-0001 superseded by ADR-0002 (2026-01-02),"
            " cited by architecture.md",
            "  2026-01-02  ADR-0002 accepted, cited by architecture.md",
            f"  2026-01-02  architecture.md created  {self.b}",
            "FEEDBACK",
            f"  2026-01-05  release.md created  {self.d}",
            f"  2026-01-05  retro.md created  {self.d}",
            f"CHANGES SINCE {since}",
        ])


class TestRunReport(Repo):
    def test_a_run_ref_prints_four_dated_sections_offline(self):
        code, out = self.trace("feature:demo")
        self.assertEqual(code, 0)
        self.assertEqual(out, self.offline_report(
            "feature:demo (PRD-0001)") + "\n" + "\n".join([
                f"  2026-01-01  idea.md: add idea and prd  {self.a}",
                f"  2026-01-01  prd.md: add idea and prd  {self.a}",
                f"  2026-01-02  architecture.md: design  {self.b}",
                f"  2026-01-02  breakdown.md: design  {self.b}",
                f"  2026-01-04  prd.md: tweak prd  {self.c}",
                f"  2026-01-05  release.md: ship  {self.d}",
                f"  2026-01-05  retro.md: ship  {self.d}",
            ]) + "\n")

    def test_since_narrows_only_the_changes_list(self):
        code, out = self.trace("feature:demo", "--since", "2026-01-04")
        self.assertEqual(code, 0)
        self.assertEqual(out, self.offline_report(
            "feature:demo (PRD-0001)", since="2026-01-04") + "\n" +
            "\n".join([
                f"  2026-01-04  prd.md: tweak prd  {self.c}",
                f"  2026-01-05  release.md: ship  {self.d}",
                f"  2026-01-05  retro.md: ship  {self.d}",
            ]) + "\n")

    def test_a_malformed_since_is_a_problem_string(self):
        code, out = self.trace("feature:demo", "--since", "last week")
        self.assertEqual(code, 1)
        self.assertEqual(out, "trace: --since takes YYYY-MM-DD, not"
                              " 'last week'\ntrace: 1 problem(s)\n")

    def test_the_budget_caps_the_report_in_bytes(self):
        code, out = self.trace("feature:demo", "--budget", "200")
        self.assertEqual(code, 0)
        self.assertLessEqual(len(out.encode("utf-8")), 200)
        self.assertTrue(out.endswith(
            "... cut at 200 bytes; raise --budget\n"), out)
        self.assertTrue(out.startswith(
            f"feature:demo (PRD-0001) as of {self.d}\n"))

    def test_a_maintenance_run_cites_its_adr_and_has_no_prd(self):
        code, out = self.trace("maintenance:bug")
        self.assertEqual(code, 0)
        self.assertEqual(out, "\n".join([
            f"maintenance:bug as of {self.d}",
            "note: issue history not read (CI is set)",
            "TICKETS",
            "REQUIREMENTS",
            f"  2026-01-01  defect.md created  {self.a}",
            "DECISIONS",
            "  2026-01-02  ADR-0002 accepted, cited by defect.md",
            "FEEDBACK",
            "CHANGES SINCE 2026-01-01",
            f"  2026-01-01  defect.md: add idea and prd  {self.a}",
        ]) + "\n")


class TestKeyResolution(Repo):
    def header(self, key):
        code, out = self.trace(key)
        self.assertEqual(code, 0, out)
        return out.splitlines()[0]

    def test_every_key_kind_resolves_to_its_run(self):
        expected = f"feature:demo (PRD-0001) as of {self.d}"
        for key in ("feature:demo", "PRD-0001", "WO-0001", "ADR-0001",
                    "#12", "#13", "docs/kb/page.md"):
            with self.subTest(key=key):
                self.assertEqual(self.header(key), expected)

    def test_an_id_more_runs_cite_names_the_others(self):
        code, out = self.trace("ADR-0002")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[:2], [
            f"feature:demo (PRD-0001) as of {self.d}",
            "note: ADR-0002 is also cited by maintenance:bug"])

    def test_the_other_citing_runs_are_capped_at_five(self):
        runs = [{"ref": f"feature:r{n}"} for n in range(8)]
        self.assertEqual(trace_view.pick("ADR-0001", None, runs), (
            runs[0], ["ADR-0001 is also cited by feature:r1, feature:r2,"
                      " feature:r3, feature:r4, feature:r5 and 2 more"]))

    def test_unresolvable_keys_are_exact_problem_strings(self):
        cases = {
            "banana": "trace: banana is not a run ref, typed id, issue"
                      " number (#N) or docs/kb/ page",
            "feature:nope": "trace: feature:nope names no run directory",
            "ADR-0003": "trace: ADR-0003 is declared or cited by no run",
            "docs/kb/none.md": "trace: docs/kb/none.md does not exist",
            "#30": "trace: #30 has no tracker row or Closes line in any"
                   " run, and issue history was not read (CI is set)",
            # The issue key has no leading zero (cost_ledger.ISSUE_KEY).
            "#0": "trace: #0 is not a run ref, typed id, issue number"
                  " (#N) or docs/kb/ page",
            "#012": "trace: #012 is not a run ref, typed id, issue number"
                    " (#N) or docs/kb/ page",
        }
        for key, problem in cases.items():
            with self.subTest(key=key):
                self.assertEqual(self.trace(key),
                                 (1, f"{problem}\ntrace: 1 problem(s)\n"))

    def test_an_issue_resolves_online_through_the_run_its_body_cites(self):
        gh = FakeGh({("issue", "view", "30"): json.dumps(
            {"number": 30, "title": "Bug", "state": "OPEN",
             "createdAt": "2026-01-06T00:00:00Z", "closedAt": None,
             "body": "Follow-up to maintenance:bug."})})
        code, out = self.trace("#30", run=gh, environ={})
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines()[0], f"maintenance:bug as of {self.d}")


class TestIssueHistory(Repo):
    def online_gh(self):
        def view(number, title, created, closed):
            return json.dumps({"number": number, "title": title,
                               "state": "CLOSED", "createdAt": created,
                               "closedAt": closed, "body": ""})
        return FakeGh({
            ("issue", "view", "12"): view(12, "Build it",
                                          "2026-01-02T13:00:00Z",
                                          "2026-01-05T09:00:00Z"),
            ("issue", "view", "13"): view(13, "Ship it",
                                          "2026-01-03T13:00:00Z",
                                          "2026-01-05T11:00:00Z"),
            ("api", TIMELINE): json.dumps([[
                {"event": "labeled", "label": {"name": "wo:ready"},
                 "created_at": "2026-01-03T00:00:00Z"}]]),
            ("api", "repos/{owner}/{repo}/issues/13/timeline"): "[[]]",
            ("issue", "list"): json.dumps([
                {"number": 13, "title": "Ship it", "state": "CLOSED",
                 "createdAt": "2026-01-03T13:00:00Z",
                 "closedAt": "2026-01-05T11:00:00Z"},
                {"number": 20, "title": "Retro on\nfeature:demo",
                 "state": "OPEN", "createdAt": "2026-01-06T00:00:00Z",
                 "closedAt": None}]),
        })

    def test_online_tickets_and_citing_issues_are_dated(self):
        gh = self.online_gh()
        code, out = self.trace("feature:demo", run=gh, environ={})
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(lines[1:8], [
            "TICKETS",
            "  2026-01-02  #12 opened (tracker of WO-0001): Build it",
            "  2026-01-03  #12 labeled wo:ready",
            "  2026-01-03  #13 opened (Closes line in release.md): Ship it",
            "  2026-01-05  #12 closed",
            "  2026-01-05  #13 closed",
            "REQUIREMENTS",
        ])
        feedback = lines[lines.index("FEEDBACK"):
                         lines.index("CHANGES SINCE 2026-01-01")]
        self.assertEqual(feedback[-1],
                         "  2026-01-06  #20 cites the run (open):"
                         " Retro on feature:demo")
        self.assertIn(["issue", "list", "--state", "all", "--search",
                       '"feature:demo" OR "PRD-0001"', "--json",
                       "number,title,state,createdAt,closedAt",
                       "--limit", "100"], gh.calls)

    def test_an_unreachable_gh_is_one_stated_line_and_exit_zero(self):
        gh = FakeGh(failing=["issue"])
        code, out = self.trace("feature:demo", run=gh, environ={})
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[1],
                         "note: issue history not read"
                         " (gh issue view #12 failed: boom)")
        self.assertEqual(len(gh.calls), 1)
        self.assertIn("  ----------  #12 tracker of WO-0001",
                      out.splitlines())

    def test_ci_makes_no_gh_call(self):
        gh = FakeGh()
        self.trace("feature:demo", run=gh)
        self.assertEqual(gh.calls, [])


class TestJson(Repo):
    def test_json_carries_the_same_events_for_renderers(self):
        code, out = self.trace("feature:demo", "--json")
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(sorted(report), [
            "changes", "decisions", "feedback", "head", "issue_history",
            "key", "notes", "prd", "requirements", "run", "since",
            "tickets"])
        self.assertEqual(
            (report["key"], report["run"], report["prd"], report["head"],
             report["since"], report["issue_history"]),
            ("feature:demo", "feature:demo", "PRD-0001", self.d,
             "2026-01-01", "not read (CI is set)"))
        self.assertEqual(report["decisions"][0], {
            "date": "2025-12-01", "commit": None, "ref": "ADR-0001",
            "text": "ADR-0001 superseded by ADR-0002 (2026-01-02),"
                    " cited by architecture.md"})
        self.assertEqual(report["tickets"][0], {
            "date": None, "commit": None, "ref": "#12",
            "text": "#12 tracker of WO-0001"})
        self.assertEqual(report["requirements"][1]["ref"],
                         "docs/features/demo/prd.md")


class TestCli(Repo):
    def cli(self, *argv):
        env = {**os.environ, "CI": "true"}
        return subprocess.run(
            [sys.executable, str(ROOT / "trace.py"), *argv,
             "--root", str(self.root)],
            capture_output=True, text=True, env=env)

    def test_the_cli_prints_the_report_and_exits_zero(self):
        result = self.cli("feature:demo")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith(
            f"feature:demo (PRD-0001) as of {self.d}\n"))

    def test_the_cli_exits_nonzero_on_an_unknown_key(self):
        result = self.cli("banana")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stdout.endswith("trace: 1 problem(s)\n"))


if __name__ == "__main__":
    unittest.main()
