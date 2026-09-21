"""dashboard.py (WO-0019, PRD-0002) — operator config + gather skeleton.

Same discipline as the other factory-tool suites: fixture trees on
disk, no network, and the CLI pinned through the shared contract
mixins. The gather half is pure disk — protocol orientation over the
knowledge plane's run walk — so these tests exercise it through the
public state dict and the exact problem strings.
"""
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cost_ledger
import cost_report
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

    def test_bytes_that_are_not_utf8_are_a_problem_string(self):
        """repo_set's own docstring says only an unreadable or misshapen
        config is a problem. A non-UTF-8 config is unreadable, so it
        belongs in the `cannot read` arm — but UnicodeDecodeError
        subclasses ValueError, so that OSError arm never saw it."""
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            config.write_bytes('{"repos": ["caf\u00e9"]}'.encode("latin-1"))
            paths, problems = dashboard.repo_set([], config)
            self.assertEqual(paths, [])
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                f"dashboard: cannot read {config}:"), problems)


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

    def test_a_malformed_timestamp_is_refused_not_swallowed(self):
        """#491: a labeled event whose created_at does not read as a
        timestamp is silently dropped by label_events (#326), with no
        signal that anything was refused. The fetch itself succeeded, so
        read.problems says nothing — the refusal needs its own line."""
        with tempfile.TemporaryDirectory() as tmp:
            factory_repo(tmp)
            gh = queue_gh(timelines={
                7: [labeled("not-a-timestamp", "wo:draft")]})
            state = dashboard.gather(tmp, run=gh, git=git_remote(),
                                     clock=clock)
        self.assertEqual(state["problems"], [
            "dashboard: timeline for #7 refused 1 malformed timestamp(s)"])
        self.assertEqual([q["waited_s"] for q in state["queues"]],
                         [None, None])

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
    """The dashboard's half of plane_drift.reconcile_drift (ADR-0060):
    that gather feeds it the right rows and the right policy. The rule's
    own classes are pinned in tests/test_plane_drift.py."""

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
            "docs/features/f/breakdown.md: an unchecked row mirrors #7,"
            " which is closed carrying wo:draft — the row says the work"
            " is outstanding"])
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
            "docs/features/f/breakdown.md: a checked row mirrors #9,"
            " which carries no wo: label — the row says merged"])

    def test_a_clean_fixture_is_silent(self):
        # #7/#8 open with unchecked rows agree across planes; #9's
        # checked row has no listing entry, and this caller passes
        # absent_is_drift=False — its window renders on when truncated,
        # so a mirror it never saw says nothing.
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


