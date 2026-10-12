"""conductor_run.py launch refusals (#708, #709). An absent cost ledger
on origin/main is zero spend, since nothing seeds one in a consumer
repo; a malformed one still refuses. A refusal no retry fixes (a push
gap, an unusable factory.json, a malformed ledger) pauses dispatch
behind a batch-wide ask, so `next` stops re-offering the refused step.
`open` checks the same item-independent refusals before it queues the
spend ask, so none can first appear after spend consent. git is a fake
or a scratch repo, gh is FakeGh, and the harness never runs a model.
"""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import conductor
import conductor_flow as flow
import conductor_plan
import conductor_run

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_plan import CONFIG, clock, fake_gh, issue  # noqa: E402
from test_conductor_run import BASE, MAIN_COSTS, Gh, Git, Harness, \
    RunCase, pr_body, spend_line  # noqa: E402
from test_conductor_run_guard import PUSHURL, configured  # noqa: E402

AGENTS = Path(__file__).resolve().parents[1] / "factory" / "agents"
PUSHURL_REFUSAL = ("cd: launch refused: remote origin has an explicit"
                   " pushurl, which the Worker's push block does not"
                   " rewrite; unset remote.origin.pushurl while a batch"
                   " runs")
MALFORMED = (f"cd: {MAIN_COSTS}:1 is not valid JSON: Expecting value:"
             " line 1 column 1 (char 0)")


def absent_main_ledger(tmp):
    """The scratch Git port over a main with no costs.jsonl: `git show`
    of it fails as real git's does, and ls-tree lists nothing."""
    git = Git(tmp)

    def run(args):
        if MAIN_COSTS in args:
            git.calls.append(args)
            raise subprocess.CalledProcessError(
                128, args, stderr="fatal: path 'docs/factory/costs.jsonl'"
                " does not exist in 'origin/main'")
        return git(args)
    run.calls = git.calls
    return run


class TestAbsentLedger(RunCase):
    def test_no_ledger_on_main_is_zero_spend_and_the_run_launches(self):
        summary, problems = self.run_step(
            "#12", "spec", Harness(act=pr_body),
            git=absent_main_ledger(self.tmp.name))
        self.assertEqual(problems, [])
        self.assertEqual(summary["outcome"], "completed")
        self.assertFalse([call for call in self.git.calls
                          if MAIN_COSTS in call])

    def test_a_real_main_without_a_ledger_spends_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            def sh(*args):
                return subprocess.run(["git", "-C", tmp, *args], check=True,
                                      capture_output=True, text=True)
            sh("init", "-q")
            sh("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
               "--allow-empty", "-m", "seed")
            sh("update-ref", "refs/remotes/origin/main", "HEAD")
            self.assertEqual(
                conductor_run.month_spend(
                    lambda args: sh(*args), BASE, "b1",
                    datetime(2026, 10, 10, tzinfo=timezone.utc)),
                (0, [], []))

    def test_a_malformed_ledger_on_main_still_refuses(self):
        summary, problems = self.run_step(
            "#12", "spec", Harness(act=pr_body),
            git=Git(self.tmp.name, shows={MAIN_COSTS: "not json\n"}))
        self.assertIsNone(summary)
        self.assertEqual(problems, [
            MALFORMED, "cd: launching #12 spec was refused; dispatch is"
            " paused behind ask-2"])
        self.assertEqual(self.harness.calls, [])


