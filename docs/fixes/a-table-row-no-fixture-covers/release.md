---
stage: ship
run: maintenance:a-table-row-no-fixture-covers
date: 2026-08-30
assumptions:
  - "The run stops at 'PR open'. Merge is ADR-0033 gate 3, a human decision. #421 closes on merge via the commit trailer."
---

# Release: a table row no fixture covers

## What shipped

- Branch `agent/a-table-row-no-fixture-covers`, commit `a24773b`
- **PR #422**, open against `main`
- Intake **#421**, closed on merge by the `Closes #421` trailer

One new fixture tree and two test files. No production-code change, no
mirrored file, so no `update-manifest` and no detector E interaction.

## State at hand-off

```
$ python3 -m unittest discover tests 2>&1 | tail -3
Ran 1346 tests in 16.421s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

Merge: **not done** — human gate.

## Seeds

- `_maintenance_stage_complete` gives `architect` and `decompose` the
  same completion expression. The new fixture closes the `decompose` row
  for one tree shape; the interaction between the two rows across
  re-entry depths is not enumerated. review.md §4 records why that was
  left alone.
- The same closure question applies to any other table in this repo that
  a fixture set claims to cover. `human_gates.GATES` and
  `sweeps.TRIAGE` were both checked during this session's wider sweep
  and are pinned indirectly (emptying either fails 10 and 36 tests
  respectively), so neither needs this treatment.
