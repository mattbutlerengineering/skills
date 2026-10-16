"""conductor_next.py (#939): `next`'s impure side — the bookkeeping turn
that redoes a finished run's spend commit, push and PR instead of
relaunching the Worker, the issue-state read before any launch, and
the delivery a runner ends with. git and gh go through FakeGit and
FakeGh; tests assert the EXACT rows, calls and problem strings.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import conductor
import conductor_flow as flow
import conductor_landed as landed
import conductor_next as nxt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fake_gh import FakeGh  # noqa: E402
from fake_git import FakeGit  # noqa: E402
from test_conductor_flow import (AT, LEDGER, NOW, START, alive,  # noqa: E402
                                 answered, clock, dead, launch, moved, ran,
                                 stall_ask)

PUSH_FAILED = "pushing conductor/b1-13 failed: fatal: rejected"
RID = "conductor-b1-13-spec-1"
REL = f"docs/factory/costs/runs/{RID}.jsonl"
SPENT = json.dumps({"wo": "#13", "run_id": RID, "model": "m", "tokens": 120,
                    "cost": 1.25, "outcome": "completed",
                    "at": "2026-10-10"}) + "\n"
RESULT = {"type": "result", "subtype": "success", "is_error": False,
          "total_cost_usd": 1.25,
          "usage": {"input_tokens": 100, "output_tokens": 20},
          "modelUsage": {"m": {}}}
RESUMED = ("bookkeeping retried for conductor-b1-13-spec-1: the Worker's"
           " run completed; its spend row, push and PR were redone")


def delivery_failed(key="#13", frm="planned", step="spec", seq=1,
                    reason=PUSH_FAILED, ask_id="ask-2", choice="retry"):
    """The rows of a run that completed and stalled in its bookkeeping,
    answered `choice`."""
    return [launch(key, frm, step, seq=seq), ran(key, step, seq),
            moved(key, step, "stalled", reason=reason,
                  cause="delivery-failed"),
            stall_ask(ask_id, key, options=("retry", "block")),
            answered(ask_id, choice, key)]


def gh(state="OPEN", prs=(), fail=None, closed=(), landed=()):
    """The fake gh: every issue reads `state`, the numbers in `closed`
    read CLOSED, `pr list --state open` names `prs`, and `--state
    merged` names `landed` as (number, merge commit) pairs."""
    def listed(args):
        if "merged" in args:
            return json.dumps([{"number": n, "mergeCommit": {"oid": sha}}
                               for n, sha in landed])
        return json.dumps([{"number": n} for n in prs])
    answers = {("issue", "view"): json.dumps({"state": state}),
               ("pr", "list"): listed}
    for number in closed:
        answers[("issue", "view", number)] = json.dumps({"state": "CLOSED"})
    return FakeGh(answers, failing=fail)


MERGED_CALL = ["pr", "list", "--head", "conductor/b1-13", "--state", "merged",
               "--json", "number,mergeCommit"]
CONTINUED = ("Continues after PR #6667, which merged outside conductor batch"
             " b1 with this item's earlier work.\n\nBody\n")


class NextCase(unittest.TestCase):
    """`conductor.py next b1` over a scratch root whose #13 worktree
    exists, with git and gh injected."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        Path(self.root, ".github").mkdir()
        Path(self.root, ".github/factory.json").write_text(
            json.dumps({"wip_cap": 2}))
        self.wt = self.root / ".claude/worktrees/conductor-b1-13"
        self.wt.mkdir(parents=True)

    def git(self, log="", failing=None, error=None):
        return FakeGit({("rev-parse",): f"{self.root}/.git\n",
                        ("log",): log}, failing=failing, error=error)

    def spent(self, text=SPENT):
        (self.wt / REL).parent.mkdir(parents=True, exist_ok=True)
        (self.wt / REL).write_text(text)

    def body(self):
        (self.wt / "pr-body.md").write_text("Body\n")

    def kept(self, event=RESULT):
        runs = self.root / "docs/factory/batches/b1/runs"
        runs.mkdir(parents=True, exist_ok=True)
        (runs / f"{RID}.json").write_text(json.dumps(event))

    def next(self, rows, git=None, gh_=None, probe=alive):
        path = self.root / LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        self.git_ = git or self.git()
        self.gh_ = gh_ or gh()
        code, out = cli_contract.capture(
            conductor.main, ["next", "b1"], env={}, clock=clock,
            root=str(self.root), run=self.gh_, git=self.git_, alive=probe)
        after, _ = conductor.load(self.root, "b1")
        payload = json.loads(out[:out.rindex("\ncd:")]) \
            if "\ncd:" in out and code == 0 else None
        return {"code": code, "out": out, "rows": after[len(rows):],
                "payload": payload,
                "wt_calls": [c for c in self.git_.calls if c[:1] == ["-C"]]}


