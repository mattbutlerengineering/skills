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

TestMonthlyWindow pins what makes the breaker MONTHLY (ADR-0034): the
verdict decides on the report month's spend, so a past month's blowout
un-latches when a new month opens under the cap, and legacy (pre-`at`)
rows count in the lifetime figure but never in a month window.
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
            entry("WO-0001", "r-1", "m", 1000, 12.50, "merged", "2026-07-06"),
            entry("WO-0002", "r-2", "m", 2000, 5.00, "merged", "2026-07-08"),
            entry("WO-0001", "r-3", "m", 500, 2.50, "budget-exhausted",
                  "2026-07-10"),
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

    def test_gate_latency_rows_are_not_runs(self):
        # A gate-wait observation (ADR-0041) is $0 either way; what it must
        # not do is inflate the run count or pad by_wo with $0.00 lines.
        entries = [
            entry("WO-0001", "r-1", "m", 1000, 12.50, "merged", "2026-07-06"),
            cost_ledger.gate_entry("WO-0001", "merge", 7260,
                                   "2026-07-22T05:17:00Z"),
            cost_ledger.gate_entry("WO-0002", "prd", 86400,
                                   "2026-07-21T09:00:00Z"),
        ]
        self.assertEqual(cost_report.aggregate(entries), {
            "total_cost": 12.50,
            "total_tokens": 1000,
            "run_count": 1,
            "by_wo": {"WO-0001": 12.50},
        })

    def test_a_month_window_counts_only_that_months_rows(self):
        entries = [
            entry("WO-0001", "r-1", "m", 1000, 12.50, "merged", "2026-07-06"),
            entry("WO-0002", "r-2", "m", 2000, 5.00, "merged", "2026-06-28"),
        ]
        self.assertEqual(cost_report.aggregate(entries, month="2026-07"), {
            "total_cost": 12.50,
            "total_tokens": 1000,
            "run_count": 1,
            "by_wo": {"WO-0001": 12.50},
        })

    def test_legacy_rows_without_at_are_excluded_from_a_window(self):
        # Pre-timestamp rows belong to closed months by construction: they
        # count in the lifetime total (month=None) but never in a window.
        legacy = {"wo": "WO-0001", "run_id": "r-1", "model": "m",
                  "tokens": 1000, "cost": 12.50, "outcome": "merged"}
        self.assertEqual(
            cost_report.aggregate([legacy], month="2026-07")["total_cost"],
            0.0)
        self.assertEqual(
            cost_report.aggregate([legacy])["total_cost"], 12.50)


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

    def test_nonsense_spend_pauses_not_continues(self):
        # NaN >= cap is False: without validation, nonsense would slip
        # past the comparison and silently CONTINUE — the fail-open
        # direction the breaker must not have. Same boundary discipline
        # as budget_guard's _validate_spend, PAUSE-shaped.
        for bad in (float("nan"), float("inf"), -1.0, "12", None, True):
            verdict, reason = cost_report.decide(bad, 300)
            self.assertEqual(verdict, cost_report.PAUSE, bad)
            self.assertIn("is not a finite, non-negative number", reason)


