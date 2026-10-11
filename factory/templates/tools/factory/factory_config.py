#!/usr/bin/env python3
"""factory_config: the one reader of the factory config (ADR-0034,
ADR-0037) — .github/factory.json when stamped, else the template payload
copy — and the fail-closed accessors over its fields.

Before this seam the config had four runtime homes: assembler.py owned
load_config and the band->model resolver, budget_guard.py and
cost_report.py each grew a sibling resolve_* — and both imported the
DISPATCHER for the privilege of reading a config file. The schema now
lives behind one interface; factory.json stays the single routing source
of truth (ADR-0004), resolved in exactly one place, and detector F
(gates.check_config_shape) remains the CI gate over the whole shape.

This module also owns the vocabularies its accessors resolve over
(ADR-0048): BANDS, the legal routing bands; EFFORTS, the legal values of
the optional effort table (PRD-0013); and ARTIFACT_HOMES /
artifact_paths, the installed-vs-payload location grammar every
dual-home factory artifact is read through.

Conventions match gates.py: functions return (value, problems) with
config:-prefixed problem strings; a field the config does not cover is a
problem, never a silent default.
"""
import math
from pathlib import Path

from cli import read_file

# The routing-band vocabulary (ADR-0034): the exact key set factory.json's
# routing table must map. One home (ADR-0048) — gates' detector F and the
# WO-0007 acceptance evidence read this tuple. resolve_model stays
# fail-closed per lookup, so a band outside the vocabulary is already a
# problem there without a second membership check.
BANDS = ("mechanical", "implementation", "architecture_review")

# The effort vocabulary (PRD-0013): the values factory.json's optional
# effort table may map a band to, the harness's own --effort choices.
EFFORTS = ("low", "medium", "high", "xhigh", "max")

# The installed-vs-payload location grammar (ADR-0048): artifact name ->
# (installed rel to the repo root, payload rel to factory/ — the manifest
# key grammar of gates.manifest_files). The .github/ asymmetry is stated
# here once: factory.json sits at the payload root and is mapped at stamp
# time (factory_init.INSTALL_MAP derives from this table); labels.json
# already sits under templates/.github/, so the stamp's default strip
# rule lands it installed.
ARTIFACT_HOMES = {
    "factory.json": (".github/factory.json", "templates/factory.json"),
    "labels.json": (".github/labels.json",
                    "templates/.github/labels.json"),
}


def artifact_paths(root, name):
    """The ordered candidate homes of a dual-home factory artifact:
    ((installed path, True), (payload path, False)) — installed first,
    the read order every runtime loader uses (load here,
    label_sync.load_labels); detector F checks every candidate. `name`
    must be an ARTIFACT_HOMES key — call sites pass literals, so a typo
    is a KeyError at test time, not a runtime state."""
    installed, payload = ARTIFACT_HOMES[name]
    root = Path(root)
    return ((root / installed, True),
            (root / "factory" / payload, False))


def load(root):
    """(the factory config, problems): the installed .github/factory.json
    when stamped, else the template payload copy — the first existing
    candidate in artifact_paths' installed-first order, same fallback
    shape as label_sync.load_labels."""
    root = Path(root)
    candidates = artifact_paths(root, "factory.json")
    # The first home that is there decides, broken or not: only absence
    # moves on to the next. dict, because every accessor below subscripts
    # the config — detector F asks read_file the same question, so the
    # runtime reader and the CI gate cannot disagree about it (ADR-0075).
    for path, _ in candidates:
        config, problem = read_file(
            path, path.relative_to(root).as_posix(), dict)
        if problem:
            return None, [f"config: {problem}"]
        if config is not None:
            return config, []
    homes = " or ".join(p.relative_to(root).as_posix() for p, _ in candidates)
    return None, [f"config: missing factory.json ({homes})"]


