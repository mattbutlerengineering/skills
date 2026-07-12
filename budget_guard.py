#!/usr/bin/env python3
"""budget_guard: the ADR-0034 stop-or-continue check for a dispatched work
order — CONTINUE while spend is within its size class's dollar budget,
HARD-STOP at or over it. Conventions match assembler.py: functions return
bg:-prefixed problem strings; the CLI prints them and exits nonzero.

This is one of THREE uncorrelated stops ADR-0034 puts around every
dispatched run (token budget, max-turns cap, wall-clock timeout) — the
dollar-budget stop, checked against the run's own running spend. Exhaustion
is a HANDOFF, not a failure (ADR-0034): hard_stop pushes whatever is on
disk (push_wip), composes and posts a handoff naming the remaining
acceptance criteria (handoff.compose / handoff.post_handoff), and appends
the run's line to the append-only cost ledger (ledger_entry /
append_ledger_line) — RESILIENTLY, so a WIP-push failure (the normal
no-upstream case) still leaves the handoff and ledger behind. See
docs/adr/0034-work-order-budgets-and-routing.md.

  python3 budget_guard.py check <size> <spend_usd>
        Resolve <size>'s dollar budget from factory.json and print CONTINUE
        or HARD-STOP against <spend_usd>. Exits nonzero only on a genuine
        misconfiguration (fails CLOSED: an unresolvable budget prints
        HARD-STOP and still exits nonzero, so a broken config can never
        silently wave a run through).
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import gates
import handoff
from assembler import load_config
from gates import COST_LEDGER, LEDGER_FIELDS

CONTINUE = "CONTINUE"
HARD_STOP = "HARD-STOP"

# A failed or missing git raises one of these; push_wip turns them into a
# bg: problem string instead of a traceback (same discipline as
# label_sync.GH_FAILURES).
GIT_FAILURES = (subprocess.CalledProcessError, OSError)


def resolve_budget(size, config):
    """(budget_usd, problems): <size>'s dollar ceiling from factory.json's
    budgets_usd table (ADR-0034) — the single routing source of truth, same
    shape as assembler.resolve_model. A size the table does not cover, or a
    non-positive budget, is a problem, never a silent default."""
    budgets = config.get("budgets_usd")
    if not isinstance(budgets, dict):
        return None, ["bg: factory.json has no budgets_usd table"]
    budget = budgets.get(size)
    if isinstance(budget, bool) or not isinstance(budget, (int, float)) \
            or budget <= 0:
        return None, [
            f"bg: factory.json names no positive budget for size {size!r}"]
    return budget, []


def _validate_spend(spend_usd):
    """Spend-so-far must be a finite, non-negative number — the boundary
    check coding-style.md demands (never trust the caller's input). A
    negative spend, NaN, or infinity is nonsense that would slip past
    decide's `>=` comparison and silently CONTINUE, so it is a problem
    here and guard fails CLOSED on it (ADR-0034: an unaccountable run is
    treated as out of budget, never waved through)."""
    if isinstance(spend_usd, bool) or not isinstance(spend_usd, (int, float)) \
            or not math.isfinite(spend_usd) or spend_usd < 0:
        return [f"bg: spend {spend_usd!r} is not a finite, non-negative"
                " number"]
    return []


def decide(spend_usd, budget_usd):
    """(verdict, reason): CONTINUE while spend is strictly under budget,
    HARD-STOP at or over it — a run that has just reached its ceiling has
    no more to spend. Pure: the comparison alone is the ADR-0034 stop rule;
    resolving the budget (and failing closed when that is not possible) is
    guard's concern."""
    if spend_usd >= budget_usd:
        return HARD_STOP, (f"bg: spend ${spend_usd:.2f} has reached or"
                           f" exceeded the ${budget_usd:.2f} budget")
    return CONTINUE, (f"bg: spend ${spend_usd:.2f} is within the"
                      f" ${budget_usd:.2f} budget")


def guard(root, size, spend_usd, config=None):
    """(verdict, reason, problems): resolve <size>'s budget (from the repo's
    factory.json, or an injected `config` for tests/callers that already
    have it) and decide against spend_usd. FAILS CLOSED: any resolution
    problem hard-stops rather than letting an unaccountable run continue —
    an agent that cannot prove it is in budget is treated as out of it."""
    problems = _validate_spend(spend_usd)
    if problems:
        return HARD_STOP, "bg: invalid spend — failing closed", problems
    if config is None:
        config, problems = load_config(root)
        if problems:
            return (HARD_STOP, "bg: no budget could be resolved — failing"
                    " closed", problems)
    budget_usd, problems = resolve_budget(size, config)
    if problems:
        return (HARD_STOP, "bg: no budget could be resolved — failing"
                " closed", problems)
    verdict, reason = decide(spend_usd, budget_usd)
    return verdict, reason, []


def git_runner(args):
    """The real git CLI, same shape as label_sync.gh_runner: a failed or
    missing git raises (GIT_FAILURES), and push_wip turns that into a bg:
    problem string rather than a traceback."""
    return subprocess.run(["git", *args], check=True, capture_output=True,
                          text=True)


def _git_detail(err):
    """One-line detail for a failed git call's bg: problem string: git's own
    stderr when it ran, else the OS error (mirrors label_sync.gh_detail)."""
    stderr = (getattr(err, "stderr", None) or "").strip()
    return stderr.splitlines()[-1] if stderr else str(err)


def push_wip(wo, run=git_runner):
    """Commit and push whatever is on disk under `wo`'s name, returning a
    list of bg: problems (empty on success) — ADR-0034: a run that hits its
    budget preserves its work-in-progress, it never discards it. `run` is an
    injected command runner (same shape as label_sync.gh_runner) so tests
    never touch a real repository. --allow-empty: a run that hard-stops
    before changing a file still needs a commit to push.

    A push failure NEVER raises. The normal hard-stop state is a fresh WO
    branch with no upstream, where `git push` exits 128; because push_wip
    runs BEFORE the handoff and ledger (hard_stop), an uncaught crash here
    would swallow the accountability record ADR-0034 promises ("a handoff
    comment to read", not "a bill to dispute"). So the failure is caught
    and surfaced as a problem, and hard_stop still completes."""
    try:
        run(["add", "-A"])
        run(["commit", "-m", f"wip({wo}): budget exhausted", "--allow-empty"])
        run(["push"])
    except GIT_FAILURES as err:
        return [f"bg: pushing {wo} WIP failed: {_git_detail(err)}"]
    return []


def hard_stop(root, wo, reason, done, remaining, resume, *, run_id, model,
              tokens, cost, outcome="budget-exhausted", run=git_runner,
              post=print):
    """The ADR-0034 hard-stop sequence, made RESILIENT: push WIP, post the
    handoff, append the ledger line — in that order, but a push failure
    NEVER prevents the handoff and ledger from being produced. The handoff
    and the ledger line ARE the accountability record; they must exist even
    when the WIP push fails (a fresh WO branch with no upstream, git exit
    128, is the normal case). Returns any bg: problems (a failed push),
    having still completed the handoff + ledger. Pure orchestration over the
    tested pieces; all IO is injected (run/post) so tests need touch neither
    git nor the network.

    done/remaining are short acceptance-criterion strings the run tracked,
    never a raw issue body — handoff.compose draws that ADR-0032 boundary."""
    problems = push_wip(wo, run=run)
    handoff.post_handoff(
        handoff.compose(wo, reason, done, remaining, resume), post=post)
    append_ledger_line(root, ledger_entry(
        wo, run_id, model, tokens, cost, outcome))
    return problems


def ledger_entry(wo, run_id, model, tokens, cost, outcome):
    """A well-formed docs/factory/costs.jsonl record (ADR-0034), built from
    gates.LEDGER_FIELDS so the field set cannot drift from what detector G
    checks — the single place a caller assembles one."""
    return dict(zip(LEDGER_FIELDS, (wo, run_id, model, tokens, cost, outcome)))


def append_ledger_line(root, entry):
    """Append one line to docs/factory/costs.jsonl. APPEND ONLY: opens in
    "a" mode and never reads or rewrites existing lines — the ledger is the
    factory's measurement substrate and gets the same append-only
    discipline as evals/results/ (CLAUDE.md eval honesty)."""
    ledger = Path(root) / COST_LEDGER
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def main(argv):
    if len(argv) == 3 and argv[0] == "check":
        _, size, spend_raw = argv
        try:
            spend_usd = float(spend_raw)
        except ValueError:
            print(f"bg: {spend_raw!r} is not a number")
            print("budget_guard: 1 problem(s)")
            return 1
        root = gates.repo_root()
        verdict, reason, problems = guard(root, size, spend_usd)
        print(reason)
        for problem in problems:
            print(problem)
        print(verdict)
        print(f"budget_guard: {len(problems)} problem(s)")
        return 1 if problems else 0
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
