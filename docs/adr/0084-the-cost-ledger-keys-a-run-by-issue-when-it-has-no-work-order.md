# The cost ledger keys a run by its issue when it has no work order

- Status: provisional
- Date: 2026-10-10

Amends ADR-0034's ledger `wo` field. The field set, the append-only rule,
the monthly circuit breaker and ADR-0041's gate rows all stand. Written
unattended by an autorun Architect stage (PRD-0013), so the status is
provisional until the Owner confirms it.

ADR-0034 fixed one spend ledger, `docs/factory/costs.jsonl`, with fields
`{wo, run_id, model, tokens, cost, outcome}` plus `at`.
`cost_ledger.line_problems` requires `wo` to be a `WO-####` token. Until
now every writer had one, because the assembler and `work-queue` only ever
run a work order.

The Conductor (PRD-0013) runs Workers that have no work order. A batch item
is a GitHub issue. Before its run reaches Decompose there is no breakdown
row, and so no work order. The spec stages, verify, review and ship are
real, metered runs with no `WO-####` to key them on. PRD-0013 requires a
metered row for every Worker run. Getting this wrong costs a lot, because
the ledger is append-only: a row shape that lands on `main` stays there.

Three shapes were weighed:

- **A second spend file** inside the batch's own ledger. Rejected: spend
  would have two homes, and `work_queue.month_to_date`, the input to
  ADR-0034's monthly breaker, would never see batch spend. A breaker that
  cannot see the largest spender does not protect the cap.
- **Key the run on a reserved work-order number** before its row exists.
  Rejected: detector G fails any ledger `wo` with no breakdown row. A
  reservation that never becomes a row, such as an item blocked at its PRD
  gate, would leave that failure on `main` for good.
- **Admit the issue as the key** for a run that has no work order. Chosen.

## Decision

The ledger's `wo` field holds either a `WO-####` token or an issue key
`#<n>`: the issue the run served, as digits with no leading zero. A writer
uses the work order whenever the run implements exactly one. It uses the
issue key only when no single work order exists. The field keeps its name,
so every existing row and reader stays valid as written.

`cost_ledger.line_problems` admits both shapes. Every rule keyed to work
orders stays work-order-only by construction, because
`cost_ledger.wo_token` already returns None for any other value. Detector
G's breakdown cross-checks and ADR-0080's dispatched set therefore ignore
issue-keyed rows. `cost_ledger.dispatched`, the breaker's row selection,
counts them, and that is the purpose of the change.

## Consequences

- The monthly breaker and the weekly report see Conductor spend, and
  neither changes.
- A field named `wo` now sometimes holds an issue. Readers that group by
  `wo` (`cost_report`'s per-order spend, the dashboard) will show
  issue-keyed groups beside work orders. They should label them as issues,
  not present them as orders.
- Issue-keyed rows are permanent. Once one is on `main`, narrowing the
  grammar back would make the ledger fail its own detector. Reversing this
  decision needs a superseding ADR and a reader that still admits the old
  rows.
- ADR-0034's cost per merged work order undercounts the work behind an
  order when part of that work ran before Decompose. For that reason the
  Conductor's scorecard reports cost per merged item.
