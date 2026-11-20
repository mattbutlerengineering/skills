"""work_queue.py — implement-queue's work-order batch planner (ADR-0127).

Same discipline as test_label_sync/test_gate_digest: the gh CLI is
injected through the shared fake (tests/fake_gh.py, never the network),
the planning core is pure and exercised directly, and tests assert the
exact problem and deferral strings a caller will print.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fake_gh import FakeGh  # noqa: E402
from fixture_tree import FixtureTree  # noqa: E402
from test_work_orders import (  # noqa: E402
    DUP_ISSUE, DUP_WO, NEWER, OLDER, Tree as WorkOrderTree)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cli  # noqa: E402
import work_queue  # noqa: E402

CONFIG = {"budgets_usd": {"S": 5, "M": 15, "L": 40},
          "routing": {}, "wip_cap": 3, "monthly_cap_usd": 300}


def row(wo, done=False, size="S", issue=1, blockers="—", where="b.md:1",
        unreadable=None, clashes=()):
    return {"wo": wo, "done": done, "size": size, "issue": issue,
            "blockers": [] if blockers == "—" else blockers,
            "unreadable": unreadable, "where": where,
            "clashes": list(clashes)}


def found(*rows):
    return {r["wo"]: r for r in rows}


OWNER = "the-owner"


def labeled_by(login):
    return {"event": "labeled", "label": {"name": "wo:ready-for-agent"},
            "created_at": "2026-08-01T00:00:00Z", "actor": {"login": login}}


def listing(*numbers, in_flight=(), labelers=None, owner=OWNER):
    """A gh whose ready listing answers with these issue numbers.

    work_queue's reads, each keyed on its own argv prefix: the ready
    listing (`work_queue.LIST_ARGS`), the in-flight listing
    (`work_queue.IN_FLIGHT_ARGS`), the repo owner (`gh repo view`), and
    each ready issue's timeline. `labelers` maps an issue to the login
    whose labeled event applied the ready label; an issue it does not
    name was labelled by `owner` — the only labeler ADR-0032 honours.
    """
    labelers = labelers or {}

    def timeline(args):
        number = int(args[1].split("/")[-2])
        return json.dumps([[labeled_by(labelers.get(number, owner))]])

    return FakeGh(answers={
        tuple(work_queue.LIST_ARGS[:4]):
            json.dumps([{"number": n} for n in numbers]),
        tuple(work_queue.IN_FLIGHT_ARGS[:4]):
            json.dumps([{"number": n} for n in in_flight]),
        ("repo", "view"): json.dumps({"owner": {"login": owner}}),
        ("api",): timeline})


def unreachable():
    """A gh whose ready listing fails.

    The error is stated rather than inherited: a `CalledProcessError`
    with no stderr is a different `cli.detail` path from the shared
    fake's default, and this suite's problem-string assertions are
    about that path.
    """
    return FakeGh(failing=["issue"],
                  error=subprocess.CalledProcessError(1, "gh"))


class TestEligible(unittest.TestCase):
    def test_a_ready_unblocked_row_is_the_only_candidate(self):
        candidates, deferred = work_queue.eligible(
            found(row("WO-0001", done=True),
                  row("WO-0002", issue=7)), {7})
        self.assertEqual([c["wo"] for c in candidates], ["WO-0002"])
        self.assertEqual(deferred, [])

    def test_every_plane_says_why_it_holds_a_row_back(self):
        _, deferred = work_queue.eligible(
            found(row("WO-0001", done=False, issue=7, blockers=["WO-0009"]),
                  row("WO-0002", issue=None),
                  row("WO-0003", issue=8)), {7})
        self.assertEqual(deferred, [
            "WO-0001: blocked by WO-0009",
            "WO-0002: its row carries no (tracker: #N) mirror, so no issue"
            " can carry the ready label",
            "WO-0003: no open issue #8 carries wo:ready-for-agent — the"
            " owner applies that label, and it does nothing on a closed"
            " issue; the reconcile sweep reports a row whose issue was"
            " closed"])

    def test_the_unready_line_never_claims_the_issue_is_open(self):
        """The listing covers OPEN issues, so a miss is equally "open but
        unlabelled" and "closed". WO-0018/#123 in this repo is the second,
        and the old wording sent the reader to apply a label to a closed
        issue — advice that cannot work. The line now says only what the
        listing proves, and names the sweep that owns the drift."""
        _, deferred = work_queue.eligible(
            found(row("WO-0003", issue=123)), set())
        self.assertEqual(len(deferred), 1)
        self.assertNotIn("that is the opt-in", deferred[0])
        self.assertIn("no open issue #123", deferred[0])
        self.assertIn("reconcile sweep", deferred[0])

    def test_a_blocker_that_is_checked_off_no_longer_blocks(self):
        candidates, deferred = work_queue.eligible(
            found(row("WO-0001", done=True),
                  row("WO-0002", issue=7, blockers=["WO-0001"])), {7})
        self.assertEqual([c["wo"] for c in candidates], ["WO-0002"])
        self.assertEqual(deferred, [])

    def test_a_blocker_with_no_row_at_all_still_blocks(self):
        # an unknown edge is unmet, never assumed satisfied — the failure
        # mode of the other choice is dispatching work whose dependency
        # nobody has written down yet
        _, deferred = work_queue.eligible(
            found(row("WO-0002", issue=7, blockers=["WO-9999"])), {7})
        self.assertEqual(deferred, ["WO-0002: blocked by WO-9999"])


    def test_an_unreadable_blocker_holds_the_row_back(self):
        # Read as "no blockers", this row was a candidate: the fail-open
        # that dispatched work before its dependency (beads wo-o3l).
        candidates, deferred = work_queue.eligible(
            found(row("WO-0002", issue=7, unreadable="Export API")), {7})
        self.assertEqual(candidates, [])
        self.assertEqual(deferred, [
            "WO-0002: blocked by 'Export API', which names no work order,"
            " so its dependency cannot be checked"])


    def test_a_ready_label_the_owner_did_not_apply_holds_the_row_back(self):
        """ADR-0032: only the repo owner may apply wo:ready-for-agent;
        anyone else's label is inert, here as in assembler.yml."""
        candidates, deferred = work_queue.eligible(
            found(row("WO-0002", issue=7)), {7},
            held={7: "carries wo:ready-for-agent applied by drive-by, not"
                     " the owner — inert (ADR-0032)"})
        self.assertEqual(candidates, [])
        self.assertEqual(deferred, [
            "WO-0002: issue #7 carries wo:ready-for-agent applied by"
            " drive-by, not the owner — inert (ADR-0032)"])

    def test_an_order_already_in_flight_is_not_a_candidate_again(self):
        candidates, deferred = work_queue.eligible(
            found(row("WO-0002", issue=7)), {7}, in_flight={7})
        self.assertEqual(candidates, [])
        self.assertEqual(deferred, [
            "WO-0002: issue #7 is already in flight on wo:in-progress"])


