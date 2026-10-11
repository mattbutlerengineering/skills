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

    def test_an_ask_may_carry_a_train_and_gate_blobs(self):
        row = dict(ask_row("ask-1"), covers=["#12", "#13"],
                   gate_blobs={"docs/adr/0090-x.md": "abc123"})
        self.assertEqual(conductor.row_problems(row), [])


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
                " digits and hyphens)"]))


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



# --- plan and open (WO-0156) -------------------------------------------

OWNER = {"owner": {"login": "matt"}}


def issue(number, labels=("type:feature", "size:M"), state="OPEN",
          author="matt"):
    return {"number": number, "state": state, "author": {"login": author},
            "labels": [{"name": name} for name in labels]}


def fake_gh(issues, owner=OWNER, fail=None):
    """A gh port answering repo view and issue view from canned data;
    `fail` names an issue number whose read raises."""
    import subprocess

    def run(args):
        if args[:2] == ["repo", "view"]:
            return json.dumps(owner)
        if args[:2] == ["issue", "view"]:
            if args[2] == str(fail):
                raise subprocess.CalledProcessError(1, args,
                                                    stderr="HTTP 502")
            return json.dumps(issues[int(args[2])])
        raise AssertionError(args)
    return run


def fake_git(grep="PRD-0013\nADR-0083\nWO-0152\nWO-0007\n", calls=None):
    import subprocess

    def run(args):
        if calls is not None:
            calls.append(args)
        if args[0] == "grep":
            return subprocess.CompletedProcess(args, 0, stdout=grep,
                                               stderr="")
        if args[:2] == ["worktree", "add"]:
            Path(args[4]).mkdir(parents=True)
            return subprocess.CompletedProcess(args, 0, stdout="",
                                               stderr="")
        raise AssertionError(args)
    return run


CONFIG = {"budgets_usd": {"S": 5, "M": 15, "L": 40},
          "routing": {"mechanical": "haiku", "implementation": "sonnet",
                      "architecture_review": "fable"},
          "effort": {"mechanical": "low", "implementation": "medium",
                     "architecture_review": "high"},
          "wip_cap": 3, "monthly_cap_usd": 300}
AGENTS = Path(__file__).resolve().parents[1] / "factory" / "agents"
HIGHEST = {"prd": 13, "adr": 83, "wo": 152}


def plan(issues, config=CONFIG, spent=0.0, highest=HIGHEST):
    return conductor.plan_batch(issues, "matt", config, spent, highest,
                                AGENTS)


class TestIdsInUse(unittest.TestCase):
    def test_the_highest_of_each_kind_on_origin_main(self):
        calls = []
        self.assertEqual(conductor.ids_in_use(fake_git(calls=calls)),
                         (HIGHEST, []))
        self.assertEqual(calls, [["grep", "-h", "-o", "-E",
                                  "(PRD|ADR|WO)-[0-9]{4}", "origin/main",
                                  "--", "docs"]])

    def test_no_ids_at_all_is_zero(self):
        import subprocess

        def run(args):
            raise subprocess.CalledProcessError(1, args, stderr="")
        self.assertEqual(conductor.ids_in_use(run),
                         ({"prd": 0, "adr": 0, "wo": 0}, []))

    def test_a_failing_grep_is_a_problem(self):
        import subprocess

        def run(args):
            raise subprocess.CalledProcessError(128, args,
                                                stderr="bad revision")
        self.assertEqual(conductor.ids_in_use(run), (None, [
            "cd: git grep origin/main failed: bad revision"]))


class TestReadIssues(unittest.TestCase):
    def test_reads_each_issue(self):
        issues = {12: issue(12), 13: issue(13)}
        self.assertEqual(conductor.read_issues([12, 13], fake_gh(issues)),
                         ([issues[12], issues[13]], []))

    def test_an_unreadable_issue_refuses_the_read(self):
        self.assertEqual(
            conductor.read_issues([12, 13], fake_gh({12: issue(12)},
                                                    fail=13)),
            (None, ["cd: gh issue view #13 failed: HTTP 502"]))

    def test_a_truncated_issue_refuses_the_read(self):
        partial = {12: {"number": 12, "state": "OPEN", "labels": []}}
        self.assertEqual(conductor.read_issues([12], fake_gh(partial)), (
            None, ["cd: gh issue view #12 returned an incomplete issue"]))

    def test_the_owner_is_read_and_fails_closed(self):
        self.assertEqual(conductor.repo_owner(fake_gh({})), ("matt", []))
        self.assertEqual(conductor.repo_owner(fake_gh({}, owner={})),
                         (None, ["cd: gh repo view names no owner"]))


