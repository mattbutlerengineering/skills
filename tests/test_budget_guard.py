"""budget_guard.py (the ADR-0034 dollar-budget stop) — pure-function +
fixture tests.

Same discipline as test_assembler: every function is exercised through its
public interface, tests assert the EXACT strings callers will print or
write, and nothing here touches the network or a real git repository —
push_wip takes an injected command runner, same shape as
label_sync.gh_runner.

TestAcceptanceScenario is the WO-0006 acceptance criterion end to end: a
deliberately over-budget run hard-stops, pushes WIP, posts a handoff naming
the remaining work, and appends a costs.jsonl line that satisfies detector
G's own shape check (gates.check_cost_ledger) — not a re-implementation of
G's rules, a cross-check against the real one.
"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import budget_guard
import gates
import handoff

CONFIG = {
    "budgets_usd": {"S": 5, "M": 15, "L": 40},
    "routing": {"mechanical": "claude-haiku-4-5",
                "implementation": "claude-sonnet-5",
                "architecture_review": "claude-fable-5"},
    "wip_cap": 3,
    "monthly_cap_usd": 300,
}


class FixtureTree:
    def __init__(self, root):
        self.root = Path(root)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def factory(self):
        self.write("factory/templates/factory.json", json.dumps(CONFIG))
        return self


class TestResolveBudget(unittest.TestCase):
    def test_each_size_resolves_to_its_dollar_ceiling(self):
        for size, dollars in (("S", 5), ("M", 15), ("L", 40)):
            self.assertEqual(budget_guard.resolve_budget(size, CONFIG),
                             (dollars, []), size)

    def test_an_uncovered_size_is_a_problem(self):
        self.assertEqual(
            budget_guard.resolve_budget("XL", CONFIG),
            (None, ["bg: factory.json names no positive budget for size"
                    " 'XL'"]))

    def test_a_config_without_a_budgets_table_is_a_problem(self):
        self.assertEqual(
            budget_guard.resolve_budget("S", {}),
            (None, ["bg: factory.json has no budgets_usd table"]))

    def test_a_non_positive_budget_is_a_problem(self):
        self.assertEqual(
            budget_guard.resolve_budget("S", {"budgets_usd": {"S": 0}}),
            (None, ["bg: factory.json names no positive budget for size"
                    " 'S'"]))

    def test_a_bool_budget_is_a_problem(self):
        # bool is an int subclass in Python; True/False must not pass as $.
        self.assertEqual(
            budget_guard.resolve_budget("S", {"budgets_usd": {"S": True}}),
            (None, ["bg: factory.json names no positive budget for size"
                    " 'S'"]))


class TestDecide(unittest.TestCase):
    def test_spend_under_budget_continues(self):
        verdict, reason = budget_guard.decide(4.99, 5)
        self.assertEqual(verdict, budget_guard.CONTINUE)
        self.assertEqual(reason, "bg: spend $4.99 is within the $5.00 budget")

    def test_spend_at_budget_hard_stops(self):
        # Equality hard-stops: a run at exactly its ceiling has no more to
        # spend.
        verdict, reason = budget_guard.decide(15.0, 15)
        self.assertEqual(verdict, budget_guard.HARD_STOP)
        self.assertEqual(
            reason,
            "bg: spend $15.00 has reached or exceeded the $15.00 budget")

    def test_spend_over_budget_hard_stops(self):
        verdict, reason = budget_guard.decide(20, 15)
        self.assertEqual(verdict, budget_guard.HARD_STOP)


class TestGuard(unittest.TestCase):
    def test_under_budget_continues_using_repo_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            verdict, reason, problems = budget_guard.guard(
                tree.root, "M", 3.0)
            self.assertEqual(problems, [])
            self.assertEqual(verdict, budget_guard.CONTINUE)
            self.assertIn("$3.00", reason)

    def test_over_budget_hard_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            verdict, reason, problems = budget_guard.guard(
                tree.root, "M", 16.0)
            self.assertEqual(problems, [])
            self.assertEqual(verdict, budget_guard.HARD_STOP)
            self.assertIn("$16.00", reason)

    def test_an_injected_config_skips_the_repo_lookup(self):
        verdict, reason, problems = budget_guard.guard(
            "/does/not/exist", "S", 1.0, config=CONFIG)
        self.assertEqual((verdict, problems), (budget_guard.CONTINUE, []))

    def test_a_missing_factory_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            verdict, reason, problems = budget_guard.guard(tmp, "S", 0.0)
            self.assertEqual(verdict, budget_guard.HARD_STOP)
            self.assertEqual(reason,
                             "bg: no budget could be resolved — failing"
                             " closed")
            self.assertTrue(problems)
            self.assertTrue(problems[0].startswith("asm: missing"),
                            problems)

    def test_an_unbudgeted_size_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            verdict, reason, problems = budget_guard.guard(
                tree.root, "XL", 0.0)
            self.assertEqual(verdict, budget_guard.HARD_STOP)
            self.assertEqual(problems,
                             ["bg: factory.json names no positive budget for"
                              " size 'XL'"])


class TestPushWip(unittest.TestCase):
    def test_pushes_wip_through_the_injected_runner(self):
        calls = []
        budget_guard.push_wip("WO-0006", run=calls.append)
        self.assertEqual(calls, [
            ["add", "-A"],
            ["commit", "-m", "wip(WO-0006): budget exhausted",
             "--allow-empty"],
            ["push"],
        ])


class TestLedgerEntry(unittest.TestCase):
    def test_builds_exactly_the_gates_ledger_fields(self):
        entry = budget_guard.ledger_entry(
            "WO-0006", "r-1", "claude-sonnet-5", 9000, 16.25,
            "budget-exhausted")
        self.assertEqual(set(entry), set(gates.LEDGER_FIELDS))
        self.assertEqual(entry["wo"], "WO-0006")
        self.assertEqual(entry["cost"], 16.25)
        self.assertEqual(entry["outcome"], "budget-exhausted")


class TestAppendLedgerLine(unittest.TestCase):
    def test_appends_one_line_creating_the_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry = budget_guard.ledger_entry(
                "WO-0006", "r-1", "m", 100, 1.0, "merged")
            budget_guard.append_ledger_line(tmp, entry)
            ledger = Path(tmp) / "docs" / "factory" / "costs.jsonl"
            self.assertEqual(
                ledger.read_text(encoding="utf-8"),
                json.dumps(entry) + "\n")

    def test_appends_without_touching_existing_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = budget_guard.ledger_entry(
                "WO-0001", "r-1", "m", 100, 1.0, "merged")
            second = budget_guard.ledger_entry(
                "WO-0002", "r-2", "m", 200, 2.0, "budget-exhausted")
            budget_guard.append_ledger_line(tmp, first)
            budget_guard.append_ledger_line(tmp, second)
            ledger = Path(tmp) / "docs" / "factory" / "costs.jsonl"
            lines = ledger.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines, [json.dumps(first), json.dumps(second)])


class TestAcceptanceScenario(unittest.TestCase):
    """WO-0006's acceptance criterion, wired end to end from the public
    interfaces of budget_guard.py and handoff.py: a deliberately
    over-budget run hard-stops, pushes WIP, posts a handoff naming the
    remaining work, and appends a costs.jsonl line."""

    def test_a_deliberately_over_budget_run_hard_stops_and_hands_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.write("docs/features/demo/breakdown.md",
                       "- [ ] WO-0006 budget_guard (PRD-0001)\n")

            # A size:M order that has already overspent its $15 ceiling.
            verdict, reason, problems = budget_guard.guard(
                tree.root, "M", 16.40)
            self.assertEqual(problems, [])
            self.assertEqual(verdict, budget_guard.HARD_STOP)

            # Hard-stop: push whatever is on disk (never discard WIP).
            calls = []
            budget_guard.push_wip("WO-0006", run=calls.append)
            self.assertEqual(calls[-1], ["push"])

            # Hard-stop: compose and post a handoff naming remaining work.
            posted = []
            text = handoff.compose(
                "WO-0006", reason,
                done=["budget_guard.decide", "handoff.compose"],
                remaining=["cost ledger append", "factory_init mirrors"],
                resume="rerun budget_guard.py check M <spend> after review")
            handoff.post_handoff(text, post=posted.append)
            self.assertEqual(posted, [text])
            self.assertIn("cost ledger append", text)
            self.assertIn("factory_init mirrors", text)
            self.assertIn("$16.40", text)

            # Hard-stop: append the run's line to the cost ledger.
            budget_guard.append_ledger_line(
                tree.root, budget_guard.ledger_entry(
                    "WO-0006", "r-over-budget", "claude-sonnet-5",
                    9500, 16.40, "budget-exhausted"))
            ledger = tree.root / "docs" / "factory" / "costs.jsonl"
            self.assertEqual(len(ledger.read_text(
                encoding="utf-8").splitlines()), 1)

            # The appended line satisfies detector G's own shape check —
            # not a re-implementation of G's rules, a cross-check against
            # the real one.
            self.assertEqual(gates.check_cost_ledger(tree.root), [])


class TestMain(unittest.TestCase):
    def run_cli(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = budget_guard.main(argv)
        return code, out.getvalue()

    def test_unknown_subcommand_prints_usage(self):
        code, out = self.run_cli(["nonsense"])
        self.assertEqual(code, 2)
        self.assertIn("python3 budget_guard.py check", out)

    def test_a_non_numeric_spend_is_a_problem(self):
        code, out = self.run_cli(["check", "S", "lots"])
        self.assertEqual(code, 1)
        self.assertIn("bg: 'lots' is not a number", out)
        self.assertIn("budget_guard: 1 problem(s)", out)

    def test_check_against_the_real_repo_config_exits_zero(self):
        # The real repo's factory.json budgets S at $5; a trivial spend
        # continues and the CLI mechanism itself is clean (0 problems).
        code, out = self.run_cli(["check", "S", "0.01"])
        self.assertEqual(code, 0)
        self.assertIn("CONTINUE", out)
        self.assertIn("budget_guard: 0 problem(s)", out)


if __name__ == "__main__":
    unittest.main()
