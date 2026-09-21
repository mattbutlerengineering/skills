---
stage: verify
run: maintenance:a-forbid-only-case-checks-nothing
date: 2026-09-20
assumptions: []
---

# Verification — a forbid-only case checks nothing

Every criterion below was run on this branch, `fix/charter-replay-forbid-only-case`.

## 1. `validate()` rejects a forbid-only case

The exact case from `defect.md`'s reproduction, on the fixed code:

```
>>> charter_replay.validate({"version": 1, "cases": [c]}, ROOT, "cases")
["cases case 'c1' has no require expectation (a successful empty replay checks nothing)"]
```

Before the fix this returned `[]`.

**Result:** PASS

## 2. `score_case` is untouched — the fix is at the validator, not the scorer

```
>>> charter_replay.score_case(c, {"tool_calls": [{"name": "Bash",
...     "input": {"command": "ls"}}], "text": ""})
{'id': 'c1', 'role': 'swe', 'pass': True, 'failed': [], 'failures': [],
 'tool_calls': 1, 'error': None}
```

Identical to the before-fix run in `defect.md`. This is deliberate:
`score_case` defends the transcript it is handed (#365's job); this run's
job is to stop a case with no positive expectation from reaching a
replay at all. A case-set *file* built this way is now rejected before
`run_suite` ever calls `score_case`.

**Result:** PASS (behaves as designed, not a regression)

## 3. The regression test, RED then GREEN

`test_case_with_no_required_behaviour_checks_nothing` was added first
and confirmed failing against the unfixed `_case_problems` (11 failures
total — this test plus the 10 tests using the `forbid_only()` helper,
whose self-check also flipped):

```
FAIL: test_case_with_no_required_behaviour_checks_nothing (tests.test_charter_replay.TestValidation...)
AssertionError: "... has no require expectation ..." not found in []
Ran 63 tests in 4.542s
FAILED (failures=11)
```

After the fix, the same run:

```
$ python3 -m unittest tests.test_charter_replay -v
Ran 63 tests in 4.600s

OK
```

**Result:** PASS — RED confirmed before the fix, GREEN after.

## 4. The four shipped golden cases still validate clean, and all carry a require

```
$ python3 -m unittest tests.test_charter_replay.TestGoldenCaseSet -v
test_every_case_carries_a_require ... ok
test_every_case_names_the_trap_it_plants ... ok
test_every_fixture_work_order_exists ... ok
test_replay_coverage_matches_the_declared_subset ... ok
test_set_loads_without_problems ... ok

Ran 5 tests in 0.001s

OK
```

`test_set_loads_without_problems` pins `factory/evals/charters.json`
loading with zero problems; `test_every_case_carries_a_require` (new)
pins the specific fact this fix depends on. `factory/evals/charters.json`
itself is unmodified — `git diff --stat` shows only `charter_replay.py`
and `tests/test_charter_replay.py`.

**Result:** PASS

## 5. Collateral tests that built a forbid-only case for an unrelated
reason still test what they meant to test

```
$ python3 -m unittest tests.test_charter_replay.TestValidation -v
test_any_chartered_role_is_valid ... ok
test_case_naming_no_trap ... ok
test_case_with_no_forbidden_behaviour_checks_nothing ... ok
test_case_with_no_required_behaviour_checks_nothing ... ok
test_duplicate_case_id ... ok
test_invalid_scope_and_mode ... ok
test_invalid_set_yields_no_cases ... ok
test_malformed_json ... ok
test_missing_file ... ok
test_missing_fixture_work_order ... ok
test_missing_version ... ok
test_uncompilable_pattern ... ok
test_unknown_role ... ok

Ran 13 tests in 0.007s

OK
```

**Result:** PASS

## 6. `TestAVerdictNeedsEvidence` (the #365 evidence-rule suite) is
unaffected — score_case's independent defense still holds

```
$ python3 -m unittest tests.test_charter_replay.TestAVerdictNeedsEvidence \
    tests.test_charter_replay.TestTheGoldenSetsRequiresAreNotTheGuarantee -v
Ran 18 tests in 0.006s

OK
```

**Result:** PASS

## 7. The repo battery

```
$ python3 -m unittest discover tests
Ran 1619 tests in 20.240s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

1619 is `origin/main`'s count plus the 2 new tests
(`test_every_case_carries_a_require`,
`test_case_with_no_required_behaviour_checks_nothing`).

`one_owner.py` (on demand, outside every gate): `one-owner: 7 problem(s)`,
identical to `origin/main` — this diff adds no shared literal or payload
key across modules.

**Result:** PASS

## 8. Nothing to mirror

`charter_replay.py` is not in `factory_init.MIRRORS`:

```
>>> [k for k in factory_init.MIRRORS if "charter_replay" in str(k)]
[]
```

No `factory/templates/**` file and no `factory_init.MIRRORS` root file
is touched, so `python3 factory_init.py update-manifest` is not owed and
was not run.

**Result:** PASS

## Not verified

```
Not run: a live charter replay against a real model.
```

**Result:** NOT RUN — a live replay costs money and is on-demand only
(CLAUDE.md). Everything this run changed is in the pure validation seam,
which CI covers with no model in the loop.