class TestPriced(unittest.TestCase):
    def test_cheapest_band_leads(self):
        ordered, problems = work_queue.priced(
            [row("WO-0003", size="L"), row("WO-0001", size="M"),
             row("WO-0002", size="S")], CONFIG)
        self.assertEqual([r["wo"] for r in ordered],
                         ["WO-0002", "WO-0001", "WO-0003"])
        self.assertEqual([r["budget"] for r in ordered], [5, 15, 40])
        self.assertEqual(problems, [])

    def test_an_unpriceable_size_is_dropped_and_reported(self):
        # fail closed: never run a work order at an unknown price
        ordered, problems = work_queue.priced(
            [row("WO-0001", size="XL", where="docs/b.md:9")], CONFIG)
        self.assertEqual(ordered, [])
        self.assertEqual(problems, [
            "wq: WO-0001 (docs/b.md:9) config: factory.json names no"
            " positive budget for size 'XL'"])


class TestPlanBatch(unittest.TestCase):
    def test_the_wip_cap_bounds_the_batch_and_names_the_overflow(self):
        rows = found(*[row(f"WO-000{n}", issue=n) for n in range(1, 5)])
        batch, deferred, problems = work_queue.plan_batch(
            rows, {1, 2, 3, 4}, CONFIG, spent_usd=0)
        self.assertEqual([r["wo"] for r in batch],
                         ["WO-0001", "WO-0002", "WO-0003"])
        self.assertEqual(deferred,
                         ["WO-0004: over the wip_cap of 3 this round"])
        self.assertEqual(problems, [])

    def test_the_monthly_cap_refuses_a_batch_before_it_is_paid_for(self):
        rows = found(row("WO-0001", size="L", issue=1))
        batch, deferred, problems = work_queue.plan_batch(
            rows, {1}, CONFIG, spent_usd=290)
        self.assertEqual(batch, [])
        self.assertEqual(deferred, [
            "WO-0001: would put the month over its $300.00 cap ($290.00"
            " spent, $0.00 already planned, size:L budgets $40.00)"])
        self.assertEqual(problems, [])

    def test_the_cap_counts_what_this_batch_already_planned(self):
        # the second order must be priced against the first one's budget,
        # or a batch walks past the cap one affordable-looking order at a
        # time
        rows = found(row("WO-0001", size="M", issue=1),
                     row("WO-0002", size="M", issue=2))
        batch, deferred, _ = work_queue.plan_batch(
            rows, {1, 2}, CONFIG, spent_usd=280)
        self.assertEqual([r["wo"] for r in batch], ["WO-0001"])
        self.assertIn("$15.00 already planned", deferred[0])

    def test_an_unresolvable_cap_refuses_to_plan(self):
        # fail closed, the same rule an unpriceable size gets: an
        # unresolvable cap is an unknown ceiling, not an absent one
        capless = {k: v for k, v in CONFIG.items() if k != "monthly_cap_usd"}
        batch, _, problems = work_queue.plan_batch(
            found(row("WO-0001", issue=1)), {1}, capless, spent_usd=0)
        self.assertEqual(batch, [])
        self.assertEqual(problems, [
            "config: factory.json names no positive monthly_cap_usd",
            "wq: no monthly cap could be resolved — refusing to plan a"
            " batch it cannot price"])

    def test_an_unresolvable_cap_is_not_an_unlimited_one(self):
        # the hazard the refusal closes: with the comparison skipped,
        # a month that has already spent a fortune plans a full batch
        capless = {k: v for k, v in CONFIG.items() if k != "monthly_cap_usd"}
        rows = found(*[row(f"WO-000{n}", size="L", issue=n)
                       for n in range(1, 4)])
        batch, _, _ = work_queue.plan_batch(rows, {1, 2, 3}, capless,
                                            spent_usd=999999.0)
        self.assertEqual(batch, [])

    def test_the_refusal_still_reports_the_near_misses(self):
        # refusing to plan is not refusing to explain — the wip_cap
        # refusal hands back eligible's deferrals too
        capless = {k: v for k, v in CONFIG.items() if k != "monthly_cap_usd"}
        rows = found(row("WO-0001", issue=1),
                     row("WO-0002", issue=None))
        _, deferred, _ = work_queue.plan_batch(rows, {1}, capless,
                                               spent_usd=0)
        self.assertEqual(deferred, [
            "WO-0002: its row carries no (tracker: #N) mirror, so no"
            " issue can carry the ready label"])

    def test_a_missing_wip_cap_refuses_to_guess(self):
        batch, _, problems = work_queue.plan_batch(
            found(row("WO-0001", issue=1)), {1},
            dict(CONFIG, wip_cap=0), spent_usd=0)
        self.assertEqual(batch, [])
        self.assertEqual(problems, [
            "wq: factory.json wip_cap must be a positive integer —"
            " refusing to guess a batch size"])

    def test_a_boolean_wip_cap_is_not_a_number(self):
        # True is an int in Python; a config that says `"wip_cap": true`
        # must not silently mean a batch of one
        _, _, problems = work_queue.plan_batch(
            found(row("WO-0001", issue=1)), {1},
            dict(CONFIG, wip_cap=True), spent_usd=0)
        self.assertIn("wip_cap must be a positive integer", problems[0])


