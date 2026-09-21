---
stage: decompose
run: maintenance:row-done-guard
date: 2026-08-23
assumptions:
  - "The cut was not reviewed live — this run is autorun-driven, so the rows below are read out of architecture.md's Components and Interfaces sections rather than from the operator's judgment. A mis-sized row is a note to log at implement time, not a design change."
  - "Rows carry an item letter and a size class (ADR-0034 vocabulary), matching this repo's maintenance-run precedent. No row mints a WO-#### id and no row carries a (tracker: #N) reference: this is a backlog-seed run, and minting a WO- token with no issue behind it would run the dispatch plane ahead of the knowledge plane (ADR-0032). Issue #327 is the run's tracking issue, closed by the PR — not a work order."
  - "One item, not two. The guard and its tests are the same sitting, and the previous run in this repo (maintenance:gate-timeline-timestamp-trust) logged a deviation for splitting a comment-only row off a behavioural one and then landing both in one commit. This cut does not repeat that."
---

# Breakdown: give the checked-row accessor the guard its siblings have

Progress lives in the checkbox below. Source is `architecture.md` in this
directory, which chose to fix the grammar at its owner rather than at
detector G's call site.

**The one thing that must not happen.** `gates.merged_wo_rows` does not
change. Its `WO_TOKEN.search` and its ADR-0043 pre-ledger exclusion stay
exactly as they are — the run's claim is that fixing `row_done` is enough,
and editing G as well would make that claim untestable. If a diff in this
run touches `gates.py`, the item has been misread.

**Manifest churn.** `knowledge_plane.py` IS a `factory_init.MIRRORS`
entry, so the item must run `python3 factory_init.py update-manifest` and
commit the regenerated payload copy and manifest in the same change. (The
previous run learned this from a red mirror pin; this one states it up
front.)

**The battery is green at the item boundary**, in full: `python3 -m
unittest discover tests`, `python3 lint.py` (matching `lint: 0
problem(s)`) and `python3 gates.py && python3 gates.py --selftest`
(matching `gates: 0 problem(s)`).

## Milestone A: one module, one answer to "is this a row"

Demonstrable at the close: a line matching `DONE_ROW` but not `ROW` is
`False` to `row_done`, exactly as it is empty to every sibling accessor,
and detector G no longer counts it as a merged work order.

- [x] **A1** the guard, in the siblings' shape — size:S, blocked by: —
  - Accept: with the guard reverted, a `tests/test_knowledge_plane.py`
    case asserting a checked box with no space after it is `False` to
    `row_done` fails;
    with it in place that case passes, a companion case pins that
    `row_done` and `ROW.match` agree across the module's adversarial
    bullet shapes, and a third drives `gates.merged_wo_rows` over a
    breakdown containing the malformed row and finds it absent from the
    result. Every existing expectation in the suite is unmoved, the
    payload copy and manifest are regenerated in the same commit, and the
    full battery is green.
  - Blocked by: —

## Design gaps found

None. `architecture.md` answered the one open question — which function
absorbs the change — with the call-site measurement in `defect.md`, and
nothing in the cut needed a decision it had not made.

## Notes

**2026-08-23 — this file's own acceptance criterion tripped detector A.**
The criterion quoted the malformed row it describes, four-digit work-order
token and all, and detector A reads any `WO-####` in a breakdown file as a
work-order row owing a PRD citation:

```
A: docs/fixes/row-done-guard/breakdown.md:42 work-order row WO-00xx cites no PRD id
```

(The id is written `WO-00xx` above — quoting the real four-digit token
verbatim re-trips the same detector on the line that reports it, which is
how this note was written twice. `docs/backlog.md:38` uses the same
redaction for the same reason.)

The criterion now says the shape in words instead. Worth recording rather
than silently rewording: a run about a row grammar cannot quote a row in
its own breakdown, and the detector that caught it is not the one this run
is fixing.
