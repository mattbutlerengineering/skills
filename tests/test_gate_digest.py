"""gate_digest.py (WO-0017, ADR-0041) — the daily gate-queue digest and
gate-latency capture.

Same discipline as test_validator: the gh CLI is injected (a recording
fake, never the network), the clock is injected, and tests assert the
exact problem strings and ledger rows through the public interface. The
pure part this tool still owns — digest composition — is exercised
directly; run_daily composes it against the fakes.

The gate vocabulary and the stay walk are human_gates.py's (ADR-0056),
so timeline parsing, passage detection and waiting_since are covered in
tests/test_human_gates.py — one frame further out, where the miner's
half of the same partition is covered too. The mirror map is the
knowledge plane's (ADR-0039), covered in tests/test_knowledge_plane.py.
"""
import json
import re
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
import cli_contract  # noqa: E402
from fake_gh import FakeGh  # noqa: E402
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


def gh(issues=(), timelines=None,
       create_url="https://github.com/o/r/issues/50", **kwargs):
    """A fake gh for the digest's traffic: `issue list` answers with a
    canned issue set, `api .../timeline` with per-issue canned timelines
    (in --slurp's array-of-pages shape), `issue create` with the new
    issue's URL. Failure is declared via FakeGh's failing= (the shared
    default error carries stderr "boom\\n")."""
    canned = timelines or {}

    def timeline(args):
        number = int(args[1].split("/")[-2])
        return json.dumps([canned.get(number, [])])

    return FakeGh(answers={
        ("issue", "list"): json.dumps(list(issues)),
        ("api",): timeline,
        ("issue", "create"): create_url + "\n",
    }, **kwargs)


def item(number, title, waited, aged=True):
    """A queue item as _queues emits it. `aged` defaults True because an
    unreadable history is the exceptional case, and a fixture that has to
    opt IN to the failure reads the way the digest does."""
    return gate_digest.Item(number, title, waited, aged)


def tree(tmp):
    fixture = FixtureTree(tmp)
    fixture.write("docs/features/demo/breakdown.md", BREAKDOWN)
    return fixture


def labeled(ts, name):
    return {"event": "labeled", "label": {"name": name}, "created_at": ts}


def unlabeled(ts, name):
    return {"event": "unlabeled", "label": {"name": name}, "created_at": ts}


class TestComposeDigest(unittest.TestCase):
    def test_the_body_leads_with_the_marker_and_lists_every_gate(self):
        queues = [
            ("PRD gate", "wo:draft",
             [item(123, "WO-0018 rejection mining", 266400)]),
            ("Blueprint gate", "wo:prd-approved", []),
            ("Merge gate", "wo:needs-review",
             [item(131, "WO-0010 sweeps", 1800)]),
        ]
        body = gate_digest.compose_digest(queues, "2026-07-22", False)
        self.assertEqual(body.splitlines()[0], gate_digest.DIGEST_MARKER)
        self.assertIn("# Factory gate queue — 2026-07-22", body)
        self.assertIn("## PRD gate (wo:draft)", body)
        self.assertIn("- #123 WO-0018 rejection mining — waiting 3d 2h",
                      body)
        self.assertIn("## Blueprint gate (wo:prd-approved)", body)
        self.assertIn("- (empty)", body)
        self.assertIn("- #131 WO-0010 sweeps — waiting <1h", body)

    def test_an_item_with_no_known_age_is_still_listed(self):
        queues = [("PRD gate", "wo:draft",
                   [item(7, "WO-0001 a title", None)])]
        body = gate_digest.compose_digest(queues, "2026-07-22", False)
        self.assertIn("- #7 WO-0001 a title\n", body)

    def test_an_unaged_item_says_why_when_its_history_was_unreadable(self):
        """The two states the defect brief measured as one line. `aged`
        is read, never inferred from `waited` — an item whose history was
        read and simply held no arrival is not a failure and must not
        wear a failure's mark."""
        readable = gate_digest.compose_digest(
            [("PRD gate", "wo:draft", [item(7, "WO-0001 a title", None)])],
            "2026-07-22", False)
        unreadable = gate_digest.compose_digest(
            [("PRD gate", "wo:draft",
              [item(7, "WO-0001 a title", None, aged=False)])],
            "2026-07-22", False)
        self.assertIn("- #7 WO-0001 a title\n", readable)
        self.assertIn("- #7 WO-0001 a title — age unknown"
                      " (timeline unreadable)\n", unreadable)
        self.assertNotEqual(readable, unreadable)

    def test_an_aged_item_never_wears_the_mark(self):
        """Precedence, not a guard: a known age wins over an unread
        history. _queues cannot currently produce this combination (no
        timeline means no arrival means no age), so this pins which fact
        the renderer prefers if a later change ever derives an age some
        other way — it does not stand in for a reachable bug."""
        body = gate_digest.compose_digest(
            [("PRD gate", "wo:draft", [item(7, "t", 1800, aged=False)])],
            "2026-07-22", False)
        self.assertIn("- #7 t — waiting <1h\n", body)
        self.assertNotIn("unreadable", body)

    def test_a_truncated_listing_is_stated_in_the_footer(self):
        queues = [("PRD gate", "wo:draft", [])]
        complete = gate_digest.compose_digest(queues, "2026-07-22", False)
        partial = gate_digest.compose_digest(queues, "2026-07-22", True)
        self.assertNotEqual(complete, partial)
        self.assertIn(gate_digest.TRUNCATED_NOTE, partial)
        self.assertNotIn(gate_digest.TRUNCATED_NOTE, complete)
        # under the sections it qualifies, above the standing footer —
        # a caveat printed after the provenance line reads as a footnote
        # about the tool rather than about the queue above it
        paragraphs = partial.strip().split("\n\n")
        self.assertEqual(paragraphs[-2], gate_digest.TRUNCATED_NOTE)
        self.assertIn("Updated daily by the gate digest", paragraphs[-1])

    def test_the_coverage_fact_has_no_default(self):
        """A default would let a caller omit the fact silently, which is
        the defect this contract exists to prevent."""
        with self.assertRaises(TypeError):
            gate_digest.compose_digest([], "2026-07-22")


