---
stage: architect
run: feature:size-band-calibration
date: 2026-10-20
ux: skipped — CLI text output only; no screens or flows.
assumptions:
  - "No live interview: every PRD open question was settled from autorun-brief.md, idea.md, prd.md, the code and read-only measurements on this clone (nothing committed but this artifact and ADR-0112), taking the recommended default each time. Nothing here is expensive to reverse: the tool writes no record, so no number outlives a rule change. ADR-0112 is provisional."
  - "Recommended default taken (where the size band is joined): at read time, from the ledger row's `wo` token to the working-tree breakdown row that names it (`knowledge_plane.parse_row`, field `size`). The ledger gets no new field. Detector G and `cost_ledger.line_problems` reject unknown fields (ADR-0034 fixes the field set), the ledger is append-only and never backfilled, and a band copied onto a row would drift from the breakdown row that owns it. Measured 2026-10-20: 164 distinct WO tokens sit in breakdown rows, none under two different sizes, and both metered work orders (WO-0074, WO-0076, run first-live-dispatch) join to S. This restates PRD success criterion 1: the calibration row, not the written ledger row, carries the band, and the join is the tested seam. Surfaced to the caller as a wording change; the metering volume problem is not a seam problem, because Conductor build runs already record spend under the row's own WO token."
  - "Recommended default taken (ledger walk, PRD open question 1): no sharing with `conductor_calibrate`. It walks closed batch ledgers (`conductor_close.closed_batches`) and joins them to costs.jsonl to get the Conductor plan item's size, which is the issue's size label, not Decompose's breakdown-row band. This tool needs only the cost rows, which `cost_ledger.read` and `cost_ledger.dispatched` already own and which hold every closed batch's spend. Importing `conductor_calibrate` would pull in `conductor`, `conductor_close` and `conductor_flow` for a quantity this tool does not read. Accepted gap: a batch not yet closed has not landed its spend in costs.jsonl, so it is invisible here. `python3 one_owner.py` is the check at Implement."
  - "Recommended default taken (sample unit): one work order, the sum of the cost of every dispatched ledger row whose `wo` is that token, over every attempt and step. It is the unit `conductor_calibrate._budgets` already uses for an item (whole spend) and the unit the band's dollar budget caps (ADR-0034). Measured: WO-0074 has 6 rows summing $5.435, WO-0076 has 1 row of $0.474, so n is 2 for band S, not 7. Treating each row as a sample would put n at 7 and clear the minimum on 2 work orders."
  - "Recommended default taken (the estimate in BRE): the band's dollar budget from `factory_config.resolve_budget` (factory.json `budgets_usd`; S 5, M 15, L 40 in `factory/templates/factory.json`, which `factory_config.load` falls back to in this repo). It is the number a work order of that size was priced and capped at, so it is the estimate the size band implies. It is not a calibration number: the tool reads it as the thing under test and never writes it. The alternative, the band's own median, measures spread around itself and cannot show an overrun or underrun."
  - "Recommended default taken (BRE): Miyazaki's Balanced Relative Error, signed: (actual - estimate) / min(actual, estimate). A work order at twice its budget reads +1 and one at half reads -1, so over- and underruns weigh the same, unlike plain relative error (the second is bounded at -1, the first is not). Positive is an overrun. Measured on the two metered work orders against S = $5: WO-0074 +0.087, WO-0076 -9.554. Zero actual cost cannot occur, because zero-cost rows are excluded first."
  - "Recommended default taken (interval): the 10th, 50th and 90th percentiles of a band's BRE values by nearest rank (rank = ceil(p * n / 100) of the sorted values, 1-based; no interpolation), printed as P10, P50 and P90 and called an 80% interval of past error. At n = 5, P10 is the minimum and P90 is the maximum, so the interval is the observed range; the output says so rather than dressing it as more. Sorting and `math.ceil` only, stdlib."
  - "Recommended default taken (minimum n): the floor comes from `factory_config.resolve_calibrate_floor` (factory.json `conductor.calibrate_floor`, default `DEFAULT_CALIBRATE_FLOOR` = 5), the same floor `conductor.py calibrate` refuses below (#940). One owner for the number, and the brief's 5 is the default. An Owner who sets a lower floor in factory.json has chosen it; this repo sets none."
  - "Recommended default taken (miss): a work order whose actual cost exceeds its band's budget (BRE > 0) is an overrun. The band line prints `over budget <k> of <n>`, with the cost next to it. A refused band prints its n and cost but no interval and no miss count, so a thin sample never reads as a rate."
  - "Recommended default taken (re-plan beside each band): `decompose_signals.measure` supplies one RunRecord per run, keyed by breakdown path. A band's re-plan figure pools the measurable runs that hold at least one of the band's metered work orders (sum of `count` over sum of `items_at_d`) and names the number of unmeasurable ones; no measurable run prints `re-plan unmeasurable`, never 0. The figure is a run's, not a work order's: Decompose re-plans runs. Measured 2026-10-20: 36 runs, combined 12/250 over 29 runs, unmeasurable 7."
  - "Recommended default taken (record): none. The PRD asks for a report, not a snapshot, and nothing downstream reads a file yet; #988 can read stdout or add `--record` through `eval_schema.write_snapshot` when it has a reader. YAGNI."
  - "Recommended default taken (root-only, PRD open question 5): root-only. `grep` for importers of `decompose_signals` finds `factory.py` (a lazy VERBS row) and nothing in `factory_init.MIRRORS`; no payload tool needs a Decompose calibration, and a stamped repo has no learning loop. It adds four root-only to mirrored pairs (`cli`, `knowledge_plane`, `cost_ledger`, `factory_config`), recorded in ADR-0112 with the pin in `tests/test_dual_membership.py`. Whether that ADR clears the hard-to-reverse leg is doubtful; written anyway on the ADR-0110 precedent because the pin test says a change to the set 'has to be recorded'. Provisional."
