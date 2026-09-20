"""Factory role charters (WO-0013, WO-0014) — file-contract tests.

The subagent registry keys agents by frontmatter `name:`, not filename —
a charter that fails these checks is silently undispatchable. Each role
is encoded as two files (agent stub + full charter in
factory/charters/<role>/CHARTER.md); tests assert the exact paths and
fields the dispatch plane (ADR-0032) depends on.

Charters carry a routing *band* (`route:`), never a model id: the band
resolves to a model through the per-repo `factory.json` routing table
(ADR-0034), which is the single routing source of truth (ADR-0004).
Resolution itself is `factory_config.resolve_model` (band -> model id),
pinned end to end against the real charter files here by WO-0007's
tests/test_model_routing.py — these tests only pin that the charters
name a real band and assert no model of their own.

The role vocabulary and both per-role paths are factory_roles' (the
seam, ADR-0047) — this file is a thin caller asserting the real files
honour it. `factory/CHARTERS.md` indexes the roles for the human reader
and carries the three human-gate checklists (ADR-0033).
"""
import re
import unittest
from pathlib import Path

import factory_config
import factory_roles
import protocol

REPO_ROOT = Path(__file__).resolve().parent.parent

ROLES = factory_roles.ROLES  # the seam owns the vocabulary (ADR-0047)

CHARTERS_INDEX = REPO_ROOT / "factory" / "CHARTERS.md"

# The three human gates of ADR-0033, in order. Each must appear in the
# index as a checklist the human owner can actually work through.
GATES = ("PRD approval", "Blueprint/ADR approval", "PR merge")

CHECKBOX = re.compile(r"^- \[ \] ", re.MULTILINE)


def agent_path(role):
    return factory_roles.agent_path(REPO_ROOT, role)


def charter_path(role):
    return factory_roles.charter_path(REPO_ROOT, role)


def real_config():
    """The repo's factory config through the one reader (factory_config
    .load, ADR-0037) — never a direct read of the template file."""
    config, problems = factory_config.load(REPO_ROOT)
    assert not problems, problems
    return config


def routing_bands():
    """The band names defined by the factory config's routing table."""
    return set(real_config()["routing"])


def routed_model_ids():
    """The model ids the routing table resolves bands to. No charter may
    name one — that would be a second routing source (ADR-0004)."""
    return set(real_config()["routing"].values())


def agent_body(role):
    """Text after the frontmatter block of the agent stub."""
    text = agent_path(role).read_text(encoding="utf-8")
    return text.split("\n---\n", 1)[1]