class TestRunDaily(unittest.TestCase):
    def test_first_run_creates_and_pins_the_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(
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
            run = gh(issues=[
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
            run = gh(issues=issues, timelines=timelines)
            outputs, problems = gate_digest.run_daily(
                fixture.root, run=run, clock=clock)
            self.assertEqual(problems, [])
            self.assertEqual(outputs["changed"], "true")
            entries, ledger_problems = cost_ledger.read(fixture.root)
            self.assertEqual(ledger_problems, [])
            self.assertEqual(entries, [cost_ledger.gate_entry(
                "WO-0010", "merge", 3600, "2026-07-01T10:00:00Z")])
            # the captured row is stamped with the passage date — the
            # monthly circuit breaker windows on it
            self.assertEqual(entries[0]["at"], "2026-07-01")
            # the daily re-scan sees the same passage and records nothing
            rerun = gh(issues=issues, timelines=timelines)
            outputs, problems = gate_digest.run_daily(
                fixture.root, run=rerun, clock=clock)
            self.assertEqual(problems, [])
            self.assertEqual(outputs["changed"], "false")
            entries, _ = cost_ledger.read(fixture.root)
            self.assertEqual(len(entries), 1)

    def test_a_closed_issue_is_never_a_queue_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(issues=[
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
                tree(tmp).root, run=gh())
            self.assertEqual(problems, [])

    def test_the_edit_path_re_pins_and_tolerates_the_usual_refusal(self):
        # Re-pinning a pinned issue fails; that steady-state refusal is
        # not a problem. What the retry buys: a human unpin heals on the
        # next daily run instead of rotting unpinned forever.
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(failing=["issue", "pin"], issues=[
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
                    run = gh(failing=failing, issues=issues)
                    outputs, problems = gate_digest.run_daily(
                        tree(tmp).root, run=run, clock=clock)
                    self.assertEqual(problems, [problem])
        # a create-path pin failure IS reported: nothing retries it later
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(failing=["issue", "pin"])
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, ["gd: gh issue pin failed: boom"])

    def test_ledger_problems_pass_through_with_their_own_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = tree(tmp)
            fixture.write("docs/factory/costs.jsonl", '{"wo": "WO-0010"}\n')
            outputs, problems = gate_digest.run_daily(
                fixture.root, run=gh(), clock=clock)
            self.assertEqual(problems, [
                "ledger: docs/factory/costs.jsonl:1 ledger line is missing"
                " field(s): cost, model, outcome, run_id, tokens"])

    def test_a_failing_issue_list_reports_and_posts_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(failing=["issue", "list"])
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, ["gd: gh issue list failed: boom"])
            self.assertEqual(outputs["changed"], "false")
            self.assertEqual(run.called("issue", "create"), [])

    def test_an_unparseable_issue_list_reports_and_posts_nothing(self):
        # gh ran, exited 0, answered `issue list` with raw non-JSON.
        with tempfile.TemporaryDirectory() as tmp:
            run = FakeGh(answers={("issue", "list"): "gh: banner text"})
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, [
                "gd: gh issue list returned unparseable JSON: Expecting"
                " value: line 1 column 1 (char 0)"])
            self.assertEqual(outputs["changed"], "false")
            self.assertEqual(run.called("issue", "create"), [])

    def test_a_non_list_issue_listing_reports_and_posts_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = FakeGh(answers={("issue", "list"): "{}"})
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, [
                "gd: gh issue list returned dict where list was expected"])
            self.assertEqual(outputs["changed"], "false")
            self.assertEqual(run.called("issue", "create"), [])

    def test_a_full_issue_window_is_reported_and_the_digest_still_posts(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(issues=[
                issue(10_000 + n, f"noise {n}", state="CLOSED")
                for n in range(gate_digest.LIST_WINDOW)])
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, [
                "gd: gh issue list returned a full"
                f" {gate_digest.LIST_WINDOW}-entry window — older entries"
                " are invisible; raise the window or narrow the query"])
            self.assertEqual(len(run.called("issue", "create")), 1)

    def test_an_unparseable_timeline_still_posts_the_digest(self):
        # The same traffic gh() cans, but the timeline endpoint answers
        # raw non-JSON.
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(issues=[issue(123, "WO-0018 rejection mining",
                                   labels=["wo:draft"])])
            run.answers[("api",)] = "not json"
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, [
                "gd: gh api timeline for #123 returned unparseable"
                " JSON: Expecting value: line 1 column 1 (char 0)"])
            (create,) = run.called("issue", "create")
            body = create[create.index("--body") + 1]
            self.assertIn("- #123 WO-0018 rejection mining — age"
                          " unknown (timeline unreadable)\n", body)

    def test_a_failing_timeline_still_posts_the_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(
                failing=["api"],
                issues=[issue(123, "WO-0018 rejection mining",
                              labels=["wo:draft"])])
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, ["gd: gh api timeline for #123"
                                        " failed: boom"])
            (create,) = run.called("issue", "create")
            body = create[create.index("--body") + 1]
            self.assertIn("- #123 WO-0018 rejection mining — age"
                          " unknown (timeline unreadable)\n", body)

    def _body(self, run, tmp):
        gate_digest.run_daily(tree(tmp).root, run=run, clock=clock)
        (create,) = run.called("issue", "create")
        return create[create.index("--body") + 1]

    def test_an_unreadable_timeline_is_marked_in_the_posted_body(self):
        """The defect brief's second reproduction, as a regression: the
        two causes of a missing age rendered the same line."""
        waiting = [issue(123, "WO-0018 rejection mining",
                         labels=["wo:prd-approved"])]
        with tempfile.TemporaryDirectory() as tmp:
            readable = self._body(gh(issues=waiting, timelines={123: []}),
                                  tmp)
            broken = gh(issues=waiting)
            broken.answers[("api",)] = "not json"
            unreadable = self._body(broken, tmp)
        self.assertIn("- #123 WO-0018 rejection mining\n", readable)
        self.assertIn("- #123 WO-0018 rejection mining — age unknown"
                      " (timeline unreadable)\n", unreadable)
        self.assertNotEqual(readable, unreadable)

    def test_a_full_window_says_so_in_the_posted_body(self):
        """The defect brief's first reproduction, as a regression: the
        truncated digest was byte-identical to the complete one."""
        waiting = issue(123, "WO-0018 rejection mining",
                        labels=["wo:prd-approved"])
        seen = {123: [labeled("2026-07-20T09:00:00Z", "wo:prd-approved")]}
        with tempfile.TemporaryDirectory() as tmp:
            complete = self._body(gh(issues=[waiting], timelines=seen), tmp)
            partial = self._body(gh(
                issues=[waiting] + [
                    issue(10_000 + n, f"noise {n}", state="CLOSED")
                    for n in range(gate_digest.LIST_WINDOW - 1)],
                timelines=seen), tmp)
        self.assertNotEqual(complete, partial)
        self.assertNotIn(gate_digest.TRUNCATED_NOTE, complete)
        self.assertIn(gate_digest.TRUNCATED_NOTE, partial)
        # the queue itself still renders — truncation reports, never aborts
        self.assertIn("- #123 WO-0018 rejection mining — waiting 2d 0h",
                      partial)


