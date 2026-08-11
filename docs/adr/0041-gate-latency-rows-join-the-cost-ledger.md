# Gate-latency observations are cost-ledger rows

- Status: amended by ADR-0049
- Date: 2026-07-22

Amends ADR-0034. Its ledger decision reads "one ledger, derived
reports: every run appends `{wo, run_id, model, tokens, cost, outcome}`"
— and CONTEXT.md glossed the ledger as "one line per dispatched run".
PRD-0001's user story 4 wants "how long work waits on Matt" measured,
and the rollup ADR-0034 commissions lists gate latency among its derived
metrics — but nothing captured the raw waits to derive it from. The
three gates are human decision points (ADR-0033): their waits happen on
the mirrored issues' `wo:` lifecycle labels (ADR-0032), outside any
dispatched run, so no run could ever record them.

## Decision

**A confirmed gate passage is a ledger row.** When a work order's queue
label is removed and the gate's pass label applied
(`wo:draft`→`wo:prd-approved`, `wo:prd-approved`→`wo:blueprint-approved`,
`wo:needs-review`→`wo:merged`), the daily gate digest (WO-0017) appends
a row built by `cost_ledger.gate_entry`: the ADR-0034 field set
unchanged, `model: "none"`, zero tokens, zero cost, and the wait
recorded inside the deliberately open outcome vocabulary as
`gate_wait:<gate>:<seconds>s`. The passage timestamp keys `run_id`, so
a daily re-scan of the same label history dedups instead of
double-recording.

The ledger's meaning widens from "one line per dispatched run" to **one
line per spend event or gate passage** — capture, not rollup. The
derived-reports discipline stands: `cost_report.aggregate` keeps gate
rows out of its run counts and spend breakdown (they are $0 wait
observations, not runs), and any latency rollup derives from the rows
rather than being stored beside them.

## Consequences

- User story 4's "how long work waits on me" has a substrate: every
  gate wait survives as data, not as a number recomputable only while
  the label events stay fetchable.
- Detector G gates gate rows with the same grammar as run rows — the
  field set never forked. A gate row's WO must still have a breakdown
  row, and a merged order's ledger presence can now be satisfied by a
  gate row alone; G's per-run guarantees stay anchored to dispatched
  runs recording themselves (ADR-0034's handoff discipline), not to the
  ledger's mere non-emptiness.
- The digest tool, not the gates themselves, writes the rows: the two
  human approval flips are manual `gh` label edits with no script hook,
  so capture is observational (a daily timeline scan) rather than
  inline — which is why dedup is part of the grammar, not an
  afterthought.
