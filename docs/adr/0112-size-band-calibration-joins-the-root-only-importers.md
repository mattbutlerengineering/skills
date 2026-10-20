# size_band_calibration joins the root-only importers of cli.py, knowledge_plane.py, cost_ledger.py and factory_config.py

- Status: provisional
- Date: 2026-10-20

Follows ADR-0110, which added `decompose_signals` to three rows of the
dual-membership set ADR-0091 pinned. Recorded by the `size-band-calibration`
feature run (`docs/features/size-band-calibration/`), unattended, so it is
provisional.

## Context

After ADR-0110 the set is 46 root-only to mirrored import pairs over nine
mirrored modules, asserted by `tests/test_dual_membership.py`. The run adds
`size_band_calibration.py`, which computes per-band error intervals from
the cost ledger. It is root-only under ADR-0060's rule: no payload tool
imports it, and it measures this repo's own Decompose sizing. It imports
four mirrored modules:

- `cli`, for `report` and the injected git runner;
- `knowledge_plane`, for `breakdown_files` and `parse_row`;
- `cost_ledger`, for `read`, `dispatched`, `gate_wait` and `owner_session`;
- `factory_config`, for `load`, `resolve_budget` and
  `resolve_calibrate_floor`.

Its other import, `decompose_signals`, is root-only and crosses nothing.

## Decision

- The `cli.py` row reads 21 root-only importers, `knowledge_plane.py` 12,
  and the `cost_ledger.py` and `factory_config.py` rows each gain
  `size_band_calibration`.
- The set is 50 pairs over the same nine mirrored modules. The mirrored to
  root-only direction is unchanged. `factory.py`'s `VERBS` gains a
  `size-band-calibration` row for a root-only module.
- `tests/test_dual_membership.py`'s pin carries the four new pairs.

## Rejected alternatives

- **Retype the ledger read, the breakdown row grammar, the budget table
  and the floor in the tool.** Four second owners of facts that
  `cost_ledger`, `knowledge_plane` and `factory_config` own.
- **Import `conductor_calibrate` for its ledger walk.** It adds
  `conductor`, `conductor_close` and `conductor_flow` as dependencies for
  a different size band (the issue label) and an input, closed batch
  ledgers, that costs.jsonl already holds.
- **Mirror it into the payload.** No payload tool needs it, and a stamped
  repo has no Decompose learning loop.

## Consequences

- A later move of any of the four mirrored modules under `tools/factory/`
  has one more root-only importer to repoint.
- The pin fails again on the next new edge, as intended.