class TestBookkeepingRetry(NextCase):
    """A retry answer on a delivery-failed stall whose run completed
    redoes the spend commit, push and PR in the Owner's session and
    launches nothing (#939: one spec completed three times for $12.53)."""

    ROWS = START + delivery_failed()

    def test_the_turn_commits_pushes_opens_the_pr_and_resumes(self):
        self.spent()
        self.body()
        got = self.next(self.ROWS)
        self.assertEqual(got["code"], 0, got["out"])
        wt = str(self.wt)
        self.assertEqual(got["wt_calls"], [
            ["-C", wt, "add", REL],
            ["-C", wt, "commit", "-m", f"chore(cost): {RID}"],
            ["-C", wt, "push", "-u", "origin", "conductor/b1-13"]])
        self.assertIn(["pr", "create", "--head", "conductor/b1-13",
                       "--base", "main", "--title",
                       "#13: conductor batch b1", "--body-file", "Body\n"],
                      self.gh_.calls)
        self.assertEqual(got["rows"][0], {
            "at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#13",
            "from": "stalled", "to": "spec", "reason": RESUMED,
            "run_id": RID})
        self.assertFalse((self.wt / "pr-body.md").exists())
        # The same tick reads the branch facts: a fix with no gate file
        # goes straight to build, which the issue read then clears.
        self.assertIn({"item": "#13", "step": "build"},
                      got["payload"]["ready"])
        self.assertEqual(len(got["rows"]), 1)

    def test_a_spend_commit_the_branch_already_holds_is_not_redone(self):
        self.body()
        got = self.next(self.ROWS, git=self.git(
            log=f"docs: later\nchore(cost): {RID}\n"))
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual([c[2] for c in got["wt_calls"]], ["push"])
        self.assertEqual(got["rows"][0]["to"], "spec")

    def test_an_open_pr_is_updated_not_reopened(self):
        self.spent()
        self.body()
        got = self.next(self.ROWS, gh_=gh(prs=(7,)))
        self.assertEqual(got["code"], 0, got["out"])
        self.assertIn(["api", "-X", "PATCH", "repos/{owner}/{repo}/pulls/7",
                       "-F", "body=@" + str(self.wt / "pr-body.md")],
                      self.gh_.calls)
        self.assertFalse([c for c in self.gh_.calls if c[:2] == ["pr",
                                                                 "create"]])

    def test_a_missing_spend_file_is_re_metered_from_the_kept_result(self):
        self.kept()
        got = self.next(self.ROWS)
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual((self.wt / REL).read_text(), SPENT)
        self.assertEqual([c[2] for c in got["wt_calls"]],
                         ["add", "commit", "push"])

    def test_no_spend_row_and_no_kept_result_stalls_again(self):
        got = self.next(self.ROWS)
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual([(r["kind"], r.get("to"), r.get("cause"))
                          for r in got["rows"]],
                         [("state", "spec", None),
                          ("state", "stalled", "delivery-failed"),
                          ("ask", None, None)])
        self.assertTrue(got["rows"][1]["reason"].startswith(
            f"no spend row of {RID} to commit, and its result event cannot"
            " be metered: cannot read execution file"), got["rows"][1])
        self.assertEqual(
            (got["rows"][2]["options"], got["rows"][2]["recommended"],
             got["rows"][2]["why"]),
            (["retry", "block"], "retry", flow.DELIVERY_WHY))
        self.assertEqual(got["wt_calls"], [])

    def test_a_failed_push_stalls_with_the_commands_stderr_tail(self):
        self.spent()
        self.body()
        error = subprocess.CalledProcessError(
            1, "git", stderr="To github.com:o/r.git\n ! [rejected]"
            "        conductor/b1-13 -> conductor/b1-13 (fetch first)\n"
            "error: failed to push some refs to 'github.com:o/r.git'\n"
            "hint: Updates were rejected because the remote contains work\n")
        got = self.next(self.ROWS, git=self.git(
            failing=["-C", str(self.wt), "push"], error=error))
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual(got["rows"][1]["reason"], (
            "pushing conductor/b1-13 failed: ! [rejected]        "
            "conductor/b1-13 -> conductor/b1-13 (fetch first) | error:"
            " failed to push some refs to 'github.com:o/r.git' | hint:"
            " Updates were rejected because the remote contains work"))
        self.assertEqual(got["rows"][1]["cause"], "delivery-failed")
        self.assertEqual(got["rows"][2]["options"], ["retry", "block"])
        # The body stays for the next turn.
        self.assertTrue((self.wt / "pr-body.md").exists())

    def test_a_missing_worktree_is_a_problem_and_nothing_is_written(self):
        self.wt.rmdir()
        got = self.next(self.ROWS)
        self.assertNotEqual(got["code"], 0)
        self.assertIn(f"cd: #13's worktree {self.wt} is gone, so run {RID}'s"
                      " bookkeeping cannot be retried", got["out"])
        self.assertEqual(got["rows"], [])

    def test_a_second_bookkeeping_failure_is_retried_the_same_way(self):
        rows = self.ROWS + [
            flow.state_row(NOW, "#13", "stalled", "spec", RESUMED,
                           run_id=RID),
            moved("#13", "spec", "stalled", reason=PUSH_FAILED,
                  cause="delivery-failed"),
            stall_ask("ask-3", "#13", options=("retry", "block")),
            answered("ask-3", "retry", "#13")]
        self.spent()
        got = self.next(rows)
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual([c[2] for c in got["wt_calls"]],
                         ["add", "commit", "push"])
        self.assertEqual(got["rows"][0]["to"], "spec")

    def test_a_closed_issue_is_asked_about_before_any_bookkeeping(self):
        self.spent()
        self.body()
        got = self.next(self.ROWS, gh_=gh(closed=("13",)))
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual(got["wt_calls"], [])
        self.assertEqual(got["rows"], [{
            "at": "2026-10-10T12:30:00Z", "kind": "ask", "item": "#13",
            "id": "ask-3", "ask_kind": "clarify",
            "question": "#13's issue is closed on GitHub, so a run would"
                        " spend on finished work. Block it, or reopen the"
                        " issue and proceed?",
            "options": ["block", "proceed"], "recommended": "block",
            "why": nxt.CLOSED_WHY}])
        self.assertNotIn("#13", [e["item"] for e in got["payload"]["ready"]])

    def test_a_block_answer_to_the_clarify_ask_blocks_the_item(self):
        # #12 never launched: the block carries owner-block, the cause of
        # a block on an unstalled item.
        rows = START + [nxt.clarify_ask(START, NOW, "#12", "closed", [])[0]]
        path = self.root / LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        code, out = cli_contract.capture(
            conductor.main, ["answer", "b1", "ask-2", "block"], env={},
            clock=clock, root=str(self.root))
        self.assertEqual(code, 0, out)
        after, _ = conductor.load(self.root, "b1")
        self.assertEqual((after[-1]["item"], after[-1]["to"],
                          after[-1]["cause"]),
                         ("#12", "blocked", "owner-block"))


