"""Factory role charters (WO-0013) — file-contract tests.

The subagent registry keys agents by frontmatter `name:`, not filename —
a charter that fails these checks is silently undispatchable. Each role
is encoded as two files (agent stub + full charter in
factory/skills/<role>/SKILL.md); tests assert the exact paths and fields
the dispatch plane (ADR-0032) depends on.

Charters carry a routing *band* (`route:`), never a model id: the band
resolves to a model through the per-repo `factory.json` routing table
(ADR-0034), which is the single routing source of truth (ADR-0004).
Resolution itself is WO-0007's job — these tests only pin that the
charters name a real band and assert no model of their own.
"""
import json
import unittest
from pathlib import Path

import protocol

REPO_ROOT = Path(__file__).resolve().parent.parent

ROLES = ("swe", "reviewer", "planner")

REQUIRED_FIELDS = ("description", "tools", "route")


def agent_path(role):
    return REPO_ROOT / "factory" / "agents" / f"factory-{role}.md"


def skill_path(role):
    return REPO_ROOT / "factory" / "skills" / role / "SKILL.md"


def routing_bands():
    """The band names defined by the factory config's routing table."""
    config = json.loads(
        (REPO_ROOT / "factory" / "templates" / "factory.json")
        .read_text(encoding="utf-8"))
    return set(config["routing"])


def agent_body(role):
    """Text after the frontmatter block of the agent stub."""
    text = agent_path(role).read_text(encoding="utf-8")
    return text.split("\n---\n", 1)[1]


class TestAgentStubs(unittest.TestCase):
    def test_agent_file_exists(self):
        for role in ROLES:
            with self.subTest(role=role):
                self.assertTrue(agent_path(role).is_file(),
                                f"missing factory/agents/factory-{role}.md")

    def test_frontmatter_parses(self):
        for role in ROLES:
            with self.subTest(role=role):
                self.assertIsNotNone(
                    protocol.read_frontmatter(agent_path(role)),
                    f"factory-{role}.md has no frontmatter block")

    def test_name_keys_the_subagent_registry(self):
        for role in ROLES:
            with self.subTest(role=role):
                fields = protocol.read_frontmatter(agent_path(role)) or {}
                self.assertEqual(fields.get("name"), f"factory-{role}")

    def test_required_fields_present_and_non_empty(self):
        for role in ROLES:
            fields = protocol.read_frontmatter(agent_path(role)) or {}
            for field in REQUIRED_FIELDS:
                with self.subTest(role=role, field=field):
                    self.assertTrue(fields.get(field, "").strip(),
                                    f"factory-{role}.md {field} is empty")

    def test_body_loads_the_charter_skill(self):
        for role in ROLES:
            with self.subTest(role=role):
                self.assertIn(f"factory/skills/{role}/SKILL.md",
                              agent_body(role))

    def test_route_names_a_band_the_factory_config_defines(self):
        bands = routing_bands()
        for role in ROLES:
            with self.subTest(role=role):
                fields = protocol.read_frontmatter(agent_path(role)) or {}
                self.assertIn(fields.get("route"), bands)

    def test_no_stub_hardcodes_a_model(self):
        """A `model:` in a stub is a second routing source (ADR-0004)."""
        for role in ROLES:
            with self.subTest(role=role):
                fields = protocol.read_frontmatter(agent_path(role)) or {}
                self.assertNotIn("model", fields)


class TestCharterSkills(unittest.TestCase):
    def test_skill_file_exists(self):
        for role in ROLES:
            with self.subTest(role=role):
                self.assertTrue(skill_path(role).is_file(),
                                f"missing factory/skills/{role}/SKILL.md")

    def test_charter_has_must_never_and_escalation_sections(self):
        for role in ROLES:
            text = skill_path(role).read_text(encoding="utf-8")
            with self.subTest(role=role, section="Must never"):
                self.assertIn("Must never", text)
            with self.subTest(role=role, section="Escalat"):
                self.assertIn("Escalat", text)


if __name__ == "__main__":
    unittest.main()
