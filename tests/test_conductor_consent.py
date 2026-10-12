"""The standing-consent merge policy (ADR-0086, issue #679): opt-in in
factory.json and OFF by default. When on, `next` records a `consent`
row for a shipped item no Owner merge ask covers, provided the item
changes no gate-path file and, if tier labels are configured, its issue
carries one; the merge turn then needs no in-session answer, and still
holds every other precondition. Every git, gh and tool call is a fake or
a scratch repo, and tests assert the EXACT problem strings and rows.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import conductor
import conductor_close as close
import conductor_consent as consent
import conductor_flow as flow
import conductor_merge as merge
import factory_config

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
import test_conductor_merge as tcm  # noqa: E402
from fake_gh import FakeGh  # noqa: E402
from test_conductor_flow import (AT, LEDGER, NOW, START,  # noqa: E402
                                 answered, alive, clock)

REPO = Path(__file__).resolve().parent.parent
ON = {"enabled": True, "tier_labels": []}
TIERED = {"enabled": True, "tier_labels": ["tier:low", "tier:docs"]}
OFF = {"enabled": False, "tier_labels": []}
ADR = "docs/adr/0090-x.md"
SHIPPED = tcm.feature_shipped({})
ROW = {"at": AT, "kind": "consent", "item": "#12", "policy": "standing",
       "reason": "standing consent (ADR-0086): no gate-path file changed"}


def config(policy):
    return {"conductor": {"standing_consent": policy}}


class TestPolicyConfig(unittest.TestCase):
    def test_absent_the_policy_is_off(self):
        self.assertEqual(factory_config.resolve_standing_consent({}),
                         (OFF, []))
        self.assertEqual(factory_config.resolve_standing_consent(
            {"conductor": {}}), (OFF, []))

    def test_a_configured_policy_is_read(self):
        self.assertEqual(factory_config.resolve_standing_consent(
            config(TIERED)), (TIERED, []))
        self.assertEqual(factory_config.resolve_standing_consent(
            config({"enabled": True})), (ON, []))

    def test_a_malformed_policy_is_a_problem_never_a_default(self):
        for policy, problem in (
                ([], "conductor.standing_consent must be an object"),
                ({"enabled": "yes"},
                 "conductor.standing_consent.enabled must be true or"
                 " false"),
                ({"enabled": True, "tier_labels": "tier:low"},
                 "conductor.standing_consent.tier_labels must be a list"
                 " of distinct label names"),
                ({"enabled": True, "tier_labels": ["a", "a"]},
                 "conductor.standing_consent.tier_labels must be a list"
                 " of distinct label names"),
                ({"enabled": True, "tiers": []},
                 "conductor.standing_consent has unknown key(s): tiers")):
            with self.subTest(policy=policy):
                self.assertEqual(
                    factory_config.resolve_standing_consent(config(policy)),
                    (None, [f"config: factory.json {problem}"]))

    def test_this_repo_ships_it_off(self):
        loaded, problems = factory_config.load(REPO)
        self.assertEqual(problems, [])
        self.assertEqual(factory_config.resolve_standing_consent(loaded),
                         (OFF, []))


class TestConsentRow(unittest.TestCase):
    def test_a_standing_consent_row_is_ledger_grammar(self):
        self.assertEqual(conductor.row_problems(ROW), [])

    def test_its_policy_reason_and_item_are_checked(self):
        self.assertEqual(conductor.row_problems(dict(ROW, policy="owner")),
                         ["consent policy 'owner' is not standing"])
        self.assertEqual(conductor.row_problems(dict(ROW, reason=" ")),
                         ["reason must be a non-empty string"])
        self.assertEqual(conductor.row_problems(dict(ROW, item=None)),
                         ["a consent row names its item"])


class TestStandingProblems(unittest.TestCase):
    def test_an_off_policy_covers_nothing(self):
        self.assertEqual(consent.standing_problems("#12", {}, None, OFF),
                         ["standing consent is off in factory.json"])

    def test_a_gate_path_item_always_needs_the_owner(self):
        self.assertEqual(
            consent.standing_problems("#12", {ADR: "b1"}, None, ON),
            [f"#12 changes gate-path file(s) {ADR}; standing consent never"
             " covers a gate-path item"])

    def test_a_tier_allowlist_needs_one_of_its_labels(self):
        self.assertEqual(
            consent.standing_problems("#12", {}, ["type:feature"], TIERED),
            ["#12's issue carries none of the tier labels tier:low,"
             " tier:docs"])
        self.assertEqual(consent.standing_problems(
            "#12", {}, ["tier:docs"], TIERED), [])

    def test_a_clean_item_under_an_open_policy_is_covered(self):
        self.assertEqual(consent.standing_problems("#12", {}, None, ON), [])


def branch_git(changed=""):
    """A git port answering the item branch's diff (and ls-tree for
    any gate path in it)."""
    def run(args):
        if args[0] == "diff":
            return subprocess.CompletedProcess(args, 0, stdout=changed)
        if args[0] == "ls-tree":
            tree = "".join(f"100644 blob b1\t{path}\n"
                           for path in changed.split())
            return subprocess.CompletedProcess(args, 0, stdout=tree)
        raise AssertionError(args)
    return run


def issue_gh(labels):
    return FakeGh(answers={("issue", "view"): json.dumps(
        {"labels": [{"name": name} for name in labels]})})


class TestNextRecordsStandingConsent(unittest.TestCase):
    def advance(self, rows, policy, changed="src.txt\n", gh=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / LEDGER
            path.parent.mkdir(parents=True)
            path.write_text("".join(json.dumps(r) + "\n" for r in rows))
            self.gh = gh or issue_gh([])
            result, problems = flow.advance(
                tmp, "b1", NOW, 3, alive, branch_git(changed), gh=self.gh,
                policy=policy)
            self.rows, _ = conductor.load(tmp, "b1")
            return result, problems

    def test_a_covered_item_gets_a_consent_row_and_a_merge_step(self):
        result, problems = self.advance(START + SHIPPED, ON)
        self.assertEqual(problems, [])
        self.assertEqual(self.rows[-1], {
            "at": "2026-10-10T12:30:00Z", "kind": "consent", "item": "#12",
            "policy": "standing",
            "reason": "standing consent (ADR-0086): no gate-path file"
                      " changed"})
        self.assertIn({"item": "#12", "step": "merge"}, result["ready"])
        self.assertEqual(result["merge_due"], [])
        self.assertEqual(self.gh.calls, [])

    def test_the_policy_off_leaves_the_merge_to_the_owner(self):
        result, _ = self.advance(START + SHIPPED, OFF)
        self.assertEqual(result["merge_due"], ["#12"])
        self.assertFalse([r for r in self.rows if r["kind"] == "consent"])

    def test_a_gate_path_item_stays_merge_due(self):
        result, _ = self.advance(START + SHIPPED, ON, changed=f"{ADR}\n")
        self.assertEqual(result["merge_due"], ["#12"])
        self.assertNotIn({"item": "#12", "step": "merge"}, result["ready"])
        self.assertFalse([r for r in self.rows if r["kind"] == "consent"])

    def test_a_tier_label_is_read_from_the_issue(self):
        result, _ = self.advance(START + SHIPPED, TIERED,
                                 gh=issue_gh(["tier:low"]))
        self.assertEqual(self.rows[-1]["reason"],
                         "standing consent (ADR-0086): no gate-path file"
                         " changed; tier label tier:low")
        self.assertEqual(self.gh.called("issue", "view"), [[
            "issue", "view", "12", "--json", "labels"]])
        result, _ = self.advance(START + SHIPPED, TIERED,
                                 gh=issue_gh(["type:feature"]))
        self.assertEqual(result["merge_due"], ["#12"])

    def test_an_owner_merge_ask_already_covering_it_wins(self):
        one_by_one = tcm.train("ask-2", ["#12", "#14"], "one-by-one")
        result, _ = self.advance(START + SHIPPED + one_by_one, ON)
        self.assertEqual(result["merge_due"], ["#12"])
        self.assertFalse([r for r in self.rows if r["kind"] == "consent"])

    def test_a_failed_label_read_is_a_problem(self):
        gh = FakeGh(answers={}, failing=["issue"],
                    error=subprocess.CalledProcessError(1, "gh",
                                                        stderr="HTTP 502"))
        result, problems = self.advance(START + SHIPPED, TIERED, gh=gh)
        self.assertIsNone(result)
        self.assertEqual(problems, ["cd: gh issue view #12 failed: HTTP 502"])


class TestMergeUnderStandingConsent(unittest.TestCase):
    def problems(self, rows, blobs=None, policy=ON):
        return merge.merge_problems(START + rows, "#12", blobs or {},
                                    policy=policy)

    def test_a_consent_row_covers_the_merge(self):
        self.assertEqual(self.problems(SHIPPED + [ROW]), [])

    def test_a_policy_turned_off_since_refuses_it(self):
        self.assertEqual(self.problems(SHIPPED + [ROW], policy=OFF), [
            "cd: merge refused: standing consent is off in factory.json"])
        self.assertEqual(merge.merge_problems(START + SHIPPED + [ROW], "#12",
                                              {}),
                         ["cd: merge refused: standing consent is off in"
                          " factory.json"])

    def test_a_gate_file_since_refuses_it(self):
        self.assertEqual(self.problems(SHIPPED + [ROW], {ADR: "b1"}), [
            f"cd: merge refused: #12 changes gate-path file(s) {ADR};"
            " standing consent never covers a gate-path item"])

    def test_the_reviewed_pass_is_still_required(self):
        unreviewed = [row for row in SHIPPED if row.get("to") != "reviewed"]
        self.assertEqual(self.problems(unreviewed + [ROW]), [
            "cd: merge refused: #12 has no reviewed pass"])


class TestCover(unittest.TestCase):
    """One reading of what covers an item's merge (issue #734), which
    `next` and the merge precondition both consult: covered (ready to
    merge), waiting (behind an unmerged train item) or owed (the Owner
    owes a merge answer)."""

    def cover(self, rows, blobs=None, policy=OFF):
        return consent.cover(START + rows, "#12", blobs or {}, policy)

    def test_a_consent_row_under_a_policy_turned_off_is_owed(self):
        self.assertEqual(self.cover(SHIPPED + [ROW]), (
            "owed", ["standing consent is off in factory.json"]))
        self.assertEqual(self.cover(SHIPPED + [ROW], policy=ON),
                         ("covered", []))

    def test_a_train_answer_over_an_unapproved_blob_is_owed(self):
        rows = tcm.feature_shipped({ADR: "aaa"}) + tcm.train("ask-2",
                                                             ["#12"])
        self.assertEqual(self.cover(rows, {ADR: "ccc"}), (
            "owed", [f"#12's gate file {ADR} is not the one approved at"
                     " its gate ask; it needs its own merge ask"]))
        self.assertEqual(self.cover(rows, {ADR: "aaa"}), ("covered", []))

    def test_a_train_behind_an_unmerged_item_is_waiting(self):
        rows = SHIPPED + tcm.train("ask-2", ["#13", "#12"])
        self.assertEqual(self.cover(rows), (
            "waiting", ["#12 rides train ask-2 behind #13, which is"
                        " planned, not merged"]))

    def test_its_own_answer_beats_a_lapsed_standing_consent(self):
        rows = SHIPPED + [ROW] + tcm.own("ask-2", "#12")
        self.assertEqual(self.cover(rows), ("covered", []))

    def test_nothing_covering_it_is_owed(self):
        self.assertEqual(self.cover(SHIPPED),
                         ("owed", ["no merge answer covers #12"]))


class TestNextAgreesWithMerge(unittest.TestCase):
    """The defect #734 named: `next` reported an item ready that the
    merge precondition refused on every turn, and never offered the
    merge ask the Owner then owed (ADR-0086)."""

    advance = TestNextRecordsStandingConsent.advance

    def test_a_lapsed_standing_consent_is_due_not_ready(self):
        result, problems = self.advance(START + SHIPPED + [ROW], OFF)
        self.assertEqual(problems, [])
        self.assertNotIn({"item": "#12", "step": "merge"}, result["ready"])
        self.assertEqual(result["merge_due"], ["#12"])
        self.assertEqual(merge.merge_problems(self.rows, "#12", {}, OFF), [
            "cd: merge refused: standing consent is off in factory.json"])

    def test_a_train_over_a_changed_gate_blob_is_due_not_ready(self):
        rows = (START + tcm.feature_shipped({ADR: "aaa"})
                + tcm.train("ask-2", ["#12"]))
        result, problems = self.advance(rows, OFF, changed=f"{ADR}\n")
        self.assertEqual(problems, [])
        self.assertNotIn({"item": "#12", "step": "merge"}, result["ready"])
        self.assertEqual(result["merge_due"], ["#12"])

    def test_a_train_behind_an_unmerged_item_is_neither(self):
        rows = START + SHIPPED + tcm.train("ask-2", ["#13", "#12"])
        result, _ = self.advance(rows, ON)
        self.assertNotIn({"item": "#12", "step": "merge"}, result["ready"])
        self.assertEqual(result["merge_due"], [])

    def test_a_pending_own_ask_is_not_due(self):
        rows = START + SHIPPED + [ROW] + tcm.own("ask-2", "#12")[:1]
        result, _ = self.advance(rows, OFF)
        self.assertEqual(result["merge_due"], [])

    def test_its_own_answer_beats_a_lapsed_standing_consent(self):
        rows = START + SHIPPED + [ROW] + tcm.own("ask-2", "#12")
        result, _ = self.advance(rows, OFF)
        self.assertIn({"item": "#12", "step": "merge"}, result["ready"])
        self.assertEqual(result["merge_due"], [])


class TestStandingMergeTurn(tcm.TurnCase):
    def merge(self, policy):
        self.ledger(tcm.START + self.filled(SHIPPED) + [ROW])
        return merge.merge_turn(
            self.root, "b1", "#12", self.clock, self.git, self.fake_gh(),
            self.tool(), self.clock.sleep, pid=555, config=config(policy))

    def test_a_consented_item_merges_after_green_checks(self):
        self.item({"src.txt": "x\n"})
        summary, problems = self.merge(ON)
        self.assertEqual((problems, summary["stall"], summary["sha"]),
                         ([], None, "m1"))
        self.rows, _ = conductor.load(self.root, "b1")
        self.assertEqual(self.rows[-1]["to"], "merged")

    def test_a_gate_path_item_is_refused_before_anything_runs(self):
        self.item({ADR: "# ADR\n"})
        summary, problems = self.merge(ON)
        self.assertIsNone(summary)
        self.assertEqual(problems, [
            f"cd: merge refused: #12 changes gate-path file(s) {ADR};"
            " standing consent never covers a gate-path item"])
        self.assertFalse(self.calls("git", "fetch"))


class TestScorecard(unittest.TestCase):
    def test_a_standing_merge_is_no_owner_touch(self):
        rows = START + SHIPPED + [ROW, tcm.moved(
            "#12", "ship", "merging"), tcm.moved(
            "#12", "merging", "merged", pr=1, sha="s", checks={})]
        spend = [{"run_id": row["run_id"], "cost": 1.0} for row in rows
                 if row["kind"] == "run"]
        card, problems = close.compute(rows, list(range(1, len(rows) + 1)),
                                       LEDGER, spend, NOW)
        self.assertEqual(problems, [])
        # The spend approval and the gate approval: two Owner answers,
        # and the standing consent is not one of them.
        self.assertEqual(card["owner_touches_per_merged"], 2.0)
        self.assertEqual(card["merged"], 1)


class TestNextCli(unittest.TestCase):
    def run_cli(self, env):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / LEDGER
            path.parent.mkdir(parents=True)
            path.write_text("".join(json.dumps(r) + "\n"
                                    for r in START + SHIPPED))
            Path(tmp, ".github").mkdir()
            Path(tmp, ".github/factory.json").write_text(json.dumps(
                dict(config(ON), wip_cap=2)))
            code, out = cli_contract.capture(
                conductor.main, ["next", "b1"], env=env, clock=clock,
                root=tmp, git=branch_git("src.txt\n"), alive=alive,
                run=issue_gh([]))
            rows, _ = conductor.load(tmp, "b1")
        return code, out, rows

    def test_next_reads_the_policy_from_factory_json(self):
        code, out, rows = self.run_cli({})
        self.assertEqual(code, 0, out)
        self.assertEqual(rows[-1]["kind"], "consent")

    def test_a_worker_never_runs_next(self):
        # `next` now writes consent, so ADR-0085's guard on `answer`
        # covers it too: it stops a confused Worker.
        code, out, rows = self.run_cli({"CONDUCTOR_WORKER": "b1"})
        self.assertEqual((code, out), (1, (
            "cd: next refused: CONDUCTOR_WORKER is set, and a Worker never"
            " advances a batch\ncd: 1 problem(s)\n")))
        self.assertEqual(rows, START + SHIPPED)


if __name__ == "__main__":
    unittest.main()
