"""budget_guard.py (the ADR-0034 dollar-budget stop) — pure-function +
fixture tests.

Same discipline as test_assembler: every function is exercised through its
public interface, tests assert the EXACT strings callers will print or
write, and nothing here touches the network or a real git repository —
push_wip takes an injected command runner, same shape as
cli.gh_runner.

TestAcceptanceScenario is the WO-0006 acceptance criterion end to end: a
deliberately over-budget run hard-stops, pushes WIP, posts a handoff naming
the remaining work, and appends a costs.jsonl line that satisfies detector
G's own shape check (gates.check_cost_ledger) — not a re-implementation of
G's rules, a cross-check against the real one.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import budget_guard
import cost_ledger
import gates
import handoff

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling factory_fixture import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from factory_fixture import CONFIG, FixtureTree  # noqa: E402
import cli_contract  # noqa: E402


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
            self.assertTrue(problems[0].startswith("config: missing"),
                            problems)

    def test_an_unbudgeted_size_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            verdict, reason, problems = budget_guard.guard(
                tree.root, "XL", 0.0)
            self.assertEqual(verdict, budget_guard.HARD_STOP)
            self.assertEqual(problems,
                             ["config: factory.json names no positive budget"
                              " for size 'XL'"])

    def test_a_negative_spend_fails_closed_not_continue(self):
        # Fix 2 (review): `budget_guard.py check S -1` must NOT silently
        # CONTINUE. A negative spend is nonsense that would slip past
        # decide's >= comparison; guard fails closed before even resolving
        # the budget.
        verdict, reason, problems = budget_guard.guard(
            "/does/not/exist", "S", -1.0, config=CONFIG)
        self.assertEqual(verdict, budget_guard.HARD_STOP)
        self.assertEqual(reason, "bg: invalid spend — failing closed")
        self.assertEqual(problems, [
            "bg: spend -1.0 is not a finite, non-negative number"])

    def test_a_nan_spend_fails_closed(self):
        # NaN also slips past >= (every comparison with NaN is False).
        verdict, _, problems = budget_guard.guard(
            "/does/not/exist", "S", float("nan"), config=CONFIG)
        self.assertEqual(verdict, budget_guard.HARD_STOP)
        self.assertEqual(problems, [
            "bg: spend nan is not a finite, non-negative number"])

    def test_an_infinite_spend_fails_closed(self):
        verdict, _, problems = budget_guard.guard(
            "/does/not/exist", "S", float("inf"), config=CONFIG)
        self.assertEqual(verdict, budget_guard.HARD_STOP)
        self.assertEqual(problems, [
            "bg: spend inf is not a finite, non-negative number"])


class TestPushWip(unittest.TestCase):
    def test_pushes_wip_through_the_injected_runner(self):
        calls = []
        problems = budget_guard.push_wip("WO-0006", run=calls.append)
        self.assertEqual(problems, [])
        self.assertEqual(calls, [
            ["add", "-A"],
            ["commit", "-m", "wip(WO-0006): budget exhausted",
             "--allow-empty"],
            ["push"],
        ])

    def test_a_git_failure_is_a_problem_not_a_raise(self):
        # Fix 1 (review): a failing git command (here, a CalledProcessError
        # with the exit-128 stderr a no-upstream push produces) becomes a
        # bg: problem string, never an uncaught traceback.
        def boom(args):
            if args[0] == "push":
                raise subprocess.CalledProcessError(
                    128, ["git", "push"], stderr="fatal: no upstream")
            return None
        problems = budget_guard.push_wip("WO-0006", run=boom)
        self.assertEqual(
            problems, ["bg: pushing WO-0006 WIP failed: fatal: no upstream"])

    def test_a_missing_git_binary_is_a_problem_not_a_raise(self):
        def boom(args):
            raise OSError("git not found")
        problems = budget_guard.push_wip("WO-0006", run=boom)
        self.assertEqual(
            problems, ["bg: pushing WO-0006 WIP failed: git not found"])


def scratch_repo(path):
    """A real, initialised git repo at `path` with a commit and NO remote —
    the normal hard-stopped state, where `git push` exits 128."""
    path.mkdir(parents=True)
    for args in (["init"], ["config", "user.email", "t@example.com"],
                 ["config", "user.name", "Tester"],
                 ["commit", "--allow-empty", "-m", "root"]):
        subprocess.run(["git", "-C", str(path), *args],
                       check=True, capture_output=True, text=True)


class TestPushWipRealRunner(unittest.TestCase):
    """Fix 1 (review): the DEFAULT git_runner, exercised against a real
    scratch repo with no upstream, must surface the push failure as a
    problem rather than raise — the failure mode a mocked runner cannot
    prove."""

    def test_the_real_runner_no_upstream_push_is_a_problem_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            scratch_repo(repo)
            cwd = os.getcwd()
            try:
                os.chdir(repo)
                problems = budget_guard.push_wip("WO-0006")
            finally:
                os.chdir(cwd)
            self.assertEqual(len(problems), 1, problems)
            self.assertTrue(problems[0].startswith(
                "bg: pushing WO-0006 WIP failed:"), problems)


class TestHardStop(unittest.TestCase):
    """Fix 1 (review): the hard-stop sequence is RESILIENT — a WIP-push
    failure is surfaced but must NOT prevent the handoff and ledger, the
    accountability record ADR-0034 promises."""

    def test_push_failure_still_produces_handoff_and_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/features/demo/breakdown.md",
                       "- [ ] WO-0006 budget_guard (PRD-0001)\n")

            def failing_push(args):
                if args[0] == "push":
                    raise subprocess.CalledProcessError(
                        128, ["git", "push"], stderr="fatal: no upstream")
                return None

            posted = []
            problems = budget_guard.hard_stop(
                tree.root, "WO-0006", "bg: spend $16.40 over the $15.00"
                " budget", done=["decide"],
                remaining=["cost ledger append"], resume="rerun after review",
                run_id="r-1", model="claude-sonnet-5", tokens=9500, cost=16.40,
                at="2026-08-02", run=failing_push, post=posted.append)

            # The push failure is surfaced...
            self.assertEqual(problems, [
                "bg: pushing WO-0006 WIP failed: fatal: no upstream"])
            # ...but the handoff was still posted naming the remaining work...
            self.assertEqual(len(posted), 1)
            self.assertIn("cost ledger append", posted[0])
            # ...and the ledger line was still appended (and is well-formed
            # per detector G's real check).
            ledger = tree.root / "docs" / "factory" / "costs.jsonl"
            (line,) = ledger.read_text(encoding="utf-8").splitlines()
            # ...stamped with the caller's date (the monthly circuit
            # breaker windows on it)...
            self.assertEqual(json.loads(line)["at"], "2026-08-02")
            self.assertEqual(gates.check_cost_ledger(tree.root), [])

    def test_the_exhaustion_row_is_inside_the_pushed_commit(self):
        # WO-0032: the pushed WIP commit is the row's only escape from
        # the ephemeral runner — `git add -A` must already see it on
        # disk, or every successful hard stop strands ADR-0034's
        # accountability record on the runner (review.md major; local
        # existence after the fact proves nothing).
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/features/demo/breakdown.md",
                       "- [ ] WO-0006 budget_guard (PRD-0001)\n")
            ledger = tree.root / "docs" / "factory" / "costs.jsonl"
            at_add_time = []

            def snapshotting_run(args):
                if args[0] == "add":
                    at_add_time.append(
                        ledger.read_text(encoding="utf-8")
                        if ledger.exists() else "")
                return None

            budget_guard.hard_stop(
                tree.root, "WO-0006", "over budget", done=[],
                remaining=["finish"], resume="rerun",
                run_id="r-1", model="m", tokens=1, cost=16.40,
                at="2026-08-02", run=snapshotting_run, post=lambda _: None)
            (staged,) = at_add_time
            self.assertIn("WO-0006", staged)

    def test_the_real_runner_end_to_end_no_uncaught_raise(self):
        # The default git_runner against a real no-upstream repo: push
        # fails, yet hard_stop returns (does not raise) and still leaves the
        # handoff + ledger behind.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            scratch_repo(repo)
            repo.joinpath("docs/features/demo").mkdir(parents=True)
            repo.joinpath("docs/features/demo/breakdown.md").write_text(
                "- [ ] WO-0006 budget_guard (PRD-0001)\n", encoding="utf-8")
            posted = []
            cwd = os.getcwd()
            try:
                os.chdir(repo)
                problems = budget_guard.hard_stop(
                    repo, "WO-0006", "over budget", done=[],
                    remaining=["finish"], resume="rerun",
                    run_id="r-1", model="m", tokens=1, cost=16.40,
                    at="2026-08-02", post=posted.append)
            finally:
                os.chdir(cwd)
            self.assertEqual(len(problems), 1, problems)
            self.assertEqual(len(posted), 1)
            ledger = repo / "docs" / "factory" / "costs.jsonl"
            self.assertEqual(len(ledger.read_text(
                encoding="utf-8").splitlines()), 1)


class TestRecord(unittest.TestCase):
    """budget_guard.record — the success-path ledger writer (issue #222).

    Before it, hard_stop was the only in-repo writer of a dispatched-run
    row, so the ledger held exhausted runs and nothing else and the
    monthly total could only ever be $0.00. Every refusal here happens
    BEFORE the append, because the ledger is append-only.
    """

    def tree(self, stack):
        return FixtureTree(stack.enter_context(
            tempfile.TemporaryDirectory()))

    def lines(self, tree):
        ledger = tree.root / "docs" / "factory" / "costs.jsonl"
        if not ledger.is_file():
            return []
        return [json.loads(line) for line
                in ledger.read_text(encoding="utf-8").splitlines() if line]

    def test_a_completed_run_lands_one_well_formed_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            problems = budget_guard.record(
                tree.root, "WO-0007", "r-1", "claude-sonnet-5", 4200, 1.25,
                "completed", "2026-08-07")
            self.assertEqual(problems, [])
            self.assertEqual(self.lines(tree), [{
                "wo": "WO-0007", "run_id": "r-1", "model": "claude-sonnet-5",
                "tokens": 4200, "cost": 1.25, "outcome": "completed",
                "at": "2026-08-07"}])

    def test_the_line_it_writes_satisfies_the_real_detector_g(self):
        """Cross-check against gates.check_cost_ledger itself, never a
        re-implementation of G's rules here."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/features/f/breakdown.md",
                       "- [x] **WO-0007** a thing — size:S,"
                       " blocked by: — (PRD-0001 §Solution) (tracker: #7)\n")
            self.assertEqual(budget_guard.record(
                tree.root, "WO-0007", "r-1", "claude-sonnet-5", 4200, 1.25,
                "completed", "2026-08-07"), [])
            self.assertEqual(gates.check_cost_ledger(tree.root), [])

    def test_a_malformed_row_is_refused_before_the_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            problems = budget_guard.record(
                tree.root, "WO-7", "r-1", "claude-sonnet-5", 4200, 1.25,
                "completed", "2026-08-07")
            self.assertEqual(problems, [
                "bg: refusing to record WO-7: wo 'WO-7' is not a"
                " WO-#### token"])
            self.assertEqual(self.lines(tree), [])

    def test_a_negative_cost_is_refused_before_the_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            problems = budget_guard.record(
                tree.root, "WO-0007", "r-1", "claude-sonnet-5", 4200, -1.0,
                "completed", "2026-08-07")
            self.assertEqual(problems, [
                "bg: refusing to record WO-0007: cost must be a"
                " non-negative number"])
            self.assertEqual(self.lines(tree), [])

    def test_the_same_run_is_never_recorded_twice(self):
        """A re-recorded run would double-count against the monthly cap,
        which is the entire reason the row is written."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            self.assertEqual(budget_guard.record(
                tree.root, "WO-0007", "r-1", "claude-sonnet-5", 4200, 1.25,
                "completed", "2026-08-07"), [])
            problems = budget_guard.record(
                tree.root, "WO-0007", "r-1", "claude-sonnet-5", 4200, 1.25,
                "completed", "2026-08-07")
            self.assertEqual(problems, [
                "bg: refusing to record WO-0007: run_id 'r-1' is already in"
                " the ledger — recording it twice would double-count the"
                " run against the monthly cap"])
            self.assertEqual(len(self.lines(tree)), 1)

    def test_a_second_run_of_the_same_work_order_is_allowed(self):
        """Dedupe keys on (wo, run_id), not wo — a work order legitimately
        gets a second dispatch after a failure."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            for run_id in ("r-1", "r-2"):
                self.assertEqual(budget_guard.record(
                    tree.root, "WO-0007", run_id, "claude-sonnet-5", 4200,
                    1.25, "completed", "2026-08-07"), [])
            self.assertEqual([row["run_id"] for row in self.lines(tree)],
                             ["r-1", "r-2"])

    def test_the_refusal_agrees_with_the_seam_about_identity(self):
        """record's double-count guard and cost_ledger.row_key must be the
        SAME fact, not two facts that agree today.

        Every other case here writes the identity out by hand, so all of
        them keep passing if the seam's identity moves and record's copy
        does not — measured: mutating row_key to a three-field identity
        fails one cost_ledger test and none of this module's. This case asks
        the seam what it thinks of the candidate row and asserts record
        reached the same verdict, so a divergence lands here.

        The candidate differs from the recorded row in `model` alone: under
        today's (wo, run_id) identity the seam calls it a duplicate, and
        under any identity that grows to include model it does not.
        """
        first = ("WO-0007", "r-1", "claude-sonnet-5", 4200, 1.25,
                 "completed", "2026-08-07")
        candidate = ("WO-0007", "r-1", "claude-haiku-4-5", 100, 0.1,
                     "completed", "2026-08-07")
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            self.assertEqual(budget_guard.record(tree.root, *first), [])
            recorded, problems = cost_ledger.read(tree.root)
            self.assertEqual(problems, [])
            seam_calls_it_a_duplicate = (
                cost_ledger.row_key(cost_ledger.entry(*candidate))
                == cost_ledger.row_key(recorded[0]))
            refused = bool(budget_guard.record(tree.root, *candidate))
            self.assertEqual(
                refused, seam_calls_it_a_duplicate,
                "record and cost_ledger.row_key disagree about whether"
                f" {candidate[:3]} is already in the ledger")
            self.assertEqual(len(self.lines(tree)),
                             1 if seam_calls_it_a_duplicate else 2)

    def test_an_unparseable_ledger_fails_closed(self):
        """Appending spend to a ledger that cannot be summed would
        undercount silently — the failure this path exists to end."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/factory/costs.jsonl", "{not json\n")
            problems = budget_guard.record(
                tree.root, "WO-0007", "r-1", "claude-sonnet-5", 4200, 1.25,
                "completed", "2026-08-07")
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                "bg: refusing to record WO-0007: ledger:"), problems)
            self.assertEqual(
                (tree.root / "docs" / "factory" / "costs.jsonl").read_text(
                    encoding="utf-8"), "{not json\n")

    def test_an_exhaustion_row_and_a_completion_row_coexist(self):
        """hard_stop and record write the same shape; only outcome differs,
        and cost_report sums both."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            cost_ledger.append(tree.root, cost_ledger.entry(
                "WO-0006", "r-0", "claude-opus-5", 9500, 16.40,
                "budget-exhausted", "2026-08-07"))
            self.assertEqual(budget_guard.record(
                tree.root, "WO-0007", "r-1", "claude-sonnet-5", 4200, 1.25,
                "completed", "2026-08-07"), [])
            self.assertEqual([row["outcome"] for row in self.lines(tree)],
                             ["budget-exhausted", "completed"])


