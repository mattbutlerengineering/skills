# Autonomy baseline — accepted orders per gate-wait hour

The baseline half of `wo-25y.5` (issue #434): ADR-0069 settled the formula
and deferred the number until the factory had dispatched and merged real
work orders. It now has two, so the number is computed here from
`docs/factory/costs.jsonl` as of 2026-10-10, with the accessors ADR-0069
names (`cost_ledger.dispatched`, `cost_ledger.gate_wait`).

## Inputs

| Input | Value |
|---|---|
| Gate-wait rows | 32 — merge 26, prd 3, blueprint 3 (all three gates now record waits) |
| Gate-wait hours | 2,775.9 |
| Dispatched rows | 126 — 119 `owner-session:unmetered`, 7 `completed` |
| Assembler-dispatched work orders | 2 — WO-0074 (6 runs), WO-0076 (1 run), $5.91 metered |
| Their mirror issues | #536 and #574, both labelled `wo:merged` |

## The number

| Reading | Accepted | Metric |
|---|---|---|
| ADR-0069 as written (`outcome == "merged"`) | 0 | 0.0 per gate-wait hour |
| Joined with the mirror issues' `wo:merged` label | 2 | 0.00072 per gate-wait hour (one accepted order per ~1,388 gate-wait hours) |

Reported alongside, per ADR-0069: raw acceptance is 2 of 2 dispatched
work orders (7 runs). Escapes stay undefined (no field exists).

## Finding: the formula's filter can never match

The assembler writes the ledger row when the agent job ends
(`.github/workflows/assembler.yml`: `OUTCOME=... 'completed' || 'agent-failed'`),
before any merge, and nothing writes a `merged` outcome later. So
ADR-0069's `outcome == "merged"` filter selects nothing by construction,
and the literal metric stays 0 however much merged work the factory does.
The label-joined reading above
is the honest number. ADR-0080 settles the remedy: accepted means an
assembler-dispatched work order whose mirror issue reached `wo:merged`,
so the label-joined reading is the baseline of record.

## Caveats

- The denominator sums every recorded gate wait, including waits on
  owner-session work that the assembler never dispatched; the numerator
  counts only assembler dispatches. ADR-0069 defines it that way. With two
  accepted orders the baseline is a floor to argue against, not a rate.
- Gate waits are wall-clock time between label events, not attention time.
