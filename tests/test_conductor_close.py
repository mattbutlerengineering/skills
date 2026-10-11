"""conductor_close.py (PRD-0013, WO-0162, WO-0163): the scorecard and
closing a batch. The scorecard is pure over the ledger's text and the
cost ledger's rows; close runs only through injected ports (a recording
git and FakeGh) — no real push, PR or label — and tests assert the EXACT
problem strings and rows.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import conductor
import conductor_close as close
import conductor_flow as flow

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fake_gh import FakeGh  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
