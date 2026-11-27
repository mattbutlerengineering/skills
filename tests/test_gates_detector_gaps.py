"""Reproduced gate-detector gaps (fail-open shapes an audit found): H, M
and O reading HTML-comment content as visible, H's verdict label read
too narrowly, F passing an effort table dispatch rejects, E standing its
mirror half down on a marker alone, K's status read by one spelling, O
crediting one section's citation to another, and selftest rows that
stayed green with a sub-rule dead.

Same discipline as test_gates: public interfaces, exact problem strings.
"""
import hashlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import factory_config
import gates
import gates_selftest as fixtures

sys.path.insert(0, str(Path(__file__).resolve().parent))
from factory_fixture import CONFIG  # noqa: E402
from fixture_tree import FixtureTree  # noqa: E402
import linear_time  # noqa: E402

FM = "---\nstage: verify\ndate: 2026-11-01\n---\n"
NEVER = re.compile(r"(?!x)x")


def claim(lineno, title, verdict="PASS"):
    return (lineno, f'criterion "{title}" asserts {verdict} with neither'
                    " literal evidence nor a NOT-RUN disclaimer (evidence"
                    " must be a fenced code block in this section)")


BACKSTOP = (1, "verification artifact shows neither literal evidence nor"
               " a NOT-RUN disclaimer (evidence must be a fenced code"
               " block)")


class TestEvidenceIgnoresHtmlComments(unittest.TestCase):
    def test_a_fence_inside_a_comment_is_not_evidence(self):
        text = (FM + "# V\n\n## AC1\n\n<!--\n```\nfake output\n```\n-->\n"
                "- Result: PASS\n")
        self.assertEqual(gates.evidence_problems(text), [claim(14, "AC1")])

    def test_a_not_run_inside_a_comment_discloses_nothing(self):
        text = FM + "# V\n\n## AC1\n\nAll fine. <!-- not run -->\n"
        self.assertEqual(gates.evidence_problems(text), [BACKSTOP])

    def test_a_summary_naming_the_unknown_in_a_comment_names_nothing(self):
        text = (FM + "# V\n\n## Summary\n\nAll pass. <!-- 1 not run -->\n\n"
                "## AC1\n\n- Result: NOT RUN\n")
        self.assertEqual(gates.evidence_problems(text), [
            (7, 'summary "Summary" neither counts nor names the 1 criterion'
                ' section(s) disclosed as not run (first: "AC1", line 13);'
                " unknown never rolls up to pass")])

    def test_a_verdict_inside_a_comment_asserts_nothing(self):
        text = (FM + "# V\n\n## AC1\n\n<!--\n- Result: PASS\n-->\n"
                "```\nok\n```\n")
        self.assertEqual(gates.evidence_problems(text), [])

    def test_a_comment_opener_inside_a_fence_is_quoted_not_hidden(self):
        """A `<!--` in fenced evidence is output: it must not hide the
        headings and verdicts between it and a later `-->`."""
        text = (FM + "# V\n\n## AC1\n\n```\n<!--\n```\n- Result: PASS\n\n"
                "## AC2\n\n- Result: PASS\n\n## AC3\n\n```\nend -->\n```\n"
                "- Result: PASS\n")
        self.assertEqual(gates.evidence_problems(text), [claim(16, "AC2")])

    def test_an_unclosed_line_start_comment_hides_the_rest(self):
        text = (FM + "# V\n\n## AC1\n\n```\nok\n```\n- Result: PASS\n\n"
                "<!--\n## AC2\n\n- Result: PASS\n")
        self.assertEqual(gates.evidence_problems(text), [])

    def test_a_mid_line_unclosed_opener_is_literal(self):
        text = FM + "# V\n\n## AC1\n\nSee `<!--` here.\n- Result: PASS\n"
        self.assertEqual(gates.evidence_problems(text), [claim(10, "AC1")])

    def test_a_mid_line_opener_closed_later_in_its_paragraph_hides(self):
        # GitHub hides an inline comment that spans lines of one
        # paragraph, as B's HTML_COMMENT does; H read the verdict in it.
        text = (FM + "# V\n\n## AC1\n\nEvidence pending <!--\n"
                "- Result: PASS\n-->\n")
        self.assertEqual(gates.evidence_problems(text), [BACKSTOP])

    def test_a_blank_line_ends_a_mid_line_opener_paragraph(self):
        # The paragraph ends at the blank line, so the `<!--` stays text.
        text = (FM + "# V\n\n## AC1\n\nSee <!-- here.\n\n"
                "- Result: PASS\n\n-->\n")
        self.assertEqual(gates.evidence_problems(text), [claim(11, "AC1")])

    def test_an_opener_in_a_code_span_stays_literal_before_a_close(self):
        text = (FM + "# V\n\n## AC1\n\nSee `<!--` here.\n"
                "- Result: PASS\nthen `-->`.\n")
        self.assertEqual(gates.evidence_problems(text), [claim(10, "AC1")])

    def test_text_after_a_comment_close_is_still_read(self):
        text = (FM + "# V\n\n## AC1\n\n<!--\nhidden\n--> - Result: PASS\n")
        self.assertEqual(gates.evidence_problems(text), [claim(11, "AC1")])


