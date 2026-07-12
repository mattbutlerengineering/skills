# Work-order budgets and model routing

- Status: provisional
- Date: 2026-07-11

Unattended agents burn tokens with nobody watching; 8090 itself reported
its AI spend tripling. A single runaway loop can spend a month's budget
overnight, and post-hoc monitoring alone discovers that the morning
after. The ai-tooling agent-bounding guidance calls for explicit stop
rules per task.

## Decision

**Every work order carries a budget by size class**, anchored in dollars
(token equivalents derived per model):

| Class | Budget (start) | Shape |
|-------|----------------|-------|
| S | ≈ $5 | one file cluster, obvious test |
| M | ≈ $15 | one feature slice, 2–5 files |
| L | ≈ $40 | cross-cutting slice; anything larger must be split at decompose |

The table is a starting point, tuned from ledger actuals — the planner
role owns the estimation loop (budget vs actual per merged order).

**Three uncorrelated stops** bound every dispatched run: the token budget
(a hook reads cumulative usage from the session transcript; 80% triggers
a wrap-up warning, 100% blocks further tool use), a max-turns cap, and
the job's wall-clock timeout. Exhaustion is a *handoff, not a failure
mode*: the run commits and pushes WIP, writes a structured handoff
(done/undone acceptance criteria, last state, resume instructions,
spend), and labels the order `budget-exhausted needs-human wo:failed`.
The dispatcher refuses a `budget-exhausted` order until the owner clears
the label — no self-retry loops.

**Model routing by work type**: cheap models for mechanical work (chores,
sweeps, label plumbing), the standard model for implementation, the top
model for architecture and review. The routing table lives in the
per-repo factory config next to the budget table.

**One ledger, derived reports**: every run appends
`{wo, run_id, model, tokens, cost, outcome}` to `docs/factory/costs.jsonl`
(append-only, same discipline as eval results). A weekly job derives the
rollup — cost per merged order by class, acceptance rate, churn, escapes,
MTTR, gate latency — and a monthly circuit breaker pauses dispatch
repo-wide when spend crosses the cap. A merged order with no ledger line
is a gating detector finding.

## Consequences

- A bad unattended run costs a bounded, known amount; the failure surface
  is "a handoff comment to read", not "a bill to dispute".
- Budgets create honest pressure on decompose: work that can't fit L must
  be split, which is the tracer-bullet discipline the pipeline wants
  anyway.
- The ledger is the factory's measurement substrate — without it,
  autonomy graduation (ADR-0033) has no data to graduate on.