class TestInFlight(unittest.TestCase):
    """Orders already on wo:in-progress hold wip slots and budget money
    that the ledger has not recorded yet — the Conductor survey's
    wip_cap-minus-in-flight rule, applied to the work-order planner."""

    def test_in_flight_orders_take_wip_slots(self):
        rows = found(*[row(f"WO-000{n}", issue=n) for n in range(1, 4)],
                     row("WO-0009", issue=9))
        batch, deferred, problems = work_queue.plan_batch(
            rows, {1, 2, 3}, CONFIG, spent_usd=0, in_flight={9})
        self.assertEqual([r["wo"] for r in batch], ["WO-0001", "WO-0002"])
        self.assertEqual(deferred, [
            "WO-0003: over the wip_cap of 3 this round (1 already in"
            " flight)",
            "WO-0009: issue #9 is already in flight on wo:in-progress"])
        self.assertEqual(problems, [])

    def test_a_full_house_in_flight_plans_nothing(self):
        rows = found(row("WO-0001", issue=1),
                     *[row(f"WO-000{n}", issue=n) for n in range(7, 10)])
        batch, deferred, _ = work_queue.plan_batch(
            rows, {1}, CONFIG, spent_usd=0, in_flight={7, 8, 9})
        self.assertEqual(batch, [])
        self.assertEqual(deferred, [
            "WO-0001: over the wip_cap of 3 this round (3 already in"
            " flight)",
            *[f"WO-000{n}: issue #{n} is already in flight on"
              " wo:in-progress" for n in range(7, 10)]])

    def test_in_flight_budgets_count_against_the_monthly_cap(self):
        rows = found(row("WO-0001", size="M", issue=1),
                     row("WO-0009", size="L", issue=9))
        batch, deferred, problems = work_queue.plan_batch(
            rows, {1}, CONFIG, spent_usd=250, in_flight={9})
        self.assertEqual(batch, [])
        self.assertEqual(deferred, [
            "WO-0001: would put the month over its $300.00 cap ($250.00"
            " spent, $40.00 budgeted in flight, $0.00 already planned,"
            " size:M budgets $15.00)",
            "WO-0009: issue #9 is already in flight on wo:in-progress"])
        self.assertEqual(problems, [])

    def test_an_unpriceable_in_flight_order_refuses_the_plan(self):
        """ADR-0034's fail-closed rule: money already committed at an
        unknown price is an unknown spend, not a zero one."""
        rows = found(row("WO-0001", issue=1),
                     row("WO-0008", size="XL", issue=8, where="b.md:8"))
        batch, _, problems = work_queue.plan_batch(
            rows, {1}, CONFIG, spent_usd=0, in_flight={8, 9})
        self.assertEqual(batch, [])
        self.assertEqual(problems, [
            "wq: WO-0008 (b.md:8) config: factory.json names no positive"
            " budget for size 'XL'",
            "wq: issue #9 is on wo:in-progress but no breakdown row"
            " mirrors it, so its budget is unknown",
            "wq: an order in flight cannot be priced — refusing to plan a"
            " batch against a spend it cannot know"])

    def test_the_in_flight_listing_asks_for_open_claimed_issues(self):
        runner = listing(in_flight=(4, 5))
        numbers, problems = work_queue.in_flight_issue_numbers(runner)
        self.assertEqual((numbers, problems), ({4, 5}, []))
        self.assertIn("wo:in-progress", runner.calls[0])
        self.assertIn("open", runner.calls[0])

    def test_a_full_in_flight_window_is_refused(self):
        numbers, problems = work_queue.in_flight_issue_numbers(
            listing(in_flight=range(100)))
        self.assertIsNone(numbers)
        self.assertEqual(len(problems), 1)
        self.assertIn("older in-flight orders are invisible", problems[0])


