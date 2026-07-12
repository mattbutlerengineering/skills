"""validator.py (the validator workflow's brain) — pure-function + fixture
tests.

Same discipline as test_label_sync/test_factory_gates: every function is
exercised through its public interface, tests assert the EXACT problem
strings callers will print, and the gh runner is injected so no test ever
touches the network.
"""
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import validator

REPO_ROOT = Path(__file__).resolve().parent.parent

# One row per grammar case the merged-label step must survive: the target
# row, a later row that only *mentions* the target in its blocking edges, a
# row with no tracker mirror, and a Notes line carrying the target's token.
BREAKDOWN = (
    "# Breakdown\n"
    "\n"
    "- [x] **WO-0003** detector B — size:S, blocked by: —"
    " (PRD-0001 §Success criteria) (tracker: #108)\n"
    "- [ ] **WO-0004** validator.yml — size:M, blocked by: WO-0003"
    " (PRD-0001 §Solution) (tracker: #109)\n"
    "- [ ] **WO-0005** assembler — size:L, blocked by: WO-0004"
    " (PRD-0001 §Solution) (tracker: #110)\n"
    "- [ ] **WO-0007** unmirrored row (PRD-0001 §Solution)\n"
    "\n"
    "## Notes\n"
    "\n"
    "- 2026-07-12: a note naming WO-0004 (PRD-0001) is not a row.\n"
)

LIFECYCLE = ["wo:draft", "wo:prd-approved", "wo:blueprint-approved",
             "wo:ready-for-agent", "wo:in-progress", "wo:needs-review",
             "wo:merged", "wo:failed", "wo:blocked"]


class FixtureTree:
    def __init__(self, root):
        self.root = Path(root)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


class RecordingRunner:
    """Injected gh runner: records every call (resolving --body-file to its
    content, which the real gh reads before the caller deletes it), answers
    `issue view` with a canned label set, and never touches the network."""

    def __init__(self, labels=()):
        self.labels = list(labels)
        self.calls = []

    def __call__(self, args):
        call = list(args)
        if "--body-file" in call:
            index = call.index("--body-file") + 1
            call[index] = Path(call[index]).read_text(encoding="utf-8")
        self.calls.append(call)
        if call[:2] == ["issue", "view"]:
            return json.dumps(
                {"labels": [{"name": name} for name in self.labels]})
        return ""

    def called(self, *prefix):
        return [c for c in self.calls if c[:len(prefix)] == list(prefix)]


class FailingRunner(RecordingRunner):
    """Injected gh runner that fails the way a real gh does on a chosen
    subcommand: raises what subprocess.run(check=True) would raise."""

    def __init__(self, labels=(), error=None, failing=()):
        super().__init__(labels)
        self.error = error or subprocess.CalledProcessError(1, "gh")
        self.failing = list(failing)

    def __call__(self, args):
        result = super().__call__(args)
        if list(args[:len(self.failing)]) == self.failing:
            raise self.error
        return result


def pr_env(tmp, **pr):
    """A GITHUB_EVENT_PATH env pointing at a pull_request payload."""
    path = Path(tmp) / "event.json"
    path.write_text(json.dumps({"pull_request": pr}), encoding="utf-8")
    return {"GITHUB_EVENT_PATH": str(path)}


