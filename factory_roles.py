#!/usr/bin/env python3
"""factory_roles: the factory role vocabulary (ADR-0047) — the nine
chartered roles PRD-0001 §Actors names, and the two files each role is
encoded in (agent stub + charter; factory/CHARTERS.md indexes both for
the human reader).

Before this seam the role set had four homes that never imported each
other: tests/test_factory_charters.py's ROLES tuple (a vocabulary living
in tests), charter_replay.py's three-role literal (a TODO encoded as a
constant), assembler.py's CHARTER_BY_TYPE label map, and
factory/CHARTERS.md's prose index. Adding a tenth role touched all of
them, and nothing failed when they disagreed. The shared-module bar
(CLAUDE.md: multiple real callers AND observed divergence) is met — the
copies had already diverged, 9 vs 3 vs 2.
"""
from pathlib import Path

# The chartered roles (PRD-0001 §Actors; the engineer ships as `swe`).
ROLES = ("pm", "architect", "ux", "planner", "swe", "qa", "reviewer",
         "support", "toolsmith")

# The frontmatter fields a dispatchable agent stub must carry beyond
# `name:` (the subagent-registry key): what the dispatch plane reads
# (ADR-0032). `route:` names a routing band, never a model id (ADR-0034).
REQUIRED_FIELDS = ("description", "tools", "route")


def charter_path(root, role):
    """The role's authoritative charter file."""
    return Path(root) / "factory" / "charters" / role / "CHARTER.md"


def agent_path(root, role):
    """The role's dispatchable agent stub (frontmatter keyed by name:)."""
    return Path(root) / "factory" / "agents" / f"factory-{role}.md"
