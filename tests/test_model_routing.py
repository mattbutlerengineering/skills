"""WO-0007 acceptance evidence: model routing table + resolution.

WO-0007's acceptance criterion is "each type label resolves to a model id
from factory config; a unit test covers all three routes." That resolver
already exists: dispatching a work order (WO-0005, assembler.py) has to
turn a charter's routing *band* into a model id before it can run the
chartered agent, so `assembler.resolve_model` (band -> model, through
factory.json's `routing` table — the single routing source of truth per
ADR-0004/ADR-0034) and its coverage (tests/test_assembler.py
TestResolveModel) landed as part of WO-0005, ahead of this work order.

This file is WO-0007's own citable acceptance evidence, not a second
resolver: a `model_routing` module reimplementing band -> model would
itself be a second routing source of truth (ADR-0004) — the exact drift
ADR-0034 exists to catch (see tests/test_factory_charters.py
TestNoSecondRoutingSource, docs/features/software-factory/breakdown.md's
2026-07-12 note). assembler.py is the natural home WO-0005 already built;
this module exercises it end to end — through the REPO'S OWN factory.json
and its real charter stubs, not fixture copies — rather than
reimplementing it.

The "three routes" are the three routing bands ADR-0034 names: cheap
model for mechanical work, standard model for implementation, top model
for architecture and review.
"""
import unittest
from pathlib import Path

import assembler

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / "factory" / "agents"

ROUTES = ("mechanical", "implementation", "architecture_review")


def real_config():
    config, problems = assembler.load_config(REPO_ROOT)
    assert not problems, problems
    return config


class TestThreeRoutesAgainstTheRealConfig(unittest.TestCase):
    """Each of the three routing bands resolves to a model id from the
    repo's own factory.json — not a test fixture copy."""

    def test_all_three_routes_resolve_to_a_model_id(self):
        config = real_config()
        for band in ROUTES:
            with self.subTest(band=band):
                model, problems = assembler.resolve_model(band, config)
                self.assertEqual(problems, [])
                self.assertIsInstance(model, str)
                self.assertTrue(model)

    def test_the_real_routing_table_names_exactly_these_three_bands(self):
        self.assertEqual(set(real_config()["routing"]), set(ROUTES))


class TestTypeLabelToModelEndToEnd(unittest.TestCase):
    """The full chain a `type:` label travels to reach a model id:
    charter selection (assembler.select_charter) -> the charter's routing
    band, read from its real stub (assembler.charter_band) -> the model
    (assembler.resolve_model) — exercised against the real charter files
    WO-0014 shipped, not fixtures."""

    def resolve(self, labels):
        role = assembler.select_charter(labels)
        band, problems = assembler.charter_band(AGENTS_DIR, role)
        self.assertEqual(problems, [])
        model, problems = assembler.resolve_model(band, real_config())
        self.assertEqual(problems, [])
        return role, band, model

    def test_a_feature_label_routes_to_the_implementation_model(self):
        role, band, model = self.resolve(["type:feature"])
        self.assertEqual((role, band), ("swe", "implementation"))
        self.assertEqual(model, real_config()["routing"]["implementation"])

    def test_a_defect_label_routes_to_the_implementation_model(self):
        role, band, model = self.resolve(["type:defect"])
        self.assertEqual((role, band), ("swe", "implementation"))

    def test_a_chore_label_routes_to_the_implementation_model(self):
        role, band, model = self.resolve(["type:chore"])
        self.assertEqual((role, band), ("swe", "implementation"))

    def test_a_support_label_routes_to_the_mechanical_model(self):
        role, band, model = self.resolve(["type:support"])
        self.assertEqual((role, band), ("support", "mechanical"))
        self.assertEqual(model, real_config()["routing"]["mechanical"])

    def test_the_third_route_architecture_review_is_a_real_charter_band(self):
        """No `type:` label reaches architecture_review — the PM/architect/
        UX/reviewer roles produce human-gated artifacts and are never
        auto-dispatched by a ready label (assembler.select_charter has no
        entry for them; assembler.py's CHARTER_BY_TYPE docstring is
        explicit about this). The third route is still real: it is the
        band their charter stubs declare, and it resolves to a model like
        the other two."""
        band, problems = assembler.charter_band(AGENTS_DIR, "architect")
        self.assertEqual((band, problems), ("architecture_review", []))
        model, problems = assembler.resolve_model(band, real_config())
        self.assertEqual(problems, [])
        self.assertEqual(model, real_config()["routing"]["architecture_review"])


class TestUnknownBandFailsClosed(unittest.TestCase):
    """A band the routing table does not cover is a problem, never a
    silent default (ADR-0034) — resolve_model's fail-closed path."""

    def test_an_unrouted_band_is_a_problem_not_a_silent_default(self):
        config = {"routing": {"implementation": "claude-sonnet-5"}}
        model, problems = assembler.resolve_model("ghost-band", config)
        self.assertIsNone(model)
        self.assertEqual(problems, [
            "asm: factory.json routes no model to the ghost-band band"])


if __name__ == "__main__":
    unittest.main()
