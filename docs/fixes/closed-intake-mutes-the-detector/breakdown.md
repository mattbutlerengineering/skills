---
stage: decompose
run: maintenance:closed-intake-mutes-the-detector
date: 2026-08-25
assumptions: ["One milestone. The rule is a single boolean in a single function, and cutting it into 'read the state' and 'use the state' would produce an item whose acceptance criterion is 'a field arrives that nothing reads'. The four corners of the rule are four acceptance criteria on one item, not four items."]
---

# Breakdown: a closed intake stops suppressing, unless the source re-reports

No work orders and no tracker mirror: this is a maintenance run, not a
dispatch. Issue #338 tracks the run as a whole.

## M1 — the dedupe rule knows what a closed issue means

**Demonstrable at the boundary:** `known_keys`, driven with a fixture
listing, returns a detector key for an open issue and omits it for a closed
one, while a `sentry:` key comes back from both.

- [x] **I1 — `RE_REPORTED`, and `known_keys` filters on state.**
  Add the namespace tuple with the comment that carries the rule; add
  `state` to the `--json` field list; collect a key unless it is
  detector-derived and its issue's state is the literal `"CLOSED"`.
  Rewrite the docstring so the Sentry paragraph keeps the case it covers
  and the detector-derived case sits beside it.
  *Acceptance, all four corners:*
  - `sweep:label-drift` on a CLOSED issue → **not** in the returned set;
  - `sweep:label-drift` on an OPEN issue → in the set;
  - `sentry:PROJ-7K` on a CLOSED issue → in the set;
  - a key on an issue whose `state` is absent, `None`, or any string other
    than `"CLOSED"` → in the set.

- [x] **I2 — the untouched contracts still hold.** *(blocked by I1)*
  *Acceptance:* a listing failure still returns `(None, problems)`; a full
  `LIST_WINDOW` listing still reports its existing problem string with
  byte-identical wording; `file_issues`' cap arithmetic and its
  `screen`-then-dedupe order are unchanged; every pre-existing case in
  `tests/test_sweeps.py` passes untouched.

- [x] **I3 — nothing fires on this repo today.** *(blocked by I1)*
  *Acceptance:* with the fix in place, both detectors still report clean —
  `python3 label_sync.py` prints `label-sync: 0 problem(s)` and
  `sweeps.reconcile(Path("."))` returns `([], [])` — so merging files no
  issue immediately. Evidence is the read-only detector calls only; no
  stage runs a sweep in a filing mode.

- [x] **I4 — battery green.** *(blocked by I1, I2)*
  *Acceptance:* `python3 -m unittest discover tests` OK;
  `python3 lint.py` reports `lint: 0 problem(s)`; `python3 gates.py`
  reports `gates: 0 problem(s)` and `python3 gates.py --selftest` reports
  whatever it actually reports, quoted.

## Notes

*(dated deviations from the design go here)*

**2026-08-25 — I1, `LIST_CALL` moved with the change.** `tests/test_sweeps.py:36`
pins the dedupe listing's exact gh argv, so adding `state` to `--json`
changed it. Three pre-existing cases failed on that pin alone and none on
behaviour — including `test_a_closed_issue_with_the_same_key_is_not_refiled`,
which drives a `sentry:` key on a CLOSED issue and still expects
suppression. That case passing unchanged is the Sentry half of the rule,
pinned by a test this run did not write.

**2026-08-25 — I4, the battery moved to a worktree.** Another session is
writing untracked files into this checkout, one of which is an ADR with no
index row, so `gates.py` — which reads the live tree — fails for reasons
unrelated to this branch. Every battery measurement was taken in a detached
worktree at the branch tip instead. Recorded in `verification.md` rather
than worked around silently.
