"""The dual-membership set that blocks the tools/factory/ restructure.

ADR-0091 records which mirrored modules root-only tools import, and the
one mirrored module that imports a root-only tool. Three earlier ADRs
quoted that set by hand and every number drifted. This test derives it
from the tree (an AST walk over every root *.py against
factory_init.MIRRORS) and pins it, so a change to the set fails here
and has to be recorded rather than discovered by the next review.
"""
import ast
import unittest
from pathlib import Path

import factory_init

REPO_ROOT = Path(__file__).resolve().parent.parent

# ADR-0091's table as (root-only importer, mirrored module) pairs:
# 50 pairs over nine mirrored modules (ADR-0097 added fast_path to the
# cli.py row; ADR-0106 added pr_body_preflight to the cli.py and gates.py
# rows; ADR-0110 added decompose_signals to the cli.py, knowledge_plane.py
# and protocol.py rows; ADR-0112 added size_band_calibration to the cli.py,
# knowledge_plane.py, cost_ledger.py and factory_config.py rows). The pairs
# land one per item as the module grows its imports.
ROOT_ONLY_IMPORTS_MIRRORED = frozenset(
    {(tool, "cli") for tool in (
        "adr_status", "board", "charter_recorded", "charter_replay",
        "dashboard", "decompose_signals", "eval_schema", "factory_init",
        "fast_path", "kb", "kb_drift", "kb_harvest", "launch_demo", "lint",
        "md_claims", "one_owner", "plane_drift", "pr_body_preflight",
        "sweeps", "trigger_eval",
    )}
    | {(tool, "knowledge_plane") for tool in (
        "adr_status", "board", "dashboard", "decompose_signals", "kb",
        "kb_drift", "lint", "md_claims", "one_owner", "plane_drift",
        "size_band_calibration", "sweeps",
    )}
    | {(tool, "protocol") for tool in (
        "board", "dashboard", "decompose_signals", "kb", "kb_drift", "lint",
        "trigger_eval",
    )}
    | {
        ("dashboard", "factory_config"), ("factory_init", "factory_config"),
        ("dashboard", "cost_ledger"), ("dashboard", "cost_report"),
        ("size_band_calibration", "cost_ledger"),
        ("size_band_calibration", "factory_config"),
        ("dashboard", "human_gates"), ("factory_init", "gates"),
        ("sweeps", "label_sync"), ("pr_body_preflight", "gates"),
    })

# The other direction: conductor_merge reads MIRRORS from the stamper in
# a function-level import that only runs in the factory source repo.
MIRRORED_IMPORTS_ROOT_ONLY = frozenset({("conductor_merge", "factory_init")})


def mirrored_modules():
    """Module names of the root .py files MIRRORS ships into the payload."""
    return {Path(name).stem for name, _, _ in factory_init.MIRRORS
            if name.endswith(".py") and "/" not in name}


def sibling_imports(path, modules):
    """Root modules `path` imports, at any depth (function-level too)."""
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 \
                and node.module:
            found.add(node.module.split(".")[0])
    return (found & modules) - {path.stem}


def crossing_pairs():
    """(importer, imported) pairs that cross the mirror boundary, split
    by direction: root-only -> mirrored, and mirrored -> root-only."""
    paths = sorted(REPO_ROOT.glob("*.py"))
    modules = {path.stem for path in paths}
    mirrored = mirrored_modules()
    inward, outward = set(), set()
    for path in paths:
        for imported in sibling_imports(path, modules):
            if path.stem not in mirrored and imported in mirrored:
                inward.add((path.stem, imported))
            elif path.stem in mirrored and imported not in mirrored:
                outward.add((path.stem, imported))
    return inward, outward


class DualMembershipPinned(unittest.TestCase):
    """Growing or shrinking either set is a decision: record it in a new
    ADR that supersedes ADR-0091's table, then update the pin."""

    def test_every_mirrored_source_is_a_root_file(self):
        missing = sorted(m for m in mirrored_modules()
                         if not (REPO_ROOT / f"{m}.py").is_file())
        self.assertEqual(missing, [])

    def test_root_only_tools_import_exactly_the_pinned_mirrored_modules(self):
        inward, _ = crossing_pairs()
        self.assertEqual(
            sorted(inward), sorted(ROOT_ONLY_IMPORTS_MIRRORED),
            "the root-only -> mirrored import set moved; record it in an "
            "ADR superseding ADR-0091's table, then update this pin")

    def test_mirrored_modules_import_exactly_the_pinned_root_only_tools(self):
        _, outward = crossing_pairs()
        self.assertEqual(
            sorted(outward), sorted(MIRRORED_IMPORTS_ROOT_ONLY),
            "the mirrored -> root-only import set moved; record it in an "
            "ADR superseding ADR-0091's table, then update this pin")


if __name__ == "__main__":
    unittest.main()
