"""validator.py (the validator workflow's brain) — pure-function + fixture
tests.

Same discipline as test_label_sync/test_gates: every function is
exercised through its public interface, tests assert the EXACT problem
strings callers will print, and the gh runner is injected so no test ever
touches the network.
"""
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

import cli
import validator

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling fixture_tree import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_gh import FakeGh  # noqa: E402
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

# The lifecycle labels come from the shipped taxonomy, exactly as the
# other gh-seam suites load it — a wo:* label added to the template
# reaches this suite too, instead of dying against a hand-copied list.
LIFECYCLE = [label["name"] for label in json.loads(
    (REPO_ROOT / "factory" / "templates" / ".github" / "labels.json")
    .read_text(encoding="utf-8")) if label["name"].startswith("wo:")]


def gh(labels=(), login="github-actions[bot]", **kwargs):
    """A fake gh for the validator's traffic: `issue view` answers with
    a canned label set, `api user` with the login the token actually
    posts as (failure declared via FakeGh's failing=/error=)."""
    return FakeGh(answers={
        ("issue", "view"): json.dumps(
            {"labels": [{"name": name} for name in labels]}),
        ("api", "user"): f"{login}\n",
    }, **kwargs)


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
    def test_taxonomy_yields_the_lifecycle_labels_in_order(self):
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
        run = gh(login="factory-bot")
        self.assertEqual(validator.reviewer_login({}, run), (
            None, ["V: the review step did not declare the token's provenance"
                   " (FACTORY_REVIEW_TOKEN_SET) — refusing to post"]))
        self.assertEqual(run.calls, [])

    def test_a_garbled_provenance_fails_closed(self):
        run = gh(login="factory-bot")
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
        run = gh(login="never-asked")
        self.assertEqual(
            validator.reviewer_login({"FACTORY_REVIEW_TOKEN_SET": "false"},
                                     run),
            ("github-actions[bot]", []))
        self.assertEqual(run.calls, [])

    def test_a_review_token_is_asked_who_it_actually_is(self):
        run = gh(login="factory-bot")
        self.assertEqual(
            validator.reviewer_login({"FACTORY_REVIEW_TOKEN_SET": "true"}, run),
            ("factory-bot", []))
        self.assertEqual(run.called("api", "user"),
                         [["api", "user", "--jq", ".login"]])

    def test_an_unresolvable_identity_fails_closed(self):
        run = gh(error=OSError("gh: not found"), failing=["api", "user"])
        self.assertEqual(
            validator.reviewer_login({"FACTORY_REVIEW_TOKEN_SET": "true"}, run),
            (None, ["V: cannot resolve the reviewing identity from"
                    " FACTORY_REVIEW_TOKEN (gh api user failed: gh: not"
                    " found) — refusing to post"]))

    def test_an_empty_login_fails_closed(self):
        run = gh(login="")
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
            run = gh(login="factory-bot")
            problems = validator.run_review(
                tree.root, tree.root / "findings.txt", 0, env=env, run=run)
            self.assertEqual(problems, [
                "V: the review step did not declare the token's provenance"
                " (FACTORY_REVIEW_TOKEN_SET) — refusing to post"])
            self.assertEqual(run.calls, [])

    def test_posts_findings_as_the_non_authoring_actor(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
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
            run = gh()
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
            run = gh(login="factory-bot")
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
            run = gh(error=OSError("gh: not found"),
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
            run = gh(login="factory-bot")
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
            run = gh()
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
            run = gh(failing=["pr", "comment", "42", "--edit-last"])
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
            run = gh(
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
            run = gh()
            problems = validator.run_review(
                tree.root, missing, 0, env=self.env(tmp), run=run)
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                f"V: cannot read findings file {missing}:"), problems)
            self.assertEqual(run.calls, [])

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-000 file")
    def test_unreadable_findings_file_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            findings = tree.root / "findings.txt"
            findings.chmod(0)
            run = gh()
            try:
                problems = validator.run_review(
                    tree.root, findings, 0, env=self.env(tmp), run=run)
            finally:
                findings.chmod(0o644)
            self.assertEqual(problems, [
                f"V: cannot read findings file {findings}: [Errno 13]"
                f" Permission denied: '{findings}'"])
            self.assertEqual(run.calls, [])

    def test_findings_that_are_not_utf8_are_a_problem_not_a_traceback(self):
        """The findings file is another step's captured output, so its
        bytes are whatever that step printed. Undecodable ones are a
        read failure like a missing file — a problem string and nothing
        posted, where the review job used to die on the decode."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            findings = tree.root / "findings.txt"
            findings.write_bytes(b"\xff\xfe")
            run = gh()
            problems = validator.run_review(
                tree.root, findings, 0, env=self.env(tmp), run=run)
            self.assertEqual(problems, [
                f"V: cannot read findings file {findings}: 'utf-8' codec"
                " can't decode byte 0xff in position 0: invalid start"
                " byte"])
            self.assertEqual(run.calls, [])

    def test_outside_a_pull_request_event_nothing_is_posted(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
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
            run = gh(labels=["wo:needs-review", "size:M"])
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
            run = gh(labels=["wo:merged"])
            self.assertEqual(validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp), run=run), [])
            self.assertEqual(run.called("issue", "edit"), [])

    def test_a_label_outside_the_state_machine_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
            self.assertEqual(
                validator.run_lifecycle(
                    tree.root, "wo:done", env=self.env(tmp), run=run),
                ["V: wo:done is not a lifecycle label in the taxonomy"])
            self.assertEqual(run.calls, [])

    def test_a_pr_citing_no_work_order_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
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
            run = gh(labels=["wo:in-progress"])
            body = ("Builds on WO-0004. This is WO-0005 (PRD-0001).\n\n"
                    "Closes #110\n")
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp, body=body), run=run)
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "110",
                "--add-label", "wo:merged",
                "--remove-label", "wo:in-progress"]])

    def test_a_fenced_citation_that_resolves_still_flips_the_label(self):
        """The passing direction, pinned before the skip gate narrows.

        Resolution reads the WHOLE body and keeps the work orders the PR
        actually closes, so a token quoted inside a fenced block still
        flips its issue when the Closes line backs it. The gate that
        judges a body's tokens a claim is reached only AFTER resolution
        fails, so nothing here may change when it narrows."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh(labels=["wo:needs-review", "size:M"])
            body = ("Fixes the row the detector printed:\n\n"
                    "```\n"
                    "- [x] **WO-0004** (PRD-0001) the row it printed\n"
                    "```\n\n"
                    "Closes #109\n")
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp, body=body), run=run)
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "109",
                "--add-label", "wo:merged",
                "--remove-label", "wo:needs-review"]])

    def test_a_nameless_label_entry_is_dropped_not_compared(self):
        # gh can answer `issue view` with a label entry carrying no usable
        # name. The seam (cli.label_names) drops it, so the lifecycle
        # transition never compares a non-name against the state machine
        # and the flip proceeds on the labels that ARE named.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = FakeGh(answers={
                ("issue", "view"): json.dumps({"labels": [
                    "junk", {"id": 4321},
                    {"name": "wo:needs-review"}, {"name": "size:M"}]}),
                ("api", "user"): "github-actions[bot]\n",
            })
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp), run=run)
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "edit", "109"), [[
                "issue", "edit", "109",
                "--add-label", "wo:merged",
                "--remove-label", "wo:needs-review"]])

    def test_a_failing_gh_call_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh(labels=["wo:needs-review"],
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
            run = gh()
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
            run = gh()
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
            run = gh(labels=["wo:in-progress"])
            problems = validator.run_lifecycle(
                tree.root, "wo:needs-review", env=self.env(tmp), run=run,
                uncited="skip")
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "109",
                "--add-label", "wo:needs-review",
                "--remove-label", "wo:in-progress"]])

    def test_the_relaxation_must_be_asked_for(self):
        # The FUNCTION default stays strict, so no caller gets the
        # relaxation by accident. Both Makefile targets ask for it
        # (ADR-0057) — TestLockstep in test_gates pins that they do.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
            problems = validator.run_lifecycle(
                tree.root, "wo:merged",
                env=self.env(tmp, body="chore: housekeeping"), run=run)
            self.assertEqual(
                problems, ["V: PR body cites no work-order id"])

    def test_the_merged_leg_skips_an_uncited_pr_too(self):
        # ADR-0057: the two legs agreed about a malformed citation and
        # disagreed about no citation, which left a housekeeping PR with
        # no body that could satisfy both — naming a work order failed
        # the open leg, naming none failed the merged leg.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
            problems = validator.run_lifecycle(
                tree.root, "wo:merged",
                env=self.env(tmp, body="chore: housekeeping"), run=run,
                uncited="skip")
            self.assertEqual(problems, [])
            self.assertEqual(run.calls, [])

    def test_the_merged_leg_keeps_a_malformed_citation_loud(self):
        # The relaxation is gated on the body naming NO work order, so
        # it cannot widen into the case the strictness actually exists
        # for: a body that names one which resolves to none.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
            problems = validator.run_lifecycle(
                tree.root, "wo:merged",
                env=self.env(tmp, body="Implements WO-0004."), run=run,
                uncited="skip")
            self.assertEqual(problems, [
                "V: PR body has no Closes #N link, so the work order it"
                " implements cannot be told from the ones it only"
                " mentions"])
            self.assertEqual(run.calls, [])

    def test_a_token_only_inside_a_fence_is_not_a_claim(self):
        """ADR-0064. The body pastes the detector output it is fixing;
        every work-order token in it is evidence, not an assertion, so
        the body claims no work order and the skip applies."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
            body = ("The detector printed this:\n\n"
                    "```\n"
                    "A: docs/features/demo/breakdown.md:7 work-order row"
                    " WO-0004 cites no PRD id\n"
                    "```\n\n"
                    "No work order: tightens a detector.\n")
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp, body=body),
                run=run, uncited="skip")
            self.assertEqual(problems, [])
            self.assertEqual(run.calls, [])

    def test_a_token_only_inside_a_blockquote_is_not_a_claim_either(self):
        # PR #330's shape: the body quoted a breakdown row it was
        # discussing, in a blockquote rather than a fence.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
            body = ("Quoting the row under discussion:\n\n"
                    "> - [x] **WO-0004** (PRD-0001) the row it printed\n\n"
                    "No work order: docs only.\n")
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp, body=body),
                run=run, uncited="skip")
            self.assertEqual(problems, [])
            self.assertEqual(run.calls, [])

    def test_a_tilde_fence_quotes_as_a_backtick_fence_does(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
            body = ("~~~\nsee WO-0004\n~~~\n\nNo work order: chore.\n")
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp, body=body),
                run=run, uncited="skip")
            self.assertEqual(problems, [])
            self.assertEqual(run.calls, [])

    def test_a_quoted_fence_inside_a_longer_fence_is_content(self):
        """one-fence-rule's repro: a four-backtick block quoting a markdown
        example. The inner ``` line is content, so the work-order line
        after it is still quoted and the body claims nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
            body = ("````markdown\n```\n"
                    "Implements WO-0004. Closes #999\n```\n````\n\n"
                    "No work order: docs only.\n")
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp, body=body),
                run=run, uncited="skip")
            self.assertEqual(problems, [])
            self.assertEqual(run.calls, [])

    def test_an_unterminated_fence_swallows_the_rest_of_the_body(self):
        """The conservative direction, asserted rather than assumed: an
        author who opens a fence and never closes it gets a skip, which
        is a no-op, rather than a flip of an issue nobody named."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
            body = "```\nsee WO-0004\n\nand then prose about WO-0004\n"
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp, body=body),
                run=run, uncited="skip")
            self.assertEqual(problems, [])
            self.assertEqual(run.calls, [])

    def test_inline_code_is_typography_not_quotation(self):
        """The boundary that must not move. Backticks around an id are how
        this repo writes identifiers in ordinary prose, genuine claims
        included, so an inline-code citation is still a citation and a
        body carrying one with no Closes line is still malformed."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
            problems = validator.run_lifecycle(
                tree.root, "wo:merged",
                env=self.env(tmp, body="Implements `WO-0004`."), run=run,
                uncited="skip")
            self.assertEqual(problems, [
                "V: PR body has no Closes #N link, so the work order it"
                " implements cannot be told from the ones it only"
                " mentions"])
            self.assertEqual(run.calls, [])

    def test_an_unparseable_issue_view_is_a_problem_not_a_traceback(self):
        # gh ran, exited 0, answered `issue view` with raw non-JSON.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = FakeGh(answers={("issue", "view"): "gh: banner text"})
            problems = validator.run_lifecycle(
                tree.root, "wo:merged", env=self.env(tmp), run=run)
            self.assertEqual(problems, [
                "V: gh issue view 109 returned unparseable JSON:"
                " Expecting value: line 1 column 1 (char 0)"])
            self.assertEqual(run.called("issue", "edit"), [])

    def test_a_non_object_issue_view_is_a_problem_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = FakeGh(answers={("issue", "view"): "[]"})
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
            run = gh(labels=["wo:ready-for-agent", "size:M"])
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
            run = gh(labels=["wo:in-progress"])
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
            run = gh(labels=["wo:blocked"])
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
            run = gh(labels=["size:M"])
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
            run = gh()
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
            run = gh(labels=["wo:in-progress"])
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
            run = gh(error=OSError("gh: not found"),
                     failing=["issue", "view"])
            self.assertEqual(
                validator.run_claim(
                    tree.root, "wo:in-progress", "109", env=env, run=run),
                ["V: gh issue view 109 failed: gh: not found"])
            self.assertEqual(self.outputs(env), "")


