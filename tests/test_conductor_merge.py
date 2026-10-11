"""conductor_merge.py (PRD-0013, WO-0160, WO-0161): the merge
precondition and the merge turn. The precondition is pure over ledger
rows and the branch's gate blobs; the merge turn runs only through
injected ports (a scratch git repo with a local bare origin, FakeGh, a
fake tool runner and clock) — no real PR, push or merge — and tests
assert the EXACT problem strings and rows.
"""
import sys
import unittest
from pathlib import Path

import conductor_merge as merge

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_flow import (AT, START, answered, launch,  # noqa: E402
                                 moved, ran, run_id)

ADR = "docs/adr/0090-x.md"


def ask(ask_id, key, ask_kind, options, covers=None, gate_blobs=None):
    row = {"at": AT, "kind": "ask", "item": key, "id": ask_id,
           "ask_kind": ask_kind, "question": "Q?", "options": list(options),
           "recommended": options[0], "why": "w"}
    if covers:
        row["covers"] = list(covers)
    if gate_blobs is not None:
        row["gate_blobs"] = gate_blobs
    return row


def reviewed(key, authors, reviewer, verdict="pass"):
    return moved(key, "review", "reviewed", verdict=verdict,
                 author_runs=authors, reviewer_run=reviewer)


def order_shipped(key="#14"):
    """An order item's rows through a completed ship step."""
    return [launch(key, "planned", "build"), ran(key, "build"),
            launch(key, "build", "verify"), ran(key, "verify"),
            launch(key, "verify", "review"), ran(key, "review"),
            reviewed(key, [run_id(key, "build"), run_id(key, "verify")],
                     run_id(key, "review")),
            launch(key, "reviewed", "ship"), ran(key, "ship")]


def feature_shipped(blobs, key="#12"):
    """A feature item's rows through a completed ship step, with its gate
    ask (asked as ask-9) approved over these gate blobs."""
    return [launch(key, "planned", "spec"), ran(key, "spec"),
            moved(key, "spec", "awaiting-gate"),
            ask("ask-9", key, "gate", ["approve", "block"],
                gate_blobs=blobs),
            answered("ask-9", "approve", key),
            launch(key, "awaiting-gate", "build")] + order_shipped(key)[1:]


def own(ask_id, key, choice="merge"):
    return [ask(ask_id, key, "merge", ["merge", "block"]),
            answered(ask_id, choice, key)]


def train(ask_id, covers, choice="train"):
    return [ask(ask_id, None, "merge", ["train", "one-by-one"],
                covers=covers), answered(ask_id, choice)]


class TestMergePrecondition(unittest.TestCase):
    def problems(self, rows, key="#14", blobs=None):
        return merge.merge_problems(START + rows, key, blobs or {})

    def test_a_reviewed_shipped_item_with_its_own_answer_may_merge(self):
        self.assertEqual(self.problems(order_shipped() + own("ask-2", "#14")),
                         [])

    def test_an_item_never_reviewed_is_refused(self):
        rows = order_shipped()[:6] + own("ask-2", "#14")
        self.assertEqual(self.problems(rows),
                         ["cd: merge refused: #14 has no reviewed pass"])

    def test_a_reviewer_among_the_author_runs_is_refused(self):
        rows = order_shipped()
        rows[6] = reviewed("#14", [run_id("#14", "build")],
                           run_id("#14", "verify"))
        self.assertEqual(
            self.problems(rows + own("ask-2", "#14")),
            ["cd: merge refused: #14's reviewer run conductor-b1-14-verify-1"
             " is among its author runs"])

    def test_an_unfinished_ship_step_is_refused(self):
        rows = order_shipped()[:-1] + own("ask-2", "#14")
        self.assertEqual(self.problems(rows),
                         ["cd: merge refused: #14's ship step has not"
                          " completed"])

    def test_an_item_with_no_covering_answer_is_refused(self):
        self.assertEqual(self.problems(order_shipped()),
                         ["cd: merge refused: no merge answer covers #14"])

    def test_an_own_ask_answered_otherwise_does_not_cover(self):
        rows = order_shipped() + [ask("ask-2", "#14", "merge",
                                      ["merge", "hold"]),
                                  answered("ask-2", "hold", "#14")]
        self.assertEqual(self.problems(rows),
                         ["cd: merge refused: no merge answer covers #14"])

    def test_an_unanswered_merge_ask_is_refused(self):
        rows = order_shipped() + own("ask-2", "#14")[:1]
        self.assertEqual(self.problems(rows),
                         ["cd: #14 has an unanswered ask (ask-2)"])

    def test_a_train_covers_its_first_item(self):
        rows = order_shipped() + train("ask-2", ["#14", "#13"])
        self.assertEqual(self.problems(rows), [])

    def test_a_train_answered_otherwise_does_not_cover(self):
        rows = order_shipped() + train("ask-2", ["#14"], "one-by-one")
        self.assertEqual(self.problems(rows),
                         ["cd: merge refused: no merge answer covers #14"])

    def test_a_train_waits_for_every_earlier_item_to_merge(self):
        rows = order_shipped() + train("ask-2", ["#13", "#14"])
        self.assertEqual(
            self.problems(rows),
            ["cd: merge refused: #14 rides train ask-2 behind #13, which is"
             " planned, not merged"])
        merged = moved("#13", "merging", "merged", pr=5, sha="abc",
                       checks={})
        self.assertEqual(self.problems(rows + [merged]), [])

    def test_a_gate_path_item_rides_a_train_on_identical_blobs(self):
        blobs = {ADR: "aaa", "docs/features/x/prd.md": "bbb"}
        rows = feature_shipped(blobs) + train("ask-2", ["#12"])
        self.assertEqual(self.problems(rows, "#12", blobs), [])

    def test_a_changed_gate_blob_is_refused_on_a_train(self):
        rows = feature_shipped({ADR: "aaa"}) + train("ask-2", ["#12"])
        self.assertEqual(
            self.problems(rows, "#12", {ADR: "ccc"}),
            [f"cd: merge refused: #12's gate file {ADR} is not the one"
             " approved at its gate ask; it needs its own merge ask"])

    def test_a_gate_file_never_approved_is_refused_on_a_train(self):
        rows = feature_shipped({}) + train("ask-2", ["#12"])
        self.assertEqual(
            self.problems(rows, "#12", {ADR: "aaa"}),
            [f"cd: merge refused: #12's gate file {ADR} is not the one"
             " approved at its gate ask; it needs its own merge ask"])

    def test_its_own_merge_answer_covers_a_changed_gate_file(self):
        rows = feature_shipped({ADR: "aaa"}) + own("ask-2", "#12")
        self.assertEqual(self.problems(rows, "#12", {ADR: "ccc"}), [])

    def test_an_item_outside_the_plan_is_refused(self):
        self.assertEqual(self.problems([], "#99"),
                         ["cd: #99 is not an item of this batch's plan"])


if __name__ == "__main__":
    unittest.main()
