---
stage: verify
run: feature:size-band-calibration
date: 2026-10-20
assumptions:
  - "No live interview: the autorun brief holds no Verify-specific answers, so the skill's defaults were taken. The criteria list is prd.md's nine success criteria plus the breakdown acceptance criteria no PRD criterion covers (last section)."
  - "Every piece of evidence was run on HEAD 15c1b65 in this session; nothing is carried over from the Implement stage's report."
  - "Recommended default taken (flake re-check): four full-suite runs, three at the default 8 workers and one at -j 16."
  - "Recommended default taken (protected paths): compared with the three-dot form origin/main...HEAD, so main's own moves do not count as this branch's changes."
---

# Verification: Calibrate S/M/L size bands from past error

## Summary

9 of 9 PRD success criteria PASS, 0 FAIL, 0 NOT RUN, on HEAD 15c1b65. The
breakdown acceptance criteria no PRD criterion covers also pass. Four
full-suite runs were green (3470 tests, 108 modules). Three mutations of
load-bearing behaviour each applied (diff shown) and each made tests fail.
One caveat the verdict does not hide: on this clone's real ledger the tool
refuses every band (S has n 2, M and L have no joined row), so the interval
arithmetic is proven by fixture tests and by hand calculation of the S
totals, never by a live interval. See Not verified.

## Criteria & evidence

### 1. A ledger row joins by work-order token to a breakdown row's `size:` at read time; a test asserts the join; the ledger gains no field

- Check: ran the join tests and recomputed the join by hand. WO-0074 and WO-0076 are both `size:S` rows in docs/features/first-live-dispatch/breakdown.md; the tool reports band S with n 2.
- Evidence:
  ```
  $ python3 -m unittest tests.test_size_band_calibration (tests named)
  test_a_token_joins_to_the_size_of_the_row_that_names_it ... ok
  test_the_join_adds_no_field_to_a_ledger_entry ... ok
  test_a_token_under_two_sizes_is_left_out_and_ambiguous ... ok
  test_a_row_with_no_size_is_not_defaulted ... ok
  Ran 48 tests in 0.024s  OK
  $ grep WO-0074/WO-0076 docs/features/*/breakdown.md
  first-live-dispatch/breakdown.md:40:- [x] **WO-0074** ... — size:S
  first-live-dispatch/breakdown.md:65:- [x] **WO-0076** ... — size:S
  ```
- Result: PASS

### 2. Band with n below 5 prints a refusal (band, n, minimum, reason), no interval; exact string at n = 4 and the interval at n = 5

- Check: ran the live tool and the two report tests that assert the exact strings (tests/test_size_band_calibration.py lines 412 and 431).
- Evidence:
  ```
  $ python3 size_band_calibration.py
  size-band-calibration: band S — refused: n 2 work order(s) is below the minimum of 5, no interval printed; cost $5.908 total; re-plan 4/8 over 1 run(s) (0 unmeasurable)
  test_a_band_at_four_is_refused_with_cost_and_replan_only ... ok   (asserts "refused: n 4 work order(s) is below the minimum of 5 ...")
  test_the_same_band_at_five_prints_the_interval ... ok              (asserts "BRE P10 ..., P50 ..., P90 ... over 5 ...")
  ```
- Result: PASS

### 3. A band with no joined rows prints a string different from the refusal; a test asserts both

- Evidence:
  ```
  size-band-calibration: band M — no metered work order joins this band; re-plan unmeasurable
  size-band-calibration: band L — no metered work order joins this band; re-plan unmeasurable
  test_an_empty_band_has_no_rows_and_no_interval ... ok
  test_the_replan_figure_never_reads_zero_over_zero ... ok
  test_a_band_at_four_is_refused_with_cost_and_replan_only ... ok
  ```
- Check: the refusal line (criterion 2) and these lines differ in text; the report tests assert both exact strings.
- Result: PASS

### 4. Unmetered owner sessions and rows with no cost are excluded; the count and reason print for each kind; no cost estimated

