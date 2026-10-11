"""conductor_run.py (PRD-0013, WO-0158): one metered headless Worker run
per step. Every harness, git and gh call goes through an injected fake —
no model ever runs — and tests assert the EXACT problem strings and rows.
"""
import contextlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import conductor
import conductor_run

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fake_gh import FakeGh  # noqa: E402
from test_conductor_flow import (PLAN, START, answered,  # noqa: E402
                                 launch, moved, ran, run_id, stall_ask)

LEDGER = "docs/factory/batches/b1/ledger.jsonl"
NOW = datetime(2026, 10, 10, 12, 30, tzinfo=timezone.utc)
POLICY_PLAN = dict(PLAN, policy={
    "routing": {"mechanical": "haiku", "implementation": "sonnet",
                "architecture_review": "fable"},
    "effort": {"mechanical": "low", "implementation": "medium",
               "architecture_review": "high"}})
BASE = [POLICY_PLAN] + START[1:]
RESULT = {"type": "result", "subtype": "success", "is_error": False,
          "total_cost_usd": 1.25,
          "usage": {"input_tokens": 100, "output_tokens": 20},
          "modelUsage": {"m": {}}}


class FakeEvents(list):
    timed_out = False


class Harness:
    """A stand-in for cli.harness_run: records the call, lets `act`
    write files into the Worker's cwd, and yields canned events."""

    def __init__(self, events=(RESULT,), act=None, timed_out=False,
                 missing=False):
        self.events, self.act = list(events), act
        self.timed_out, self.missing = timed_out, missing
        self.calls = []

    @contextlib.contextmanager
    def __call__(self, cmd, cwd, timeout, env=None, spawn=None):
        self.calls.append({"cmd": cmd, "cwd": cwd, "timeout": timeout,
                           "env": env})
        if self.missing:
            raise FileNotFoundError(2, "No such file or directory",
                                    "claude")
        if self.act:
            self.act(Path(cwd))
        events = FakeEvents(self.events)
        events.timed_out = self.timed_out
        yield events


def pr_body(path):
    (path / "pr-body.md").write_text("Body\n")


def Git(tmp, changed="", shows=None, fail=None):
    """A git port over a scratch tree: worktree add makes the directory;
    every other call is recorded (run.calls) and answered from canned
    output. `fail` names an argument whose call is rejected."""
    calls = []

    def run(args):
        calls.append(args)
        if fail and fail in args:
            raise subprocess.CalledProcessError(1, args, stderr="rejected")
        out = ""
        if args[:1] == ["rev-parse"]:
            out = str(Path(tmp) / ".git") + "\n"
        elif args[:2] == ["worktree", "add"]:
            Path(args[4]).mkdir(parents=True)
        elif "diff" in args:
            out = changed
        elif "show" in args:
            out = (shows or {})[args[-1]]
        return subprocess.CompletedProcess(args, 0, stdout=out, stderr="")
    run.calls = calls
    return run


def Gh(prs=(), body="Spec this.", title="t", fail=None):
    """The one fake gh, answering issue view and pr list; `fail` is the
    argv prefix whose call is rejected with HTTP 422."""
    return FakeGh(
        answers={("issue", "view"): json.dumps({"title": title,
                                                "body": body}),
                 ("pr", "list"): json.dumps([{"number": n} for n in prs])},
        failing=fail,
        error=subprocess.CalledProcessError(1, "gh", stderr="HTTP 422"))


WORKTREE = ".claude/worktrees/conductor-b1-{n}"


class RunCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "conductor"
        self.root.mkdir()

    def ledger(self, *rows):
        path = self.root / LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))

    def run_step(self, item, step, harness, git=None, gh=None, rows=BASE):
        self.ledger(*rows)
        self.git = git or Git(self.tmp.name)
        self.gh = gh or Gh()
        self.harness = harness
        result = conductor_run.run_step(
            self.root, "b1", item, step, NOW, git=self.git, gh=self.gh,
            harness=harness, pid=777)
        self.rows, _ = conductor.load(self.root, "b1")
        return result

    def worktree(self, item):
        return Path(self.tmp.name) / WORKTREE.format(n=item[1:])

    def spend(self, item):
        path = self.worktree(item) / "docs/factory/costs.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()]