class TestRecordRun(unittest.TestCase):
    """budget_guard.record_run — record(), with tokens and cost read from
    the harness's own execution file (issue #222's assembler caller)
    rather than typed by a caller. Any file read_execution cannot account
    for is a refusal BEFORE the write: never an invented row."""

    RESULT = {"type": "result", "total_cost_usd": 0.75,
              "usage": {"input_tokens": 900, "output_tokens": 100}}

    def execution(self, tmp, payload):
        path = Path(tmp) / "execution.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def ledger(self, tmp):
        path = Path(tmp) / "docs" / "factory" / "costs.jsonl"
        if not path.is_file():
            return []
        return [json.loads(line) for line
                in path.read_text(encoding="utf-8").splitlines() if line]

    def test_a_run_s_spend_lands_from_its_execution_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            problems = budget_guard.record_run(
                tree.root, "WO-0007", "run-9", "claude-sonnet-5",
                self.execution(tmp, [self.RESULT]), "completed",
                "2026-08-10")
            self.assertEqual(problems, [])
            self.assertEqual(self.ledger(tmp), [{
                "wo": "WO-0007", "run_id": "run-9",
                "model": "claude-sonnet-5", "tokens": 1000, "cost": 0.75,
                "outcome": "completed", "at": "2026-08-10"}])

    def test_an_unaccountable_file_is_refused_before_the_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            path = self.execution(tmp, [{"type": "assistant"}])
            problems = budget_guard.record_run(
                tree.root, "WO-0007", "run-9", "claude-sonnet-5", path,
                "completed", "2026-08-10")
            self.assertEqual(problems, [
                f"bg: refusing to record WO-0007: execution file {path}"
                " has no result entry"])
            self.assertEqual(self.ledger(tmp), [])

    def test_a_re_recorded_run_is_still_refused(self):
        """record_run inherits record's (wo, run_id) dedup — the same
        double-count guard, not a second copy of it."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            path = self.execution(tmp, [self.RESULT])
            self.assertEqual(budget_guard.record_run(
                tree.root, "WO-0007", "run-9", "claude-sonnet-5", path,
                "completed", "2026-08-10"), [])
            problems = budget_guard.record_run(
                tree.root, "WO-0007", "run-9", "claude-sonnet-5", path,
                "agent-failed", "2026-08-10")
            self.assertEqual(problems, [
                "bg: refusing to record WO-0007: run_id 'run-9' is already"
                " in the ledger — recording it twice would double-count the"
                " run against the monthly cap"])
            self.assertEqual(len(self.ledger(tmp)), 1)


class TestRecordRunCLI(cli_contract.ReportContract, unittest.TestCase):
    summary_line = "budget_guard: 0 problem(s)"

    def capture_cli(self, argv, root, at="2026-08-10"):
        """(code, stdout) of one main(...) call, root and clock injected."""
        clock = lambda: datetime(*(int(part) for part in at.split("-")),
                                 tzinfo=timezone.utc)
        return cli_contract.capture(budget_guard.main, argv, clock=clock,
                                    root=Path(root))

    def run_cli(self, argv, root, at="2026-08-10"):
        return self.capture_cli(argv, root, at)[0]

    def clean_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "execution.json"
            path.write_text(json.dumps([TestRecordRun.RESULT]),
                            encoding="utf-8")
            return self.capture_cli(
                ["record-run", "WO-0007", "run-9", "claude-sonnet-5",
                 str(path)], tmp)

    def test_a_refused_run_ends_with_the_same_summary_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.capture_cli(
                ["record-run", "WO-0007", "run-9", "claude-sonnet-5",
                 str(Path(tmp) / "nope.json")], tmp)
        lines = out.splitlines()
        self.assertEqual(code, 1)
        self.assertEqual(lines[-1], "budget_guard: 1 problem(s)")
        self.assertIn("nope.json", lines[0])

    def test_outcome_defaults_to_completed_and_the_clock_stamps_at(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            path = Path(tmp) / "execution.json"
            path.write_text(json.dumps([TestRecordRun.RESULT]),
                            encoding="utf-8")
            code = self.run_cli(
                ["record-run", "WO-0007", "run-9", "claude-sonnet-5",
                 str(path)], tmp)
            self.assertEqual(code, 0)
            row = json.loads((tree.root / "docs" / "factory"
                              / "costs.jsonl").read_text(
                                  encoding="utf-8").splitlines()[0])
            self.assertEqual(row["outcome"], "completed")
            self.assertEqual(row["at"], "2026-08-10")

    def test_an_explicit_outcome_is_recorded_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            path = Path(tmp) / "execution.json"
            path.write_text(json.dumps([TestRecordRun.RESULT]),
                            encoding="utf-8")
            self.assertEqual(self.run_cli(
                ["record-run", "WO-0007", "run-9", "claude-sonnet-5",
                 str(path), "agent-failed"], tmp), 0)
            row = json.loads((tree.root / "docs" / "factory"
                              / "costs.jsonl").read_text(
                                  encoding="utf-8").splitlines()[0])
            self.assertEqual(row["outcome"], "agent-failed")

    def test_a_missing_file_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = self.run_cli(
                ["record-run", "WO-0007", "run-9", "claude-sonnet-5",
                 str(Path(tmp) / "nope.json")], tmp)
            self.assertEqual(code, 1)
            self.assertEqual(
                (Path(tmp) / "docs" / "factory" / "costs.jsonl").is_file(),
                False)

    def test_wrong_arity_prints_usage_rather_than_recording(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_cli(["record-run", "WO-0007"], tmp), 2)


class TestRecordCLI(cli_contract.ReportContract, unittest.TestCase):
    summary_line = "budget_guard: 0 problem(s)"

    def capture_cli(self, argv, root, at="2026-08-07"):
        """(code, stdout) of one main(...) call. The root is INJECTED.
        repo_root() resolves from __file__, so a chdir-only harness would
        write these fabricated rows straight into the real append-only
        ledger — which is how this test was first written, and it did
        exactly that."""
        clock = lambda: datetime(*(int(part) for part in at.split("-")),
                                 tzinfo=timezone.utc)
        return cli_contract.capture(budget_guard.main, argv, clock=clock,
                                    root=Path(root))

    def run_cli(self, argv, root, at="2026-08-07"):
        return self.capture_cli(argv, root, at)[0]

    def clean_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            return self.capture_cli(
                ["record", "WO-0007", "r-1", "claude-sonnet-5", "4200",
                 "1.25"], tmp)

    def test_a_refused_row_ends_with_the_same_summary_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.capture_cli(
                ["record", "WO-0007", "r-1", "claude-sonnet-5", "lots",
                 "free"], tmp)
        lines = out.splitlines()
        self.assertEqual(code, 1)
        self.assertEqual(lines[-1], "budget_guard: 2 problem(s)")
        self.assertEqual(lines[:2], ["bg: tokens 'lots' is not an integer",
                                     "bg: cost 'free' is not a number"])

    def test_outcome_defaults_to_completed_and_the_clock_stamps_at(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            code = self.run_cli(
                ["record", "WO-0007", "r-1", "claude-sonnet-5", "4200",
                 "1.25"], tmp)
            self.assertEqual(code, 0)
            row = json.loads((tree.root / "docs" / "factory"
                              / "costs.jsonl").read_text(
                                  encoding="utf-8").splitlines()[0])
            self.assertEqual(row["outcome"], "completed")
            self.assertEqual(row["at"], "2026-08-07")

    def test_a_non_numeric_token_count_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = self.run_cli(
                ["record", "WO-0007", "r-1", "claude-sonnet-5", "lots",
                 "1.25"], tmp)
            self.assertEqual(code, 1)
            self.assertEqual(
                (Path(tmp) / "docs" / "factory" / "costs.jsonl").is_file(),
                False)

    def test_a_non_numeric_cost_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_cli(
                ["record", "WO-0007", "r-1", "claude-sonnet-5", "4200",
                 "free"], tmp), 1)

    def test_wrong_arity_prints_usage_rather_than_recording(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_cli(["record", "WO-0007"], tmp), 2)


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
            posted.append(text)
            self.assertEqual(posted, [text])
            self.assertIn("cost ledger append", text)
            self.assertIn("factory_init mirrors", text)
            self.assertIn("$16.40", text)

            # Hard-stop: append the run's line to the cost ledger.
            cost_ledger.append(
                tree.root, cost_ledger.entry(
                    "WO-0006", "r-over-budget", "claude-sonnet-5",
                    9500, 16.40, "budget-exhausted", "2026-08-02"))
            ledger = tree.root / "docs" / "factory" / "costs.jsonl"
            self.assertEqual(len(ledger.read_text(
                encoding="utf-8").splitlines()), 1)

            # The appended line satisfies detector G's own shape check —
            # not a re-implementation of G's rules, a cross-check against
            # the real one.
            self.assertEqual(gates.check_cost_ledger(tree.root), [])


class TestMain(cli_contract.CliContract, cli_contract.ReportContract,
               unittest.TestCase):
    usage_fragment = "python3 budget_guard.py check"
    summary_line = "budget_guard: 0 problem(s)"

    def run_cli(self, argv):
        return cli_contract.capture(budget_guard.main, argv)

    def clean_cli(self):
        return self.run_cli(["check", "S", "0.01"])

    def test_a_non_numeric_spend_is_a_problem(self):
        code, out = self.run_cli(["check", "S", "lots"])
        self.assertEqual(code, 1)
        self.assertIn("bg: 'lots' is not a number", out)
        self.assertIn("budget_guard: 1 problem(s)", out)

    def test_a_negative_spend_fails_closed_with_nonzero_exit(self):
        # Fix 2 (review): the CLI must not wave a negative spend through.
        code, out = self.run_cli(["check", "S", "-1"])
        self.assertEqual(code, 1)
        self.assertIn("bg: spend -1.0 is not a finite, non-negative number",
                      out)
        self.assertIn(budget_guard.HARD_STOP, out)
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