class TestOwnerHolds(unittest.TestCase):
    """ADR-0032: the ready label is the owner's. The planner asks each
    ready issue's timeline who applied it last, and treats the owner
    exactly as assembler.actor_is_owner does."""

    def test_the_owner_s_label_holds_nothing_back(self):
        self.assertEqual(work_queue.owner_holds([7], listing(7)), ({}, []))

    def test_the_owner_is_matched_case_insensitively(self):
        run = listing(7, labelers={7: "The-Owner"})
        self.assertEqual(work_queue.owner_holds([7], run), ({}, []))

    def test_anyone_else_s_label_is_inert(self):
        run = listing(7, 8, labelers={8: "drive-by"})
        self.assertEqual(work_queue.owner_holds([7, 8], run), ({
            8: "carries wo:ready-for-agent applied by drive-by, not the"
               " owner — inert (ADR-0032)"}, []))

    def test_an_unreadable_timeline_fails_closed(self):
        run = FakeGh(answers={("repo", "view"):
                              json.dumps({"owner": {"login": OWNER}})},
                     failing=["api"])
        self.assertEqual(work_queue.owner_holds([7], run), ({
            7: "carries wo:ready-for-agent, but who applied it could not"
               " be read — held back until it can be (ADR-0032)"},
            ["wq: gh api timeline for #7 failed: boom"]))

    def test_a_timeline_with_no_labeled_event_fails_closed(self):
        run = FakeGh(answers={("repo", "view"):
                              json.dumps({"owner": {"login": OWNER}}),
                              ("api",): json.dumps([[]])})
        self.assertEqual(work_queue.owner_holds([7], run), ({
            7: "carries wo:ready-for-agent, but who applied it could not"
               " be read — held back until it can be (ADR-0032)"},
            ["wq: issue #7's timeline holds no event applying"
             " wo:ready-for-agent, so who applied it is unknown"]))

    def test_an_unknown_owner_trusts_no_label(self):
        holds, problems = work_queue.owner_holds(
            [7], FakeGh(failing=["repo"]))
        self.assertIsNone(holds)
        self.assertEqual(problems, ["wq: gh repo view failed: boom"])

    def test_no_ready_issue_reads_nothing(self):
        run = listing()
        self.assertEqual(work_queue.owner_holds([], run), ({}, []))
        self.assertEqual(run.calls, [])


