"""conductor.py (PRD-0013, the Conductor's batch tool) — pure-function +
fixture tests.

Same discipline as test_work_queue: every function is exercised through
its public interface, every external call goes through an injected fake,
and tests assert the EXACT problem strings callers print.
"""
import fcntl
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import conductor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402

LEDGER = "docs/factory/batches/b1/ledger.jsonl"
AT = "2026-10-10T12:00:00Z"


def clock():
    return datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)


PLAN = {"at": AT, "kind": "plan", "item": None, "batch": "b1", "items": [],
        "policy": {"routing": {}, "effort": {}}, "estimate_usd": 0.0,
        "month_to_date_usd": 0.0, "cap_usd": 300}


def ask_row(ask_id, item="#12", options=("yes", "no"), ask_kind="spend"):
    return {"at": AT, "kind": "ask", "item": item, "id": ask_id,
            "ask_kind": ask_kind, "question": "Spend it?",
            "options": list(options), "recommended": options[0],
            "why": "it is cheap"}


def answer_row(ask_id, choice="yes", item="#12"):
    return {"at": AT, "kind": "answer", "item": item, "ask": ask_id,
            "choice": choice, "note": ""}


def write_ledger(tmp, *rows, text=None):
    path = Path(tmp) / LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text is not None else
                    "".join(json.dumps(row) + "\n" for row in rows),
                    encoding="utf-8")
    return path


# The smallest well-formed row of every kind in the architecture's table.
MINIMAL = {
    "plan": PLAN,
    "reserve": {"at": AT, "kind": "reserve", "item": "#12", "what": "adr",
                "values": [90, 91]},
    "state": {"at": AT, "kind": "state", "item": "#12", "from": "planned",
              "to": "spec", "reason": "dispatched"},
    "run": {"at": AT, "kind": "run", "item": "#12", "step": "spec",
            "charter": "architect", "band": "architecture_review",
            "model": "m", "models_reported": ["m"], "effort": "high",
            "run_id": "conductor-b1-12-spec-1", "pid": 4242,
            "outcome": "completed"},
    "ask": ask_row("ask-1"),
    "answer": answer_row("ask-1"),
    "consent": {"at": AT, "kind": "consent", "item": "#12",
                "policy": "standing", "reason": "no gate-path file"},
    "close": {"at": AT, "kind": "close", "item": None, "merged": ["#12"],
              "blocked": []},
}


