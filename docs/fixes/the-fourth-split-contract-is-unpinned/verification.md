---
stage: verify
run: maintenance:the-fourth-split-contract-is-unpinned
date: 2026-08-30
assumptions: []
---

# Verification: the fourth split contract

## 1. Both sides are derived, and the check is non-vacuous — PASS

```
yaml refs    : ['changed']
intersection : ['changed']
```

Neither side is typed into the test: the refs come from a regex over
the real `gate-digest.yml`, the keys from three real `run_daily` calls
through the public interface. `assertTrue(refs, ...)` fails rather than
passes if the workflow stops referencing anything.

## 2. Renaming the Python key fails the test — PASS

`"changed"` → `"did_change"` in `gate_digest.py` (2 occurrences,
asserted before the edit):

```
AssertionError: None != 'false' : the no-new-rows path did not report
changed=false — fixture or key is wrong
FAILED (failures=1)
```

## 3. Renaming the YAML ref fails the test — PASS

`steps.digest.outputs.changed` → `...dirty`:

```
AssertionError: {'dirty'} not less than or equal to {'changed'}
AssertionError: 'changed' not found in {'dirty'}
FAILED (failures=2)
```

## 4. A key emitted on SOME paths but not all fails the test — PASS

This is the criterion that justifies departing from the two siblings.
Made the unreachable-tracker path return `{}` instead of
`{"changed": "false"}`:

```
AssertionError: {'changed'} not less than or equal to set()
FAILED (failures=1)
```

A **union**-based test — what `test_assembler` and `test_cost_report`
use — would have **passed** this mutation, because the other two paths
still emit `changed`. The workflow reads its ref unconditionally, on
whichever path the run took, so a key only some paths write still
expands to `''` on the others. `emitted_keys` therefore returns the
intersection of three real paths: unreachable tracker, no new rows, one
captured row.

The intersection is also strictly smaller than the union here — the
union would be `{changed, reason}` — so it is doing real work, not
coinciding.

Every mutation asserted its own `s.count(old) >= 1` before editing and
was confirmed with `git diff --stat` after; all three reverted, and
`git diff --stat -- gate_digest.py .github/workflows/gate-digest.yml`
is empty.

## 5. A hiccup: the first mutation run printed nothing

The first pass of §2–§4 ran the test through a shell variable,
`T="python3 -m unittest ..."` then `$T`. zsh does not word-split
unquoted parameters, so `$T` was one argument, not a command — every
mutation ran against nothing and the grep matched no verdict at all.

The mutations themselves had landed (`git diff --stat` confirmed each),
so this was a silent no-verdict rather than a false pass. Redone with
the command written out. Noted because it is the third variant this
session of the same trap: **evidence that a mutation ran is not the
same as evidence that the test ran.**

## 6. The failure message was tightened after the first result — PASS

§2 initially failed with a bare `KeyError: 'changed'` raised from a path
guard inside `emitted_keys`, not from the lockstep assertion. The test
failed, but for an unhelpful reason. The guards now use
`outputs.get(...)` with an explanatory message, so a renamed key reports
what actually went wrong. The guards were kept, not deleted: they are
what proves the three fixtures reach three different branches rather
than the same one three times.

## 7. Full battery — PASS

Base `main` is 1344; this branch is 1346. Two tests added.

```
$ python3 -m unittest discover tests
Ran 1346 tests in 26.707s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills

$ python3 gates.py
gates: 0 problem(s)

$ python3 gates.py --selftest
selftest: ok
```

No payload change — the only edited file is a test.

## What is NOT verified

- **`toolsmith-mine.yml` is not covered, because it has no contract.**
  `rejection_mining.run_mine` writes a `reason` key, but that workflow
  declares no step `id` and reads no outputs — swept, not assumed. The
  write is a harmless no-op (the value is also printed to stdout), not
  a defect.
- `steps.agent.outputs.execution_file` in `assembler.yml` is written by
  the Claude action, not by this repo's Python, so there is no split
  contract to bridge.
- `steps.find.outputs.pr` is asserted by literal `assertIn` in
  `test_assembler`, not derived on both sides. Left alone — see
  `review.md` §3.