def charter_files():
    """Every file a charter is written in, index included."""
    return ([agent_path(role) for role in ROLES]
            + [charter_path(role) for role in ROLES]
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
            for field in factory_roles.REQUIRED_FIELDS:
                with self.subTest(role=role, field=field):
                    self.assertTrue(fields.get(field, "").strip(),
                                    f"factory-{role}.md {field} is empty")

    def test_body_loads_the_charter(self):
        for role in ROLES:
            with self.subTest(role=role):
                self.assertIn(f"factory/charters/{role}/CHARTER.md",
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

    def test_the_index_band_column_matches_each_stubs_route(self):
        """The CHARTERS.md Band column restates the stub's route for the
        human reader — pinned to the frontmatter so it cannot drift into
        a third, silently divergent band source."""
        text = CHARTERS_INDEX.read_text(encoding="utf-8")
        for role in ROLES:
            with self.subTest(role=role):
                row = next((line for line in text.splitlines()
                            if f"factory/agents/factory-{role}.md" in line),
                           None)
                self.assertIsNotNone(row, "CHARTERS.md has no table row"
                                          f" naming factory-{role}")
                band = row.rstrip().rstrip("|").rsplit("|", 1)[-1].strip()
                fields = protocol.read_frontmatter(agent_path(role)) or {}
                self.assertEqual(band.strip("`"), fields.get("route"),
                                 f"CHARTERS.md Band for {role} disagrees"
                                 " with the stub's route")


class TestCharterFiles(unittest.TestCase):
    def test_charter_file_exists(self):
        for role in ROLES:
            with self.subTest(role=role):
                self.assertTrue(charter_path(role).is_file(),
                                f"missing factory/charters/{role}/CHARTER.md")

    def test_charter_has_must_never_and_escalation_sections(self):
        for role in ROLES:
            text = charter_path(role).read_text(encoding="utf-8")
            with self.subTest(role=role, section="Must never"):
                self.assertIn("Must never", text)
            with self.subTest(role=role, section="Escalat"):
                self.assertIn("Escalat", text)

    def test_charter_states_its_gate_obligation(self):
        """Every role works between the gates and none may cross one — the
        charter has to say which gate binds it (ADR-0033)."""
        for role in ROLES:
            with self.subTest(role=role):
                text = charter_path(role).read_text(encoding="utf-8")
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
                    + [charter_path(role) for role in ROLES]
                    + [agent_path(role) for role in ROLES])
        for path in surfaces:
            flat = " ".join(
                path.read_text(encoding="utf-8").split()).lower()
            for phrase in stale:
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertNotIn(phrase, flat)
        for path in (charter_path("reviewer"), agent_path("reviewer"),
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
                text = charter_path(role).read_text(encoding="utf-8")
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
            with self.subTest(role=role, file="charter"):
                self.assertIn(f"factory/charters/{role}/CHARTER.md", text)

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


class TestTheVocabularyIsTheWholeDomain(unittest.TestCase):
    """The inverse direction, which nothing in this repo asserted.

    Every other check here iterates ROLES and asks whether the files
    honour it. None asks whether the files hold anything ROLES does not
    name — `charter_files()` is itself built from ROLES, so even the
    scan for a hard-coded model id has a ROLES-shaped domain. A stub at
    `factory/agents/factory-<x>.md` for an `x` outside the vocabulary is
    therefore dispatchable (the subagent registry keys on frontmatter
    `name:`, not on ROLES) and checked by nothing: not for a `route:`
    the factory config defines, not for an absent `model:`, not for a
    charter to pair with, not for a row in the index.

    That is the failure factory_roles exists to end — "adding a tenth
    role touched all of them, and nothing failed when they disagreed."
    The seam made the nine agree; it took a tenth to notice nothing
    fails on one.
    """

    AGENTS_DIR = REPO_ROOT / "factory" / "agents"
    CHARTERS_DIR = REPO_ROOT / "factory" / "charters"
    # Both path shapes the index spells a role in, so a row surviving a
    # role's removal is caught in whichever column still names it.
    INDEX_ROLES = re.compile(
        r"factory/agents/factory-([\w-]+)\.md"
        r"|factory/charters/([\w-]+)/CHARTER\.md")

    def test_every_agent_stub_on_disk_is_a_chartered_role(self):
        for path in sorted(self.AGENTS_DIR.glob("*.md")):
            with self.subTest(stub=path.name):
                self.assertTrue(path.name.startswith("factory-"),
                                f"{path.name} is not a factory-<role> stub")
                self.assertIn(path.stem[len("factory-"):], ROLES,
                              f"{path.name} is dispatchable but names no"
                              " role in factory_roles.ROLES")

    def test_every_charter_directory_on_disk_is_a_chartered_role(self):
        for path in sorted(p for p in self.CHARTERS_DIR.iterdir()
                           if p.is_dir()):
            with self.subTest(charter=path.name):
                self.assertIn(path.name, ROLES,
                              f"factory/charters/{path.name}/ names no role"
                              " in factory_roles.ROLES")

    def test_the_index_names_no_role_the_vocabulary_dropped(self):
        text = CHARTERS_INDEX.read_text(encoding="utf-8")
        for stub_role, charter_role in self.INDEX_ROLES.findall(text):
            role = stub_role or charter_role
            with self.subTest(role=role):
                self.assertIn(role, ROLES,
                              f"CHARTERS.md still lists {role!r}, which"
                              " factory_roles.ROLES does not name")


if __name__ == "__main__":
    unittest.main()