- Check: live exclusion lines against an independent count over costs.jsonl (184 rows), then the exclusion tests.
- Evidence:
  ```
  size-band-calibration: excluded 145 owner-session:unmetered row(s) — cost never recorded, none estimated
  size-band-calibration: excluded 32 gate-latency row(s) — waits, not spend
  $ python3 (independent count, outcome field of docs/factory/costs.jsonl)
  unmetered 145 gate 32          # 145 + 32 + 7 costed rows = 184 = wc -l
  test_an_all_unmetered_ledger_excludes_every_row ... ok
  test_a_mixed_ledger_prints_each_nonzero_exclusion_in_order ... ok
  test_an_excluded_row_adds_no_cost ... ok
  test_only_unmetered_owner_sessions_leave_nothing_used ... ok
  ```
- Result: PASS

### 5. Each band prints misses beside cost and the re-plan rate from decompose_signals.py; unmeasurable named, never zero

- Check: the live S line carries cost and re-plan; the re-plan figure was recomputed from `python3 decompose_signals.py`. Misses (`over budget k of n`) print only at or above the floor, by design (architecture.md), so a refused band prints cost and re-plan but no miss count; the n = 5 test asserts `over budget <k> of <n>`.
- Evidence:
  ```
  $ python3 decompose_signals.py | grep first-live-dispatch
  ... feature:first-live-dispatch — ... re-plan 4 of 8 (added 3, dropped 0, split 1, merged 0; renamed 0) inferred ...
  S line: ... cost $5.908 total; re-plan 4/8 over 1 run(s) (0 unmeasurable)
  M/L: ... re-plan unmeasurable
  test_all_unmeasurable_runs_name_the_reason_never_zero ... ok
  test_a_failed_measurement_is_one_problem_and_all_unmeasurable ... ok
  test_a_band_pools_the_runs_that_hold_its_work_orders ... ok
  ```
- Result: PASS (live misses column is absent for every band because every live band is below the floor; the PRD criterion is "beside its cost" for reported bands, which the n = 5 test pins).

### 6. No number is hand-written: every figure recomputes from ledger rows; a fixture test asserts the figures

- Check: independent hand calculation of band S from docs/factory/costs.jsonl with a separate script, not the tool's code.
- Evidence:
  ```
  WO-0074 (6 rows) 5.4345177   WO-0076 (1 row) 0.4737711   sum 5.9082888
  tool prints: cost $5.908 total   (n 2 = two tokens, both size:S)
  re-plan: decompose_signals 4 of 8 for first-live-dispatch = tool's 4/8 over 1 run(s)
  determinism: two runs, md5 e5d0168723348a2d64216356c989e4af both times
  test_the_budget_comes_from_the_fixture_config ... ok
  test_a_band_at_the_floor_has_an_interval_and_totals ... ok   (figures recomputed in the test from fixture rows)
  ```
- Result: PASS

### 7. Stdlib only, no network call

- Evidence:
  ```
  $ grep -n "^import\|^from" size_band_calibration.py
  math, sys, collections.Counter, pathlib.Path, cost_ledger, decompose_signals,
  factory_config, cli (read_file, report, runner), knowledge_plane
  $ grep -n "socket\|urllib\|http" size_band_calibration.py   -> (no output)
  test_the_module_imports_no_network_module ... ok
  test_the_live_measure_runs_only_read_only_git_verbs ... ok
  ```
- Result: PASS

### 8. Tests through the public interface cover n = 4, n = 5, no rows, only-unmetered, mixed, each asserting exact strings

- Evidence:
  ```
  test_a_band_at_four_is_refused_with_cost_and_replan_only ... ok
  test_the_same_band_at_five_prints_the_interval ... ok
  test_an_empty_band_has_no_rows_and_no_interval ... ok
  test_an_all_unmetered_ledger_excludes_every_row ... ok
  test_a_mixed_ledger_prints_each_nonzero_exclusion_in_order ... ok
  Ran 48 tests in 0.024s  OK
  ```
- Result: PASS

