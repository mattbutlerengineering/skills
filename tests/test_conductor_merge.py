"""conductor_merge.py (PRD-0013, WO-0160, WO-0161): the merge
precondition and the merge turn. The precondition is pure over ledger
rows and the branch's gate blobs; the merge turn runs only through
injected ports (a scratch git repo with a local bare origin, FakeGh, a
fake tool runner and clock) — no real PR, push or merge — and tests
assert the EXACT problem strings and rows.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

import conductor
import conductor_flow as flow
import conductor_merge as merge

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fake_gh import FakeGh  # noqa: E402
from test_conductor_flow import (AT, NOW, START, answered,  # noqa: E402
                                 launch, moved, ran, run_id, stall_ask)

ADR = "docs/adr/0090-x.md"


def ask(ask_id, key, ask_kind, options, covers=None, gate_blobs=None):
    row = {"at": AT, "kind": "ask", "item": key, "id": ask_id,
           "ask_kind": ask_kind, "question": "Q?", "options": list(options),
           "recommended": options[0], "why": "w"}
    if covers:
        row["covers"] = list(covers)
    if gate_blobs is not None:
        row["gate_blobs"] = gate_blobs
    return row


def reviewed(key, authors, reviewer, verdict="pass"):
    return moved(key, "review", "reviewed", verdict=verdict,
                 author_runs=authors, reviewer_run=reviewer)


def order_shipped(key="#14"):
    """An order item's rows through a completed ship step."""
    return [launch(key, "planned", "build"), ran(key, "build"),
            launch(key, "build", "verify"), ran(key, "verify"),
            launch(key, "verify", "review"), ran(key, "review"),
            reviewed(key, [run_id(key, "build"), run_id(key, "verify")],
                     run_id(key, "review")),
            launch(key, "reviewed", "ship"), ran(key, "ship")]


def feature_shipped(blobs, key="#12"):
    """A feature item's rows through a completed ship step, with its gate
    ask (asked as ask-9) approved over these gate blobs."""
    return [launch(key, "planned", "spec"), ran(key, "spec"),
            moved(key, "spec", "awaiting-gate"),
            ask("ask-9", key, "gate", ["approve", "block"],
                gate_blobs=blobs),
            answered("ask-9", "approve", key),
            launch(key, "awaiting-gate", "build")] + order_shipped(key)[1:]


def own(ask_id, key, choice="merge"):
    return [ask(ask_id, key, "merge", ["merge", "block"]),
            answered(ask_id, choice, key)]


def train(ask_id, covers, choice="train"):
    return [ask(ask_id, None, "merge", ["train", "one-by-one"],
                covers=covers), answered(ask_id, choice)]


