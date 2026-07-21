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
import json
import re
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import cost_ledger
import cost_report

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling factory_fixture import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from factory_fixture import CONFIG, FixtureTree as FactoryTree  # noqa: E402
import cli_contract  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# fixture records come from the ledger seam itself — no local twin to
# drift from the real shape
entry = cost_ledger.entry


def fixed_clock(iso_date):
    """A zero-arg clock injected in place of datetime.now — deterministic
    report dates without touching real time."""
    dt = datetime.fromisoformat(iso_date).replace(tzinfo=timezone.utc)
    return lambda: dt


class FixtureTree(FactoryTree):
    def ledger(self, entries):
        text = "".join(json.dumps(e) + "\n" for e in entries)
        self.write("docs/factory/costs.jsonl", text)
        return self


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
            self.assertTrue(problems[0].startswith("config: missing"),
                            problems)

    def test_an_uncapped_config_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/factory.json",
                       json.dumps({"budgets_usd": {"S": 5}}))
            verdict, reason, totals, cap, problems = cost_report.guard(
                tree.root)
            self.assertEqual(verdict, cost_report.PAUSE)
            self.assertEqual(problems, [
                "config: factory.json names no positive monthly_cap_usd"])

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


class TestMain(cli_contract.CliContract, unittest.TestCase):
    usage_fragment = "python3 cost_report.py report"

    def run_cli(self, argv, env=None):
        return cli_contract.capture(
            cost_report.main, argv,
            env=env if env is not None else {})

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


class TestWorkflowOutputLockstep(unittest.TestCase):
    """The $GITHUB_OUTPUT seam, cost-report side: run_report's output keys
    and cost-report.yml's steps.report.outputs.<name> references are a
    split contract with no other bridge — a renamed key would silently
    post an empty report title or, worse, never trip the FACTORY_PAUSED
    gate. Same idiom as test_assembler.TestWorkflowOutputLockstep."""

    WORKFLOW = REPO_ROOT / ".github" / "workflows" / "cost-report.yml"
    REFS = re.compile(r"steps\.report\.outputs\.(\w+)")

    def yaml_refs(self):
        refs = set(self.REFS.findall(
            self.WORKFLOW.read_text(encoding="utf-8")))
        self.assertTrue(refs, "cost-report.yml references no report outputs")
        return refs

    def emitted_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            outputs, problems = cost_report.run_report(
                tree.root, clock=fixed_clock("2026-07-20"))
            self.assertEqual(problems, [])
            return set(outputs)

    def test_every_yaml_output_ref_is_an_emitted_key(self):
        self.assertLessEqual(self.yaml_refs(), self.emitted_keys())

    def test_the_workflow_consumes_the_circuit_breaker_keys(self):
        self.assertLessEqual({"pause", "title", "body"}, self.yaml_refs())


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
