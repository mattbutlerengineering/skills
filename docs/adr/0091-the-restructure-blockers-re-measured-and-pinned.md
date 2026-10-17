# The tools/factory restructure blockers, re-measured and pinned

- Status: superseded in part by ADR-0106 (the cli.py and gates.py rows; the cli.py row earlier by ADR-0097; accepted by the Owner, 2026-10-13)
- Date: 2026-10-13

The Owner chose this on 2026-10-13, in session. It resolves issue #783.

## Context

Three ADRs say what blocks moving the mirrored factory tools to
`tools/factory/` at the root, so the root layout equals the payload
layout. They disagree with each other, and every number they quote has
drifted:

- ADR-0046 names one blocker, `protocol.py`'s dual membership, and
  counts "14" mirrored tools.
- ADR-0059 replaces that with a nine-module table. Its header says
  accepted, while its own Consequences say the status is provisional.
- ADR-0065 tells future reviews to find "one blocker (`frontmatter.py`'s
  42 lines)" once a split lands. The split never landed. ADR-0059 says
  resolving `protocol.py` alone "must not be described as" unblocking
  the move.

A reader cannot tell what the blocker is without re-measuring, which is
the work these ADRs were written to save.

## The measurement

Measured at a4f324a with a `python3 -I` AST walk over the 45 root
`*.py` files, against the 26 `.py` sources in `factory_init.MIRRORS`
(19 root files are root-only). Every import counts, including
function-level imports.

| mirrored module | root-only importers | ADR-0059 said |
|---|---|---|
| `cli.py` | 17: adr_status, board, charter_recorded, charter_replay, dashboard, eval_schema, factory_init, kb, kb_drift, kb_harvest, launch_demo, lint, md_claims, one_owner, plane_drift, sweeps, trigger_eval | 6 |
| `knowledge_plane.py` | 10: adr_status, board, dashboard, kb, kb_drift, lint, md_claims, one_owner, plane_drift, sweeps | 2 |
| `protocol.py` | 6: board, dashboard, kb, kb_drift, lint, trigger_eval | 3 |
| `factory_config.py` | 2: dashboard, factory_init | 2 |
| `cost_ledger.py` | 1: dashboard | 1 |
| `cost_report.py` | 1: dashboard | 1 |
| `human_gates.py` | 1: dashboard | 1 |
| `gates.py` | 1: factory_init | 1 |
| `label_sync.py` | 1: sweeps | 1 |

That is nine mirrored modules and 40 importer pairs. ADR-0059 counted
the same nine modules but only 18 pairs.

Two blockers that a bare-import scan of root-only tools cannot see:

- **The other direction.** `conductor_merge.py:187` runs
  `from factory_init import MIRRORS`, so a mirrored module imports a
  root-only tool. The import is function-level and runs only in the
  factory source repo, but moving `conductor_merge.py` without
  `factory_init.py` still breaks it.
- **Imports by name.** `factory.py`'s `VERBS` loads 24 CLI modules
  through `importlib.import_module`. Twelve of them are mirrored
  (assembler, budget_guard, conductor, cost_report, gate_digest, gates,
  handoff, label_sync, rejection_mining, standards_index, validator,
  work_queue). No `import` statement names them, so an import scan
  misses all twelve.

Facts the earlier ADRs state that no longer hold:

- `frontmatter.py` does not exist. ADR-0065's split was never done.
- `protocol.py` is 404 lines. ADR-0065 says 291.
- The payload calls `read_frontmatter` from four modules, not two:
  `gates.py:95`, `assembler.py:53`, `knowledge_plane.py:29` and
  `conductor_run.py:38`. It is the only `protocol` name a mirrored
  module imports.
- `MIRRORS` has 26 `.py` sources, not 14. The newest is
  `gates_selftest.py`.

## Decision

**The restructure stays deferred.** ADR-0046's judgement holds: keep
the flat root. The blocker is not one file. It is the full set above:
40 root-only → mirrored import pairs over nine modules, one
mirrored → root-only import, and twelve mirrored modules loaded by name
from `factory.py`. A future attempt must account for all three, by
dual-homing shared primitives, reclassifying tools, or both.
Cutting `protocol.py`, or any other single module, does not unblock
the move. A review that says it does is citing a stale premise.

**The frontmatter split is withdrawn as a restructure step.** It
narrows one of nine modules and leaves `cli.py`'s 17 importers and
`knowledge_plane.py`'s 10 untouched. If someone wants it for payload
size (about 360 of `protocol.py`'s lines ship into every stamped repo
behind one function), that is a new proposal. It needs its own ADR and
must clear ADR-0046's shared-module bar on its own merits.

**The set is pinned by a test.** ADR-0059 left this open.
`tests/test_dual_membership.py` derives both directions from the tree
(an AST walk over root `*.py` against `factory_init.MIRRORS`) and
asserts them equal to this table. Adding or dropping a crossing import
fails CI, so the count cannot drift a fourth time without anyone
noticing. When it fails, record the change in an ADR that supersedes
this table, then update the pin. The `VERBS` count is not pinned here:
`tests/test_factory_cli.py` already pins `VERBS` against the root
modules.

## Consequences

- This ADR supersedes in part ADR-0046, ADR-0059 and ADR-0065: their
  blocker diagnoses, counts and line numbers, ADR-0065's "one blocker"
  direction, and ADR-0059's provisional note. Their bodies are not
  rewritten. ADR-0046's deferral and its account of the bare-sibling
  import convention still stand. So do ADR-0059's point that the
  blocker is a pattern, not a file, and ADR-0065's open question about
  root↔root `MIRRORS` pairs.
- A review that wants the current blocker reads this ADR and runs
  `tests/test_dual_membership.py`. It does not re-measure by hand.
- No code moves in this change.