class TestLaunchChecksTheIssue(NextCase):
    """Before any run launches, `next` re-reads the issue's state (#939:
    nine items were closed by other PRs and still got paid retries and
    fresh spec launches)."""

    def test_an_open_issue_launches(self):
        got = self.next(START)
        self.assertEqual(got["payload"]["ready"],
                         [{"item": "#12", "step": "spec"},
                          {"item": "#13", "step": "spec"}])
        self.assertEqual([c for c in self.gh_.calls if c[:2] == [
            "issue", "view"]], [["issue", "view", "12", "--json", "state"],
                                ["issue", "view", "13", "--json", "state"]])

    def test_a_closed_issue_is_held_behind_a_clarify_ask(self):
        got = self.next(START, gh_=gh(state="CLOSED"))
        self.assertEqual(got["payload"]["ready"], [])
        self.assertEqual([(r["item"], r["id"], r["ask_kind"])
                          for r in got["rows"]],
                         [("#12", "ask-2", "clarify"),
                          ("#13", "ask-3", "clarify")])
        self.assertEqual(got["payload"]["recorded"], ["ask-2", "ask-3"])
        self.assertEqual(got["payload"]["ask"]["id"], "ask-2")

    def test_an_unreadable_state_holds_the_item_too(self):
        got = self.next(START, gh_=gh(fail=["issue", "view"]))
        self.assertEqual(got["payload"]["ready"], [])
        asked = got["rows"][0]
        self.assertEqual(
            (asked["question"], asked["recommended"], asked["why"]),
            ("#12's issue state could not be read (cd: gh issue view #12"
             " failed: boom), so nothing launches until it can. Block it,"
             " or proceed once gh reads it?", "proceed", nxt.UNREAD_WHY))

    def test_a_proceed_answer_re_reads_before_launching(self):
        rows = START + [nxt.clarify_ask(START, NOW, "#12", "closed", [])[0],
                        answered("ask-2", "proceed", "#12")]
        got = self.next(rows, gh_=gh(state="CLOSED"))
        self.assertEqual(got["payload"]["ready"],
                         [])
        self.assertEqual(got["rows"][0]["ask_kind"], "clarify")
        got = self.next(rows)
        self.assertIn({"item": "#12", "step": "spec"},
                      got["payload"]["ready"])

    def test_a_dead_runner_is_still_charged_before_the_read(self):
        # #967's charge and the issue read compose: the lost run is
        # charged, then the retry it offers waits on the Owner anyway.
        rows = START + [launch("#13", "planned", "spec", pid=9)]
        self.spent()
        got = self.next(rows, probe=dead)
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual([r["kind"] for r in got["rows"]],
                         ["run", "state", "ask"])

    def test_a_merge_step_is_not_read(self):
        gh_ = gh(state="CLOSED")
        self.assertEqual(
            nxt.clarify_closed(gh_, START, [{"item": "#12", "step": "merge"}],
                               NOW),
            ([{"item": "#12", "step": "merge"}], [], []))
        self.assertEqual(gh_.calls, [])


