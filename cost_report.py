#!/usr/bin/env python3
"""cost_report: the ADR-0034 weekly rollup and monthly circuit breaker.
Recomputes spend numbers from docs/factory/costs.jsonl — read through
cost_ledger.read, the same line grammar detector G gates in CI (ADR-0037),
so the report's reader cannot diverge from the CI rule — and decides
whether total spend has crossed factory.json's monthly_cap_usd.
Conventions match budget_guard.py: functions return cr:-prefixed problem
strings (ledger problems keep cost_ledger's ledger: prefix, the same way
validator.py surfaces label_sync's L: strings); the CLI prints them and
exits nonzero.

This module COMPUTES ONLY: aggregate the ledger, decide PAUSE/CONTINUE
against the cap, and compose the report text. All IO is injected (the
ledger path, the clock) so it is unit-testable without touching real time
or a real repository, and it never shells out to gh. The workflow
(.github/workflows/cost-report.yml) is the one that MUTATES — it posts the
report issue and, on a PAUSE verdict, sets the FACTORY_PAUSED repo
variable (`gh variable set`, readable as `vars.FACTORY_PAUSED` by any
workflow's `if:`, the same vars.* convention sweeps.yml's Sentry job and
validator.yml's FACTORY_REVIEW_LOGIN already use) — both real gh
mutations, so they stay in the YAML, never here.

  python3 cost_report.py report
        Recompute spend from docs/factory/costs.jsonl, decide against
        factory.json's monthly_cap_usd, and write title/body/pause/reason
        to $GITHUB_OUTPUT for the workflow's gh steps. Exits nonzero only
        on a genuine misconfiguration (fails CLOSED: an unreadable ledger
        or unresolvable cap decides PAUSE and still exits nonzero, so a
        broken config can never silently wave spend through unpaused).
"""
import os
import sys
from datetime import datetime, timezone

import cost_ledger
import factory_config
from cli import write_outputs
from knowledge_plane import repo_root

PAUSE = "PAUSE"
CONTINUE = "CONTINUE"


def aggregate(entries):
    """PURE: recompute the weekly report's numbers from already-parsed
    ledger entries — total spend, total tokens, run count, and spend by
    work order. Trusts the full ledger shape cost_ledger.read already
    established (coding-style.md: no defensive re-validation of an
    invariant enforced one call up)."""
    total_cost = 0.0
    total_tokens = 0
    by_wo = {}
    for entry in entries:
        cost = entry["cost"]
        total_cost += cost
        total_tokens += entry["tokens"]
        by_wo[entry["wo"]] = by_wo.get(entry["wo"], 0.0) + cost
    return {
        "total_cost": round(total_cost, 2),
        "total_tokens": total_tokens,
        "run_count": len(entries),
        "by_wo": {wo: round(cost, 2) for wo, cost in by_wo.items()},
    }


def decide(total_cost, cap):
    """(verdict, reason): PAUSE once total spend has reached or crossed the
    monthly cap — the same >= boundary as budget_guard.decide (a month that
    has just reached its ceiling has no more to spend)."""
    if total_cost >= cap:
        return PAUSE, (f"cr: spend ${total_cost:.2f} has reached or"
                       f" exceeded the ${cap:.2f} monthly cap — pausing"
                       " dispatch (FACTORY_PAUSED)")
    return CONTINUE, (f"cr: spend ${total_cost:.2f} is within the"
                      f" ${cap:.2f} monthly cap")


def guard(root, config=None, ledger_path=None):
    """(verdict, reason, totals, cap, problems): recompute spend from the
    ledger and decide against factory.json's monthly cap. FAILS CLOSED: any
    read or resolution problem decides PAUSE rather than letting
    unaccountable spend continue — a report that cannot prove it is under
    the cap is treated as over it (same discipline as budget_guard.guard).
    totals is always the best-effort aggregate of what WAS readable, even
    on a failing path, so a human reading the report still sees something."""
    entries, problems = cost_ledger.read(root, ledger_path=ledger_path)
    totals = aggregate(entries)
    if problems:
        return PAUSE, "cr: unreadable ledger — failing closed", totals, \
            None, problems
    if config is None:
        config, problems = factory_config.load(root)
        if problems:
            return (PAUSE, "cr: no monthly cap could be resolved — failing"
                    " closed", totals, None, problems)
    cap, problems = factory_config.resolve_cap(config)
    if problems:
        return (PAUSE, "cr: no monthly cap could be resolved — failing"
                " closed", totals, None, problems)
    verdict, reason = decide(totals["total_cost"], cap)
    return verdict, reason, totals, cap, []


def report_title(as_of):
    """The weekly report issue's title, date-stamped by the injected
    clock."""
    return f"Factory cost report — {as_of}"


def compose_report(totals, verdict, reason, cap, as_of):
    """The weekly report issue body: total spend against the monthly cap, a
    by-work-order breakdown, and the pause verdict. Deterministic text,
    easy to assert on and easy to skim (same discipline as
    handoff.compose). cap is None only on a failing-closed guard() path
    (no cap could be resolved); shown honestly rather than faked."""
    cap_text = f"${cap:.2f}" if cap is not None else "unknown"
    lines = [f"## {report_title(as_of)}", "",
             f"**Total spend:** ${totals['total_cost']:.2f} of {cap_text}"
             " monthly cap",
             f"**Runs recorded:** {totals['run_count']}",
             f"**Total tokens:** {totals['total_tokens']}", "",
             "### By work order"]
    if totals["by_wo"]:
        for wo in sorted(totals["by_wo"]):
            lines.append(f"- {wo}: ${totals['by_wo'][wo]:.2f}")
    else:
        lines.append("- (no runs recorded)")
    lines += ["", "### Verdict", reason.strip()]
    return "\n".join(lines) + "\n"


def _utcnow():
    return datetime.now(timezone.utc)


def run_report(root, clock=None, ledger_path=None):
    """(outputs, problems) for the `report` command: recompute spend,
    decide PAUSE/CONTINUE, and compose everything the workflow's gh steps
    need — title, body, pause ('true'/'false'), reason — as $GITHUB_OUTPUT
    values. The workflow, never this module, runs `gh issue create` and
    `gh variable set FACTORY_PAUSED` (the compute/mutate boundary)."""
    clock = clock or _utcnow
    as_of = clock().date().isoformat()
    verdict, reason, totals, cap, problems = guard(
        root, ledger_path=ledger_path)
    outputs = {
        "pause": "true" if verdict == PAUSE else "false",
        "title": report_title(as_of),
        "body": compose_report(totals, verdict, reason, cap, as_of),
        "reason": reason,
    }
    return outputs, problems


def main(argv, env=None, clock=None):
    env = os.environ if env is None else env
    root = repo_root()
    if argv == ["report"]:
        outputs, problems = run_report(root, clock=clock)
        write_outputs(env, outputs)
        if outputs.get("reason"):
            print(outputs["reason"])
    else:
        print(__doc__.strip())
        return 2
    for problem in problems:
        print(problem)
    print(f"cost_report: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
