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

Conventions match gates.py: functions return (value, problems) with
config:-prefixed problem strings; a field the config does not cover is a
problem, never a silent default.
"""
import json
from pathlib import Path


def load(root):
    """(the factory config, problems): the installed .github/factory.json
    when stamped, else the template payload copy — same fallback shape as
    label_sync.load_labels."""
    root = Path(root)
    candidates = (root / ".github" / "factory.json",
                  root / "factory" / "templates" / "factory.json")
    path = next((p for p in candidates if p.is_file()), None)
    if path is None:
        return None, ["config: missing factory.json (.github/factory.json or"
                      " factory/templates/factory.json)"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as err:
        rel = path.relative_to(root).as_posix()
        return None, [f"config: {rel} is not valid JSON: {err}"]


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


def resolve_budget(size, config):
    """(budget_usd, problems): <size>'s dollar ceiling from factory.json's
    budgets_usd table (ADR-0034). A size the table does not cover, or a
    non-positive budget, is a problem, never a silent default."""
    budgets = config.get("budgets_usd")
    if not isinstance(budgets, dict):
        return None, ["config: factory.json has no budgets_usd table"]
    budget = budgets.get(size)
    if isinstance(budget, bool) or not isinstance(budget, (int, float)) \
            or budget <= 0:
        return None, [
            f"config: factory.json names no positive budget for size {size!r}"]
    return budget, []


def resolve_cap(config):
    """(cap_usd, problems): factory.json's monthly_cap_usd — the single
    repo-wide ceiling ADR-0034's circuit breaker checks total spend
    against, same fail-closed shape as resolve_budget's per-size lookup."""
    cap = config.get("monthly_cap_usd")
    if isinstance(cap, bool) or not isinstance(cap, (int, float)) \
            or cap <= 0:
        return None, ["config: factory.json names no positive monthly_cap_usd"]
    return cap, []