class TestReadyIssueNumbers(unittest.TestCase):
    def test_it_asks_for_open_ready_labelled_issues(self):
        runner = listing(7, 8)
        numbers, problems = work_queue.ready_issue_numbers(runner)
        self.assertEqual(numbers, {7, 8})
        self.assertEqual(problems, [])
        self.assertIn("wo:ready-for-agent", runner.calls[0])
        self.assertIn("--state", runner.calls[0])

    def test_an_unreachable_tracker_is_a_problem_not_an_empty_queue(self):
        numbers, problems = work_queue.ready_issue_numbers(
            unreachable())
        self.assertIsNone(numbers)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("wq: gh issue list failed:"))

    def test_a_full_window_is_refused_rather_than_trusted(self):
        """Same rule as sweeps.live_issues: past the window an issue is
        simply absent, and absence is what the ready check reads as a
        finding. A truncated listing is no listing."""
        runner = listing(*range(100))
        numbers, problems = work_queue.ready_issue_numbers(runner)
        self.assertIsNone(numbers)
        self.assertEqual(len(problems), 1)
        self.assertIn("full 100-entry window", problems[0])

    def test_the_full_window_message_names_a_reachable_remedy(self):
        """gh_read's default note reads like a runtime option ("raise the
        window or narrow the query"); neither is reachable here —
        LIST_WINDOW is a module constant, and in a stamped repo this tool
        is a mirrored payload copy. The message must say the remedy is a
        code edit, not imply a flag (ADR-0066, issue #449)."""
        runner = listing(*range(100))
        _, problems = work_queue.ready_issue_numbers(runner)
        self.assertEqual(len(problems), 1)
        self.assertIn("LIST_WINDOW", problems[0])
        self.assertIn("not a runtime option", problems[0])
        self.assertNotIn("raise the window or narrow the query",
                         problems[0])