class TestRunOutcome(unittest.TestCase):
    """The dispatch failure leg (ADR-0045): the assembler's failure() step
    flips the order it claimed to wo:failed. Same KNOWN-issue flip as the
    claim, deliberately without the idempotency verdict — nothing runs
    after a failed job that could read one."""

    def tree(self, tmp):
        tree = FixtureTree(tmp)
        tree.write(".github/labels.json", json.dumps(
            [{"name": name, "color": "ededed", "description": "lifecycle"}
             for name in LIFECYCLE]
            + [{"name": "size:M", "color": "f4a261", "description": "size"}]))
        return tree

    def test_a_dispatched_order_lands_on_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh(labels=["wo:in-progress", "size:M"])
            problems = validator.run_outcome(
                tree.root, "wo:failed", "109", run=run)
            self.assertEqual(problems, [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "109",
                "--add-label", "wo:failed",
                "--remove-label", "wo:in-progress"]])

    def test_it_writes_no_verdict(self):
        # The claim's transitioned output is a dispatch decision. A step
        # that runs BECAUSE the job failed has no business casting one,
        # and no later step survives to read it.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            outputs = Path(tmp) / "outputs.txt"
            run = gh(labels=["wo:in-progress"])
            # run_outcome takes no env at all — the signature is the
            # guarantee. Nothing may appear at $GITHUB_OUTPUT.
            validator.run_outcome(tree.root, "wo:failed", "109", run=run)
            self.assertFalse(outputs.exists())

    def test_an_already_failed_order_is_a_no_op(self):
        # A re-run of a failed job must not churn the label.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh(labels=["wo:failed"])
            self.assertEqual(
                validator.run_outcome(tree.root, "wo:failed", "109",
                                      run=run), [])
            self.assertEqual(run.called("issue", "edit"), [])

    def test_a_label_outside_the_state_machine_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh()
            self.assertEqual(
                validator.run_outcome(tree.root, "wo:exploded", "109",
                                      run=run),
                ["V: wo:exploded is not a lifecycle label in the taxonomy"])
            self.assertEqual(run.calls, [])

    def test_a_taxonomy_without_the_ready_label_still_flips(self):
        # Unlike the claim, this leg never reasons about ready state, so a
        # taxonomy missing that label is none of its business — the failed
        # order still gets its terminal state.
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/labels.json", json.dumps(
                [{"name": name, "color": "ededed",
                  "description": "lifecycle"}
                 for name in LIFECYCLE if name != "wo:ready-for-agent"]))
            run = gh(labels=["wo:in-progress"])
            self.assertEqual(
                validator.run_outcome(tree.root, "wo:failed", "109",
                                      run=run), [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "109",
                "--add-label", "wo:failed",
                "--remove-label", "wo:in-progress"]])

    def test_a_failing_gh_call_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree(tmp)
            run = gh(error=OSError("gh: not found"),
                     failing=["issue", "view"])
            self.assertEqual(
                validator.run_outcome(tree.root, "wo:failed", "109",
                                      run=run),
                ["V: gh issue view 109 failed: gh: not found"])


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
                run=gh(labels=["wo:ready-for-agent"]))
            self.assertEqual(problems, [])
            written = Path(env["GITHUB_OUTPUT"]).read_text(encoding="utf-8")
        keys = {line.split("=", 1)[0]
                for line in written.splitlines() if "=" in line}
        self.assertLessEqual(refs, keys)