def resolve_model(band, config):
    """(the model id for this band, problems) through factory.json's routing
    table — the single routing source of truth (ADR-0004/0034). A band the
    table does not cover is a problem, never a silent default."""
    routing = config.get("routing")
    if not isinstance(routing, dict):
        return None, ["config: factory.json has no routing table"]
    model = routing.get(band)
    if not isinstance(model, str) or not model:
        return None, [
            f"config: factory.json routes no model to the {band} band"]
    return model, []


def resolve_effort(band, config):
    """(the effort for this band, problems) through factory.json's effort
    table, which sits beside routing (PRD-0013). Fail-closed like
    resolve_model: no table, or a band it does not map to an EFFORTS
    value, is a problem, never a silent default."""
    efforts = config.get("effort")
    if not isinstance(efforts, dict):
        return None, ["config: factory.json has no effort table"]
    effort = efforts.get(band)
    if effort not in EFFORTS:
        return None, [
            f"config: factory.json names no effort for the {band} band"]
    return effort, []


def _positive_number(value):
    """True for a finite positive int/float that is not a bool — True is
    an int in Python, and a bool where a dollar amount belongs is a typo.

    Finite because an infinite amount is not a ceiling: `total >= inf` is
    false at every spend, so an infinite monthly_cap_usd would leave
    ADR-0034's breaker returning CONTINUE forever, and json.loads accepts
    a bare Infinity literal straight from factory.json. cost_report.decide
    already refuses a non-finite SPEND with that reasoning; the comparison
    has two sides. NaN needs no clause — `nan > 0` is already false."""
    return (not isinstance(value, bool)
            and isinstance(value, (int, float))
            and math.isfinite(value) and value > 0)


def resolve_budget(size, config):
    """(budget_usd, problems): <size>'s dollar ceiling from factory.json's
    budgets_usd table (ADR-0034). A size the table does not cover, or a
    non-positive budget, is a problem, never a silent default."""
    budgets = config.get("budgets_usd")
    if not isinstance(budgets, dict):
        return None, ["config: factory.json has no budgets_usd table"]
    if not _positive_number(budgets.get(size)):
        return None, [
            f"config: factory.json names no positive budget for size {size!r}"]
    return budgets[size], []


def resolve_cap(config):
    """(cap_usd, problems): factory.json's monthly_cap_usd — the single
    repo-wide ceiling ADR-0034's circuit breaker checks total spend
    against, same fail-closed shape as resolve_budget's per-size lookup."""
    if not _positive_number(config.get("monthly_cap_usd")):
        return None, ["config: factory.json names no positive monthly_cap_usd"]
    return config["monthly_cap_usd"], []


def config_problems(config):
    """Field-grammar problems for a parsed factory config, unprefixed.

    The one home for what a valid field VALUE is (twin of
    cost_ledger.line_problems): the resolve_* accessors above apply the
    same rules fail-closed per lookup, and gates' detector F prefixes
    these problems and layers its whole-shape key-set cross-checks
    (exactly S/M/L, exactly the routed bands) on top. Key-set
    completeness stays with the gate — a missing entry is a shape
    concern, not a value one.
    """
    problems = []
    budgets = config.get("budgets_usd")
    if isinstance(budgets, dict):
        problems += [f"budgets_usd.{size} must be a positive number"
                     for size, value in budgets.items()
                     if not _positive_number(value)]
    routing = config.get("routing")
    if isinstance(routing, dict):
        problems += [f"routing.{route} must name a model id"
                     for route, model in routing.items()
                     if not isinstance(model, str) or not model]
    wip = config.get("wip_cap")
    if isinstance(wip, bool) or not isinstance(wip, int) or wip < 1:
        problems.append("wip_cap must be a positive integer")
    if not _positive_number(config.get("monthly_cap_usd")):
        problems.append("monthly_cap_usd must be a positive number")
    efforts = config.get("effort")
    if isinstance(efforts, dict):
        problems += [f"effort.{band} must be one of {', '.join(EFFORTS)}"
                     for band, effort in efforts.items()
                     if effort not in EFFORTS]
    return problems
