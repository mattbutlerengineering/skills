---
stage: verify
run: maintenance:a-config-that-is-not-an-object
date: 2026-08-30
assumptions: []
---

# Verification: a config that is not an object

## 1. The seam reports every non-object top level — PASS

```
$ python3 -c "... factory_config.load(root) for each shape"
  null       -> (None, ['config: .github/factory.json is not a JSON object'])
  []         -> (None, ['config: .github/factory.json is not a JSON object'])
  "factory"  -> (None, ['config: .github/factory.json is not a JSON object'])
  5          -> (None, ['config: .github/factory.json is not a JSON object'])
  true       -> (None, ['config: .github/factory.json is not a JSON object'])
```

The `null` case is the one that mattered most: it used to answer
`(None, [])` — a config of `None` with no problem attached.

## 2. The rule has one home — PASS

`object_problems` returns unlocated suffixes, the same
caller-prefixes-its-own-label split as `cost_ledger.line_problems`, so
the runtime reader and the gate cannot drift apart.

```
$ python3 -c "... factory_config.object_problems(v)"
  {}   -> []
  None -> ['is not a JSON object']
  []   -> ['is not a JSON object']
  5    -> ['is not a JSON object']
```

## 3. Detector F reports instead of dying — PASS

Driven through the CI command itself, on a full checkout with the
payload config replaced:

```
$ python3 gates.py                       # valid config, baseline
gates: 0 problem(s)

$ echo 'null' > factory/templates/factory.json && python3 gates.py
F: factory/templates/factory.json is not a JSON object
gates: 2 problem(s)
```

Before the fix this same command exited with an `AttributeError`
traceback. (The second problem is detector E: replacing the payload copy
by hand is itself a checksum drift — correct, and unrelated.)

Every shape behaves the same way:

```
[]         -> F: factory/templates/factory.json is not a JSON object
"factory"  -> F: factory/templates/factory.json is not a JSON object
5          -> F: factory/templates/factory.json is not a JSON object
```

## 4. A broken home does not mask the other home — PASS

F checks every candidate home rather than the first hit, and the skip is
per-file: a `null` payload copy still lets the installed copy be
reported. Pinned by
`test_a_non_object_home_does_not_mask_the_other_home`.

```
F: factory/templates/factory.json is not a JSON object
F: .github/factory.json wip_cap must be a positive integer
```

## 5. The fail-closed callers now actually fail closed — PASS

`cost_report.guard` documents that it fails closed. It now does so on
this input rather than raising:

```
$ python3 -c "... cost_report.guard(root)"
  null   verdict=PAUSE  cap=None  problems=['config: .github/factory.json is not a JSON object']
  []     verdict=PAUSE  cap=None  problems=['config: .github/factory.json is not a JSON object']
```

`work_queue.main` returns at its `if problems: return report(...)` guard
for the same reason — the problem list is no longer empty.

## 6. Full battery green, payload mirrored — PASS

1344 tests on the merge base, 1350 here: the six added above.
`factory_config.py` and `gates.py` are both mirrored, so
`update-manifest` ran and the payload copies carry the fix.

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)

$ python3 -m unittest discover tests
Ran 1350 tests in 18.366s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills

$ python3 gates.py
gates: 0 problem(s)

$ python3 gates.py --selftest
selftest: ok
```

## 7. Red before green — PASS

The six tests were written first and failed against the unpatched
modules:

```
$ python3 -m unittest tests.test_factory_config tests.test_gates
AssertionError: Tuples differ: (True, []) != (None, ['config: .github/factory.json is not a JSON object'])
...
Ran 194 tests
FAILED (failures=6, errors=15)
```

The 15 errors were the `AttributeError` raises themselves — the defect,
observed through the new tests.
