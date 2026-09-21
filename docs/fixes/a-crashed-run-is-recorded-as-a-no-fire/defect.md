---
stage: capture
run: maintenance:a-crashed-run-is-recorded-as-a-no-fire
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance is recorded at the head of
  autorun-brief.md"]
---

# Defect: a crashed run is recorded as a no-fire

## Defect

`run_eval` folds two different outcomes into one bucket:

```python
try:
    fired = future.result()
except Exception as err:
    print(f"warning: run for {case_id!r} failed: {err}", file=sys.stderr)
    fired = None
counts = fired_by_case.setdefault(case_id, Counter())
counts[fired or "none"] += 1
```

`run_single_query` returns `None` when the router legitimately fired
nothing. A worker that *crashed* also becomes `None`. Both then increment
`counts["none"]`, and nothing downstream can tell them apart.

The warning goes to stderr. `record()` writes only `output`. So the
recorded file — the thing that lives forever under append-only
`evals/results/` and that LEDGER links as maturity evidence — contains no
indication that any run failed.

## Reproduction / Evidence

Every worker raising, driven through `run_eval`'s real interface with
`run_single_query` replaced by a function that raises
`RuntimeError("harness exploded")`:

```
  distractor-1   expected=None  fired={'none': 3} runs=3 rate=1.0 pass=True
  direct-1       expected=idea  fired={'none': 3} runs=3 rate=0.0 pass=False
  summary: passed=1 failed=1 total=2
  'errors' anywhere in the recorded record? False
  warnings went to stderr only, 12 line(s)
```

Read the first line carefully. **Every run of `distractor-1` crashed, and
it is recorded as a perfect pass** — `correct_rate` 1.0, `pass` true. The
snapshot asserts the router correctly declined to fire, on evidence that
does not exist.

The direction of the error is not symmetric, which is what makes it
worth fixing rather than tolerating:

| Case kind | `expected` | A crashed run counts as | Effect |
|---|---|---|---|
| distractor | `null` → `"none"` | **correct** | inflates the pass rate |
| direct / situational | a slug | a miss | deflates the pass rate |

The repo requires at least three distractor cases per eval set
(`eval_schema.validate`), so the inflating direction is always present.

## Root-cause hypothesis

Confirmed by reading, not inferred: `None` is overloaded. It is both
`detect_fired`'s legitimate "nothing fired" answer and the value the
exception handler substitutes for "we have no answer". The `or "none"`
then erases the distinction permanently.

## Blast radius

Bounded but permanent where it lands.

- `evals/results/trigger[-<harness>]-<date>.json` — append-only. A
  snapshot recorded during a flaky harness period overstates distractor
  performance and understates routing, and nothing in the file says so.
- `LEDGER.md` maturity links to those snapshots as evidence.
- `main()`'s exit code (`0` if `summary.failed == 0`) can report success
  for a run in which workers crashed.

No file in `factory_init.MIRRORS` is touched, so no manifest
regeneration. Verified against `factory_init.MIRRORS` directly.

## Ruled out

- **"Nobody knew" — false, and the record should say so.**
  `tests/harness_contract.py:67` already carries the comment *"A crashed
  worker buckets its run as 'none' and warns — without this check it
  would masquerade as a routing miss below"*, and asserts
  `assertNotIn("warning:", err)`. The bucketing behaviour was known. What
  that guard protects is **the test's own validity**, not the recorded
  artifact: it ensures the suite's assertions aren't satisfied by a
  crash. Production recording was left as it is. This run fixes the
  artifact, and does not claim to have discovered the behaviour.
- **The stderr warning is sufficient — false.** It is not in the
  recorded file, and the recorded file is what is read months later. A
  diagnostic that exists only in a terminal scrollback is not evidence.
- **Silent-failure-free in practice — untested, and not claimed.** No
  attempt was made to determine whether any existing snapshot under
  `evals/results/` was recorded during a crashing period. Those files are
  append-only and this run does not touch them.

## Work items

- [x] **A failed run is counted as a failure, not as a no-fire** — track
  errors per case separately from the fired Counter.
  - Accept: with every worker raising, no case's `fired` gains a `"none"`
    entry from the crash; a regression test drives this through
    `run_eval`'s real interface and fails first.
- [x] **The recorded output states the failures** — per case and in the
  summary total.
  - Accept: each result carries an `errors` count and the summary carries
    the total; with every worker raising, the distractor case is no
    longer recorded as a clean pass on absent evidence.
