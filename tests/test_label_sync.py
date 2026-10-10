"""label_sync.py (detector L, LABEL-SYNC) — pure-function + fixture tests.

Same discipline as test_gates/test_factory_init: every function is
exercised through its public interface, tests assert the EXACT problem
strings callers will print, and the gh runner is injected so no test ever
touches the network.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import label_sync

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling fixture_tree import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_gh import FakeGh  # noqa: E402
from fixture_tree import FixtureTree  # noqa: E402
import cli_contract  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT / "factory" / "templates" / ".github" / "labels.json"

# The full 27-label work-order taxonomy, pinned by name: 9 wo:*, 3 size:*,
# 3 risk:*, 5 type:*, 4 source:*, 3 flags.
EXPECTED_NAMES = {
    "wo:draft", "wo:prd-approved", "wo:blueprint-approved",
    "wo:ready-for-agent", "wo:in-progress", "wo:needs-review",
    "wo:merged", "wo:failed", "wo:blocked",
    "size:S", "size:M", "size:L",
    "risk:low", "risk:med", "risk:high",
    "type:feature", "type:defect", "type:chore", "type:support",
    "type:sweep",
    "source:human", "source:sentry", "source:validator", "source:sweep",
    "pipeline-intake",
    "budget-exhausted", "needs-human", "blueprint-drift",
}

MISSING_PROBLEM = ("L: missing labels.json (.github/labels.json or"
                   " factory/templates/.github/labels.json)")


def taxonomy():
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def gh(listing, **kwargs):
    """A fake gh for label-sync traffic: `label list` answers with the
    canned listing (failure declared via FakeGh's failing=/error=)."""
    return FakeGh(answers={("label", "list"): json.dumps(listing)},
                  **kwargs)


class TestTaxonomyTemplate(unittest.TestCase):
    def test_template_parses_with_exactly_the_28_names(self):
        labels = taxonomy()
        self.assertEqual(len(labels), 28)
        self.assertEqual({label["name"] for label in labels}, EXPECTED_NAMES)
        for label in labels:
            self.assertEqual(sorted(label), ["color", "description", "name"],
                             f"bad shape for {label}")
            for field in ("name", "color", "description"):
                self.assertIsInstance(label[field], str)
                self.assertTrue(label[field], f"empty {field} in {label}")


class TestLoadLabels(unittest.TestCase):
    def test_falls_back_to_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/.github/labels.json", json.dumps(
                [{"name": "wo:draft", "color": "ededed",
                  "description": "d"}]))
            labels, problems = label_sync.load_labels(tree.root)
            self.assertEqual(problems, [])
            self.assertEqual(labels, [{"name": "wo:draft", "color": "ededed",
                                       "description": "d"}])

    def test_prefers_installed_copy_over_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/labels.json", json.dumps(
                [{"name": "installed", "color": "aaaaaa",
                  "description": "d"}]))
            tree.write("factory/templates/.github/labels.json", json.dumps(
                [{"name": "template", "color": "bbbbbb",
                  "description": "d"}]))
            labels, problems = label_sync.load_labels(tree.root)
            self.assertEqual(problems, [])
            self.assertEqual([label["name"] for label in labels],
                             ["installed"])

    def test_missing_everywhere_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            labels, problems = label_sync.load_labels(Path(tmp))
            self.assertEqual(labels, [])
            self.assertEqual(problems, [MISSING_PROBLEM])

    def test_malformed_json_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/labels.json", "{nope")
            try:
                json.loads("{nope")
            except json.JSONDecodeError as err:
                expected = f"L: .github/labels.json is not valid JSON: {err}"
            labels, problems = label_sync.load_labels(tree.root)
            self.assertEqual(labels, [])
            self.assertEqual(problems, [expected])

    def test_a_taxonomy_that_is_not_utf8_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".github" / "labels.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'[{"name": "caf\xe9"}]')
            labels, problems = label_sync.load_labels(Path(tmp))
            self.assertEqual(labels, [])
            self.assertEqual(problems, [
                "L: .github/labels.json is not valid JSON: 'utf-8' codec"
                " can't decode byte 0xe9 in position 14: invalid"
                " continuation byte"])

    def test_non_array_and_empty_array_are_flagged(self):
        for payload in ("{}", "[]"):
            with tempfile.TemporaryDirectory() as tmp:
                tree = FixtureTree(tmp)
                tree.write(".github/labels.json", payload)
                labels, problems = label_sync.load_labels(tree.root)
                self.assertEqual(labels, [])
                self.assertEqual(problems, [
                    "L: .github/labels.json must be a non-empty JSON array"
                    " of label entries"])

    def test_a_string_and_a_null_are_flagged_the_same_way(self):
        """The loader's own shape wording covers every top level that is
        not a non-empty array — null included, which is why it keeps its
        own check rather than asking cli.read_file for a shape."""
        for payload in ('"labels"', "null"):
            with self.subTest(payload=payload), \
                    tempfile.TemporaryDirectory() as tmp:
                tree = FixtureTree(tmp)
                tree.write(".github/labels.json", payload)
                self.assertEqual(label_sync.load_labels(tree.root), ([], [
                    "L: .github/labels.json must be a non-empty JSON array"
                    " of label entries"]))

    def test_an_empty_taxonomy_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/labels.json", "")
            self.assertEqual(label_sync.load_labels(tree.root), ([], [
                "L: .github/labels.json is not valid JSON: Expecting value:"
                " line 1 column 1 (char 0)"]))

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-000 file")
    def test_a_taxonomy_the_process_may_not_read_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            path = tree.write(".github/labels.json", "[]")
            path.chmod(0)
            try:
                self.assertEqual(label_sync.load_labels(tree.root), ([], [
                    "L: cannot read .github/labels.json: [Errno 13]"
                    f" Permission denied: '{path}'"]))
            finally:
                path.chmod(0o644)

    def test_entry_lacking_fields_is_flagged_and_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/labels.json", json.dumps(
                [{"name": "wo:draft"},
                 {"name": "size:S", "color": "f9d0c4",
                  "description": "Budget class S (~$5)"},
                 "not-a-dict"]))
            labels, problems = label_sync.load_labels(tree.root)
            self.assertEqual(problems, [
                "L: .github/labels.json[0] entry lacks color, description",
                "L: .github/labels.json[2] entry lacks name, color,"
                " description"])
            self.assertEqual([label["name"] for label in labels], ["size:S"])

    def test_duplicate_name_is_flagged_and_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/labels.json", json.dumps(
                [{"name": "size:S", "color": "f9d0c4",
                  "description": "Budget class S (~$5)"},
                 {"name": "size:M", "color": "f9d0c4",
                  "description": "Budget class M (~$15)"},
                 {"name": "size:S", "color": "ffffff",
                  "description": "second definition wins on GitHub"}]))
            labels, problems = label_sync.load_labels(tree.root)
            self.assertEqual(problems, [
                "L: .github/labels.json[2] duplicate label name size:S"])
            self.assertEqual([label["name"] for label in labels],
                             ["size:S", "size:M"])


