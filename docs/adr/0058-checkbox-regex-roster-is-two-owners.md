# The checkbox-regex roster is two owners, not three

- Status: accepted
- Date: 2026-08-22

Amends ADR-0039's Consequences, which read: "only the three
checkbox-regex owners (knowledge_plane.ROW / protocol._CHECKBOX /
gates.MERGED_ROW) remain deliberately separate."

That was true on 2026-07-22. The three regexes genuinely differ: `ROW`
matches either box and requires trailing whitespace, `protocol._CHECKBOX`
captures the box contents and is deliberately factory-agnostic, and
`gates.MERGED_ROW` matched only the checked form.

`knowledge_plane.DONE_ROW` arrived on 2026-08-10 (#221, work-queue
parallel dispatch) as a fourth owner, and it *was* `MERGED_ROW` —
identical pattern, identical flags. Nothing said so, because the roster
had been fixed at three nineteen days earlier and was never revisited.
The code was equally stale: gates.py gave "only the checked form counts"
as the reason for a separate owner, and since August the knowledge plane
has had a checked-only form.

Measured before deciding: over the 924 breakdown lines in this repo plus
12 adversarial bullet shapes, `MERGED_ROW.match` and `row_done` disagreed
on nothing — 67 checked rows, found identically by both.

## Decision

**`knowledge_plane.row_done` is the one owner of the checked-row
grammar.** `gates.MERGED_ROW` is deleted; detector G and the reconcile
sweep read `row_done`. `sweeps.py` drops `import gates`, which existed
for that regex and nothing else.

**The roster is now two owners: `knowledge_plane.ROW` (with its
`row_done` accessor) and `protocol._CHECKBOX`.** ADR-0039's reasoning for
keeping `_CHECKBOX` separate is unchanged and still correct.

**The pre-ledger exclusion does not move.** `merged_wo_rows` keeps its
`and not row_pre_ledger(line)` — ADR-0043's rule and detector G's
concern, never the row grammar's.

## Consequences

- One definition of "checked row" for the five call sites that ask
  (gates.py, sweeps.py, work_queue.py, dashboard.py twice).
- `tests/test_knowledge_plane.py`'s alignment test loses its
  `gates.MERGED_ROW` assertions and keeps its `protocol._CHECKBOX` ones;
  `row_done` gains the direct coverage it never had, and a roster test
  fails if a fourth owner is added again.
- One tool-to-tool import fewer: sweeps.py no longer imports a detector
  module.
- ADR-0039 stays live and citable; its roster sentence is read through
  this amendment.
- Not addressed here: `row_done` is the only `row_*` accessor without the
  `ROW.match` guard its siblings apply, so `- [x]a` is a checked row to
  it and not a row to `row_size`/`row_title`/`row_blockers`. Closing that
  is a behaviour change with its own risk; it is seeded, not decided
  here.
- Status is provisional: the roster is the owner's to curate, and this
  amends a decision rather than recording a fresh one.
