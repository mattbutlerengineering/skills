"""gate_digest.py (WO-0017, ADR-0041) — the daily gate-queue digest and
gate-latency capture.

Same discipline as test_validator: the gh CLI is injected (a recording
fake, never the network), the clock is injected, and tests assert the
exact problem strings and ledger rows through the public interface. The
pure parts — timeline parsing, passage detection, digest composition —
are exercised directly; run_daily composes them against the fakes.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import cost_ledger
import gate_digest

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling fixture_tree import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture_tree import FixtureTree  # noqa: E402

BREAKDOWN = (
    "# Breakdown\n"
    "\n"
    "- [ ] **WO-0018** rejection mining — size:S, blocked by: —"
    " (PRD-0001 §User stories) (tracker: #123)\n"
    "- [x] **WO-0010** sweeps — size:S, blocked by: —"
    " (PRD-0001 §Solution) (tracker: #131)\n"
    "- [ ] **WO-0007** unmirrored row (PRD-0001 §Solution)\n"
)


def clock():
    return datetime(2026, 7, 22, 9, 0, tzinfo=timezone.utc)


def issue(number, title, state="OPEN", labels=(), body=""):
    return {"number": number, "title": title, "state": state,
            "labels": [{"name": name} for name in labels], "body": body}


class DigestRunner:
    """Injected gh runner: answers `issue list` with a canned issue set,
    `api .../timeline` with per-issue canned timelines (in --slurp's
    array-of-pages shape), `issue create` with a new issue's URL, and
    records every call."""

    def __init__(self, issues=(), timelines=None,
                 create_url="https://github.com/o/r/issues/50"):
        self.issues = list(issues)
        self.timelines = timelines or {}
        self.create_url = create_url
        self.calls = []

    def __call__(self, args):
        call = list(args)
        self.calls.append(call)
        if call[:2] == ["issue", "list"]:
            return json.dumps(self.issues)
        if call[0] == "api":
            number = int(call[1].split("/")[-2])
            return json.dumps([self.timelines.get(number, [])])
        if call[:2] == ["issue", "create"]:
            return self.create_url + "\n"
        return ""

    def called(self, *prefix):
        return [c for c in self.calls if c[:len(prefix)] == list(prefix)]


class FailingRunner(DigestRunner):
    def __init__(self, failing, **kwargs):
        super().__init__(**kwargs)
        self.failing = list(failing)

    def __call__(self, args):
        result = super().__call__(args)
        if list(args[:len(self.failing)]) == self.failing:
            raise subprocess.CalledProcessError(1, "gh", stderr="boom\n")
        return result


def tree(tmp):
    fixture = FixtureTree(tmp)
    fixture.write("docs/features/demo/breakdown.md", BREAKDOWN)
    return fixture


def labeled(ts, name):
    return {"event": "labeled", "label": {"name": name}, "created_at": ts}


def unlabeled(ts, name):
    return {"event": "unlabeled", "label": {"name": name}, "created_at": ts}


class TestLabelEvents(unittest.TestCase):
    def test_keeps_only_label_flips_in_timeline_order(self):
        timeline = [
            {"event": "commented", "created_at": "2026-07-01T09:00:00Z"},
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            {"event": "labeled", "label": {}},
            unlabeled("2026-07-02T09:00:00Z", "wo:draft"),
        ]
        self.assertEqual(gate_digest.label_events(timeline), [
            ("2026-07-01T09:00:00Z", "labeled", "wo:draft"),
            ("2026-07-02T09:00:00Z", "unlabeled", "wo:draft"),
        ])


class TestGatePassages(unittest.TestCase):
    def test_a_confirmed_flip_is_a_passage(self):
        events = gate_digest.label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            labeled("2026-07-02T09:00:00Z", "wo:prd-approved"),
            unlabeled("2026-07-02T09:00:00Z", "wo:draft"),
        ])
        self.assertEqual(gate_digest.gate_passages(events),
                         [("prd", 86400, "2026-07-02T09:00:00Z")])

    def test_a_flip_to_anything_but_the_pass_label_is_not_a_passage(self):
        # wo:draft -> wo:blocked is a rejection, not a PRD-gate pass.
        events = gate_digest.label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            unlabeled("2026-07-03T09:00:00Z", "wo:draft"),
            labeled("2026-07-03T09:00:00Z", "wo:blocked"),
        ])
        self.assertEqual(gate_digest.gate_passages(events), [])

    def test_a_rejected_stay_is_not_confirmed_by_a_later_pass(self):
        # First stay ends in wo:blocked (rejection); the gate is re-entered
        # and passed later. Only the second stay is a passage — the later
        # confirmation must not reach back past the re-entry.
        events = gate_digest.label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            unlabeled("2026-07-02T09:00:00Z", "wo:draft"),
            labeled("2026-07-02T09:00:00Z", "wo:blocked"),
            labeled("2026-07-05T09:00:00Z", "wo:draft"),
            labeled("2026-07-06T09:00:00Z", "wo:prd-approved"),
            unlabeled("2026-07-06T09:00:00Z", "wo:draft"),
        ])
        self.assertEqual(gate_digest.gate_passages(events),
                         [("prd", 86400, "2026-07-06T09:00:00Z")])

    def test_a_re_entered_gate_yields_one_passage_per_pair(self):
        events = gate_digest.label_events([
            labeled("2026-07-01T09:00:00Z", "wo:needs-review"),
            unlabeled("2026-07-01T10:00:00Z", "wo:needs-review"),
            labeled("2026-07-01T10:00:00Z", "wo:merged"),
            labeled("2026-07-05T09:00:00Z", "wo:needs-review"),
            unlabeled("2026-07-05T11:00:00Z", "wo:needs-review"),
            labeled("2026-07-05T11:00:00Z", "wo:merged"),
        ])
        self.assertEqual(gate_digest.gate_passages(events), [
            ("merge", 3600, "2026-07-01T10:00:00Z"),
            ("merge", 7200, "2026-07-05T11:00:00Z"),
        ])


class TestWaitingSince(unittest.TestCase):
    def test_a_still_applied_queue_label_reports_its_timestamp(self):
        events = gate_digest.label_events([
            labeled("2026-07-20T09:00:00Z", "wo:draft"),
        ])
        self.assertEqual(
            gate_digest.waiting_since(events, "wo:draft"),
            "2026-07-20T09:00:00Z")

    def test_a_removed_or_never_applied_label_is_none(self):
        events = gate_digest.label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            unlabeled("2026-07-02T09:00:00Z", "wo:draft"),
        ])
        self.assertIsNone(gate_digest.waiting_since(events, "wo:draft"))
        self.assertIsNone(gate_digest.waiting_since([], "wo:draft"))


class TestComposeDigest(unittest.TestCase):
    def test_the_body_leads_with_the_marker_and_lists_every_gate(self):
        queues = [
            ("PRD gate", "wo:draft",
             [(123, "WO-0018 rejection mining", 266400)]),
            ("Blueprint gate", "wo:prd-approved", []),
            ("Merge gate", "wo:needs-review",
             [(131, "WO-0010 sweeps", 1800)]),
        ]
        body = gate_digest.compose_digest(queues, "2026-07-22")
        self.assertEqual(body.splitlines()[0], gate_digest.DIGEST_MARKER)
        self.assertIn("# Factory gate queue — 2026-07-22", body)
        self.assertIn("## PRD gate (wo:draft)", body)
        self.assertIn("- #123 WO-0018 rejection mining — waiting 3d 2h",
                      body)
        self.assertIn("## Blueprint gate (wo:prd-approved)", body)
        self.assertIn("- (empty)", body)
        self.assertIn("- #131 WO-0010 sweeps — waiting <1h", body)

    def test_an_item_with_no_known_age_is_still_listed(self):
        queues = [("PRD gate", "wo:draft", [(7, "WO-0001 a title", None)])]
        body = gate_digest.compose_digest(queues, "2026-07-22")
        self.assertIn("- #7 WO-0001 a title\n", body)


class TestMirrorMap(unittest.TestCase):
    def test_maps_tracker_numbers_to_work_orders(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(gate_digest.mirror_map(tree(tmp).root),
                             {123: "WO-0018", 131: "WO-0010"})


class TestRunDaily(unittest.TestCase):
    def test_first_run_creates_and_pins_the_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = DigestRunner(
                issues=[issue(123, "WO-0018 rejection mining",
                              labels=["wo:draft", "size:S"])],
                timelines={123: [labeled("2026-07-20T09:00:00Z",
                                         "wo:draft")]})
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, [])
            self.assertEqual(outputs["changed"], "false")
            (create,) = run.called("issue", "create")
            body = create[create.index("--body") + 1]
            self.assertEqual(body.splitlines()[0], gate_digest.DIGEST_MARKER)
            self.assertIn("- #123 WO-0018 rejection mining — waiting 2d 0h",
                          body)
            self.assertIn("## Blueprint gate (wo:prd-approved)\n- (empty)",
                          body)
            self.assertEqual(run.called("issue", "pin"),
                             [["issue", "pin", "50"]])

    def test_a_later_run_edits_the_marker_issue_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = DigestRunner(issues=[
                issue(50, "Factory gate queue",
                      body=gate_digest.DIGEST_MARKER + "\nold"),
            ])
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "create"), [])
            (edit,) = run.called("issue", "edit")
            self.assertEqual(edit[2], "50")
            # the edit path re-pins (a human unpin heals the next day)
            self.assertEqual(run.called("issue", "pin"),
                             [["issue", "pin", "50"]])

    def test_a_confirmed_passage_lands_a_deduped_ledger_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = tree(tmp)
            timelines = {131: [
                labeled("2026-07-01T09:00:00Z", "wo:needs-review"),
                unlabeled("2026-07-01T10:00:00Z", "wo:needs-review"),
                labeled("2026-07-01T10:00:00Z", "wo:merged"),
            ]}
            issues = [issue(131, "WO-0010 sweeps", state="CLOSED",
                            labels=["wo:merged"])]
            run = DigestRunner(issues=issues, timelines=timelines)
            outputs, problems = gate_digest.run_daily(
                fixture.root, run=run, clock=clock)
            self.assertEqual(problems, [])
            self.assertEqual(outputs["changed"], "true")
            entries, ledger_problems = cost_ledger.read(fixture.root)
            self.assertEqual(ledger_problems, [])
            self.assertEqual(entries, [cost_ledger.gate_entry(
                "WO-0010", "merge", 3600, "2026-07-01T10:00:00Z")])
            # the daily re-scan sees the same passage and records nothing
            rerun = DigestRunner(issues=issues, timelines=timelines)
            outputs, problems = gate_digest.run_daily(
                fixture.root, run=rerun, clock=clock)
            self.assertEqual(problems, [])
            self.assertEqual(outputs["changed"], "false")
            entries, _ = cost_ledger.read(fixture.root)
            self.assertEqual(len(entries), 1)

    def test_a_closed_issue_is_never_a_queue_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = DigestRunner(issues=[
                issue(123, "WO-0018 rejection mining", state="CLOSED",
                      labels=["wo:draft"])])
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, [])
            (create,) = run.called("issue", "create")
            body = create[create.index("--body") + 1]
            self.assertNotIn("#123", body)

    def test_the_default_clock_needs_no_injection(self):
        # Every other test injects clock; the workflow runs without one —
        # this is the path a missing import would hide on.
        with tempfile.TemporaryDirectory() as tmp:
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=DigestRunner())
            self.assertEqual(problems, [])

    def test_the_edit_path_re_pins_and_tolerates_the_usual_refusal(self):
        # Re-pinning a pinned issue fails; that steady-state refusal is
        # not a problem. What the retry buys: a human unpin heals on the
        # next daily run instead of rotting unpinned forever.
        with tempfile.TemporaryDirectory() as tmp:
            run = FailingRunner(["issue", "pin"], issues=[
                issue(50, "Factory gate queue",
                      body=gate_digest.DIGEST_MARKER + "\nold")])
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "pin"),
                             [["issue", "pin", "50"]])

    def test_a_failing_create_or_edit_or_pin_reports_the_exact_string(self):
        digest = issue(50, "Factory gate queue",
                       body=gate_digest.DIGEST_MARKER + "\nold")
        cases = [
            (["issue", "create"], [], "gd: gh issue create failed: boom"),
            (["issue", "edit"], [digest],
             "gd: gh issue edit 50 failed: boom"),
        ]
        for failing, issues, problem in cases:
            with self.subTest(failing=failing):
                with tempfile.TemporaryDirectory() as tmp:
                    run = FailingRunner(failing, issues=issues)
                    outputs, problems = gate_digest.run_daily(
                        tree(tmp).root, run=run, clock=clock)
                    self.assertEqual(problems, [problem])
        # a create-path pin failure IS reported: nothing retries it later
        with tempfile.TemporaryDirectory() as tmp:
            run = FailingRunner(["issue", "pin"])
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, ["gd: gh issue pin failed: boom"])

    def test_ledger_problems_pass_through_with_their_own_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = tree(tmp)
            fixture.write("docs/factory/costs.jsonl", '{"wo": "WO-0010"}\n')
            outputs, problems = gate_digest.run_daily(
                fixture.root, run=DigestRunner(), clock=clock)
            self.assertEqual(problems, [
                "ledger: docs/factory/costs.jsonl:1 ledger line is missing"
                " field(s): cost, model, outcome, run_id, tokens"])

    def test_a_failing_issue_list_reports_and_posts_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = FailingRunner(["issue", "list"])
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, ["gd: gh issue list failed: boom"])
            self.assertEqual(outputs["changed"], "false")
            self.assertEqual(run.called("issue", "create"), [])

    def test_a_failing_timeline_still_posts_the_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = FailingRunner(
                ["api"],
                issues=[issue(123, "WO-0018 rejection mining",
                              labels=["wo:draft"])])
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, ["gd: gh api timeline for #123"
                                        " failed: boom"])
            (create,) = run.called("issue", "create")
            body = create[create.index("--body") + 1]
            self.assertIn("- #123 WO-0018 rejection mining\n", body)


class TestMain(unittest.TestCase):
    def test_daily_writes_changed_to_github_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.txt"
            run = DigestRunner()
            code = gate_digest.main(
                ["daily"], env={"GITHUB_OUTPUT": str(out)},
                root=tree(tmp).root, run=run, clock=clock)
            self.assertEqual(code, 0)
            self.assertIn("changed=false",
                          out.read_text(encoding="utf-8"))

    def test_anything_else_prints_usage(self):
        self.assertEqual(gate_digest.main(["nonsense"], env={}), 2)


if __name__ == "__main__":
    unittest.main()
