"""validator.py's four lifecycle verbs — claim, fail, pr-opened,
pr-merged — each at its own interface (issue #859).

Each verb names the one label its leg writes and owns its leg's
uncited-PR rule (ADR-0057, amended by ADR-0064) in code. Which label
went with which leg, and which legs skipped an uncited PR, used to be
said by the Makefile recipes' flags; a recipe that dropped
`--uncited skip` reddened four consecutive post-merge runs (#302-#306).
These pin the pairing where it now lives, so a verb cannot be handed
another leg's label or policy.

Same discipline as test_validator: exact problem strings, gh injected.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import validator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture_tree import FixtureTree  # noqa: E402
from test_validator import BREAKDOWN, LIFECYCLE, gh, pr_env  # noqa: E402
import cli_contract  # noqa: E402

HOUSEKEEPING = "chore: housekeeping"
MALFORMED = "Implements WO-0004."
CITED = "WO-0004 (PRD-0001 §Solution) Closes #109"
NO_CLOSES = ("V: PR body has no Closes #N link, so the work order it"
             " implements cannot be told from the ones it only mentions")


def tree(tmp):
    tree = FixtureTree(tmp)
    tree.write("docs/features/demo/breakdown.md", BREAKDOWN)
    tree.write(".github/labels.json", json.dumps(
        [{"name": name, "color": "ededed", "description": "lifecycle"}
         for name in LIFECYCLE]
        + [{"name": "size:M", "color": "f4a261", "description": "size"}]))
    return tree


def pr(tmp, body):
    return pr_env(tmp, number=42, body=body, merged=True,
                  user={"login": "mattb"})


class TestParseVerbs(unittest.TestCase):
    """A verb's arguments are its issue or nothing: no flag picks the
    leg, so no flag combination can pick the wrong one."""

    def test_the_issue_verbs_take_one_numeric_issue(self):
        for verb in ("claim", "fail"):
            with self.subTest(verb=verb):
                self.assertEqual(validator.parse([verb, "5"]),
                                 (verb, {"issue": "5"}))

    def test_the_pr_verbs_take_nothing(self):
        for verb in ("pr-opened", "pr-merged"):
            with self.subTest(verb=verb):
                self.assertEqual(validator.parse([verb]), (verb, {}))

    def test_anything_else_is_usage(self):
        # An empty $(ISSUE) reaches the CLI as a bare verb, and must
        # stay usage (exit 2) as it was under the --issue grammar.
        for argv in (["claim"], ["fail"], ["claim", "x"], ["claim", "²"],
                     ["claim", "5", "6"], ["claim", "--issue", "5"],
                     ["fail", "5", "--verdict", "skip"], ["pr-merged", "5"],
                     ["pr-opened", "--uncited", "skip"],
                     ["pr-merged", "--label", "wo:in-progress"]):
            with self.subTest(argv=argv):
                self.assertEqual(validator.parse(argv), (None, None))


class TestLegLabels(unittest.TestCase):
    """The label a leg writes is the verb's, not the caller's."""

    def test_the_merge_legs_write_the_merge_gates_labels(self):
        # pr-opened enters the merge gate's queue; pr-merged records its
        # pass — the two labels human_gates' digest reads that gate by.
        merge = next(g for g in validator.GATES if g.name == "merge")
        self.assertEqual((merge.queue, merge.passed),
                         ("wo:needs-review", "wo:merged"))

    def test_pr_opened_flips_the_cited_order_to_needs_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(labels=["wo:in-progress"])
            self.assertEqual(validator.pr_opened(
                tree(tmp).root, env=pr(tmp, CITED), run=run), [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "109", "--add-label", "wo:needs-review",
                "--remove-label", "wo:in-progress"]])

    def test_pr_merged_flips_the_cited_order_to_merged(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(labels=["wo:needs-review", "size:M"])
            self.assertEqual(validator.pr_merged(
                tree(tmp).root, env=pr(tmp, CITED), run=run), [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "109", "--add-label", "wo:merged",
                "--remove-label", "wo:needs-review"]])

    def test_claim_takes_a_ready_order_to_in_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"GITHUB_OUTPUT": str(Path(tmp) / "outputs.txt")}
            run = gh(labels=["wo:ready-for-agent", "size:M"])
            self.assertEqual(validator.claim(
                tree(tmp).root, "109", env=env, run=run), [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "109", "--add-label", "wo:in-progress",
                "--remove-label", "wo:ready-for-agent"]])
            self.assertEqual(Path(env["GITHUB_OUTPUT"]).read_text(
                encoding="utf-8"), "transitioned=true\n")

    def test_fail_lands_the_order_on_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = gh(labels=["wo:in-progress", "size:M"])
            self.assertEqual(validator.fail(
                tree(tmp).root, "109", run=run), [])
            self.assertEqual(run.called("issue", "edit"), [[
                "issue", "edit", "109", "--add-label", "wo:failed",
                "--remove-label", "wo:in-progress"]])


class TestUncitedPolicy(unittest.TestCase):
    """ADR-0057: both PR legs make a PR citing no work order a silent
    no-op, and both keep a malformed citation loud. The verbs own that
    rule — there is no flag left to forget."""

    LEGS = ("pr_opened", "pr_merged")

    def test_both_pr_legs_skip_a_pr_citing_no_work_order(self):
        for leg in self.LEGS:
            with self.subTest(leg=leg), tempfile.TemporaryDirectory() as tmp:
                run = gh()
                self.assertEqual(getattr(validator, leg)(
                    tree(tmp).root, env=pr(tmp, HOUSEKEEPING), run=run), [])
                self.assertEqual(run.calls, [])

    def test_both_pr_legs_keep_a_malformed_citation_loud(self):
        # The skip fires only when the body claims no work order; one
        # that names an order resolving to none is a malformed WO PR.
        for leg in self.LEGS:
            with self.subTest(leg=leg), tempfile.TemporaryDirectory() as tmp:
                run = gh()
                self.assertEqual(getattr(validator, leg)(
                    tree(tmp).root, env=pr(tmp, MALFORMED), run=run),
                    [NO_CLOSES])
                self.assertEqual(run.calls, [])


class TestVerbRouting(unittest.TestCase):
    """main hands each verb to its own leg."""

    def cli(self, argv, run, env=None):
        return cli_contract.capture(validator.main, argv,
                                    env={} if env is None else env, run=run)

    def test_claim_names_its_issue_and_needs_no_pr_event(self):
        run = gh(labels=["wo:ready-for-agent"])
        code, _ = self.cli(["claim", "7"], run)
        self.assertEqual(code, 0)
        self.assertEqual(run.called("issue", "edit"), [[
            "issue", "edit", "7", "--add-label", "wo:in-progress",
            "--remove-label", "wo:ready-for-agent"]])

    def test_fail_names_its_issue_and_needs_no_pr_event(self):
        run = gh(labels=["wo:in-progress"])
        code, _ = self.cli(["fail", "7"], run)
        self.assertEqual(code, 0)
        self.assertEqual(run.called("issue", "edit"), [[
            "issue", "edit", "7", "--add-label", "wo:failed",
            "--remove-label", "wo:in-progress"]])

    def test_the_pr_verbs_are_pr_shaped(self):
        for verb in ("pr-opened", "pr-merged"):
            with self.subTest(verb=verb):
                code, out = self.cli([verb], gh())
                self.assertEqual(code, 1)
                self.assertIn("V: no pull_request in the CI event payload",
                              out)

    def test_an_empty_issue_is_usage(self):
        for verb in ("claim", "fail"):
            with self.subTest(verb=verb):
                self.assertEqual(self.cli([verb], gh())[0], 2)


if __name__ == "__main__":
    unittest.main()