class TestSpendCountsOnlyDispatchedRows(unittest.TestCase):
    """cost_ledger.dispatched is the one row-selection rule for what
    counts as spend, because a gate-latency observation (ADR-0041) is a
    $0 wait record, not a run. _metrics keeps it through
    cost_report.aggregate; _spend, reading the same list from the same
    cost_ledger.read call, must keep it too — or the console prints a
    measured $0.00 where the page has an em dash ready."""

    GATE_ONLY = [
        {"wo": "WO-0102", "run_id": "gate-prd-1", "model": "none",
         "tokens": 0, "cost": 0.0, "outcome": "gate_wait:prd:100s",
         "at": "2026-08-02"},
    ]
    RAN = [
        {"wo": "WO-0101", "run_id": "r1", "model": "m", "tokens": 10,
         "cost": 2.0, "outcome": "completed", "at": "2026-08-10"},
        {"wo": "WO-0101", "run_id": "gate-merge-1", "model": "none",
         "tokens": 0, "cost": 0.0, "outcome": "gate_wait:merge:300s",
         "at": "2026-08-11"},
    ]

    def test_the_fixture_holds_both_row_kinds(self):
        """Non-vacuity: these tests mean nothing over rows that are all
        one kind."""
        rows = self.GATE_ONLY + self.RAN
        self.assertTrue([r for r in rows if cost_ledger.gate_wait(r)])
        self.assertTrue(cost_ledger.dispatched(rows))

    def test_a_gate_only_work_order_has_no_spend(self):
        self.assertEqual(dashboard._spend(self.GATE_ONLY), {})

    def test_a_gate_row_does_not_perturb_a_work_order_that_ran(self):
        self.assertEqual(dashboard._spend(self.RAN), {"WO-0101": 2.0})

    def test_the_two_ledger_readers_agree_on_the_work_order_set(self):
        """The console shows _spend's numbers in the output table and
        aggregate's by_wo count in cost_per_wo. A work order in one and
        not the other makes the two disagree on the same page."""
        rows = self.GATE_ONLY + self.RAN
        self.assertEqual(set(dashboard._spend(rows)),
                         set(cost_report.aggregate(rows)["by_wo"]))

    def test_the_rule_is_cost_ledgers_not_a_second_copy(self):
        """A future change to what counts as a spend row must reach the
        console without a second edit here."""
        rows = self.GATE_ONLY + self.RAN
        with mock.patch.object(dashboard.cost_ledger, "dispatched",
                               return_value=[]) as filtered:
            self.assertEqual(dashboard._spend(rows), {})
        filtered.assert_called_once_with(rows)

    def test_the_console_renders_no_spend_for_a_gate_only_row(self):
        """End to end: the row reaches the output table with spend None,
        which dashboard.html renders as an em dash rather than $0.00."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = factory_repo(tmp)
            tree.write("docs/factory/costs.jsonl",
                       "".join(json.dumps(row) + "\n"
                               for row in self.GATE_ONLY + self.RAN))
            tree.write(".github/factory.json",
                       '{"monthly_cap_usd": 300.0}')
            state = dashboard.gather(tmp, run=queue_gh(),
                                     git=git_remote(), clock=clock)
        self.assertEqual(state["problems"], [])
        spend = {row["wo"]: row["spend"] for row in state["output"]}
        self.assertIsNone(spend["WO-0102"])
        self.assertEqual(spend["WO-0101"], 2.0)


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


class TestRespond(unittest.TestCase):
    """The read endpoints' pure half — every handler test pins
    (status, payload) here; the HTTP class stays a thin shim and no
    test opens a socket."""

    def repos_fn(self):
        return ["/repos/alpha", "/repos/beta"], []

    def test_api_repos_lists_the_configured_set_with_indices(self):
        status, payload = dashboard.respond("/api/repos", self.repos_fn,
                                            None)
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"repos": [
            {"i": 0, "path": "/repos/alpha", "name": "alpha"},
            {"i": 1, "path": "/repos/beta", "name": "beta"},
        ]})

    def test_an_unreadable_config_is_the_whole_page_500(self):
        def repos_fn():
            return [], ["dashboard: bad config"]
        status, payload = dashboard.respond("/api/repos", repos_fn, None)
        self.assertEqual(status, 500)
        self.assertEqual(payload,
                         {"problems": ["dashboard: bad config"]})

    def test_api_repo_gathers_the_indexed_repo(self):
        gathered = []

        def gather_fn(path):
            gathered.append(path)
            return {"repo": {"path": path}}
        status, payload = dashboard.respond("/api/repo?i=1",
                                            self.repos_fn, gather_fn)
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"repo": {"path": "/repos/beta"}})
        self.assertEqual(gathered, ["/repos/beta"])

    def test_an_out_of_range_or_unparseable_index_is_404(self):
        for target in ("/api/repo?i=2", "/api/repo?i=-1",
                       "/api/repo?i=x", "/api/repo"):
            with self.subTest(target=target):
                status, payload = dashboard.respond(
                    target, self.repos_fn, None)
                self.assertEqual(status, 404)
                self.assertEqual(payload, {
                    "problems": ["dashboard: no such repo index"]})

    def test_any_other_path_is_404(self):
        status, payload = dashboard.respond("/nope", self.repos_fn, None)
        self.assertEqual(status, 404)
        self.assertEqual(payload,
                         {"problems": ["dashboard: no such path"]})


class TestPage(unittest.TestCase):
    """WO-0026/WO-0027: the console page. / serves dashboard.html
    as-is; the page's render half is pure string functions, exercised
    here against canned payloads under node (the DOM shim is guarded,
    so the script loads without a browser). Skipped only where node is
    absent — CI runners carry it."""

    def repos_fn(self):
        return ["/repos/alpha"], []

    def test_root_serves_the_page(self):
        status, payload = dashboard.respond("/", self.repos_fn, None)
        self.assertEqual(status, 200)
        self.assertIsInstance(payload, str)
        self.assertIn("<!doctype html", payload.lower())

    def test_a_missing_page_file_is_a_500(self):
        page, dashboard.PAGE = dashboard.PAGE, Path("/nope/dashboard.html")
        try:
            status, payload = dashboard.respond("/", self.repos_fn, None)
        finally:
            dashboard.PAGE = page
        self.assertEqual(status, 500)
        self.assertEqual(len(payload["problems"]), 1)
        self.assertTrue(payload["problems"][0].startswith(
            "dashboard: cannot read dashboard.html: "))

    def test_page_fires_one_request_per_repo(self):
        page = dashboard.PAGE.read_text(encoding="utf-8")
        self.assertIn("/api/repos", page)
        self.assertIn("/api/repo?i=", page)

    def test_page_carries_the_no_repos_empty_state(self):
        page = dashboard.PAGE.read_text(encoding="utf-8")
        self.assertIn("No repos configured", page)
        self.assertIn(".process-dashboard.json", page)

    PAYLOAD = {
        "repo": {"path": "/repos/alpha", "name": "alpha",
                 "remote": "octo/alpha"},
        "runs": [{"ref": "feature:process-dashboard",
                  "dir": "docs/features/process-dashboard",
                  "stage": "prd"}],
        "queues": [{"gate": "prd", "issue": 7,
                    "title": "WO-0101 <b>seed</b>", "waited_s": 189000,
                    "url": "https://github.com/octo/alpha/issues/7"}],
        "output": [],
        "drift": ["drift: WO-0102 row is checked but its mirror #8 "
                  "is still open"],
        "metrics": None,
        "problems": ["dashboard: docs/backlog.md is unreadable"],
    }

    OUTPUT_STATES = [
        {"name": "alpha", "payload": {"output": [
            {"wo": "WO-0101", "title": "gate-queue digest", "size": "S",
             "state": "merged", "pr": 245,
             "url": "https://github.com/octo/alpha/pull/245",
             "spend": 3.2},
            {"wo": "WO-0102", "title": "drift <i>x</i>", "size": "M",
             "state": None, "pr": None,
             "url": "https://github.com/octo/alpha/issues/8",
             "spend": None},
        ]}},
        {"name": "beta", "payload": {"output": []}},
    ]

    METRICS_STATES = [
        {"name": "alpha", "payload": {"metrics": {
            "month_spend": 84.1, "cap": 300.0, "cost_per_wo": 4.1,
            "gate_wait_median": 93600, "acceptance": 0.8,
            "rework": 0.25}}},
        {"name": "beta", "payload": {"metrics": None}},
    ]

    BACKLOG_STATES = [
        {"i": 0, "name": "alpha", "payload": {"backlog": {
            "hash": "h1", "seeds": [
                {"line": 3, "text": "seed <one>", "claimed": None},
                {"line": 4, "text": "seed two",
                 "claimed": "feature:beta"},
                {"line": 5, "text": "seed three", "claimed": None},
            ]}}},
        {"i": 1, "name": "beta", "payload": {"backlog": None}},
    ]

    @classmethod
    def rendered(cls):
        """Run the page's render functions under node against the
        canned payload once; assertions read the printed JSON."""
        if not hasattr(cls, "_rendered"):
            import re
            import shutil
            import subprocess
            if not shutil.which("node"):
                raise unittest.SkipTest("node not available")
            page = dashboard.PAGE.read_text(encoding="utf-8")
            script = re.search(r"<script>(.*)</script>", page,
                               re.DOTALL).group(1)
            harness = script + """