class TestRowsAndSpend(unittest.TestCase):
    def test_rows_reads_the_row_grammar_off_a_real_breakdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/features/demo/breakdown.md",
                       "- [x] **WO-0001** done — size:M, blocked by: —"
                       " (PRD-0001 §S) (tracker: #106)\n"
                       "- [ ] **WO-0002** open — size:S, blocked by:"
                       " WO-0001 (PRD-0001 §S) (tracker: #107)\n"
                       "  - Accept: not a row\n")
            found_rows = work_queue.rows(tree.root)
            self.assertEqual(sorted(found_rows), ["WO-0001", "WO-0002"])
            self.assertTrue(found_rows["WO-0001"]["done"])
            self.assertEqual(found_rows["WO-0002"]["size"], "S")
            self.assertEqual(found_rows["WO-0002"]["blockers"], ["WO-0001"])
            self.assertEqual(found_rows["WO-0002"]["issue"], 107)
            self.assertIsNone(found_rows["WO-0002"]["unreadable"])

    def test_a_template_style_blocked_by_sub_bullet_blocks_the_row(self):
        # #1997: decompose's template writes `  - Blocked by: <item>`.
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/features/demo/breakdown.md",
                       "- [ ] **WO-0001** base — size:S"
                       " (PRD-0001 §S) (tracker: #106)\n"
                       "- [ ] **WO-0002** polish — size:M"
                       " (PRD-0001 §S) (tracker: #107)\n"
                       "  - Accept: it works\n"
                       "  - Blocked by: WO-0001\n"
                       "- [ ] **WO-0003** other — size:M"
                       " (PRD-0001 §S) (tracker: #108)\n"
                       "  - Blocked by: Export API\n")
            found_rows = work_queue.rows(tree.root)
            self.assertEqual(found_rows["WO-0002"]["blockers"], ["WO-0001"])
            self.assertEqual(found_rows["WO-0003"]["unreadable"],
                             "Export API")
            _, deferred = work_queue.eligible(found_rows, {106, 107, 108})
            self.assertIn("WO-0002: blocked by WO-0001", deferred)

    def test_rows_carries_what_a_clause_could_not_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/features/demo/breakdown.md",
                       "- [ ] **WO-0002** open — size:S, blocked by:"
                       " Export API (PRD-0001 §S) (tracker: #107)\n")
            found_rows = work_queue.rows(tree.root)
            self.assertEqual(found_rows["WO-0002"]["unreadable"],
                             "Export API")

    def test_a_duplicated_row_is_deferred_as_the_dispatcher_refuses_it(self):
        # Issue #885: rows() kept its own walk and let the last duplicate
        # win, so the queue planned #9 as WO-0001 while the dispatcher
        # refuses both clashing rows. It now reads work_orders' index.
        with tempfile.TemporaryDirectory() as tmp:
            root = WorkOrderTree(tmp, OLDER, NEWER).root
            found_rows = work_queue.rows(root)
            self.assertEqual(found_rows["WO-0001"]["issue"], 5)
            self.assertEqual(found_rows["WO-0001"]["where"],
                             "docs/breakdown.md:3")
            candidates, deferred = work_queue.eligible(found_rows, {5, 9})
        self.assertEqual(candidates, [])
        self.assertEqual(deferred, [f"WO-0001: {DUP_WO}",
                                    f"WO-0002: {DUP_ISSUE}"])

    def test_a_blocker_reads_the_done_the_dispatcher_sees(self):
        # Issue #885's reproduction: the first WO-0001 row is checked
        # off, so WO-0002 is unblocked; the open copy is deferred.
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/features/demo/breakdown.md",
                       "- [x] **WO-0001** first (tracker: #5) size:S\n"
                       "- [ ] **WO-0001** copy (tracker: #9) size:L\n"
                       "- [ ] **WO-0002** next (tracker: #7) size:S,"
                       " blocked by: WO-0001\n")
            candidates, deferred = work_queue.eligible(
                work_queue.rows(tree.root), {5, 7, 9})
        self.assertEqual([c["wo"] for c in candidates], ["WO-0002"])
        self.assertEqual(deferred, [
            "WO-0001: docs/features/demo/breakdown.md:2 WO-0001"
            " duplicates the row at docs/features/demo/breakdown.md:1"])

    def test_month_to_date_counts_only_this_month(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/factory/costs.jsonl", "\n".join(
                json.dumps({"wo": f"WO-000{n}", "run_id": f"r{n}",
                            "model": "m", "tokens": 1, "cost": cost,
                            "outcome": "merged", "at": at})
                for n, (cost, at) in enumerate(
                    [(10, "2026-08-04"), (7, "2026-08-30"),
                     (99, "2026-07-31")], start=1)) + "\n")
            spent, problems = work_queue.month_to_date(
                tree.root, datetime(2026, 8, 6, tzinfo=timezone.utc))
            self.assertEqual(spent, 17)
            self.assertEqual(problems, [])

    def test_no_ledger_yet_is_zero_spent_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            spent, problems = work_queue.month_to_date(
                Path(tmp), datetime(2026, 8, 6, tzinfo=timezone.utc))
            self.assertEqual((spent, problems), (0, []))

    def test_a_ledger_that_is_not_utf8_is_a_problem_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/factory/costs.jsonl", "").write_bytes(
                b"\xff\xfe\x00")
            self.assertEqual(
                work_queue.month_to_date(
                    tree.root, datetime(2026, 8, 6, tzinfo=timezone.utc)),
                (0, ["ledger: cannot read docs/factory/costs.jsonl: 'utf-8'"
                     " codec can't decode byte 0xff in position 0: invalid"
                     " start byte"]))