class TestGuard(unittest.TestCase):
    def test_guard_returns_a_named_result(self):
        # Six fields used to travel as a positional tuple unpacked (and
        # mostly discarded) at every call site; the names are the
        # contract now. Field order stays pinned because GuardResult is
        # still a tuple — positional unpacking keeps working.
        result = cost_report.guard("/does/not/exist", config=CONFIG)
        self.assertEqual(
            result._fields,
            ("verdict", "reason", "totals", "month_totals", "cap",
             "problems"))
        self.assertEqual(result.verdict, cost_report.CONTINUE)

    def test_under_cap_continues_using_repo_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([entry("WO-0001", "r-1", "m", 1000, 50.0, "merged",
                               "2026-07-06")])
            result = cost_report.guard(tree.root)
            self.assertEqual(result.problems, [])
            self.assertEqual(result.verdict, cost_report.CONTINUE)
            self.assertEqual(result.cap, 300)
            self.assertEqual(result.totals["total_cost"], 50.0)

    def test_a_simulated_cap_breach_pauses(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([
                entry("WO-0001", "r-1", "m", 100000, 250.0, "merged",
                      "2026-07-06"),
                entry("WO-0002", "r-2", "m", 50000, 75.0, "merged",
                      "2026-07-08"),
            ])
            result = cost_report.guard(tree.root)
            self.assertEqual(result.problems, [])
            self.assertEqual(result.verdict, cost_report.PAUSE)
            self.assertIn("FACTORY_PAUSED", result.reason)
            self.assertEqual(result.totals["total_cost"], 325.0)

    def test_no_month_decides_on_the_lifetime_total(self):
        # guard(month=None) keeps the pre-window behavior: month_totals is
        # the lifetime aggregate, so the verdict covers every row.
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([entry("WO-0001", "r-1", "m", 1000, 50.0, "merged",
                               "2026-07-06")])
            result = cost_report.guard(tree.root)
            self.assertEqual(result.problems, [])
            self.assertEqual(result.month_totals, result.totals)

    def test_a_month_windows_the_verdict(self):
        # An over-cap June plus a quiet July: windowed on July, the guard
        # CONTINUEs, while the lifetime figure still shows everything.
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([
                entry("WO-0001", "r-1", "m", 900000, 305.0, "merged",
                      "2026-06-20"),
                entry("WO-0002", "r-2", "m", 1000, 5.0, "merged",
                      "2026-07-06"),
            ])
            result = cost_report.guard(tree.root, month="2026-07")
            self.assertEqual(result.problems, [])
            self.assertEqual(result.verdict, cost_report.CONTINUE)
            self.assertEqual(result.month_totals["total_cost"], 5.0)
            self.assertEqual(result.totals["total_cost"], 310.0)

    def test_no_runs_yet_is_well_under_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            result = cost_report.guard(tree.root)
            self.assertEqual(result.problems, [])
            self.assertEqual(result.verdict, cost_report.CONTINUE)
            self.assertEqual(result.totals["total_cost"], 0.0)

    def test_an_injected_config_skips_the_repo_lookup(self):
        result = cost_report.guard("/does/not/exist", config=CONFIG)
        self.assertEqual(result.problems, [])
        self.assertEqual(result.verdict, cost_report.CONTINUE)
        self.assertEqual(result.cap, 300)

    def test_a_missing_factory_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = cost_report.guard(tmp)
            self.assertEqual(result.verdict, cost_report.PAUSE)
            self.assertEqual(
                result.reason,
                "cr: no monthly cap could be resolved — failing closed")
            self.assertIsNone(result.cap)
            self.assertTrue(result.problems)
            self.assertTrue(result.problems[0].startswith("config: missing"),
                            result.problems)

    def test_an_uncapped_config_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/factory.json",
                       json.dumps({"budgets_usd": {"S": 5}}))
            result = cost_report.guard(tree.root)
            self.assertEqual(result.verdict, cost_report.PAUSE)
            self.assertEqual(result.problems, [
                "config: factory.json names no positive monthly_cap_usd"])

    def test_an_unparseable_ledger_line_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.write("docs/factory/costs.jsonl", "not json\n")
            result = cost_report.guard(tree.root)
            self.assertEqual(result.verdict, cost_report.PAUSE)
            self.assertEqual(
                result.reason, "cr: unreadable ledger — failing closed")
            self.assertIsNone(result.cap)
            self.assertTrue(result.problems)