---

# Architecture: Calibrate S/M/L size bands from past error

## Approach

One root-only, stdlib module, `size_band_calibration.py`, with a pure core
and no adapter of its own. The cost side comes from the seam that already
owns it: `cost_ledger.read` returns validated rows (its problems stop the
run, fail closed) and `cost_ledger.dispatched` drops gate-latency rows.
The band side comes from the seam that owns the breakdown row grammar:
`knowledge_plane.breakdown_files` and `parse_row` give each work order's
`size:`. The join is read-time, on the ledger row's `wo` token. Rows are
sorted into used or excluded, each exclusion with a counted reason.
Used rows sum to one cost per work order. Per band, the work orders'
Balanced Relative Error against the band's budget
(`factory_config.resolve_budget`) is sorted, and nearest-rank P10, P50 and
P90 form the interval, printed only when the band's n meets the floor
(`factory_config.resolve_calibrate_floor`). Beside each band the tool
prints misses, cost, and the re-plan rate pooled from the runs holding the
band's work orders, taken from `decompose_signals.measure`.

The other shape compared was a ledger walk shared with
`conductor_calibrate`, reading closed batch ledgers for the plan item's
size. It loses because that size is the issue label, a different band from
the one Decompose assigns, and because costs.jsonl already holds every
closed batch's spend, so the batch ledgers add nothing this tool reads.

| PRD success criterion | Where |
|---|---|
| Calibration row carries a band; the join is tested | Band join |
| Below-minimum refusal vs no-row string, exact | Interval, Report |
| Unmetered and zero-cost rows excluded, counted, never estimated | Row selection |
| Misses beside cost and re-plan rate; unmeasurable named, never 0 | Report, Re-plan source |
| Every figure computed from rows | Interval, fixture-ledger tests |
| Stdlib, no network | Stack |
| Five repo checks pass | ADR-0112, `factory.py` VERBS row, dual-membership pin |

## Components

### Row selection (`select`)