const PAYLOAD = %s;
const OUTPUT_STATES = %s;
const METRICS_STATES = %s;
const BACKLOG_STATES = %s;
console.log(JSON.stringify({
  needsYou: renderNeedsYou([{name: "alpha", payload: PAYLOAD}]),
  needsYouEmpty: renderNeedsYou([]),
  card: renderRepoCard("alpha", PAYLOAD, null),
  cardEmpty: renderRepoCard("alpha", {runs: [], problems: []}, null),
  cardError: renderRepoCard("alpha", null, "HTTP 500"),
  cardLoading: renderRepoCard("alpha", null, null),
  status: renderStatus(
    [{i: 0, name: "alpha"}, {i: 1, name: "beta"}, {i: 2, name: "c"}],
    {0: "ok", 1: "error"}),
  wait: [fmtWait(189000), fmtWait(7200), fmtWait(120), fmtWait(null)],
  output: renderOutput(OUTPUT_STATES),
  metrics: renderMetrics(METRICS_STATES),
  metricsEmpty: renderMetrics([METRICS_STATES[1]]),
  backlogDirty: renderBacklog(BACKLOG_STATES, {0: [5, 3, 4]},
                              {0: true}, {0: "HTTP 500: boom"}),
  backlogClean: renderBacklog(BACKLOG_STATES, {0: [3, 4, 5]}, {}, {}),
  moveDown: applyMove([3, 4, 5], 3, 5),
  moveUp: applyMove([3, 4, 5], 5, 3),
  moveSelf: applyMove([3, 4, 5], 4, 4),
  nudgeUp: nudge([3, 4, 5], 4, -1),
  nudgeDown: nudge([3, 4, 5], 4, 1),
  nudgeTopEdge: nudge([3, 4, 5], 3, -1),
  nudgeBottomEdge: nudge([3, 4, 5], 5, 1),
  nudgeUnknown: nudge([3, 4, 5], 9, 1),
}));
""" % (json.dumps(cls.PAYLOAD), json.dumps(cls.OUTPUT_STATES),
       json.dumps(cls.METRICS_STATES), json.dumps(cls.BACKLOG_STATES))
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "render_check.js"
                path.write_text(harness, encoding="utf-8")
                run = subprocess.run(["node", str(path)],
                                     capture_output=True, text=True)
            if run.returncode != 0:
                raise AssertionError(
                    f"render harness failed under node: {run.stderr}")
            cls._rendered = json.loads(run.stdout)
        return cls._rendered

    def test_needs_you_renders_queues_and_drift_with_links(self):
        strip = self.rendered()["needsYou"]
        self.assertIn("Needs you (2)", strip)
        self.assertIn("prd gate", strip)
        self.assertIn('href="https://github.com/octo/alpha/issues/7"',
                      strip)
        self.assertIn("waiting 2d 4h", strip)
        self.assertIn('href="https://github.com/octo/alpha/issues/8"',
                      strip)
        self.assertIn("[alpha]", strip)
        self.assertIn("WO-0101 &lt;b&gt;seed&lt;/b&gt;", strip)
        self.assertNotIn("<b>", strip)

    def test_needs_you_empty_state(self):
        strip = self.rendered()["needsYouEmpty"]
        self.assertIn("Needs you (0)", strip)
        self.assertIn("Nothing waits on you.", strip)

    def test_repo_card_lists_runs_and_renders_problems_in_place(self):
        card = self.rendered()["card"]
        self.assertIn("alpha", card)
        self.assertIn("process-dashboard ▸ prd", card)
        self.assertIn("dashboard: docs/backlog.md is unreadable", card)

    def test_repo_card_states(self):
        self.assertIn("No active runs.", self.rendered()["cardEmpty"])
        self.assertIn("HTTP 500", self.rendered()["cardError"])
        self.assertIn("gathering", self.rendered()["cardLoading"])

    def test_gather_status_marks_each_repo(self):
        self.assertEqual(self.rendered()["status"],
                         "alpha ✓  beta ✗  c …")

    def test_wait_ages_match_the_gate_digest_format(self):
        self.assertEqual(self.rendered()["wait"],
                         ["2d 4h", "2h", "<1h", None])

    def test_output_renders_work_orders_per_repo(self):
        table = self.rendered()["output"]
        self.assertIn("Factory output", table)
        self.assertIn("WO-0101", table)
        self.assertIn("gate-queue digest", table)
        self.assertIn("merged", table)
        self.assertIn('href="https://github.com/octo/alpha/pull/245"',
                      table)
        self.assertIn("#245", table)
        self.assertIn("$3.20", table)
        self.assertIn("drift &lt;i&gt;x&lt;/i&gt;", table)
        self.assertIn('href="https://github.com/octo/alpha/issues/8"',
                      table)
        self.assertIn("No factory stamped in this repo.", table)

    def test_metrics_renders_headline_and_per_repo_rows(self):
        metrics = self.rendered()["metrics"]
        self.assertIn("Metrics", metrics)
        self.assertIn("month spend $84.10 / $300 caps", metrics)
        self.assertIn("alpha", metrics)
        self.assertIn("$84.10 / $300", metrics)
        self.assertIn("cost/WO $4.10", metrics)
        self.assertIn("gate wait 1d 2h", metrics)
        self.assertIn("acceptance 80%", metrics)
        self.assertIn("rework 25%", metrics)
        self.assertIn("No runs recorded yet.", metrics)

    def test_metrics_empty_state(self):
        self.assertIn("No runs recorded yet.",
                      self.rendered()["metricsEmpty"])

    def test_backlog_renders_the_posted_order_with_drag_and_dirty(self):
        section = self.rendered()["backlogDirty"]
        self.assertIn("Backlog", section)
        self.assertIn("seed &lt;one&gt;", section)
        self.assertLess(section.index("seed three"),
                        section.index("seed &lt;one&gt;"))
        self.assertIn('draggable="true" data-repo="0" data-line="3"',
                      section)
        self.assertIn('class="claimed"', section)
        self.assertNotIn('data-line="4"', section)
        self.assertIn("(unsaved order)", section)
        self.assertIn("HTTP 500: boom", section)
        self.assertIn('<button data-save="0">Save order</button>',
                      section)
        self.assertIn("No docs/backlog.md in this repo.", section)

    def test_backlog_clean_state_disables_save(self):
        section = self.rendered()["backlogClean"]
        self.assertNotIn("(unsaved order)", section)
        self.assertIn('<button data-save="0" disabled>Save order'
                      "</button>", section)

    def test_apply_move_is_a_pure_reorder(self):
        self.assertEqual(self.rendered()["moveDown"], [4, 5, 3])
        self.assertEqual(self.rendered()["moveUp"], [5, 3, 4])
        self.assertEqual(self.rendered()["moveSelf"], [3, 4, 5])

    def test_backlog_rows_carry_move_buttons(self):
        """Fix console-drag-ergonomics: every unclaimed row gets real
        ▲/▼ buttons (keyboard-usable); claimed rows get none; the row
        at the very top/bottom has that direction's button disabled."""
        section = self.rendered()["backlogClean"]
        self.assertIn('data-line="3">'
                      '<button data-move="up" disabled>▲</button>'
                      '<button data-move="down">▼</button>', section)
        self.assertIn('data-line="5">'
                      '<button data-move="up">▲</button>'
                      '<button data-move="down" disabled>▼</button>',
                      section)
        self.assertEqual(section.count("data-move="), 4)

    def test_backlog_move_button_edges_follow_list_position(self):
        """Edges are absolute list positions: a mid-list unclaimed row
        keeps ▼ enabled even when every row below it is claimed —
        clicking still moves it, matching what a drop there does."""
        section = self.rendered()["backlogDirty"]
        self.assertIn('data-line="5">'
                      '<button data-move="up" disabled>▲</button>'
                      '<button data-move="down">▼</button>', section)
        self.assertIn('data-line="3">'
                      '<button data-move="up">▲</button>'
                      '<button data-move="down">▼</button>', section)

    def test_nudge_click_moves_match_drag_moves(self):
        """nudge is the click path's applyMove: swap with the adjacent
        slot, no-op at the edges or on an unknown line."""
        r = self.rendered()
        self.assertEqual(r["nudgeUp"], [4, 3, 5])
        self.assertEqual(r["nudgeDown"], [3, 5, 4])
        self.assertEqual(r["nudgeTopEdge"], [3, 4, 5])
        self.assertEqual(r["nudgeBottomEdge"], [3, 4, 5])
        self.assertEqual(r["nudgeUnknown"], [3, 4, 5])