class TestMergePrecondition(unittest.TestCase):
    def problems(self, rows, key="#14", blobs=None):
        return merge.merge_problems(START + rows, key, blobs or {})

    def test_a_reviewed_shipped_item_with_its_own_answer_may_merge(self):
        self.assertEqual(self.problems(order_shipped() + own("ask-2", "#14")),
                         [])

    def test_an_item_never_reviewed_is_refused(self):
        rows = order_shipped()[:6] + own("ask-2", "#14")
        self.assertEqual(self.problems(rows),
                         ["cd: merge refused: #14 has no reviewed pass"])

    def test_a_reviewer_among_the_author_runs_is_refused(self):
        rows = order_shipped()
        rows[6] = reviewed("#14", [run_id("#14", "build")],
                           run_id("#14", "verify"))
        self.assertEqual(
            self.problems(rows + own("ask-2", "#14")),
            ["cd: merge refused: #14's reviewer run conductor-b1-14-verify-1"
             " is among its author runs"])

    def test_an_unfinished_ship_step_is_refused(self):
        rows = order_shipped()[:-1] + own("ask-2", "#14")
        self.assertEqual(self.problems(rows),
                         ["cd: merge refused: #14's ship step has not"
                          " completed"])

    def test_an_item_with_no_covering_answer_is_refused(self):
        self.assertEqual(self.problems(order_shipped()),
                         ["cd: merge refused: no merge answer covers #14"])

    def test_an_own_ask_answered_otherwise_does_not_cover(self):
        rows = order_shipped() + [ask("ask-2", "#14", "merge",
                                      ["merge", "hold"]),
                                  answered("ask-2", "hold", "#14")]
        self.assertEqual(self.problems(rows),
                         ["cd: merge refused: no merge answer covers #14"])

    def test_an_unanswered_merge_ask_is_refused(self):
        rows = order_shipped() + own("ask-2", "#14")[:1]
        self.assertEqual(self.problems(rows),
                         ["cd: #14 has an unanswered ask (ask-2)"])

    def test_a_train_covers_its_first_item(self):
        rows = order_shipped() + train("ask-2", ["#14", "#13"])
        self.assertEqual(self.problems(rows), [])

    def test_a_train_answered_otherwise_does_not_cover(self):
        rows = order_shipped() + train("ask-2", ["#14"], "one-by-one")
        self.assertEqual(self.problems(rows),
                         ["cd: merge refused: no merge answer covers #14"])

    def test_a_train_waits_for_every_earlier_item_to_merge(self):
        rows = order_shipped() + train("ask-2", ["#13", "#14"])
        self.assertEqual(
            self.problems(rows),
            ["cd: merge refused: #14 rides train ask-2 behind #13, which is"
             " planned, not merged"])
        merged = moved("#13", "merging", "merged", pr=5, sha="abc",
                       checks={})
        self.assertEqual(self.problems(rows + [merged]), [])

    def test_a_gate_path_item_rides_a_train_on_identical_blobs(self):
        blobs = {ADR: "aaa", "docs/features/x/prd.md": "bbb"}
        rows = feature_shipped(blobs) + train("ask-2", ["#12"])
        self.assertEqual(self.problems(rows, "#12", blobs), [])

    def test_a_changed_gate_blob_is_refused_on_a_train(self):
        rows = feature_shipped({ADR: "aaa"}) + train("ask-2", ["#12"])
        self.assertEqual(
            self.problems(rows, "#12", {ADR: "ccc"}),
            [f"cd: merge refused: #12's gate file {ADR} is not the one"
             " approved at its gate ask; it needs its own merge ask"])

    def test_a_gate_file_never_approved_is_refused_on_a_train(self):
        rows = feature_shipped({}) + train("ask-2", ["#12"])
        self.assertEqual(
            self.problems(rows, "#12", {ADR: "aaa"}),
            [f"cd: merge refused: #12's gate file {ADR} is not the one"
             " approved at its gate ask; it needs its own merge ask"])

    def test_its_own_merge_answer_covers_a_changed_gate_file(self):
        rows = feature_shipped({ADR: "aaa"}) + own("ask-2", "#12")
        self.assertEqual(self.problems(rows, "#12", {ADR: "ccc"}), [])

    def test_an_item_outside_the_plan_is_refused(self):
        self.assertEqual(self.problems([], "#99"),
                         ["cd: #99 is not an item of this batch's plan"])


# --- the merge turn, over a scratch repo with a local bare origin --------

BRANCH = "conductor/b1-12"
LEDGER = "docs/factory/batches/b1/ledger.jsonl"
SEED = {".gitattributes": "docs/factory/costs.jsonl merge=union\n",
        "docs/factory/costs.jsonl": '{"row": "seed"}\n',
        ".claude-plugin/plugin.json": '{\n  "name": "p",\n'
                                      '  "version": "0.7.3"\n}\n',
        "factory/manifest.json": '{"files": "seed"}\n',
        "README.md": "readme\n",
        "docs/adr/README.md": "# ADRs\n\nThe index.\n\n- ADR-0001 a\n"
                              "- ADR-0002 b\n- ADR-0003 c\n"}
GREEN_RUN = {"name": "validate", "status": "completed",
             "conclusion": "success"}


def sh(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True,
                          capture_output=True, text=True).stdout


def write(root, files):
    for path, text in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text)


def commit(cwd, files, message="c"):
    write(Path(cwd), files)
    sh(cwd, "add", "-A")
    sh(cwd, "commit", "-q", "-m", message)


class Clock:
    """The wall clock the turn stamps rows and times waits with; sleep
    advances it."""

    def __init__(self):
        self.now, self.slept = NOW, []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += timedelta(seconds=seconds)


def replies(*values):
    """A FakeGh answer that replies with each value in turn, then the
    last one forever."""
    queue = [json.dumps(v) for v in values]

    def answer(args):
        return queue.pop(0) if len(queue) > 1 else queue[0]
    return answer


class TurnCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        seed = self.tmp / "seed"
        seed.mkdir()
        sh(seed, "init", "-q", "-b", "main")
        self.configure(seed)
        commit(seed, SEED)
        subprocess.run(["git", "clone", "-q", "--bare", str(seed),
                        str(self.tmp / "origin.git")], check=True)
        self.repo = self.tmp / "repo"
        subprocess.run(["git", "clone", "-q", str(self.tmp / "origin.git"),
                        str(self.repo)], check=True)
        self.configure(self.repo)
        self.wt = self.repo / ".claude/worktrees/conductor-b1-12"
        sh(self.repo, "worktree", "add", "-q", "-b", BRANCH, str(self.wt),
           "origin/main")
        self.root = self.tmp / "batch"
        self.log, self.clock = [], Clock()

    @staticmethod
    def configure(cwd):
        for key, value in (("user.email", "t@example.com"),
                           ("user.name", "t"), ("commit.gpgsign", "false"),
                           ("core.hooksPath", os.devnull)):
            sh(cwd, "config", key, value)

    def item(self, files, message="item"):
        """Commit on the item branch and push it (the runner's work)."""
        commit(self.wt, files, message)
        sh(self.wt, "push", "-q", "-u", "origin", BRANCH)

    def main_moves(self, files):
        """Another merge lands on origin/main."""
        commit(self.repo, files, "main")
        sh(self.repo, "push", "-q", "origin", "main")

    def ledger(self, rows):
        path = self.root / LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))

    def git(self, args):
        self.log.append(("git", list(args)))
        return subprocess.run(["git", "-C", str(self.repo), *args],
                              check=True, capture_output=True, text=True)

    def tool(self, fail=None):
        def run(args):
            self.log.append(("tool", list(args)))
            if fail and fail in args:
                raise subprocess.CalledProcessError(
                    2, args, stderr="make: *** [check] Error 1\n")
            if "update-manifest" in args:
                (Path(args[1]).parent / "factory/manifest.json").write_text(
                    '{"files": "regenerated"}\n')
            return subprocess.CompletedProcess(args, 0, "", "")
        return run

    def fake_gh(self, checks=([GREEN_RUN],), queue=None, views=None):
        """`checks` is the check runs each successive read returns."""
        fake = FakeGh(answers={
            ("pr", "list"): json.dumps([{"number": 44}]),
            ("api",): replies(*[{"total_count": len(c), "check_runs":
                                 list(c)} for c in checks]),
            ("api", "graphql"): json.dumps(
                {"data": {"repository": {"mergeQueue": queue}}}),
            ("pr", "view"): replies(*(views or [
                {"state": "MERGED", "mergeCommit": {"oid": "m1"}}]))})

        def gh(args):
            self.log.append(("gh", list(args)))
            return fake(args)
        gh.fake = fake
        return gh

    def turn(self, rows, gh=None, tool=None):
        self.ledger(START + rows)
        self.gh = gh or self.fake_gh()
        summary, problems = merge.merge_turn(
            self.root, "b1", "#12", self.clock, self.git, self.gh,
            tool or self.tool(), self.clock.sleep)
        self.rows, _ = conductor.load(self.root, "b1")
        return summary, problems

    def calls(self, port, word):
        return [args for kind, args in self.log
                if kind == port and word in args]

    def first(self, port, word):
        """The log index of the first call on `port` carrying `word`."""
        return next(index for index, (kind, args) in enumerate(self.log)
                    if kind == port and word in args)

    def head(self, ref=BRANCH):
        return sh(self.repo, "rev-parse", ref).strip()


SHIPPED = feature_shipped({}) + own("ask-2", "#12")


