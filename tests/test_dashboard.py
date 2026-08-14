"""dashboard.py (WO-0019, PRD-0002) — operator config + gather skeleton.

Same discipline as the other factory-tool suites: fixture trees on
disk, no network, and the CLI pinned through the shared contract
mixins. The gather half is pure disk — protocol orientation over the
knowledge plane's run walk — so these tests exercise it through the
public state dict and the exact problem strings.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import dashboard

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling fixture_tree import
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fixture_tree import FixtureTree  # noqa: E402


def repo(tmp):
    """A fixture repo with one run per interesting shape: a feature run
    at the prd stage, a maintenance run at implement (re-entry:
    implement, unchecked inline box), a completed run, and a docs/ root
    that is a candidate directory but not a run (no artifacts)."""
    tree = FixtureTree(tmp)
    tree.write("docs/features/alpha/idea.md", "# Idea: alpha\n")
    tree.write("docs/fixes/bug/defect.md",
               "---\nstage: capture\nrun: maintenance:bug\n"
               "re-entry: implement\n---\n\n# Condition\n\n"
               "- [ ] **Fix** — the fix\n")
    tree.write("docs/features/done/idea.md", "# Idea: done\n")
    tree.write("docs/features/done/retro.md", "# Retro\n")
    return tree


class TestRepoSet(unittest.TestCase):
    def test_argv_paths_win_over_the_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            config.write_text(json.dumps({"repos": ["/from/config"]}),
                              encoding="utf-8")
            paths, problems = dashboard.repo_set(["/from/argv"], config)
            self.assertEqual(paths, ["/from/argv"])
            self.assertEqual(problems, [])

    def test_the_config_file_answers_when_argv_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            config.write_text(json.dumps({"repos": ["/a", "/b"]}),
                              encoding="utf-8")
            paths, problems = dashboard.repo_set([], config)
            self.assertEqual(paths, ["/a", "/b"])
            self.assertEqual(problems, [])

    def test_no_argv_and_no_config_is_the_empty_state_not_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "absent.json"
            self.assertEqual(dashboard.repo_set([], config), ([], []))

    def test_a_malformed_config_is_a_problem_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            config.write_text('{"repos": "not-a-list"}', encoding="utf-8")
            paths, problems = dashboard.repo_set([], config)
            self.assertEqual(paths, [])
            self.assertEqual(problems, [
                f"dashboard: {config} must be a JSON object with a"
                " \"repos\" list of paths"])

    def test_an_unparseable_config_is_a_problem_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            config.write_text("{nope", encoding="utf-8")
            paths, problems = dashboard.repo_set([], config)
            self.assertEqual(paths, [])
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                f"dashboard: {config} is not valid JSON:"))


class TestGather(unittest.TestCase):
    def test_active_runs_carry_ref_dir_and_orientation_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo(tmp)
            state = dashboard.gather(tmp)
            self.assertEqual(state["problems"], [])
            self.assertEqual(state["repo"]["name"], Path(tmp).name)
            self.assertEqual(state["repo"]["path"], str(Path(tmp)))
            self.assertEqual(state["runs"], [
                {"ref": "feature:alpha", "dir": "docs/features/alpha",
                 "stage": "prd"},
                {"ref": "maintenance:bug", "dir": "docs/fixes/bug",
                 "stage": "implement"},
            ])

    def test_a_completed_run_and_a_bare_docs_root_are_not_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo(tmp)
            refs = [run["ref"] for run in dashboard.gather(tmp)["runs"]]
            self.assertNotIn("feature:done", refs)
            self.assertNotIn("product", refs)

    def test_a_product_run_at_the_docs_root_is_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            FixtureTree(tmp).write("docs/idea.md", "# Idea\n")
            self.assertEqual(dashboard.gather(tmp)["runs"], [
                {"ref": "product", "dir": "docs", "stage": "prd"}])

    def test_gather_dot_still_yields_the_repo_name(self):
        """`gather .` is the natural invocation from inside a repo;
        Path(".").name is "" unresolved — the acceptance run caught
        exactly this blemish."""
        with tempfile.TemporaryDirectory() as tmp:
            repo(tmp)
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                state = dashboard.gather(".")
            finally:
                os.chdir(cwd)
            self.assertEqual(state["repo"]["name"],
                             Path(tmp).resolve().name)

    def test_a_missing_repo_path_is_a_problem_not_a_crash(self):
        missing = "/no/such/repo"
        state = dashboard.gather(missing)
        self.assertEqual(state["runs"], [])
        self.assertEqual(state["problems"],
                         [f"dashboard: {missing} is not a directory"])


def factory_repo(tmp):
    """A fixture repo whose feature run has a factory breakdown: one row
    waiting at the PRD gate (#7), one at the merge gate (#8), one
    checked and merged (#9, in no queue)."""
    tree = FixtureTree(tmp)
    tree.write("docs/features/f/idea.md", "# Idea\n")
    tree.write("docs/features/f/breakdown.md",
               "# Breakdown\n\n"
               "- [ ] **WO-0101** first — size:S, blocked by: —"
               " (PRD-0009 §X) (tracker: #7)\n"
               "- [ ] **WO-0102** second — size:S, blocked by: WO-0101"
               " (PRD-0009 §X) (tracker: #8)\n"
               "- [x] **WO-0103** done — size:S, blocked by: —"
               " (PRD-0009 §X) (tracker: #9)\n")
    return tree


def git_remote(url="git@github.com:o/r.git"):
    """A fake cli.runner('git') answering remote.origin.url."""
    import subprocess as sp

    def run(args):
        return sp.CompletedProcess(args, 0, stdout=url + "\n", stderr="")
    return run


def clock():
    from datetime import datetime, timezone
    return datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)


def queue_gh(timelines=None, issues=None, **kwargs):
    """A fake gh for the queue traffic: issue list -R and per-issue
    timelines in --slurp's array-of-pages shape (the gate_digest
    idiom)."""
    from fake_gh import FakeGh
    canned = timelines or {}
    listing = issues if issues is not None else [
        {"number": 7, "title": "WO-0101: first",
         "labels": [{"name": "wo:draft"}, {"name": "size:S"}],
         "url": "https://github.com/o/r/issues/7"},
        {"number": 8, "title": "WO-0102: second",
         "labels": [{"name": "wo:needs-review"}],
         "url": "https://github.com/o/r/issues/8"},
    ]

    def timeline(args):
        number = int(args[1].split("/")[-2])
        return json.dumps([canned.get(number, [])])

    return FakeGh(answers={
        ("issue", "list"): json.dumps(listing),
        ("api",): timeline,
    }, **kwargs)


def labeled(ts, name):
    return {"event": "labeled", "label": {"name": name}, "created_at": ts}


class TestRemoteSlug(unittest.TestCase):
    def test_ssh_and_https_remotes_parse_to_the_slug(self):
        for url in ("git@github.com:o/r.git", "https://github.com/o/r",
                    "https://github.com/o/r.git"):
            slug, problems = dashboard.remote_slug("/repo", git_remote(url))
            self.assertEqual((slug, problems), ("o/r", []), url)

    def test_a_repo_without_a_remote_is_a_problem(self):
        import subprocess as sp

        def run(args):
            raise sp.CalledProcessError(1, "git", stderr="")
        slug, problems = dashboard.remote_slug("/repo", run)
        self.assertIsNone(slug)
        self.assertEqual(problems, [
            "dashboard: /repo has no readable remote.origin.url"])

    def test_a_non_github_remote_is_a_problem(self):
        slug, problems = dashboard.remote_slug(
            "/repo", git_remote("https://gitlab.com/o/r.git"))
        self.assertIsNone(slug)
        self.assertEqual(problems, [
            "dashboard: /repo remote https://gitlab.com/o/r.git is not"
            " a github.com remote"])


class TestQueues(unittest.TestCase):
    def test_queued_issues_carry_gate_age_and_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            gh = queue_gh(timelines={
                7: [labeled("2026-08-14T10:00:00Z", "wo:draft")]})
            state = dashboard.gather(tmp, run=gh, git=git_remote(),
                                     clock=clock)
        self.assertEqual(state["problems"], [])
        self.assertEqual(state["repo"]["remote"], "o/r")
        self.assertEqual(state["queues"], [
            {"gate": "prd", "issue": 7, "title": "WO-0101: first",
             "waited_s": 7200, "url": "https://github.com/o/r/issues/7"},
            {"gate": "merge", "issue": 8, "title": "WO-0102: second",
             "waited_s": None,
             "url": "https://github.com/o/r/issues/8"},
        ])

    def test_a_repo_with_no_tracker_rows_makes_no_gh_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo(tmp)
            gh = queue_gh()
            state = dashboard.gather(tmp, run=gh, git=git_remote(),
                                     clock=clock)
        self.assertEqual(gh.calls, [])
        self.assertEqual(state["queues"], [])
        self.assertEqual(state["problems"], [])

    def test_a_failing_issue_list_is_a_problem_and_gather_renders_on(self):
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            gh = queue_gh(failing=["issue", "list"])
            state = dashboard.gather(tmp, run=gh, git=git_remote(),
                                     clock=clock)
        self.assertEqual(state["queues"], [])
        self.assertEqual(state["problems"],
                         ["dashboard: gh issue list failed: boom"])
        self.assertEqual(len(state["runs"]), 1)

    def test_a_failing_timeline_lists_the_item_without_an_age(self):
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            gh = queue_gh(failing=["api"])
            state = dashboard.gather(tmp, run=gh, git=git_remote(),
                                     clock=clock)
        self.assertEqual([q["waited_s"] for q in state["queues"]],
                         [None, None])
        self.assertEqual(state["problems"], [
            "dashboard: gh api timeline for #7 failed: boom",
            "dashboard: gh api timeline for #8 failed: boom"])

    def test_a_missing_remote_skips_the_dispatch_plane_with_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            import subprocess as sp

            def git(args):
                raise sp.CalledProcessError(1, "git", stderr="")
            gh = queue_gh()
            state = dashboard.gather(tmp, run=gh, git=git, clock=clock)
        self.assertEqual(gh.calls, [])
        self.assertIsNone(state["repo"]["remote"])
        self.assertEqual(state["queues"], [])
        self.assertEqual(state["problems"], [
            f"dashboard: {tmp} has no readable remote.origin.url"])


class TestMain(cli_contract.CliContract, cli_contract.ReportContract,
               unittest.TestCase):
    summary_line = "dashboard: 0 problem(s)"
    usage_fragment = "dashboard"

    def run_cli(self, argv):
        return cli_contract.capture(dashboard.main, argv)

    def clean_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo(tmp)
            return self.run_cli(["gather", tmp])

    def test_gather_prints_the_state_dict_as_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo(tmp)
            code, out = self.run_cli(["gather", tmp])
        self.assertEqual(code, 0)
        state = json.loads(out[:out.rindex("dashboard:")])
        self.assertEqual(
            [run["ref"] for run in state["runs"]],
            ["feature:alpha", "maintenance:bug"])

    def test_a_gather_problem_exits_nonzero_with_the_problem_line(self):
        code, out = self.run_cli(["gather", "/no/such/repo"])
        self.assertEqual(code, 1)
        self.assertIn("dashboard: /no/such/repo is not a directory", out)
        self.assertEqual(out.splitlines()[-1], "dashboard: 1 problem(s)")

    def test_gather_without_a_path_prints_usage(self):
        code, out = self.run_cli(["gather"])
        self.assertEqual(code, 2)
        self.assertIn(self.usage_fragment, out)


if __name__ == "__main__":
    unittest.main()