class TestPlanBatch(unittest.TestCase):
    def test_a_feature_item_is_priced_step_by_step(self):
        result, problems = plan([issue(12)])
        self.assertEqual(problems, [])
        self.assertEqual(result["items"], [{
            "item": "#12", "type": "feature", "size": "M",
            "steps": [
                {"step": "spec", "charter": "architect",
                 "band": "architecture_review", "model": "fable",
                 "effort": "high", "ceiling_usd": 3.0},
                {"step": "build", "charter": "swe",
                 "band": "implementation", "model": "sonnet",
                 "effort": "medium", "ceiling_usd": 3.0},
                {"step": "verify", "charter": "qa",
                 "band": "implementation", "model": "sonnet",
                 "effort": "medium", "ceiling_usd": 3.0},
                {"step": "review", "charter": "reviewer",
                 "band": "architecture_review", "model": "fable",
                 "effort": "high", "ceiling_usd": 3.0},
                {"step": "ship", "charter": "qa",
                 "band": "implementation", "model": "sonnet",
                 "effort": "medium", "ceiling_usd": 3.0}],
            "estimate_usd": 15, "after": [],
            "block": {"prd": [14], "adr": [84, 85, 86],
                      "wo": list(range(153, 163))}}])
        self.assertEqual((result["estimate_usd"], result["cap_usd"],
                          result["month_to_date_usd"]), (15, 300, 0.0))
        self.assertEqual(result["policy"], {"routing": CONFIG["routing"],
                                            "effort": CONFIG["effort"]})

    def test_types_map_from_labels(self):
        result, _ = plan([
            issue(1, ("type:defect", "size:S")),
            issue(2, ("type:chore", "size:S")),
            issue(3, ("type:support", "wo:ready-for-agent", "size:S"))])
        self.assertEqual(
            [(i["type"], [s["step"] for s in i["steps"]], i["block"])
             for i in result["items"]],
            [("fix", ["spec", "build", "verify", "review", "ship"],
              {"adr": [84], "wo": [153, 154, 155, 156, 157]}),
             ("fix", ["spec", "build", "verify", "review", "ship"],
              {"adr": [85], "wo": [158, 159, 160, 161, 162]}),
             ("order", ["build", "verify", "review", "ship"], {})])
        self.assertEqual(result["items"][2]["steps"][0]["charter"],
                         "support")

    def test_no_two_items_blocks_share_a_number(self):
        result, _ = plan([issue(n) for n in (1, 2, 3)]
                         + [issue(4, ("type:defect", "size:S"))])
        for kind in ("prd", "adr", "wo"):
            values = [v for i in result["items"]
                      for v in i["block"].get(kind, [])]
            self.assertEqual(len(values), len(set(values)), kind)
            self.assertGreater(min(values), HIGHEST[kind], kind)

    def test_every_deferral_has_its_own_line(self):
        result, problems = plan([
            issue(1, author="mallory"), issue(2, ("size:S",)),
            issue(3, ("type:feature",)), issue(4, state="CLOSED"),
            issue(5, ("type:sweep", "size:S")),
            issue(6, ("type:feature", "size:L"))], spent=270.0)
        self.assertEqual(problems, [])
        self.assertEqual(result["items"], [])
        self.assertEqual(result["deferred"], [
            "#1 deferred: authored by mallory, not the repo owner matt",
            "#2 deferred: no type: label",
            "#3 deferred: no size: label",
            "#4 deferred: closed",
            "#5 deferred: type:sweep is not plannable",
            "#6 deferred: its $40.00 estimate is over the $30.00 left of"
            " the $300.00 monthly cap"])

    def test_the_cap_counts_earlier_items_in_the_batch(self):
        result, _ = plan([issue(1), issue(2)], spent=275.0)
        self.assertEqual([i["item"] for i in result["items"]], ["#1"])
        self.assertEqual(result["deferred"], [
            "#2 deferred: its $15.00 estimate is over the $10.00 left of"
            " the $300.00 monthly cap"])

    def test_a_config_problem_plans_nothing(self):
        config = dict(CONFIG, effort={"mechanical": "low"})
        self.assertEqual(plan([issue(12)], config=config), (None, [
            "config: factory.json names no effort for the"
            " architecture_review band",
            "config: factory.json names no effort for the implementation"
            " band"]))


class TestComposePlan(unittest.TestCase):
    def test_the_plan_as_report_lines(self):
        result, _ = plan([issue(12), issue(13, ("size:S",))], spent=20.0)
        lines = conductor.compose_plan(result)
        self.assertEqual(lines[0], "cd: 1 item(s) planned")
        self.assertEqual(lines[1], "  #12  feature  size:M  $15.00"
                         "  reserves prd 14, adr 84-86, wo 153-162")
        self.assertEqual(lines[2], "    spec    architect  architecture_review"
                         "  fable  high  $3.00")
        self.assertEqual(lines[-2], "  batch estimate $15.00 against"
                         " $280.00 left of the $300.00 monthly cap")
        self.assertEqual(lines[-1], "  #13 deferred: no type: label")