class TestRowGrammar(unittest.TestCase):
    def test_every_kinds_minimal_row_is_clean(self):
        self.assertEqual(sorted(MINIMAL), sorted(conductor.ROW_FIELDS))
        for kind, row in MINIMAL.items():
            self.assertEqual(conductor.row_problems(row), [], kind)

    def test_an_unknown_kind_is_a_problem(self):
        self.assertEqual(
            conductor.row_problems({"at": AT, "kind": "vote", "item": None}),
            ["kind 'vote' is not a batch ledger row kind"])

    def test_missing_and_unknown_fields_are_named_sorted(self):
        row = {key: value for key, value in MINIMAL["answer"].items()
               if key not in ("choice", "note")}
        row["extra"] = 1
        self.assertEqual(conductor.row_problems(row), [
            "answer row is missing field(s): choice, note",
            "answer row has unknown field(s): extra"])

    def test_at_must_be_a_utc_timestamp_to_the_second(self):
        for value in ("2026-10-10", "2026-10-10T12:00:00",
                      "2026-13-01T00:00:00Z", None):
            row = dict(MINIMAL["close"], at=value)
            self.assertEqual(conductor.row_problems(row), [
                f"at {value!r} is not a UTC timestamp"
                " (YYYY-MM-DDTHH:MM:SSZ)"], value)

    def test_item_is_an_issue_key_or_null(self):
        for value in ("12", "#0", "WO-0001", 12):
            row = dict(MINIMAL["state"], item=value)
            self.assertEqual(conductor.row_problems(row), [
                f"item {value!r} is not an issue key (#<n>) or null"],
                value)

    def test_a_reviewed_state_carries_its_verdict_fields(self):
        row = dict(MINIMAL["state"], to="reviewed")
        self.assertEqual(conductor.row_problems(row), [
            "state row to reviewed is missing field(s): author_runs,"
            " reviewer_run, verdict"])

    def test_a_merged_state_carries_its_merge_fields(self):
        row = dict(MINIMAL["state"], to="merged")
        self.assertEqual(conductor.row_problems(row), [
            "state row to merged is missing field(s): checks, pr, sha"])

    def test_an_ask_names_a_known_kind_and_recommends_an_option(self):
        row = dict(ask_row("ask-1"), ask_kind="vibes", recommended="maybe")
        self.assertEqual(conductor.row_problems(row), [
            "ask_kind 'vibes' is not one of spend, gate, merge, stall,"
            " clarify",
            "recommended 'maybe' is not among the options"])

    def test_ask_options_are_distinct_non_empty_strings(self):
        for options in ([], ["a", "a"], ["a", ""], "a", ["a", 1]):
            row = dict(ask_row("ask-1"), options=options, recommended="a")
            self.assertIn(
                "options must be a non-empty list of distinct non-empty"
                " strings", conductor.row_problems(row), options)

    def test_an_ask_question_and_why_are_non_empty(self):
        row = dict(ask_row("ask-1"), question=" ", why=None)
        self.assertEqual(conductor.row_problems(row), [
            "question must be a non-empty string",
            "why must be a non-empty string"])

    def test_a_launch_state_row_carries_its_run_id_and_pid(self):
        row = dict(MINIMAL["state"], run_id="conductor-b1-12-spec-1",
                   pid=4242)
        self.assertEqual(conductor.row_problems(row), [])

    def test_an_ask_may_carry_a_train_and_gate_blobs(self):
        row = dict(ask_row("ask-1"), covers=["#12", "#13"],
                   gate_blobs={"docs/adr/0090-x.md": "abc123"})
        self.assertEqual(conductor.row_problems(row), [])

    def test_covers_is_a_list_of_distinct_issue_keys(self):
        # Review minor 3: `"covers": "#13"` passed, and consents() then
        # found "#1" in it by substring, granting consent to #1.
        for covers in ("#13", [], ["#12", "#12"], ["12"], [12], None):
            row = dict(ask_row("ask-1"), covers=covers)
            self.assertEqual(conductor.row_problems(row), [
                "covers must be a non-empty list of distinct issue keys"],
                covers)

    def test_gate_blobs_maps_paths_to_blob_ids(self):
        for blobs in ("abc", ["docs/adr/x.md"], {"docs/adr/x.md": 1},
                      {"": "abc"}, None):
            row = dict(ask_row("ask-1"), gate_blobs=blobs)
            self.assertEqual(conductor.row_problems(row), [
                "gate_blobs must map file paths to blob ids"], blobs)
        row = dict(ask_row("ask-1"), gate_blobs={})
        self.assertEqual(conductor.row_problems(row), [])


class TestOneOwner(unittest.TestCase):
    def test_block_spans_and_ledger_times_have_one_owner_each(self):
        # Review minor 10: byte-for-byte copies in sibling modules.
        import conductor_close
        import conductor_flow
        import conductor_plan
        import conductor_run
        self.assertIs(conductor_run.span, conductor_plan.span)
        self.assertIs(conductor_flow.parsed_at, conductor.parsed_at)
        self.assertIs(conductor_close.parsed_at, conductor.parsed_at)
        self.assertEqual(conductor.parsed_at(AT), clock())