class TestHarnessCommand(unittest.TestCase):
    def test_every_flag_is_composed_in_one_place(self):
        cmd = conductor_run.harness_command("Brief", "sonnet", "medium",
                                            3.0)
        self.assertEqual(cmd[:11], [
            "claude", "-p", "Brief", "--model", "sonnet", "--effort",
            "medium", "--max-budget-usd", "3.00", "--output-format",
            "json"])
        self.assertEqual(cmd[11], "--allowedTools")
        tools = cmd[12:]
        self.assertEqual(tools, list(conductor_run.ALLOWED_TOOLS))
        self.assertFalse([t for t in tools if "push" in t or "gh" in t])


class TestBrief(unittest.TestCase):
    def brief(self, step, issue_body=None):
        return conductor_run.compose_brief(
            step=step, item="#12", item_type="feature",
            worktree="/w", branch="conductor/b1-12",
            block={"adr": [90, 91]}, wo="WO-0170",
            context="ROW AND PACK", issue_body=issue_body, ceiling=3.0)

    def test_the_brief_has_its_fixed_sections(self):
        text = self.brief("build")
        for heading in ("## Objective", "## Output", "## Tools",
                        "## Boundaries", "## Context budget"):
            self.assertIn(heading, text)
        self.assertIn("Implement WO-0170 test-first", text)
        self.assertIn("Work only in /w", text)
        self.assertIn("adr 90-91", text)
        self.assertIn("never edit .claude-plugin/plugin.json's version",
                      text)
        self.assertIn("leave pr-body.md uncommitted", text)
        self.assertIn("never git push", text)
        self.assertIn("$3.00", text)
        self.assertIn("ROW AND PACK", text)

    def test_only_a_spec_brief_carries_the_issue_body(self):
        self.assertIn("ISSUE TEXT", self.brief("spec", "ISSUE TEXT"))
        self.assertIn("stop-after: decompose",
                      self.brief("spec", "ISSUE TEXT"))
        self.assertNotIn("ISSUE TEXT", self.brief("verify", "ISSUE TEXT"))

    def test_a_review_brief_asks_for_a_verdict_and_overrides_the_exit(self):
        text = self.brief("review")
        self.assertIn("`verdict: pass` or `verdict: changes`", text)
        self.assertIn("post no comment, apply no label and merge nothing",
                      text)


