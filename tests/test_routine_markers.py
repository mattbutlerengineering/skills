"""Every routine protocol under docs/factory/ is that routine's runtime
interface. #844: a cloud run with GitHub reachable only through MCP tools
stored its HTML-comment markers escaped (`&lt;!-- ... --&gt;`), missed
its journal by marker, and opened a duplicate. These tests pin the
clauses that stop it, in all four protocols, so a later edit cannot drop
one silently.
"""
import unittest
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[1] / "docs" / "factory"

_WEEKLY_LOOKUP = ("Find it by marker, in either form (§Markers on GitHub);"
                  " create it only when that search succeeded and found"
                  " none.")

# protocol file -> the journal-lookup sentence its report section carries
JOURNAL_LOOKUP = {
    "queue-groomer-routine.md": _WEEKLY_LOOKUP,
    "retro-reflect-routine.md": _WEEKLY_LOOKUP,
    "doc-gardener-routine.md": _WEEKLY_LOOKUP,
    "improvement-routine.md":
        "Find it by marker among open issues, in either form (§Markers on"
        " GitHub); create and pin it only when that search succeeded and"
        " found none; re-pin if unpinned",
}

ROUTINES_WITH_TRIGGER = ("queue-groomer-routine.md",
                         "retro-reflect-routine.md",
                         "doc-gardener-routine.md")


def text(name):
    return " ".join((FACTORY / name).read_text(encoding="utf-8").split())


class TestEveryRoutineProtocolIsCovered(unittest.TestCase):

    def test_the_table_names_every_routine_protocol(self):
        on_disk = {p.name for p in FACTORY.glob("*-routine.md")}
        self.assertEqual(set(JOURNAL_LOOKUP), on_disk)


class TestMarkersOnGitHub(unittest.TestCase):

    def test_the_environment_may_be_mcp_only(self):
        for name in JOURNAL_LOOKUP:
            with self.subTest(name):
                self.assertIn(
                    "The cloud environment may reach GitHub only through"
                    " the GitHub MCP tools, with no `gh` CLI (#844)",
                    text(name))

    def test_find_matches_raw_and_escaped_forms(self):
        for name in JOURNAL_LOOKUP:
            with self.subTest(name):
                self.assertIn(
                    "**Find by both forms.** A marker is matched in its"
                    " raw form (`<!-- … -->`) and in its HTML-escaped"
                    " form (`&lt;!-- … --&gt;`).", text(name))

    def test_write_raw_then_verify_by_rereading(self):
        for name in JOURNAL_LOOKUP:
            with self.subTest(name):
                body = text(name)
                self.assertIn(
                    "**Write raw, then verify.** Write the marker as"
                    " literal `<!--` and `-->`, never pre-escaped.", body)
                self.assertIn(
                    "re-read what GitHub stored; if it holds the escaped"
                    " form, update that body or comment to the raw form"
                    " and re-read again.", body)

    def test_never_create_a_journal_on_a_failed_or_ambiguous_search(self):
        for name in JOURNAL_LOOKUP:
            with self.subTest(name):
                self.assertIn(
                    "**Never create on doubt.** Create a journal only when"
                    " the marker search succeeded and matched no open"
                    " issue in either form. If the search errored, or"
                    " matched more than one open issue, create nothing:"
                    " report it under Health in the session log and stop.",
                    text(name))

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