class TestTaxonomyPath(unittest.TestCase):
    """Where the taxonomy lives, asked once.

    load_labels resolved this inline and was the only thing that knew
    the answer, so detector J — which needs to tell an absent taxonomy
    (nothing to be wrong about) from an unreadable one (very much
    something to be wrong about) — had no way to ask without walking
    the candidates itself. A second walk is a second answer waiting to
    happen, which is the thing J's own docstring says it will not do.
    """

    ENTRY = [{"name": "wo:draft", "color": "ededed", "description": "d"}]

    def test_it_resolves_the_installed_copy_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/labels.json", json.dumps(self.ENTRY))
            tree.write("factory/templates/.github/labels.json",
                       json.dumps(self.ENTRY))
            self.assertEqual(label_sync.taxonomy_path(tree.root),
                             tree.root / ".github" / "labels.json")

    def test_it_falls_back_to_the_template_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/.github/labels.json",
                       json.dumps(self.ENTRY))
            self.assertEqual(
                label_sync.taxonomy_path(tree.root),
                tree.root / "factory" / "templates" / ".github"
                / "labels.json")

    def test_it_is_none_when_no_candidate_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(label_sync.taxonomy_path(Path(tmp)))

    def test_load_labels_reports_against_the_path_it_resolves(self):
        """The two must never name different files. Asserted through
        the problem string, which is the only place load_labels says
        out loud which file it read."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/labels.json", "{nope")
            tree.write("factory/templates/.github/labels.json",
                       json.dumps(self.ENTRY))
            resolved = label_sync.taxonomy_path(tree.root)
            _, problems = label_sync.load_labels(tree.root)
            self.assertEqual(len(problems), 1)
            self.assertTrue(
                problems[0].startswith(
                    f"L: {resolved.relative_to(tree.root).as_posix()} "),
                problems)

    def test_the_shipped_repo_resolves_its_payload_copy(self):
        self.assertEqual(
            label_sync.taxonomy_path(REPO_ROOT),
            REPO_ROOT / "factory" / "templates" / ".github" / "labels.json")


class TestPlan(unittest.TestCase):
    def test_empty_current_recreates_the_full_taxonomy(self):
        desired = taxonomy()
        problems = label_sync.plan([], desired)
        self.assertEqual(problems, [f"L: missing label {label['name']}"
                                    for label in desired])
        self.assertEqual(len(problems), 28)

    def test_tampered_color_yields_exact_mismatch_line(self):
        desired = taxonomy()
        current = [dict(label) for label in desired]
        [size_s] = [label for label in current if label["name"] == "size:S"]
        size_s["color"] = "ffffff"
        self.assertEqual(label_sync.plan(current, desired), [
            "L: label size:S color ffffff, want f9d0c4"])

    def test_tampered_description_yields_exact_mismatch_line(self):
        desired = taxonomy()
        current = [dict(label) for label in desired]
        [flag] = [label for label in current
                  if label["name"] == "needs-human"]
        flag["description"] = "oops"
        self.assertEqual(label_sync.plan(current, desired), [
            "L: label needs-human description 'oops',"
            " want 'Flag: agent escalation'"])

    def test_color_case_is_not_drift(self):
        # GitHub returns whatever case the color was created with — this
        # repo already carries 0E8A16 — so hex case alone must not drift.
        desired = taxonomy()
        current = [dict(label, color=label["color"].upper())
                   for label in desired]
        self.assertEqual(label_sync.plan(current, desired), [])

    def test_non_taxonomy_labels_are_ignored(self):
        desired = taxonomy()
        current = [dict(label) for label in desired] + [
            {"name": "bug", "color": "d73a4a",
             "description": "Something isn't working"},
            {"name": "duplicate", "color": "cfd3d7",
             "description": "This issue or pull request already exists"}]
        self.assertEqual(label_sync.plan(current, desired), [])


class TestSync(unittest.TestCase):
    DESIRED = [
        {"name": "wo:draft", "color": "ededed",
         "description": "WO lifecycle: mirrored, awaiting PRD approval"},
        {"name": "size:S", "color": "f9d0c4",
         "description": "Budget class S (~$5)"},
    ]
    LIST_CALL = ["label", "list", "--json", "name,color,description",
                 "--limit", "1000"]

    def tree_with_template(self, tmp):
        tree = FixtureTree(tmp)
        tree.write("factory/templates/.github/labels.json",
                   json.dumps(self.DESIRED))
        return tree

    def test_report_lists_drift_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            runner = gh([self.DESIRED[1]])
            problems = label_sync.sync(tree.root, run=runner)
            self.assertEqual(problems, ["L: missing label wo:draft"])
            self.assertEqual(runner.calls, [self.LIST_CALL])

    def test_clean_repo_reports_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            runner = gh(self.DESIRED)
            self.assertEqual(label_sync.sync(tree.root, run=runner), [])
            self.assertEqual(runner.calls, [self.LIST_CALL])

    def test_apply_force_creates_only_drifted_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            runner = gh([
                {"name": "size:S", "color": "ffffff",
                 "description": "Budget class S (~$5)"}])
            problems = label_sync.sync(tree.root, apply=True, run=runner)
            self.assertEqual(problems, [
                "L: missing label wo:draft",
                "L: label size:S color ffffff, want f9d0c4"])
            self.assertEqual(runner.calls, [
                self.LIST_CALL,
                ["label", "create", "wo:draft", "--force",
                 "--color", "ededed", "--description",
                 "WO lifecycle: mirrored, awaiting PRD approval"],
                ["label", "create", "size:S", "--force",
                 "--color", "f9d0c4", "--description",
                 "Budget class S (~$5)"]])

    def test_load_problems_short_circuit_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/labels.json", "[]")
            runner = gh([])
            problems = label_sync.sync(tree.root, apply=True, run=runner)
            self.assertEqual(problems, [
                "L: .github/labels.json must be a non-empty JSON array"
                " of label entries"])
            self.assertEqual(runner.calls, [])

    def test_failing_gh_list_reports_stderr_not_a_traceback(self):
        # gh present but unauthenticated / rate-limited: check=True raises.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            runner = gh([], failing=("label", "list"),
                        error=subprocess.CalledProcessError(
                            1, ["gh", "label", "list"],
                            stderr="gh: Bad credentials (HTTP 401)\n"))
            problems = label_sync.sync(tree.root, run=runner)
            self.assertEqual(problems, [
                "L: gh label list failed: gh: Bad credentials (HTTP 401)"])
            self.assertEqual(runner.calls, [self.LIST_CALL])

    def test_missing_gh_binary_reports_the_os_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            error = FileNotFoundError(2, "No such file or directory")
            error.filename = "gh"
            runner = gh([], failing=("label", "list"), error=error)
            problems = label_sync.sync(tree.root, run=runner)
            self.assertEqual(problems, [
                f"L: gh label list failed: {error}"])

    def test_unparseable_gh_list_is_a_problem_not_a_traceback(self):
        # gh ran, exited 0, said raw non-JSON nonsense (a banner).
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            runner = FakeGh(answers={("label", "list"): "gh: banner text"})
            problems = label_sync.sync(tree.root, apply=True, run=runner)
            self.assertEqual(problems, [
                "L: gh label list returned unparseable JSON: Expecting"
                " value: line 1 column 1 (char 0)"])
            self.assertEqual(runner.calls, [self.LIST_CALL])

    def test_a_non_list_gh_listing_is_a_problem_not_fake_drift(self):
        # A dict here must short-circuit: comparing the taxonomy against
        # nonsense would report every label as missing drift (and, with
        # apply, force-create the whole taxonomy off nonsense).
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            runner = FakeGh(answers={("label", "list"): "{}"})
            problems = label_sync.sync(tree.root, apply=True, run=runner)
            self.assertEqual(problems, [
                "L: gh label list returned dict where list was expected"])
            self.assertEqual(runner.calls, [self.LIST_CALL])

    def test_a_full_label_window_is_reported_alongside_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            runner = gh(
                [self.DESIRED[1]]
                + [{"name": f"noise:{n}", "color": "ededed",
                    "description": "noise"}
                   for n in range(label_sync.LIST_WINDOW - 1)])
            problems = label_sync.sync(tree.root, run=runner)
            self.assertEqual(problems, [
                "L: gh label list returned a full"
                f" {label_sync.LIST_WINDOW}-entry window — older entries"
                " are invisible; raise the window or narrow the query",
                "L: missing label wo:draft"])

    def test_failing_gh_create_reports_per_label_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            runner = gh([self.DESIRED[1]], failing=("label", "create"),
                        error=subprocess.CalledProcessError(
                            1, ["gh", "label", "create"],
                            stderr="HTTP 403: rate limit exceeded\n"))
            problems = label_sync.sync(tree.root, apply=True, run=runner)
            self.assertEqual(problems, [
                "L: missing label wo:draft",
                "L: gh label create wo:draft failed:"
                " HTTP 403: rate limit exceeded"])


class TestCli(cli_contract.CliContract, cli_contract.ReportContract,
              unittest.TestCase):
    usage_fragment = "label-sync"
    bad_argv = ("--bogus",)  # the tool has flags, not subcommands
    summary_line = "label-sync: 0 problem(s)"

    def run_cli(self, argv, runner=None):
        return cli_contract.capture(
            label_sync.main, argv,
            run=runner if runner is not None else gh([]))

    def clean_cli(self):
        desired, _ = label_sync.load_labels(REPO_ROOT)
        return self.run_cli([], gh(desired))

    def test_clean_run_prints_zero_and_exits_zero(self):
        desired, problems = label_sync.load_labels(REPO_ROOT)
        self.assertEqual(problems, [])
        code, out = self.run_cli([], gh(desired))
        self.assertEqual(code, 0)
        self.assertEqual(out, "label-sync: 0 problem(s)\n")

    def test_drift_prints_problems_and_exits_one(self):
        code, out = self.run_cli([], gh([]))
        self.assertEqual(code, 1)
        lines = out.splitlines()
        self.assertEqual(len(lines), 29)
        self.assertEqual(lines[0], "L: missing label wo:draft")
        self.assertEqual(lines[-1], "label-sync: 28 problem(s)")



if __name__ == "__main__":
    unittest.main()