class TestTrackerIssue(unittest.TestCase):
    """The mirrored issue number comes from the breakdown row, never from
    the issue (ADR-0032: the dispatch mirror is one-way)."""

    def tree(self, tmp):
        tree = FixtureTree(tmp)
        tree.write("docs/features/demo/breakdown.md", BREAKDOWN)
        return tree

    def test_row_token_resolves_to_its_tracker_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            self.assertEqual(validator.tracker_issue(tree.root, "WO-0004"),
                             (109, []))

    def test_a_blocking_edge_mention_is_not_the_row(self):
        """WO-0005's row names WO-0004 in its blocking edges; resolving
        WO-0005 must return #110, not #109."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            self.assertEqual(validator.tracker_issue(tree.root, "WO-0005"),
                             (110, []))

    def test_unmirrored_row_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            self.assertEqual(validator.tracker_issue(tree.root, "WO-0007"), (
                None, ["V: WO-0007 has no (tracker: #N) mirror on its"
                       " breakdown row"]))

    def test_unknown_work_order_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            self.assertEqual(validator.tracker_issue(tree.root, "WO-0099"), (
                None, ["V: WO-0099 has no breakdown row"]))


class TestLifecycleLabels(unittest.TestCase):
    def test_taxonomy_yields_the_nine_lifecycle_labels_in_order(self):
        names, problems = validator.lifecycle_labels(REPO_ROOT)
        self.assertEqual(problems, [])
        self.assertEqual(names, LIFECYCLE)

    def test_missing_taxonomy_surfaces_the_label_sync_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            names, problems = validator.lifecycle_labels(Path(tmp))
            self.assertEqual(names, [])
            self.assertEqual(problems, [
                "L: missing labels.json (.github/labels.json or"
                " factory/templates/.github/labels.json)"])


class TestTransition(unittest.TestCase):
    """ADR-0032: exactly one lifecycle label at a time."""

    def test_target_is_added_and_every_other_lifecycle_label_removed(self):
        self.assertEqual(
            validator.transition(["wo:needs-review", "size:M", "type:feature"],
                                 LIFECYCLE, "wo:merged"),
            (["wo:merged"], ["wo:needs-review"]))

    def test_orthogonal_labels_are_never_touched(self):
        add, remove = validator.transition(
            ["size:M", "risk:low", "needs-human"], LIFECYCLE, "wo:merged")
        self.assertEqual((add, remove), (["wo:merged"], []))

    def test_already_labelled_issue_is_a_no_op(self):
        self.assertEqual(
            validator.transition(["wo:merged"], LIFECYCLE, "wo:merged"),
            ([], []))


class TestActorConflict(unittest.TestCase):
    """PRD-0001: no work is verified by the agent that produced it."""

    def test_distinct_actors_are_silent(self):
        self.assertEqual(
            validator.actor_conflict("mattb", "github-actions[bot]"), [])

    def test_self_review_is_refused_case_insensitively(self):
        self.assertEqual(validator.actor_conflict("MattB", "mattb"), [
            "V: MattB authored this PR and cannot review it — generation and"
            " verification must be separate actors (set FACTORY_REVIEW_TOKEN"
            " and FACTORY_REVIEW_LOGIN to a non-authoring identity)"])

    def test_unnamed_reviewer_is_refused(self):
        self.assertEqual(validator.actor_conflict("mattb", ""), [
            "V: the reviewing actor is unnamed (set FACTORY_REVIEW_LOGIN)"])


class TestRenderFindings(unittest.TestCase):
    def test_pass_body_names_both_actors_and_the_work_order(self):
        body = validator.render_findings(
            "WO-0004", "mattb", "github-actions[bot]", "gates: 0 problem(s)\n",
            0)
        self.assertIn(validator.REVIEW_MARKER, body)
        self.assertIn("WO-0004", body)
        self.assertIn("`github-actions[bot]`", body)
        self.assertIn("`mattb`", body)
        self.assertIn("PASS", body)
        self.assertIn("gates: 0 problem(s)", body)

    def test_fail_body_reports_the_failure(self):
        body = validator.render_findings(
            "WO-0004", "mattb", "bot", "A: uncited row\n", 1)
        self.assertIn("FAIL", body)
        self.assertIn("A: uncited row", body)

    def test_long_output_is_truncated_not_dropped(self):
        output = "".join(f"line {n}\n" for n in range(5000))
        body = validator.render_findings("WO-0004", "a", "b", output, 1)
        self.assertLess(len(body), 20000)
        self.assertIn("line 0", body)
        self.assertIn("truncated", body)


class TestRunReview(unittest.TestCase):
    def tree(self, tmp):
        tree = FixtureTree(tmp)
        tree.write("docs/features/demo/breakdown.md", BREAKDOWN)
        tree.write("findings.txt", "gates: 0 problem(s)\n")
        return tree

    def env(self, tmp, author="mattb", login="github-actions[bot]"):
        env = pr_env(tmp, number=42, body="WO-0004 (PRD-0001) Closes #109",
                     user={"login": author})
        env["FACTORY_REVIEW_LOGIN"] = login
        return env

    def test_posts_findings_as_the_non_authoring_actor(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner()
            problems = validator.run_review(
                tree.root, tree.root / "findings.txt", 0,
                env=self.env(tmp), run=run)
            self.assertEqual(problems, [])
            posted = run.called("pr", "comment", "42")
            self.assertTrue(posted, run.calls)
            body = posted[-1][posted[-1].index("--body-file") + 1]
            self.assertIn("WO-0004", body)
            self.assertIn("gates: 0 problem(s)", body)
            self.assertIn("PASS", body)

    def test_author_cannot_review_their_own_pr_and_nothing_is_posted(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner()
            problems = validator.run_review(
                tree.root, tree.root / "findings.txt", 0,
                env=self.env(tmp, author="factory-bot", login="factory-bot"),
                run=run)
            self.assertEqual(problems, [
                "V: factory-bot authored this PR and cannot review it —"
                " generation and verification must be separate actors (set"
                " FACTORY_REVIEW_TOKEN and FACTORY_REVIEW_LOGIN to a"
                " non-authoring identity)"])
            self.assertEqual(run.calls, [])

    def test_red_findings_still_post_and_do_not_fail_the_review_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            tree.write("findings.txt", "A: uncited row\ngates: 1 problem(s)\n")
            run = RecordingRunner()
            problems = validator.run_review(
                tree.root, tree.root / "findings.txt", 1,
                env=self.env(tmp), run=run)
            self.assertEqual(problems, [])
            body = run.calls[-1][run.calls[-1].index("--body-file") + 1]
            self.assertIn("FAIL", body)
            self.assertIn("A: uncited row", body)

    def test_first_comment_falls_back_when_there_is_none_to_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = FailingRunner(failing=["pr", "comment", "42", "--edit-last"])
            problems = validator.run_review(
                tree.root, tree.root / "findings.txt", 0,
                env=self.env(tmp), run=run)
            self.assertEqual(problems, [])
            self.assertEqual(len(run.calls), 2)
            self.assertIn("--edit-last", run.calls[0])
            self.assertNotIn("--edit-last", run.calls[1])

    def test_a_failing_post_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = FailingRunner(
                error=OSError("gh: not found"), failing=["pr", "comment"])
            problems = validator.run_review(
                tree.root, tree.root / "findings.txt", 0,
                env=self.env(tmp), run=run)
            self.assertEqual(
                problems, ["V: gh pr comment failed: gh: not found"])

    def test_missing_findings_file_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            missing = tree.root / "nope.txt"
            run = RecordingRunner()
            problems = validator.run_review(
                tree.root, missing, 0, env=self.env(tmp), run=run)
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                f"V: cannot read findings file {missing}:"), problems)
            self.assertEqual(run.calls, [])

    def test_outside_a_pull_request_event_nothing_is_posted(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner()
            problems = validator.run_review(
                tree.root, tree.root / "findings.txt", 0, env={}, run=run)
            self.assertEqual(
                problems, ["V: no pull_request in the CI event payload"])
            self.assertEqual(run.calls, [])


class TestRunLifecycle(unittest.TestCase):
    def tree(self, tmp):
        tree = FixtureTree(tmp)
        tree.write("docs/features/demo/breakdown.md", BREAKDOWN)
        tree.write(".github/labels.json", json.dumps(
            [{"name": name, "color": "ededed", "description": "lifecycle"}
             for name in LIFECYCLE]
            + [{"name": "size:M", "color": "f4a261", "description": "size"}]))
        return tree

    def env(self, tmp, body="WO-0004 (PRD-0001 §Solution) Closes #109"):
        return pr_env(tmp, number=42, body=body, merged=True,
                      user={"login": "mattb"})

    def test_merged_pr_flips_the_work_order_to_the_target_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner(labels=["wo:needs-review", "size:M"])
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp), run=run)
            self.assertEqual(problems, [])
            edits = run.called("issue", "edit", "109")
            self.assertEqual(edits, [[
                "issue", "edit", "109",
                "--add-label", "wo:merged",
                "--remove-label", "wo:needs-review"]])

    def test_an_already_merged_issue_needs_no_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner(labels=["wo:merged"])
            self.assertEqual(validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp), run=run), [])
            self.assertEqual(run.called("issue", "edit"), [])

    def test_a_label_outside_the_state_machine_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner()
            self.assertEqual(
                validator.run_lifecycle(
                    tree.root, "wo:done", env=self.env(tmp), run=run),
                ["V: wo:done is not a lifecycle label in the taxonomy"])
            self.assertEqual(run.calls, [])

    def test_a_pr_citing_no_work_order_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner()
            self.assertEqual(
                validator.run_lifecycle(tree.root, "wo:merged",
                                        env=self.env(tmp, body="no tokens"),
                                        run=run),
                ["V: PR body cites no work-order id"])
            self.assertEqual(run.calls, [])

    def test_a_failing_gh_call_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = FailingRunner(labels=["wo:needs-review"],
                                error=OSError("gh: not found"),
                                failing=["issue", "view"])
            self.assertEqual(
                validator.run_lifecycle(
                    tree.root, "wo:merged", env=self.env(tmp), run=run),
                ["V: gh issue view 109 failed: gh: not found"])


class TestMain(unittest.TestCase):
    def main(self, argv):
        """(exit code, stdout) — the CLI's printed contract, captured so the
        test run stays quiet."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = validator.main(argv, env={}, run=RecordingRunner())
        return code, out.getvalue()

    def test_unknown_subcommand_prints_usage(self):
        code, out = self.main(["nonsense"])
        self.assertEqual(code, 2)
        self.assertIn("python3 validator.py review", out)

    def test_a_non_numeric_status_is_a_usage_error(self):
        self.assertEqual(
            self.main(["review", "--status", "red"])[0], 2)

    def test_review_outside_an_event_exits_nonzero_with_the_problem(self):
        code, out = self.main(["review", "--findings", "findings.txt"])
        self.assertEqual(code, 1)
        self.assertIn("V: no pull_request in the CI event payload", out)
        self.assertIn("validator: 1 problem(s)", out)


if __name__ == "__main__":
    unittest.main()
