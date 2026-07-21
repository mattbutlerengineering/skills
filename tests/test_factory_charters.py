"""Factory role charters (WO-0013, WO-0014) — file-contract tests.

The subagent registry keys agents by frontmatter `name:`, not filename —
a charter that fails these checks is silently undispatchable. Each role
is encoded as two files (agent stub + full charter in
factory/skills/<role>/SKILL.md); tests assert the exact paths and fields
the dispatch plane (ADR-0032) depends on.

Charters carry a routing *band* (`route:`), never a model id: the band
resolves to a model through the per-repo `factory.json` routing table
(ADR-0034), which is the single routing source of truth (ADR-0004).
Resolution itself is `assembler.resolve_model` (band -> model id),
pinned end to end against the real charter files here by WO-0007's
tests/test_model_routing.py — these tests only pin that the charters
name a real band and assert no model of their own.

The nine roles are the ones PRD-0001 §Actors names (PM, architect, UX
designer, planner, engineer, QA, reviewer, support, toolsmith); the
engineer role ships as `swe`. `factory/CHARTERS.md` indexes them and
carries the three human-gate checklists (ADR-0033).
"""
import json
import re
import unittest
from pathlib import Path

import protocol

REPO_ROOT = Path(__file__).resolve().parent.parent

ROLES = ("pm", "architect", "ux", "planner", "swe", "qa", "reviewer",
         "support", "toolsmith")

REQUIRED_FIELDS = ("description", "tools", "route")

CHARTERS_INDEX = REPO_ROOT / "factory" / "CHARTERS.md"

# The three human gates of ADR-0033, in order. Each must appear in the
# index as a checklist the human owner can actually work through.
GATES = ("PRD approval", "Blueprint/ADR approval", "PR merge")

CHECKBOX = re.compile(r"^- \[ \] ", re.MULTILINE)


def agent_path(role):
    return REPO_ROOT / "factory" / "agents" / f"factory-{role}.md"


def skill_path(role):
    return REPO_ROOT / "factory" / "skills" / role / "SKILL.md"


def factory_config():
    return json.loads(
        (REPO_ROOT / "factory" / "templates" / "factory.json")
        .read_text(encoding="utf-8"))


def routing_bands():
    """The band names defined by the factory config's routing table."""
    return set(factory_config()["routing"])


def routed_model_ids():
    """The model ids the routing table resolves bands to. No charter may
    name one — that would be a second routing source (ADR-0004)."""
    return set(factory_config()["routing"].values())


def agent_body(role):
    """Text after the frontmatter block of the agent stub."""
    text = agent_path(role).read_text(encoding="utf-8")
    return text.split("\n---\n", 1)[1]


def charter_files():
    """Every file a charter is written in, index included."""
    return ([agent_path(role) for role in ROLES]
            + [skill_path(role) for role in ROLES]
            + [CHARTERS_INDEX])


def gate_sections(text):
    """Split the index on '## ' headings, keyed by heading text."""
    sections = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return {head: "\n".join(body) for head, body in sections.items()}


