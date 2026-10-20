# decompose_signals joins the root-only importers of cli.py, knowledge_plane.py and protocol.py

- Status: provisional
- Date: 2026-10-18

Supersedes in part ADR-0106, its `cli.py` row, and ADR-0091, its
`knowledge_plane.py` and `protocol.py` rows. The rest of both ADRs stands.
Recorded by the `decompose-outcome-signals` feature run
(`docs/features/decompose-outcome-signals/`), unattended, so it is
provisional.

## Context

ADR-0091 pinned the dual-membership set that blocks the `tools/factory/`
restructure. The set is derived from the tree and asserted by
`tests/test_dual_membership.py`. After ADR-0106 it holds 43 root-only →
mirrored import pairs over nine modules:

- the `cli.py` row names 19 root-only importers;
- the `knowledge_plane.py` row names 10;
- the `protocol.py` row names 6.

The run adds `decompose_signals.py`, which measures Decompose outcome
signals from git history. It is root-only under ADR-0060's rule: no
payload tool imports it, and it measures this repo's own runs. It imports
three mirrored modules:

- `cli`, for `runner`, `CLI_FAILURES`, `detail`, `report` and `read_file`;
- `knowledge_plane`, for `breakdown_files`, `breakdown_rows`,
  `ROW`, `row_title`, `unfenced`, `WO_TOKEN`, `BLOCKED_BY` and
  `repo_root`;
- `protocol`, for `STAGE_ARTIFACTS` and `run_ref`.

Its fourth import, `eval_schema`, is root-only and crosses nothing.

## Decision

- The `cli.py` row reads 20 root-only importers: ADR-0106's 19 plus
  `decompose_signals`.
- The `knowledge_plane.py` row reads 11: ADR-0091's 10 plus
  `decompose_signals`.
- The `protocol.py` row reads 7: ADR-0091's 6 plus `decompose_signals`.
- The set is 46 pairs over the same nine mirrored modules. The mirrored
  → root-only direction is unchanged. `factory.py`'s `VERBS` gains a
  `decompose-signals` row for a root-only module, which loads no mirrored
  module by name.
- `tests/test_dual_membership.py`'s pin carries the three new pairs.

## Rejected alternatives

- **Retype the run walk, row grammar, fence rule and stage table in the
  tool**, so it imports only `cli`. That makes four second owners of facts
  `knowledge_plane.py` and `protocol.py` own, which is exactly what
  `one_owner.py` exists to flag.
- **Make it a `kb.py` or `gates.py` subcommand.** `gates.py` is mirrored,
  so a repo-only measurement would ship into every stamped repo.
  `kb.py` owns the knowledge base, not history measurements, and the pairs
  would still exist through `kb.py`.
- **Mirror it into the payload.** No payload tool needs it, and a stamped
  repo's history has no Decompose learning loop to feed.

## Consequences

- The restructure blocker set grows by three edges. A later move of
  `cli.py`, `knowledge_plane.py` or `protocol.py` under `tools/factory/`
  has one more root-only importer each to repoint.
- The pin fails again on the next new edge, as intended.