class TestParseLifecycle(unittest.TestCase):
    """The four lifecycle invocations (ADR-0032, ADR-0045): the merged leg
    (--label alone), the dispatch claim (--label --issue N), the failure
    leg (--label --issue N --verdict skip), and the PR-open leg (--label
    --uncited skip). Anything else is usage."""

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

    def test_the_verdict_form_takes_only_skip_and_a_numeric_issue(self):
        self.assertEqual(
            validator.parse(["lifecycle", "--label", "wo:failed",
                             "--issue", "42", "--verdict", "skip"]),
            ("lifecycle", {"label": "wo:failed", "issue": "42",
                           "verdict": "skip"}))
        self.assertEqual(
            validator.parse(["lifecycle", "--label", "wo:failed",
                             "--issue", "42", "--verdict", "write"]),
            (None, None))
        self.assertEqual(
            validator.parse(["lifecycle", "--label", "wo:failed",
                             "--issue", "abc", "--verdict", "skip"]),
            (None, None))

    def test_the_verdict_form_needs_its_issue(self):
        # "no verdict" is only meaningful for the KNOWN-issue legs; on a
        # PR-shaped invocation it is a confused caller.
        self.assertEqual(
            validator.parse(["lifecycle", "--label", "wo:failed",
                             "--verdict", "skip"]),
            (None, None))

    def test_the_claim_and_uncited_forms_do_not_combine(self):
        # A claim names its issue outright; "uncited" only means anything
        # for a PR-shaped resolution. Both at once is a confused caller.
        self.assertEqual(
            validator.parse(["lifecycle", "--label", "wo:in-progress",
                             "--issue", "42", "--uncited", "skip"]),
            (None, None))