class TestMergeTurn(TurnCase):
    def test_the_eight_steps_run_in_order_and_record_merged(self):
        self.item({"docs/factory/costs.jsonl":
                   '{"row": "seed"}\n{"row": "item"}\n',
                   "src.txt": "item\n"})
        self.main_moves({"docs/factory/costs.jsonl":
                         '{"row": "seed"}\n{"row": "main"}\n'})
        summary, problems = self.turn(SHIPPED)
        self.assertEqual(problems, [])
        self.assertEqual(summary["sha"], "m1")
        steps = [("git", "fetch"), ("git", "merge"), ("tool", "check"),
                 ("git", "push"),
                 ("gh", f"repos/{{owner}}/{{repo}}/commits/{self.head()}"
                        "/check-runs?per_page=100"),
                 ("gh", "graphql"), ("gh", "merge")]
        firsts = [self.first(*step) for step in steps]
        self.assertEqual(firsts, sorted(firsts))
        costs = (self.wt / "docs/factory/costs.jsonl").read_text()
        self.assertEqual(costs, '{"row": "seed"}\n{"row": "item"}\n'
                                '{"row": "main"}\n')
        self.assertEqual(self.head(), self.head("origin/" + BRANCH))
        sh(self.repo, "merge-base", "--is-ancestor", "origin/main", BRANCH)
        self.assertEqual(self.gh.fake.called("pr", "merge"), [[
            "pr", "merge", "44", "--squash", "--match-head-commit",
            self.head()]])
        self.assertEqual(self.rows[-2]["to"], "merging")
        self.assertEqual(self.rows[-1], {
            "at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#12",
            "from": "merging", "to": "merged", "reason": "merged as m1",
            "pr": 44, "sha": "m1", "checks": {"validate": "success"}})
        self.assertFalse([args for _, args in self.log
                          if any("force" in a for a in args)])

    def test_a_skills_change_bumps_the_patch_version_from_main(self):
        self.item({"skills/x/SKILL.md": "x\n"})
        self.main_moves({".claude-plugin/plugin.json":
                         SEED[".claude-plugin/plugin.json"].replace(
                             "0.7.3", "0.7.5")})
        self.assertEqual(self.turn(SHIPPED)[1], [])
        plugin = json.loads((self.wt / ".claude-plugin/plugin.json")
                            .read_text())
        self.assertEqual(plugin["version"], "0.7.6")
        self.assertLess(self.first("git", "merge"),
                        self.first("tool", "update-manifest"))
        self.assertLess(self.first("tool", "update-manifest"),
                        self.first("tool", "check"))
        self.assertEqual(sh(self.repo, "show", f"{BRANCH}:factory/"
                            "manifest.json"), '{"files": "regenerated"}\n')
        self.assertIn({"at": "2026-10-10T12:30:00Z", "kind": "reserve",
                       "item": "#12", "what": "plugin-version",
                       "values": ["0.7.6"]}, self.rows)

    def test_no_skills_change_leaves_the_version(self):
        self.item({"src.txt": "x\n"})
        self.turn(SHIPPED)
        self.assertIn('"version": "0.7.3"',
                      (self.wt / ".claude-plugin/plugin.json").read_text())
        self.assertFalse(self.calls("tool", "update-manifest"))

    def test_a_manifest_conflict_is_resolved_by_regeneration(self):
        self.item({"factory/manifest.json": '{"files": "item"}\n'})
        self.main_moves({"factory/manifest.json": '{"files": "main"}\n'})
        summary, problems = self.turn(SHIPPED)
        self.assertEqual((problems, summary["stall"]), ([], None))
        self.assertEqual(sh(self.repo, "show", f"{BRANCH}:factory/"
                            "manifest.json"), '{"files": "regenerated"}\n')


