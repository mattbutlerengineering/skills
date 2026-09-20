---
stage: decompose
run: maintenance:one-labels-walk
date: 2026-08-24
assumptions:
  - "The cut was not reviewed live — this run is autorun-driven, so the two items, their sizes and their order are read out of architecture.md's Components and Interfaces & contracts sections rather than from the operator's judgment. A mis-sized row is a note to log at implement time, not a design change."
  - "Rows carry an item id and a size class (ADR-0034 vocabulary) and no work-order id and no (tracker: #N) reference, matching every maintenance run in docs/fixes/. Minting a WO-#### with no breakdown-row-then-issue behind it would run the dispatch plane ahead of the knowledge plane (ADR-0032)."
  - "A1 is a characterization item that lands GREEN, the same shape the previous run used. issue_lifecycle has no direct test today — it is covered only through reconcile_drift — so the pins are written at the intended interface against today's code, pass today, and must pass unchanged after A2. Written afterwards they would prove nothing about what was preserved."
---

# Breakdown: pin the walk, then delete it

Progress lives in the checkboxes below. Source is `architecture.md` in this
directory, which decided that `issue_lifecycle` keeps the `wo:` filter and
gives extraction back to `cli.label_names`.

**The ordering rule, which decides the cut.** A1 pins `issue_lifecycle`'s
behaviour directly, against today's hand-rolled walk. A2 replaces the walk
and every A1 pin must still pass, unedited. If one needs editing, that is
the signal to revert A2 rather than to edit the test.

**The battery is green at every item.** `python3 -m unittest discover
tests`, `python3 lint.py` (`lint: 0 problem(s)`) and `python3 gates.py &&
python3 gates.py --selftest` (`gates: 0 problem(s)`, `selftest: ok`).
Neither item touches a `factory_init.MIRRORS` entry — `plane_drift.py` is
root-only and `cli.py` is not edited — so **no item regenerates the
manifest**, and each asserts that by leaving `factory/` untouched.

## Milestone A: one owner for the labels-array walk

Items 1 and 2 of the design, plus the record item the design's fourth
component names.

- [x] **A1** pin `issue_lifecycle` at its own interface, against today's code — size:S, blocked by: —
  - Accept: a new `TestIssueLifecycle` in tests/test_plane_drift.py drives `plane_drift.issue_lifecycle` directly — it has no direct coverage today, only coverage through `reconcile_drift` — and pins: `wo:` names are returned sorted; a non-`wo:` name is dropped; a duplicate `wo:` label survives (`reconcile_drift`'s multiple-lifecycle-labels line needs it); an entry that is not an object, an entry with no `name`, a non-string `name` and an empty `name` each contribute nothing; a missing `labels` key, a non-list `labels` and an empty list each give `[]`; and the prefix test is case-sensitive, so `WO:MERGED` is not a lifecycle label. Every case passes against today's hand-rolled walk, before any change to plane_drift.py, and the commit message says so. No production file changes; `factory/` is untouched, so no manifest regeneration.
- [x] **A2** the walk is deleted and the seam is called — size:S, blocked by: A1
  - Accept: `plane_drift.issue_lifecycle` is `sorted(name for name in label_names(issue) if name.startswith("wo:"))` over a `from cli import label_names`, and `grep -n 'entry.get("name")' plane_drift.py` finds nothing. Every A1 pin passes UNCHANGED, and so do tests/test_plane_drift.py's existing `TestReconcileDrift` and `TestAbsencePolicy` and tests/test_sweeps.py and tests/test_dashboard.py. The module docstring's purity sentence says what purity means here — no runner and no I/O, not an empty import list — and the function docstring names the seam. One new case pins the widening the design accepted: a non-dict `issue` returns `[]` rather than raising `AttributeError`. `python3 one_owner.py` drops from nine groups to eight and no longer names `plane_drift`. `factory/` is untouched: `plane_drift.py` is not a MIRRORS entry and `cli.py` is not edited, so detector E and `tests/test_factory_init.TestRealTreeMirrors` are green by construction rather than by regeneration.
- [x] **A3** the record stops saying the group is open — size:S, blocked by: A2
  - Accept: the two comments in tests/test_one_owner.py that call this group live at HEAD — the fixture header (:271-277) and the miss-3 header (:786-789) — read as closed, naming this run's commit in the form the miss-1 header already uses. The frozen fixture STRINGS `LABEL_NAMES` and `ISSUE_LIFECYCLE` are byte-identical to what they are today: they are the historical shape the pass must keep finding, and rebasing them onto folded code would delete the acceptance evidence. `TestSameKeys` and the miss-3 and both-misses cases pass unchanged, which is what proves the strings did not move.

## Notes

Deviations, dated, as they happen.
