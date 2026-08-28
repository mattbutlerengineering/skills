# Autorun brief — a dead CLI scores as a pass

## Scale

Maintenance run, `re-entry: implement`. Artifacts at
`docs/fixes/a-dead-cli-scores-as-a-pass/`.

## What and why

`charter_replay.py` is the charter regression suite: it replays golden
fixture work orders against the role charters and writes a dated,
append-only snapshot under `evals/results/` as the evidence that the
charters still hold. Its scoring seam decides a case passed without ever
checking that the replay produced anything to judge, so a replay that
never ran can be recorded as a passing one.

CLAUDE.md's least-negotiable rule is the one this breaks: "Never
fabricate run or eval evidence."

## Scope

In scope: the pure scoring seam (`charter_replay.score_case`) and its
tests in `tests/test_charter_replay.py`.

Out of scope: the live runner and `cli.harness_run`. Whether
`harness_run` should read the child's exit status is a real question,
but it is the shared external-CLI seam (ADR-0039) with several callers,
and answering it there is a separate run. The fix here holds regardless
of what any runner does, which is the point of putting it in the pure
seam.

Also out of scope: changing the case-set validator. A forbid-only case
is legal by explicit design and its comment says why; the fix makes it
safe rather than banning it.

## Constraints

Stdlib only. The scoring seam stays pure — case plus transcript in,
verdict out — so CI keeps covering it with no model in the loop.

## Success

A case whose expectations are all `forbid` cannot score `pass` against a
replay that errored or produced nothing, in either the live or the
recorded path, and the suite exits nonzero.

## Release authorization

None. Prepare and stop.
