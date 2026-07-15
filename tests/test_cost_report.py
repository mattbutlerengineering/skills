"""cost_report.py (the ADR-0034 weekly rollup and monthly circuit breaker) —
pure-function + fixture tests.

Same discipline as test_budget_guard: every function is exercised through
its public interface, tests assert the EXACT strings callers will print or
write, and nothing here touches the network or real time — the clock is
injected, same shape budget_guard.push_wip injects its git runner.

TestAcceptanceScenario is the WO-0009 acceptance criterion end to end: a
fixture costs.jsonl recomputes to the right totals, and a simulated cap
breach decides PAUSE — the signal the workflow's `gh variable set
FACTORY_PAUSED` step reads from $GITHUB_OUTPUT (this module only computes;
the workflow is the one that mutates, per the compute/mutate boundary in
its own header comment).
"""
import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import cost_report
import gates

CONFIG = {
    "budgets_usd": {"S": 5, "M": 15, "L": 40},
    "routing": {"mechanical": "claude-haiku-4-5",
                "implementation": "claude-sonnet-5",
                "architecture_review": "claude-fable-5"},
    "wip_cap": 3,
    "monthly_cap_usd": 300,
}


def entry(wo, run_id, model, tokens, cost, outcome):
    """One well-formed docs/factory/costs.jsonl record, built from
    gates.LEDGER_FIELDS so a fixture line can never silently drift from the
    real ledger shape (same discipline as budget_guard.ledger_entry)."""
    return dict(zip(gates.LEDGER_FIELDS,
                    (wo, run_id, model, tokens, cost, outcome)))


def fixed_clock(iso_date):
    """A zero-arg clock injected in place of datetime.now — deterministic
    report dates without touching real time."""
    dt = datetime.fromisoformat(iso_date).replace(tzinfo=timezone.utc)
    return lambda: dt


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

    def ledger(self, entries):
        text = "".join(json.dumps(e) + "\n" for e in entries)
        self.write("docs/factory/costs.jsonl", text)
        return self


class TestReadLedger(unittest.TestCase):
    def test_a_missing_ledger_is_empty_not_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(cost_report.read_ledger(tmp), ([], []))

    def test_parses_well_formed_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            e1 = entry("WO-0001", "r-1", "m", 100, 1.5, "merged")
            e2 = entry("WO-0002", "r-2", "m", 200, 2.5, "merged")
            tree.ledger([e1, e2])
            entries, problems = cost_report.read_ledger(tmp)
            self.assertEqual(entries, [e1, e2])
            self.assertEqual(problems, [])

    def test_blank_lines_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            e1 = entry("WO-0001", "r-1", "m", 100, 1.5, "merged")
            tree.write("docs/factory/costs.jsonl", json.dumps(e1) + "\n\n")
            entries, problems = cost_report.read_ledger(tmp)
            self.assertEqual(entries, [e1])
            self.assertEqual(problems, [])

    def test_invalid_json_is_a_problem_and_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/factory/costs.jsonl", "not json\n")
            entries, problems = cost_report.read_ledger(tmp)
            self.assertEqual(entries, [])
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                "cr: docs/factory/costs.jsonl:1 is not valid JSON:"),
                problems)

    def test_a_non_object_line_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/factory/costs.jsonl", "[1, 2, 3]\n")
            entries, problems = cost_report.read_ledger(tmp)
            self.assertEqual(entries, [])
            self.assertEqual(problems, [
                "cr: docs/factory/costs.jsonl:1 is not a JSON object"])

    def test_an_entry_missing_a_usable_cost_is_excluded_and_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            bad = {"wo": "WO-0001", "run_id": "r-1", "model": "m",
                   "tokens": 100, "outcome": "merged"}  # no cost field
            tree.write("docs/factory/costs.jsonl", json.dumps(bad) + "\n")
            entries, problems = cost_report.read_ledger(tmp)
            self.assertEqual(entries, [])
            self.assertEqual(problems, [
                "cr: docs/factory/costs.jsonl:1 ledger line is not usable"
                " for cost aggregation (wo/cost/tokens)"])

    def test_a_negative_cost_is_excluded_and_flagged(self):
        # Fail closed: a negative cost would silently pull the total spend
        # DOWN, exactly the direction that could mask a real cap breach.
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            bad = entry("WO-0001", "r-1", "m", 100, -5.0, "merged")
            tree.write("docs/factory/costs.jsonl", json.dumps(bad) + "\n")
            entries, problems = cost_report.read_ledger(tmp)
            self.assertEqual(entries, [])
            self.assertEqual(len(problems), 1)

    def test_an_injected_ledger_path_overrides_the_repo_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            custom = Path(tmp) / "custom.jsonl"
            e1 = entry("WO-0001", "r-1", "m", 100, 1.5, "merged")
            custom.write_text(json.dumps(e1) + "\n", encoding="utf-8")
            entries, problems = cost_report.read_ledger(
                "/does/not/exist", ledger_path=custom)
            self.assertEqual((entries, problems), ([e1], []))