class TestIssueState(unittest.TestCase):
    def test_reads_one_state_lowercased(self):
        self.assertEqual(nxt.issue_state(gh("CLOSED"), "#12"),
                         ("closed", []))
        self.assertEqual(nxt.issue_state(gh("OPEN"), "#12"), ("open", []))

    def test_a_failed_read_is_the_problem(self):
        self.assertEqual(nxt.issue_state(gh(fail=["issue"]), "#12"),
                         (None, ["cd: gh issue view #12 failed: boom"]))

    def test_a_missing_state_is_none_with_no_problem(self):
        gh_ = FakeGh({("issue", "view"): json.dumps({"title": "t"})})
        self.assertEqual(nxt.issue_state(gh_, "#12"), (None, []))


class TestBookkeepingDue(unittest.TestCase):
    def test_a_delivery_failed_stall_with_a_completed_run_is_due(self):
        rows = START + delivery_failed()
        [(found, step, run)] = nxt.bookkeeping_due(rows)
        self.assertEqual((found["item"], step, run["run_id"]),
                         ("#13", "spec", RID))

    def test_other_stalls_and_unanswered_ones_are_not(self):
        for rows in (
                START + delivery_failed(choice="block"),
                START + delivery_failed()[:-1],
                START + [launch("#13", "planned", "spec"),
                         ran("#13", "spec", outcome="agent-failed"),
                         moved("#13", "spec", "stalled", reason="r",
                               cause="agent-failed"),
                         stall_ask("ask-2", "#13"),
                         answered("ask-2", "retry", "#13")],
                START + [launch("#13", "planned", "spec"), ran("#13", "spec"),
                         moved("#13", "spec", "stalled", reason="r"),
                         stall_ask("ask-2", "#13"),
                         answered("ask-2", "retry", "#13")]):
            with self.subTest(rows=rows[-1]):
                self.assertEqual(nxt.bookkeeping_due(rows), [])


