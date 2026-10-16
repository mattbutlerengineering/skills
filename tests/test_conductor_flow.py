"""conductor_flow.py (PRD-0013, WO-0157): the item state machine and the
stall rule in `next` — pure-function + fixture tests in test_conductor's
discipline: every external call (git, the pid probe) goes through an
injected fake, and tests assert the EXACT problem strings.
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import conductor
import conductor_flow as flow

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fake_git import FakeGit  # noqa: E402

LEDGER = "docs/factory/batches/b1/ledger.jsonl"
AT = "2026-10-10T12:00:00Z"
NOW = datetime(2026, 10, 10, 12, 30, tzinfo=timezone.utc)


def clock():
    return NOW


def step(name, charter, band):
    return {"step": name, "charter": charter, "band": band, "model": "m",
            "effort": "medium", "ceiling_usd": 3.0}


FEATURE_STEPS = [step("spec", "architect", "architecture_review"),
                 step("build", "swe", "implementation"),
                 step("verify", "qa", "implementation"),
                 step("review", "reviewer", "architecture_review"),
                 step("ship", "qa", "implementation")]


def item(key, item_type, size="M"):
    steps = (FEATURE_STEPS if item_type != "order" else FEATURE_STEPS[1:])
    return {"item": key, "type": item_type, "size": size, "steps": steps,
            "estimate_usd": 15, "after": []}


PLAN = {"at": AT, "kind": "plan", "item": None, "batch": "b1",
        "items": [item("#12", "feature"), item("#13", "fix", "S"),
                  item("#14", "order")],
        "policy": {"routing": {}, "effort": {}}, "estimate_usd": 45,
        "month_to_date_usd": 0.0, "cap_usd": 300}
SPEND = {"at": AT, "kind": "ask", "item": None, "id": "ask-1",
         "ask_kind": "spend", "question": "Spend?",
         "options": ["approve", "decline"], "recommended": "approve",
         "why": "fits"}


def answered(ask_id, choice, item=None, at=AT):
    return {"at": at, "kind": "answer", "item": item, "ask": ask_id,
            "choice": choice, "note": ""}


START = [PLAN, SPEND, answered("ask-1", "approve")]


def run_id(key, name, seq=1):
    return f"conductor-b1-{key[1:]}-{name}-{seq}"


def moved(key, frm, to, at=AT, **extra):
    return {"at": at, "kind": "state", "item": key, "from": frm, "to": to,
            "reason": "r", **extra}


def launch(key, frm, name, seq=1, pid=100, at=AT):
    return moved(key, frm, name, at=at, run_id=run_id(key, name, seq),
                 pid=pid)


def ran(key, name, seq=1, outcome="completed", at=AT):
    return {"at": at, "kind": "run", "item": key, "step": name,
            "charter": "c", "band": "implementation", "model": "m",
            "models_reported": ["m"], "effort": "medium",
            "run_id": run_id(key, name, seq), "pid": 100,
            "outcome": outcome}


def stall_ask(ask_id, key, options=("retry", "retry-up", "block")):
    return {"at": AT, "kind": "ask", "item": key, "id": ask_id,
            "ask_kind": "stall", "question": "Stalled?",
            "options": list(options), "recommended": options[0],
            "why": "w"}


def gate_ask(ask_id, key):
    return {"at": AT, "kind": "ask", "item": key, "id": ask_id,
            "ask_kind": "gate", "question": "Gate?",
            "options": ["approve", "block"], "recommended": "approve",
            "why": "w", "gate_blobs": {}}


def alive(pid):
    return True


def dead(pid):
    return False


class TestTransitions(unittest.TestCase):
    def problems(self, rows, key, to, **fields):
        return flow.transition_problems(START + rows, key, to, fields)

    def test_a_feature_walks_the_whole_sequence(self):
        rows = []
        path = [("planned", "spec"), ("spec", "awaiting-gate"),
                ("awaiting-gate", "build"), ("build", "verify"),
                ("verify", "review"), ("review", "reviewed"),
                ("reviewed", "ship"), ("ship", "merging"),
                ("merging", "merged")]
        for frm, to in path:
            fields = ({"verdict": "pass", "author_runs": ["a"],
                       "reviewer_run": "r"} if to == "reviewed" else {})
            if to == "build":
                rows += [gate_ask("ask-2", "#12"),
                         answered("ask-2", "approve", "#12")]
            self.assertEqual(self.problems(rows, "#12", to, **fields), [],
                             (frm, to))
            rows.append(moved("#12", frm, to, **fields))

    def test_a_feature_never_skips_its_gate(self):
        self.assertEqual(
            self.problems([moved("#12", "planned", "spec")], "#12",
                          "build"),
            ["cd: #12 cannot move from spec to build"])

    def test_a_fix_may_skip_the_gate(self):
        self.assertEqual(
            self.problems([moved("#13", "planned", "spec")], "#13",
                          "build"), [])

    def test_an_order_starts_at_build(self):
        self.assertEqual(self.problems([], "#14", "build"), [])
        self.assertEqual(self.problems([], "#14", "spec"),
                         ["cd: #14 cannot move from planned to spec"])

    def test_states_cannot_be_skipped(self):
        self.assertEqual(self.problems([], "#12", "verify"),
                         ["cd: #12 cannot move from planned to verify"])

    def test_the_gate_opens_only_on_an_approve_answer(self):
        rows = [moved("#12", "planned", "spec"),
                moved("#12", "spec", "awaiting-gate"),
                gate_ask("ask-2", "#12")]
        self.assertEqual(self.problems(rows, "#12", "build"), [
            "cd: #12 has an unanswered ask (ask-2)"])
        self.assertEqual(
            self.problems(rows + [answered("ask-2", "block", "#12")],
                          "#12", "build"),
            ["cd: #12 leaves awaiting-gate only after an approve answer"
             " to its gate ask"])

    def test_any_non_terminal_state_may_stall(self):
        for frm in ("planned", "spec", "build", "review", "merging"):
            rows = [] if frm == "planned" else [moved("#12", "x", frm)]
            self.assertEqual(self.problems(rows, "#12", "stalled"), [], frm)

    def test_terminal_states_never_move(self):
        for terminal in ("merged", "blocked"):
            self.assertEqual(
                self.problems([moved("#12", "x", terminal)], "#12",
                              "stalled"),
                [f"cd: #12 is {terminal}, and {terminal} is terminal"])

    def test_blocked_is_reached_only_through_an_answer(self):
        self.assertEqual(self.problems([], "#12", "blocked"), [
            "cd: #12 is blocked only by a block answer to one of its"
            " asks"])

    def test_a_stalled_item_resumes_its_step_after_a_retry(self):
        rows = [launch("#12", "planned", "spec"),
                moved("#12", "spec", "stalled"), stall_ask("ask-2", "#12")]
        self.assertEqual(self.problems(rows, "#12", "spec"), [
            "cd: #12 has an unanswered ask (ask-2)"])
        for choice in ("retry", "retry-up"):
            self.assertEqual(self.problems(
                rows + [answered("ask-2", choice, "#12")], "#12", "spec"),
                [], choice)
        self.assertEqual(self.problems(
            rows + [answered("ask-2", "retry", "#12")], "#12", "build"),
            ["cd: #12 leaves stalled only for spec, after a retry answer"])

    def test_the_first_request_for_changes_returns_to_build_once(self):
        rows = [moved("#12", "x", "review")]
        self.assertEqual(self.problems(rows, "#12", "build"), [])
        rows += [moved("#12", "review", "build"),
                 moved("#12", "build", "verify"),
                 moved("#12", "verify", "review")]
        self.assertEqual(self.problems(rows, "#12", "build"),
                         ["cd: #12 cannot move from review to build"])

    def test_a_reviewer_who_wrote_the_item_cannot_pass_it(self):
        rows = [moved("#12", "x", "review")]
        self.assertEqual(self.problems(
            rows, "#12", "reviewed", verdict="pass",
            author_runs=["conductor-b1-12-build-1"],
            reviewer_run="conductor-b1-12-build-1"),
            ["cd: #12 reviewed pass refused: reviewer run"
             " conductor-b1-12-build-1 is among its author runs"])

    def test_a_launch_waits_for_the_items_unanswered_ask(self):
        rows = [stall_ask("ask-2", "#12")]
        self.assertEqual(self.problems(rows, "#12", "spec",
                                       run_id="r", pid=1),
                         ["cd: #12 has an unanswered ask (ask-2)"])

    def test_a_step_still_in_flight_is_never_launched_twice(self):
        # Review finding: build -> build is a legal move, so a second
        # runner launched from a stale `next` passed while the first
        # build run had no finishing row, both Workers sharing one
        # worktree and one run id.
        rows = [launch("#13", "planned", "spec"), ran("#13", "spec"),
                launch("#13", "spec", "build")]
        self.assertEqual(
            self.problems(rows, "#13", "build", run_id="r2", pid=2),
            ["cd: #13's build run conductor-b1-13-build-1 is still in"
             " flight"])
        self.assertEqual(self.problems(rows, "#13", "stalled"), [])
        self.assertEqual(self.problems(rows + [ran("#13", "build")], "#13",
                                       "build", run_id="r2", pid=2), [])

    def test_an_item_outside_the_plan_is_refused(self):
        self.assertEqual(self.problems([], "#99", "spec"),
                         ["cd: #99 is not an item of this batch's plan"])


class TestMove(unittest.TestCase):
    def test_a_legal_move_is_appended_and_an_illegal_one_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / LEDGER
            path.parent.mkdir(parents=True)
            path.write_text("".join(json.dumps(r) + "\n" for r in START))
            row, problems = flow.move(tmp, "b1", NOW, "#12", "spec",
                                      "launched", run_id="r1", pid=7)
            self.assertEqual(problems, [])
            self.assertEqual(row, {
                "at": "2026-10-10T12:30:00Z", "kind": "state",
                "item": "#12", "from": "planned", "to": "spec",
                "reason": "launched", "run_id": "r1", "pid": 7})
            before = path.read_bytes()
            row, problems = flow.move(tmp, "b1", NOW, "#12", "ship", "x")
            self.assertEqual(path.read_bytes(), before)
        self.assertEqual((row, problems),
                         (None, ["cd: #12 cannot move from spec to ship"]))


class TestSurveyReady(unittest.TestCase):
    def survey(self, rows, wip_cap=3, probe=alive, facts=None, now=NOW):
        return flow.survey(START + rows, now, wip_cap, probe, facts or {})

    def test_planned_items_are_ready_for_their_first_step(self):
        ready, writes, problems = self.survey([])
        self.assertEqual((writes, problems), ([], []))
        self.assertEqual(ready, [{"item": "#12", "step": "spec"},
                                 {"item": "#13", "step": "spec"},
                                 {"item": "#14", "step": "build"}])

    def test_the_wip_cap_counts_runs_in_flight(self):
        ready, _, _ = self.survey([launch("#12", "planned", "spec")],
                                  wip_cap=2)
        self.assertEqual(ready, [{"item": "#13", "step": "spec"}])

    def test_an_unanswered_batch_ask_holds_all_dispatch(self):
        ready, _, _ = flow.survey([PLAN, SPEND], NOW, 3, alive, {})
        self.assertEqual(ready, [])

    def test_a_declined_spend_holds_all_dispatch(self):
        ready, _, _ = flow.survey(
            [PLAN, SPEND, answered("ask-1", "decline")], NOW, 3, alive, {})
        self.assertEqual(ready, [])

    def test_an_item_with_an_unanswered_ask_is_never_ready(self):
        ready, _, _ = self.survey([stall_ask("ask-2", "#12")])
        self.assertNotIn("#12", [entry["item"] for entry in ready])

    def test_finished_steps_make_their_successor_ready(self):
        rows = [launch("#14", "planned", "build"), ran("#14", "build"),
                launch("#13", "planned", "spec"), ran("#13", "spec"),
                moved("#12", "review", "reviewed", verdict="pass",
                      author_runs=["a"], reviewer_run="r")]
        ready, writes, _ = self.survey(
            rows, facts={"#13": {"gate_blobs": {}, "unchecked": 2},
                         "#14": {"gate_blobs": {}, "unchecked": 0}})
        self.assertEqual(writes, [])
        self.assertEqual(ready, [{"item": "#12", "step": "ship"},
                                 {"item": "#13", "step": "build"},
                                 {"item": "#14", "step": "verify"}])

    def test_build_repeats_while_breakdown_rows_remain(self):
        rows = [launch("#13", "planned", "spec"), ran("#13", "spec"),
                launch("#13", "spec", "build"), ran("#13", "build")]
        ready, _, _ = self.survey(
            rows, facts={"#13": {"gate_blobs": {}, "unchecked": 1}})
        self.assertIn({"item": "#13", "step": "build"}, ready)
        ready, _, _ = self.survey(
            rows, facts={"#13": {"gate_blobs": {}, "unchecked": 0}})
        self.assertIn({"item": "#13", "step": "verify"}, ready)

    def test_a_failed_run_leaves_the_item_to_its_stall(self):
        rows = [launch("#14", "planned", "build"),
                ran("#14", "build", outcome="agent-failed")]
        ready, writes, _ = self.survey(rows)
        self.assertNotIn("#14", [entry["item"] for entry in ready])
        self.assertEqual(writes, [])

    def test_a_retry_answer_makes_the_stalled_step_ready(self):
        rows = [launch("#14", "planned", "build"),
                moved("#14", "build", "stalled"), stall_ask("ask-2", "#14"),
                answered("ask-2", "retry", "#14")]
        ready, _, _ = self.survey(rows)
        self.assertIn({"item": "#14", "step": "build"}, ready)

    def test_an_approved_gate_makes_build_ready(self):
        rows = [moved("#12", "spec", "awaiting-gate"),
                gate_ask("ask-2", "#12"),
                answered("ask-2", "approve", "#12")]
        ready, _, _ = self.survey(rows)
        self.assertIn({"item": "#12", "step": "build"}, ready)

    def test_a_missing_plan_row_is_a_problem(self):
        self.assertEqual(flow.survey([SPEND], NOW, 3, alive, {}),
                         (None, None,
                          ["cd: the batch ledger has no plan row"]))


class TestSurveyWrites(unittest.TestCase):
    def writes(self, rows, probe=alive, facts=None, now=NOW):
        _, writes, problems = flow.survey(START + rows, now, 3, probe,
                                          facts or {})
        self.assertEqual(problems, [])
        return writes

    def test_a_completed_spec_queues_its_gate_ask(self):
        rows = [launch("#12", "planned", "spec"), ran("#12", "spec")]
        blobs = {"docs/features/x/prd.md": "abc"}
        writes = self.writes(rows, facts={
            "#12": {"gate_blobs": blobs, "unchecked": 0}})
        self.assertEqual(writes, [
            {"at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#12",
             "from": "spec", "to": "awaiting-gate",
             "reason": "spec run conductor-b1-12-spec-1 completed"},
            {"at": "2026-10-10T12:30:00Z", "kind": "ask", "item": "#12",
             "id": "ask-2", "ask_kind": "gate",
             "question": "#12's spec is ready for its gate: approve these"
                         " gate files, its build of 0 breakdown row(s)"
                         " at up to $3.00 each ($0.00) and its review of"
                         " what those rows produce at up to $3.00,"
                         " re-pricing #12 at $12.00 against its $15.00"
                         " plan estimate?",
             "options": ["approve", "block"], "recommended": "approve",
             "why": "the spec step completed; the gate files are"
                    " docs/features/x/prd.md",
             "gate_blobs": blobs, "build_usd": 0.0}])

    def test_the_gate_ask_reprices_the_build_from_its_rows(self):
        # Review major 2: build runs once per breakdown row at the build
        # step's full ceiling, so the gate answer is the build's spend
        # consent and names its price. #936: the review that reads what
        # those rows produce is priced beside it, at its own ceiling.
        rows = [launch("#12", "planned", "spec"), ran("#12", "spec")]
        writes = self.writes(rows, facts={
            "#12": {"gate_blobs": {}, "unchecked": 4}})
        self.assertEqual(writes[1]["question"],
                         "#12's spec is ready for its gate: approve these"
                         " gate files, its build of 4 breakdown row(s)"
                         " at up to $3.00 each ($12.00) and its review of"
                         " what those rows produce at up to $3.00,"
                         " re-pricing #12 at $24.00 against its $15.00"
                         " plan estimate?")
        self.assertEqual(writes[1]["build_usd"], 12.0)

    def test_the_gate_ask_prices_the_review_at_its_own_ceiling(self):
        # The review runs once under its ceiling, which the plan estimate
        # already holds: the figure is stated, not added to the re-price.
        rows = [launch("#13", "planned", "spec"), ran("#13", "spec")]
        plan = dict(PLAN, items=[dict(item("#13", "fix", "S"), steps=[
            dict(s, ceiling_usd=(5.0 if s["step"] == "review" else 1.0))
            for s in FEATURE_STEPS])])
        _, writes, problems = flow.survey(
            [plan] + START[1:] + rows, NOW, 3, alive,
            {"#13": {"gate_blobs": {"docs/adr/0090-x.md": "b"},
                     "unchecked": 2}})
        self.assertEqual(problems, [])
        self.assertEqual(writes[1]["question"],
                         "#13's spec is ready for its gate: approve these"
                         " gate files, its build of 2 breakdown row(s)"
                         " at up to $1.00 each ($2.00) and its review of"
                         " what those rows produce at up to $5.00,"
                         " re-pricing #13 at $16.00 against its $15.00"
                         " plan estimate?")
        self.assertNotIn("review_usd", writes[1])

    def test_a_feature_gates_even_with_no_gate_files(self):
        rows = [launch("#12", "planned", "spec"), ran("#12", "spec")]
        writes = self.writes(rows, facts={
            "#12": {"gate_blobs": {}, "unchecked": 0}})
        self.assertEqual([w["kind"] for w in writes], ["state", "ask"])
        self.assertEqual(writes[1]["why"], "the spec step completed; the"
                         " item branch changes no gate file")

    def test_a_fix_with_gate_files_gates(self):
        rows = [launch("#13", "planned", "spec"), ran("#13", "spec")]
        writes = self.writes(rows, facts={
            "#13": {"gate_blobs": {"docs/adr/0090-x.md": "b"},
                    "unchecked": 1}})
        self.assertEqual(writes[0]["to"], "awaiting-gate")

    def test_a_dead_runner_with_no_finishing_row_stalls(self):
        # #937: the lost run gets its run row first, outcome the charged
        # ceiling, so the scorecard and calibrate join its spend row like
        # any failed run's.
        rows = [launch("#14", "planned", "build", pid=4242)]
        writes = self.writes(rows, probe=dead)
        self.assertEqual(writes, [
            {"at": "2026-10-10T12:30:00Z", "kind": "run", "item": "#14",
             "step": "build", "charter": "swe", "band": "implementation",
             "model": "m", "models_reported": [], "effort": "medium",
             "run_id": "conductor-b1-14-build-1", "pid": 4242,
             "outcome": "runner-lost:cost-at-ceiling"},
            {"at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#14",
             "from": "build", "to": "stalled",
             "reason": "its runner (pid 4242) is gone with no finishing"
                       " run row", "cause": "runner-lost"},
            {"at": "2026-10-10T12:30:00Z", "kind": "ask", "item": "#14",
             "id": "ask-2", "ask_kind": "stall",
             "question": "#14 stalled in build: its runner (pid 4242) is"
                         " gone with no finishing run row. Retry, retry"
                         " one band up, or block?",
             "options": ["retry", "retry-up", "block"],
             "recommended": "retry",
             "why": "a dead runner or an idle step is evidence about the"
                    " run more than about the item"}])

    def test_a_dead_merge_turn_stalls_and_resumes_as_a_merge(self):
        # Review finding: an interrupted merge turn left the item at
        # `merging` with no stall, no ready step and no way out.
        rows = [launch("#14", "planned", "build"), ran("#14", "build"),
                moved("#14", "ship", "merging", pid=4242)]
        self.assertEqual(self.writes(rows), [])
        writes = self.writes(rows, probe=dead)
        self.assertEqual(writes[0], {
            "at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#14",
            "from": "merging", "to": "stalled",
            "reason": "its merge turn (pid 4242) is gone with no merged"
                      " row", "cause": "runner-lost"})
        self.assertEqual((writes[1]["ask_kind"], writes[1]["recommended"]),
                         ("stall", "retry"))
        resumed = rows + writes + [answered(writes[1]["id"], "retry",
                                            "#14")]
        ready, _, _ = flow.survey(START + resumed, NOW, 3, dead, {})
        self.assertIn({"item": "#14", "step": "merge"}, ready)

    def test_an_idle_step_stalls_after_twice_its_wall_clock_limit(self):
        # #14 is size M: a 90-minute limit, so 180 minutes idle stalls.
        rows = [launch("#14", "planned", "build")]
        start = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(self.writes(rows, now=start + timedelta(
            minutes=180)), [])
        writes = self.writes(rows, now=start + timedelta(minutes=181))
        self.assertEqual((writes[0]["reason"], writes[0]["cause"]),
                         ("no state change for over 180 minutes",
                          "runner-lost"))

    def test_a_top_band_step_offers_no_retry_up(self):
        rows = [launch("#12", "planned", "spec", pid=1)]
        writes = self.writes(rows, probe=dead)
        self.assertEqual(writes[2]["options"], ["retry", "block"])

    def test_a_lost_run_after_a_retry_up_records_the_band_it_ran_at(self):
        # The launch-time policy, one band up, not the plan's: a lost
        # retry-up run at the top band is not offered retry-up again
        # (#732), and its spend row names the model that spent.
        plan = dict(PLAN, policy={
            "routing": {"implementation": "s", "architecture_review": "f"},
            "effort": {"implementation": "medium",
                       "architecture_review": "high"}})
        rows = ([plan] + START[1:] + failed("#14", "planned", "build")[:-1]
                + [answered("ask-2", "retry-up", "#14"),
                   launch("#14", "stalled", "build", seq=2, pid=4242)])
        _, writes, problems = flow.survey(rows, NOW, 3, dead, {})
        self.assertEqual(problems, [])
        self.assertEqual(
            {key: writes[0][key] for key in ("band", "model", "effort",
                                             "run_id", "outcome")},
            {"band": "architecture_review", "model": "f", "effort": "high",
             "run_id": "conductor-b1-14-build-2",
             "outcome": "runner-lost:cost-at-ceiling"})
        self.assertEqual(writes[2]["options"], ["retry", "block"])

    def test_an_idle_live_runner_gets_no_run_row(self):
        # Its runner is alive and may yet finish and write its own.
        rows = [launch("#14", "planned", "build")]
        start = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
        writes = self.writes(rows, now=start + timedelta(minutes=181))
        self.assertEqual([w["kind"] for w in writes], ["state", "ask"])

    def test_three_consecutive_failures_pause_dispatch(self):
        rows = [launch("#12", "planned", "spec"),
                ran("#12", "spec", outcome="agent-failed"),
                launch("#13", "planned", "spec"),
                ran("#13", "spec", outcome="agent-failed"),
                launch("#14", "planned", "build"),
                ran("#14", "build", outcome="killed:cost-at-ceiling")]
        ready, writes, _ = flow.survey(START + rows, NOW, 3, alive, {})
        self.assertEqual(ready, [])
        self.assertEqual(writes, [
            {"at": "2026-10-10T12:30:00Z", "kind": "ask", "item": None,
             "id": "ask-2", "ask_kind": "stall",
             "question": "Three consecutive Worker runs failed in batch"
                         " b1. Resume dispatch, or stop?",
             "options": ["resume", "stop"], "recommended": "stop",
             "why": "three failures in a row point at the batch or the"
                    " harness more than at any one item"}])

    def test_a_resumed_pause_counts_failures_afresh(self):
        rows = [ran("#12", "spec", outcome="agent-failed"),
                ran("#13", "spec", outcome="agent-failed"),
                ran("#14", "build", outcome="agent-failed"),
                dict(stall_ask("ask-2", None, ("resume", "stop"))),
                answered("ask-2", "resume")]
        self.assertEqual(self.writes(rows), [])

    def test_a_cap_pause_does_not_reset_the_failure_streak(self):
        rows = [ran("#12", "spec", outcome="agent-failed"),
                ran("#13", "spec", outcome="agent-failed"),
                dict(stall_ask("ask-2", None, ("resume", "stop")),
                     ask_kind="spend"),
                answered("ask-2", "resume"),
                ran("#14", "build", outcome="agent-failed")]
        self.assertEqual([w["options"] for w in self.writes(rows)],
                         [["resume", "stop"]])

    def test_a_success_breaks_the_failure_streak(self):
        rows = [ran("#12", "spec", outcome="agent-failed"),
                ran("#13", "spec", outcome="agent-failed"),
                ran("#14", "build"),
                ran("#12", "spec", 2, outcome="agent-failed")]
        self.assertEqual(
            [w for w in self.writes(rows) if w["item"] is None], [])


class TestVerdict(unittest.TestCase):
    def ledger(self, tmp, rows):
        path = Path(tmp) / LEDGER
        path.parent.mkdir(parents=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in START + rows))

    BUILT = [launch("#14", "planned", "build"), ran("#14", "build"),
             launch("#14", "build", "verify"), ran("#14", "verify"),
             launch("#14", "verify", "review"), ran("#14", "review")]

    def verdict(self, rows, verdict, reviewer=run_id("#14", "review")):
        with tempfile.TemporaryDirectory() as tmp:
            self.ledger(tmp, rows)
            written, problems = flow.record_verdict(tmp, "b1", NOW, "#14",
                                                    verdict, reviewer, "h0")
            return written, problems

    def test_a_pass_records_the_author_and_reviewer_runs(self):
        written, problems = self.verdict(self.BUILT, "pass")
        self.assertEqual(problems, [])
        self.assertEqual(written, [{
            "at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#14",
            "from": "review", "to": "reviewed",
            "reason": "the reviewer passed it", "verdict": "pass",
            "author_runs": [run_id("#14", "build"), run_id("#14", "verify")],
            "reviewer_run": run_id("#14", "review"),
            # The branch head the review run was launched on: the merge
            # refuses any later change but the ship artifacts.
            "reviewed_head": "h0"}])

    def test_the_first_request_for_changes_queues_one_build_fix(self):
        written, _ = self.verdict(self.BUILT, "changes")
        self.assertEqual([(w["from"], w["to"], w["reason"])
                          for w in written],
                         [("review", "build",
                           "the reviewer requested changes; one fix step")])

    def test_a_second_request_for_changes_stalls(self):
        again = self.BUILT + [
            moved("#14", "review", "build"),
            launch("#14", "build", "build", seq=2), ran("#14", "build", 2),
            launch("#14", "build", "verify", seq=2),
            ran("#14", "verify", 2),
            launch("#14", "verify", "review", seq=2),
            ran("#14", "review", 2)]
        written, _ = self.verdict(again, "changes",
                                  reviewer=run_id("#14", "review", 2))
        self.assertEqual((written[0]["to"], written[0]["cause"]),
                         ("stalled", "changes-again"))
        self.assertEqual(written[1]["recommended"], "block")
        self.assertEqual(written[1]["why"], "a second request for changes"
                         " is evidence about the item")

    def test_an_unknown_verdict_is_refused(self):
        self.assertEqual(self.verdict(self.BUILT, "meh"), (None, [
            "cd: verdict 'meh' is not pass or changes"]))


class TestGitFacts(unittest.TestCase):
    def git(self, changed, tree="", shows=None):
        return FakeGit({("diff",): changed, ("ls-tree",): tree,
                        **{("show", spec): text
                           for spec, text in (shows or {}).items()}})

    def test_gate_blobs_are_the_changed_gate_files_blob_ids(self):
        git = self.git(
            "docs/features/x/prd.md\nconductor.py\ndocs/adr/0090-y.md\n",
            "100644 blob aaa\tdocs/adr/0090-y.md\n"
            "100644 blob bbb\tdocs/features/x/prd.md\n")
        self.assertEqual(flow.gate_blobs(git, "conductor/b1-12"), (
            {"docs/adr/0090-y.md": "aaa", "docs/features/x/prd.md": "bbb"},
            []))

    def test_no_changed_gate_file_is_empty(self):
        self.assertEqual(flow.gate_blobs(self.git("conductor.py\n"),
                                         "conductor/b1-12"), ({}, []))

    def test_unchecked_rows_come_from_the_branchs_breakdown(self):
        path = "docs/features/x/breakdown.md"
        git = self.git(f"{path}\n", shows={
            f"conductor/b1-12:{path}":
                "- [x] **WO-0170** done\n- [ ] **WO-0171** next\n"
                "  - [ ] not a row\n- [ ] **WO-0172** later\n"})
        self.assertEqual(flow.unchecked_rows(git, "conductor/b1-12"), ([
            "- [ ] **WO-0171** next", "- [ ] **WO-0172** later"], []))

    def test_a_failing_git_read_is_a_problem(self):
        git = FakeGit(failing=["diff"])
        self.assertEqual(flow.gate_blobs(git, "conductor/b1-12"), (None, [
            "cd: git diff for conductor/b1-12 failed: fatal: rejected"]))


class TestNextCli(unittest.TestCase):
    def run_cli(self, rows, probe=alive):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / LEDGER
            path.parent.mkdir(parents=True)
            path.write_text("".join(json.dumps(r) + "\n" for r in rows))
            Path(tmp, ".github").mkdir()
            Path(tmp, ".github/factory.json").write_text(
                json.dumps({"wip_cap": 2}))
            # #937: a dead runner's charge needs its worktree and git.
            Path(tmp, ".claude/worktrees/conductor-b1-14").mkdir(
                parents=True)
            code, out = cli_contract.capture(
                conductor.main, ["next", "b1"], env={}, clock=clock,
                root=tmp, git=FakeGit({("rev-parse",): f"{tmp}/.git\n"}),
                alive=probe)
            rows, _ = conductor.load(tmp, "b1")
            return code, out, rows

    def test_next_reports_ready_steps_under_the_cap(self):
        code, out, _ = self.run_cli(START)
        self.assertEqual(code, 0, out)
        payload = json.loads(out[:out.rindex("\ncd:")])
        self.assertEqual(payload, {
            "ask": None, "recorded": [], "merge_due": [],
            "ready": [{"item": "#12", "step": "spec"},
                      {"item": "#13", "step": "spec"}]})

    def test_next_records_a_stall_and_shows_it_as_the_ask(self):
        code, out, rows = self.run_cli(
            START + [launch("#14", "planned", "build", pid=9)], probe=dead)
        payload = json.loads(out[:out.rindex("\ncd:")])
        self.assertEqual(payload["recorded"], ["ask-2"])
        self.assertEqual(payload["ask"]["id"], "ask-2")
        self.assertEqual(rows[-2]["to"], "stalled")


if __name__ == "__main__":
    unittest.main()


BUDGET = "the Worker run ended error_max_budget_usd"
# The result event of a budget stop that never let the Worker start
# (#936): single-digit turns, output tokens in the hundreds.
NEVER_STARTED = {"num_turns": 5, "usage": {"output_tokens": 1072}}


def failed(key, frm, name, seq=1, band="implementation",
           reason=BUDGET, ask_id="ask-2"):
    """One failed run of `name` that stalled with `reason`, answered
    retry: the rows a retry launches after."""
    return [launch(key, frm, name, seq=seq),
            dict(ran(key, name, seq, outcome="agent-failed"), band=band),
            moved(key, name, "stalled", reason=reason),
            stall_ask(ask_id, key), answered(ask_id, "retry", key)]


class TestStallWording(unittest.TestCase):
    """#725 item 3: the question names only the options offered."""

    def ask(self, key):
        entry = flow.item_view(START, key)["entry"]
        rows = START + [launch(key, "planned", entry["steps"][0]["step"])]
        written, problems = flow.stall_rows(rows, NOW, entry, "x",
                                            "agent-failed", "retry", "w")
        self.assertEqual(problems, [])
        return written[1]

    def test_below_the_top_band_all_three_options_are_named(self):
        asked = self.ask("#14")
        self.assertEqual(asked["question"], "#14 stalled in build: x."
                         " Retry, retry one band up, or block?")

    def test_at_the_top_band_retry_up_is_neither_offered_nor_named(self):
        asked = self.ask("#12")
        self.assertEqual(asked["options"], ["retry", "block"])
        self.assertEqual(asked["question"],
                         "#12 stalled in spec: x. Retry, or block?")