class TestCompletedRun(RunCase):
    def test_a_completed_build_writes_one_run_row_and_one_spend_row(self):
        path = "docs/features/x/breakdown.md"
        git = Git(self.tmp.name, changed=f"{path}\n", shows={
            f"conductor/b1-13:{path}": "- [x] **WO-0170** a\n"
                                       "- [ ] **WO-0171** b\n"})
        rows = BASE + [launch("#13", "planned", "spec"), ran("#13", "spec")]
        summary, problems = self.run_step("#13", "build",
                                          Harness(act=pr_body), git=git,
                                          rows=rows)
        self.assertEqual(problems, [])
        rid = "conductor-b1-13-build-1"
        self.assertEqual(self.rows[-2], {
            "at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#13",
            "from": "spec", "to": "build", "reason": "launched",
            "run_id": rid, "pid": 777})
        self.assertEqual(self.rows[-1], {
            "at": "2026-10-10T12:30:00Z", "kind": "run", "item": "#13",
            "step": "build", "charter": "swe", "band": "implementation",
            "model": "m", "models_reported": ["m"],
            "effort": "medium", "run_id": rid, "pid": 777,
            "outcome": "completed"})
        self.assertEqual(self.spend("#13"), [{
            "wo": "WO-0171", "run_id": rid, "model": "m", "tokens": 120,
            "cost": 1.25, "outcome": "completed", "at": "2026-10-10"}])
        kept = self.root / "docs/factory/batches/b1/runs" / f"{rid}.json"
        self.assertEqual(json.loads(kept.read_text()), RESULT)
        self.assertEqual(summary["outcome"], "completed")

    def test_the_harness_runs_bound_by_policy_in_the_item_worktree(self):
        self.run_step("#12", "spec", Harness(act=pr_body))
        call = self.harness.calls[0]
        self.assertEqual(call["cwd"], str(self.worktree("#12")))
        self.assertEqual(call["timeout"], 90 * 60)
        self.assertEqual(call["env"]["CONDUCTOR_WORKER"], "b1")
        cmd = call["cmd"]
        self.assertEqual(cmd[cmd.index("--model") + 1], "m")
        self.assertIn(["worktree", "add", "-b", "conductor/b1-12",
                       str(self.worktree("#12")), "origin/main"],
                      self.git.calls)

    def test_a_non_build_step_is_keyed_by_its_issue(self):
        self.run_step("#12", "spec", Harness(act=pr_body))
        self.assertEqual(self.spend("#12")[0]["wo"], "#12")

    def test_the_branch_is_committed_pushed_and_its_pr_opened(self):
        self.run_step("#12", "spec", Harness(act=pr_body))
        wt = str(self.worktree("#12"))
        self.assertIn(["-C", wt, "add", "docs/factory/costs.jsonl"],
                      self.git.calls)
        self.assertIn(["-C", wt, "commit", "-m",
                       "chore(cost): conductor-b1-12-spec-1"],
                      self.git.calls)
        self.assertIn(["-C", wt, "push", "-u", "origin",
                       "conductor/b1-12"], self.git.calls)
        self.assertFalse([c for c in self.git.calls
                          if any("force" in a for a in c)])
        self.assertIn(["pr", "create", "--head", "conductor/b1-12",
                       "--base", "main", "--title",
                       "#12: conductor batch b1", "--body-file", "Body\n"],
                      self.gh.calls)

    def test_an_open_pr_is_updated_not_duplicated(self):
        self.run_step("#12", "spec", Harness(act=pr_body), gh=Gh(prs=[44]))
        body = str(self.worktree("#12") / "pr-body.md")
        self.assertIn(["api", "-X", "PATCH",
                       "repos/{owner}/{repo}/pulls/44", "-F",
                       f"body=@{body}"], self.gh.calls)
        self.assertFalse([c for c in self.gh.calls if c[:2] == ["pr",
                                                                "create"]])

    def test_the_issue_body_reaches_only_a_spec_brief(self):
        self.run_step("#12", "spec", Harness(act=pr_body),
                      gh=Gh(body="SECRET-ISSUE-TEXT"))
        self.assertIn("SECRET-ISSUE-TEXT", self.harness.calls[0]["cmd"][2])

    def test_seq_counts_earlier_runs_of_the_step(self):
        rows = BASE + [launch("#14", "planned", "build"),
                       moved("#14", "build", "stalled"),
                       stall_ask("ask-2", "#14"),
                       answered("ask-2", "retry", "#14")]
        self.run_step("#14", "build", Harness(act=pr_body),
                      gh=Gh(title="WO-0180: order"), rows=rows)
        self.assertEqual(self.rows[-1]["run_id"], "conductor-b1-14-build-2")
        self.assertEqual(self.spend("#14")[0]["wo"], "WO-0180")

    def test_retry_up_runs_one_band_up(self):
        rows = BASE + [launch("#14", "planned", "build"),
                       moved("#14", "build", "stalled"),
                       stall_ask("ask-2", "#14"),
                       answered("ask-2", "retry-up", "#14")]
        self.run_step("#14", "build", Harness(act=pr_body),
                      gh=Gh(title="WO-0180: order"), rows=rows)
        self.assertEqual((self.rows[-1]["band"], self.rows[-1]["model"],
                          self.rows[-1]["effort"]),
                         ("architecture_review", "fable", "high"))


