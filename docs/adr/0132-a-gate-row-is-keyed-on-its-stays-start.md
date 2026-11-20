# A gate row is keyed on its stay's start

- Status: accepted
- Date: 2026-11-20

Amends ADR-0041. Its dedup rule reads "the passage timestamp keys
`run_id`, so a daily re-scan of the same label history dedups instead
of double-recording".

## Context

The passage timestamp is not a label event. It is the end of a stay as
`human_gates.completed_stays` computes it, and ADR-0074 changed that
computation: a confirmed stay now ends at its first pass label when that
came before the queue label's removal. The next daily digest run
recomputed four ends, built rows with new run_ids, and found none of
them recorded. `docs/factory/costs.jsonl` now holds each of these
passages twice, once per walk: WO 0074's prd (1399s, then 1380s),
blueprint (19s, then 4s) and merge (558s, then 557s) stays, and WO
0034's merge stay (48s, then 47s). Every reader that counts gate rows
counts them twice, among them the dashboard's median gate wait. Any
later amendment to the walk would do the same again.

The ledger is append-only, so the duplicates stay in it.

## Decision

**A gate row is keyed on the stay's start**, the time the queue label
was added. That is a label event, and no amendment to the walk can move
it. `human_gates.gate_passages` returns `(gate, waited, passed at,
started at)`, and `cost_ledger.gate_entry` writes the run_id
`gate-<gate>-entered-<start>`. The row's `at` and its outcome's wait are
unchanged: `at` is still the passage date and the wait still runs to the
walk's end.

**A stay is `(wo, gate, start)`, read from either key.**
`cost_ledger.gate_stay` reads the start from a start-keyed run_id. For a
legacy end-keyed run_id it takes the end minus the row's wait. GitHub
timestamps are whole seconds and the wait is the whole-second difference
between them, so that is the start exactly, whichever walk computed the
end. The four legacy pairs each name one stay under this rule.

**The writer bridges the change.** `cost_ledger.record_new` skips a gate
row whose stay is already recorded, under either key. The switch itself
re-records nothing, and neither does any later change to the walk.

**Readers collapse the duplicates.** `cost_ledger.gate_rows` returns one
gate row per stay and keeps the last one recorded. That is the latest
walk's measurement, which for the four pairs is ADR-0074's corrected
wait. A row whose run_id holds no readable timestamp names no stay and
is kept as it is. The dashboard's median gate wait reads through it.

**Admitted timestamps are UTC Z form.** `human_gates` admission
respells every timestamp as `YYYY-MM-DDTHH:MM:SSZ`, because a row's
`at` is a timestamp's first ten characters and its run_id embeds one.
An offset spelling dated a row by its local day. A basic-format
spelling gave an `at` that `line_problems` refuses, which made
`record_new` refuse the digest's whole batch on every later run.

## Consequences

- `row_key` stays ADR-0049's `(wo, run_id)` identity. `gate_stay` is a
  second identity for gate rows only, used by the batch writer and the
  gate-row readers.
- `docs/factory/costs.jsonl` is not rewritten. Its 32 gate rows read as
  28 stays.
- `size_band_calibration`'s exclusion counts still count gate rows, not
  stays. Its counts cover every ledger row exactly once. They report
  rows excluded from a cost sample and measure no wait.
- Detector G still uses `gate_wait` as a predicate only. It counts
  nothing, so duplicates do not affect it.
