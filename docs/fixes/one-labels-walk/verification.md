---
stage: verify
run: maintenance:one-labels-walk
date: 2026-08-24
assumptions:
  - "Criteria source: there is no prd.md — this is a maintenance run that entered at capture with re-entry: architect — so the criteria list is defect.md's Expected line and its explicit non-claim (D1-D4) plus every clause of breakdown.md's three acceptance criteria (A1.1-A1.2, A2.1-A2.4, A3.1), with the battery scored once as B."
  - "The equivalence measurement is scored against the OLD walk, in a detached worktree at 45f4b43. Re-running it after the fold would be tautological — the probe's reference expression IS the folded body — so the post-fold run is recorded but not scored."
  - "trigger_eval.py and charter_replay.py were NOT run: real model runs, on demand only, and no criterion names them. Recorded under Not verified."
---

# Verification: one walk, and nothing else moved

Verified at `74420f7`, five commits `main..HEAD`, working tree as the run
left it.

## Summary

**11 criteria. 11 PASS, 0 FAIL.**

The hand-rolled walk is gone, the seam is called, and the change is
provably confined: `cli.py`, `tests/test_sweeps.py`,
`tests/test_dashboard.py`, `tests/test_cli.py` and the whole of
`factory/` are byte-identical across the run, and every changed line in
`tests/test_one_owner.py` is a comment.

## D1 — one owner for the labels-array walk

```
$ grep -n 'entry.get("name")' plane_drift.py
(no match)
$ grep -n "^from cli import" plane_drift.py
31:from cli import label_names
$ grep -n "return sorted(name for name in label_names" -A1 plane_drift.py
53:    return sorted(name for name in label_names(issue)
54:                  if name.startswith("wo:"))
```

**PASS.** Extraction belongs to the seam; the `wo:` filter and the sort
are what is left here.

## D2 — no behaviour change on any reachable input

`defect.md`'s explicit non-claim. Measured against the **old** walk, in a
detached worktree at `45f4b43`, so the comparison is between the two real
implementations rather than between the fold and itself:

```
$ git worktree add -q --detach $S/old 45f4b43 && cp probe_equivalence.py $S/old/
$ cd $S/old && grep -c 'entry.get("name")' plane_drift.py && python3 probe_equivalence.py
1
missing labels key: [] [] agree
mismatches over all label-array shapes: 0
```

**PASS.** Twelve label-entry shapes in every arrangement up to length two,
every malformed `labels` value, and a missing key: zero disagreements.
Re-run post-fold it prints the same thing, which proves nothing and is
recorded rather than scored.

## D3 — the standing pre-pass finding clears

```
$ python3 one_owner.py | tail -1
one-owner: 8 problem(s)
$ python3 one_owner.py | grep plane_drift
(no group names plane_drift)
```

**PASS.** Nine groups to eight, and the miss-3 group is the one that went.

## D4 — the record no longer says the group is open

```
$ git diff -U0 main..HEAD -- tests/test_one_owner.py | grep -E "^[-+]" | grep -vE "^(\+\+\+|---)" | grep -vE "^[-+][[:space:]]*#" | grep -vE "^[-+]$"
(no output)
```

**PASS.** Every changed line in that file is a comment — so the two
headers now read as closed while the frozen fixture strings are untouched,
which is D4 and A3.1 in one measurement.

## A1.1 — the pins were green against the old walk

Re-derived rather than asserted, in a detached worktree at the A1 commit,
where `plane_drift.py` still carries the hand-rolled loop:

```
$ git worktree add -q --detach $S/a1 45f4b43
$ cd $S/a1 && grep -n 'entry.get("name")' plane_drift.py
37:    names = [entry.get("name") for entry in labels
$ python3 -m unittest tests.test_plane_drift.TestIssueLifecycle
Ran 10 tests in 0.000s

OK
```

**PASS.** Ten pins, green against the implementation they were written to
characterize, one commit before it changed.

