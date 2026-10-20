# pr_body_preflight joins the root-only importers of gates.py and cli.py

- Status: superseded in part by ADR-0110 (the cli.py row; provisional)
- Date: 2026-10-16

Supersedes in part ADR-0091: its measurement table's `cli.py` row (as
ADR-0097 left it) and its `gates.py` row. The rest of ADR-0091 stands,
and so does ADR-0097's decision; only its count moves. Recorded by the
`pr-body-preflight` feature run (`docs/features/pr-body-preflight/`,
an Architect re-entry), unattended, so it is provisional.

## Context

ADR-0091 pinned the dual-membership set that blocks the `tools/factory/`
restructure, derived from the tree and asserted by
`tests/test_dual_membership.py`. After ADR-0097 it is 41 root-only →
mirrored import pairs over nine modules. Its `cli.py` row names 18
root-only importers and its `gates.py` row names one, `factory_init`.

The `pr-body-preflight` run adds `pr_body_preflight.py`, a Claude Code
`PreToolUse` hook that refuses a `gh pr create` whose body would fail
detector B. It is root-only: the brief scopes it to this repo, it is
not a `factory_init.MIRRORS` entry, and no payload tool imports it
(ADR-0060's rule). It judges the body with `gates.pr_body_problems`,
B's one statement of the body rule, and it reads a `--body-file`
through `cli.read_file`, the guarded local-file read (ADR-0075). Those
are two more edges of the kind ADR-0091 counted.

## Decision

- The `cli.py` row reads 19 root-only importers: ADR-0097's 18 plus
  `pr_body_preflight`.
- The `gates.py` row reads 2: `factory_init` and `pr_body_preflight`.
- The set is 43 pairs over the same nine mirrored modules. The
  mirrored → root-only direction and the imports by name are
  unchanged, apart from `factory.py`'s `VERBS` gaining a
  `pr-body-preflight` row for a root-only module, which adds no
  mirrored module loaded by name.
- `tests/test_dual_membership.py`'s pin carries both new pairs.

## Rejected alternatives

- **Copy B's regexes into the hook**, dropping the `gates` edge. It
  makes a second owner of the rule and of B's problem strings, which
  is the drift the hook exists to remove.
- **A private `open()` for the body file**, dropping the `cli` edge.
  It is a second owner of how a local file read fails, the same
  rejection ADR-0097 made for a private `subprocess.run`.
- **Run `gates.py` as a subprocess over a synthesised CI event**,
  leaving the set at 41. It writes a temp file on every judged call,
  couples the hook to `cli.read_event`'s environment names, and costs
  a second Python start-up; the run's architecture rejected it on
  those grounds before the pin was considered.
- **Put the hook inside `gates.py`** as a subcommand, so no root-only
  module imports anything. `gates.py` is mirrored, so a repo-only hook
  adapter would ship into every stamped repo, against the brief's
  scope.

## Consequences

- The restructure blocker set grows by two edges. A later move of
  `cli.py` or `gates.py` under `tools/factory/` has one more root-only
  importer each to repoint, with the same fix as the others.
- The pin fails again on the next new edge, as intended.
