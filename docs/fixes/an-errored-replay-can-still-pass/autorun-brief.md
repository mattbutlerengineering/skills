# Autorun brief — an errored replay can still pass

## Provenance

No user-supplied brief exists for this run. It was authored from this
session's own investigation under a standing autorun instruction. The
candidate came from testing a module's stated convention against its
code: `charter_replay.claude_runner` explains why a failed replay is
safe, and the explanation is a claim about the fixture set rather than
about the scorer.

## What and why

`charter_replay.score_case` computes its verdict from expectation
matches alone:

```python
failures, failed = [], []
for expectation in case["expectations"]:
    ...
return {..., "pass": not failures, ..., "error": transcript.get("error")}
```

The transcript's `error` is carried into the record and never consulted.
`claude_runner` sets it for a timed-out or failed CLI run, and reasons
about why that is enough:

> A timeout returns the partial transcript marked with the error rather
> than a fabricated one: an incomplete replay fails its required
> expectations, which is the honest verdict.

That holds only if every case has a `require` expectation AND the
partial transcript has not already satisfied them. Neither is
guaranteed. `_case_problems` requires a `forbid` — "a regression case
with no trap checks nothing" — and says nothing about `require`. And a
replay that times out late can have satisfied every `require` before the
clock ran out, while the `forbid` it exists to catch never got its
chance.

Both are demonstrable, one of them on a shipped fixture: a
`reviewer-asked-to-merge` replay marked `timed out after 900s` scores
`pass: true`.

This is a regression suite whose whole job is to fail when a charter has
weakened. A run that did not finish cannot certify a charter.

## Scale and re-entry

Maintenance run, slug `an-errored-replay-can-still-pass`. Re-entry is
`implement`: the error is already computed, recorded and printed; the
verdict just does not read it.

## Scope

In: `score_case` treats a transcript error as a failure, and
`print_report` loses the error line that becomes a duplicate of it.

Out: `_case_problems` gaining a `require` rule. That is a second and
separate claim — that a forbid-only case cannot tell a run that did
nothing from a run that behaved — and with the error consulted, the
error path is closed regardless of how a case is authored. Recorded as
an open finding.

Out: the live runner, which already returns the right transcripts. Out:
anything that spends money — no replay is run; the scoring seam is pure
and that is the point of it.

## Constraints

Stdlib only. `charter_replay.py` is not in `factory_init.MIRRORS`, so no
payload mirror and no manifest regeneration. `python3 charter_replay.py`
must not be run: a live replay costs money (CLAUDE.md).

## Release authorization

None. Ship prepares and stops.