class TestAggregate(unittest.TestCase):
    def test_recomputes_totals_from_a_fixture(self):
        entries = [
            entry("WO-0001", "r-1", "m", 1000, 12.50, "merged"),
            entry("WO-0002", "r-2", "m", 2000, 5.00, "merged"),
            entry("WO-0001", "r-3", "m", 500, 2.50, "budget-exhausted"),
        ]
        self.assertEqual(cost_report.aggregate(entries), {
            "total_cost": 20.00,
            "total_tokens": 3500,
            "run_count": 3,
            "by_wo": {"WO-0001": 15.00, "WO-0002": 5.00},
        })

    def test_an_empty_ledger_aggregates_to_zero(self):
        self.assertEqual(cost_report.aggregate([]), {
            "total_cost": 0.0, "total_tokens": 0, "run_count": 0,
            "by_wo": {}})


class TestResolveCap(unittest.TestCase):
    def test_resolves_the_configured_cap(self):
        self.assertEqual(cost_report.resolve_cap(CONFIG), (300, []))

    def test_a_config_without_a_cap_is_a_problem(self):
        self.assertEqual(
            cost_report.resolve_cap({}),
            (None, ["cr: factory.json names no positive monthly_cap_usd"]))

    def test_a_non_positive_cap_is_a_problem(self):
        self.assertEqual(
            cost_report.resolve_cap({"monthly_cap_usd": 0}),
            (None, ["cr: factory.json names no positive monthly_cap_usd"]))

    def test_a_bool_cap_is_a_problem(self):
        # bool is an int subclass in Python; True/False must not pass as $.
        self.assertEqual(
            cost_report.resolve_cap({"monthly_cap_usd": True}),
            (None, ["cr: factory.json names no positive monthly_cap_usd"]))


class TestDecide(unittest.TestCase):
    def test_spend_under_cap_continues(self):
        verdict, reason = cost_report.decide(299.99, 300)
        self.assertEqual(verdict, cost_report.CONTINUE)
        self.assertEqual(
            reason, "cr: spend $299.99 is within the $300.00 monthly cap")

    def test_spend_at_cap_pauses(self):
        # Equality pauses: a month that has just reached its ceiling has no
        # more to spend.
        verdict, reason = cost_report.decide(300.0, 300)
        self.assertEqual(verdict, cost_report.PAUSE)
        self.assertEqual(
            reason, "cr: spend $300.00 has reached or exceeded the $300.00"
            " monthly cap — pausing dispatch (FACTORY_PAUSED)")

    def test_spend_over_cap_pauses(self):
        verdict, _ = cost_report.decide(310, 300)
        self.assertEqual(verdict, cost_report.PAUSE)