# #13's spec completed: its PR is due a read before build launches.
SPECCED = START + [launch("#13", "planned", "spec"), ran("#13", "spec")]
LANDED_STALL = [
    moved("#13", "spec", "stalled", reason="PR #6667 merged outside the"
          " batch", cause="merge-drift", pr=6667),
    stall_ask("ask-2", "#13", options=("retry", "merged", "block"))]


class TestLandedRead(NextCase):
    """#938: `next` reads each due item's merged PR every tick, through
    the injected gh, and stalls an item whose PR the repo merged
    outside the batch; a `merged` answer then records that PR."""

    def test_a_merged_pr_stalls_the_item_and_names_it(self):
        got = self.next(SPECCED, gh_=gh(landed=((6667, "abc"),)))
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual(self.gh_.called("pr", "list"), [MERGED_CALL])
        self.assertEqual(got["rows"], [
            {"at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#13",
             "from": "spec", "to": "stalled",
             "reason": "PR #6667 merged outside the batch",
             "cause": "merge-drift", "pr": 6667},
            {"at": "2026-10-10T12:30:00Z", "kind": "ask", "item": "#13",
             "id": "ask-2", "ask_kind": "stall",
             "question": "#13 stalled in spec: PR #6667 merged outside the"
                         " batch. Retry, treat it as merged, or block?",
             "options": ["retry", "merged", "block"],
             "recommended": "retry",
             "why": landed.REST_WHY.format(pr=6667)}])
        self.assertEqual(got["payload"]["ready"],
                         [{"item": "#12", "step": "spec"},
                          {"item": "#14", "step": "build"}])
        self.assertEqual(got["payload"]["ask"]["id"], "ask-2")

    def test_no_merged_pr_launches_as_before(self):
        got = self.next(SPECCED)
        self.assertEqual(self.gh_.called("pr", "list"), [MERGED_CALL])
        self.assertIn({"item": "#13", "step": "build"},
                      got["payload"]["ready"])
        self.assertEqual(got["rows"], [])

    def test_a_merged_answer_writes_the_merge_from_the_read(self):
        rows = SPECCED + LANDED_STALL + [answered("ask-2", "merged", "#13")]
        got = self.next(rows, gh_=gh(landed=((6667, "abc"),)))
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual(got["rows"], [
            {"at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#13",
             "from": "stalled", "to": "merged",
             "reason": "merged outside the batch as PR #6667",
             "pr": 6667, "sha": "abc", "checks": {}}])
        self.assertNotIn("#13", [e["item"] for e in got["payload"]["ready"]])

    def test_a_retry_answer_resumes_without_a_read(self):
        rows = SPECCED + LANDED_STALL + [answered("ask-2", "retry", "#13")]
        got = self.next(rows, gh_=gh(landed=((6667, "abc"),)))
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual(self.gh_.called("pr", "list"), [])
        self.assertIn({"item": "#13", "step": "spec"},
                      got["payload"]["ready"])

    def test_a_failed_read_is_the_problem_and_nothing_is_written(self):
        got = self.next(SPECCED, gh_=gh(fail=["pr", "list"]))
        self.assertEqual((got["code"], got["out"]), (1, (
            "cd: gh pr list --head conductor/b1-13 --state merged failed:"
            " boom\ncd: 1 problem(s)\n")))
        self.assertEqual(got["rows"], [])