class TestNames(unittest.TestCase):
    """The Batch's names (#735): one owner, and the batch and item
    namespaces disjoint."""
    NAMES = ("oct", "oct-2", "oct-2-x", "b1", "b1-13", "a-b-c", "x9", "2")
    ITEMS = ("#2", "#13", "#5")

    def test_an_item_name_is_refused_as_a_batch_name(self):
        self.assertEqual(conductor.item_branch("oct", "#2"),
                         "conductor/oct-2")
        self.assertEqual(conductor.batch_name_problems("oct-2"), [
            "cd: batch 'oct-2' is not a batch name (lowercase letters,"
            " digits and hyphens, never ending in -<digits>, which names"
            " an item)"])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(conductor.load(tmp, "oct-2"), (
                None, conductor.batch_name_problems("oct-2")))

    def test_no_item_branch_or_worktree_is_another_batchs(self):
        batches = [name for name in self.NAMES
                   if not conductor.batch_name_problems(name)]
        self.assertEqual(batches, ["oct", "oct-2-x", "b1", "a-b-c", "x9", "2"])
        branches = {conductor.batch_branch(b) for b in batches}
        worktrees = {conductor.batch_worktree(b) for b in batches}
        for batch in batches:
            for item in self.ITEMS:
                self.assertNotIn(conductor.item_branch(batch, item),
                                 branches, (batch, item))
                self.assertNotIn(conductor.item_worktree(batch, item),
                                 worktrees, (batch, item))
        self.assertEqual(conductor.batch_worktree("oct"),
                         ".claude/worktrees/conductor-oct")
        self.assertEqual(conductor.item_worktree("oct", "#2"),
                         ".claude/worktrees/conductor-oct-2")

    def test_a_run_id_round_trips_and_a_prefix_sharing_batch_is_not_ours(
            self):
        made = conductor.run_id("oct", "#2", "spec", 1)
        self.assertEqual(made, "conductor-oct-2-spec-1")
        self.assertEqual(conductor.run_item("oct", made), "#2")
        # Batch oct-2-x's item #5 shares the prefix conductor-oct-2-.
        other = conductor.run_id("oct-2-x", "#5", "spec", 1)
        self.assertIsNone(conductor.run_item("oct", other))
        self.assertEqual(conductor.run_item("oct-2-x", other), "#5")
        self.assertIsNone(conductor.run_item("oct", "unrelated-run"))

    def test_the_batch_dir_holds_the_ledger_and_runs(self):
        top = Path(conductor.batch_dir("b1"))
        self.assertEqual(top, Path("docs/factory/batches/b1"))
        self.assertEqual(Path(conductor.LEDGER.format(batch="b1")).parent,
                         top)
        self.assertEqual(Path(conductor.RUNS.format(batch="b1")).parent,
                         top)


class TestLoad(unittest.TestCase):
    def test_reads_rows_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_ledger(tmp, PLAN, ask_row("ask-1"))
            self.assertEqual(conductor.load(tmp, "b1"),
                             ([PLAN, ask_row("ask-1")], []))

    def test_an_absent_ledger_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(conductor.load(tmp, "b1"), (None, [
                f"cd: no batch ledger at {LEDGER}"]))

    def test_a_line_that_does_not_parse_fails_the_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_ledger(tmp, text=json.dumps(PLAN) + "\n{oops\n[1]\n")
            rows, problems = conductor.load(tmp, "b1")
        self.assertIsNone(rows)
        self.assertEqual(len(problems), 2, problems)
        self.assertTrue(problems[0].startswith(
            f"cd: {LEDGER}:2 is not valid JSON:"), problems)
        self.assertEqual(problems[1], f"cd: {LEDGER}:3 is not a JSON object")

    def test_a_line_that_breaks_its_kinds_rules_fails_the_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_ledger(tmp, PLAN, dict(ask_row("ask-1"), why=""))
            self.assertEqual(conductor.load(tmp, "b1"), (None, [
                f"cd: {LEDGER}:2 why must be a non-empty string"]))

    def test_a_ledger_that_is_not_utf8_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_ledger(tmp, text="").write_bytes(b"\xff\n")
            rows, problems = conductor.load(tmp, "b1")
        self.assertIsNone(rows)
        self.assertEqual(len(problems), 1, problems)
        self.assertTrue(problems[0].startswith(
            f"cd: cannot read {LEDGER}:"), problems)

    def test_a_batch_name_that_is_not_a_slug_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(conductor.load(tmp, "../x"), (None, [
                "cd: batch '../x' is not a batch name (lowercase letters,"
                " digits and hyphens, never ending in -<digits>, which"
                " names an item)"]))


