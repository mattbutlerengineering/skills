---
stage: decompose
run: feature:size-band-calibration
date: 2026-10-20
assumptions:
  - "No live review of the cut: autorun-brief.md holds Owner decisions 1-4 and says nothing about milestones or sizing. Milestone boundaries and sizes are the skill's own defaults (each milestone independently demonstrable, one item per sitting, vertical slices where the architecture allows). Milestone 1 is the join and row selection, because every figure rests on which rows are used and it can be shown on fixture rows alone. Milestone 2 is the Balanced Relative Error and interval math. Milestone 3 is the re-plan source and the one command the PRD asks for. Milestone 4 is the docs and the whole-repo verify."
  - "Test-first ordering follows the repo's TDD rule: each implementation item is blocked by a tests item whose Accept says its cases run and fail against the tree before the implementation lands."
  - "No work-order ids and no tracker markers: the brief says issue 987 seeds the run, ADR-0032 mirroring is not used, and detectors C and I scan every markdown file. Items carry short labels (S1, S2, ...) at the start of the bold span, the form decompose-outcome-signals used. Fixtures that need a work-order token build it in the test file, not here."
  - "Owner decision 4 is binding: the band is joined at read time from a ledger row's work-order token to the breakdown row's size, and no item adds a ledger field or touches cost_ledger's field set. The PRD's first success criterion is covered by S1 and S2 as that decision rewords it."
  - "Dual-membership pin placement, derived from ADR-0112: the pin moves in the item that first adds each import. S2 adds knowledge_plane and cost_ledger, S4 adds factory_config, S8 adds cli, so the set grows by one pair per item and reaches 50 pairs at S8. decompose_signals is root-only and crosses nothing, so S6 edits no pin. S10 asserts the final count."
  - "Derived, not stated: the tool is built as one module, size_band_calibration.py, in the order selection, math, report, because architecture.md lists its components as pure functions with the front door last. All tests go in tests/test_size_band_calibration.py unless an item says otherwise, with fixture ledgers and breakdown text in a temp dir and an injected measure, as architecture.md's Stack section says."
  - "No design gap found, so nothing is routed to Architect. Architecture.md's exclusion order, sample unit, BRE formula, rank rule, floor owner and output strings are specific enough to write acceptance lines from."
---

# Breakdown: Calibrate S/M/L size bands from past error

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. Every implementation item is blocked by the
tests item that pins it. All tests go in `tests/test_size_band_calibration.py`
unless an item says otherwise, and they run through the public interface
with fixture ledgers (architecture.md, Stack).

## Milestone 1: ledger rows are selected and joined to a size band

When this milestone is done, `size_band_calibration.bands`, `select` and
`work_orders` turn a ledger and breakdown text into one cost per sized work
order plus counted exclusions, with no cost estimated for any excluded row.

- [x] **S1 Join and selection tests** — cases for `bands`, `select` and `work_orders` over fixture breakdown text and fixture ledger entries — size:M
  - Accept: the module holds these cases, each asserting exact values. Join: a ledger row's work-order token joins to the `size:` of the breakdown row that names it, and the ledger entry gains no field. A token under two different sizes is left out of the map and counted as `ambiguous`; a row with no `size:` is not defaulted. Selection order, each row counted once: gate-latency rows, then owner-session rows, then dispatched rows with cost 0, then dispatched rows whose token names no sized breakdown row (an issue key, an unknown token, a row with no `size:`); the rest are used. A ledger of only unmetered owner-session rows gives no used rows and an owner-session count equal to its length. Sample unit: six used rows for one token and one for another give two work orders, with the first costing the sum of its six; n counts work orders, never rows. Each excluded row yields no cost. Before the module exists the test module fails on import.
  - Blocked by: —
