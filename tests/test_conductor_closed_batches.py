"""conductor_close.closed_batches (#854): the one walk over every batch
ledger that calibrate and the miner read. A ledger that will not load
and an unclosed one are gaps, never problems: closed ledgers on main are
append-only evidence (#837). The gap rules are tested once here, not per
walker; tests assert the EXACT walk.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import conductor
import conductor_close as close

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor import MINIMAL, PLAN  # noqa: E402

CLOSE = MINIMAL["close"]


def text(*rows):
    return "".join(json.dumps(row) + "\n" for row in rows)


def walk(ledgers):
    with tempfile.TemporaryDirectory() as tmp:
        for batch, body in ledgers.items():
            path = Path(tmp) / conductor.LEDGER.format(batch=batch)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return close.closed_batches(tmp)


class TestClosedBatches(unittest.TestCase):
    def test_a_closed_ledger_is_read_with_its_line_numbers(self):
        body = "\n" + text(PLAN) + "\n" + text(CLOSE)
        self.assertEqual(walk({"b1": body}), (
            [("b1", [PLAN, CLOSE], [2, 4])],
            {"unreadable": [], "unclosed": 0}))

    def test_a_line_that_does_not_parse_is_an_unreadable_gap(self):
        self.assertEqual(walk({"good": "not json\n"}), (
            [], {"unreadable": ["good"], "unclosed": 0}))

    def test_a_directory_that_is_not_a_batch_is_an_unreadable_gap(self):
        self.assertEqual(walk({"oct-2": text(PLAN, CLOSE)}), (
            [], {"unreadable": ["oct-2"], "unclosed": 0}))

    def test_an_unclosed_ledger_is_counted_not_read(self):
        self.assertEqual(walk({"b1": text(PLAN)}), (
            [], {"unreadable": [], "unclosed": 1}))

    def test_every_gap_and_closed_ledger_in_name_order(self):
        closed = text(PLAN, CLOSE)
        self.assertEqual(walk({"zed": closed, "bad": "{\n",
                               "open": text(PLAN), "alpha": closed}), (
            [("alpha", [PLAN, CLOSE], [1, 2]),
             ("zed", [PLAN, CLOSE], [1, 2])],
            {"unreadable": ["bad"], "unclosed": 1}))

    def test_no_ledgers_is_nothing_closed_and_no_gap(self):
        self.assertEqual(walk({}), ([], {"unreadable": [], "unclosed": 0}))

    def test_is_closed_holds_once_a_close_row_is_written(self):
        self.assertEqual((close.is_closed([PLAN]),
                          close.is_closed([PLAN, CLOSE])), (False, True))


if __name__ == "__main__":
    unittest.main()
