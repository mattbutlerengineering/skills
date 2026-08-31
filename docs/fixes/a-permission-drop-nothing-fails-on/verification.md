---
stage: verify
run: maintenance:a-permission-drop-nothing-fails-on
date: 2026-08-30
assumptions:
  - "Criteria are defect.md's three work items plus the standing triad; this run is re-entry: implement with no prd.md/breakdown.md pair."
  - "Every mutant below was applied to the real tree in an isolated worktree and reverted with `git checkout` immediately after. The four-grant mutant was run WITH `factory_init.py update-manifest`, because without it the mirror tests fire and the result proves nothing about permissions."
---

# Verification: a permission drop nothing fails on

## Criteria

| # | Criterion | Result |
| --- | --- | --- |
| 1 | Dropping `issues: write` from any of the four jobs fails by name, after `update-manifest` | **pass** — 4 named subTest failures |
| 2 | A new workflow fails until recorded | **pass** |
| 3 | A new job in an existing workflow fails until recorded | **pass** |
| 4 | A table entry for a deleted job fails | **pass** |
| 5 | No false failure on the current tree | **pass** — full battery green |
| 6 | `python3 -m unittest discover tests` | **pass** — `Ran 1348 tests ... OK` (1344 + 4) |
| 7 | `python3 lint.py` | **pass** — `lint: 0 problem(s) across 24 skills` |
| 8 | `python3 gates.py`, `--selftest` | **pass** — `gates: 0 problem(s)`, `selftest: ok` |

## Evidence

The battery on the branch tip, verbatim:

```
$ python3 -m unittest discover tests 2>&1 | tail -3
Ran 1348 tests in 16.329s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

The four-grant mutant, with the mirror synced the way the contributing
procedure says to sync it:

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
$ python3 -m unittest discover tests
FAIL: test_every_job_holds_exactly_its_recorded_grant (workflow='assembler.yml', job='dispatch')
FAIL: test_every_job_holds_exactly_its_recorded_grant (workflow='cost-report.yml', job='report')
FAIL: test_every_job_holds_exactly_its_recorded_grant (workflow='gate-digest.yml', job='digest')
FAIL: test_every_job_holds_exactly_its_recorded_grant (workflow='validator.yml', job='needs-review-label')
Ran 1348 tests in 18.760s
FAILED (failures=4)
```

The same mutant on `main`, before this change, is the defect itself:

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
$ python3 -m unittest discover tests
Ran 1346 tests in 16.068s
OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
$ grep -c 'issues: write' .github/workflows/cost-report.yml .github/workflows/gate-digest.yml
.github/workflows/cost-report.yml:0
.github/workflows/gate-digest.yml:0
```

## Mutants

| mutant | observed |
| --- | --- |
| Drop `issues: write` from cost-report, gate-digest, assembler, validator **and run `update-manifest`** | 4 failures, each naming its workflow and job: `(workflow='assembler.yml', job='dispatch')`, `cost-report.yml:report`, `gate-digest.yml:digest`, `validator.yml:needs-review-label` |
| Add an unrecorded workflow `zz-probe.yml` | `test_the_table_names_every_workflow_and_every_job` fails |
| Add an unrecorded job `extra:` to `sweeps.yml` | same test fails |
| Add a table entry `"ghost"` for a job that does not exist | `test_the_table_names_every_workflow_and_every_job` **and** `test_the_table_names_nothing_that_is_gone` fail |

## Two things the run got wrong and fixed

**The table was wrong on first write.** It recorded `assembler.yml:dispatch`
as `contents/pull-requests/issues` and the parser immediately failed it:
the job also holds `actions: write`, sitting below a three-line comment
that my earlier hand survey had stopped at. The parser was right and the
table was wrong. Recorded because it is the argument for the test: a
grant that a careful reader misses twice in one session is exactly the
grant that gets deleted.

**The first version raised `KeyError` on an unrecorded job.** Adding
`zz-probe.yml` produced a bare traceback from `EXPECTED[name][job]`
alongside the readable closure failure. That is the same rough edge
fixed in PR #416 a few hours earlier, reintroduced in new code. The
lookup now uses `.get` and defers to the closure test, which owns that
finding; the mutant re-run gives one readable failure and no traceback.

## Not verified

- That each recorded grant is *sufficient* for what the job does at
  runtime. That is a live-GitHub property; nothing here dispatches a
  workflow. What is verified is that the grants cannot change silently.
- The payload copies' permissions, deliberately — the lockstep tests own
  root↔payload equality.
