"""conductor_close.py (PRD-0013, WO-0162, WO-0163): the scorecard and
closing a batch. The scorecard is pure over the ledger's text and the
cost ledger's rows; close runs only through injected ports (FakeGit
and FakeGh) — no real push, PR or label — and tests assert the EXACT
problem strings and rows.
"""
import json
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from datetime import datetime, timezone
from pathlib import Path

import conductor
import conductor_close as close
import conductor_flow as flow
import conductor_run

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fake_gh import FakeGh  # noqa: E402
from fake_git import FakeGit  # noqa: E402

LEDGER = "docs/factory/batches/b1/ledger.jsonl"
COSTS = "docs/factory/costs.jsonl"
NOW = datetime(2026, 10, 10, 16, 0, tzinfo=timezone.utc)
POLICY = {"routing": {"mechanical": "h", "implementation": "s",
                      "architecture_review": "f"},
          "effort": {"mechanical": "low", "implementation": "medium",
                     "architecture_review": "high"}}


def at(hour, minute=0):
    return f"2026-10-10T{hour:02d}:{minute:02d}:00Z"


def plan_item(key, item_type):
    return {"item": key, "type": item_type, "size": "M", "steps": [],
            "estimate_usd": 10, "after": []}


PLAN = {"at": at(10), "kind": "plan", "item": None, "batch": "b1",
        "items": [plan_item("#12", "feature"), plan_item("#13", "fix"),
                  plan_item("#14", "order")],
        "policy": POLICY, "estimate_usd": 40, "month_to_date_usd": 0.0,
        "cap_usd": 300}


def ask(ask_id, key, ask_kind, when, options=("approve", "block"),
        covers=None):
    row = {"at": when, "kind": "ask", "item": key, "id": ask_id,
           "ask_kind": ask_kind, "question": "Q?", "options": list(options),
           "recommended": options[0], "why": "w"}
    if covers:
        row["covers"] = list(covers)
    return row


def answer(ask_id, choice, when, key=None):
    return {"at": when, "kind": "answer", "item": key, "ask": ask_id,
            "choice": choice, "note": ""}


def state(key, frm, to, when, reason="r", **extra):
    return {"at": when, "kind": "state", "item": key, "from": frm, "to": to,
            "reason": reason, **extra}


def run(key, step, band, model, effort, reported, outcome="completed"):
    return {"at": at(11), "kind": "run", "item": key, "step": step,
            "charter": "c", "band": band, "model": model,
            "models_reported": reported, "effort": effort,
            "run_id": f"conductor-b1-{key[1:]}-{step}-1", "pid": 7,
            "outcome": outcome}


def merged(key, when):
    return state(key, "merging", "merged", when, pr=1, sha="abc",
                 checks={"ci": "success"})


# A closed-out batch: #12 and #14 merged on a train, #13 blocked after a
# second request for changes. Five runs: three on policy, one on the
# wrong effort, one whose passed model the harness never reported.
ROWS = [
    PLAN,
    ask("ask-1", None, "spend", at(10), ("approve", "decline")),
    answer("ask-1", "approve", at(10, 30)),
    {"at": at(10), "kind": "reserve", "item": "#12", "what": "adr",
     "values": [91, 92]},
    run("#12", "spec", "architecture_review", "f", "high", ["f"]),
    ask("ask-2", "#12", "gate", at(11)),
    answer("ask-2", "approve", at(12), "#12"),
    run("#12", "build", "implementation", "s", "low", ["s"]),
    run("#14", "build", "implementation", "s", "medium", ["s", "h"]),
    run("#14", "review", "architecture_review", "f", "high", ["s"]),
    run("#13", "spec", "architecture_review", "f", "high", ["f"],
        outcome="agent-failed"),
    state("#13", "review", "build", at(11), "the reviewer requested"
          " changes; one fix step"),
    state("#13", "review", "stalled", at(12), flow.CHANGES_AGAIN),
    ask("ask-3", "#13", "stall", at(12), ("retry", "retry-up", "block")),
    answer("ask-3", "block", at(12, 30), "#13"),
    state("#13", "stalled", "blocked", at(12, 30), "answer to ask-3: block"),
    ask("ask-4", None, "merge", at(13), ("train", "one-by-one"),
        covers=["#14", "#12"]),
    answer("ask-4", "train", at(13, 30)),
    {"at": at(14), "kind": "reserve", "item": "#12", "what": "adr",
     "values": [95, 96], "renumbered_from": [91, 92]},
    merged("#14", at(14)),
    merged("#12", at(15)),
]