class TestWorkerAdvice(unittest.TestCase):
    """#725 item 2: a failed Worker run's stall ask depends on how many
    runs of the step have failed in a row, and a repeat budget stop at
    the same ceiling recommends no plain retry."""

    def advice(self, rows, key, name, band, reason=BUDGET, result=None):
        entry = flow.item_view(START, key)["entry"]
        return flow.worker_advice(START + rows, entry, name, band, reason,
                                  result)

    def test_a_first_failure_recommends_retry(self):
        self.assertEqual(
            self.advice([], "#12", "spec", "architecture_review"),
            ("retry", "a first failure is evidence about the item as often"
                      " as about the agent, so nothing retries without your"
                      " answer"))

    def test_a_first_budget_stop_that_never_started_recommends_block(self):
        # #936: review-1 of consumer batch b20261013 ended
        # error_max_budget_usd after 5 turns and 1,072 output tokens — the
        # ceiling went on loading the brief and the tree, so a plain retry
        # spends it again; at the top band there is no band to go up to.
        self.assertEqual(
            self.advice([], "#12", "spec", "architecture_review",
                        result=NEVER_STARTED),
            ("block", "a first budget stop on spec at its $3.00 ceiling"
                      " after 5 turn(s) and 1072 output tokens: the ceiling"
                      " never let the Worker start, so a plain retry spends"
                      " it again; block it"))

    def test_a_never_started_stop_below_the_top_recommends_retry_up(self):
        self.assertEqual(
            self.advice([], "#14", "build", "implementation",
                        result=NEVER_STARTED),
            ("retry-up", "a first budget stop on build at its $3.00 ceiling"
                         " after 5 turn(s) and 1072 output tokens: the"
                         " ceiling never let the Worker start, so a plain"
                         " retry spends it again; retry it one band up, on"
                         " a stronger model"))

    def test_a_zeroed_usage_reads_the_per_model_output_tokens(self):
        # A budget stop zeroes usage and leaves its counts in modelUsage
        # (#725).
        result = {"num_turns": 5, "usage": {"output_tokens": 0},
                  "modelUsage": {"m": {"outputTokens": 500},
                                 "n": {"outputTokens": 31}}}
        self.assertEqual(
            self.advice([], "#12", "spec", "architecture_review",
                        result=result)[1],
            "a first budget stop on spec at its $3.00 ceiling after 5"
            " turn(s) and 531 output tokens: the ceiling never let the"
            " Worker start, so a plain retry spends it again; block it")

    def test_a_first_budget_stop_that_started_recommends_retry(self):
        # Ten turns or two thousand output tokens is a Worker that ran; a
        # missing event, or one with no num_turns count, is no evidence.
        for result in ({"num_turns": 10, "usage": {"output_tokens": 1999}},
                       {"num_turns": 9, "usage": {"output_tokens": 2000}},
                       {"usage": {"output_tokens": 12}}, {}, None):
            with self.subTest(result=result):
                self.assertEqual(
                    self.advice([], "#12", "spec", "architecture_review",
                                result=result)[0], "retry")

    def test_a_tiny_run_that_was_not_a_budget_stop_still_retries(self):
        self.assertEqual(
            self.advice([], "#12", "spec", "architecture_review",
                        reason="the run completed but left no pr-body.md",
                        result=NEVER_STARTED)[0], "retry")

    def test_a_completed_earlier_run_does_not_count(self):
        rows = [launch("#14", "planned", "build"), ran("#14", "build")]
        self.assertEqual(self.advice(rows, "#14", "build",
                                     "implementation")[0], "retry")

    def test_a_repeat_budget_stop_at_the_top_band_recommends_block(self):
        rows = failed("#12", "planned", "spec", band="architecture_review")
        self.assertEqual(
            self.advice(rows, "#12", "spec", "architecture_review"),
            ("block", "a second consecutive budget stop on spec at the same"
                      " $3.00 ceiling: the outcome repeats at that ceiling,"
                      " so a plain retry spends it again; block it"))

    def test_a_repeat_budget_stop_below_the_top_recommends_retry_up(self):
        rows = failed("#14", "planned", "build")
        self.assertEqual(
            self.advice(rows, "#14", "build", "implementation"),
            ("retry-up", "a second consecutive budget stop on build at the"
                         " same $3.00 ceiling: the outcome repeats at that"
                         " ceiling, so a plain retry spends it again; retry"
                         " it one band up, on a stronger model"))

    def test_a_repeat_budget_stop_after_a_retry_up_recommends_block(self):
        rows = failed("#14", "planned", "build", band="architecture_review")
        self.assertEqual(
            self.advice(rows, "#14", "build", "architecture_review")[0],
            "block")

    def test_a_budget_stop_after_another_failure_still_retries(self):
        rows = failed("#12", "planned", "spec", band="architecture_review",
                      reason="the run completed but left no pr-body.md")
        self.assertEqual(
            self.advice(rows, "#12", "spec", "architecture_review"),
            ("retry", "attempt 2 at spec failed after an earlier one did,"
                      " so the item is as likely a cause as the agent;"
                      " nothing retries without your answer"))

    def test_the_attempt_counts_every_consecutive_failure(self):
        rows = (failed("#12", "planned", "spec", band="architecture_review",
                       reason="a")
                + failed("#12", "stalled", "spec", seq=2,
                         band="architecture_review", reason="b",
                         ask_id="ask-3"))
        self.assertEqual(
            self.advice(rows, "#12", "spec", "architecture_review",
                        reason="c")[1],
            "attempt 3 at spec failed after an earlier one did, so the item"
            " is as likely a cause as the agent; nothing retries without"
            " your answer")

    def test_prior_stalls_lists_the_trailing_failed_runs(self):
        rows = (START + [launch("#14", "planned", "build"),
                         ran("#14", "build")]
                + failed("#14", "build", "build", seq=2))
        self.assertEqual(
            [(run["run_id"], reason)
             for run, reason in flow.prior_stalls(rows, "#14", "build")],
            [(run_id("#14", "build", 2), BUDGET)])


