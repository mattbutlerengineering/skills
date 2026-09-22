"""standards_index.py (the ADR-0073 normative-statement-index seam) —
pure-function + fixture tests.

Same discipline as test_cost_ledger: every function is exercised through
its public interface and tests assert the EXACT strings callers will
print or write.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import standards_index

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402


# The architecture.md worked example, used throughout as the one valid
# bullet fixture so every test reads the same real-shaped statement.
VALID_BULLET = ("- **adr0032-one-way-mirror** (factory): A work-order"
                " issue MUST be created only after its breakdown row"
                " exists.")
VALID_ENTRY = {
    "slug": "adr0032-one-way-mirror",
    "statement": "A work-order issue MUST be created only after its"
                 " breakdown row exists.",
    "level": "MUST",
    "domain": "factory",
}


def adr_file(root, number, body):
    """Write a minimal docs/adr/<number>-x.md, returning its path."""
    path = Path(root) / "docs" / "adr" / f"{number}-x.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


class TestParseBullet(unittest.TestCase):
    def test_a_well_formed_bullet_parses(self):
        fields, problems = standards_index.parse_bullet(VALID_BULLET)
        self.assertEqual(problems, [])
        self.assertEqual(fields, VALID_ENTRY)

    def test_a_should_not_keyword_buckets_to_should(self):
        line = ("- **no-foo** (pipeline): A widget SHOULD NOT be built"
               " without a frobnicator.")
        fields, problems = standards_index.parse_bullet(line)
        self.assertEqual(problems, [])
        self.assertEqual(fields["level"], "SHOULD")

    def test_a_must_not_keyword_buckets_to_must(self):
        line = "- **no-bar** (docs): A doc MUST NOT lie about coverage."
        fields, problems = standards_index.parse_bullet(line)
        self.assertEqual(problems, [])
        self.assertEqual(fields["level"], "MUST")

    def test_a_line_with_no_bullet_shape_is_unreadable(self):
        fields, problems = standards_index.parse_bullet(
            "Just some prose, not a bullet at all.")
        self.assertIsNone(fields)
        self.assertEqual(len(problems), 1)
        self.assertIn("unreadable normative-statement bullet", problems[0])

    def test_a_missing_slug_is_a_problem(self):
        fields, problems = standards_index.parse_bullet(
            "- ** ** (factory): Something MUST happen.")
        self.assertIsNone(fields)
        self.assertTrue(any("missing or invalid slug" in p
                            for p in problems), problems)

    def test_an_invalid_slug_shape_is_a_problem(self):
        fields, problems = standards_index.parse_bullet(
            "- **Not Kebab Case** (factory): Something MUST happen.")
        self.assertIsNone(fields)
        self.assertTrue(any("missing or invalid slug" in p
                            for p in problems), problems)

    def test_an_unknown_domain_is_a_problem(self):
        fields, problems = standards_index.parse_bullet(
            "- **some-slug** (marketing): Something MUST happen.")
        self.assertIsNone(fields)
        self.assertEqual(problems, [
            "domain 'marketing' is not one of factory, pipeline, eval,"
            " docs"])

    def test_a_missing_keyword_is_a_problem(self):
        fields, problems = standards_index.parse_bullet(
            "- **some-slug** (factory): Something happens sometimes.")
        self.assertIsNone(fields)
        self.assertEqual(problems, [
            "statement carries no RFC-2119 keyword (MUST/MUST NOT/SHOULD/"
            "SHOULD NOT)"])

    def test_a_doubled_keyword_is_a_problem(self):
        fields, problems = standards_index.parse_bullet(
            "- **some-slug** (factory): It MUST happen and it SHOULD"
            " also happen.")
        self.assertIsNone(fields)
        self.assertTrue(
            any("2 RFC-2119 keywords" in p for p in problems), problems)

    def test_missing_slug_and_missing_keyword_are_both_reported(self):
        # Multiple malformed dimensions on the same bullet are never
        # collapsed into one generic complaint — each is its own
        # actionable problem string.
        fields, problems = standards_index.parse_bullet(
            "- ** ** (factory): Nothing normative here.")
        self.assertIsNone(fields)
        self.assertEqual(len(problems), 2)


class TestAdrNumber(unittest.TestCase):
    def test_an_adr_derived_source_yields_its_number(self):
        self.assertEqual(
            standards_index.adr_number("adr/0032#adr0032-one-way-mirror"),
            "0032")

    def test_a_hand_curated_source_yields_none(self):
        self.assertIsNone(
            standards_index.adr_number("CLAUDE.md#stdlib-only"))

    def test_a_non_string_yields_none(self):
        self.assertIsNone(standards_index.adr_number(None))
        self.assertIsNone(standards_index.adr_number(7))

    def test_a_short_number_does_not_match(self):
        self.assertIsNone(standards_index.adr_number("adr/32#slug"))


class TestBuildIndex(unittest.TestCase):
    def test_no_adr_directory_is_empty_and_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(standards_index.build_index(tmp), ([], []))

    def test_an_adr_with_no_normative_heading_contributes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr_file(tmp, "0001", "# Real\n\n- Status: accepted\n\n"
                                  "## Decision\n\nSomething MUST happen.\n")
            self.assertEqual(standards_index.build_index(tmp), ([], []))

    def test_a_well_formed_bullet_becomes_an_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr_file(tmp, "0032",
                     "# One-way mirror\n\n- Status: accepted\n\n"
                     "## Normative statements\n\n" + VALID_BULLET + "\n")
            entries, problems = standards_index.build_index(tmp)
            self.assertEqual(problems, [])
            self.assertEqual(entries, [{
                "slug": "adr0032-one-way-mirror",
                "statement": VALID_ENTRY["statement"],
                "level": "MUST",
                "source": "adr/0032#adr0032-one-way-mirror",
                "status": "advisory",
                "domain": "factory",
            }])

    def test_entries_are_sorted_by_slug(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr_file(tmp, "0001",
                     "# X\n\n## Normative statements\n\n"
                     "- **zzz-last** (docs): It MUST be last.\n"
                     "- **aaa-first** (docs): It MUST be first.\n")
            entries, problems = standards_index.build_index(tmp)
            self.assertEqual(problems, [])
            self.assertEqual([e["slug"] for e in entries],
                             ["aaa-first", "zzz-last"])

    def test_the_section_stops_at_the_next_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr_file(tmp, "0001",
                     "# X\n\n## Normative statements\n\n"
                     + VALID_BULLET + "\n\n## Consequences\n\n"
                     "- **not-collected** (docs): This MUST NOT be read"
                     " as a statement.\n")
            entries, problems = standards_index.build_index(tmp)
            self.assertEqual(problems, [])
            self.assertEqual([e["slug"] for e in entries],
                             ["adr0032-one-way-mirror"])

    def test_a_malformed_bullet_is_a_located_unlabelled_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr_file(tmp, "0001",
                     "# X\n\n## Normative statements\n\n"
                     "- **some-slug** (factory): No keyword here.\n")
            entries, problems = standards_index.build_index(tmp)
            self.assertEqual(entries, [])
            self.assertEqual(problems, [
                "docs/adr/0001-x.md:5 statement carries no RFC-2119"
                " keyword (MUST/MUST NOT/SHOULD/SHOULD NOT)"])

    def test_a_duplicate_slug_across_two_adrs_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr_file(tmp, "0001",
                     "# X\n\n## Normative statements\n\n" + VALID_BULLET
                     + "\n")
            adr_file(tmp, "0002",
                     "# Y\n\n## Normative statements\n\n" + VALID_BULLET
                     + "\n")
            entries, problems = standards_index.build_index(tmp)
            self.assertEqual(len(entries), 1)
            self.assertEqual(problems, [
                "docs/adr/0002-x.md:5 slug 'adr0032-one-way-mirror'"
                " duplicates docs/adr/0001-x.md:5"])

    def test_blank_lines_inside_the_section_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr_file(tmp, "0001",
                     "# X\n\n## Normative statements\n\n"
                     + VALID_BULLET + "\n\n\n")
            entries, problems = standards_index.build_index(tmp)
            self.assertEqual(problems, [])
            self.assertEqual(len(entries), 1)


class TestForeignEntries(unittest.TestCase):
    def test_an_absent_file_is_empty_and_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(standards_index.foreign_entries(tmp), ([], []))

    def test_only_claude_md_sourced_entries_are_returned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / standards_index.STANDARDS_PATH
            path.parent.mkdir(parents=True, exist_ok=True)
            hand = {"slug": "stdlib-only", "statement": "x", "level": "MUST",
                    "source": "CLAUDE.md#stdlib-only", "status": "advisory",
                    "domain": "factory"}
            derived = {"slug": "adr0032-one-way-mirror", "statement": "x",
                      "level": "MUST", "source": "adr/0032#x",
                      "status": "advisory", "domain": "factory"}
            path.write_text(json.dumps([hand, derived]), encoding="utf-8")
            self.assertEqual(standards_index.foreign_entries(tmp),
                             ([hand], []))

    def test_invalid_json_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / standards_index.STANDARDS_PATH
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("not json", encoding="utf-8")
            entries, problems = standards_index.foreign_entries(tmp)
            self.assertEqual(entries, [])
            self.assertEqual(len(problems), 1)
            self.assertIn("is not valid JSON", problems[0])

    def test_a_non_array_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / standards_index.STANDARDS_PATH
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
            self.assertEqual(standards_index.foreign_entries(tmp),
                             ([], [f"{standards_index.STANDARDS_PATH} is"
                                   " not a JSON array"]))


class TestUpdate(unittest.TestCase):
    def test_regenerates_from_adrs_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr_file(tmp, "0032",
                     "# One-way mirror\n\n## Normative statements\n\n"
                     + VALID_BULLET + "\n")
            problems = standards_index.update(tmp)
            self.assertEqual(problems, [])
            written = json.loads(
                (Path(tmp) / standards_index.STANDARDS_PATH).read_text(
                    encoding="utf-8"))
            self.assertEqual(written, [{
                "slug": "adr0032-one-way-mirror",
                "statement": VALID_ENTRY["statement"],
                "level": "MUST",
                "source": "adr/0032#adr0032-one-way-mirror",
                "status": "advisory",
                "domain": "factory",
            }])

    def test_preserves_hand_curated_entries_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr_file(tmp, "0032",
                     "# One-way mirror\n\n## Normative statements\n\n"
                     + VALID_BULLET + "\n")
            path = Path(tmp) / standards_index.STANDARDS_PATH
            path.parent.mkdir(parents=True, exist_ok=True)
            hand = {"slug": "stdlib-only", "statement": "Stdlib only.",
                    "level": "MUST", "source": "CLAUDE.md#stdlib-only",
                    "status": "enforced", "domain": "factory"}
            path.write_text(json.dumps([hand]), encoding="utf-8")
            problems = standards_index.update(tmp)
            self.assertEqual(problems, [])
            written = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn(hand, written)
            self.assertEqual(len(written), 2)

    def test_regen_replaces_the_previous_adr_derived_subset(self):
        # A second update, after an ADR-derived statement's text changed,
        # must not leave the STALE entry sitting beside the fresh one.
        with tempfile.TemporaryDirectory() as tmp:
            path = adr_file(tmp, "0032",
                            "# One-way mirror\n\n## Normative statements\n\n"
                            + VALID_BULLET + "\n")
            self.assertEqual(standards_index.update(tmp), [])
            path.write_text(
                "# One-way mirror\n\n## Normative statements\n\n"
                "- **adr0032-one-way-mirror** (factory): A work-order"
                " issue MUST be created only after its row exists"
                " (reworded).\n", encoding="utf-8")
            self.assertEqual(standards_index.update(tmp), [])
            written = json.loads(
                (Path(tmp) / standards_index.STANDARDS_PATH).read_text(
                    encoding="utf-8"))
            self.assertEqual(len(written), 1)
            self.assertIn("reworded", written[0]["statement"])

    def test_a_malformed_bullet_refuses_to_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr_file(tmp, "0001",
                     "# X\n\n## Normative statements\n\n"
                     "- **some-slug** (factory): No keyword here.\n")
            problems = standards_index.update(tmp)
            self.assertEqual(problems, [
                "standards-index: docs/adr/0001-x.md:5 statement carries"
                " no RFC-2119 keyword (MUST/MUST NOT/SHOULD/SHOULD NOT)"])
            self.assertFalse(
                (Path(tmp) / standards_index.STANDARDS_PATH).exists())

    def test_an_unreadable_existing_file_refuses_to_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / standards_index.STANDARDS_PATH
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("not json", encoding="utf-8")
            problems = standards_index.update(tmp)
            self.assertEqual(problems, [
                f"standards-index: {standards_index.STANDARDS_PATH} is not"
                " valid JSON: Expecting value: line 1 column 1 (char 0)"])
            # Refused, not clobbered: the malformed file is untouched.
            self.assertEqual(path.read_text(encoding="utf-8"), "not json")


class TestMain(cli_contract.CliContract, cli_contract.ReportContract,
               unittest.TestCase):
    usage_fragment = "update"
    summary_line = "standards-index: 0 problem(s)"

    def run_cli(self, argv):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(standards_index, "repo_root",
                                   lambda: Path(tmp)):
                return cli_contract.capture(standards_index.main, argv)

    def clean_cli(self):
        return self.run_cli(["update"])


if __name__ == "__main__":
    unittest.main()