def spend(run_id, cost, wo="#12"):
    return {"wo": wo, "run_id": run_id, "model": "s", "tokens": 10,
            "cost": cost, "outcome": "completed", "at": "2026-10-10"}


SPEND = [spend("conductor-b1-12-spec-1", 2.0),
         spend("conductor-b1-12-build-1", 4.0, "WO-0001"),
         spend("conductor-b1-14-build-1", 3.0, "WO-0002"),
         spend("conductor-b1-14-review-1", 1.5, "#14"),
         spend("conductor-b1-13-spec-1", 0.5, "#13"),
         spend("unrelated-run", 99.0, "WO-0003")]


def lines(rows):
    return "".join(json.dumps(row) + "\n" for row in rows)


def write(root, ledger=None, costs=None):
    root = Path(root)
    if ledger is not None:
        path = root / LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(ledger, encoding="utf-8")
    if costs is not None:
        path = root / COSTS
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(costs, encoding="utf-8")


EXPECTED = {
    "batch": "b1", "at": "2026-10-10T16:00:00Z", "items": 3, "merged": 2,
    "blocked": 1, "owner_touches_per_merged": 2.0, "metered_usd": 11.0,
    "metered_usd_per_merged": 5.5, "estimate_usd": 40,
    "estimate_error_pct": -72.5, "collisions": 2, "stalls": 1,
    "escalations": 1, "review_changes_per_item": 0.6667,
    "start_to_last_merge_s": 18000, "merged_per_owner_wait_hour": 0.8,
    "policy_compliance": 0.6, "conductor_session": "unmetered"}


class TestScorecard(unittest.TestCase):
    def score(self, ledger, spend_rows=SPEND):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, ledger, lines(spend_rows))
            return close.scorecard(tmp, "b1", NOW)

    def test_every_field_comes_from_the_ledger_and_its_costs(self):
        self.assertEqual(self.score(lines(ROWS)), (EXPECTED, []))

    def test_nothing_merged_reports_no_per_merged_ratios(self):
        rows = [row for row in ROWS if row.get("to") != "merged"]
        card, problems = self.score(lines(rows))
        self.assertEqual(problems, [])
        self.assertEqual(
            {key: card[key] for key in (
                "merged", "owner_touches_per_merged",
                "metered_usd_per_merged", "start_to_last_merge_s",
                "merged_per_owner_wait_hour")},
            {"merged": 0, "owner_touches_per_merged": None,
             "metered_usd_per_merged": None, "start_to_last_merge_s": None,
             "merged_per_owner_wait_hour": 0.0})

    def test_a_line_that_does_not_parse_fails_naming_file_and_line(self):
        text = lines(ROWS[:2]) + "{not json\n" + lines(ROWS[2:])
        self.assertEqual(self.score(text), (None, [
            f"cd: {LEDGER}:3 is not valid JSON: Expecting property name"
            " enclosed in double quotes: line 1 column 2 (char 1)"]))

    def test_a_row_breaking_its_kinds_rules_fails(self):
        broken = {key: value for key, value in ROWS[4].items()
                  if key != "outcome"}
        text = lines(ROWS[:4] + [broken] + ROWS[5:])
        self.assertEqual(self.score(text), (None, [
            f"cd: {LEDGER}:5 run row is missing field(s): outcome"]))

    def test_a_run_with_no_spend_row_fails_naming_its_line(self):
        text = "\n" + lines(ROWS)
        self.assertEqual(self.score(text, SPEND[:3] + SPEND[4:]), (None, [
            f"cd: {LEDGER}:11 run conductor-b1-14-review-1 has no {COSTS}"
            " row with its run_id"]))

    def test_a_missing_plan_row_fails(self):
        self.assertEqual(self.score(lines(ROWS[1:])), (None, [
            f"cd: {LEDGER} has no plan row"]))

    def test_an_unreadable_cost_ledger_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, lines(ROWS), lines(SPEND) + "nope\n")
            self.assertEqual(close.scorecard(tmp, "b1", NOW), (None, [
                f"ledger: {COSTS}:7 is not valid JSON: Expecting value:"
                " line 1 column 1 (char 0)"]))


