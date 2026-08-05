"""validator.py (the validator workflow's brain) — pure-function + fixture
tests.

Same discipline as test_label_sync/test_factory_gates: every function is
exercised through its public interface, tests assert the EXACT problem
strings callers will print, and the gh runner is injected so no test ever
touches the network.
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import validator

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling fixture_tree import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture_tree import FixtureTree  # noqa: E402
import cli_contract  # noqa: E402

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


class RecordingRunner:
    """Injected gh runner: records every call (resolving --body-file to its
    content, which the real gh reads before the caller deletes it), answers
    `issue view` with a canned label set and `api user` with the login the
    token actually posts as, and never touches the network."""

    def __init__(self, labels=(), login="github-actions[bot]"):
        self.labels = list(labels)
        self.login = login
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
        if call[:2] == ["api", "user"]:
            return f"{self.login}\n"
        return ""

    def called(self, *prefix):
        return [c for c in self.calls if c[:len(prefix)] == list(prefix)]


class FailingRunner(RecordingRunner):
    """Injected gh runner that fails the way a real gh does on a chosen
    subcommand: raises what subprocess.run(check=True) would raise."""

    def __init__(self, labels=(), error=None, failing=(),
                 login="github-actions[bot]"):
        super().__init__(labels, login)
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
            " verification must be separate actors (give the reviewer its own"
            " identity: FACTORY_REVIEW_TOKEN)"])

    def test_unnamed_reviewer_is_refused(self):
        self.assertEqual(validator.actor_conflict("mattb", ""), [
            "V: the reviewing actor is unnamed — no identity was resolved"
            " from the review token"])

    def test_unnamed_author_is_refused(self):
        """Symmetry: an author who cannot be named cannot be shown to DIFFER
        from the reviewer either — an empty string compares unequal to every
        login, so the guard would pass on nothing."""
        self.assertEqual(validator.actor_conflict("", "github-actions[bot]"), [
            "V: the PR's author is unnamed — an author who cannot be named"
            " cannot be shown to differ from the reviewer"])


class TestReviewerLogin(unittest.TestCase):
    """The reviewing identity is derived from the TOKEN, never declared: a
    variable that *says* who the token is proves nothing about who it posts
    as, and PRD-0001's non-authoring property is only as good as the identity
    it compares. Anything unresolved fails CLOSED — never fall through to
    posting."""

    def test_an_undeclared_provenance_fails_closed(self):
        """An ABSENT flag must not read as "false". Inside the pinned workflow
        both env values are set in one step, but any OTHER caller of `make
        review` in a stamped repo — WO-0005's assembler running a re-review
        job with its PAT in GH_TOKEN and no flag set — would otherwise
        reintroduce the original bug verbatim: the reviewer ASSERTED to be
        github-actions[bot] while actually posting as factory-bot. Detector E
        pins factory/templates/**, not a downstream repo's other workflows,
        so nothing else catches it."""
        run = RecordingRunner(login="factory-bot")
        self.assertEqual(validator.reviewer_login({}, run), (
            None, ["V: the review step did not declare the token's provenance"
                   " (FACTORY_REVIEW_TOKEN_SET) — refusing to post"]))
        self.assertEqual(run.calls, [])

    def test_a_garbled_provenance_fails_closed(self):
        run = RecordingRunner(login="factory-bot")
        self.assertEqual(
            validator.reviewer_login({"FACTORY_REVIEW_TOKEN_SET": "yes"}, run),
            (None, ["V: the review step did not declare the token's"
                    " provenance (FACTORY_REVIEW_TOKEN_SET) — refusing to"
                    " post"]))
        self.assertEqual(run.calls, [])

    def test_a_declared_absence_of_a_review_token_is_the_workflows_own_bot(self):
        """FACTORY_REVIEW_TOKEN_SET=false means GH_TOKEN is the workflow's own
        GITHUB_TOKEN, whose posting identity GitHub fixes — that is derived
        from the token's provenance, not from a human-maintained variable, so
        there is nothing to ask."""
        run = RecordingRunner(login="never-asked")
        self.assertEqual(
            validator.reviewer_login({"FACTORY_REVIEW_TOKEN_SET": "false"},
                                     run),
            ("github-actions[bot]", []))
        self.assertEqual(run.calls, [])

    def test_a_review_token_is_asked_who_it_actually_is(self):
        run = RecordingRunner(login="factory-bot")
        self.assertEqual(
            validator.reviewer_login({"FACTORY_REVIEW_TOKEN_SET": "true"}, run),
            ("factory-bot", []))
        self.assertEqual(run.called("api", "user"),
                         [["api", "user", "--jq", ".login"]])

    def test_an_unresolvable_identity_fails_closed(self):
        run = FailingRunner(error=OSError("gh: not found"),
                            failing=["api", "user"])
        self.assertEqual(
            validator.reviewer_login({"FACTORY_REVIEW_TOKEN_SET": "true"}, run),
            (None, ["V: cannot resolve the reviewing identity from"
                    " FACTORY_REVIEW_TOKEN (gh api user failed: gh: not"
                    " found) — refusing to post"]))

    def test_an_empty_login_fails_closed(self):
        run = RecordingRunner(login="")
        self.assertEqual(
            validator.reviewer_login({"FACTORY_REVIEW_TOKEN_SET": "true"}, run),
            (None, ["V: FACTORY_REVIEW_TOKEN resolves to no login —"
                    " refusing to post"]))


class TestDeclaredConflict(unittest.TestCase):
    """FACTORY_REVIEW_LOGIN survives only as an optional cross-check."""

    def test_an_unset_declaration_is_silent(self):
        self.assertEqual(validator.declared_conflict("", "factory-bot"), [])

    def test_a_declaration_the_token_confirms_is_silent(self):
        self.assertEqual(
            validator.declared_conflict("Factory-Bot", "factory-bot"), [])

    def test_a_declaration_the_token_contradicts_refuses_to_post(self):
        self.assertEqual(
            validator.declared_conflict("github-actions[bot]", "factory-bot"),
            ["V: FACTORY_REVIEW_LOGIN declares github-actions[bot] but the"
             " review token posts as factory-bot — refusing to post until the"
             " declaration matches the token"])


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
        """The workflow's default review step: no FACTORY_REVIEW_TOKEN, and
        the step SAYS so — the provenance is always declared explicitly."""
        env = pr_env(tmp, number=42, body="WO-0004 (PRD-0001) Closes #109",
                     user={"login": author})
        env["FACTORY_REVIEW_LOGIN"] = login
        env["FACTORY_REVIEW_TOKEN_SET"] = "false"
        return env

    def test_a_caller_that_declares_no_provenance_posts_nothing(self):
        """The hardening case: a stamped repo wires up another caller of
        `make review` (an assembler re-review job) with its PAT in GH_TOKEN
        and no FACTORY_REVIEW_TOKEN_SET. The guard must refuse, not assume
        github-actions[bot] and post as the bot that authored the PR."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            env = self.env(tmp, author="factory-bot", login="")
            del env["FACTORY_REVIEW_TOKEN_SET"]
            run = RecordingRunner(login="factory-bot")
            problems = validator.run_review(
                tree.root, tree.root / "findings.txt", 0, env=env, run=run)
            self.assertEqual(problems, [
                "V: the review step did not declare the token's provenance"
                " (FACTORY_REVIEW_TOKEN_SET) — refusing to post"])
            self.assertEqual(run.calls, [])

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
        """The default token posts as github-actions[bot]; a PR that bot
        authored is one it cannot review."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner()
            problems = validator.run_review(
                tree.root, tree.root / "findings.txt", 0,
                env=self.env(tmp, author="github-actions[bot]", login=""),
                run=run)
            self.assertEqual(problems, [
                "V: github-actions[bot] authored this PR and cannot review"
                " it — generation and verification must be separate actors"
                " (give the reviewer its own identity: FACTORY_REVIEW_TOKEN)"])
            self.assertEqual(run.called("pr", "comment"), [])

    def test_a_token_that_is_the_author_never_posts_however_it_is_declared(self):
        """The exact case WO-0005's assembler creates: the bot's PAT is set
        as FACTORY_REVIEW_TOKEN and FACTORY_REVIEW_LOGIN is left unset (so it
        used to default to github-actions[bot]). Comparing the author against
        that DECLARATION saw two different strings and posted — the bot
        reviewing its own PR while the guard reported success. The identity
        that matters is the one the TOKEN posts as."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            env = self.env(tmp, author="factory-bot",
                           login="github-actions[bot]")
            env["FACTORY_REVIEW_TOKEN_SET"] = "true"
            run = RecordingRunner(login="factory-bot")
            problems = validator.run_review(
                tree.root, tree.root / "findings.txt", 0, env=env, run=run)
            self.assertIn(
                "V: factory-bot authored this PR and cannot review it —"
                " generation and verification must be separate actors (give"
                " the reviewer its own identity: FACTORY_REVIEW_TOKEN)",
                problems)
            self.assertEqual(run.called("pr", "comment"), [])

    def test_an_unresolvable_reviewing_identity_posts_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            env = self.env(tmp)
            env["FACTORY_REVIEW_TOKEN_SET"] = "true"
            run = FailingRunner(error=OSError("gh: not found"),
                                failing=["api", "user"])
            problems = validator.run_review(
                tree.root, tree.root / "findings.txt", 0, env=env, run=run)
            self.assertEqual(problems, [
                "V: cannot resolve the reviewing identity from"
                " FACTORY_REVIEW_TOKEN (gh api user failed: gh: not found) —"
                " refusing to post"])
            self.assertEqual(run.called("pr", "comment"), [])

    def test_the_comment_names_the_identity_the_token_posts_as(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            env = self.env(tmp, author="mattb", login="")
            env["FACTORY_REVIEW_TOKEN_SET"] = "true"
            run = RecordingRunner(login="factory-bot")
            problems = validator.run_review(
                tree.root, tree.root / "findings.txt", 0, env=env, run=run)
            self.assertEqual(problems, [])
            posted = run.called("pr", "comment", "42")[-1]
            self.assertIn("`factory-bot`",
                          posted[posted.index("--body-file") + 1])

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


class TestCitedWorkOrder(unittest.TestCase):
    """Which work order a PR implements. The merged-label step flips THAT
    work order's issue, so a body that merely MENTIONS another one ("builds
    on WO-0004", a quoted Accept line) must not redirect the label. The
    citation is structural, not positional: the work order is the one whose
    breakdown row is mirrored to an issue the PR closes."""

    def tree(self, tmp):
        tree = FixtureTree(tmp)
        tree.write("docs/features/demo/breakdown.md", BREAKDOWN)
        return tree

    def cited(self, tmp, body):
        return validator.cited_work_order(self.tree(tmp).root, body)

    def test_the_work_order_is_the_one_whose_tracker_the_pr_closes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                self.cited(tmp, "WO-0005 assembler (PRD-0001)\n\nCloses #110"),
                ("WO-0005", []))

    def test_a_mention_before_the_citation_does_not_redirect_the_label(self):
        """The regression: WO-0005's PR body opens by naming WO-0004 (its
        blocking edge). Taking the FIRST token would flip WO-0004's issue."""
        with tempfile.TemporaryDirectory() as tmp:
            body = ('Builds on WO-0004 — Accept: "…the review job posts'
                    ' findings from a non-authoring actor."\n\n'
                    "This is WO-0005 (PRD-0001 §Solution).\n\nCloses #110\n")
            self.assertEqual(self.cited(tmp, body), ("WO-0005", []))

    def test_a_body_citing_no_work_order_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.cited(tmp, "no tokens\nCloses #110"),
                             (None, ["V: PR body cites no work-order id"]))

    def test_a_body_with_no_closes_link_cannot_be_disambiguated(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                self.cited(tmp, "WO-0004 (PRD-0001), which unblocks WO-0005."),
                (None, ["V: PR body has no Closes #N link, so the work order"
                        " it implements cannot be told from the ones it only"
                        " mentions"]))

    def test_closing_no_cited_work_orders_issue_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                self.cited(tmp, "WO-0004 unblocks WO-0005\nCloses #999"),
                (None, ["V: none of the work orders this PR cites (WO-0004,"
                        " WO-0005) is mirrored to an issue it closes (#999) —"
                        " a PR implements the work order whose breakdown row"
                        " it closes"]))

    def test_closing_two_work_orders_issues_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                self.cited(tmp, "WO-0004 and WO-0005\nCloses #109\nCloses #110"),
                (None, ["V: this PR closes the mirrored issues of more than"
                        " one work order (WO-0004, WO-0005); a work order is"
                        " one PR"]))

    def test_a_lone_citation_reports_why_its_row_did_not_resolve(self):
        """WO-0007's row has no (tracker: #N): say so, rather than hiding it
        behind a generic "nothing matched"."""
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                self.cited(tmp, "WO-0007 (PRD-0001)\nCloses #199"),
                (None, ["V: WO-0007 has no (tracker: #N) mirror on its"
                        " breakdown row"]))

    def test_a_lone_citation_that_closes_the_wrong_issue_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                self.cited(tmp, "WO-0004 (PRD-0001)\nCloses #999"),
                (None, ["V: none of the work orders this PR cites (WO-0004)"
                        " is mirrored to an issue it closes (#999) — a PR"
                        " implements the work order whose breakdown row it"
                        " closes"]))


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

    def test_a_mentioned_work_order_does_not_get_the_merged_label(self):
        """End to end for the merged-label step: WO-0005's PR names WO-0004
        first. #109 (WO-0004's issue) must not be touched — #110 is."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner(labels=["wo:in-progress"])
            body = ("Builds on WO-0004. This is WO-0005 (PRD-0001).\n\n"
                    "Closes #110\n")
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp, body=body), run=run)
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "110",
                "--add-label", "wo:merged",
                "--remove-label", "wo:in-progress"]])

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

    def test_uncited_skip_silences_a_pr_with_no_work_order(self):
        # The PR-open leg (wo:needs-review) labels every WO PR, but a
        # human housekeeping PR cites no work order — that is normal
        # traffic, not an error. Nothing is resolved, nothing is called.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner()
            problems = validator.run_lifecycle(
                tree.root, "wo:needs-review",
                env=self.env(tmp, body="chore: housekeeping"), run=run,
                uncited="skip")
            self.assertEqual(problems, [])
            self.assertEqual(run.calls, [])

    def test_uncited_skip_keeps_a_malformed_citation_loud(self):
        # The skip is exactly the no-citation case. A body that NAMES a
        # work order but resolves to none is a malformed WO PR — silently
        # not labelling it would lose the queue-entry event with nothing
        # ever retrying it (the job fires on opened/reopened only).
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner()
            problems = validator.run_lifecycle(
                tree.root, "wo:needs-review",
                env=self.env(tmp, body="Implements WO-0004."), run=run,
                uncited="skip")
            self.assertEqual(problems, [
                "V: PR body has no Closes #N link, so the work order it"
                " implements cannot be told from the ones it only"
                " mentions"])
            self.assertEqual(run.calls, [])

    def test_uncited_skip_still_flips_a_cited_work_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner(labels=["wo:in-progress"])
            problems = validator.run_lifecycle(
                tree.root, "wo:needs-review", env=self.env(tmp), run=run,
                uncited="skip")
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "109",
                "--add-label", "wo:needs-review",
                "--remove-label", "wo:in-progress"]])

    def test_the_merged_leg_stays_strict_by_default(self):
        # Only an explicit uncited="skip" relaxes the citation; the
        # merged leg keeps failing loudly on an uncited PR (mutating the
        # wrong issue silently would be worse than a red job).
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = RecordingRunner()
            problems = validator.run_lifecycle(
                tree.root, "wo:merged",
                env=self.env(tmp, body="chore: housekeeping"), run=run)
            self.assertEqual(
                problems, ["V: PR body cites no work-order id"])

    class BannerViewRunner(RecordingRunner):
        """Records like RecordingRunner but answers `issue view` with raw
        non-JSON (or wrong-shape) stdout — gh ran, exited 0, said nonsense."""

        def __init__(self, stdout):
            super().__init__()
            self.stdout = stdout

        def __call__(self, args):
            out = super().__call__(args)
            return self.stdout if list(args[:2]) == ["issue", "view"] else out

    def test_an_unparseable_issue_view_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = self.BannerViewRunner("gh: banner text")
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp), run=run)
            self.assertEqual(problems, [
                "V: gh issue view 109 returned unparseable JSON:"
                " Expecting value: line 1 column 1 (char 0)"])
            self.assertEqual(run.called("issue", "edit"), [])

    def test_a_non_object_issue_view_is_a_problem_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = self.BannerViewRunner("[]")
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp), run=run)
            self.assertEqual(problems, [
                "V: gh issue view 109 returned list where dict"
                " was expected"])
            self.assertEqual(run.called("issue", "edit"), [])


class TestRunClaim(unittest.TestCase):
    """The dispatch claim (ADR-0032): flip a known issue to
    wo:in-progress and tell the workflow whether the order was actually
    in ready state — `transitioned` on $GITHUB_OUTPUT is the assembler's
    idempotency verdict; false means a repeat/stale event and the paid
    agent step must not run."""

    def tree(self, tmp):
        tree = FixtureTree(tmp)
        tree.write(".github/labels.json", json.dumps(
            [{"name": name, "color": "ededed", "description": "lifecycle"}
             for name in LIFECYCLE]
            + [{"name": "size:M", "color": "f4a261", "description": "size"}]))
        return tree

    def env(self, tmp):
        return {"GITHUB_OUTPUT": str(Path(tmp) / "outputs.txt")}

    def outputs(self, env):
        path = Path(env["GITHUB_OUTPUT"])
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def test_a_ready_order_is_claimed_and_reports_transitioned(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            env = self.env(tmp)
            run = RecordingRunner(labels=["wo:ready-for-agent", "size:M"])
            problems = validator.run_claim(
                tree.root, "wo:in-progress", "109", env=env, run=run)
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "109",
                "--add-label", "wo:in-progress",
                "--remove-label", "wo:ready-for-agent"]])
            self.assertEqual(self.outputs(env), "transitioned=true\n")

    def test_a_repeat_claim_is_a_no_op_not_an_error(self):
        # The concurrency group queues a repeat label event behind the
        # running dispatch; by the time it runs, the order is already
        # wo:in-progress. That is a skip (exit 0, transitioned=false),
        # never a red workflow.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            env = self.env(tmp)
            run = RecordingRunner(labels=["wo:in-progress"])
            problems = validator.run_claim(
                tree.root, "wo:in-progress", "109", env=env, run=run)
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "edit"), [])
            self.assertEqual(self.outputs(env), "transitioned=false\n")

    def test_an_order_no_longer_ready_does_not_count_as_a_claim(self):
        # The flip happens (exactly-one-label invariant) but the order
        # was not in ready state, so this event did not claim it —
        # transitioned=false keeps the agent step skipped.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            env = self.env(tmp)
            run = RecordingRunner(labels=["wo:blocked"])
            problems = validator.run_claim(
                tree.root, "wo:in-progress", "109", env=env, run=run)
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "109",
                "--add-label", "wo:in-progress",
                "--remove-label", "wo:blocked"]])
            self.assertEqual(self.outputs(env), "transitioned=false\n")

    def test_an_order_with_no_lifecycle_label_is_labelled_not_claimed(self):
        # The dispatch job's own if: saw the ready label at event time, so
        # an empty label set means it vanished in between — a raced or
        # hand-tended order. The invariant flip still happens, but this
        # event did not take the order out of ready, so no paid dispatch.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            env = self.env(tmp)
            run = RecordingRunner(labels=["size:M"])
            problems = validator.run_claim(
                tree.root, "wo:in-progress", "109", env=env, run=run)
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "109",
                "--add-label", "wo:in-progress"]])
            self.assertEqual(self.outputs(env), "transitioned=false\n")

    def test_a_label_outside_the_state_machine_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            env = self.env(tmp)
            run = RecordingRunner()
            self.assertEqual(
                validator.run_claim(
                    tree.root, "wo:done", "109", env=env, run=run),
                ["V: wo:done is not a lifecycle label in the taxonomy"])
            self.assertEqual(run.calls, [])
            self.assertEqual(self.outputs(env), "")

    def test_a_taxonomy_without_the_ready_label_is_refused(self):
        # transitioned is "did the flip take the order out of ready" — a
        # taxonomy that lost the ready label would make every verdict
        # false and silently stop all dispatch. Loud beats silent.
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/labels.json", json.dumps(
                [{"name": name, "color": "ededed",
                  "description": "lifecycle"}
                 for name in LIFECYCLE if name != "wo:ready-for-agent"]))
            env = self.env(tmp)
            run = RecordingRunner(labels=["wo:in-progress"])
            self.assertEqual(
                validator.run_claim(
                    tree.root, "wo:in-progress", "109", env=env, run=run),
                ["V: wo:ready-for-agent is not a lifecycle label in the"
                 " taxonomy"])
            self.assertEqual(run.calls, [])
            self.assertEqual(self.outputs(env), "")

    def test_a_failing_gh_call_is_a_problem_and_writes_no_verdict(self):
        # A claim that cannot verify the order's state must fail the
        # step (problems -> nonzero) rather than declare a verdict.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            env = self.env(tmp)
            run = FailingRunner(error=OSError("gh: not found"),
                                failing=["issue", "view"])
            self.assertEqual(
                validator.run_claim(
                    tree.root, "wo:in-progress", "109", env=env, run=run),
                ["V: gh issue view 109 failed: gh: not found"])
            self.assertEqual(self.outputs(env), "")


class TestClaimOutputLockstep(unittest.TestCase):
    """The $GITHUB_OUTPUT seam: run_claim's output keys and assembler.yml's
    steps.claim.outputs.<name> references are a split contract — Python
    writes the keys, the workflow reads them by literal name (the same
    lockstep idiom test_assembler's TestWorkflowOutputLockstep applies to
    resolve). A renamed key breaks here, in CI, instead of silently
    expanding to an empty string that skips every paid dispatch. Root and
    payload YAML are byte-identical (detector E), so pinning the root
    copy pins both."""

    WORKFLOW = REPO_ROOT / ".github" / "workflows" / "assembler.yml"
    REFS = re.compile(r"steps\.claim\.outputs\.(\w+)")

    def test_every_yaml_claim_ref_is_an_emitted_key(self):
        refs = set(self.REFS.findall(
            self.WORKFLOW.read_text(encoding="utf-8")))
        self.assertTrue(refs, "assembler.yml references no claim outputs")
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/labels.json", json.dumps(
                [{"name": name, "color": "ededed",
                  "description": "lifecycle"} for name in LIFECYCLE]))
            env = {"GITHUB_OUTPUT": str(Path(tmp) / "outputs.txt")}
            problems = validator.run_claim(
                tree.root, "wo:in-progress", "7", env=env,
                run=RecordingRunner(labels=["wo:ready-for-agent"]))
            self.assertEqual(problems, [])
            written = Path(env["GITHUB_OUTPUT"]).read_text(encoding="utf-8")
        keys = {line.split("=", 1)[0]
                for line in written.splitlines() if "=" in line}
        self.assertLessEqual(refs, keys)


class TestParseLifecycle(unittest.TestCase):
    """The three lifecycle invocations (ADR-0032): the merged leg
    (--label alone), the dispatch claim (--label --issue N), and the
    PR-open leg (--label --uncited skip). Anything else is usage."""

    def test_the_bare_label_form_still_parses(self):
        self.assertEqual(
            validator.parse(["lifecycle", "--label", "wo:merged"]),
            ("lifecycle", {"label": "wo:merged"}))

    def test_the_claim_form_takes_a_numeric_issue(self):
        self.assertEqual(
            validator.parse(["lifecycle", "--label", "wo:in-progress",
                             "--issue", "42"]),
            ("lifecycle", {"label": "wo:in-progress", "issue": "42"}))

    def test_a_non_numeric_issue_is_a_usage_error(self):
        self.assertEqual(
            validator.parse(["lifecycle", "--label", "wo:in-progress",
                             "--issue", "abc"]),
            (None, None))

    def test_the_uncited_form_takes_only_skip(self):
        self.assertEqual(
            validator.parse(["lifecycle", "--label", "wo:needs-review",
                             "--uncited", "skip"]),
            ("lifecycle", {"label": "wo:needs-review", "uncited": "skip"}))
        self.assertEqual(
            validator.parse(["lifecycle", "--label", "wo:needs-review",
                             "--uncited", "yes"]),
            (None, None))

    def test_the_claim_and_uncited_forms_do_not_combine(self):
        # A claim names its issue outright; "uncited" only means anything
        # for a PR-shaped resolution. Both at once is a confused caller.
        self.assertEqual(
            validator.parse(["lifecycle", "--label", "wo:in-progress",
                             "--issue", "42", "--uncited", "skip"]),
            (None, None))


class TestMain(cli_contract.CliContract, unittest.TestCase):
    usage_fragment = "python3 validator.py review"

    def run_cli(self, argv):
        return cli_contract.capture(validator.main, argv, env={},
                                    run=RecordingRunner())

    def test_a_non_numeric_status_is_a_usage_error(self):
        self.assertEqual(
            self.run_cli(["review", "--status", "red"])[0], 2)

    def test_review_outside_an_event_exits_nonzero_with_the_problem(self):
        code, out = self.run_cli(["review", "--findings", "findings.txt"])
        self.assertEqual(code, 1)
        self.assertIn("V: no pull_request in the CI event payload", out)
        self.assertIn("validator: 1 problem(s)", out)

    def test_a_non_numeric_claim_issue_is_a_usage_error(self):
        self.assertEqual(
            self.run_cli(["lifecycle", "--label", "wo:in-progress",
                          "--issue", "abc"])[0], 2)

    def test_a_claim_invocation_routes_past_the_pr_event(self):
        # No event payload in env, yet the claim succeeds: --issue N
        # names the issue outright, so main must route to run_claim, not
        # the PR-shaped leg (which would fail here on the missing event).
        run = RecordingRunner(labels=["wo:ready-for-agent"])
        code, out = cli_contract.capture(
            validator.main,
            ["lifecycle", "--label", "wo:in-progress", "--issue", "7"],
            env={}, run=run)
        self.assertEqual(code, 0)
        self.assertEqual(run.called("issue", "edit"), [[
            "issue", "edit", "7",
            "--add-label", "wo:in-progress",
            "--remove-label", "wo:ready-for-agent"]])

    def test_an_uncited_skip_invocation_is_still_pr_shaped(self):
        # --uncited skip relaxes the citation, not the event: outside a
        # pull_request payload it is still a config error.
        code, out = self.run_cli(["lifecycle", "--label", "wo:needs-review",
                                  "--uncited", "skip"])
        self.assertEqual(code, 1)
        self.assertIn("V: no pull_request in the CI event payload", out)


if __name__ == "__main__":
    unittest.main()
