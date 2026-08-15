# The budget hook and payload charters stay deferred

- Status: accepted
- Date: 2026-08-14

## Context

The software-factory run's review (review.md, 2026-08-13) surfaced two
gaps against ADR-0034 and the stamped-repo story, and the operator
arbitrated both to *deferred* rather than into the fix package:

- **The token-budget hook.** ADR-0034 names three uncorrelated mechanical
  stops on a dispatched agent run: a token-budget hook (80% warns, 100%
  blocks tool use), a max-turns cap, and the job's wall-clock timeout.
  Only the hook reads the session transcript; the other two are flags the
  harness and GitHub Actions already understand. No hook exists yet —
  building one means shipping transcript-parsing code into the dispatch
  action's environment, a real project, not a workflow edit.
- **Payload charters.** The template payload ships `assembler.yml` and
  `assembler.py` but no charter tree (`factory/agents/`,
  `factory/charters/` are factory-repo-only). A stamped product repo
  therefore has the dispatch *plumbing* but dispatch fails closed at the
  charter lookup even with every secret configured. Charters encode role
  judgment tuned to this repo; stamping them verbatim would hand a product
  repo instructions written for a different codebase.

## Decision

- **Two mechanical stops now, the hook later.** WO-0034 lands
  `timeout-minutes: 60` on the dispatch job and `--max-turns 100` on the
  agent step — ADR-0034's two flag-shaped stops, set generously: they are
  backstops against runaway runs, not budget enforcement, which stays the
  routing band's job (`budget_guard.py`). ADR-0034 names no numeric
  values, so these are operational settings, tunable without amending it.
- **The token-budget hook is deferred, not dropped.** ADR-0034's
  three-stop design stands. The hook joins when dispatch has real run
  history to size it against — a threshold tuned before any live runs
  would be a guess wearing a number.
- **Payload charters are deferred, not dropped.** The payload keeps
  shipping the dispatch workflow without charters, and `docs/setup.md`
  discloses the consequence in "Deliberately not in scope": stamped-repo
  dispatch needs charters authored for that repo. Authoring a charter
  template or a charter-authoring skill is future work with its own run.

## Consequences

- A dispatched run that loses its mind stops at 100 turns or 60 minutes,
  whichever comes first, and the `failure()` step flips the order to
  `wo:failed`. Until the hook lands, a run that burns tokens *quickly* is
  bounded by these two stops plus the routing band's per-order budget —
  three correlated-with-nothing ceilings, just not ADR-0034's exact three.
- A stamped repo's operator reading setup.md learns dispatch is
  deliberately inert there before wiring any secrets, instead of
  discovering it at the first `wo:ready-for-agent` label.
- "assembler.yml ships without charters" and "no budget hook exists" stop
  being review findings — a future review reads this ADR instead of
  re-deriving the gap (the same service ADR-0046, ADR-0053 and ADR-0054
  perform for their dead ends).
- Reopening either deferral is a new work order citing this ADR: the hook
  when run history exists to size it; payload charters when a product repo
  actually wants dispatch.
