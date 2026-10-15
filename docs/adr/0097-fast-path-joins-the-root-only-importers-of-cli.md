# fast_path joins the root-only importers of cli.py

- Status: provisional
- Date: 2026-10-15

Supersedes in part ADR-0091: its measurement table's `cli.py` row. The
rest of ADR-0091 stands. Recorded by the `faster-sdlc` feature run
(`docs/features/faster-sdlc/breakdown.md`, Milestone 3; issue #909).

## Context

ADR-0091 pinned the dual-membership set that blocks the `tools/factory/`
restructure: 40 root-only → mirrored import pairs over nine modules,
derived from the tree and asserted by `tests/test_dual_membership.py`,
so that a change to the set is recorded rather than discovered by the
next review. Its `cli.py` row names 17 root-only importers.

Issue #909 adds `fast_path.py`, the ADR-0096 fast-path classifier. It
is root-only (ADR-0060's rule: mirrored iff a payload tool imports it,
and none does) and it shells out to git, which it does the way every
other root-only CLI tool here does: through `cli.runner("git")`, with
`cli.CLI_FAILURES` as the failure vocabulary and `cli.detail` for the
reason it prints. That is one more edge of the kind ADR-0091 counted.

## Decision

The `cli.py` row reads 18 root-only importers: ADR-0091's 17 plus
`fast_path`. The set is 41 pairs over the same nine modules; the
mirrored → root-only direction and the imports by name are unchanged.
`tests/test_dual_membership.py`'s pin carries the new pair.

## Rejected alternative

A private `subprocess.run` in `fast_path.py`, leaving the set at 40.
It would be a second owner of the git port and of how a git call
fails, which is what the one fake git at that port removed (#781), and
it would make the classifier the one root CLI tool that bypasses the
adapter discipline (ADR-0021) to keep a count still.

## Consequences

- The restructure blocker set grows by one edge of its most common
  kind. A later move of `cli.py` under `tools/factory/` has one more
  root-only importer to repoint, with the same fix as the other 17.
- The pin fails again on the next new edge, as intended.