- [x] **S2 Band join, row selection and work orders** — root-level `size_band_calibration.py` with `bands`, `select` and `work_orders` as architecture.md's Band join and Row selection describe — size:M
  - Accept: the S1 tests pass. The ledger is read through `cost_ledger.read`, with `cost_ledger.dispatched`, `gate_wait` and `owner_session` as the predicates and none re-implemented. Breakdowns come from `knowledge_plane.breakdown_files` and `parse_row`, with no retyped row regex. The module imports only the standard library, `cost_ledger` and `knowledge_plane`, and is not in `factory_init.MIRRORS`. `tests/test_dual_membership.py`'s pin gains `(size_band_calibration, knowledge_plane)` and `(size_band_calibration, cost_ledger)`, its pair-count comment is updated, and the test passes.
  - Blocked by: S1 Join and selection tests

## Milestone 2: a band's past error is an interval or a refusal

When this milestone is done, `bre` and `interval` turn one band's work
orders into nearest-rank P10, P50 and P90 of Balanced Relative Error, or
`None` below the floor, and never invent a value.

- [x] **S3 Error and interval tests** — hand-worked cases for `bre` and `interval`, plus the budget and floor sources — size:M
  - Accept: the module holds these cases, each asserting exact numbers worked by hand in the test. `bre` is (actual - estimate) / min(actual, estimate) with the estimate the band's budget: a cost of twice the budget gives +1 and half the budget gives -1. The budget is read through `factory_config.resolve_budget` from a fixture config, not a retyped table. `interval` on four values returns `None`; on five returns P10 as the minimum and P90 as the maximum; on a longer list the ranks are ceil(p * n / 100) of the sorted values, 1-based, with no interpolation, so every returned value is a member of the input. A custom floor from `factory_config.resolve_calibrate_floor` moves the refusal point. An unsorted input and a sorted one give the same interval. A band's over-budget count is the number of work orders with BRE above 0. Before the functions exist the cases fail.
  - Blocked by: S2 Band join, row selection and work orders
- [x] **S4 Balanced Relative Error and nearest-rank interval** — `bre`, `interval` and the over-budget count as architecture.md's Work orders and BRE and Interval describe — size:S
  - Accept: the S3 tests pass, and every earlier test still passes. Sorting and `math.ceil` only; no `statistics` call. The floor and budget come from `factory_config`, and the module defines no constant 5 and no budget table. `tests/test_dual_membership.py`'s pin gains `(size_band_calibration, factory_config)` and the test passes.
  - Blocked by: S3 Error and interval tests

## Milestone 3: one command prints every band, its refusal and its re-plan rate

When this milestone is done, `python3 size_band_calibration.py` and
`python3 factory.py size-band-calibration` print one line per nonzero
exclusion, one line per band S, M and L, and the `cli.report` summary.

- [ ] **S5 Re-plan source tests** — cases for `replan_by_band` with an injected `measure` — size:S
  - Accept: the module holds these cases, each asserting exact values. A band pools the measurable runs that hold at least one of its work orders: the sum of `count` over the sum of `items_at_d`, with the number of runs and the number of unmeasurable ones. A band whose contributing runs are all unmeasurable gives `re-plan unmeasurable` with the reason, never `0/0` and never zero. A band with no contributing run is unmeasurable. A failed measurement gives one problem string and every band unmeasurable with that reason. A work order joins to its run by the breakdown path that `bands` kept.
  - Blocked by: S4 Balanced Relative Error and nearest-rank interval
- [ ] **S6 Re-plan source** — `replan_by_band` over `decompose_signals.measure` records as architecture.md's Re-plan source describes — size:S
  - Accept: the S5 tests pass, and every earlier test still passes. `measure` is a parameter, so tests pass a fixed result and the live call reaches git only through `cli.runner` inside `decompose_signals`. The module imports `decompose_signals` and no other new module; it is root-only, so the dual-membership pin is unchanged and still passes.
  - Blocked by: S5 Re-plan source tests
