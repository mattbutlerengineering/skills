---
stage: verify
run: maintenance:two-owners-for-the-results-snapshot
date: 2026-08-27
assumptions: []
---

# Verification: two owners for the results snapshot

Every criterion below carries its own evidence. Neither eval runner was
executed: both spend real money on model runs, so the whole verification
surface here is offline unit tests and a direct A/B of the two writers.

## 1. The seam owns the write — PASS

`eval_schema.write_snapshot` creates the directory, names the file
through `results_path`, serialises, and returns the path. Five new tests
pin that shape.

```
$ python3 -m unittest tests.test_eval_schema -k WriteSnapshot
.....
----------------------------------------------------------------------
Ran 5 tests in 0.003s

OK
```

## 2. Both runners produce byte-identical output to before — PASS

The pre-change implementation was reconstructed verbatim and run beside
the new one over both kinds and both harness states. Names and bytes
agree in every case.

```
  trigger  harness='omp'  name=trigger-omp-2026-07-02.json  bytes identical: True
  trigger  harness=None   name=trigger-2026-07-02.json  bytes identical: True
  charter  harness=None   name=charter-2026-07-02.json  bytes identical: True
old and new writers agree on name and bytes for every case
```

## 3. The existing recording tests pass unmodified — PASS

The trigger and charter suites were not edited; the only test file this
run touched is `tests/test_eval_schema.py`.

```
$ git diff --name-only -- tests/
tests/test_eval_schema.py

$ python3 -m unittest tests.test_trigger_eval_scoring tests.test_charter_replay
Ran 63 tests in 3.561s

OK
```

## 4. The full battery is green — PASS

1344 tests on the merge base, 1349 here: the five added above and no
others. No file this run edits appears in `factory_init.MIRRORS`, so the
payload manifest is untouched and detector E has nothing to diff.

```
$ python3 -m unittest discover tests
Ran 1349 tests in 16.372s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

## 5. The pre-pass reports nothing new — PASS

`one_owner.py` stands at nine problems, the same nine as on the merge
base. It never flagged this pair: it compares stated values and payload-
key reads, and two identical function bodies are neither. That is a
coverage gap in the pre-pass, recorded in `review.md` as an observation
rather than fixed here — `one_owner.py` is claimed by PRs #322 and #337.

```
$ python3 one_owner.py | tail -1
one-owner: 9 problem(s)
```

## Not verified

No live eval run. `trigger_eval.py` and `charter_replay.py` were never
executed against a model, so this run has no evidence that a real
recording still lands correctly end to end — only that the write path is
byte-identical to the one that did. `evals/results/` is unchanged by
this run.