class TestScorecardCli(unittest.TestCase):
    def main(self, root, argv):
        return cli_contract.capture(conductor.main, argv, env={},
                                    clock=lambda: NOW, root=root)

    def test_prints_the_scorecard_row_and_appends_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, lines(ROWS), lines(SPEND))
            code, out = self.main(tmp, ["scorecard", "b1"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out[:out.rindex("}") + 1]), EXPECTED)
            self.assertFalse((Path(tmp) / close.SCORECARDS).exists())

    def test_a_malformed_ledger_exits_nonzero_with_no_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, lines(ROWS[1:]), lines(SPEND))
            code, out = self.main(tmp, ["scorecard", "b1"])
            self.assertEqual((code, out),
                             (1, f"cd: {LEDGER} has no plan row\n"
                                 "cd: 1 problem(s)\n"))
            self.assertFalse((Path(tmp) / close.SCORECARDS).exists())


# --- closing a batch (WO-0163), through FakeGit and FakeGh ------------

BLOCKED_SPEND = [spend("conductor-b1-13-spec-1", 0.5, "#13"),
                 spend("conductor-b1-13-build-1", 0.0, "#13")]
CARD = '{"batch": "b0"}\n'
LABEL_LIST = ("label", "list")
LABEL_LIST_CALL = ["label", "list", "--json", "name,color,description",
                   "--limit", "1000"]
HAS_NEEDS_HUMAN = json.dumps([{"name": "bug"}, {"name": "needs-human"}])
# Git's whole stderr for a merge a dirty tracked file refuses (#726):
# its last line alone, "Aborting", hides the reason.
DIRTY_MERGE = subprocess.CalledProcessError(
    1, "git", stderr="error: Your local changes to the following files"
    " would be overwritten by merge:\n\ttools/factory/__pycache__/cli.pyc\n"
    "Please commit your changes or stash them before you merge.\n"
    "Aborting\n")


# The blocked item's commits beyond origin/main: only its spend rows,
# which close carries into costs.jsonl (#728 item 2), or real work too.
COST_ONLY_LOG = "".join(f"{conductor_run.SPEND_SUBJECT}{entry['run_id']}\n"
                        for entry in BLOCKED_SPEND)
WORK_LOG = "feat: the blueprint\n" + COST_ONLY_LOG


BRANCH_SHA = "5bed5e"
LEASED_DELETE = ["push", "--force-with-lease=refs/heads/conductor/b1-13:"
                 f"{BRANCH_SHA}", "origin", ":refs/heads/conductor/b1-13"]


def head_call(root):
    return ("-C", str(root), "rev-parse", "conductor/b1-13")


def ls_call(root):
    return ("-C", str(root), "ls-tree", "--name-only", "conductor/b1-13",
            "--", COSTS)


def log_call(root):
    return ("-C", str(root), "log", "--format=%s",
            f"origin/main..{BRANCH_SHA}")