class TestVerdictLabelReadWidely(unittest.TestCase):
    APPENDIX = "\n## Appendix\n\n```\nok\n```\n"

    def test_each_reworded_label_asserts(self):
        for line in ("✅ Result: PASS", "Result for AC1: PASS",
                     "Verdict (AC1): PASS", "Test 2 result: PASS",
                     "Criterion 3 result: PASS", "Result (smoke): PASS",
                     "- ✔️ **Verdict of the smoke run:** PASS"):
            with self.subTest(line=line):
                text = FM + "# V\n\n## AC1\n\n" + line + "\n" + self.APPENDIX
                self.assertEqual(gates.evidence_problems(text),
                                 [claim(9, "AC1")])

    def test_the_verdict_value_is_read_after_the_clause(self):
        self.assertEqual(
            gates.RESULT_LINE.match("Verdict (AC1): NOT RUN").group(1),
            "NOT RUN")
        self.assertEqual(
            gates.RESULT_LINE.match("Result for AC1: PASS").group(1), "PASS")

    def test_inputs_and_asides_still_assert_nothing(self):
        for line in ("Check: ran it", "Note: see above",
                     "Evidence for AC1: below", "Command (smoke): make"):
            with self.subTest(line=line):
                self.assertIsNone(gates.RESULT_LINE.match(line))

    def test_the_wider_label_stays_linear(self):
        for unit, tail in (("✅", "x"), ("- ", "x"), ("✅ -", ""),
                           ("✅", "Result for " + "a" * 60)):
            with self.subTest(unit=unit):
                self.assertLess(linear_time.growth(
                    gates.RESULT_LINE.match,
                    lambda n, u=unit, t=tail: u * n + t, 20000),
                    linear_time.GROWTH_LIMIT)


def brief(**sections):
    """A fresh defect.md with every required section filled for real,
    each overridable by keyword (the title with spaces and slashes
    dropped)."""
    body = ""
    for name in gates.CAPTURE_REQUIRED_SECTIONS:
        key = re.sub(r"\W+", "_", name).strip("_").lower()
        body += sections.get(key, f"## {name}\n\nreal content\n") + "\n"
    return ("---\nstage: capture\nrun: maintenance:demo\ndate: 2026-11-01\n"
            "re-entry: implement\n---\n\n# Defect: demo\n\n" + body)


class TestCaptureIgnoresHtmlComments(unittest.TestCase):
    def test_a_filled_brief_is_clean(self):
        self.assertEqual(gates.capture_completeness_problems(brief()), [])

    def test_a_section_holding_only_comments_is_placeholder_only(self):
        for content in ("<!-- TODO fill this in -->",
                        "<!-- who? -->\n<!-- since when -->",
                        "<!--\nreal content\n-->"):
            with self.subTest(content=content):
                text = brief(blast_radius=f"## Blast radius\n\n{content}\n")
                self.assertEqual(gates.capture_completeness_problems(text), [
                    "required section 'Blast radius' is present but"
                    " placeholder-only (template text was never filled in)"])

    def test_a_section_wrapped_in_a_comment_is_missing(self):
        text = brief(blast_radius="<!--\n## Blast radius\n\nreal content\n"
                                  "-->\n")
        self.assertEqual(gates.capture_completeness_problems(text), [
            "missing required section 'Blast radius'"])


