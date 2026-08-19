# The three human gates get a module of their own

- Status: provisional
- Date: 2026-08-18

## Context

The three gates are the factory's only human decision points (ADR-0033;
CONTEXT.md), and their queues live as `wo:` lifecycle labels on the
mirrored issues (ADR-0032). The vocabulary that says what a gate IS —
its ledger name, the label it waits on, the label that confirms its
pass, its digest heading — and the walk that reads one issue's label
history against it were written inside the first tool that needed them,
`gate_digest.py` (WO-0017). Three more callers then reached in rather
than the vocabulary moving out:

- `dashboard.py:52` imports `GATES, label_events, mirror_map,
  waiting_since`;
- `rejection_mining.py:40` imports `GATES, label_events, mirror_map`;
- `gates.py:777-778` reads the tuple **positionally** —
  `{name for gate in mod.GATES for name in gate[1:3]}` — inside
  `LABEL_DECLARERS`, from detector J. A CI detector depends on the field
  order of a leaf tool's constant.

The copies then disagreed, which is the second half of CLAUDE.md's bar.
`gate_digest.gate_passages` (gate_digest.py:99-115) and
`rejection_mining.gate_rejections` (rejection_mining.py:69-87) carry the
same confirmations list and the same stay-collection loop, and then
spell the same window test two ways —
`c >= start and (next_start is None or c < next_start)` versus
`start <= ts and (window_end is None or ts < window_end)`. The invariant
that joins them — the two tools partition completed stays between them,
every stay a passage there or a rejection here, never both — exists only
as prose, in a docstring at rejection_mining.py:62-66. Nothing executes
it, so nothing catches the day the two spellings stop agreeing.

That is multiple real callers AND observed divergence between the
copies: the two-part bar, met.

## Decision

**`human_gates.py` owns the gate vocabulary and the stay partition.** A
new root module, mirrored into the payload like every other shared
module (ADR-0037's four seams, ADR-0047's roles seam).

- It owns `GATES`, `label_events`, `completed_stays`, `gate_passages`,
  `gate_rejections`, `waiting_since`, `waited_seconds` and
  `gate_labels()`.
- **A gate row becomes a `Gate` namedtuple** (`name`, `queue`,
  `passed`, `heading`). Positional unpacking keeps working at the three
  sites that iterate the rows, and the detector names the field it
  wants instead of slicing it — the same move, for the same reason, as
  `cost_report.GuardResult`.
- **Detector J calls `gate_labels()`.** `LABEL_DECLARERS` keys
  `human_gates` and stops depending on field order. The declaring site
  in J's problem string changes accordingly, from `gate_digest.py` to
  `human_gates.py`; the string fires only against a broken taxonomy, and
  the new name is the true one.
- **`completed_stays(events, gate)` returns `[(start, end,
  confirmed)]`** — one walk, one window test. The digest keeps the
  confirmed stays, the miner keeps the rest, and the invariant that was
  prose is now the return value both of them filter.
- **The module is pure.** No gh, no ledger, no filesystem, no clock:
  events in, gate facts out, testable with a literal list.

**The name is `human_gates`, not `gate_plane`.** CONTEXT.md spends
"plane" on exactly two authorities — knowledge and dispatch (ADR-0032) —
and the gates are decision points on one of them, not a third. The
module takes ADR-0033's own noun.

What deliberately did NOT move — this decision is bounded by its
evidence, not by what happens to sit nearby:

- **`_timelines`** (gate_digest.py:189, rejection_mining.py:165) and
  `dashboard._timeline`. They are gh reads with an owner of their own at
  the cli seam; putting a network adapter inside a pure module would
  couple two seams to save nothing, and what still differs between them
  is their label and their local meaning, which stays theirs
  (ADR-0051).
- **`_post_digest` / `_post_queue`** (gate_digest.py:253,
  rejection_mining.py:206). Tracker mutations with per-tool titles,
  markers and pin semantics; no divergence was observed between them,
  and their home would not be the gate vocabulary anyway.
- **`compose_digest` / `compose_queue`, `_capture_latency`** and the
  ledger writes — per-tool text and cost-ledger business.
- **`mirror_map` goes to `knowledge_plane.py`, not here.** It is built
  from `breakdown_files`, `row_work_order` and `row_tracker_issue` and
  names no gate; ADR-0039 already placed the tracker-mirror grammar
  there. A module that also owns the mirror map has two subjects.

## Consequences

- `gate_digest.py`, `rejection_mining.py`, `dashboard.py` and detector J
  become thin callers, and no module imports a leaf tool for shared
  vocabulary any more.
- The partition invariant is executable and gets its first test: for one
  event history, passages and rejections together are exactly the
  completed stays, and no stay is in both. It passes before the move
  (the two spellings agree today) and after it (there is one spelling).
- `human_gates.py` joins `factory_init.MIRRORS` as an identity entry —
  required, not optional: `gate_digest.py` and `rejection_mining.py`
  both ship and both import it as a bare sibling, so a stamped repo
  without it is a broken stamp. `python3 factory_init.py
  update-manifest` runs in the same change (detector E), the payload's
  `tools/factory/` count goes from 16 to 17 in docs/setup.md, and
  `EXPECTED_RELS` in tests/test_factory_init.py gains the row. It does
  not join `factory_init._PRODUCT_TOOLS`: that tuple respells Makefile
  commands, and no target invokes this module.
- One output change, deliberate: detector J's declaring site name (see
  above). Every other string in the tree stays byte-identical.
- A fourth tool that needs to know what a gate is imports one module
  instead of copying a stay walk out of the digest — which is how the
  divergence this ADR closes was created in the first place.