class TestRoleSet(unittest.TestCase):
    def test_nine_roles(self):
        """PRD-0001 §Actors names nine chartered roles."""
        self.assertEqual(len(ROLES), 9)
        self.assertEqual(len(set(ROLES)), 9)


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

    def test_charter_states_its_gate_obligation(self):
        """Every role works between the gates and none may cross one — the
        charter has to say which gate binds it (ADR-0033)."""
        for role in ROLES:
            with self.subTest(role=role):
                text = skill_path(role).read_text(encoding="utf-8")
                self.assertIn("ADR-0033", text)

    def test_merge_authority_tracks_the_amendment(self):
        """ADR-0036 amended ADR-0033's gate 3: the independent,
        non-authoring Reviewer merges when checks are green on the merge
        result, its review is recorded on the PR, and the PR is not a
        gate change — gate-change PRs and gates 1-2 stay human, and
        authors still never self-merge. A charter surface still claiming
        merge is unconditionally human trains the fleet against the
        accepted amendment, so the pre-amendment shorthands are pinned
        out and the surfaces that state merge authority cite ADR-0036.
        Text is whitespace-flattened first: charters hard-wrap prose, so
        a stale phrase can straddle a line break."""
        stale = ("human gate 3", "merge (human gate", "human merge gate",
                 "agents never merge", "no agent may merge",
                 "no agent merges", "merge is a human gate",
                 "merge is one of the three human gates",
                 "the human reads it at gate 3")
        surfaces = ([CHARTERS_INDEX]
                    + [skill_path(role) for role in ROLES]
                    + [agent_path(role) for role in ROLES])
        for path in surfaces:
            flat = " ".join(
                path.read_text(encoding="utf-8").split()).lower()
            for phrase in stale:
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertNotIn(phrase, flat)
        for path in (skill_path("reviewer"), agent_path("reviewer"),
                     CHARTERS_INDEX):
            with self.subTest(path=path.name, cites="ADR-0036"):
                self.assertIn("ADR-0036",
                              path.read_text(encoding="utf-8"))

    def test_stub_contract_keeps_the_load_bearing_rules(self):
        """The stub's compressed contract is a cache of the charter; a
        cache that silently drops an integrity rule is false, and the
        agent reading only the stub inherits the gap. Pin the rules this
        audit found dropped (2026-07-20): each phrase names a charter
        Must-never obligation the stub must keep carrying, in any
        wording that preserves the phrase."""
        keeps = {
            "pm": ("manufacture",),
            "architect": ("second source of truth",),
            "ux": ("report it as done",),
            "swe": ("weaken, skip, or delete",),
            "qa": ("fabricate", "weaken a criterion"),
            "support": ("invent a work-order row", "metric"),
            "toolsmith": ("fabricate", "eval, or test"),
        }
        for role, phrases in keeps.items():
            flat = " ".join(
                agent_path(role).read_text(encoding="utf-8").split()).lower()
            for phrase in phrases:
                with self.subTest(role=role, phrase=phrase):
                    self.assertIn(phrase, flat)

    def test_charter_and_stub_agree_on_the_band(self):
        for role in ROLES:
            with self.subTest(role=role):
                fields = protocol.read_frontmatter(agent_path(role)) or {}
                text = skill_path(role).read_text(encoding="utf-8")
                self.assertIn(f"`{fields.get('route')}`", text)


class TestNoSecondRoutingSource(unittest.TestCase):
    def test_no_charter_file_names_a_model_id(self):
        """Not just frontmatter: a model id anywhere in a charter competes
        with factory.json's routing table (ADR-0004, ADR-0034)."""
        models = routed_model_ids()
        for path in charter_files():
            text = path.read_text(encoding="utf-8")
            for model in models:
                with self.subTest(path=path.name, model=model):
                    self.assertNotIn(model, text)


class TestChartersIndex(unittest.TestCase):
    def test_index_exists(self):
        self.assertTrue(CHARTERS_INDEX.is_file(),
                        "missing factory/CHARTERS.md")

    def test_index_lists_every_role_and_both_of_its_files(self):
        text = CHARTERS_INDEX.read_text(encoding="utf-8")
        for role in ROLES:
            with self.subTest(role=role, file="agent"):
                self.assertIn(f"factory/agents/factory-{role}.md", text)
            with self.subTest(role=role, file="skill"):
                self.assertIn(f"factory/skills/{role}/SKILL.md", text)

    def test_index_carries_a_checklist_for_each_human_gate(self):
        sections = gate_sections(CHARTERS_INDEX.read_text(encoding="utf-8"))
        for gate in GATES:
            matches = [body for head, body in sections.items()
                       if gate.lower() in head.lower()]
            with self.subTest(gate=gate, has="section"):
                self.assertEqual(len(matches), 1,
                                 f"expected one '## ...{gate}...' section")
            with self.subTest(gate=gate, has="checklist"):
                self.assertGreaterEqual(len(CHECKBOX.findall(matches[0])), 3,
                                        f"{gate} checklist is too thin")

    def test_index_cites_the_gates_adr(self):
        self.assertIn("ADR-0033",
                      CHARTERS_INDEX.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