LOST = "runner-lost:cost-at-ceiling"
LOST_FILE = "docs/factory/costs/runs/conductor-b1-14-build-1.jsonl"


class TestNextLostRun(unittest.TestCase):
    """#937: six runners lost across two consumer batches left no spend
    row, so the cap, the scorecard and calibrate read $0 for them. `next`
    now charges a runner found dead its full ceiling, fail-closed like a
    wall-clock kill, through the one spend path on the item branch,
    before it writes the stall."""

    ROWS = START + [launch("#14", "planned", "build", pid=9)]

    def next(self, rows, worktree=True, log="", failing=None, spent=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / LEDGER
            path.parent.mkdir(parents=True)
            path.write_text("".join(json.dumps(r) + "\n" for r in rows))
            Path(tmp, ".github").mkdir()
            Path(tmp, ".github/factory.json").write_text(
                json.dumps({"wip_cap": 2}))
            wt = Path(tmp) / ".claude/worktrees/conductor-b1-14"
            if worktree:
                wt.mkdir(parents=True)
            if spent is not None:
                (wt / LOST_FILE).parent.mkdir(parents=True)
                (wt / LOST_FILE).write_text(spent)
            git = FakeGit({("rev-parse",): f"{tmp}/.git\n", ("log",): log},
                          failing=failing)
            code, out = cli_contract.capture(
                conductor.main, ["next", "b1"], env={}, clock=clock,
                root=tmp, git=git, alive=dead)
            rows, _ = conductor.load(tmp, "b1")
            text = (wt / LOST_FILE).read_text() \
                if (wt / LOST_FILE).is_file() else None
            return {"code": code, "out": out, "rows": rows,
                    "calls": [c for c in git.calls if c[:1] == ["-C"]],
                    "spent": text, "worktree": str(wt)}

    def test_a_dead_runner_is_charged_its_ceiling_on_its_branch(self):
        got = self.next(self.ROWS)
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual(got["spent"], json.dumps({
            "wo": "#14", "run_id": "conductor-b1-14-build-1", "model": "m",
            "tokens": 0, "cost": 3.0, "outcome": LOST,
            "at": "2026-10-10"}) + "\n")
        self.assertEqual(got["calls"], [
            ["-C", got["worktree"], "add", LOST_FILE],
            ["-C", got["worktree"], "commit", "-m",
             "chore(cost): conductor-b1-14-build-1"]])
        self.assertEqual([(r["kind"], r.get("outcome", r.get("to")))
                          for r in got["rows"][-3:]],
                         [("run", LOST), ("state", "stalled"),
                          ("ask", None)])

    def test_a_missing_worktree_is_a_problem_and_nothing_is_written(self):
        got = self.next(self.ROWS, worktree=False)
        self.assertNotEqual(got["code"], 0)
        self.assertIn(f"cd: #14's worktree {got['worktree']} is gone, so"
                      " its lost run conductor-b1-14-build-1 cannot be"
                      " charged its ceiling", got["out"])
        self.assertEqual(len(got["rows"]), len(self.ROWS))
        self.assertIsNone(got["spent"])

    def test_a_spend_row_already_committed_is_not_charged_twice(self):
        # A tick whose ledger append failed after the spend commit: the
        # branch's log names the run, so the rows are written and no
        # second row is.
        got = self.next(self.ROWS,
                        log="chore(cost): conductor-b1-14-build-1\n")
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual(got["calls"], [])
        self.assertIsNone(got["spent"])
        self.assertEqual(got["rows"][-3]["outcome"], LOST)

    def test_a_spend_file_left_uncommitted_is_committed_not_rewritten(self):
        row = json.dumps({"wo": "#14", "run_id": "conductor-b1-14-build-1",
                          "model": "m", "tokens": 0, "cost": 3.0,
                          "outcome": LOST, "at": "2026-10-09"}) + "\n"
        got = self.next(self.ROWS, spent=row)
        self.assertEqual(got["code"], 0, got["out"])
        self.assertEqual(got["spent"], row)
        self.assertEqual([c[2] for c in got["calls"]], ["add", "commit"])

    def test_a_failing_spend_commit_is_a_problem_and_nothing_is_written(self):
        got = self.next(self.ROWS, failing=["-C"])
        self.assertNotEqual(got["code"], 0)
        self.assertIn("cd: #14: committing the spend row of"
                      " conductor-b1-14-build-1 failed: fatal: rejected",
                      got["out"])
        self.assertEqual(len(got["rows"]), len(self.ROWS))

    def test_a_live_runner_charges_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / LEDGER
            path.parent.mkdir(parents=True)
            path.write_text("".join(json.dumps(r) + "\n"
                                    for r in self.ROWS))
            Path(tmp, ".github").mkdir()
            Path(tmp, ".github/factory.json").write_text(
                json.dumps({"wip_cap": 2}))
            git = FakeGit({})
            code, _ = cli_contract.capture(
                conductor.main, ["next", "b1"], env={}, clock=clock,
                root=tmp, git=git, alive=alive)
            self.assertEqual(code, 0)
            self.assertEqual(git.calls, [])
