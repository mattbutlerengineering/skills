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
acceptance criteria (handoff.compose), and appends the run's line to the
append-only cost ledger (cost_ledger.entry / cost_ledger.append) —
RESILIENTLY, so a WIP-push failure (the normal no-upstream case) still
leaves the handoff and ledger behind. See
docs/adr/0034-work-order-budgets-and-routing.md.

  python3 budget_guard.py check <size> <spend_usd>
        Resolve <size>'s dollar budget from factory.json and print CONTINUE
        or HARD-STOP against <spend_usd>. Exits nonzero only on a genuine
        misconfiguration (fails CLOSED: an unresolvable budget prints
        HARD-STOP and still exits nonzero, so a broken config can never
        silently wave a run through).
"""
import math
import sys

import cost_ledger
import factory_config
import handoff
from cli import CLI_FAILURES as GIT_FAILURES
from cli import detail as _git_detail
from cli import report, runner
from knowledge_plane import repo_root

CONTINUE = "CONTINUE"
HARD_STOP = "HARD-STOP"


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
        config, problems = factory_config.load(root)
        if problems:
            return (HARD_STOP, "bg: no budget could be resolved — failing"
                    " closed", problems)
    budget_usd, problems = factory_config.resolve_budget(size, config)
    if problems:
        return (HARD_STOP, "bg: no budget could be resolved — failing"
                " closed", problems)
    verdict, reason = decide(spend_usd, budget_usd)
    return verdict, reason, []


# The real git CLI (cli.runner): a failed or missing git raises
# GIT_FAILURES, and push_wip turns that into a bg: problem string rather
# than a traceback.
git_runner = runner("git")


def push_wip(wo, run=git_runner):
    """Commit and push whatever is on disk under `wo`'s name, returning a
    list of bg: problems (empty on success) — ADR-0034: a run that hits its
    budget preserves its work-in-progress, it never discards it. `run` is an
    injected command runner (same shape as cli.gh_runner) so tests
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
              tokens, cost, at, outcome="budget-exhausted", run=git_runner,
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
    never a raw issue body — handoff.compose draws that ADR-0032 boundary.
    `at` is the UTC date the caller stamps on the ledger row (injected,
    not computed here, to keep the function's IO injected)."""
    problems = push_wip(wo, run=run)
    post(handoff.compose(wo, reason, done, remaining, resume))
    cost_ledger.append(root, cost_ledger.entry(
        wo, run_id, model, tokens, cost, outcome, at))
    return problems


def main(argv):
    if len(argv) == 3 and argv[0] == "check":
        _, size, spend_raw = argv
        try:
            spend_usd = float(spend_raw)
        except ValueError:
            return report("budget_guard",
                          [f"bg: {spend_raw!r} is not a number"])
        root = repo_root()
        verdict, reason, problems = guard(root, size, spend_usd)
        print(reason)
        print(verdict)
        return report("budget_guard", problems)
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
