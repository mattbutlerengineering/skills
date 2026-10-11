"""conductor_plan.py (PRD-0013, the Conductor's plan and open, WO-0156)
— pure-function + fixture tests, in test_conductor's discipline: every
external call goes through an injected fake, and tests assert the EXACT
problem strings callers print.
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import conductor
import conductor_plan

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402

AT = "2026-10-10T12:00:00Z"


def clock():
    return datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)



OWNER = {"owner": {"login": "matt"}}


def issue(number, labels=("type:feature", "size:M"), state="OPEN",
          author="matt"):
    return {"number": number, "state": state, "author": {"login": author},
            "labels": [{"name": name} for name in labels]}


def fake_gh(issues, owner=OWNER, fail=None):
    """A gh port answering repo view and issue view from canned data;
    `fail` names an issue number whose read raises."""
    import subprocess

    def run(args):
        if args[:2] == ["repo", "view"]:
            return json.dumps(owner)
        if args[:2] == ["issue", "view"]:
            if args[2] == str(fail):
                raise subprocess.CalledProcessError(1, args,
                                                    stderr="HTTP 502")
            return json.dumps(issues[int(args[2])])
        raise AssertionError(args)
    return run


def fake_git(grep="PRD-0013\nADR-0083\nWO-0152\nWO-0007\n", calls=None):
    import subprocess

    def run(args):
        if calls is not None:
            calls.append(args)
        if args[0] == "grep":
            return subprocess.CompletedProcess(args, 0, stdout=grep,
                                               stderr="")
        if args[:2] == ["worktree", "add"]:
            Path(args[4]).mkdir(parents=True)
            return subprocess.CompletedProcess(args, 0, stdout="",
                                               stderr="")
        raise AssertionError(args)
    return run


CONFIG = {"budgets_usd": {"S": 5, "M": 15, "L": 40},
          "routing": {"mechanical": "haiku", "implementation": "sonnet",
                      "architecture_review": "fable"},
          "effort": {"mechanical": "low", "implementation": "medium",
                     "architecture_review": "high"},
          "wip_cap": 3, "monthly_cap_usd": 300}
AGENTS = Path(__file__).resolve().parents[1] / "factory" / "agents"
HIGHEST = {"prd": 13, "adr": 83, "wo": 152}


def plan(issues, config=CONFIG, spent=0.0, highest=HIGHEST):
    return conductor_plan.plan_batch(issues, "matt", config, spent, highest,
                                AGENTS)


class TestIdsInUse(unittest.TestCase):
    def test_the_highest_of_each_kind_on_origin_main(self):
        calls = []
        self.assertEqual(conductor_plan.ids_in_use(fake_git(calls=calls)),
                         (HIGHEST, []))
        self.assertEqual(calls, [["grep", "-h", "-o", "-E",
                                  "(PRD|ADR|WO)-[0-9]{4}", "origin/main",
                                  "--", "docs"]])

    def test_no_ids_at_all_is_zero(self):
        import subprocess

        def run(args):
            raise subprocess.CalledProcessError(1, args, stderr="")
        self.assertEqual(conductor_plan.ids_in_use(run),
                         ({"prd": 0, "adr": 0, "wo": 0}, []))

    def test_a_failing_grep_is_a_problem(self):
        import subprocess

        def run(args):
            raise subprocess.CalledProcessError(128, args,
                                                stderr="bad revision")
        self.assertEqual(conductor_plan.ids_in_use(run), (None, [
            "cd: git grep origin/main failed: bad revision"]))


class TestReadIssues(unittest.TestCase):
    def test_reads_each_issue(self):
        issues = {12: issue(12), 13: issue(13)}
        self.assertEqual(conductor_plan.read_issues([12, 13], fake_gh(issues)),
                         ([issues[12], issues[13]], []))

    def test_an_unreadable_issue_refuses_the_read(self):
        self.assertEqual(
            conductor_plan.read_issues([12, 13], fake_gh({12: issue(12)},
                                                    fail=13)),
            (None, ["cd: gh issue view #13 failed: HTTP 502"]))

    def test_a_truncated_issue_refuses_the_read(self):
        partial = {12: {"number": 12, "state": "OPEN", "labels": []}}
        self.assertEqual(conductor_plan.read_issues([12], fake_gh(partial)), (
            None, ["cd: gh issue view #12 returned an incomplete issue"]))

    def test_the_owner_is_read_and_fails_closed(self):
        self.assertEqual(conductor_plan.repo_owner(fake_gh({})), ("matt", []))
        self.assertEqual(conductor_plan.repo_owner(fake_gh({}, owner={})),
                         (None, ["cd: gh repo view names no owner"]))


class TestPlanBatch(unittest.TestCase):
    def test_a_feature_item_is_priced_step_by_step(self):
        result, problems = plan([issue(12)])
        self.assertEqual(problems, [])
        self.assertEqual(result["items"], [{
            "item": "#12", "type": "feature", "size": "M",
            "steps": [
                {"step": "spec", "charter": "architect",
                 "band": "architecture_review", "model": "fable",
                 "effort": "high", "ceiling_usd": 3.0},
                {"step": "build", "charter": "swe",
                 "band": "implementation", "model": "sonnet",
                 "effort": "medium", "ceiling_usd": 3.0},
                {"step": "verify", "charter": "qa",
                 "band": "implementation", "model": "sonnet",
                 "effort": "medium", "ceiling_usd": 3.0},
                {"step": "review", "charter": "reviewer",
                 "band": "architecture_review", "model": "fable",
                 "effort": "high", "ceiling_usd": 3.0},
                {"step": "ship", "charter": "qa",
                 "band": "implementation", "model": "sonnet",
                 "effort": "medium", "ceiling_usd": 3.0}],
            "estimate_usd": 15, "after": [],
            "block": {"prd": [14], "adr": [84, 85, 86],
                      "wo": list(range(153, 163))}}])
        self.assertEqual((result["estimate_usd"], result["cap_usd"],
                          result["month_to_date_usd"]), (15, 300, 0.0))
        self.assertEqual(result["policy"], {"routing": CONFIG["routing"],
                                            "effort": CONFIG["effort"]})

    def test_types_map_from_labels(self):
        result, _ = plan([
            issue(1, ("type:defect", "size:S")),
            issue(2, ("type:chore", "size:S")),
            issue(3, ("type:support", "wo:ready-for-agent", "size:S"))])
        self.assertEqual(
            [(i["type"], [s["step"] for s in i["steps"]], i["block"])
             for i in result["items"]],
            [("fix", ["spec", "build", "verify", "review", "ship"],
              {"adr": [84], "wo": [153, 154, 155, 156, 157]}),
             ("fix", ["spec", "build", "verify", "review", "ship"],
              {"adr": [85], "wo": [158, 159, 160, 161, 162]}),
             ("order", ["build", "verify", "review", "ship"], {})])
        self.assertEqual(result["items"][2]["steps"][0]["charter"],
                         "support")

    def test_no_two_items_blocks_share_a_number(self):
        result, _ = plan([issue(n) for n in (1, 2, 3)]
                         + [issue(4, ("type:defect", "size:S"))])
        for kind in ("prd", "adr", "wo"):
            values = [v for i in result["items"]
                      for v in i["block"].get(kind, [])]
            self.assertEqual(len(values), len(set(values)), kind)
            self.assertGreater(min(values), HIGHEST[kind], kind)

    def test_every_deferral_has_its_own_line(self):
        result, problems = plan([
            issue(1, author="mallory"), issue(2, ("size:S",)),
            issue(3, ("type:feature",)), issue(4, state="CLOSED"),
            issue(5, ("type:sweep", "size:S")),
            issue(6, ("type:feature", "size:L"))], spent=270.0)
        self.assertEqual(problems, [])
        self.assertEqual(result["items"], [])
        self.assertEqual(result["deferred"], [
            "#1 deferred: authored by mallory, not the repo owner matt",
            "#2 deferred: no type: label",
            "#3 deferred: no size: label",
            "#4 deferred: closed",
            "#5 deferred: type:sweep is not plannable",
            "#6 deferred: its $40.00 estimate is over the $30.00 left of"
            " the $300.00 monthly cap"])

    def test_the_cap_counts_earlier_items_in_the_batch(self):
        result, _ = plan([issue(1), issue(2)], spent=275.0)
        self.assertEqual([i["item"] for i in result["items"]], ["#1"])
        self.assertEqual(result["deferred"], [
            "#2 deferred: its $15.00 estimate is over the $10.00 left of"
            " the $300.00 monthly cap"])

    def test_a_config_problem_plans_nothing(self):
        config = dict(CONFIG, effort={"mechanical": "low"})
        self.assertEqual(plan([issue(12)], config=config), (None, [
            "config: factory.json names no effort for the"
            " architecture_review band",
            "config: factory.json names no effort for the implementation"
            " band"]))


class TestComposePlan(unittest.TestCase):
    def test_the_plan_as_report_lines(self):
        result, _ = plan([issue(12), issue(13, ("size:S",))], spent=20.0)
        lines = conductor_plan.compose_plan(result)
        self.assertEqual(lines[0], "cd: 1 item(s) planned")
        self.assertEqual(lines[1], "  #12  feature  size:M  $15.00"
                         "  reserves prd 14, adr 84-86, wo 153-162")
        self.assertEqual(lines[2], "    spec    architect  architecture_review"
                         "  fable  high  $3.00")
        self.assertEqual(lines[-2], "  batch estimate $15.00 against"
                         " $280.00 left of the $300.00 monthly cap")
        self.assertEqual(lines[-1], "  #13 deferred: no type: label")


class TestOpen(unittest.TestCase):
    def test_opens_the_branch_worktree_ledger_and_spend_ask(self):
        result, _ = plan([issue(12), issue(13, ("type:defect", "size:S"))])
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            worktree, problems = conductor_plan.open_batch(
                tmp, "b1", result, clock(), fake_git(calls=calls))
            self.assertEqual(problems, [])
            self.assertEqual(worktree,
                             Path(tmp) / ".claude/worktrees/conductor-b1")
            rows, problems = conductor.load(worktree, "b1")
        self.assertEqual(calls, [["worktree", "add", "-b", "conductor/b1",
                                  str(worktree), "origin/main"]])
        self.assertEqual(problems, [])
        self.assertEqual([r["kind"] for r in rows],
                         ["plan", "reserve", "reserve", "reserve",
                          "reserve", "reserve", "ask"])
        self.assertEqual(rows[0]["batch"], "b1")
        self.assertNotIn("block", rows[0]["items"][0])
        self.assertEqual(rows[0]["policy"], result["policy"])
        self.assertEqual(
            [(r["item"], r["what"], r["values"]) for r in rows[1:6]],
            [("#12", "prd", [14]), ("#12", "adr", [84, 85, 86]),
             ("#12", "wo", list(range(153, 163))),
             ("#13", "adr", [87]), ("#13", "wo", [163, 164, 165, 166, 167])])
        self.assertEqual(rows[-1], {
            "at": AT, "kind": "ask", "item": None, "id": "ask-1",
            "ask_kind": "spend",
            "question": "Spend up to $20.00 on batch b1 (2 item(s))?",
            "options": ["approve", "decline"], "recommended": "approve",
            "why": "the $20.00 estimate fits the $300.00 left of the"
                   " $300.00 monthly cap"})

    def test_an_all_deferred_plan_opens_nothing(self):
        result, _ = plan([issue(12, state="CLOSED")])
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                conductor_plan.open_batch(tmp, "b1", result, clock(),
                                     fake_git(calls=calls)),
                (None, ["cd: nothing to open: every issue was deferred"]))
        self.assertEqual(calls, [])

    def test_an_existing_worktree_is_never_reused(self):
        result, _ = plan([issue(12)])
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".claude/worktrees/conductor-b1").mkdir(
                parents=True)
            self.assertEqual(
                conductor_plan.open_batch(tmp, "b1", result, clock(), fake_git()),
                (None, ["cd: .claude/worktrees/conductor-b1 already"
                        " exists"]))

    def test_a_bad_batch_name_is_refused_before_git(self):
        result, _ = plan([issue(12)])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                conductor_plan.open_batch(tmp, "B 1", result, clock(),
                                     fake_git())[1],
                ["cd: batch 'B 1' is not a batch name (lowercase letters,"
                 " digits and hyphens)"])


class TestPlanCli(unittest.TestCase):
    def run_cli(self, argv, issues, fail=None):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".github").mkdir()
            Path(tmp, ".github/factory.json").write_text(json.dumps(CONFIG))
            Path(tmp, "factory").mkdir()
            Path(tmp, "factory/agents").symlink_to(AGENTS)
            return cli_contract.capture(
                conductor.main, argv, env={}, clock=clock, root=tmp,
                run=fake_gh(issues, fail=fail), git=fake_git())

    def test_plan_prints_the_plan(self):
        code, out = self.run_cli(["plan", "#12"], {12: issue(12)})
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines()[0], "cd: 1 item(s) planned")
        self.assertEqual(out.splitlines()[-1], "cd: 0 problem(s)")

    def test_an_unreadable_issue_refuses_the_whole_plan(self):
        code, out = self.run_cli(["plan", "#12", "#13"], {12: issue(12)},
                                 fail=13)
        self.assertEqual(code, 1)
        self.assertNotIn("planned", out)
        self.assertIn("cd: gh issue view #13 failed: HTTP 502", out)

    def test_an_issue_argument_must_be_an_issue_key(self):
        code, out = self.run_cli(["plan", "12"], {12: issue(12)})
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