class TestComposeReport(unittest.TestCase):
    def test_report_body_shows_totals_and_verdict(self):
        totals = {"total_cost": 20.0, "total_tokens": 3500, "run_count": 3,
                  "by_wo": {"WO-0001": 15.0, "WO-0002": 5.0}}
        body = cost_report.compose_report(
            totals, cost_report.CONTINUE,
            "cr: spend $20.00 is within the $300.00 monthly cap", 300,
            "2026-07-13", "2026-07", totals)
        self.assertIn("## Factory cost report — 2026-07-13", body)
        self.assertIn("**Spend this month (2026-07):** $20.00 of $300.00"
                      " monthly cap (lifetime: $20.00)", body)
        self.assertIn("- WO-0001: $15.00", body)
        self.assertIn("- WO-0002: $5.00", body)
        self.assertIn("cr: spend $20.00 is within the $300.00 monthly cap",
                      body)

    def test_month_and_lifetime_figures_are_distinct(self):
        totals = {"total_cost": 310.0, "total_tokens": 901000,
                  "run_count": 2,
                  "by_wo": {"WO-0001": 305.0, "WO-0002": 5.0}}
        month_totals = {"total_cost": 5.0, "total_tokens": 1000,
                        "run_count": 1, "by_wo": {"WO-0002": 5.0}}
        body = cost_report.compose_report(
            totals, cost_report.CONTINUE,
            "cr: spend $5.00 is within the $300.00 monthly cap", 300,
            "2026-07-13", "2026-07", month_totals)
        self.assertIn("**Spend this month (2026-07):** $5.00 of $300.00"
                      " monthly cap (lifetime: $310.00)", body)

    def test_no_runs_recorded_says_so(self):
        totals = {"total_cost": 0.0, "total_tokens": 0, "run_count": 0,
                  "by_wo": {}}
        body = cost_report.compose_report(
            totals, cost_report.CONTINUE,
            "cr: spend $0.00 is within the $300.00 monthly cap", 300,
            "2026-07-13", "2026-07", totals)
        self.assertIn("(no runs recorded)", body)

    def test_an_unknown_cap_is_shown_honestly(self):
        totals = {"total_cost": 0.0, "total_tokens": 0, "run_count": 0,
                  "by_wo": {}}
        body = cost_report.compose_report(
            totals, cost_report.PAUSE,
            "cr: unreadable ledger — failing closed", None, "2026-07-13",
            "2026-07", totals)
        self.assertIn("of unknown monthly cap", body)


class TestReportTitle(unittest.TestCase):
    def test_title_includes_the_date(self):
        self.assertEqual(cost_report.report_title("2026-07-13"),
                         "Factory cost report — 2026-07-13")


class TestRunReport(unittest.TestCase):
    def test_under_cap_outputs_continue_and_pause_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([entry("WO-0001", "r-1", "m", 1000, 50.0, "merged",
                               "2026-07-06")])
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
                entry("WO-0001", "r-1", "m", 100000, 250.0, "merged",
                      "2026-07-06"),
                entry("WO-0002", "r-2", "m", 50000, 75.0, "merged",
                      "2026-07-08"),
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