## A1.2 — A1 changed no production file

```
$ git show --stat --format= 45f4b43
 docs/fixes/one-labels-walk/architecture.md | 134 +++++++++++++++++++++++++++++
 docs/fixes/one-labels-walk/breakdown.md    |  43 +++++++++
 tests/test_plane_drift.py                  |  63 ++++++++++++++
 3 files changed, 240 insertions(+)
```

**PASS.** Docs and one test file.

## A2.1 — the walk is deleted and the seam is called

Scored by D1's evidence above, plus the size of what changed:

```
$ git diff --stat main..HEAD -- plane_drift.py
 plane_drift.py | 34 ++++++++++++++++++++++++----------
 1 file changed, 24 insertions(+), 10 deletions(-)
```

**PASS.** Ten lines deleted — the walk, its import line's old form and the
old docstring — against twenty-four added, almost all of them the
docstrings that record why.

## A2.2 — the widening was watched to fail, for the right reason

```
$ python3 -m unittest tests.test_plane_drift
ERROR: test_an_entry_that_is_not_an_object_at_all_is_no_labels (tests.test_plane_drift.TestIssueLifecycle.test_an_entry_that_is_not_an_object_at_all_is_no_labels)
AttributeError: 'NoneType' object has no attribute 'get'
Ran 30 tests in 0.001s
FAILED (errors=1)
```

**PASS.** One failure, and it is the `AttributeError` the design named —
not an import error and not a fixture fault.

## A2.3 — the existing suites pass unchanged

Unchanged asserted structurally, not by eye:

```
$ git diff --stat main..HEAD -- tests/test_sweeps.py tests/test_dashboard.py tests/test_cli.py cli.py
(no output: all four byte-identical)
```

```
$ python3 -m unittest tests.test_plane_drift tests.test_sweeps tests.test_dashboard tests.test_cli
Ran 253 tests in 3.903s

OK
```

**PASS.** The seam's own suite, both callers' suites and the drift
module's pre-existing cases, none of them edited.

## A2.4 — no manifest churn

```
$ git diff --stat main..HEAD -- factory/
(no output)
```

**PASS.** `plane_drift.py` is not a `factory_init.MIRRORS` entry
(ADR-0060) and `cli.py` was not edited, so detector E and
`tests/test_factory_init.TestRealTreeMirrors` are green by construction
rather than by regeneration — and the seven open PRs against
`factory/manifest.json` gain no eighth conflict.

## A3.1 — the frozen fixture strings did not move

Scored by D4's measurement above, and confirmed behaviourally:

```
$ python3 -m unittest tests.test_one_owner
Ran 62 tests in 0.037s

OK
```

**PASS.** `TestSameKeys`, the miss-3 case and the both-misses case all
still find the historical shape, which is what proves the strings are the
strings.

## B — the battery

```
$ python3 -m unittest discover tests
Ran 1355 tests in 15.400s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

**PASS.** 1345 on `main` → 1355 here: ten A1 pins and the one widening
case, and nothing lost.

## Not verified

- **The other eight one-owner groups.** Out of scope by
  `autorun-brief.md`; each is its own seed, and `docs/backlog.md:53` says
  so. This run cleared one and touched none of the rest — the count going
  9 → 8 is the whole claim.
- **`sweeps.py reconcile` and `dashboard.py` in anger.** Neither was run
  against live GitHub. Both are covered by their own suites, which pass
  unchanged, and the change is provably behaviour-preserving on every
  input `reconcile_drift` can hand the function — but nothing here
  observed a real scheduled run.
- **`trigger_eval.py` and `charter_replay.py`.** Real model runs, on
  demand only, no criterion names them.
- **Whether the purity clarification is what ADR-0060 meant.** The module
  docstring now says purity is about runners and I/O rather than the
  import graph. That is this run's reading, recorded where a reader hits
  it; nobody who wrote ADR-0060 has confirmed it.