### 9. run_tests, lint, kb drift, gates and gates --selftest pass (with flake re-check)

- Evidence:
  ```
  $ python3 run_tests.py   (x3, 8 workers)
  tests: 3470 tests across 108 modules in 25.6s on 8 workers, 0 problem(s)
  tests: 3470 tests across 108 modules in 25.7s on 8 workers, 0 problem(s)
  tests: 3470 tests across 108 modules in 25.5s on 8 workers, 0 problem(s)
  $ python3 run_tests.py -j 16
  tests: 3470 tests across 108 modules in 24.0s on 16 workers, 0 problem(s)
  $ python3 run_tests.py >/dev/null; echo $?      -> 0
  $ python3 lint.py        -> lint: 0 problem(s) across 34 skills
  $ python3 kb.py drift    -> drift: 0 problem(s)
  $ python3 gates.py       -> gates: 0 problem(s)     (exit 0)
  $ python3 gates.py --selftest -> selftest: ok       (exit 0)
  ```
- Result: PASS (no flake in four runs)

## Breakdown acceptance criteria not covered by a PRD criterion

### Protected paths unchanged vs origin/main

- Check: `git diff --stat origin/main...HEAD` over skills/, factory/templates/, .claude-plugin/plugin.json, docs/factory/costs.jsonl, cost_ledger.py, factory_init.py (MIRRORS lives there); then the full changed-file list from merge-base 27626c1.
- Evidence:
  ```
  (empty diff for the protected paths)
  $ git diff --name-only 27626c1 HEAD
  CLAUDE.md CONTEXT.md docs/adr/0112-...md docs/adr/README.md
  docs/features/size-band-calibration/{architecture,autorun-brief,breakdown,idea,prd}.md
  factory.py size_band_calibration.py tests/test_dual_membership.py tests/test_size_band_calibration.py
  $ grep size_band factory_init.py   -> (no output; not mirrored)
  ```
- Result: PASS

### one_owner pre-pass, dual-membership pin, front door

- Evidence:
  ```
  $ python3 one_owner.py | grep -c size_band   -> 0
  $ python3 -m unittest tests.test_dual_membership -> OK
  $ python3 factory.py size-band-calibration   -> same first lines as the module run
  ```
- Result: PASS

### Mutation checks (each applied, shown by diff, tests fail, tree restored)

- Evidence:
  ```
  M1 floor comparison:   -    if len(ordered) < floor:
                         +    if len(ordered) <= floor:
     FAILED (failures=5): at_the_floor_has_an_interval_and_totals, the_floor_comes_from_factory_config,
       a_custom_floor_moves_the_refusal_point, five_values_are_the_observed_range..., the_same_band_at_five_prints_the_interval
  M2 unmetered exclusion (spend = every entry, not cost_ledger.dispatched):
                         -    spend = cost_ledger.dispatched(entries)
                         +    spend = list(entries)
     FAILED (failures=4): mixed_ledger_prints_each_nonzero_exclusion_in_order, an_all_unmetered_ledger_excludes_every_row,
       each_row_is_counted_once_in_the_architecture_order, only_unmetered_owner_sessions_leave_nothing_used
  M3 owner-session count dropped:
                         -    owner = sum(1 for e in entries if cost_ledger.owner_session(e))
                         +    owner = sum(1 for e in entries if False)
     FAILED (failures=4): the same four report and selection tests
  after each: git checkout size_band_calibration.py; final unittest run: Ran 48 tests ... OK
  ```
- Result: PASS

## Failures

none.

## Not verified

- A live interval. The real ledger has two joined work orders, both S, so every live band refuses or is empty. Interval math is verified by fixture tests with hand-worked numbers and by the independent S cost and re-plan recomputation, not by a live n >= 5 band. This is the PRD's last open question (will metering ever produce volume), left for Operate.
- The per-band BRE for S against the live budget was not hand-computed (a refused band prints none).
- Whether the cost figures in costs.jsonl are themselves correct: the tool reads them as recorded.
