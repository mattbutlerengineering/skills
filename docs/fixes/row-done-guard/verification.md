---
stage: verify
run: maintenance:row-done-guard
date: 2026-08-23
assumptions:
  - "There is no prd.md — this is a maintenance run entering at capture — so the criteria list is breakdown.md's one acceptance criterion, defect.md's stated Expected behaviour, and architecture.md's two explicit claims (the contract narrows; detector G does not change). Nothing was invented to pad it."
  - "The tree scan is re-run rather than quoted from defect.md. Its line count moved 1460 -> 1538 because this run added artifacts containing checkbox rows, so a stale number would have been the wrong evidence for the same claim."
---

# Verification: one module, one answer to "is this a row"

## Summary

Five criteria checked, all pass. The narrowing the design promised is
demonstrated at the accessor, held as a property across every adversarial
bullet shape the suite knows, and shown at detector G — the one production
path where the two grammars could disagree.

## Criteria & evidence

### The defect no longer reproduces (defect.md, Expected)

- Check: the same four lines `defect.md` measured, driven through every
  `row_*` accessor. The two malformed rows must now agree with their
  siblings.
- Evidence:
  ```
    '- [x] **WO-0001** a real row — size:S, blocked by: —'
      row_done=True  row_work_order=WO-0001  row_size=S  row_title='a real row'  row_blockers=[]  row_pre_ledger=False
    '- [x]a **WO-0002** no space after the box — size:M, blocked by: —'
      row_done=False  row_work_order=None  row_size=None  row_title=None  row_blockers=[]  row_pre_ledger=False
    '- [x]**WO-0003** bold straight after the box — size:L'
      row_done=False  row_work_order=None  row_size=None  row_title=None  row_blockers=[]  row_pre_ledger=False
    '-[x] **WO-0004** no space after the bullet — size:S'
      row_done=False  row_work_order=None  row_size=None  row_title=None  row_blockers=[]  row_pre_ledger=False
  ```
- Result: PASS — every accessor now agrees on every line, including the
  already-correct control row and the already-correct bullet-shape case.

### A1 — the accessor pin and the agreement property

- Check: `python3 -m unittest tests.test_knowledge_plane -v`. The first
  case pins the two malformed shapes; the second is the property — nothing
  `row_done` calls a checked row may fail `ROW.match` — held across the
  twelve bullet shapes this class already knew plus the two new ones. Both
  were watched to fail before the guard landed: four red subtests,
  recorded in commit `4520083`.
- Evidence:
  ```
  test_a_box_with_no_space_after_it_is_not_a_row_at_all (tests.test_knowledge_plane.TestRowDone.test_a_box_with_no_space_after_it_is_not_a_row_at_all) ... ok
  test_row_done_never_disagrees_with_the_row_grammar (tests.test_knowledge_plane.TestRowDone.test_row_done_never_disagrees_with_the_row_grammar) ... ok
  ```
- Result: PASS

### A1 — detector G no longer counts a row nothing else can parse

- Check: `python3 -m unittest tests.test_gates -v`. The pin builds a
  breakdown holding one well-formed merged row (covered by the ledger) and
  one malformed checked row carrying a second work-order token, and
  asserts detector G reports nothing. Before the guard it reported that
  second token as a merged work order with no ledger line.
- Evidence:
  ```
  test_a_row_no_other_accessor_can_parse_is_not_a_merged_order (tests.test_gates.TestCostLedger.test_a_row_no_other_accessor_can_parse_is_not_a_merged_order)
  G reaches row_done through a raw WO_TOKEN.search rather than ... ok
  ```
- Result: PASS

### architecture.md's promise — detector G itself does not change

- Check: `git diff --stat main..HEAD` restricted first to the four caller
  modules, then to all non-test, non-payload Python.
- Evidence:
  ```
  ### gates untouched
  (empty above = untouched)
  ### non-test non-payload python in the run
   knowledge_plane.py | 10 ++++++++++
   1 file changed, 10 insertions(+)
  ```
- Result: PASS — `gates.py`, `work_queue.py`, `plane_drift.py` and
  `dashboard.py` are byte-identical to `main`. One file changed, and it is
  the accessor's own module. Ten insertions, no deletions: eight are the
  docstring paragraph explaining why the guard is load-bearing.

### architecture.md's measurement — the narrowing costs nothing here

- Check: re-scan every breakdown line in the tree through both grammars
  and count disagreements, then run the full battery.
- Evidence:
  ```
  lines scanned: 1538
  disagreements in the tree today: 0
  ```
  ```
  Ran 1347 tests in 15.279s

  OK
  lint: 0 problem(s) across 24 skills
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS — the contract narrows and no live row moves, which is the
  evidence ADR-0058 asked for when it left this gap open.

## Failures

None.

## Not verified

- **That no repo other than this one is unaffected.** The scan covers this
  tree. `knowledge_plane.py` ships in the factory payload, so a stamped
  repo could hold a malformed row that this change flips from counted to
  uncounted by detector G. That is the intended behaviour and it is stated
  in `architecture.md`'s contract section, but it is unmeasured outside
  here and the run does not claim otherwise.
- **`protocol._CHECKBOX`.** The second checkbox owner is untouched and
  unexamined. ADR-0058's alignment caveat still stands — the two grammars
  must move together — and this run did not move a bullet shape, only
  added a guard, so nothing was owed. Saying so is cheaper than leaving a
  reader to work it out.
- **The rejected alternative.** Whether `gates.merged_wo_rows` should read
  `row_work_order` instead of a raw `WO_TOKEN.search` was not tested,
  because it was not done. It is seeded at Operate.