class TestAppendLock(unittest.TestCase):
    def test_an_append_holds_an_exclusive_lock_on_the_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_ledger(tmp, PLAN)
            with mock.patch.object(conductor.fcntl, "flock",
                                   wraps=fcntl.flock) as flock:
                conductor.ask(tmp, "b1", clock(), None, "spend", "Go?",
                              ["yes", "no"], "yes", "cheap")
        self.assertIn(fcntl.LOCK_EX, [call.args[1]
                                      for call in flock.call_args_list])


class TestAsk(unittest.TestCase):
    def test_writes_an_ask_row_with_a_fresh_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_ledger(tmp, PLAN, ask_row("ask-1"))
            row, problems = conductor.ask(
                tmp, "b1", clock(), "#13", "gate", "PRD ok?",
                ["approve", "revise"], "approve", "it covers the story",
                covers=None)
            rows, _ = conductor.load(tmp, "b1")
        self.assertEqual(problems, [])
        self.assertEqual(row, {
            "at": AT, "kind": "ask", "item": "#13", "id": "ask-2",
            "ask_kind": "gate", "question": "PRD ok?",
            "options": ["approve", "revise"], "recommended": "approve",
            "why": "it covers the story"})
        self.assertEqual(rows[-1], row)

    def test_a_train_ask_records_what_it_covers(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_ledger(tmp, PLAN)
            row, problems = conductor.ask(
                tmp, "b1", clock(), None, "merge", "Merge the train?",
                ["train", "one at a time"], "train", "all reviewed",
                covers=["#12", "#13"])
        self.assertEqual(problems, [])
        self.assertEqual((row["id"], row["covers"]), ("ask-1", ["#12", "#13"]))

    def test_an_ask_that_breaks_the_grammar_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_ledger(tmp, PLAN)
            before = path.read_bytes()
            row, problems = conductor.ask(
                tmp, "b1", clock(), None, "spend", "Go?", ["yes", "no"],
                "maybe", "cheap")
            self.assertEqual(path.read_bytes(), before)
        self.assertIsNone(row)
        self.assertEqual(problems, [
            "cd: ask refused: recommended 'maybe' is not among the options"])

    def test_an_absent_ledger_is_never_created_by_an_ask(self):
        with tempfile.TemporaryDirectory() as tmp:
            row, problems = conductor.ask(
                tmp, "b1", clock(), None, "spend", "Go?", ["yes", "no"],
                "yes", "cheap")
            self.assertFalse((Path(tmp) / LEDGER).exists())
        self.assertEqual((row, problems),
                         (None, [f"cd: no batch ledger at {LEDGER}"]))


class TestAnswer(unittest.TestCase):
    def answer(self, tmp, ask_id, choice, env=None):
        return conductor.answer(tmp, "b1", clock(), ask_id, choice,
                                note="", env=env or {})

    def test_writes_an_answer_row_for_the_asks_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_ledger(tmp, PLAN, ask_row("ask-1"))
            row, problems = self.answer(tmp, "ask-1", "no")
            rows, _ = conductor.load(tmp, "b1")
        self.assertEqual(problems, [])
        self.assertEqual(row, answer_row("ask-1", choice="no"))
        self.assertEqual(rows[-1], row)

    def refused(self, rows, ask_id, choice, env=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_ledger(tmp, *rows)
            before = path.read_bytes()
            row, problems = self.answer(tmp, ask_id, choice, env)
            self.assertEqual(path.read_bytes(), before)
        self.assertIsNone(row)
        return problems

    def test_an_unknown_ask_is_refused(self):
        self.assertEqual(self.refused([PLAN, ask_row("ask-1")], "ask-9",
                                      "yes"),
                         ["cd: no ask ask-9 in this batch"])

    def test_an_already_answered_ask_is_refused(self):
        self.assertEqual(
            self.refused([PLAN, ask_row("ask-1"), answer_row("ask-1")],
                         "ask-1", "no"),
            ["cd: ask ask-1 is already answered ('yes')"])

    def test_a_choice_outside_the_options_is_refused(self):
        self.assertEqual(
            self.refused([PLAN, ask_row("ask-1")], "ask-1", "perhaps"),
            ["cd: 'perhaps' is not an option of ask ask-1 (yes, no)"])

    def test_a_block_answer_blocks_the_item_under_the_same_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_ledger(tmp, PLAN, MINIMAL["state"],
                         ask_row("ask-1", options=("retry", "block")))
            row, problems = conductor.answer(tmp, "b1", clock(), "ask-1",
                                             "block", "flaky", env={})
            rows, _ = conductor.load(tmp, "b1")
        self.assertEqual(problems, [])
        self.assertEqual(row["choice"], "block")
        self.assertEqual(rows[-2:], [row, {
            "at": AT, "kind": "state", "item": "#12", "from": "spec",
            "to": "blocked", "reason": "answer to ask-1: block (flaky)"}])

    def test_a_block_answer_on_a_batch_ask_moves_no_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_ledger(tmp, PLAN, ask_row("ask-1", item=None,
                                            options=("block", "go")))
            conductor.answer(tmp, "b1", clock(), "ask-1", "block", "",
                             env={})
            rows, _ = conductor.load(tmp, "b1")
        self.assertEqual(rows[-1]["kind"], "answer")

    def test_a_block_answer_leaves_a_terminal_item_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_ledger(tmp, PLAN, dict(MINIMAL["state"], to="blocked"),
                         ask_row("ask-1", options=("retry", "block")))
            conductor.answer(tmp, "b1", clock(), "ask-1", "block", "",
                             env={})
            rows, _ = conductor.load(tmp, "b1")
        self.assertEqual(rows[-1]["kind"], "answer")

    def test_a_worker_may_never_answer(self):
        self.assertEqual(
            self.refused([PLAN, ask_row("ask-1")], "ask-1", "yes",
                         env={"CONDUCTOR_WORKER": "1"}),
            ["cd: answer refused: CONDUCTOR_WORKER is set, and a Worker"
             " never answers an ask"])


class TestNext(unittest.TestCase):
    def test_only_the_oldest_unanswered_ask_is_returned(self):
        rows = [PLAN, ask_row("ask-1"), ask_row("ask-2", item="#13"),
                answer_row("ask-1"), ask_row("ask-3", item="#14")]
        self.assertEqual(conductor.next_ask(rows), ask_row("ask-2",
                                                           item="#13"))

    def test_no_unanswered_ask_is_none(self):
        self.assertIsNone(conductor.next_ask(
            [PLAN, ask_row("ask-1"), answer_row("ask-1")]))


ITEM_PLAN = {**PLAN, "items": [{"item": "#12", "type": "fix"},
                               {"item": "#13", "type": "order"}]}


def state(frm, to, reason="moved", **fields):
    return {"at": AT, "kind": "state", "item": "#12", "from": frm, "to": to,
            "reason": reason, **fields}


def run(run_id, step="build", outcome="completed"):
    return {**MINIMAL["run"], "step": step, "run_id": run_id,
            "outcome": outcome}


def reserve(what, values, renumbered_from=None):
    row = {"at": AT, "kind": "reserve", "item": "#12", "what": what,
           "values": values}
    if renumbered_from is not None:
        row["renumbered_from"] = renumbered_from
    return row


STALL = state("build", "stalled", "its runner is gone")


class TestItemView(unittest.TestCase):
    """The batch ledger's one reading interface (issue #694): plain
    read-only data, ordered by ledger position."""

    def item(self, *rows, item="#12"):
        return conductor.item_view([ITEM_PLAN, *rows], item)

    def test_reads_an_items_rows_into_its_fields(self):
        launched = state("planned", "build", "launched",
                         run_id="r-1", pid=7)
        found = self.item(launched, run("r-1"), ask_row("ask-1"),
                          run("r-2", step="review"))
        self.assertEqual(found["entry"], ITEM_PLAN["items"][0])
        self.assertIsNone(found["unknown"])
        self.assertEqual(found["state"], "build")
        self.assertEqual(found["last"], launched)
        self.assertEqual(found["states"], (launched,))
        self.assertEqual(found["runs"], (run("r-1"), run("r-2", "review")))
        self.assertEqual(found["asks"], (ask_row("ask-1"),))
        self.assertEqual(found["pending"], ask_row("ask-1"))
        self.assertEqual(found["finishing"], run("r-1"))
        self.assertFalse(found["in_flight"])
        self.assertTrue(found["completed"])
        self.assertEqual(found["author_runs"], ("r-1",))

    def test_a_launch_with_no_finishing_run_is_in_flight(self):
        found = self.item(state("planned", "build", "launched",
                                run_id="r-1", pid=7))
        self.assertIsNone(found["finishing"])
        self.assertTrue(found["in_flight"])
        self.assertFalse(found["completed"])

    def test_an_item_with_no_rows_is_planned(self):
        found = self.item(item="#13")
        self.assertEqual((found["state"], found["last"], found["states"]),
                         ("planned", None, ()))
        self.assertFalse(found["in_flight"] or found["retry"])

    def test_equal_valued_state_rows_resolve_by_ledger_position(self):
        # The second stall equals the first row for row: a retry answer
        # between them answered the first stall, never the second.
        found = self.item(STALL, ask_row("ask-1", ask_kind="stall"),
                          answer_row("ask-1", "retry"),
                          state("stalled", "build"), STALL)
        self.assertIsNone(found["resumed"])
        self.assertFalse(found["retry"])

    def test_a_retry_answer_counts_only_after_the_stall(self):
        before = self.item(ask_row("ask-1", ask_kind="stall"),
                           answer_row("ask-1", "retry"), STALL)
        after = self.item(STALL, ask_row("ask-1", ask_kind="stall"),
                          answer_row("ask-1", "retry-up"))
        self.assertEqual((before["resumed"], before["retry"]), (None, False))
        self.assertEqual(after["resumed"], answer_row("ask-1", "retry-up"))
        self.assertTrue(after["retry"])

    def test_a_block_answer_resumes_nothing(self):
        found = self.item(STALL, ask_row("ask-1", ask_kind="stall"),
                          answer_row("ask-1", "block"))
        self.assertFalse(found["retry"])

    def test_a_pending_ask_blocks_retry(self):
        found = self.item(STALL, ask_row("ask-1", ask_kind="stall"),
                          answer_row("ask-1", "retry"),
                          ask_row("ask-2", ask_kind="clarify"))
        self.assertEqual(found["pending"], ask_row("ask-2",
                                                   ask_kind="clarify"))
        self.assertFalse(found["retry"])

    def test_the_latest_gate_answer_is_read(self):
        found = self.item(ask_row("ask-1", ask_kind="gate"),
                          answer_row("ask-1", "block"),
                          ask_row("ask-2", ask_kind="gate"),
                          answer_row("ask-2", "approve"))
        self.assertEqual(found["gate"], answer_row("ask-2", "approve"))

    def test_the_live_block_is_the_union_less_what_was_renumbered(self):
        found = self.item(reserve("prd", [3, 4]), reserve("adr", [7, 8]),
                          reserve("adr", [12], renumbered_from=[7]))
        self.assertEqual(found["reserved"], {"prd": (3, 4), "adr": (8, 12)})

    def test_an_unknown_item_reads_with_a_ready_made_problem(self):
        found = self.item(item="#99")
        self.assertIsNone(found["entry"])
        self.assertEqual(found["unknown"],
                         "cd: #99 is not an item of this batch's plan")
        self.assertEqual(found["state"], "planned")

    def test_the_batch_view_holds_plan_answers_and_the_queue_head(self):
        rows = [ITEM_PLAN, ask_row("ask-1"), answer_row("ask-1"),
                ask_row("ask-2", item="#13")]
        found = conductor.view(rows)
        self.assertEqual(found["plan"], ITEM_PLAN)
        self.assertEqual(found["answers"], {"ask-1": answer_row("ask-1")})
        self.assertEqual(found["next_ask"], ask_row("ask-2", item="#13"))
        self.assertEqual(set(found["items"]), {"#12", "#13"})
        self.assertEqual(found["items"]["#12"],
                         conductor.item_view(rows, "#12"))

    def test_a_read_leaves_the_rows_unchanged(self):
        rows = [ITEM_PLAN, STALL, ask_row("ask-1", ask_kind="stall"),
                answer_row("ask-1", "retry"), reserve("adr", [7]),
                reserve("adr", [12], renumbered_from=[7])]
        before = json.dumps(rows)
        conductor.view(rows)
        conductor.item_view(rows, "#12")
        self.assertEqual(json.dumps(rows), before)
        self.assertEqual(len(rows), 6)

    def test_a_non_contiguous_block_renders_each_run(self):
        from conductor_plan import span
        self.assertEqual(span([7]), "7")
        self.assertEqual(span([7, 8, 9]), "7-9")
        self.assertEqual(span([3, 4, 8, 12, 13]), "3-4,8,12-13")


class TestMain(cli_contract.CliContract, cli_contract.ReportContract,
               unittest.TestCase):
    usage_fragment = "python3 conductor.py"
    summary_line = "cd: 0 problem(s)"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        write_ledger(self.tmp.name, PLAN, ask_row("ask-1"))
        Path(self.tmp.name, ".github").mkdir()
        Path(self.tmp.name, ".github/factory.json").write_text(
            json.dumps({"wip_cap": 2}))

    def run_cli(self, argv, env=None):
        return cli_contract.capture(conductor.main, argv, env=env or {},
                                    clock=clock, root=self.tmp.name)

    def clean_cli(self):
        return self.run_cli(["next", "b1"])

    def test_next_prints_the_oldest_unanswered_ask(self):
        code, out = self.run_cli(["next", "b1"])
        self.assertEqual(code, 0)
        payload = json.loads(out[:out.rindex("\ncd:")])
        self.assertEqual(payload, {"ask": ask_row("ask-1"), "ready": [],
                                   "recorded": [], "merge_due": []})

    def test_ask_then_answer_round_trip(self):
        code, out = self.run_cli([
            "ask", "b1", "--kind", "stall", "--item", "#12",
            "--question", "Retry?", "--option", "retry",
            "--option", "block", "--recommended", "retry",
            "--why", "first failure"])
        self.assertEqual((code, out.splitlines()[0]), (0, "ask-2"))
        code, out = self.run_cli(["answer", "b1", "ask-2", "block",
                                  "--note", "flaky"])
        self.assertEqual(code, 0, out)
        rows, _ = conductor.load(self.tmp.name, "b1")
        self.assertEqual(rows[-1]["to"], "blocked")
        self.assertEqual(rows[-2], {"at": AT, "kind": "answer",
                                    "item": "#12", "ask": "ask-2",
                                    "choice": "block", "note": "flaky"})

    def test_a_refused_answer_exits_nonzero(self):
        code, out = self.run_cli(["answer", "b1", "ask-1", "yes"],
                                 env={"CONDUCTOR_WORKER": "1"})
        self.assertEqual(code, 1)
        self.assertIn("CONDUCTOR_WORKER is set", out)

    def test_a_malformed_ledger_line_fails_next(self):
        write_ledger(self.tmp.name, text=json.dumps(PLAN) + "\nnope\n")
        code, out = self.run_cli(["next", "b1"])
        self.assertEqual(code, 1)
        self.assertIn(f"cd: {LEDGER}:2 is not valid JSON", out)
        self.assertNotIn('"ask"', out)

    def test_an_ask_missing_a_flag_prints_usage(self):
        code, out = self.run_cli(["ask", "b1", "--kind", "spend"])
        self.assertEqual(code, 2)
        self.assertIn(self.usage_fragment, out)


# --- autorun's stop-after line (WO-0159) -------------------------------

class TestAutorunHonoursStopAfter(unittest.TestCase):
    """A spec Worker drives a run with autorun up to a gate and stops
    there. The skill prose is the runtime interface (it ships in the
    plugin), so the contract the spec step relies on is pinned here."""

    def text(self):
        path = Path(__file__).resolve().parents[1] / "skills" / "autorun" \
            / "SKILL.md"
        return " ".join(path.read_text(encoding="utf-8").split())

    def test_a_stop_after_line_stops_autorun_at_that_stage(self):
        text = self.text()
        self.assertIn("`stop-after: <stage>` line in `autorun-brief.md`",
                      text)
        self.assertIn("stop once that stage's artifact or recorded skip"
                      " exists, without starting the next stage", text)


if __name__ == "__main__":
    unittest.main()