class TestFailedRun(RunCase):
    def stalled(self):
        return self.rows[-2]["to"], self.rows[-1]["ask_kind"]

    def test_a_missing_harness_is_agent_failed_at_cost_zero(self):
        self.run_step("#12", "spec", Harness(missing=True))
        self.assertEqual(self.spend("#12")[0]["cost"], 0.0)
        self.assertEqual(self.spend("#12")[0]["outcome"], "agent-failed")
        run = [r for r in self.rows if r["kind"] == "run"][-1]
        self.assertEqual(run["outcome"], "agent-failed")
        self.assertEqual(self.stalled(), ("stalled", "stall"))
        self.assertEqual(len(self.harness.calls), 1)

    def test_a_wall_clock_kill_records_the_ceiling_and_stalls(self):
        self.run_step("#12", "spec", Harness(events=[], timed_out=True))
        self.assertEqual(self.spend("#12")[0]["cost"], 3.0)
        self.assertEqual(self.spend("#12")[0]["outcome"],
                         "killed:cost-at-ceiling")
        self.assertEqual(self.rows[-2]["reason"],
                         "killed at its 90-minute wall-clock limit")

    def test_an_unaccountable_result_records_the_ceiling_and_stalls(self):
        bad = dict(RESULT, total_cost_usd="lots")
        self.run_step("#12", "spec", Harness(events=[bad], act=pr_body))
        self.assertEqual(self.spend("#12")[0]["cost"], 3.0)
        self.assertEqual(self.spend("#12")[0]["outcome"],
                         "unaccounted:cost-at-ceiling")
        self.assertEqual(self.stalled(), ("stalled", "stall"))

    def test_a_completed_run_without_pr_body_stalls(self):
        self.run_step("#12", "spec", Harness())
        self.assertEqual(self.rows[-2]["reason"],
                         "the run completed but left no pr-body.md")

    def test_a_failed_push_stalls_and_opens_no_pr(self):
        self.run_step("#12", "spec", Harness(act=pr_body),
                      git=Git(self.tmp.name, fail="push"))
        self.assertTrue(self.rows[-2]["reason"].startswith(
            "pushing conductor/b1-12 failed: rejected"))
        self.assertFalse([c for c in self.gh.calls if c[0] == "pr"])

    def test_a_failed_pr_open_stalls(self):
        self.run_step("#12", "spec", Harness(act=pr_body),
                      gh=Gh(fail=["pr", "create"]))
        self.assertEqual(self.rows[-2]["reason"],
                         "opening or updating the PR failed: HTTP 422")

    def test_a_launch_the_state_machine_refuses_spawns_nothing(self):
        summary, problems = self.run_step("#12", "verify", Harness())
        self.assertIsNone(summary)
        self.assertEqual(problems,
                         ["cd: #12 cannot move from planned to verify"])
        self.assertEqual(self.harness.calls, [])

    def test_an_unknown_item_or_step_is_refused(self):
        self.assertEqual(self.run_step("#99", "spec", Harness())[1],
                         ["cd: #99 is not an item of this batch's plan"])
        self.assertEqual(self.run_step("#14", "spec", Harness())[1],
                         ["cd: #14 has no spec step"])


class TestReviewRun(RunCase):
    REVIEWING = BASE + [launch("#14", "planned", "build"),
                        ran("#14", "build"),
                        launch("#14", "build", "verify"),
                        ran("#14", "verify")]

    def review(self, verdict_line):
        path = "docs/fixes/x/review.md"

        def act(cwd):
            pr_body(cwd)
            (cwd / "docs/fixes/x").mkdir(parents=True)
            (cwd / path).write_text(f"---\nstage: review\n{verdict_line}"
                                    "---\n# Review\n")
        git = Git(self.tmp.name, changed=f"{path}\n")
        self.run_step("#14", "review", Harness(act=act), git=git,
                      gh=Gh(title="WO-0180"), rows=self.REVIEWING)

    def test_a_pass_verdict_marks_the_item_reviewed(self):
        self.review("verdict: pass\n")
        self.assertEqual(self.rows[-1]["to"], "reviewed")
        self.assertEqual(self.rows[-1]["reviewer_run"],
                         "conductor-b1-14-review-1")

    def test_a_missing_verdict_stalls(self):
        self.review("")
        self.assertEqual(self.rows[-2]["reason"],
                         "review.md carries no verdict: pass|changes line")


class TestRunCli(RunCase):
    def test_run_is_a_conductor_verb(self):
        self.ledger(*BASE)
        git = Git(self.tmp.name)
        code, out = cli_contract.capture(
            conductor.main, ["run", "b1", "#12", "spec"], env={},
            clock=lambda: NOW, root=self.root, run=Gh(), git=git,
            harness=Harness(act=pr_body))
        self.assertEqual(code, 0, out)
        self.assertIn("cd: run conductor-b1-12-spec-1 completed", out)

    def test_a_bad_item_argument_prints_usage(self):
        code, _ = cli_contract.capture(
            conductor.main, ["run", "b1", "12", "spec"], env={},
            clock=lambda: NOW, root=self.root)
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
