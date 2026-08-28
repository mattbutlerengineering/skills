---
stage: review
run: maintenance:an-errored-replay-can-still-pass
date: 2026-08-27
assumptions: []
---

# Review: an errored replay can still pass

## What was examined

The run's whole diff: `charter_replay.py` (`score_case`, `print_report`)
and `tests/test_charter_replay.py` (one new class, two new imports).
Read alongside the callers of `score_case` — `run_suite`, `print_report`,
`main`, `record` — and the two runners that produce the `error` field.
Nothing else in the repo reads a scored result.

## Findings

### Critical

None.

### Major

**The fix is at the scorer, not at the runner — and that is the right
place, but it deserves saying.** An alternative was to have
`claude_runner` raise or return nothing on a timeout, so no transcript
reached the scorer at all. That would have destroyed the partial
transcript, which is evidence: the record now carries both the error
*and* what the run managed to do before it stopped, and a human reading
a FAIL can see how far it got. `claude_runner`'s docstring already
argues for keeping the partial transcript; only its conclusion about who
draws the verdict was wrong. Accepted as designed.

### Minor

**`_case_problems` still accepts a case with no `require` expectation.**
It demands at least one `forbid` — "a regression case with no trap
checks nothing" — and is silent about requires. With the error consulted
this no longer lets an *incomplete* replay pass, which was the defect.
It still lets a *successful* empty replay pass a forbid-only case: a run
that did nothing at all is indistinguishable from a run that behaved.
That is a separate claim, about validation rather than scoring, and
folding it in here would have widened a scoped maintenance run into a
change to what counts as a legal case set — including a decision about
whether the four shipped cases (all of which happen to carry requires)
are the intended shape or a coincidence. **Deferred, with its owner
named**: `_case_problems`, `charter_replay.py:110`. Recorded here rather
than in `docs/backlog.md`, because the backlog line would have to be
appended on a branch nobody has merged.

**`error` is now derived twice in the same function's mind.** `score_case`
reads `transcript.get("error")` once into a local and uses it for both
the failure string and the returned field, so the two can no longer
disagree — that was deliberate. Noting it because the previous shape
(`"error": transcript.get("error")` inline) read as harmless and was the
thing that let the field drift away from the verdict in the first place.
No action.

## Process findings

**ADR-0036 clause 2 is not satisfied.** A non-authoring reviewer must
re-execute the verification and record it on the pull request. This
review is self-authored, so the branch is deliberately **held out of the
merge queue** — no PR is opened, nothing is merged, and the branch waits
for a human reviewer exactly as the other agent branches do.

**The tests pin the defect, not the scaffolding.** All seven were run
RED against `origin/main`'s `charter_replay.py` with the new test file
already in place (verification §3), so none of them is passing because
of a helper it brought with it.

## Fix / defer decisions

| Finding | Severity | Decision |
| --- | --- | --- |
| Fix sited at the scorer, partial transcript preserved | major | fixed as designed |
| `_case_problems` accepts a case with no `require` | minor | deferred — separate claim, owner named above |
| `error` read once into a local | minor | no action |
| ADR-0036 clause 2 unsatisfied | process | branch held out of the queue |
