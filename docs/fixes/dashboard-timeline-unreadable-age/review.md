---
stage: review
run: maintenance:dashboard-timeline-unreadable-age
date: 2026-10-11
assumptions:
  - "The findings below came from an independent reviewer dispatched by the Conductor. This fixer recorded them and applied the fixes; the severity calls are the reviewer's."
  - "Nothing was pushed to main and no PR was opened during review. The Conductor owns the PR, the tracker issue (#665) and the backlog seed."
---

# Review: the dashboard cannot tell an unreadable age from an unknown one

## Scope

`git diff 147da0f..HEAD` on `fix/dashboard-timeline-unreadable-age`:
the capture, fix and verify commits (`60bf38a`, `55aac3b`, `c183b66`).
That is `dashboard.py` (`_timeline` returns `None` on an unreadable
fetch, `_queues` adds `aged`), `dashboard.html` (`renderNeedsYou` marks
an unreadable age on the item's line), `tests/test_dashboard.py`, and
the run's `defect.md` and `verification.md`. The review fixes below
touch only the test module and the two run documents.

## Findings

### Minor: the reproduction cites an uncommitted script

- Scenario: `defect.md` and `verification.md` quoted output from
  `python3 scratchpad/repro.py`, a file not on the branch, so a reader
  could not rerun the reproduction as written. The output itself was
  true: it agrees with the committed tests.
- Standard: none
- Decision: fixed. The script is now inline in `defect.md` as a fenced
  block, and both artifacts call it `repro.py`. It was rerun during
  review against a copy of the branch with `147da0f`'s `dashboard.py`
  swapped in (output matched `defect.md` byte for byte) and against the
  fixed code (output matched `verification.md` byte for byte).

### Minor: the unparseable-timeline test does not pin its problem strings

- Scenario: `test_an_unparseable_timeline_is_unreadable_not_empty`
  checked `aged: False` but not `state["problems"]`, so a parse failure
  swallowed without a problem string would still pass, leaving the
  "a failed read is a problem, never silent" rule unguarded on that path.
- Standard: none
- Decision: fixed. The test now asserts the exact `gh_read` strings,
  `dashboard: gh api timeline for #7 returned unparseable JSON:
  Expecting value: line 1 column 1 (char 0)` and the same for #8. It was
  first run with an empty expected list to see the real strings, which
  confirms the assertion bites.

## Passes with no findings

Correctness, design, security and complexity came back with no critical
or major findings. The failed-fetch problem string is unchanged, and
`dashboard.py` is not in `factory_init.MIRRORS`, so no manifest regen
applies.

## Verdict

Ready to ship. Both minor findings are fixed, and the full verify
battery is green after the fixes.
