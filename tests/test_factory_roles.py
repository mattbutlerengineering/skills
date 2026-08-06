"""factory_roles (ADR-0047) — the role-vocabulary seam's own contract.

The seam is the one home of the chartered role set. Before it, the
vocabulary had four homes that never imported each other — this file's
sibling test_factory_charters.py's ROLES tuple, charter_replay.py's
three-role literal, assembler.py's CHARTER_BY_TYPE map, and
factory/CHARTERS.md's prose index. These tests pin the vocabulary
itself, the two file paths each role is encoded at, and that every
retired home now agrees with the seam.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import assembler  # noqa: E402
import charter_replay  # noqa: E402
import factory_roles  # noqa: E402


class TestVocabulary(unittest.TestCase):
    def test_the_nine_prd_actor_roles(self):
        """PRD-0001 §Actors names nine chartered roles; the engineer
        ships as `swe`."""
        self.assertEqual(
            factory_roles.ROLES,
            ("pm", "architect", "ux", "planner", "swe", "qa", "reviewer",
             "support", "toolsmith"))

    def test_roles_are_distinct(self):
        self.assertEqual(len(set(factory_roles.ROLES)),
                         len(factory_roles.ROLES))

    def test_required_stub_fields(self):
        """Beyond name: (the registry key), a dispatchable stub carries
        description, tools, and route — the fields the dispatch plane
        reads (ADR-0032, ADR-0034)."""
        self.assertEqual(factory_roles.REQUIRED_FIELDS,
                        ("description", "tools", "route"))


class TestPaths(unittest.TestCase):
    def test_charter_path_grammar(self):
        self.assertEqual(
            factory_roles.charter_path("/repo", "swe"),
            Path("/repo/factory/charters/swe/CHARTER.md"))

    def test_agent_path_grammar(self):
        self.assertEqual(
            factory_roles.agent_path("/repo", "swe"),
            Path("/repo/factory/agents/factory-swe.md"))

    def test_every_role_has_both_files_in_this_repo(self):
        for role in factory_roles.ROLES:
            with self.subTest(role=role, file="charter"):
                self.assertTrue(
                    factory_roles.charter_path(ROOT, role).is_file(),
                    f"missing factory/charters/{role}/CHARTER.md")
            with self.subTest(role=role, file="stub"):
                self.assertTrue(
                    factory_roles.agent_path(ROOT, role).is_file(),
                    f"missing factory/agents/factory-{role}.md")


class TestCallersShareTheVocabulary(unittest.TestCase):
    """The retired homes, pinned against forking off the seam again."""

    def test_assembler_dispatch_map_targets_chartered_roles(self):
        """assembler keeps its label->role dispatch POLICY as data (which
        charter runs a type: label), but every role it names must be a
        chartered one — the vocabulary is the seam's."""
        for label, role in sorted(assembler.CHARTER_BY_TYPE.items()):
            with self.subTest(label=label):
                self.assertIn(role, factory_roles.ROLES)
        self.assertIn(assembler.DEFAULT_CHARTER, factory_roles.ROLES)

    def test_replay_fixture_coverage_is_a_subset_of_the_vocabulary(self):
        """charter_replay validates fixtures against the full chartered
        set; SUPPORTED_REPLAY_ROLES only states which roles have golden
        fixtures today, and may never leave the vocabulary."""
        self.assertTrue(
            set(charter_replay.SUPPORTED_REPLAY_ROLES)
            <= set(factory_roles.ROLES))


if __name__ == "__main__":
    unittest.main()