class TestMergedPr(unittest.TestCase):
    def test_reads_the_latest_merged_prs_number_and_commit(self):
        gh_ = gh(landed=((6667, "abc"), (6600, "old")))
        self.assertEqual(nxt.merged_pr(gh_, "conductor/b1-13"),
                         ({"pr": 6667, "sha": "abc"}, []))
        self.assertEqual(gh_.calls, [MERGED_CALL])

    def test_no_merged_pr_is_none_with_no_problem(self):
        self.assertEqual(nxt.merged_pr(gh(), "conductor/b1-13"), (None, []))

    def test_a_failed_read_is_the_problem(self):
        self.assertEqual(
            nxt.merged_pr(gh(fail=["pr", "list"]), "conductor/b1-13"),
            (None, ["gh pr list --head conductor/b1-13 --state merged"
                    " failed: boom"]))

    def test_an_unreadable_entry_is_the_problem(self):
        gh_ = FakeGh({("pr", "list"): json.dumps([{"number": "6667"}])})
        self.assertEqual(nxt.merged_pr(gh_, "conductor/b1-13"), (None, [
            "gh pr list --head conductor/b1-13 --state merged named an"
            " unreadable merged PR"]))


class TestDeliverNamesTheMergedPr(NextCase):
    """#938: with no open PR on the head, deliver looks for a merged one
    before creating a new one, and names it."""

    def deliver(self, gh_):
        self.body()
        self.git_ = FakeGit()
        return nxt.deliver(self.git_, gh_, self.wt, "conductor/b1-13",
                           "#13", "b1")

    def test_a_fresh_pr_names_the_merged_one_in_its_body(self):
        gh_ = gh(landed=((6667, "abc"),))
        self.assertIsNone(self.deliver(gh_))
        self.assertEqual(gh_.calls[-1], [
            "pr", "create", "--head", "conductor/b1-13", "--base", "main",
            "--title", "#13: conductor batch b1", "--body", CONTINUED])

    def test_without_one_the_body_file_is_sent_as_before(self):
        gh_ = gh()
        self.assertIsNone(self.deliver(gh_))
        self.assertEqual(gh_.calls[-1][-2:], ["--body-file", "Body\n"])

    def test_a_refusal_names_the_merged_pr(self):
        gh_ = gh(state="CLOSED", landed=((6667, "abc"),))
        self.assertEqual(self.deliver(gh_), (
            "refusing to open a PR for #13: the issue is already closed"
            " (PR #6667 merged outside the batch)"))
        self.assertEqual(gh_.called("pr", "create"), [])

    def test_an_open_pr_is_updated_without_the_merged_read(self):
        gh_ = gh(prs=(7,), landed=((6667, "abc"),))
        self.assertIsNone(self.deliver(gh_))
        self.assertEqual(gh_.called("pr", "list"), [
            ["pr", "list", "--head", "conductor/b1-13", "--state", "open",
             "--json", "number"]])

    def test_a_failed_merged_read_is_the_delivery_failure(self):
        gh_ = gh(fail=MERGED_CALL[:6])
        self.assertEqual(self.deliver(gh_), (
            "opening or updating the PR failed: gh pr list --head"
            " conductor/b1-13 --state merged failed: boom"))


if __name__ == "__main__":
    unittest.main()