- Responsibility: from `cost_ledger.read` entries, partition into used
  rows and counted exclusions, in this order, each row counted once:
  gate-latency rows (`cost_ledger.gate_wait`; waits, not spend),
  owner-session markers (`cost_ledger.owner_session`; unmetered, never
  estimated), dispatched rows with cost 0 (no cost recorded), dispatched
  rows whose `wo` names no sized breakdown row (an issue key `#n`, an
  unknown token, or a row with no `size:`). Used rows are the rest.
  The gate and owner predicates are `cost_ledger`'s own; `dispatched`
  is the complement of those two and is not re-implemented.
- Collaborators: `cost_ledger`. Pure over entries and a `wo -> band` map.

### Band join (`bands`)

- Responsibility: the `wo -> size` map, from every breakdown row that
  names a work order and a size. A token under two different sizes is
  excluded from the map and counted as `ambiguous size`. Today none is.
  Missing `size:` is not defaulted.
- Collaborators: `knowledge_plane.breakdown_files`, `parse_row`. Also
  keeps `wo -> breakdown path`, the key the re-plan source joins on.

### Work orders and BRE (`work_orders`, `bre`)

- Responsibility: sum used rows' cost per `wo` (one work order, all
  attempts); BRE = (actual - estimate) / min(actual, estimate) with the
  estimate the band's budget. Both actual and estimate are positive by
  construction (zero cost is excluded; `resolve_budget` refuses a
  non-positive budget).
- Collaborators: `factory_config.resolve_budget`.

### Interval (`interval`)

- Responsibility: for one band's BRE values, `None` below the floor, else
  nearest-rank P10, P50, P90 (rank = ceil(p * n / 100) of the sorted list,
  1-based). It returns the three values and n; it never invents one.
- Collaborators: `math` only. Pure.

### Re-plan source (`replan_by_band`)

- Responsibility: from `decompose_signals.measure` records (keyed by
  `path`), pool re-plan per band as above. A failed measurement is one
  problem string and every band prints `re-plan unmeasurable — <reason>`.
- Collaborators: `decompose_signals.measure`, injected as `measure` so
  tests pass a fixed result and the live call needs git only through
  `cli.runner`.

### Report and front door (`render`, `main`)

- Responsibility: load config and ledger, run the components, print
  through `cli.report`, and own the exit code. A `factory.py` `VERBS` row
  `size-band-calibration` is required by `tests/test_factory_cli.py`.
- Collaborators: everything above, `cli`.

## Data model

Access pattern: one invocation reads the whole ledger and prints once;
nothing is stored.

```
Used row    {wo, run_id, cost}                 # a ledger entry
Exclusions  {gate, owner_session, zero_cost, unjoined, ambiguous: int}
WorkOrder   {wo, band, path, cost}             # one per wo, summed
BandResult  {band, n, budget, bre: [float],    # bre sorted
             interval: {p10, p50, p90} | None,
             over, cost_total, cost_mean,
             replan: {count, items, runs, unmeasurable} | {unmeasurable}}
```

Invariants and owners: the ledger row shape belongs to `cost_ledger`; the
size belongs to the breakdown row; the budget and floor belong to
`factory_config`. The tool owns only the sort, the BRE formula and the
percentile rank. n counts work orders, never rows.

## Interfaces & contracts

### `python3 size_band_calibration.py` (also `python3 factory.py size-band-calibration`)

- Input: `docs/factory/costs.jsonl` and `docs/factory/costs/runs/`, the
  working-tree breakdowns, `factory.json`, and git history (read-only,
  through `decompose_signals`). No arguments; no network.