class TestGuard(unittest.TestCase):
    def test_under_cap_continues_using_repo_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([entry("WO-0001", "r-1", "m", 1000, 50.0, "merged")])
            verdict, reason, totals, cap, problems = cost_report.guard(
                tree.root)
            self.assertEqual(problems, [])
            self.assertEqual(verdict, cost_report.CONTINUE)
            self.assertEqual(cap, 300)
            self.assertEqual(totals["total_cost"], 50.0)

    def test_a_simulated_cap_breach_pauses(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([
                entry("WO-0001", "r-1", "m", 100000, 250.0, "merged"),
                entry("WO-0002", "r-2", "m", 50000, 75.0, "merged"),
            ])
            verdict, reason, totals, cap, problems = cost_report.guard(
                tree.root)
            self.assertEqual(problems, [])
            self.assertEqual(verdict, cost_report.PAUSE)
            self.assertIn("FACTORY_PAUSED", reason)
            self.assertEqual(totals["total_cost"], 325.0)

    def test_no_runs_yet_is_well_under_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            verdict, reason, totals, cap, problems = cost_report.guard(
                tree.root)
            self.assertEqual(problems, [])
            self.assertEqual(verdict, cost_report.CONTINUE)
            self.assertEqual(totals["total_cost"], 0.0)

    def test_an_injected_config_skips_the_repo_lookup(self):
        verdict, reason, totals, cap, problems = cost_report.guard(
            "/does/not/exist", config=CONFIG)
        self.assertEqual(problems, [])
        self.assertEqual(verdict, cost_report.CONTINUE)
        self.assertEqual(cap, 300)

    def test_a_missing_factory_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            verdict, reason, totals, cap, problems = cost_report.guard(tmp)
            self.assertEqual(verdict, cost_report.PAUSE)
            self.assertEqual(
                reason,
                "cr: no monthly cap could be resolved — failing closed")
            self.assertIsNone(cap)
            self.assertTrue(problems)
            self.assertTrue(problems[0].startswith("asm: missing"), problems)

    def test_an_uncapped_config_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/factory.json",
                       json.dumps({"budgets_usd": {"S": 5}}))
            verdict, reason, totals, cap, problems = cost_report.guard(
                tree.root)
            self.assertEqual(verdict, cost_report.PAUSE)
            self.assertEqual(problems, [
                "cr: factory.json names no positive monthly_cap_usd"])

    def test_an_unparseable_ledger_line_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.write("docs/factory/costs.jsonl", "not json\n")
            verdict, reason, totals, cap, problems = cost_report.guard(
                tree.root)
            self.assertEqual(verdict, cost_report.PAUSE)
            self.assertEqual(
                reason, "cr: unreadable ledger — failing closed")
            self.assertIsNone(cap)
            self.assertTrue(problems)


class TestComposeReport(unittest.TestCase):
    def test_report_body_shows_totals_and_verdict(self):
        totals = {"total_cost": 20.0, "total_tokens": 3500, "run_count": 3,
                  "by_wo": {"WO-0001": 15.0, "WO-0002": 5.0}}
        body = cost_report.compose_report(
            totals, cost_report.CONTINUE,
            "cr: spend $20.00 is within the $300.00 monthly cap", 300,
            "2026-07-13")
        self.assertIn("## Factory cost report — 2026-07-13", body)
        self.assertIn("$20.00 of $300.00 monthly cap", body)
        self.assertIn("- WO-0001: $15.00", body)
        self.assertIn("- WO-0002: $5.00", body)
        self.assertIn("cr: spend $20.00 is within the $300.00 monthly cap",
                      body)

    def test_no_runs_recorded_says_so(self):
        totals = {"total_cost": 0.0, "total_tokens": 0, "run_count": 0,
                  "by_wo": {}}
        body = cost_report.compose_report(
            totals, cost_report.CONTINUE,
            "cr: spend $0.00 is within the $300.00 monthly cap", 300,
            "2026-07-13")
        self.assertIn("(no runs recorded)", body)

    def test_an_unknown_cap_is_shown_honestly(self):
        totals = {"total_cost": 0.0, "total_tokens": 0, "run_count": 0,
                  "by_wo": {}}
        body = cost_report.compose_report(
            totals, cost_report.PAUSE,
            "cr: unreadable ledger — failing closed", None, "2026-07-13")
        self.assertIn("of unknown monthly cap", body)


class TestReportTitle(unittest.TestCase):
    def test_title_includes_the_date(self):
        self.assertEqual(cost_report.report_title("2026-07-13"),
                         "Factory cost report — 2026-07-13")


