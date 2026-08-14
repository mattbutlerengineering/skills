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


def queue_gh(timelines=None, issues=None, prs=None, **kwargs):
    """A fake gh for the dispatch-plane traffic: issue list -R, pr list
    -R, and per-issue timelines in --slurp's array-of-pages shape (the
    gate_digest idiom)."""
    from fake_gh import FakeGh
    canned = timelines or {}
    listing = issues if issues is not None else [
        {"number": 7, "title": "WO-0101: first", "state": "OPEN",
         "labels": [{"name": "wo:draft"}, {"name": "size:S"}],
         "url": "https://github.com/o/r/issues/7"},
        {"number": 8, "title": "WO-0102: second", "state": "OPEN",
         "labels": [{"name": "wo:needs-review"}],
         "url": "https://github.com/o/r/issues/8"},
        {"number": 9, "title": "WO-0103: done", "state": "CLOSED",
         "labels": [{"name": "wo:merged"}],
         "url": "https://github.com/o/r/issues/9"},
    ]

    def timeline(args):
        number = int(args[1].split("/")[-2])
        return json.dumps([canned.get(number, [])])

    return FakeGh(answers={
        ("issue", "list"): json.dumps(listing),
        ("pr", "list"): json.dumps(list(prs or [])),
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


class TestDrift(unittest.TestCase):
    def test_a_closed_mirror_with_an_unchecked_row_is_flagged(self):
        # The class of drift issue #123 exposed: the work landed but the
        # row never flipped. A closed issue also never queues.
        issues = [
            {"number": 7, "title": "WO-0101: first", "state": "CLOSED",
             "labels": [{"name": "wo:draft"}],
             "url": "https://github.com/o/r/issues/7"},
            {"number": 8, "title": "WO-0102: second", "state": "OPEN",
             "labels": [{"name": "wo:needs-review"}],
             "url": "https://github.com/o/r/issues/8"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            state = dashboard.gather(tmp, run=queue_gh(issues=issues),
                                     git=git_remote(), clock=clock)
        self.assertEqual(state["drift"], [
            "drift: WO-0101 row is unchecked but its mirror #7 is"
            " closed"])
        self.assertEqual([q["issue"] for q in state["queues"]], [8])

    def test_an_open_mirror_with_a_checked_row_is_the_inverse_flag(self):
        issues = [
            {"number": 9, "title": "WO-0103: done", "state": "OPEN",
             "labels": [], "url": "https://github.com/o/r/issues/9"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            state = dashboard.gather(tmp, run=queue_gh(issues=issues),
                                     git=git_remote(), clock=clock)
        self.assertEqual(state["drift"], [
            "drift: WO-0103 row is checked but its mirror #9 is still"
            " open"])

    def test_a_clean_fixture_is_silent(self):
        # #7/#8 open with unchecked rows agree across planes; #9's
        # checked row has no listing entry, and absence says nothing —
        # only definite cross-plane disagreement is a finding.
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            state = dashboard.gather(tmp, run=queue_gh(),
                                     git=git_remote(), clock=clock)
        self.assertEqual(state["drift"], [])
        self.assertEqual(state["problems"], [])

    def test_a_failed_listing_leaves_drift_empty_not_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            state = dashboard.gather(tmp,
                                     run=queue_gh(failing=["issue",
                                                           "list"]),
                                     git=git_remote(), clock=clock)
        self.assertEqual(state["drift"], [])
        self.assertEqual(state["problems"],
                         ["dashboard: gh issue list failed: boom"])


class TestOutput(unittest.TestCase):
    PRS = [
        {"number": 40, "state": "MERGED",
         "body": "Implements WO-0103.\n\nCloses #9",
         "url": "https://github.com/o/r/pull/40"},
        {"number": 41, "state": "OPEN", "body": "Closes #8",
         "url": "https://github.com/o/r/pull/41"},
        {"number": 39, "state": "CLOSED", "body": "closes #9 (abandoned)",
         "url": "https://github.com/o/r/pull/39"},
    ]

    def test_rows_join_label_state_pr_and_spend(self):
        # WO-0101: no PR cites #7 and no ledger row — issue link, no
        # spend. WO-0102: an open PR. WO-0103: the merged PR wins over
        # the abandoned closed one citing the same issue, and its two
        # ledger rows sum.
        with tempfile.TemporaryDirectory() as tmp:
            tree = factory_repo(tmp)
            tree.write(
                "docs/factory/costs.jsonl",
                '{"wo": "WO-0103", "run_id": "r1", "model": "m",'
                ' "tokens": 10, "cost": 2.0, "outcome": "completed",'
                ' "at": "2026-08-10"}\n'
                '{"wo": "WO-0103", "run_id": "r2", "model": "m",'
                ' "tokens": 5, "cost": 1.25, "outcome": "completed",'
                ' "at": "2026-08-11"}\n')
            tree.write(".github/factory.json",
                       '{"monthly_cap_usd": 300.0}')
            state = dashboard.gather(tmp, run=queue_gh(prs=self.PRS),
                                     git=git_remote(), clock=clock)
        self.assertEqual(state["problems"], [])
        self.assertEqual(state["output"], [
            {"wo": "WO-0101", "title": "first", "size": "S",
             "state": "draft", "pr": None,
             "url": "https://github.com/o/r/issues/7", "spend": None},
            {"wo": "WO-0102", "title": "second", "size": "S",
             "state": "needs-review", "pr": 41,
             "url": "https://github.com/o/r/pull/41", "spend": None},
            {"wo": "WO-0103", "title": "done", "size": "S",
             "state": "merged", "pr": 40,
             "url": "https://github.com/o/r/pull/40", "spend": 3.25},
        ])

    def test_an_absent_ledger_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            state = dashboard.gather(tmp, run=queue_gh(prs=self.PRS),
                                     git=git_remote(), clock=clock)
        self.assertEqual(state["problems"], [])
        self.assertEqual([o["spend"] for o in state["output"]],
                         [None, None, None])

    def test_a_failing_pr_list_is_a_problem_and_rows_render_on(self):
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            state = dashboard.gather(tmp,
                                     run=queue_gh(failing=["pr", "list"]),
                                     git=git_remote(), clock=clock)
        self.assertEqual(state["problems"],
                         ["dashboard: gh pr list failed: boom"])
        self.assertEqual([o["pr"] for o in state["output"]],
                         [None, None, None])
        self.assertEqual(state["output"][2]["url"],
                         "https://github.com/o/r/issues/9")

    def test_a_malformed_ledger_line_is_a_problem_never_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = factory_repo(tmp)
            tree.write("docs/factory/costs.jsonl", "{nope\n")
            state = dashboard.gather(tmp, run=queue_gh(prs=self.PRS),
                                     git=git_remote(), clock=clock)
        self.assertEqual(len(state["problems"]), 1)
        self.assertTrue(state["problems"][0].startswith(
            "ledger: docs/factory/costs.jsonl:1"))
        self.assertEqual(len(state["output"]), 3)


LEDGER = (
    '{"wo": "WO-0101", "run_id": "r0", "model": "m", "tokens": 10,'
    ' "cost": 1.0, "outcome": "completed", "at": "2026-07-05"}\n'
    '{"wo": "WO-0101", "run_id": "r1", "model": "m", "tokens": 10,'
    ' "cost": 2.0, "outcome": "completed", "at": "2026-08-10"}\n'
    '{"wo": "WO-0103", "run_id": "r2", "model": "m", "tokens": 10,'
    ' "cost": 3.0, "outcome": "completed", "at": "2026-08-01"}\n'
    '{"wo": "WO-0101", "run_id": "gate-prd-1", "model": "none",'
    ' "tokens": 0, "cost": 0.0, "outcome": "gate_wait:prd:100s",'
    ' "at": "2026-08-02"}\n'
    '{"wo": "WO-0103", "run_id": "gate-merge-1", "model": "none",'
    ' "tokens": 0, "cost": 0.0, "outcome": "gate_wait:merge:300s",'
    ' "at": "2026-08-03"}\n'
    '{"wo": "WO-0103", "run_id": "gate-merge-2", "model": "none",'
    ' "tokens": 0, "cost": 0.0, "outcome": "gate_wait:merge:200s",'
    ' "at": "2026-08-04"}\n')


class TestMetrics(unittest.TestCase):
    def test_metrics_recompute_from_the_ledger_and_cap(self):
        # Month window 2026-08 (the clock's month): $2 + $3 of the $6
        # lifetime. cost/WO is the lifetime mean over the two work
        # orders with run rows; gate rows feed the median wait and stay
        # out of every spend figure (cost_report.aggregate's rule).
        with tempfile.TemporaryDirectory() as tmp:
            tree = factory_repo(tmp)
            tree.write("docs/factory/costs.jsonl", LEDGER)
            tree.write(".github/factory.json",
                       '{"monthly_cap_usd": 300.0}')
            state = dashboard.gather(tmp, run=queue_gh(),
                                     git=git_remote(), clock=clock)
        self.assertEqual(state["problems"], [])
        self.assertEqual(state["metrics"], {
            "month_spend": 5.0, "cap": 300.0, "cost_per_wo": 3.0,
            "gate_wait_median": 200, "acceptance": None,
            "rework": None})

    def test_an_absent_ledger_is_no_runs_recorded_never_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            state = dashboard.gather(tmp, run=queue_gh(),
                                     git=git_remote(), clock=clock)
        self.assertIsNone(state["metrics"])
        self.assertEqual(state["problems"], [])

    def test_a_recorded_ledger_without_a_cap_is_a_problem(self):
        # Once runs are recorded the repo is a factory repo, and a
        # missing factory.json is a real gap — cap None, everything
        # else still renders.
        with tempfile.TemporaryDirectory() as tmp:
            tree = factory_repo(tmp)
            tree.write("docs/factory/costs.jsonl", LEDGER)
            state = dashboard.gather(tmp, run=queue_gh(),
                                     git=git_remote(), clock=clock)
        self.assertEqual(len(state["problems"]), 1)
        self.assertTrue(state["problems"][0].startswith(
            "config: missing factory.json"))
        self.assertEqual(state["metrics"]["cap"], None)
        self.assertEqual(state["metrics"]["month_spend"], 5.0)


RATED_PRS = [
    {"number": 40, "state": "MERGED", "body": "Closes #9",
     "url": "https://github.com/o/r/pull/40",
     "reviews": [{"state": "APPROVED"}]},
    {"number": 41, "state": "MERGED", "body": "Closes #8",
     "url": "https://github.com/o/r/pull/41",
     "reviews": [{"state": "CHANGES_REQUESTED"},
                 {"state": "APPROVED"}]},
    {"number": 42, "state": "OPEN", "body": "Closes #7",
     "url": "https://github.com/o/r/pull/42", "reviews": []},
]


class TestImprovementRates(unittest.TestCase):
    def test_rates_derive_from_reviews_on_merged_wo_cited_prs(self):
        # Two mirrored work orders have landed: WO-0103 (#40) merged
        # first-pass, WO-0102 (#41) after a changes-requested round.
        # The open PR (#42) is not output yet. No ledger, so the spend
        # fields stay None while the rates render.
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            state = dashboard.gather(tmp, run=queue_gh(prs=RATED_PRS),
                                     git=git_remote(), clock=clock)
        self.assertEqual(state["problems"], [])
        self.assertEqual(state["metrics"], {
            "month_spend": None, "cap": None, "cost_per_wo": None,
            "gate_wait_median": None, "acceptance": 0.5, "rework": 0.5})

    def test_corrections_fold_in_and_widen_rework(self):
        # A correction row against review-clean WO-0103: acceptance
        # (review data) holds at 0.5, rework widens to 1.0.
        with tempfile.TemporaryDirectory() as tmp:
            tree = factory_repo(tmp)
            tree.write("docs/factory/corrections.jsonl",
                       '{"wo": "WO-0103", "kind": "post-merge fix"}\n')
            state = dashboard.gather(tmp, run=queue_gh(prs=RATED_PRS),
                                     git=git_remote(), clock=clock)
        self.assertEqual(state["problems"], [])
        self.assertEqual(state["metrics"]["acceptance"], 0.5)
        self.assertEqual(state["metrics"]["rework"], 1.0)

    def test_no_merged_output_is_nothing_to_rate_never_zero(self):
        prs = [{"number": 42, "state": "OPEN", "body": "Closes #7",
                "url": "https://github.com/o/r/pull/42", "reviews": []}]
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            state = dashboard.gather(tmp, run=queue_gh(prs=prs),
                                     git=git_remote(), clock=clock)
        self.assertIsNone(state["metrics"])
        self.assertEqual(state["problems"], [])

    def test_a_malformed_corrections_line_is_a_problem_not_a_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = factory_repo(tmp)
            tree.write("docs/factory/corrections.jsonl",
                       '{nope\n{"kind": "no wo field"}\n')
            state = dashboard.gather(tmp, run=queue_gh(prs=RATED_PRS),
                                     git=git_remote(), clock=clock)
        self.assertEqual(len(state["problems"]), 2)
        self.assertTrue(state["problems"][0].startswith(
            "dashboard: docs/factory/corrections.jsonl:1 is not valid"
            " JSON:"))
        self.assertEqual(state["problems"][1],
                         "dashboard: docs/factory/corrections.jsonl:2"
                         " names no wo")
        self.assertEqual(state["metrics"]["acceptance"], 0.5)


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