class TestMain(cli_contract.ReportContract, unittest.TestCase):
    """main's summary line, on every leg that emits one.

    work_queue reaches its root through knowledge_plane.repo_root (no
    root parameter), so a leg that needs a tree of its own patches the
    name work_queue imported; the clean leg runs against the real repo,
    the same precedent as test_cost_report/test_budget_guard's TestMain.
    """
    summary_line = "wq: 0 problem(s)"

    def planned(self, argv, run=None, root=None):
        """(code, stdout) of one `plan` run, gh injected, optionally
        rooted at a fixture tree."""
        run = run or listing()
        if root is None:
            return cli_contract.capture(work_queue.main, argv, run=run)
        with mock.patch.object(work_queue, "repo_root", lambda: root):
            return cli_contract.capture(work_queue.main, argv, run=run)

    def clean_cli(self):
        # nothing carries the ready label, so nothing is eligible — and
        # nothing eligible is not a problem
        return self.planned(["plan"])

    def config_tree(self, tmp, breakdown=None):
        tree = FixtureTree(tmp)
        tree.write(".github/factory.json", json.dumps(CONFIG))
        if breakdown:
            tree.write("docs/features/demo/breakdown.md", breakdown)
        return tree

    def test_a_config_naming_no_cap_plans_nothing(self):
        """The refusal at the surface a consumer reads. The skill runs
        what `plan` prints; an unresolvable cap must not put a work
        order on that list."""
        capless = {k: v for k, v in CONFIG.items() if k != "monthly_cap_usd"}
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/factory.json", json.dumps(capless))
            tree.write(
                "docs/features/demo/breakdown.md",
                "- [ ] **WO-0001** ready and priced — size:S, blocked by: —"
                " (PRD-0001 §S) (tracker: #7)\n")
            code, out = self.planned(
                ["plan"], run=listing(7),
                root=tree.root)
        self.assertEqual(code, 1)
        self.assertNotIn("WO-0001  size:S", out)
        self.assertIn("refusing to plan a batch it cannot price", out)
        self.assertEqual(out.splitlines()[-1], "wq: 2 problem(s)")

    def test_an_unreadable_ledger_plans_no_batch(self):
        # Issue #1893: spend summed over the parsed rows was understated,
        # yet the plan opened with "1 work order(s) ready".
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.config_tree(
                tmp, "- [ ] **WO-0002** ready — size:M, blocked by: —"
                " (PRD-0001 §S) (tracker: #7)\n")
            tree.write("docs/factory/costs.jsonl", "\n".join(
                json.dumps({"wo": f"WO-000{n}", "run_id": f"r{n}",
                            "model": model, "tokens": 1, "cost": cost,
                            "outcome": "merged", "at": "2026-08-04"})
                for n, (cost, model) in enumerate(
                    [(10, "m"), (290, "")], start=1)) + "\n")
            with mock.patch.object(
                    work_queue, "_utcnow",
                    lambda: datetime(2026, 8, 6, tzinfo=timezone.utc)):
                code, out = self.planned(["plan"], run=listing(7),
                                         root=tree.root)
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            "ledger: docs/factory/costs.jsonl:2 model must be a non-empty"
            " string",
            "wq: month-to-date spend is unreadable — refusing to plan a"
            " batch it cannot price",
            "wq: 2 problem(s)"])

    def test_an_untrusted_listing_defers_no_row_for_a_reason_it_cannot_know(
            self):
        """The hazard the refusal closes. Past the 100-entry window an
        issue is invisible, and `eligible` reads a miss as "no open issue
        #N carries the ready label" — inventing drift and sending the
        owner to apply a label the issue may already carry."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.config_tree(
                tmp,
                "- [ ] **WO-0001** past the window — size:S, blocked by: —"
                " (PRD-0001 §S) (tracker: #999)\n")
            code, out = self.planned(
                ["plan"],
                run=listing(*range(100)),
                root=tree.root)
        self.assertEqual(code, 1)
        self.assertIn("full 100-entry window", out)
        self.assertNotIn("no open issue #999", out)
        self.assertEqual(out.splitlines()[-1], "wq: 1 problem(s)")

    def test_an_untrusted_listing_claims_no_count_either(self):
        """The refusal's other half. Holding every row back is only honest
        if the tool also stops announcing a batch size: "0 work order(s)
        ready" is the very sentence ready_issue_numbers refuses to let a
        broken listing produce, and it is the line a reader skims first."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.config_tree(
                tmp,
                "- [ ] **WO-0001** past the window — size:S, blocked by: —"
                " (PRD-0001 §S) (tracker: #999)\n")
            code, out = self.planned(
                ["plan"],
                run=listing(*range(100)),
                root=tree.root)
        self.assertEqual(code, 1)
        self.assertNotIn("ready to run in parallel", out)
        self.assertEqual(
            out.splitlines(),
            ["wq: gh issue list returned a full 100-entry window — older"
             " ready orders are invisible; LIST_WINDOW is a code constant"
             " in work_queue.py, not a runtime option, so the fix is"
             " raising it there (or narrowing LIST_ARGS) and redeploying",
             "wq: 1 problem(s)"])

    def test_a_non_owner_ready_label_plans_nothing_and_says_why(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.config_tree(
                tmp, "- [ ] **WO-0001** ready — size:S, blocked by: —"
                " (PRD-0001 §S) (tracker: #7)\n")
            code, out = self.planned(
                ["plan"], run=listing(7, labelers={7: "drive-by"}),
                root=tree.root)
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "wq: 0 work order(s) ready to run in parallel (wip_cap 3)",
            "  deferred WO-0001: issue #7 carries wo:ready-for-agent"
            " applied by drive-by, not the owner — inert (ADR-0032)",
            "wq: 0 problem(s)"])

    def test_orders_in_flight_fill_the_wip_cap(self):
        breakdown = "".join(
            f"- [ ] **WO-000{n}** order — size:S, blocked by: —"
            f" (PRD-0001 §S) (tracker: #{n})\n" for n in range(1, 5))
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.config_tree(tmp, breakdown)
            code, out = self.planned(
                ["plan", "--json"], run=listing(1, in_flight=(2, 3, 4)),
                root=tree.root)
        payload = json.loads("\n".join(out.splitlines()[:-1]))
        self.assertEqual(code, 0)
        self.assertEqual(payload["batch"], [])
        self.assertEqual(payload["deferred"], [
            "WO-0001: over the wip_cap of 3 this round (3 already in"
            " flight)",
            *[f"WO-000{n}: issue #{n} is already in flight on"
              " wo:in-progress" for n in range(2, 5)]])

    def test_an_unreadable_in_flight_listing_plans_nothing(self):
        run = listing(1)
        run.failing = ["issue", "list", "--label", "wo:in-progress"]
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.config_tree(
                tmp, "- [ ] **WO-0001** order — size:S, blocked by: —"
                " (PRD-0001 §S) (tracker: #1)\n")
            code, out = self.planned(["plan"], run=run, root=tree.root)
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            "wq: gh issue list failed: boom", "wq: 1 problem(s)"])

    def test_a_config_failure_ends_with_the_same_summary_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.planned(["plan"], root=Path(tmp))
        lines = out.splitlines()
        self.assertEqual(code, 1)
        self.assertEqual(lines[-1], "wq: 1 problem(s)")
        self.assertTrue(lines[0].startswith("config: missing factory.json"))

    def test_the_json_leg_prints_the_payload_then_the_summary(self):
        code, out = self.planned(["plan", "--json"])
        lines = out.splitlines()
        self.assertEqual(code, 0)
        self.assertEqual(lines[-1], "wq: 0 problem(s)")
        payload = json.loads("\n".join(lines[:-1]))
        self.assertEqual(payload["problems"], [])
        self.assertIn("batch", payload)

    def test_the_json_leg_carries_problems_instead_of_printing_them(self):
        # the one leg the ADR-0051 epilogue does not fit: problems ride
        # inside the payload, so printing them again would both duplicate
        # them and put non-JSON above the object a reader parses
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.planned(
                ["plan", "--json"],
                run=unreachable(),
                root=self.config_tree(tmp).root)
        lines = out.splitlines()
        self.assertEqual(code, 1)
        self.assertEqual(lines[-1], "wq: 1 problem(s)")
        payload = json.loads("\n".join(lines[:-1]))
        self.assertEqual(len(payload["problems"]), 1)
        self.assertEqual(out.count("gh issue list failed"), 1)

    def test_the_json_summary_is_the_seam_s_own_grammar(self):
        """The --json leg prints its summary itself (ADR-0051's epilogue
        cannot serve a leg whose problems ride inside the payload), so
        this lockstep is the only thing holding the two spellings
        together — the same split-contract idiom as the workflow-output
        lockstep tests."""
        with tempfile.TemporaryDirectory() as tmp:
            _, out = self.planned(
                ["plan", "--json"],
                run=unreachable(),
                root=self.config_tree(tmp).root)
        _, seam = cli_contract.capture(cli.report, "wq", ["one problem"])
        self.assertEqual(out.splitlines()[-1], seam.splitlines()[-1])

    def test_the_report_leg_prints_problems_above_the_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.planned(
                ["plan"],
                run=unreachable(),
                root=self.config_tree(tmp).root)
        lines = out.splitlines()
        self.assertEqual(code, 1)
        self.assertEqual(lines[-1], "wq: 1 problem(s)")
        self.assertTrue(lines[-2].startswith("wq: gh issue list failed:"))


if __name__ == "__main__":
    unittest.main()