class TestMonthlyWindow(unittest.TestCase):
    """The two load-bearing monthly behaviors, end to end through
    run_report: rollover un-latches a past breach, and a month at its
    ceiling still pauses."""

    def test_rollover_unlatches_a_past_breach(self):
        # July blew past the cap; August has spent $5.00. The August report
        # must CONTINUE (pause=false) — the workflow's resume leg reads
        # exactly this output to clear FACTORY_PAUSED.
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([
                entry("WO-0001", "r-1", "m", 900000, 305.0, "merged",
                      "2026-07-28"),
                entry("WO-0002", "r-2", "m", 1000, 5.0, "merged",
                      "2026-08-02"),
            ])
            outputs, problems = cost_report.run_report(
                tree.root, clock=fixed_clock("2026-08-03"))
            self.assertEqual(problems, [])
            self.assertEqual(outputs["pause"], "false")
            self.assertIn("cr: spend $5.00 is within the $300.00 monthly"
                          " cap", outputs["reason"])

    def test_the_current_month_at_the_cap_pauses(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.ledger([
                entry("WO-0001", "r-1", "m", 500000, 200.0, "merged",
                      "2026-08-01"),
                entry("WO-0002", "r-2", "m", 250000, 100.0, "merged",
                      "2026-08-02"),
            ])
            outputs, problems = cost_report.run_report(
                tree.root, clock=fixed_clock("2026-08-03"))
            self.assertEqual(problems, [])
            self.assertEqual(outputs["pause"], "true")
            self.assertIn("FACTORY_PAUSED", outputs["reason"])

    def test_legacy_rows_count_lifetime_not_monthly(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            legacy = {"wo": "WO-0001", "run_id": "r-0", "model": "m",
                      "tokens": 100000, "cost": 250.0, "outcome": "merged"}
            tree.ledger([
                legacy,
                entry("WO-0002", "r-1", "m", 1000, 5.0, "merged",
                      "2026-08-02"),
            ])
            outputs, problems = cost_report.run_report(
                tree.root, clock=fixed_clock("2026-08-03"))
            self.assertEqual(problems, [])
            self.assertEqual(outputs["pause"], "false")
            self.assertIn("**Spend this month (2026-08):** $5.00 of $300.00"
                          " monthly cap (lifetime: $255.00)",
                          outputs["body"])


class TestMain(cli_contract.CliContract, cli_contract.ReportContract,
               unittest.TestCase):
    usage_fragment = "python3 cost_report.py report"
    summary_line = "cost_report: 0 problem(s)"

    def run_cli(self, argv, env=None):
        return cli_contract.capture(
            cost_report.main, argv,
            env=env if env is not None else {})

    def clean_cli(self):
        return self.run_cli(["report"])

    def test_check_against_the_real_repo_config_exits_zero(self):
        # The real docs/factory/costs.jsonl holds only legacy (pre-at) and
        # gate rows: $0 this month, well under the real factory.json's
        # monthly cap (same precedent as test_budget_guard.TestMain's
        # real-repo-config check).
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

    def test_a_fail_closed_verdict_writes_pause_before_the_failing_exit(self):
        # WO-0033: the workflow's pause step reads steps.report.outputs
        # AFTER this process has exited nonzero — a fail-closed verdict
        # that exits before writing would leave FACTORY_PAUSED unset on
        # exactly the paths the module promises never wave through
        # (review.md major).
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/factory/costs.jsonl", "not json\n")
            out_path = Path(tmp) / "gh_output.txt"
            env = {"GITHUB_OUTPUT": str(out_path)}
            code, printed = cli_contract.capture(
                cost_report.main, ["report"], env=env, root=tree.root)
            self.assertEqual(code, 1)
            self.assertIn("pause=true", out_path.read_text(encoding="utf-8"))


class TestFailClosedPause(unittest.TestCase):
    """WO-0033's workflow half: the report step exits nonzero on exactly
    the fail-closed verdicts, so a pause step gated on implicit success()
    is skipped at the moment it matters most."""

    WORKFLOW = (Path(__file__).resolve().parents[1] / ".github"
                / "workflows" / "cost-report.yml")

    def test_the_pause_step_survives_a_failing_report_step(self):
        text = self.WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("always()\n          && steps.report.outputs.pause"
                      " == 'true'", text)

    def test_the_resume_step_does_not(self):
        # The asymmetry is the safety property: a failing run may pause,
        # only a clean under-cap verdict may resume.
        text = self.WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: steps.report.outputs.pause == 'false'", text)


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
                      "merged", "2026-07-06"),
                entry("WO-0002", "r-2", "claude-haiku-4-5", 4000, 1.11,
                      "merged", "2026-07-08"),
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
                      "merged", "2026-07-06"),
            ])
            outputs, problems = cost_report.run_report(
                tree.root, clock=fixed_clock("2026-07-13"))
            self.assertEqual(problems, [])
            self.assertEqual(outputs["pause"], "true")
            self.assertIn("FACTORY_PAUSED", outputs["reason"])


if __name__ == "__main__":
    unittest.main()