class TestMergeTurnStalls(TurnCase):
    def assertStalled(self, summary, reason):
        self.assertEqual(summary["stall"], reason)
        self.assertEqual(self.rows[-2]["to"], "stalled")
        self.assertEqual(self.rows[-2]["reason"], reason)
        self.assertEqual(self.rows[-1]["ask_kind"], "stall")
        self.assertEqual(self.head("origin/" + BRANCH), self.pushed)

    def item(self, files, message="item"):
        super().item(files, message)
        self.pushed = self.head()

    def test_a_non_mechanical_conflict_stalls_and_aborts(self):
        self.item({"README.md": "item\n"})
        self.main_moves({"README.md": "main\n"})
        summary, problems = self.turn(SHIPPED)
        self.assertEqual(problems, [])
        self.assertStalled(summary, f"merging origin/main into {BRANCH}"
                           " conflicts in README.md")
        self.assertEqual(self.head(), self.pushed)
        self.assertFalse((self.repo / ".git/worktrees/conductor-b1-12/"
                          "MERGE_HEAD").exists())
        self.assertFalse(self.calls("git", "push"))
        self.assertEqual(self.rows[-1]["recommended"], "block")

    def test_a_red_make_check_stalls_before_any_push(self):
        self.item({"src.txt": "x\n"})
        summary, _ = self.turn(SHIPPED, tool=self.tool(fail="check"))
        self.assertStalled(summary, f"make check failed on {BRANCH}:"
                           " make: *** [check] Error 1")
        self.assertFalse(self.calls("git", "push"))

    def test_a_red_check_run_stalls_without_merging(self):
        self.item({"src.txt": "x\n"})
        red = dict(GREEN_RUN, conclusion="failure")
        summary, _ = self.turn(SHIPPED, gh=self.fake_gh(checks=[[red]]))
        self.assertStalled(summary,
                           f"checks failed on {self.head()[:12]}: validate")
        self.assertFalse(self.gh.fake.called("pr", "merge"))

    def test_checks_that_never_finish_time_out_after_30_minutes(self):
        self.item({"src.txt": "x\n"})
        pending = dict(GREEN_RUN, status="in_progress", conclusion=None)
        summary, _ = self.turn(SHIPPED, gh=self.fake_gh(checks=[[pending]]))
        self.assertStalled(summary, f"checks on {self.head()[:12]} did not"
                           " finish within 30 minutes")
        self.assertEqual(sum(self.clock.slept), 30 * 60)
        self.assertEqual(self.rows[-1]["recommended"], "retry")
        self.assertFalse(self.gh.fake.called("pr", "merge"))

    def test_pending_checks_are_waited_for(self):
        self.item({"src.txt": "x\n"})
        pending = dict(GREEN_RUN, status="queued", conclusion=None)
        summary, _ = self.turn(SHIPPED, gh=self.fake_gh(
            checks=[[], [pending], [GREEN_RUN]]))
        self.assertEqual(summary["sha"], "m1")
        self.assertEqual(self.clock.slept, [30, 30])

    def test_a_queue_is_used_when_main_has_one(self):
        self.item({"src.txt": "x\n"})
        summary, _ = self.turn(SHIPPED, gh=self.fake_gh(
            queue={"id": "q"}, views=[
                {"state": "OPEN", "isInMergeQueue": True},
                {"state": "MERGED", "mergeCommit": {"oid": "q1"}}]))
        self.assertEqual(summary["sha"], "q1")
        self.assertEqual(self.rows[-1]["to"], "merged")

    def test_an_ejection_from_the_queue_stalls(self):
        self.item({"src.txt": "x\n"})
        summary, _ = self.turn(SHIPPED, gh=self.fake_gh(
            queue={"id": "q"}, views=[
                {"state": "OPEN", "isInMergeQueue": True},
                {"state": "OPEN", "isInMergeQueue": False}]))
        self.assertStalled(summary,
                           "PR #44 was ejected from the merge queue")

    def test_a_queue_that_never_merges_times_out(self):
        self.item({"src.txt": "x\n"})
        summary, _ = self.turn(SHIPPED, gh=self.fake_gh(
            queue={"id": "q"}, views=[{"state": "OPEN",
                                       "isInMergeQueue": True}]))
        self.assertStalled(summary, "PR #44 did not merge from the queue"
                           " within 30 minutes")

    def test_a_stalled_merge_resumes_as_a_merge(self):
        rows = START + SHIPPED + [moved("#12", "ship", "merging"),
                                  moved("#12", "merging", "stalled"),
                                  stall_ask("ask-3", "#12"),
                                  answered("ask-3", "retry", "#12")]
        ready, _, _ = flow.survey(rows, NOW, 3, lambda pid: True, {})
        self.assertIn({"item": "#12", "step": "merge"}, ready)
        self.assertEqual(merge.merge_problems(rows, "#12", {}), [])


def adr_rows(blobs=None):
    """#12 holds ADRs 90-92; covered by its own answer, or a train."""
    reserve = {"at": AT, "kind": "reserve", "item": "#12", "what": "adr",
               "values": [90, 91, 92]}
    other = dict(reserve, item="#13", values=[93])
    cover = own("ask-2", "#12") if blobs is None else train("ask-2",
                                                            ["#12"])
    return [reserve, other] + feature_shipped(blobs or {}) + cover