class TestGatherBacklog(unittest.TestCase):
    """WO-0029: gather's backlog section — the hash the Save posts
    back plus the seeds the page lists; a repo without a backlog is
    null (normal, not a problem)."""

    TEXT = ("# Backlog\n"
            "\n"
            "- seed one (from: product)\n"
            "- seed two (from: feature:alpha) (claimed: feature:beta)\n")

    def test_a_backlog_yields_hash_and_seeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            FixtureTree(tmp).write("docs/backlog.md", self.TEXT)
            state = dashboard.gather(tmp)
            self.assertEqual(state["backlog"], {
                "hash": dashboard.backlog_hash(self.TEXT),
                "seeds": [
                    {"line": 3, "text": "seed one", "claimed": None},
                    {"line": 4, "text": "seed two",
                     "claimed": "feature:beta"},
                ]})
            self.assertEqual(state["problems"], [])

    def test_no_backlog_is_null_and_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = dashboard.gather(tmp)
            self.assertIsNone(state["backlog"])
            self.assertEqual(state["problems"], [])


class TestRespondPost(unittest.TestCase):
    """WO-0029: POST /api/backlog-order — the write endpoint's pure
    half, same discipline as respond(): (status, payload) pinned here,
    the HTTP shim stays logic-free. 204 rewrites the file; stale hash
    409, non-permutation 400, unreadable/unwritable file 500, bad
    index 404 — every refusal an exact problem string."""

    TEXT = ("# Backlog\n"
            "\n"
            "- seed one (from: product)\n"
            "- seed two (from: feature:alpha) (claimed: feature:beta)\n"
            "- seed three (from: session:2026-08-01)\n")

    def backlog(self, tmp, text=None):
        FixtureTree(tmp).write("docs/backlog.md", text or self.TEXT)
        return Path(tmp) / "docs" / "backlog.md"

    def post(self, tmp, body):
        return dashboard.respond_post("/api/backlog-order", body,
                                      lambda: ([tmp], []))

    def test_a_valid_order_rewrites_the_file_and_returns_204(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.backlog(tmp)
            body = json.dumps({"i": 0,
                               "hash": dashboard.backlog_hash(self.TEXT),
                               "order": [5, 3, 4]})
            status, payload = self.post(tmp, body)
            self.assertEqual((status, payload), (204, None))
            self.assertEqual(path.read_text(encoding="utf-8"), (
                "# Backlog\n"
                "\n"
                "- seed three (from: session:2026-08-01)\n"
                "- seed one (from: product)\n"
                "- seed two (from: feature:alpha) "
                "(claimed: feature:beta)\n"))

    def test_a_stale_hash_is_409_and_leaves_the_file_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.backlog(tmp)
            body = json.dumps({"i": 0, "hash": "stale",
                               "order": [5, 3, 4]})
            status, payload = self.post(tmp, body)
            self.assertEqual(status, 409)
            self.assertEqual(payload, {"problems": [
                "dashboard: backlog changed underneath; refresh"]})
            self.assertEqual(path.read_text(encoding="utf-8"),
                             self.TEXT)

    def test_a_non_permutation_is_400(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.backlog(tmp)
            body = json.dumps({"i": 0,
                               "hash": dashboard.backlog_hash(self.TEXT),
                               "order": [3, 4]})
            status, payload = self.post(tmp, body)
            self.assertEqual(status, 400)
            self.assertEqual(payload, {"problems": [
                "dashboard: order is not a permutation of the "
                "current seed lines"]})

    def test_a_missing_backlog_is_500(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = json.dumps({"i": 0, "hash": "x", "order": []})
            status, payload = self.post(tmp, body)
            self.assertEqual(status, 500)
            self.assertEqual(len(payload["problems"]), 1)
            self.assertTrue(payload["problems"][0].startswith(
                "dashboard: cannot read docs/backlog.md: "))

    def test_an_unwritable_backlog_is_500_with_the_os_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.backlog(tmp)
            body = json.dumps({"i": 0,
                               "hash": dashboard.backlog_hash(self.TEXT),
                               "order": [5, 3, 4]})
            with mock.patch.object(Path, "write_text",
                                    side_effect=OSError("Permission denied")):
                status, payload = self.post(tmp, body)
            self.assertEqual(status, 500)
            self.assertEqual(len(payload["problems"]), 1)
            self.assertTrue(payload["problems"][0].startswith(
                "dashboard: cannot write docs/backlog.md: "))
            self.assertEqual(path.read_text(encoding="utf-8"),
                             self.TEXT)

    def test_a_bad_index_is_404(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.backlog(tmp)
            for index in (1, -1, "0"):
                with self.subTest(index=index):
                    body = json.dumps({"i": index, "hash": "x",
                                       "order": []})
                    status, payload = self.post(tmp, body)
                    self.assertEqual(status, 404)
                    self.assertEqual(payload, {"problems": [
                        "dashboard: no such repo index"]})

    def test_a_malformed_body_is_400(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.backlog(tmp)
            for body in ("not json", "[]", json.dumps({"i": 0}),
                         json.dumps({"i": 0, "hash": 5, "order": []}),
                         json.dumps({"i": 0, "hash": "x",
                                     "order": ["3"]}),
                         json.dumps({"i": 0, "hash": "x",
                                     "order": "35"})):
                with self.subTest(body=body):
                    status, payload = self.post(tmp, body)
                    self.assertEqual(status, 400)
                    self.assertEqual(payload, {"problems": [
                        "dashboard: body must be JSON with i, hash, "
                        "and an order of line numbers"]})

    def test_an_unreadable_config_is_500(self):
        status, payload = dashboard.respond_post(
            "/api/backlog-order", "{}",
            lambda: ([], ["dashboard: bad config"]))
        self.assertEqual(status, 500)
        self.assertEqual(payload, {"problems": ["dashboard: bad config"]})

    def test_any_other_path_is_404(self):
        status, payload = dashboard.respond_post(
            "/nope", "{}", lambda: ([], []))
        self.assertEqual(status, 404)
        self.assertEqual(payload,
                         {"problems": ["dashboard: no such path"]})


class TestReorderBacklog(unittest.TestCase):
    """WO-0028: the backlog reorder function — permutation-only over
    the seed lines protocol.parse_backlog identifies, claim markers
    riding with their seeds, non-seed lines (header prose, blanks,
    malformed bullets) keeping their exact positions, and the content
    hash as the optimistic-concurrency token."""

    TEXT = ("# Backlog\n"
            "\n"
            "Ordering is priority.\n"
            "\n"
            "- seed one (from: product)\n"
            "- seed two (from: feature:alpha) (claimed: feature:beta)\n"
            "- seed three (from: session:2026-08-01)\n"
            "\n"
            "Trailing prose.\n")

    def test_reorders_seeds_preserving_markers_and_prose(self):
        token = dashboard.backlog_hash(self.TEXT)
        new_text, problems = dashboard.reorder_backlog(
            self.TEXT, token, [7, 5, 6])
        self.assertEqual(problems, [])
        self.assertEqual(new_text, (
            "# Backlog\n"
            "\n"
            "Ordering is priority.\n"
            "\n"
            "- seed three (from: session:2026-08-01)\n"
            "- seed one (from: product)\n"
            "- seed two (from: feature:alpha) (claimed: feature:beta)\n"
            "\n"
            "Trailing prose.\n"))

    def test_identity_order_returns_the_text_unchanged(self):
        token = dashboard.backlog_hash(self.TEXT)
        self.assertEqual(
            dashboard.reorder_backlog(self.TEXT, token, [5, 6, 7]),
            (self.TEXT, []))

    def test_a_malformed_bullet_is_not_movable_and_keeps_its_place(self):
        text = ("- seed one (from: product)\n"
                "- dangling seed\n"
                "- seed two (from: product)\n")
        token = dashboard.backlog_hash(text)
        new_text, problems = dashboard.reorder_backlog(text, token,
                                                       [3, 1])
        self.assertEqual(problems, [])
        self.assertEqual(new_text, ("- seed two (from: product)\n"
                                    "- dangling seed\n"
                                    "- seed one (from: product)\n"))

    def test_a_stale_hash_is_refused(self):
        new_text, problems = dashboard.reorder_backlog(
            self.TEXT, "stale", [5, 6, 7])
        self.assertIsNone(new_text)
        self.assertEqual(problems, [
            "dashboard: backlog changed underneath; refresh"])

    def test_a_non_permutation_is_refused(self):
        token = dashboard.backlog_hash(self.TEXT)
        for order in ([5, 6], [5, 5, 6], [5, 6, 8], [5, 6, 7, 7], []):
            with self.subTest(order=order):
                new_text, problems = dashboard.reorder_backlog(
                    self.TEXT, token, order)
                self.assertIsNone(new_text)
                self.assertEqual(problems, [
                    "dashboard: order is not a permutation of the "
                    "current seed lines"])


class TestServe(unittest.TestCase):
    class FakeServer:
        instances = []

        def __init__(self, address, handler):
            self.address = address
            self.handler = handler
            TestServe.FakeServer.instances.append(self)

        def serve_forever(self):
            raise KeyboardInterrupt

    def test_serve_binds_localhost_only_on_the_given_port(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            problems = dashboard.serve(9123, None,
                                       server_cls=self.FakeServer)
        self.assertEqual(problems, [])
        self.assertEqual(self.FakeServer.instances[-1].address,
                         ("127.0.0.1", 9123))
        self.assertEqual(out.getvalue(),
                         "dashboard: http://127.0.0.1:9123\n")

    def test_a_failed_bind_is_a_problem_string_not_a_traceback(self):
        class BoomServer:
            def __init__(self, _address, _handler):
                raise OSError("Address already in use")
        problems = dashboard.serve(9123, None, server_cls=BoomServer)
        self.assertEqual(problems, [
            "dashboard: cannot bind 127.0.0.1:9123: "
            "Address already in use"])

    def test_an_out_of_range_port_is_a_problem_string(self):
        class RangeServer:
            def __init__(self, _address, _handler):
                raise OverflowError("bind(): port must be 0-65535.")
        problems = dashboard.serve(70000, None, server_cls=RangeServer)
        self.assertEqual(problems, [
            "dashboard: cannot bind 127.0.0.1:70000: "
            "bind(): port must be 0-65535."])

    def test_serve_args_parse_port_and_config(self):
        self.assertEqual(dashboard._serve_args([]),
                         (dashboard.DEFAULT_PORT, None, []))
        self.assertEqual(
            dashboard._serve_args(["--port", "9000",
                                   "--config", "/c.json"]),
            (9000, "/c.json", []))

    def test_a_bad_port_and_an_unknown_flag_are_problems(self):
        _, _, problems = dashboard._serve_args(["--port", "x"])
        self.assertEqual(problems,
                         ["dashboard: --port 'x' is not a number"])
        _, _, problems = dashboard._serve_args(["--nope"])
        self.assertEqual(
            problems, ["dashboard: unrecognized serve argument '--nope'"])
        _, _, problems = dashboard._serve_args(["--config"])
        self.assertEqual(problems, ["dashboard: --config needs a value"])


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

    def test_serve_with_a_bad_flag_reports_the_problem(self):
        code, out = self.run_cli(["serve", "--port", "x"])
        self.assertEqual(code, 1)
        self.assertIn("dashboard: --port 'x' is not a number", out)


class _FakeConn:
    """One HTTP conversation over BytesIO instead of a socket.

    BaseHTTPRequestHandler only needs makefile/sendall, and a real socket
    would need a port and a thread. The request line and headers are
    parsed by http.server itself, so the Content-Length under test
    arrives exactly as it would off the wire — latin-1 decoded included.
    """

    def __init__(self, raw):
        self._rfile = io.BytesIO(raw)
        self.out = io.BytesIO()

    def makefile(self, _mode, _bufsize=-1):
        return self._rfile

    def sendall(self, data):
        self.out.write(data)

    def close(self):
        pass


class _FakeServer:
    server_name = "testserver"
    server_port = 0


def post_raw(raw, repos_fn=lambda: ([], [])):
    """(status line, parsed JSON body or None) for one raw POST."""
    handler = type("H", (dashboard._Handler,), {
        "repos_fn": staticmethod(repos_fn),
        "gather_fn": staticmethod(dashboard.gather)})
    conn = _FakeConn(raw)
    handler(conn, ("127.0.0.1", 5555), _FakeServer())
    out = conn.out.getvalue()
    if not out:
        return None, None
    head, _, body = out.partition(b"\r\n\r\n")
    status = head.split(b"\r\n")[0].decode("latin-1")
    try:
        return status, json.loads(body.decode("utf-8"))
    except ValueError:
        return status, None


def post_with_length(declared, path=b"/api/repos", body=b"{}"):
    header = (b"Content-Length: " + declared + b"\r\n"
              if declared is not None else b"")
    return post_raw(b"POST " + path + b" HTTP/1.1\r\nHost: x\r\n"
                    + header + b"\r\n" + body)


class TestContentLength(unittest.TestCase):
    """The one piece of logic in a handler documented as having none.

    `int(self.headers.get("Content-Length") or 0)` had no guard and no
    test: a malformed value raised out of do_POST, and the client got no
    HTTP response at all — the connection simply closed.
    """

    def test_absent_is_an_empty_body_not_a_problem(self):
        self.assertEqual(dashboard.content_length(None), (0, []))

    def test_a_plain_count_parses(self):
        self.assertEqual(dashboard.content_length("42"), (42, []))

    def test_a_non_numeric_value_is_a_problem_string(self):
        length, problems = dashboard.content_length("abc")
        self.assertIsNone(length)
        self.assertEqual(problems, [
            "dashboard: Content-Length 'abc' is not a non-negative"
            " integer"])

    def test_a_negative_value_is_a_problem_string(self):
        """rfile.read(-1) reads to EOF, which wedges the handler thread on
        a real socket — so a negative length must never reach the read."""
        length, problems = dashboard.content_length("-1")
        self.assertIsNone(length)
        self.assertEqual(problems, [
            "dashboard: Content-Length '-1' is not a non-negative"
            " integer"])

    def test_a_digit_that_int_refuses_is_a_problem_string(self):
        """str.isdigit() is true for '\u00b2' while int() refuses it, so
        isdigit() alone is not a guard. U+00B2 is latin-1 byte 0xB2 and
        http.client decodes headers as latin-1, so it is reachable
        through an ordinary request rather than being a contrivance."""
        length, problems = dashboard.content_length("\u00b2")
        self.assertIsNone(length)
        self.assertEqual(problems, [
            "dashboard: Content-Length '\u00b2' is not a non-negative"
            " integer"])


class TestPostContentLengthOverHttp(unittest.TestCase):
    """The same values driven through a real request cycle, because the
    defect was that the exception escaped the handler, not that the
    arithmetic was wrong."""

    def test_a_valid_length_is_read_and_routed(self):
        status, payload = post_with_length(b"2")
        self.assertEqual(status, "HTTP/1.0 404 Not Found")
        self.assertEqual(payload, {"problems": ["dashboard: no such path"]})

    def test_an_absent_header_is_read_as_an_empty_body(self):
        status, payload = post_with_length(None, body=b"")
        self.assertEqual(status, "HTTP/1.0 404 Not Found")
        self.assertEqual(payload, {"problems": ["dashboard: no such path"]})

    def test_a_non_numeric_length_answers_400_instead_of_dropping(self):
        status, payload = post_with_length(b"abc")
        self.assertEqual(status, "HTTP/1.0 400 Bad Request")
        self.assertEqual(payload, {"problems": [
            "dashboard: Content-Length 'abc' is not a non-negative"
            " integer"]})

    def test_a_digit_that_int_refuses_answers_400(self):
        status, payload = post_with_length("\u00b2".encode("latin-1"))
        self.assertEqual(status, "HTTP/1.0 400 Bad Request")
        self.assertEqual(payload, {"problems": [
            "dashboard: Content-Length '\u00b2' is not a non-negative"
            " integer"]})

    def test_a_negative_length_answers_400_before_the_read(self):
        status, payload = post_with_length(b"-1")
        self.assertEqual(status, "HTTP/1.0 400 Bad Request")
        self.assertEqual(payload, {"problems": [
            "dashboard: Content-Length '-1' is not a non-negative"
            " integer"]})


if __name__ == "__main__":
    unittest.main()
