---
stage: verify
run: maintenance:a-filter-rebuilds-the-redacted-id
date: 2026-08-27
assumptions: []
---

# Verification: a filter rebuilds the redacted id

Baseline on `origin/main` (622e7c0) is 1344 tests. This run adds six.

## 1 — the reported reproduction no longer reproduces

The exact payload from `defect.md`, end to end:

```
$ python3 -c "
import sweeps
[i], _ = sweeps.sentry_intakes([{'shortId': 'WO-[0042]',
                                 'title': 'crash in dispatch'}])
print('key  :', i.key)
print('title:', i.title)
"
key  : sentry:WO-_0042_
title: [sentry] WO-_0042_: crash in dispatch
```

Before the fix these read `sentry:WO-0042` and
`[sentry] WO-0042: crash in dispatch`. PASS.

## 2 — the regression tests fail on the unfixed code

Run against `origin/main`'s `sweeps.py`, the new class fails for the
reason claimed, not for a setup error:

```
AssertionError: <re.Match object; span=(7, 14), match='WO-0042'>
  is not None : key names a work order: 'sentry:WO-0042'
```

47 failures across the file (the matrix test contributes one per
subTest). PASS — the tests were RED before they were green.

## 3 — no single unsafe character at any position smuggles the id

The matrix test tries each of seven characters the key filter refuses
(space, `[`, a backtick, a zero-width space, `/`, NUL, `|`) at each of
the six interior positions of `WO-0042`, and asserts the intake's key,
title and body name no work order — by `knowledge_plane.WO_TOKEN` and
by literal substring:

```
$ python3 -m unittest tests.test_sweeps.TestKeyFilterCannotRebuildARedactedId
Ran 6 tests in 0.001s

OK
```

PASS. Also covered by that class: a genuine `WO-0042` shortId is still
*redacted* rather than merely broken up (its key contains `redacted`),
and a well-formed `PROJ-1A` still yields exactly `sentry:PROJ-1A`, so
the change touches no legitimate key.

## 4 — the hostile payload now exercises the field that is edited

`TestUntrustedInputBoundary.HOSTILE` carries its work-order bait in the
`shortId` as well as the `title`, and its existing assertions still
hold — the path traversal is still neutralised, the fences still do not
escape, the control characters are still gone:

```
$ python3 -m unittest tests.test_sweeps.TestUntrustedInputBoundary
Ran 6 tests in 0.000s

OK
```

PASS.

## 5 — full battery

```
$ python3 -m unittest discover tests
Ran 1350 tests in 16.289s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

1350 = 1344 + 6. PASS.

## Not verified

- **Nothing runs against live GitHub.** No `gh` call was made; every
  sweeps test injects a fake runner, and this run made no exception.
- **The key format change is not observed against real filed issues.**
  A shortId containing a character outside `[A-Za-z0-9_.:-]` now yields
  a different dedupe key than it did before, so an intake already filed
  under an old key would be filed once more under the new one. Real
  Sentry shortIds are project slug plus alphanumeric suffix and contain
  no such character; that reasoning is an argument, not an observation,
  and it is recorded as one in `review.md`.
- **`one_owner.py` is unchanged at 9 findings** — the pre-pass reports
  the same set as the baseline, so this run neither added nor removed a
  second owner.