class TestRefusalPausesDispatch(RunCase):
    """#709: a refused launch writes no run row, so without a recorded
    ask `next` re-offers the same step on every tick."""

    def refuse(self, rows=BASE):
        return self.run_step("#12", "spec", Harness(act=pr_body),
                             git=configured(self.tmp.name, PUSHURL),
                             rows=rows)

    def test_a_push_gap_pauses_dispatch_behind_one_ask(self):
        summary, problems = self.refuse()
        self.assertIsNone(summary)
        self.assertEqual(problems, [
            PUSHURL_REFUSAL, "cd: launching #12 spec was refused; dispatch"
            " is paused behind ask-2"])
        self.assertEqual(self.harness.calls, [])
        self.assertEqual(self.rows[len(BASE):], [{
            "at": "2026-10-10T12:30:00Z", "kind": "ask", "item": None,
            "id": "ask-2", "ask_kind": "stall",
            "question": f"Launching #12 spec was refused: {PUSHURL_REFUSAL}."
                        " Resume dispatch, or stop?",
            "options": ["resume", "stop"], "recommended": "resume",
            "why": "a retry meets the same refusal until the setting it"
                   " names changes; change it, then resume"}])

    def test_next_holds_dispatch_behind_the_refusal(self):
        self.refuse()
        ready, _, problems = flow.survey(self.rows, self.clock(), 3,
                                         lambda pid: True, {})
        self.assertEqual((ready, problems), ([], []))
        self.assertEqual(conductor.next_ask(self.rows)["id"], "ask-2")

    def test_a_pending_pause_is_reused_not_repeated(self):
        self.refuse()
        _, problems = self.refuse(rows=self.rows)
        self.assertEqual(problems[-1], "cd: launching #12 spec was refused;"
                         " dispatch is paused behind ask-2")
        self.assertEqual(len([r for r in self.rows if r["kind"] == "ask"]),
                         2)

    def test_an_unusable_factory_json_pauses_dispatch(self):
        (self.root / ".github/factory.json").write_text("{}")
        _, problems = self.run_step("#12", "spec", Harness(act=pr_body))
        self.assertEqual(problems, [
            "config: factory.json names no positive monthly_cap_usd",
            "cd: launching #12 spec was refused; dispatch is paused behind"
            " ask-2"])
        self.assertEqual(self.rows[-1]["ask_kind"], "stall")

    def test_a_transient_git_failure_records_nothing(self):
        summary, problems = self.run_step(
            "#12", "spec", Harness(act=pr_body),
            git=Git(self.tmp.name, fail="ls-tree"))
        self.assertIsNone(summary)
        self.assertEqual(problems, [
            "cd: git ls-tree origin/main failed: rejected"])
        self.assertEqual(self.rows, BASE)


def open_git(tmp, pushurl="", main_costs=None, calls=None):
    """A git port for `open`: grep for ids, worktree add, ls-tree over a
    main that holds costs.jsonl only when `main_costs` is given, and the
    pushurl read."""
    def run(args):
        if calls is not None:
            calls.append(args)
        out = ""
        if args[0] == "grep":
            out = "PRD-0013\n"
        elif args[:2] == ["worktree", "add"]:
            Path(args[4]).mkdir(parents=True)
        elif args[0] == "ls-tree":
            out = args[-1] + "\n" if main_costs is not None \
                and args[-1] == "docs/factory/costs.jsonl" else ""
        elif args[0] == "show":
            out = main_costs
        elif "--get-regexp" in args:
            if not pushurl:
                raise subprocess.CalledProcessError(1, args)
            out = pushurl
        return subprocess.CompletedProcess(args, 0, stdout=out, stderr="")
    return run


class TestOpenPreflight(unittest.TestCase):
    """#708: `open` refuses before it makes the batch or queues the spend
    ask when `run` would refuse every launch."""

    def open(self, config=CONFIG, netrc_text=None, **git):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".github").mkdir()
            Path(tmp, ".github/factory.json").write_text(json.dumps(config))
            netrc = Path(tmp) / "netrc"
            if netrc_text is not None:
                netrc.write_text(netrc_text)
            with contextlib.redirect_stdout(io.StringIO()):
                problems = conductor_plan.open_cli(
                    tmp, ["b1", "--agents", str(AGENTS), "#12"], clock(),
                    fake_gh({12: issue(12)}), open_git(tmp, **git),
                    netrc=netrc)
            opened = (Path(tmp) / ".claude/worktrees/conductor-b1").exists()
            return problems, opened, netrc

    def test_a_clean_repo_with_no_ledger_on_main_opens(self):
        self.assertEqual(self.open()[:2], ([], True))

    def test_a_pushurl_refuses_the_open(self):
        self.assertEqual(self.open(pushurl=PUSHURL)[:2],
                         ([PUSHURL_REFUSAL], False))

    def test_a_github_netrc_entry_refuses_the_open(self):
        problems, opened, netrc = self.open(
            netrc_text="machine github.com login x password t\n")
        self.assertEqual((problems, opened), ([
            f"cd: launch refused: {netrc} has a github.com entry, which"
            " git's https transport would hand a Worker's push; move it"
            " aside while a batch runs"], False))

    def test_a_malformed_ledger_on_main_refuses_the_open(self):
        self.assertEqual(self.open(main_costs="not json\n")[:2],
                         ([MALFORMED], False))

    def test_a_readable_ledger_on_main_opens(self):
        self.assertEqual(
            self.open(main_costs=spend_line("a", 1.0) + "\n")[:2],
            ([], True))

    def test_an_unusable_gate_command_refuses_the_open(self):
        config = dict(CONFIG, conductor={"gate_command": ""})
        self.assertEqual(self.open(config=config)[:2], ([
            "config: factory.json conductor.gate_command must be one"
            " command with no shell operators"], False))


if __name__ == "__main__":
    unittest.main()