class TestMain(cli_contract.CliContract, cli_contract.ReportContract,
               unittest.TestCase):
    usage_fragment = "python3 validator.py review"
    summary_line = "validator: 0 problem(s)"

    def run_cli(self, argv):
        return cli_contract.capture(validator.main, argv, env={},
                                    run=gh())

    def clean_cli(self):
        # The claim leg needs no PR event; a ready issue flips cleanly.
        return cli_contract.capture(
            validator.main,
            ["lifecycle", "--label", "wo:in-progress", "--issue", "7"],
            env={}, run=gh(labels=["wo:ready-for-agent"]))

    def test_a_non_numeric_status_is_a_usage_error(self):
        self.assertEqual(
            self.run_cli(["review", "--status", "red"])[0], 2)

    def test_a_digit_that_int_refuses_is_a_usage_error_not_a_traceback(self):
        """str.isdigit() is true for '\u00b2' and int() refuses it, so the
        guard above let a ValueError out of parse(). U+00B2 is latin-1
        byte 0xB2 — ordinary bad input, not a contrivance. STATUS comes
        from `make review STATUS=$FINDINGS_RC`, a shell variable."""
        self.assertEqual(
            self.run_cli(["review", "--status", "\u00b2"])[0], 2)

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
        run = gh(labels=["wo:ready-for-agent"])
        code, out = cli_contract.capture(
            validator.main,
            ["lifecycle", "--label", "wo:in-progress", "--issue", "7"],
            env={}, run=run)
        self.assertEqual(code, 0)
        self.assertEqual(run.called("issue", "edit"), [[
            "issue", "edit", "7",
            "--add-label", "wo:in-progress",
            "--remove-label", "wo:ready-for-agent"]])

    def test_a_verdict_skip_invocation_routes_past_the_pr_event(self):
        # Like the claim, the failure leg names its issue outright: no
        # event payload in env, and it must still reach run_outcome.
        run = gh(labels=["wo:in-progress"])
        code, out = cli_contract.capture(
            validator.main,
            ["lifecycle", "--label", "wo:failed", "--issue", "7",
             "--verdict", "skip"],
            env={}, run=run)
        self.assertEqual(code, 0)
        self.assertEqual(run.called("issue", "edit"), [[
            "issue", "edit", "7",
            "--add-label", "wo:failed",
            "--remove-label", "wo:in-progress"]])

    def test_an_uncited_skip_invocation_is_still_pr_shaped(self):
        # --uncited skip relaxes the citation, not the event: outside a
        # pull_request payload it is still a config error.
        code, out = self.run_cli(["lifecycle", "--label", "wo:needs-review",
                                  "--uncited", "skip"])
        self.assertEqual(code, 1)
        self.assertIn("V: no pull_request in the CI event payload", out)


