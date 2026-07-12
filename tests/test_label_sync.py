"""label_sync.py (detector L, LABEL-SYNC) — pure-function + fixture tests.

Same discipline as test_factory_gates/test_factory_init: every function is
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

import label_sync

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
    "budget-exhausted", "needs-human", "blueprint-drift",
}

MISSING_PROBLEM = ("L: missing labels.json (.github/labels.json or"
                   " factory/templates/.github/labels.json)")


def taxonomy():
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


class FixtureTree:
    def __init__(self, root):
        self.root = Path(root)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


class RecordingRunner:
    """Injected gh runner: records every call, answers `label list` with a
    canned listing, and never touches the network."""

    def __init__(self, listing):
        self.listing = listing
        self.calls = []

    def __call__(self, args):
        self.calls.append(list(args))
        if args[:2] == ["label", "list"]:
            return json.dumps(self.listing)
        return ""


class FailingRunner(RecordingRunner):
    """Injected gh runner that fails the way a real gh does: raises the
    exception `subprocess.run(check=True)` / a missing binary would."""

    def __init__(self, listing, error, failing=("label", "list")):
        super().__init__(listing)
        self.error = error
        self.failing = list(failing)

    def __call__(self, args):
        self.calls.append(list(args))
        if list(args[:len(self.failing)]) == self.failing:
            raise self.error
        if args[:2] == ["label", "list"]:
            return json.dumps(self.listing)
        return ""


class TestTaxonomyTemplate(unittest.TestCase):
    def test_template_parses_with_exactly_the_27_names(self):
        labels = taxonomy()
        self.assertEqual(len(labels), 27)
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


class TestPlan(unittest.TestCase):
    def test_empty_current_recreates_the_full_taxonomy(self):
        desired = taxonomy()
        problems = label_sync.plan([], desired)
        self.assertEqual(problems, [f"L: missing label {label['name']}"
                                    for label in desired])
        self.assertEqual(len(problems), 27)

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
            runner = RecordingRunner([self.DESIRED[1]])
            problems = label_sync.sync(tree.root, run=runner)
            self.assertEqual(problems, ["L: missing label wo:draft"])
            self.assertEqual(runner.calls, [self.LIST_CALL])

    def test_clean_repo_reports_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            runner = RecordingRunner(self.DESIRED)
            self.assertEqual(label_sync.sync(tree.root, run=runner), [])
            self.assertEqual(runner.calls, [self.LIST_CALL])

    def test_apply_force_creates_only_drifted_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            runner = RecordingRunner([
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
            runner = RecordingRunner([])
            problems = label_sync.sync(tree.root, apply=True, run=runner)
            self.assertEqual(problems, [
                "L: .github/labels.json must be a non-empty JSON array"
                " of label entries"])
            self.assertEqual(runner.calls, [])

    def test_failing_gh_list_reports_stderr_not_a_traceback(self):
        # gh present but unauthenticated / rate-limited: check=True raises.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            runner = FailingRunner([], subprocess.CalledProcessError(
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
            runner = FailingRunner([], error)
            problems = label_sync.sync(tree.root, run=runner)
            self.assertEqual(problems, [
                f"L: gh label list failed: {error}"])

    def test_failing_gh_create_reports_per_label_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.tree_with_template(tmp)
            runner = FailingRunner(
                [self.DESIRED[1]],
                subprocess.CalledProcessError(
                    1, ["gh", "label", "create"],
                    stderr="HTTP 403: rate limit exceeded\n"),
                failing=("label", "create"))
            problems = label_sync.sync(tree.root, apply=True, run=runner)
            self.assertEqual(problems, [
                "L: missing label wo:draft",
                "L: gh label create wo:draft failed:"
                " HTTP 403: rate limit exceeded"])


class TestCli(unittest.TestCase):
    def run_main(self, argv, runner):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = label_sync.main(argv, run=runner)
        return code, buf.getvalue()

    def test_clean_run_prints_zero_and_exits_zero(self):
        desired, problems = label_sync.load_labels(REPO_ROOT)
        self.assertEqual(problems, [])
        code, out = self.run_main([], RecordingRunner(desired))
        self.assertEqual(code, 0)
        self.assertEqual(out, "label-sync: 0 problem(s)\n")

    def test_drift_prints_problems_and_exits_one(self):
        code, out = self.run_main([], RecordingRunner([]))
        self.assertEqual(code, 1)
        lines = out.splitlines()
        self.assertEqual(len(lines), 28)
        self.assertEqual(lines[0], "L: missing label wo:draft")
        self.assertEqual(lines[-1], "label-sync: 27 problem(s)")

    def test_unknown_argument_prints_usage(self):
        code, out = self.run_main(["--bogus"], RecordingRunner([]))
        self.assertEqual(code, 2)
        self.assertIn("label-sync", out)


if __name__ == "__main__":
    unittest.main()
