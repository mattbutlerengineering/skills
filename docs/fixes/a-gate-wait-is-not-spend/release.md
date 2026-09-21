---
stage: ship
run: maintenance:a-gate-wait-is-not-spend
date: 2026-08-28
assumptions:
  - Prepare and stop. The brief authorizes no release, and ADR-0036
    clause 2 makes a non-authoring reviewer's re-executed verification
    the condition for merge.
---

# Release — a gate wait is not spend

**Prepared, not executed.**

## Pre-flight

- **Verification green.** Eight passing criteria and one explicit NOT RUN
  (the served console in a browser; `dashboard.html` was not modified).
- **Review clear.** No critical or major findings.
- **Battery.** 1350 tests OK, `lint: 0 problem(s)`, `gates: 0
  problem(s)`, `selftest: ok`, `one-owner: 9 problem(s)` unchanged.
- **No secrets in the diff.** Two files, both Python.
- **No migration and no data change.** The cost ledger is not read
  differently, written differently, or touched: `cost_ledger.read` still
  returns all 41 rows and the fix filters in memory. `evals/results/` and
  `docs/factory/costs.jsonl` are untouched.
- **Nothing to mirror.** `dashboard.py` is operator-level and explicitly
  not in `factory_init.MIRRORS` (its module docstring says so), so
  `factory/manifest.json` is unchanged and detector E is unaffected.

## Release steps (not executed)

1. A non-authoring reviewer re-executes `python3 -m unittest discover
   tests`, `python3 lint.py`, `python3 gates.py`, `python3 gates.py
   --selftest`, and records the output on the PR (ADR-0036 clause 2).
2. Merge the PR.

The run touches no `docs/adr/**`, `prd.md`, `architecture.md` or
`docs/design/**`, so clause 3 does not additionally apply.

## Rollback

```
git revert <merge-commit>
```

One call site and one docstring. No state is created, migrated, or
consumed, so a revert restores the previous behaviour exactly.

## Post-release check

On `main`, against the repo's own ledger:

```
python3 -c "import cost_ledger, cost_report, dashboard; \
  e, _ = cost_ledger.read('.'); \
  print(set(dashboard._spend(e)) == set(cost_report.aggregate(e)['by_wo']))"
```

must print `True`.

## Follow-up recorded, not done here

- `cost_ledger.dispatched`'s docstring names two callers and there are
  now three (review finding 6). Deferred because `cost_ledger.py` is
  touched by an unmerged agent branch.