class TestMain(cli_contract.ReportContract, unittest.TestCase):
    summary_line = "gate_digest: 0 problem(s)"

    def clean_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            return cli_contract.capture(
                gate_digest.main, ["daily"], env={},
                root=tree(tmp).root, run=gh(), clock=clock)

    def test_daily_writes_changed_to_github_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.txt"
            run = gh()
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


class TestWorkflowOutputLockstep(unittest.TestCase):
    """The $GITHUB_OUTPUT seam, gate-digest side: run_daily's output keys
    and gate-digest.yml's steps.digest.outputs.<name> references are a
    split contract with no other bridge. Same idiom as
    test_assembler.TestWorkflowOutputLockstep and its cost_report twin —
    this was the fourth site of the three and the only one unpinned.

    What a rename costs here: `changed` gates the commit step. An
    unresolvable ref expands to the empty string, `'' == 'true'` is
    false, and the gate-latency rows run_daily appended to
    docs/factory/costs.jsonl are computed every day and discarded with
    the runner — silently, with the workflow green and the digest still
    posting.

    Root and payload YAML are byte-identical (detector E + TestLockstep),
    so pinning the root copy pins both.
    """

    WORKFLOW = (Path(__file__).resolve().parents[1] / ".github"
                / "workflows" / "gate-digest.yml")
    REFS = re.compile(r"steps\.digest\.outputs\.(\w+)")

    def yaml_refs(self):
        refs = set(self.REFS.findall(
            self.WORKFLOW.read_text(encoding="utf-8")))
        self.assertTrue(refs, "gate-digest.yml references no digest outputs")
        return refs

    def emitted_keys(self):
        """The keys EVERY run_daily path writes — the intersection, not
        the union its two siblings take.

        The workflow reads its ref unconditionally, on whichever path the
        run took, so a key only some paths emit would still expand to ''
        on the others. All three paths are exercised through the public
        interface rather than a hand-kept list: an unreachable tracker,
        a run with no new rows, and a run that captures one."""
        per_path = []
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(failing=["issue", "list"])
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertTrue(problems, "the unreachable-tracker path did"
                                      " not fail — fixture is wrong")
            per_path.append(set(outputs))
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(issues=[issue(123, "WO-0018 rejection mining",
                                   labels=["wo:draft", "size:S"])],
                     timelines={123: [labeled("2026-07-20T09:00:00Z",
                                              "wo:draft")]})
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, [])
            self.assertEqual(outputs.get("changed"), "false",
                             "the no-new-rows path did not report"
                             " changed=false — fixture or key is wrong")
            per_path.append(set(outputs))
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(issues=[issue(131, "WO-0010 sweeps", state="CLOSED",
                                   labels=["wo:merged"])],
                     timelines={131: [
                         labeled("2026-07-01T09:00:00Z", "wo:needs-review"),
                         unlabeled("2026-07-01T10:00:00Z", "wo:needs-review"),
                         labeled("2026-07-01T10:00:00Z", "wo:merged")]})
            outputs, problems = gate_digest.run_daily(
                tree(tmp).root, run=run, clock=clock)
            self.assertEqual(problems, [])
            self.assertEqual(outputs.get("changed"), "true",
                             "the captured-row path did not report"
                             " changed=true — fixture or key is wrong")
            per_path.append(set(outputs))
        self.assertEqual(len(per_path), 3)
        return set.intersection(*per_path)

    def test_every_yaml_output_ref_is_emitted_on_every_path(self):
        self.assertLessEqual(self.yaml_refs(), self.emitted_keys())

    def test_the_workflow_consumes_the_commit_gate_key(self):
        # the key whose silent loss discards every captured latency row
        self.assertIn("changed", self.yaml_refs())