- [x] **No existing field changes when nothing fails** — old snapshots
  stay comparable.
  - Accept: the three existing contract tests in
    `tests/harness_contract.py` pass unmodified, and `errors` is `0`
    throughout a clean run.
- [x] **The confusion matrix records no phantom observation** — a
  crashed run contributes nothing to `confusion`.
  - Accept: with every run crashing, `confusion` is empty rather than
    carrying `"none"` counts the router never produced.
- [x] **Battery green** — `python3 -m unittest discover tests` OK,
  `python3 lint.py` 0, `python3 gates.py` 0 and `--selftest` ok, quoted
  in `verification.md`.

## Notes

- 2026-08-27 (correction to this brief, made before implementing):
  an earlier draft deferred "changing the scoring denominator" as a
  separate trade-off, keeping crashes bucketed as `"none"` and merely
  annotating them. That was wrong, and the reason is the confusion
  matrix. `summarize` reads the same `fired` Counter that scoring reads
  and accumulates it into `confusion` — a record of *observed* routing
  behaviour. A crash bucketed as `"none"` therefore does not just skew a
  rate; it writes an observation that never occurred into the evidence.
  Excluding crashes is part of not fabricating evidence. The brief was
  corrected rather than the fix weakened to match it.
- 2026-08-27: **what remains deliberately undecided** is whether a case
  with *some* errors should be penalised — a minimum-observation
  threshold, or failing any case that errored. This run does not decide
  it: a case with three clean runs and one crash still scores over its
  three real observations. That is a policy question with no default this
  skill supplies, and under the autorun rules it is surfaced for a human
  rather than guessed.

- 2026-08-27 (deviation — **a pinned test was deleted**): implementing
  work item 1 put the fix in direct conflict with
  `TestWorkerExceptionBucketsAsNone` in
  `tests/test_trigger_eval_run_eval.py`, which asserted
  `result["fired"] == {"none": 2}` under a missing CLI — precisely the
  behaviour this run removes. Before overriding it I looked for the
  decision it encoded. There is none: no ADR mentions the bucketing, and
  the plan that wrote the test, `plans/002-cover-run-eval-fanout.md`,
  disclaims it three ways. It calls its tests "characterization tests of
  existing behavior"; it lists `trigger_eval.py unmodified` as a done
  criterion and makes finding a real fan-out bug a STOP condition
  ("report it, don't fix production code here"); and its own test plan
  names this case "worker exception bucketed as `"none"` with a warning
  (**the silent-failure path**)". The test pinned a behaviour its author
  had declined to fix, not one anybody chose. The load-bearing half of
  its docstring — "never crash" — is preserved and now checked for both
  harnesses by the contract.

  It was deleted rather than rewritten because
  `test_a_crashed_run_is_an_error_not_a_no_fire` in
  `tests/harness_contract.py` covers the same scenario for *both* twins
  and asserts more (`errors`, `runs`, `fired`, and the summary total);
  keeping a claude-only near-duplicate would state one fact twice. The
  module docstring's claim that missing-CLI bucketing is a claude-only
  seam test was corrected in the same change, and the four imports the
  deletion orphaned were removed. Flagged in `review.md` for human
  sign-off: this changes recorded eval semantics.

- 2026-08-27 (deviation — scope grew by one line in `summarize`): work
  item 4 was written expecting `confusion` to need no change. It did.
  `summarize` builds each row with `confusion.setdefault(expected, {})`
  *before* reading the case's `fired` Counter, so a case with no
  observations still creates a row. That was unreachable before this run
  — every run bucketed somewhere, so `fired` was never empty — and my
  change made it reachable, printing as a bare `  idea:` heading with no
  cells. The code is pre-existing but the reachability is mine, so the
  guard belongs to this run rather than to a deferred finding: a case
  whose every run errored now contributes no row at all.

- 2026-08-27 (deviation — a sixth work item, found by the review pass):
  scoring on observations only removed an accidental safety net. Before
  this run, a *partial* crash — say 2 of 3 runs raising — bucketed as
  `fired={"none": 2}` and dragged `correct_rate` to 0.33, below the
  default 0.5 threshold, so the case failed and `main` exited 1. After
  the fix that case scores `1/1 = 1.0` and passes. The all-crash case is
  handled correctly (zero observations, no pass), but the partial case
  regressed in visibility, and neither `print_report` nor `main`
  mentioned errors at all. `print_report` now names the loss, per case
  and in a summary warning line, covered by
  `TestPrintReportNamesLostRuns`. The exit-code half is deferred to a
  human — see `review.md` finding 1.