class TestPrdSectionsIgnoreHtmlComments(unittest.TestCase):
    ROOT = Path("/repo")

    def check(self, prd, rows):
        from test_gates import parsed_run, run_entry
        parsed = parsed_run(runs=[run_entry(
            self.ROOT / "docs/features/demo", prd_id="PRD-0001",
            prd_date="2026-11-01", prd=prd, breakdown=rows)])
        return gates.check_prd_coverage(self.ROOT, parsed)

    PRD = ["---", "stage: prd", "id: PRD-0001", "date: 2026-11-01", "---",
           "# P", ""]

    def test_a_commented_out_heading_is_not_a_section(self):
        prd = self.PRD + ["<!--", "## Hidden", "-->", "", "## Solution",
                          "x"]
        self.assertEqual(
            self.check(prd, ["- [ ] WO-0001 a (PRD-0001 §Solution)"]), [])

    def test_a_waiver_still_waives_and_line_numbers_survive(self):
        prd = self.PRD + ["<!-- a note", "spanning lines -->",
                          "## Actors", "",
                          "<!-- coverage-waiver: context, not work -->",
                          "## Scope", "y"]
        self.assertEqual(self.check(prd, ["- [ ] WO-0001 a (PRD-0001)"]), [
            "O: docs/features/demo/prd.md:13 PRD-0001 §Scope is cited by no"
            " breakdown row and carries no coverage waiver"])


class TestPrdCitationResolvesToOneSection(unittest.TestCase):
    ROOT = Path("/repo")
    PRD = ["---", "stage: prd", "id: PRD-0001", "date: 2026-11-01", "---",
           "# P", "", "## Solution", "x", "", "## Solution details", "y",
           "", "## Scope", "z"]

    def check(self, rows):
        from test_gates import parsed_run, run_entry
        parsed = parsed_run(runs=[run_entry(
            self.ROOT / "docs/features/demo", prd_id="PRD-0001",
            prd_date="2026-11-01", prd=self.PRD, breakdown=rows)])
        return gates.check_prd_coverage(self.ROOT, parsed)

    def uncited(self, lineno, title):
        return (f"O: docs/features/demo/prd.md:{lineno} PRD-0001 §{title}"
                " is cited by no breakdown row and carries no coverage"
                " waiver")

    def test_a_longer_title_does_not_credit_its_prefix(self):
        self.assertEqual(
            self.check(["- [ ] WO-0001 a (PRD-0001 §Solution details,"
                        " §Scope)"]),
            [self.uncited(8, "Solution")])

    def test_another_prds_section_credits_nothing_here(self):
        self.assertEqual(
            self.check(["- [ ] WO-0001 a (PRD-0001 §Solution; PRD-0002"
                        " §Solution details, §Scope)"]),
            [self.uncited(11, "Solution details"), self.uncited(14, "Scope")])

    def test_each_section_cited_on_its_own_is_covered(self):
        self.assertEqual(
            self.check(["- [ ] WO-0001 a (PRD-0001 §Solution,"
                        " §Solution details, §Scope)"]), [])

    def test_a_citation_before_any_id_belongs_to_the_rows_first_id(self):
        self.assertEqual(
            self.check(["- [ ] WO-0001 §Solution, §Solution details,"
                        " §Scope (PRD-0001)"]), [])