class TestOpen(unittest.TestCase):
    def test_opens_the_branch_worktree_ledger_and_spend_ask(self):
        result, _ = plan([issue(12), issue(13, ("type:defect", "size:S"))])
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            worktree, problems = conductor.open_batch(
                tmp, "b1", result, clock(), fake_git(calls=calls))
            self.assertEqual(problems, [])
            self.assertEqual(worktree,
                             Path(tmp) / ".claude/worktrees/conductor-b1")
            rows, problems = conductor.load(worktree, "b1")
        self.assertEqual(calls, [["worktree", "add", "-b", "conductor/b1",
                                  str(worktree), "origin/main"]])
        self.assertEqual(problems, [])
        self.assertEqual([r["kind"] for r in rows],
                         ["plan", "reserve", "reserve", "reserve",
                          "reserve", "reserve", "ask"])
        self.assertEqual(rows[0]["batch"], "b1")
        self.assertNotIn("block", rows[0]["items"][0])
        self.assertEqual(rows[0]["policy"], result["policy"])
        self.assertEqual(
            [(r["item"], r["what"], r["values"]) for r in rows[1:6]],
            [("#12", "prd", [14]), ("#12", "adr", [84, 85, 86]),
             ("#12", "wo", list(range(153, 163))),
             ("#13", "adr", [87]), ("#13", "wo", [163, 164, 165, 166, 167])])
        self.assertEqual(rows[-1], {
            "at": AT, "kind": "ask", "item": None, "id": "ask-1",
            "ask_kind": "spend",
            "question": "Spend up to $20.00 on batch b1 (2 item(s))?",
            "options": ["approve", "decline"], "recommended": "approve",
            "why": "the $20.00 estimate fits the $300.00 left of the"
                   " $300.00 monthly cap"})

    def test_an_all_deferred_plan_opens_nothing(self):
        result, _ = plan([issue(12, state="CLOSED")])
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                conductor.open_batch(tmp, "b1", result, clock(),
                                     fake_git(calls=calls)),
                (None, ["cd: nothing to open: every issue was deferred"]))
        self.assertEqual(calls, [])

    def test_an_existing_worktree_is_never_reused(self):
        result, _ = plan([issue(12)])
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".claude/worktrees/conductor-b1").mkdir(
                parents=True)
            self.assertEqual(
                conductor.open_batch(tmp, "b1", result, clock(), fake_git()),
                (None, ["cd: .claude/worktrees/conductor-b1 already"
                        " exists"]))

    def test_a_bad_batch_name_is_refused_before_git(self):
        result, _ = plan([issue(12)])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                conductor.open_batch(tmp, "B 1", result, clock(),
                                     fake_git())[1],
                ["cd: batch 'B 1' is not a batch name (lowercase letters,"
                 " digits and hyphens)"])


class TestPlanCli(unittest.TestCase):
    def run_cli(self, argv, issues, fail=None):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".github").mkdir()
            Path(tmp, ".github/factory.json").write_text(json.dumps(CONFIG))
            Path(tmp, "factory").mkdir()
            Path(tmp, "factory/agents").symlink_to(AGENTS)
            return cli_contract.capture(
                conductor.main, argv, env={}, clock=clock, root=tmp,
                run=fake_gh(issues, fail=fail), git=fake_git())

    def test_plan_prints_the_plan(self):
        code, out = self.run_cli(["plan", "#12"], {12: issue(12)})
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines()[0], "cd: 1 item(s) planned")
        self.assertEqual(out.splitlines()[-1], "cd: 0 problem(s)")

    def test_an_unreadable_issue_refuses_the_whole_plan(self):
        code, out = self.run_cli(["plan", "#12", "#13"], {12: issue(12)},
                                 fail=13)
        self.assertEqual(code, 1)
        self.assertNotIn("planned", out)
        self.assertIn("cd: gh issue view #13 failed: HTTP 502", out)

    def test_an_issue_argument_must_be_an_issue_key(self):
        code, out = self.run_cli(["plan", "12"], {12: issue(12)})
        self.assertEqual(code, 2)


class TestMain(cli_contract.CliContract, cli_contract.ReportContract,
               unittest.TestCase):
    usage_fragment = "python3 conductor.py"
    summary_line = "cd: 0 problem(s)"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        write_ledger(self.tmp.name, PLAN, ask_row("ask-1"))

    def run_cli(self, argv, env=None):
        return cli_contract.capture(conductor.main, argv, env=env or {},
                                    clock=clock, root=self.tmp.name)

    def clean_cli(self):
        return self.run_cli(["next", "b1"])

    def test_next_prints_the_oldest_unanswered_ask(self):
        code, out = self.run_cli(["next", "b1"])
        self.assertEqual(code, 0)
        payload = json.loads(out[:out.rindex("\ncd:")])
        self.assertEqual(payload, {"ask": ask_row("ask-1")})

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
        self.assertEqual(rows[-1], {"at": AT, "kind": "answer",
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


if __name__ == "__main__":
    unittest.main()