- Output, stdout, in this order. Implement pins the exact strings:
  - one line per nonzero exclusion:
    `size-band-calibration: excluded <n> owner-session:unmetered row(s) — cost never recorded, none estimated`,
    `… <n> gate-latency row(s) — waits, not spend`,
    `… <n> row(s) with cost 0 — no cost recorded`,
    `… <n> row(s) whose wo names no sized breakdown row`,
    `… <n> row(s) whose wo has conflicting sizes`
  - one line per band S, M, L:
    - `size-band-calibration: band S — BRE P10 <x>, P50 <x>, P90 <x> over <n> work order(s) against a $<budget> budget (nearest rank; at n = 5 P10 and P90 are the observed range); over budget <k> of <n>; cost $<mean> mean, $<total> total; re-plan <c>/<i> over <r> run(s) (<u> unmeasurable)`
    - `size-band-calibration: band S — refused: n <n> work order(s) is below the minimum of <floor>, no interval printed; cost $<total> total; re-plan …`
    - `size-band-calibration: band M — no metered work order joins this band; re-plan unmeasurable`
  - the `cli.report` summary,
    `size-band-calibration: <N> work order(s), <P> problem(s)`, prefix
    computed.
  - Re-plan reads `re-plan unmeasurable — <reason>` when no contributing
    run is measurable, never `0/0`.
- Exit: 0 with no problems, refusals and empty bands included (they are
  data). 1 with problems. 2 on any argument, usage printed.
- Failure modes:
  - ledger lines `cost_ledger.read` rejects: its `ledger:` problems print,
    no band lines print (a partial ledger would undercount silently).
  - factory.json missing or without `budgets_usd` or with a bad floor:
    the `config:` problem prints, no band lines.
  - an unreadable breakdown: `cli.read_file`'s problem, labelled; the
    work orders it held fall into the unjoined exclusion.
  - `decompose_signals.measure` failing (git absent, timeout): its
    problems print, re-plan is unmeasurable, the rest of the report
    stands.

## Stack & dependencies

- Python 3 stdlib only (`math`, `collections`, `pathlib`).
- Reads through `cost_ledger`, `knowledge_plane`, `factory_config`,
  `cli`, and `decompose_signals` (root-only, crosses no mirror).
- Root-only: no `factory_init.MIRRORS` entry, no manifest regen. Four new
  root-only to mirrored pairs and one pin edit (ADR-0112).
- Docs touched: a CLAUDE.md "on demand, free" bullet beside
  `decompose_signals.py`, and a CONTEXT.md entry, **Size-band error
  interval**. No Makefile or CI line: a measurement, not a gate.
- Tests: through the public interface with fixture ledgers and breakdown
  text in a temp dir and an injected `measure`: n = 4, n = 5, a band with
  no rows, an all-unmetered ledger, a mixed ledger, an ambiguous size, and
  a fixed-number BRE and percentile case worked by hand in the test.

## Decisions & alternatives

- **Read-time join on `wo`** over a `size` field on the ledger row: the
  field set is fixed by ADR-0034 and checked by detector G, the ledger is
  never backfilled, and a copied band drifts from the breakdown row that
  owns it.
- **One work order is one sample** over one ledger row: WO-0074's 6 rows
  would make n = 7 from 2 work orders.
- **Budget as the estimate** over the band's own median: a median shows
  spread, not misses.
- **Signed BRE (divide by min)** over plain relative error: plain error
  is bounded below at -1 and unbounded above, so overruns would dominate
  any percentile.
- **Nearest-rank P10/P50/P90** over `statistics.quantiles`: interpolation
  invents values between samples at n = 5, and the exclusive method
  extrapolates past the observed range. Nearest rank always returns a
  measured value.
- **Floor from `factory_config`** over a new constant: `conductor.py
  calibrate` already refuses below that floor; two owners of 5 would
  diverge.
- **No share with `conductor_calibrate`** over importing its ledger walk:
  different size, different input, heavier import (see Approach).
- **No `--record`** over a snapshot like `decompose_signals --record`:
  no reader yet.
- **Pooled per-run re-plan beside each band** over one global re-plan
  line: the PRD asks for it beside each band, and the pooling names its
  unit (runs) rather than pretending it is per work order.

## ADRs

- ADR-0112 (provisional): size_band_calibration joins the root-only
  importers of cli.py, knowledge_plane.py, cost_ledger.py and
  factory_config.py. None of the other decisions passed the
  hard-to-reverse leg: the tool writes no record, so any of them can
  change in one commit.