class TestClose(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        (self.root / close.SCORECARDS).parent.mkdir(parents=True)
        (self.root / close.SCORECARDS).write_text(CARD, encoding="utf-8")

    def close(self, rows, costs=SPEND[:4] + SPEND[5:], git=None, gh=None,
              branch_costs=BLOCKED_SPEND, branch_log=COST_ONLY_LOG):
        write(self.root, lines(rows), lines(costs))
        self.git = git or FakeGit({
            ("-C", str(self.root), "show",
             f"conductor/b1-13:{COSTS}"): lines(branch_costs),
            ls_call(self.root): COSTS + "\n",
            head_call(self.root): BRANCH_SHA + "\n",
            log_call(self.root): branch_log})
        self.gh = gh or FakeGh({LABEL_LIST: HAS_NEEDS_HUMAN})
        return close.close_batch(self.root, "b1", lambda: NOW,
                                 self.git, self.gh)

    def ledger(self):
        return [json.loads(line) for line in
                (self.root / LEDGER).read_text().splitlines()]

    def test_close_carries_blocked_spend_scores_commits_and_asks(self):
        summary, problems = self.close(ROWS)
        self.assertEqual(problems, [])
        self.assertEqual(summary, {"batch": "b1", "merged": ["#12", "#14"],
                                   "blocked": ["#13"], "ask": "ask-5"})
        costs = (self.root / COSTS).read_text().splitlines()
        self.assertEqual([json.loads(line)["run_id"] for line in costs[-2:]],
                         ["conductor-b1-13-spec-1", "conductor-b1-13-build-1"])
        cards = (self.root / close.SCORECARDS).read_text().splitlines()
        self.assertEqual(cards[0] + "\n", CARD)
        self.assertEqual(json.loads(cards[1]), EXPECTED)
        self.assertEqual(self.ledger()[-2:], [
            {"at": "2026-10-10T16:00:00Z", "kind": "close", "item": None,
             "merged": ["#12", "#14"], "blocked": ["#13"]},
            {"at": "2026-10-10T16:00:00Z", "kind": "ask", "item": None,
             "id": "ask-5", "ask_kind": "merge",
             "question": "Merge batch b1's closing PR (conductor/b1): its"
                         " ledger, run evidence and scorecard?",
             "options": ["merge", "hold"], "recommended": "merge",
             "why": "every item is merged or blocked, and the scorecard"
                    " computed from the ledger"}])
        here = ["-C", str(self.root)]
        self.assertEqual(self.git.calls, [
            here + ["fetch", "origin", "main"],
            here + ["merge", "--no-edit", "origin/main"],
            here + ["ls-tree", "--name-only", "conductor/b1-13", "--", COSTS],
            here + ["show", f"conductor/b1-13:{COSTS}"],
            here + ["rev-parse", "conductor/b1-13"],
            here + ["log", "--format=%s", f"origin/main..{BRANCH_SHA}"],
            here + ["add", "--", "docs/factory/batches/b1", COSTS,
                    close.SCORECARDS],
            here + ["commit", "-m", "chore(conductor): close batch b1"],
            here + ["push", "-u", "origin", "conductor/b1"],
            here + LEASED_DELETE])
        self.assertEqual(self.gh.calls, [
            LABEL_LIST_CALL,
            ["pr", "create", "--head", "conductor/b1", "--base", "main",
             "--title", "conductor batch b1: ledger and scorecard",
             "--body", "Conductor batch b1's closing PR: its batch"
             " ledger, run evidence, scorecard, and the spend rows of its"
             " blocked items (#13).\n\nCloses #12\nCloses #14\n\nNo work"
             " order: the Conductor's closing PR for batch b1."],
            ["issue", "edit", "13", "--add-label", "needs-human"],
            ["issue", "comment", "13", "--body", "Blocked in conductor"
             " batch b1: answer to ask-3: block"]])

    def test_a_branch_holding_real_work_is_kept_and_named(self):
        # #728 item 2: a branch with a blueprint is worth keeping, and
        # the Owner is told where it is.
        summary, problems = self.close(ROWS, branch_log=WORK_LOG)
        self.assertEqual(problems, [])
        self.assertEqual(self.git.called("-C", str(self.root), "push",
                                         LEASED_DELETE[1]), [])
        self.assertEqual(self.gh.calls[1][-1], "Conductor batch b1's closing"
                         " PR: its batch ledger, run evidence, scorecard,"
                         " and the spend rows of its blocked items (#13)."
                         "\n\nKept on origin, holding work beyond spend"
                         " rows: conductor/b1-13.\n\nCloses #12\nCloses"
                         " #14\n\nNo work order: the Conductor's closing PR"
                         " for batch b1.")
        self.assertEqual(self.gh.calls[-1], [
            "issue", "comment", "13", "--body", "Blocked in conductor batch"
            " b1: answer to ask-3: block. Its branch conductor/b1-13 is kept"
            " on origin: it holds work beyond its spend rows."])

    def test_a_branch_with_nothing_beyond_main_is_left_alone(self):
        summary, problems = self.close(ROWS, branch_log="")
        self.assertEqual(problems, [])
        self.assertEqual(self.git.called("-C", str(self.root), "push",
                                         LEASED_DELETE[1]), [])
        self.assertNotIn("Kept on origin", self.gh.calls[1][-1])

    def test_an_unreadable_branch_log_refuses_the_close(self):
        fake = FakeGit({("-C", str(self.root), "show",
                         f"conductor/b1-13:{COSTS}"): lines(BLOCKED_SPEND),
                        ls_call(self.root): COSTS + "\n",
                        head_call(self.root): BRANCH_SHA + "\n"},
                       failing=list(log_call(self.root)))
        self.assertEqual(self.close(ROWS, git=fake), (None, [
            "cd: close refused: reading conductor/b1-13's commits failed:"
            " fatal: rejected"]))
        self.assertEqual(fake.called("-C", str(self.root), "commit"), [])

    def test_the_delete_is_leased_on_the_inspected_sha(self):
        # A commit on origin's branch that the local ref lacks was never
        # inspected; the lease makes git refuse the delete then.
        self.close(ROWS)
        self.assertEqual(self.git.called("-C", str(self.root), "push",
                                         LEASED_DELETE[1]),
                         [["-C", str(self.root), *LEASED_DELETE]])

    def test_a_refused_delete_is_reported_after_the_pr(self):
        stale = subprocess.CalledProcessError(
            1, "git", stderr=" ! [rejected] (stale info)\n")
        fake = FakeGit({("-C", str(self.root), "show",
                         f"conductor/b1-13:{COSTS}"): lines(BLOCKED_SPEND),
                        ls_call(self.root): COSTS + "\n",
                        head_call(self.root): BRANCH_SHA + "\n",
                        log_call(self.root): COST_ONLY_LOG},
                       failing=["-C", str(self.root), *LEASED_DELETE],
                       error=stale)
        summary, problems = self.close(ROWS, git=fake)
        self.assertEqual(problems, [
            "cd: close: deleting origin's conductor/b1-13 failed:"
            " ! [rejected] (stale info); delete it by hand"])
        self.assertEqual([call[:2] for call in self.gh.calls],
                         [list(LABEL_LIST), ["pr", "create"],
                          ["issue", "edit"], ["issue", "comment"]])

    def test_a_prefix_sharing_batchs_spend_row_is_not_carried(self):
        # Batch b1-13-x's item #5 shares #13's old prefix conductor-b1-13-
        # (#735); its spend row on #13's branch is not this batch's.
        other = spend("conductor-b1-13-x-5-spec-1", 7.0, "#5")
        summary, problems = self.close(
            ROWS, branch_costs=BLOCKED_SPEND + [other])
        self.assertEqual(problems, [])
        costs = (self.root / COSTS).read_text().splitlines()
        self.assertEqual([json.loads(line)["run_id"] for line in costs[-2:]],
                         ["conductor-b1-13-spec-1", "conductor-b1-13-build-1"])

    def test_a_workers_own_cost_commit_keeps_the_branch(self):
        # #771: a Worker's `chore(cost): ...` commit is real work, not
        # one of this item's spend commits; deleting the branch loses it.
        worker = "chore(cost): raise the default monthly cap\n"
        summary, problems = self.close(ROWS, branch_log=worker + COST_ONLY_LOG)
        self.assertEqual(problems, [])
        self.assertEqual(self.git.called("-C", str(self.root), "push",
                                         LEASED_DELETE[1]), [])
        self.assertIn("Kept on origin", self.gh.calls[1][-1])

    def test_another_batchs_spend_commit_keeps_the_branch(self):
        # #771: carry does not carry that run's rows, so they are not on
        # the batch branch; the commit is not this item's spend.
        other = f"{conductor_run.SPEND_SUBJECT}conductor-oct-1-build-1\n"
        summary, problems = self.close(ROWS, branch_log=other + COST_ONLY_LOG)
        self.assertEqual(problems, [])
        self.assertEqual(self.git.called("-C", str(self.root), "push",
                                         LEASED_DELETE[1]), [])

    def test_a_blocked_branch_with_no_cost_ledger_carries_nothing(self):
        # #772: nothing seeds costs.jsonl in a consumer repo (#708), so a
        # branch with no spend commit has no ledger; an absent ledger
        # holds no rows, and the close goes on.
        fake = FakeGit({ls_call(self.root): "",
                        head_call(self.root): BRANCH_SHA + "\n",
                        log_call(self.root): ""},
                       failing=["-C", str(self.root), "show"])
        # #13's rows already reached the batch branch, so the scorecard
        # computes; the branch adds none.
        costs = SPEND[:4] + SPEND[5:] + BLOCKED_SPEND
        summary, problems = self.close(ROWS, costs=costs, git=fake)
        self.assertEqual(problems, [])
        self.assertEqual((self.root / COSTS).read_text(), lines(costs))

    def test_a_failing_scorecard_leaves_scorecards_byte_identical(self):
        summary, problems = self.close(ROWS, costs=SPEND[:3])
        self.assertIsNone(summary)
        self.assertEqual(problems, [
            f"cd: {LEDGER}:10 run conductor-b1-14-review-1 has no {COSTS}"
            " row with its run_id"])
        self.assertEqual((self.root / close.SCORECARDS).read_bytes(),
                         CARD.encode())
        self.assertEqual(self.ledger(), ROWS)
        self.assertEqual(self.git.called("-C", str(self.root), "commit"), [])
        self.assertEqual(self.gh.calls, [])

    def test_a_batch_with_an_item_in_flight_is_refused(self):
        rows = ROWS[:-1] + [state("#12", "ship", "merging", at(15))]
        summary, problems = self.close(rows)
        self.assertEqual((summary, problems), (None, [
            "cd: close refused: #12 is merging, not merged or blocked"]))
        self.assertEqual(self.git.calls, [])

    def test_a_closed_batch_is_refused(self):
        rows = ROWS + [{"at": at(16), "kind": "close", "item": None,
                        "merged": ["#12", "#14"], "blocked": ["#13"]}]
        self.assertEqual(self.close(rows), (None, [
            "cd: close refused: batch b1 is already closed"]))

    def test_carried_spend_is_never_appended_twice(self):
        summary, problems = self.close(ROWS, costs=SPEND,
                                       branch_costs=BLOCKED_SPEND[:1])
        self.assertEqual(problems, [])
        self.assertEqual((self.root / COSTS).read_text(), lines(SPEND))

    def test_carried_spend_dedups_on_row_key_not_run_id(self):
        # #736: ADR-0049 made (wo, run_id) the identity; a row sharing
        # only the run_id is a different row and must still be carried.
        other = spend("conductor-b1-13-spec-1", 0.5, "#99")
        costs = SPEND[:4] + SPEND[5:] + [other]
        summary, problems = self.close(ROWS, costs=costs)
        self.assertEqual(problems, [])
        self.assertEqual((self.root / COSTS).read_text(),
                         lines(costs + BLOCKED_SPEND))

    def test_a_retry_after_a_failed_close_record_scores_once(self):
        # Review minor 6: the scorecard was appended before the close
        # row, so a failed ledger write left it on disk, and the retry
        # appended a second row to the append-only history.
        failed = (None, [f"cd: cannot write {LEDGER}: disk full"])
        with unittest.mock.patch.object(close, "_record_close",
                                        return_value=failed):
            self.assertEqual(self.close(ROWS), failed)
        summary, problems = self.close(self.ledger())
        self.assertEqual(problems, [])
        cards = (self.root / close.SCORECARDS).read_text().splitlines()
        self.assertEqual(cards[0] + "\n", CARD)
        self.assertEqual([json.loads(card) for card in cards[1:]],
                         [EXPECTED])
        self.assertEqual(self.ledger()[-2]["kind"], "close")

    def test_a_merge_conflict_with_main_refuses_and_aborts(self):
        fake = FakeGit(failing=["-C", str(self.root), "merge", "--no-edit"])
        summary, problems = self.close(ROWS, git=fake)
        self.assertEqual((summary, problems), (None, [
            "cd: close refused: merging origin/main into conductor/b1"
            " failed: fatal: rejected"]))
        self.assertEqual(fake.calls[-1],
                         ["-C", str(self.root), "merge", "--abort"])
        self.assertEqual((self.root / close.SCORECARDS).read_bytes(),
                         CARD.encode())

    def test_a_refused_merge_names_gits_whole_reason(self):
        fake = FakeGit(failing=["-C", str(self.root), "merge", "--no-edit"],
                       error=DIRTY_MERGE)
        self.assertEqual(self.close(ROWS, git=fake), (None, [
            "cd: close refused: merging origin/main into conductor/b1"
            " failed: error: Your local changes to the following files"
            " would be overwritten by merge: |"
            " tools/factory/__pycache__/cli.pyc | Please commit your"
            " changes or stash them before you merge. | Aborting"]))

    def test_a_missing_needs_human_label_is_created_before_use(self):
        # #726: a tools-only stamp never syncs labels.json, so the label
        # close writes may not exist; gh issue edit then fails.
        gh = FakeGh({LABEL_LIST: json.dumps([{"name": "bug"}])})
        summary, problems = self.close(ROWS, gh=gh)
        self.assertEqual(problems, [])
        self.assertEqual([call[:3] for call in gh.calls], [
            LABEL_LIST_CALL[:3], ["pr", "create", "--head"],
            ["label", "create", "needs-human"],
            ["issue", "edit", "13"], ["issue", "comment", "13"]])
        self.assertEqual(gh.calls[2], ["label", "create", "needs-human"])

    def test_no_blocked_item_reads_no_labels(self):
        rows = [row for row in ROWS if row.get("item") != "#13"]
        rows[0] = dict(PLAN, items=[plan_item("#12", "feature"),
                                    plan_item("#14", "order")])
        summary, problems = self.close(rows, costs=SPEND[:4])
        self.assertEqual(problems, [])
        self.assertEqual([call[:2] for call in self.gh.calls],
                         [["pr", "create"]])

    def test_an_unreadable_label_list_opens_no_pr(self):
        gh = FakeGh(failing=["label", "list"])
        summary, problems = self.close(ROWS, gh=gh)
        self.assertEqual(problems, [
            "cd: close: gh label list failed: boom; finish the PR and the"
            " needs-human labels by hand"])
        self.assertEqual(gh.calls, [LABEL_LIST_CALL])

    def test_a_failed_push_is_reported_after_the_close_is_recorded(self):
        fake = FakeGit({("-C", str(self.root), "show",
                         f"conductor/b1-13:{COSTS}"): lines(BLOCKED_SPEND),
                        ls_call(self.root): COSTS + "\n",
                        head_call(self.root): BRANCH_SHA + "\n",
                        log_call(self.root): COST_ONLY_LOG},
                       failing=["-C", str(self.root), "push"])
        summary, problems = self.close(ROWS, git=fake)
        self.assertEqual(problems, [
            "cd: close: pushing conductor/b1 failed: fatal: rejected; finish"
            " the"
            " push, the PR and the needs-human labels by hand"])
        self.assertEqual(self.ledger()[-2]["kind"], "close")
        self.assertEqual(self.gh.calls, [])


CLOSED = ROWS + [
    {"at": at(16), "kind": "close", "item": None,
     "merged": ["#12", "#14"], "blocked": ["#13"]},
    ask("ask-5", None, "merge", at(16), ("merge", "hold"))]
CHECKS = ("api", "repos/{owner}/{repo}/commits/c105ed/check-runs"
          "?per_page=100")
GREEN_GH = {
    ("pr", "list", "--head", "conductor/b1"): json.dumps([{"number": 6}]),
    CHECKS: json.dumps({"check_runs": [{"name": "ci", "status": "completed",
                                         "conclusion": "success"}]}),
    ("api", "graphql"): json.dumps(
        {"data": {"repository": {"mergeQueue": None}}}),
    ("pr", "view", "6"): json.dumps({"state": "MERGED",
                                     "mergeCommit": {"oid": "m3r6ed"}})}


class TestClosingMerge(unittest.TestCase):
    """#726: the closing ask's answer is committed to the batch branch
    and pushed before the closing PR merges, so the merged ledger holds
    the answer that authorised its own merge."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.here = ["-C", str(self.root)]

    def merge(self, rows, dirty=True, gh=None, mains=("a11ce0",)):
        """`mains` is what each successive read of origin/main answers:
        a second value is main moving while the checks ran."""
        write(self.root, lines(rows))
        heads = [f"{sha}\n" for sha in mains]
        self.git = FakeGit({
            (*self.here, "status", "--porcelain"):
                f" M {LEDGER}\n" if dirty else "",
            (*self.here, "rev-parse", "origin/main"):
                lambda args: heads.pop(0) if len(heads) > 1 else heads[0],
            (*self.here, "rev-parse", "HEAD"): "c105ed\n"})
        self.gh = gh or FakeGh(GREEN_GH)
        return close.merge_closing(self.root, "b1", lambda: NOW,
                                   self.git, self.gh,
                                   lambda seconds: None)

    def test_the_answer_is_pushed_before_the_closing_pr_merges(self):
        rows = CLOSED + [answer("ask-5", "merge", at(17))]
        self.assertEqual(self.merge(rows), (
            {"batch": "b1", "pr": 6, "sha": "m3r6ed"}, []))
        self.assertEqual(self.git.calls, [
            self.here + ["status", "--porcelain", "--",
                         "docs/factory/batches/b1"],
            self.here + ["add", "--", "docs/factory/batches/b1"],
            self.here + ["commit", "-m", "chore(conductor): record batch"
                         " b1's closing answer"],
            self.here + ["fetch", "origin", "main"],
            self.here + ["merge", "--no-edit", "origin/main"],
            self.here + ["rev-parse", "origin/main"],
            self.here + ["push", "origin", "conductor/b1"],
            self.here + ["rev-parse", "HEAD"],
            self.here + ["fetch", "origin", "main"],
            self.here + ["rev-parse", "origin/main"]])
        self.assertEqual(self.gh.calls[-2], [
            "pr", "merge", "6", "--squash", "--match-head-commit",
            "c105ed"])

    def test_an_answer_already_pushed_commits_nothing(self):
        rows = CLOSED + [answer("ask-5", "merge", at(17))]
        summary, problems = self.merge(rows, dirty=False)
        self.assertEqual(problems, [])
        self.assertEqual([call[2] for call in self.git.calls],
                         ["status", "fetch", "merge", "rev-parse", "push",
                          "rev-parse", "fetch", "rev-parse"])

    def test_main_moving_while_the_checks_ran_lands_nothing(self):
        # #770: without a merge queue the squash lands on whatever main
        # is, so checks on a head that never had that main merged in
        # must not land it (ADR-0086).
        rows = CLOSED + [answer("ask-5", "merge", at(17))]
        self.assertEqual(self.merge(rows, mains=("a11ce0", "b0b0b0")), (
            None, ["cd: closing merge: origin/main moved from a11ce0 to"
                   " b0b0b0 while the checks ran; a retry merges it in"
                   " and checks again"]))
        self.assertFalse(self.gh.called("pr", "merge"))

    def test_a_conflict_with_main_lands_nothing(self):
        rows = CLOSED + [answer("ask-5", "merge", at(17))]
        write(self.root, lines(rows))
        self.git = FakeGit(failing=[*self.here, "merge", "--no-edit"])
        self.gh = FakeGh(GREEN_GH)
        self.assertEqual(close.merge_closing(
            self.root, "b1", lambda: NOW, self.git, self.gh,
            lambda seconds: None), (None, [
                "cd: closing merge: merging origin/main into conductor/b1"
                " failed: fatal: rejected"]))
        self.assertIn(self.here + ["merge", "--abort"], self.git.calls)
        self.assertEqual(self.gh.calls, [])

    def test_an_unanswered_closing_ask_is_refused(self):
        self.assertEqual(self.merge(CLOSED), (None, [
            "cd: closing merge refused: ask-5 is unanswered"]))
        self.assertEqual((self.git.calls, self.gh.calls), ([], []))

    def test_a_hold_answer_is_refused(self):
        rows = CLOSED + [answer("ask-5", "hold", at(17))]
        self.assertEqual(self.merge(rows), (None, [
            "cd: closing merge refused: ask-5 was answered hold, not"
            " merge"]))
        self.assertEqual(self.gh.calls, [])

    def test_an_open_batch_is_refused(self):
        self.assertEqual(self.merge(ROWS), (None, [
            "cd: closing merge refused: batch b1 is not closed"]))

    def test_red_checks_merge_nothing(self):
        red = {**GREEN_GH, CHECKS: json.dumps({"check_runs": [
            {"name": "ci", "status": "completed",
             "conclusion": "failure"}]})}
        rows = CLOSED + [answer("ask-5", "merge", at(17))]
        self.assertEqual(self.merge(rows, gh=FakeGh(red)), (None, [
            "cd: closing merge: checks failed on c105ed: ci"]))
        self.assertFalse(self.gh.called("pr", "merge"))

    def test_the_cli_merges_and_prints(self):
        rows = CLOSED + [answer("ask-5", "merge", at(17))]
        write(self.root, lines(rows))
        git = FakeGit({(*self.here, "rev-parse", "HEAD"): "c105ed\n",
                       (*self.here, "rev-parse", "origin/main"):
                           "a11ce0\n"})
        code, out = cli_contract.capture(
            conductor.main, ["close", "b1", "--merge"], env={},
            clock=lambda: NOW, root=self.root, run=FakeGh(GREEN_GH),
            git=git, sleep=lambda seconds: None)
        self.assertEqual((code, out), (0, (
            "cd: merged batch b1's closing PR #6 as m3r6ed\n"
            "cd: 0 problem(s)\n")))


class TestCloseCli(unittest.TestCase):
    def test_close_prints_its_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, lines(ROWS), lines(SPEND))
            fake = FakeGit({head_call(tmp): BRANCH_SHA + "\n"})
            code, out = cli_contract.capture(
                conductor.main, ["close", "b1"], env={}, clock=lambda: NOW,
                root=tmp, run=FakeGh({LABEL_LIST: HAS_NEEDS_HUMAN}),
                git=fake)
            self.assertEqual((code, out), (0, (
                "cd: closed batch b1: merged #12, #14; blocked #13;"
                " merge ask ask-5\ncd: 0 problem(s)\n")))


if __name__ == "__main__":
    unittest.main()