class TestRunReport(unittest.TestCase):
    def test_under_cap_outputs_continue_and_pause_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([entry("WO-0001", "r-1", "m", 1000, 50.0, "merged")])
            outputs, problems = cost_report.run_report(
                tree.root, clock=fixed_clock("2026-07-13"))
            self.assertEqual(problems, [])
            self.assertEqual(outputs["pause"], "false")
            self.assertEqual(outputs["title"],
                             "Factory cost report — 2026-07-13")
            self.assertIn("$50.00 of $300.00", outputs["body"])
            self.assertIn("within the $300.00 monthly cap",
                          outputs["reason"])

    def test_a_cap_breach_outputs_pause_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([
                entry("WO-0001", "r-1", "m", 100000, 250.0, "merged"),
                entry("WO-0002", "r-2", "m", 50000, 75.0, "merged"),
            ])
            outputs, problems = cost_report.run_report(
                tree.root, clock=fixed_clock("2026-07-13"))
            self.assertEqual(problems, [])
            self.assertEqual(outputs["pause"], "true")
            self.assertIn("FACTORY_PAUSED", outputs["reason"])
            self.assertIn("FACTORY_PAUSED", outputs["body"])

    def test_a_real_clock_default_produces_todays_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            outputs, problems = cost_report.run_report(tree.root)
            self.assertEqual(problems, [])
            today = datetime.now(timezone.utc).date().isoformat()
            self.assertIn(today, outputs["title"])


class TestMain(unittest.TestCase):
    def run_cli(self, argv, env=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cost_report.main(argv, env=env if env is not None else {})
        return code, out.getvalue()

    def test_unknown_subcommand_prints_usage(self):
        code, out = self.run_cli(["nonsense"])
        self.assertEqual(code, 2)
        self.assertIn("python3 cost_report.py report", out)

    def test_check_against_the_real_repo_config_exits_zero(self):
        # No docs/factory/costs.jsonl in this repo yet: $0 spend, well under
        # the real factory.json's monthly cap (same precedent as
        # test_budget_guard.TestMain's real-repo-config check).
        code, out = self.run_cli(["report"])
        self.assertEqual(code, 0)
        self.assertIn("cost_report: 0 problem(s)", out)
        self.assertIn("within the", out)

    def test_writes_github_output_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "gh_output.txt"
            env = {"GITHUB_OUTPUT": str(out_path)}
            code, _ = self.run_cli(["report"], env)
            self.assertEqual(code, 0)
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("pause=", text)
            self.assertIn("title=Factory cost report", text)
            self.assertIn("body<<", text)

    def test_no_github_output_is_a_silent_no_op(self):
        # Local/hand runs have no GITHUB_OUTPUT; nothing to write, no error.
        code, out = self.run_cli(["report"], {})
        self.assertEqual(code, 0)


class TestAcceptanceScenario(unittest.TestCase):
    """WO-0009's acceptance criterion end to end: the report recomputes
    numbers from a fixture costs.jsonl, and a simulated cap breach decides
    PAUSE — the signal the workflow's `gh variable set FACTORY_PAUSED` step
    reads. This module computes only; it never calls gh itself (the
    compute/mutate boundary), so "sets FACTORY_PAUSED" is verified as far
    as this module's public interface goes: pause == 'true'."""

    def test_the_report_recomputes_numbers_from_costs_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([
                entry("WO-0001", "r-1", "claude-sonnet-5", 9000, 12.34,
                      "merged"),
                entry("WO-0002", "r-2", "claude-haiku-4-5", 4000, 1.11,
                      "merged"),
            ])
            outputs, problems = cost_report.run_report(
                tree.root, clock=fixed_clock("2026-07-13"))
            self.assertEqual(problems, [])
            self.assertEqual(outputs["pause"], "false")
            self.assertIn("$13.45 of $300.00", outputs["body"])
            self.assertIn("- WO-0001: $12.34", outputs["body"])
            self.assertIn("- WO-0002: $1.11", outputs["body"])

    def test_a_simulated_cap_breach_sets_factory_paused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([
                entry("WO-0001", "r-1", "claude-sonnet-5", 900000, 305.0,
                      "merged"),
            ])
            outputs, problems = cost_report.run_report(
                tree.root, clock=fixed_clock("2026-07-13"))
            self.assertEqual(problems, [])
            self.assertEqual(outputs["pause"], "true")
            self.assertIn("FACTORY_PAUSED", outputs["reason"])


if __name__ == "__main__":
    unittest.main()