- [ ] **S7 Report tests** — end-to-end cases that drive `main([])` against fixture ledgers, breakdowns and an injected `measure` and assert the exact stdout lines and exit code — size:M
  - Accept: the module holds these cases, each asserting exact strings: a band at n = 4 prints the refusal naming the band, its n, the floor and that no interval is printed, with cost and re-plan beside it and no miss count; the same band at n = 5 prints P10, P50 and P90, the note that at n = 5 they are the observed range, `over budget <k> of <n>`, mean and total cost and the re-plan figure; a band with no joined rows prints the `no metered work order joins this band` line, different from the refusal; a ledger of only unmetered rows prints the owner-session exclusion line and three no-rows band lines; a mixed ledger prints each nonzero exclusion line in the architecture's order and omits zero ones; an ambiguous size prints the conflicting-sizes line. Every printed figure is recomputed in the test from the fixture rows, none copied from the tool. The summary reads `size-band-calibration: <N> work order(s), <P> problem(s)`. Exit codes: 0 with refusals and empty bands, 1 when `cost_ledger.read` rejects a line (its `ledger:` problems print and no band line does), 1 on a bad factory.json (a `config:` problem and no band line), 2 with usage on any argument. A check that the module source imports no network module and that a recording fake runner shows no git verb outside `decompose_signals`' read-only set. Before `render` and `main` exist the cases fail.
  - Blocked by: S6 Re-plan source
- [ ] **S8 Report and front door** — `render` and `main` as architecture.md's Report and front door describes, plus the `factory.py` verb — size:M
  - Accept: the S7 tests pass, and every earlier test still passes. Output goes through `cli.report`, so the summary prefix is computed. Config and ledger problems stop the band lines. An unreadable breakdown is read through `cli.read_file` and its work orders fall into the unjoined exclusion. `factory.VERBS` gains `"size-band-calibration": ("size_band_calibration", "argv")` and `tests/test_factory_cli.py` passes. The module docstring's first line states what it does. `tests/test_dual_membership.py`'s pin gains `(size_band_calibration, cli)`, so the set is 50 pairs as ADR-0112 records, and the test passes.
  - Blocked by: S7 Report tests

## Milestone 4: the docs name the tool and the repo checks pass

When this milestone is done, CLAUDE.md and CONTEXT.md name the tool and its
vocabulary, and every CI check is green over the finished change.

- [ ] **S9 Docs** — the CLAUDE.md "on demand, free" bullet beside `decompose_signals.py` and a CONTEXT.md entry for **Size-band error interval** — size:S
  - Accept: CLAUDE.md names `python3 size_band_calibration.py` as free, outside every gate and making no network call, and says it refuses a band below the floor. CONTEXT.md defines **Size-band error interval** as a band's nearest-rank P10, P50 and P90 of Balanced Relative Error against the band's budget, printed only at or above the floor. Neither doc contains a work-order token or sample id that detectors C and I would scan.
  - Blocked by: S8 Report and front door
- [ ] **S10 Whole-repo verify** — the four CI checks and the one-owner pre-pass over the finished change — size:S
  - Accept: `python3 run_tests.py` exits 0; `python3 lint.py` prints `lint: 0 problem(s)`; `python3 kb.py drift` prints `drift: 0 problem(s)`; `python3 gates.py` and `python3 gates.py --selftest` print `gates: 0 problem(s)`. `python3 one_owner.py` reports no `one-owner:` problem naming `size_band_calibration.py`. `tests/test_dual_membership.py` passes with 50 pairs over nine mirrored modules. No file under `skills/` or `factory/templates/`, and not `.claude-plugin/plugin.json`, `factory_init.MIRRORS`, `docs/factory/costs.jsonl` or `cost_ledger.py`, is changed. `python3 size_band_calibration.py` on this clone exits 0 and prints either an interval or a refusal for each of S, M and L.
  - Blocked by: S9 Docs

## Design gaps found

none.

## Notes