class TestEffortKeySet(unittest.TestCase):
    REL = "factory/templates/factory.json"

    def check(self, config):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(self.REL, json.dumps(config))
            return gates.check_config_shape(tree.root)

    def test_an_effort_table_missing_a_band_is_flagged(self):
        config = dict(CONFIG, effort={"mechanical": "low"})
        self.assertEqual(self.check(config), [
            f"F: {self.REL} effort must map exactly mechanical,"
            " implementation, architecture_review"])
        self.assertEqual(
            factory_config.resolve_effort("implementation", config)[1],
            ["config: factory.json names no effort for the implementation"
             " band"])

    def test_an_absent_effort_table_is_not_a_shape_problem(self):
        config = {k: v for k, v in CONFIG.items() if k != "effort"}
        self.assertEqual(self.check(config), [])

    def test_a_whitespace_model_is_no_model_at_gate_or_dispatch(self):
        config = dict(CONFIG, routing=dict(CONFIG["routing"],
                                           mechanical="   "))
        self.assertEqual(self.check(config), [
            f"F: {self.REL} routing.mechanical must name a model id"])
        self.assertEqual(factory_config.resolve_model("mechanical", config),
                         (None, ["config: factory.json routes no model to"
                                 " the mechanical band"]))


class TestToolsOnlyMarkerNeedsNoMirror(unittest.TestCase):
    def test_a_marker_beside_a_real_mirror_still_checks_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = fixtures.scaffold_sync_fixture(root)
            manifest = root / "factory" / "manifest.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            manifest.write_text(json.dumps(
                {gates.INSTALL_KEY: gates.TOOLS_ONLY, **data}),
                encoding="utf-8")
            self.assertEqual(gates.check_scaffold_sync(root), [])
            path.write_text("check: tampered\n", encoding="utf-8")
            self.assertEqual(gates.check_scaffold_sync(root), [
                "E: factory/templates/Makefile does not match its manifest"
                " checksum (re-run `python3 tools/factory_init.py"
                " update-manifest` in the skills repo, never hand-edit)"])


class TestStandardsStatusVocabulary(unittest.TestCase):
    ENTRY = {"slug": "some-slug", "statement": "Something MUST happen.",
             "level": "MUST", "source": "adr/0001#some-slug",
             "status": "advisory", "domain": "factory"}

    def check(self, entries, adr_status="accepted"):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/adr/0001-real.md",
                       f"# Real\n\n- Status: {adr_status}\n\n"
                       "## Normative statements\n\n- **some-slug**"
                       " (factory): Something MUST happen.\n")
            tree.write("docs/standards.json", json.dumps(entries))
            return gates.check_standards_drift(tree.root)

    def test_a_status_outside_the_vocabulary_is_flagged(self):
        for status in ("Enforced", "enforcd", None):
            with self.subTest(status=status):
                self.assertEqual(
                    self.check([dict(self.ENTRY, status=status)],
                               "superseded"),
                    ["K: docs/standards.json entry 'some-slug' has status"
                     f" {status!r}, not one of advisory, enforced"])

    def test_a_non_object_member_is_flagged(self):
        self.assertEqual(self.check([self.ENTRY, None, 42, "x"]), [
            "K: docs/standards.json entry 1 is not a JSON object",
            "K: docs/standards.json entry 2 is not a JSON object",
            "K: docs/standards.json entry 3 is not a JSON object"])

    def test_the_vocabulary_is_silent(self):
        self.assertEqual(self.check([self.ENTRY]), [])
        self.assertEqual(
            self.check([dict(self.ENTRY, status="enforced")]), [])


class TestSelftestSubRules(unittest.TestCase):
    """Each sub-rule going dead must turn its own selftest row red."""

    def failures(self, name, replacement):
        with mock.patch.object(gates, name, replacement), \
                mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            code = fixtures.selftest()
        labels = {line.split(":", 1)[0]
                  for line in out.getvalue().splitlines()
                  if not line.startswith("selftest:")}
        return code, labels

    def test_each_dead_sub_rule_turns_its_row_red(self):
        for name, replacement, label in (
                ("PLACEHOLDER_LINE", NEVER, "H placeholder"),
                ("NOT_RUN_TOKEN", NEVER, "H prose disclosure"),
                ("CAPTURE_AUTOLINK", NEVER, "M autolink"),
                ("TOOLS_ONLY", object(), "E tools-only")):
            with self.subTest(name=name):
                self.assertEqual(self.failures(name, replacement),
                                 (1, {label}))


if __name__ == "__main__":
    unittest.main()