class TestPrEvent(unittest.TestCase):
    """The dispatch shim (WO-0030). GitHub suppresses the pull_request
    event for a PR the factory's own token opened, so the validator is
    dispatched against a PR NUMBER — and the PR-shaped legs still need
    an event to read. Three workflow steps used to build that payload by
    hand, in three copies the one test over them could not tell apart
    (an assertIn over the whole file passes while two of three are
    wrong). The shape lives here now, and every test below reads it back
    through cli.read_event — the parser its consumers actually use —
    rather than through a second copy of the same literal."""

    PR = json.dumps({"number": 7, "body": "Closes #108",
                     "user": {"login": "someone"}})

    def write(self, tmp, answers=None, failing=None, env=None, number="7"):
        """(path, problems, gh) for one shim invocation."""
        path = Path(tmp) / "pr-event.json"
        run = FakeGh(answers={("api",): self.PR} if answers is None
                     else answers, failing=failing)
        problems = validator.write_pr_event(
            number, str(path),
            env={"GITHUB_REPOSITORY": "owner/repo"} if env is None else env,
            run=run)
        return path, problems, run

    def test_the_payload_is_what_read_event_hands_its_consumers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, problems, _ = self.write(tmp)
            self.assertEqual(problems, [])
            event, error = cli.read_event({"GITHUB_EVENT_PATH": str(path)})
            self.assertIsNone(error)
            self.assertEqual(event["action"], "opened")
            self.assertEqual(event["pull_request"]["body"], "Closes #108")

    def test_the_pr_is_read_from_the_repository_the_environment_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, run = self.write(tmp, number="42")
            self.assertEqual(run.calls,
                             [["api", "repos/owner/repo/pulls/42"]])

    def test_an_unset_repository_is_refused_before_gh_is_called(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, problems, run = self.write(tmp, env={})
            self.assertEqual(problems, [
                "V: GITHUB_REPOSITORY is unset — nothing names the PR to read"])
            self.assertEqual(run.calls, [])
            self.assertFalse(path.exists())

    def test_a_failed_gh_leaves_no_event_behind(self):
        # Half an event is worse than none: read_event would parse it
        # and every consumer would see a PR with no body.
        with tempfile.TemporaryDirectory() as tmp:
            path, problems, _ = self.write(tmp, failing=["api"])
            self.assertEqual(
                problems, ["V: gh api pull #7 failed: boom"])
            self.assertFalse(path.exists())

    def test_a_response_that_is_not_a_pr_object_leaves_no_event_behind(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, problems, _ = self.write(tmp, answers={("api",): "[]"})
            self.assertEqual(problems, [
                "V: gh api pull #7 returned list where dict was expected"])
            self.assertFalse(path.exists())

    def test_an_unwritable_destination_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "no-such-dir" / "pr-event.json"
            run = FakeGh(answers={("api",): self.PR})
            problems = validator.write_pr_event(
                "7", str(path), env={"GITHUB_REPOSITORY": "owner/repo"},
                run=run)
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                f"V: cannot write the event payload to {path}: "), problems)

    def test_the_cli_writes_the_event_for_a_dispatched_pr(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pr-event.json"
            run = FakeGh(answers={("api",): self.PR})
            code = validator.main(
                ["pr-event", "--pr", "7", "--out", str(path)],
                env={"GITHUB_REPOSITORY": "owner/repo"}, run=run)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")),
                             {"action": "opened",
                              "pull_request": json.loads(self.PR)})

    def test_a_non_numeric_pr_is_usage_not_a_gh_call(self):
        run = FakeGh()
        self.assertEqual(
            validator.main(["pr-event", "--pr", "x", "--out", "e.json"],
                           env={}, run=run), 2)
        self.assertEqual(run.calls, [])

    def test_both_options_are_required(self):
        for argv in (["pr-event", "--pr", "7"], ["pr-event", "--out", "e"],
                     ["pr-event"]):
            with self.subTest(argv=argv):
                self.assertEqual(validator.parse(argv), (None, None))


if __name__ == "__main__":
    unittest.main()
