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
