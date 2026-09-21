---
stage: verify
run: maintenance:a-gate-wait-is-not-spend
date: 2026-08-28
assumptions: []
---

# Verification — a gate wait is not spend

The reproduction ran against this repo's own committed ledger, so the
before and after below are the same 41 rows, not a fixture.

## 1. A gate-only work order has no spend

```
$ python3 -m unittest \
    tests.test_dashboard.TestSpendCountsOnlyDispatchedRows -v
test_a_gate_only_work_order_has_no_spend ... ok
test_a_gate_row_does_not_perturb_a_work_order_that_ran ... ok
test_the_console_renders_no_spend_for_a_gate_only_row ... ok
test_the_fixture_holds_both_row_kinds ... ok
test_the_rule_is_cost_ledgers_not_a_second_copy ... ok
test_the_two_ledger_readers_agree_on_the_work_order_set ... ok
----------------------------------------------------------------------
Ran 6 tests in 0.013s

OK
```

Before the fix, four of these six failed —
`test_a_gate_only_work_order_has_no_spend` with a dict holding the
fixture work order at `0.0` where it expected an empty one. (The
fixture's token is not spelled out here: detector C reads every
`WO-####` in `docs/**/*.md` as a claim about a real breakdown row,
and a test fixture's id has none.)

**Result:** PASS

## 2. The live ledger, before

```
ledger rows: 41 problems: []
gate rows: 22  dispatched rows: 19
gate-only WOs: ['WO-0001', 'WO-0002', 'WO-0003', 'WO-0013']
WOs in _spend but not in aggregate.by_wo:
  ['WO-0001', 'WO-0002', 'WO-0003', 'WO-0013']
their console spend value: {'WO-0001': 0.0, 'WO-0002': 0.0,
                            'WO-0003': 0.0, 'WO-0013': 0.0}
```

**Result:** PASS — four work orders rendered a measured `$0.00`.

## 3. The live ledger, after

```
rows: 41 problems: []
_spend keys == aggregate by_wo keys: True
gate-only WOs still carrying a spend value: none
WO-0001/0002/0003/0013 in spend: none
```

**Result:** PASS — the console's two ledger readers now agree on the
work-order set, and the four render an em dash.

## 4. A work order that ran is unchanged

The existing `TestOutput` fixture sums two dispatched rows to `$3.25` and
expects `None` for the two work orders with no rows; it was not touched
and still passes:

```
$ python3 -m unittest tests.test_dashboard.TestOutput -v
test_a_malformed_ledger_line_is_a_problem_and_the_table_renders ... ok
test_an_absent_ledger_is_silent ... ok
test_rows_join_label_state_pr_and_spend ... ok
----------------------------------------------------------------------
Ran 3 tests in 0.033s

OK
```

**Result:** PASS

## 5. The metrics half is unaffected

`_metrics` already routed through `cost_report.aggregate`; its pinned
numbers over the `LEDGER` fixture (which carries three gate rows) are
unchanged:

```
$ python3 -m unittest tests.test_dashboard.TestMetrics -v
test_a_missing_cap_is_a_problem_and_the_rest_still_reports ... ok
test_an_empty_ledger_reports_no_metrics ... ok
test_metrics_recompute_from_the_ledger_and_cap ... ok
----------------------------------------------------------------------
Ran 3 tests in 0.028s

OK
```

**Result:** PASS

## 6. The rule is not re-implemented

`test_the_rule_is_cost_ledgers_not_a_second_copy` patches
`cost_ledger.dispatched` to return nothing and asserts `_spend` returns
`{}` and that it was called once with the full entry list. A future
change to what counts as a spend row therefore reaches the console
without a second edit.

```
$ python3 -m unittest \
    tests.test_dashboard.TestSpendCountsOnlyDispatchedRows.test_the_rule_is_cost_ledgers_not_a_second_copy -v
test_the_rule_is_cost_ledgers_not_a_second_copy ... ok
----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
```

**Result:** PASS

## 7. Non-vacuity

`test_the_fixture_holds_both_row_kinds` asserts the fixture really
contains at least one gate row and at least one dispatched row, so the
five tests around it cannot pass over a set that is all one kind.

```
$ python3 -m unittest \
    tests.test_dashboard.TestSpendCountsOnlyDispatchedRows.test_the_fixture_holds_both_row_kinds -v
test_the_fixture_holds_both_row_kinds ... ok
----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
```

**Result:** PASS

## 8. The repo battery

```
=== unittest ===
Ran 1350 tests in 22.069s

OK
=== lint ===
lint: 0 problem(s) across 24 skills
=== gates ===
gates: 0 problem(s)
=== selftest ===
selftest: ok
=== one_owner ===
one-owner: 9 problem(s)
```

1350 is 1344 on `origin/main` plus the 6 this run adds. `one_owner` is
unchanged at 9 — the change removes a hand-rolled copy of a rule rather
than adding one.

**Result:** PASS

## Not verified

```
Not run: the served console in a browser.
```

**Result:** NOT RUN — `dashboard.html` was not modified. Its rendering of
the two cases is quoted in `defect.md` from the file, and criterion 3
verifies the value the page receives.
