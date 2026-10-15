"""Every routine protocol under docs/factory/ is that routine's runtime
interface. #844: a cloud run with GitHub reachable only through MCP tools
stored its HTML-comment markers escaped (`&lt;!-- ... --&gt;`), missed
its journal by marker, and opened a duplicate. The clauses that stop it
live once, in docs/factory/routine-markers.md (#889); these tests pin
that body and each protocol's citation of it, so a later edit cannot
drop one silently.
"""
import unittest
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[1] / "docs" / "factory"
MARKERS = "routine-markers.md"
MARKERS_PATH = f"docs/factory/{MARKERS}"

_WEEKLY_LOOKUP = ("Find it by marker, in either form (§Markers on GitHub);"
                  " create it only when that search succeeded and found"
                  " none.")

# protocol file -> the journal-lookup sentence its report section carries
JOURNAL_LOOKUP = {
    "queue-groomer-routine.md": _WEEKLY_LOOKUP,
    "retro-reflect-routine.md": _WEEKLY_LOOKUP,
    "doc-gardener-routine.md": _WEEKLY_LOOKUP,
    "merge-train-routine.md": _WEEKLY_LOOKUP,
    "improvement-routine.md":
        "Find it by marker among open issues, in either form (§Markers on"
        " GitHub); create and pin it only when that search succeeded and"
        " found none; re-pin if unpinned",
}

ROUTINES_WITH_TRIGGER = ("queue-groomer-routine.md",
                         "retro-reflect-routine.md",
                         "doc-gardener-routine.md",
                         "merge-train-routine.md")


def text(name):
    return " ".join((FACTORY / name).read_text(encoding="utf-8").split())


class TestEveryRoutineProtocolIsCovered(unittest.TestCase):

    def test_the_table_names_every_routine_protocol(self):
        on_disk = {p.name for p in FACTORY.glob("*-routine.md")}
        self.assertEqual(set(JOURNAL_LOOKUP), on_disk)


class TestRoutineMarkersReference(unittest.TestCase):
    """The marker rules live once, in the shared routine reference (#889);
    these pin its body."""

    def setUp(self):
        self.body = text(MARKERS)

    def test_the_environment_may_be_mcp_only(self):
        self.assertIn(
            "The cloud environment may reach GitHub only through the GitHub"
            " MCP tools, with no `gh` CLI (#844)", self.body)

    def test_find_matches_raw_and_escaped_forms(self):
        self.assertIn(
            "**Find by both forms.** A marker is matched in its raw form"
            " (`<!-- … -->`) and in its HTML-escaped form"
            " (`&lt;!-- … --&gt;`).", self.body)

    def test_write_raw_then_verify_by_rereading(self):
        self.assertIn(
            "**Write raw, then verify.** Write the marker as literal `<!--`"
            " and `-->`, never pre-escaped.", self.body)
        self.assertIn(
            "re-read what GitHub stored; if it holds the escaped form,"
            " update that body or comment to the raw form and re-read"
            " again.", self.body)

    def test_never_create_a_journal_on_a_failed_or_ambiguous_search(self):
        self.assertIn(
            "**Never create on doubt.** Create a journal only when the"
            " marker search succeeded and matched no open issue in either"
            " form. If the search errored, or matched more than one open"
            " issue, create nothing: report it under Health in the session"
            " log and stop.", self.body)


class TestEachProtocolCitesTheReference(unittest.TestCase):

    def test_its_markers_section_cites_the_reference(self):
        for name in JOURNAL_LOOKUP:
            with self.subTest(name):
                body = text(name)
                section = body[body.index("## Markers on GitHub"):
                               body.index("## 1 ")]
                self.assertIn(f"`{MARKERS_PATH}`", section)

    def test_it_carries_no_copy_of_the_rules(self):
        for name in JOURNAL_LOOKUP:
            with self.subTest(name):
                self.assertNotIn("**Find by both forms.**", text(name))

    def test_its_self_edit_ban_names_the_reference(self):
        """ADR-0044's self-edit ban covers the shared file the playbook
        now spans, by name."""
        for name in JOURNAL_LOOKUP:
            with self.subTest(name):
                body = text(name)
                ban = body[body.index("- Never edit this file"):]
                ban = ban[:ban.index(" - ")]
                self.assertIn(f"`{MARKERS_PATH}`", ban)

    def test_the_journal_lookup_defers_to_the_marker_rules(self):
        for name, sentence in JOURNAL_LOOKUP.items():
            with self.subTest(name):
                body = text(name)
                self.assertIn(sentence, body)
                self.assertNotIn("create it if absent", body)
                self.assertNotIn("create and pin it if absent", body)

    def test_a_missing_gh_cli_is_not_unreachable_github(self):
        for name in JOURNAL_LOOKUP:
            with self.subTest(name):
                self.assertIn(
                    "GitHub is unreachable — `gh auth status` fails and no"
                    " GitHub MCP tool answers →", text(name))


class TestTriggerEnvironment(unittest.TestCase):

    def test_no_protocol_claims_gh_and_git_only(self):
        for name in JOURNAL_LOOKUP:
            with self.subTest(name):
                self.assertNotIn("`gh` and `git` only", text(name))

    def test_trigger_states_the_real_environment(self):
        for name in ROUTINES_WITH_TRIGGER:
            with self.subTest(name):
                self.assertIn(
                    "**Environment:** `git`, and GitHub through the GitHub"
                    " MCP tools; the `gh` CLI may be absent", text(name))


if __name__ == "__main__":
    unittest.main()