class TestReservations(TurnCase):
    ITEM = {"docs/adr/0091-item.md": "# ADR-0091 item\n",
            "docs/adr/README.md": SEED["docs/adr/README.md"]
            + "- [ADR-0091](0091-item.md) item\n"}
    # Main's index row lands far enough from the item's to merge cleanly.
    MAIN = {"docs/adr/0091-main.md": "# ADR-0091 main\n",
            "docs/adr/README.md": SEED["docs/adr/README.md"].replace(
                "The index.\n", "The index.\n- [ADR-0091](0091-main.md)"
                " main\n")}

    def test_a_free_number_is_confirmed_untouched(self):
        self.item(self.ITEM)
        self.assertEqual(self.turn(adr_rows())[1], [])
        self.assertTrue((self.wt / "docs/adr/0091-item.md").is_file())
        self.assertFalse([r for r in self.rows if "renumbered_from" in r])

    def test_a_number_taken_on_main_is_renumbered_mechanically(self):
        self.item(self.ITEM)
        self.main_moves(self.MAIN)
        summary, problems = self.turn(adr_rows())
        self.assertEqual((problems, summary["stall"]), ([], None))
        self.assertEqual(sorted(p.name for p in (self.wt / "docs/adr")
                                .iterdir()),
                         ["0091-main.md", "0094-item.md", "README.md"])
        self.assertEqual((self.wt / "docs/adr/0094-item.md").read_text(),
                         "# ADR-0094 item\n")
        index = (self.wt / "docs/adr/README.md").read_text()
        self.assertIn("- [ADR-0091](0091-main.md) main\n", index)
        self.assertIn("- [ADR-0094](0094-item.md) item\n", index)
        self.assertIn({"at": "2026-10-10T12:30:00Z", "kind": "reserve",
                       "item": "#12", "what": "adr", "values": [94],
                       "renumbered_from": [91]}, self.rows)
        self.assertEqual(self.rows[-1]["to"], "merged")
        self.assertLess(self.first("git", "grep"), self.first("tool",
                                                               "check"))

    def test_a_number_that_cannot_be_renumbered_stalls(self):
        self.item(self.ITEM)
        self.main_moves(dict(self.MAIN, **{"docs/x.md": "ADR-9999\n"}))
        summary, _ = self.turn(adr_rows())
        self.assertEqual(summary["stall"], "ADR-0091 is taken on origin/main"
                         " and cannot be renumbered: ADR-10000 would leave"
                         " the 4-digit grammar")
        self.assertFalse(self.calls("git", "push"))

    def test_a_renumbered_gate_file_no_longer_rides_a_train(self):
        self.item(self.ITEM)
        blobs = {path: sh(self.repo, "rev-parse", f"{BRANCH}:{path}").strip()
                 for path in self.ITEM}
        self.main_moves(self.MAIN)
        summary, _ = self.turn(adr_rows(blobs))
        self.assertTrue(summary["stall"].startswith(
            "merge refused: #12's gate file docs/adr/"), summary)
        self.assertFalse(self.calls("git", "push"))


class TestMergeCli(TurnCase):
    def test_merge_is_a_conductor_verb(self):
        self.item({"src.txt": "x\n"})
        self.ledger(START + SHIPPED)
        code, out = cli_contract.capture(
            conductor.main, ["merge", "b1", "#12"], env={}, clock=self.clock,
            root=self.root, run=self.fake_gh(), git=self.git,
            tool=self.tool(), sleep=self.clock.sleep)
        self.assertEqual(code, 0, out)
        self.assertIn("cd: merged #12 as m1 (PR #44)", out)

    def test_a_refused_merge_touches_nothing(self):
        self.item({"src.txt": "x\n"})
        self.ledger(START + feature_shipped({}))
        before = (self.root / LEDGER).read_text()
        code, out = cli_contract.capture(
            conductor.main, ["merge", "b1", "#12"], env={}, clock=self.clock,
            root=self.root, run=self.fake_gh(), git=self.git,
            tool=self.tool(), sleep=self.clock.sleep)
        self.assertEqual(code, 1)
        self.assertIn("cd: merge refused: no merge answer covers #12", out)
        self.assertEqual((self.root / LEDGER).read_text(), before)
        self.assertFalse(self.calls("git", "fetch"))
        self.assertFalse([e for e in self.log if e[0] == "tool"])


if __name__ == "__main__":
    unittest.main()
