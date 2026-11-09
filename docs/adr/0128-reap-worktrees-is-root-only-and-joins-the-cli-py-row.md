# reap_worktrees is a root-only tool and joins the cli.py row of the dual-membership set

- Status: provisional
- Date: 2026-11-08

Recorded by the worktree-reaper run (issue #1640), unattended, so it is
provisional. It follows ADR-0097, ADR-0106, ADR-0119 and ADR-0124 for the
`cli.py` row of the dual-membership set ADR-0091 pinned.

## Context

The queue profile's `## reap` section stated the worktree cleanup rule as
prose that each pass re-derived by hand. `reap_worktrees.py` implements it
once: four tests (clean, idle, no open PR, this tip merged), a dry run by
default, `--apply` to remove. It reports problems through `cli.report` and
reuses `cli.CLI_FAILURES`, which adds a root-only to mirrored pair that
`tests/test_dual_membership.py` pins.

## Decision

`reap_worktrees.py` is root-only: it manages the clone this factory runs
in, and no payload tool imports it, so it is not in `factory_init.MIRRORS`
and no template or manifest changes. It imports `cli`, so the pin's
`cli.py` row gains `reap_worktrees`. It also gets a `reap-worktrees` row in
`factory.py`'s `VERBS`, which `tests/test_factory_cli.py` requires of every
root module with a `__main__` guard.

## Consequences

- `cli.py` gains one more root-only importer. A future attempt at the
  tools/factory restructure (ADR-0091) has one more pair to account for.
- The tool never imports a mirrored module other than `cli`, so the edge
  adds no cycle.
