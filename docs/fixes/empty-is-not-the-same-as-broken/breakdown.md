---
stage: decompose
run: maintenance:empty-is-not-the-same-as-broken
date: 2026-08-25
assumptions: ["One milestone, four items. The distinction (I1) lands before the rendering (I2) because rendering a fact the module cannot yet compute would mean writing the test against a hard-coded value."]
---

# Breakdown: say what was read

## Milestone 1 — the body distinguishes a failed stream from an empty one

- [ ] **I1 — `_change_requests` stops answering `[]` for a failed listing.**
  Return `None` on failure, `[]` on a successful empty read; `problems` is
  untouched.
  *Acceptance:* a test drives `run_mine` with `failing=["pr", "list"]` and
  asserts `_change_requests` returned `None` while the healthy-empty run
  returned `[]`, with the same problem string as today in the failing case.

- [ ] **I2 — `compose_queue` renders a `Sources:` line.**
  New `sources=None` argument; `None` renders today's body byte-for-byte.
  *Acceptance:* the existing body tests pass unedited, and a new test pins
  both worded forms — complete, and partial with a named unreadable stream.

- [ ] **I3 — `run_mine` words the two gaps.**
  Compute the timeline gap from `set(mirrored) - set(events_by_issue)` and
  the change-request gap from I1's `None`, word both, pass them down.
  *Acceptance:* the regression from `defect.md` inverts — a healthy-empty
  run and a failed-listing run now produce **different** bodies, and the
  difference names the stream that failed. A run with an unreadable timeline
  says how many of how many.

- [ ] **I4 — mirror and manifest.**
  `python3 factory_init.py update-manifest`, committed with the change.
  *Acceptance:* `python3 gates.py` reports no `E:` problem and
  `tests/test_factory_init.py` passes.

## Notes

*(deviations logged here, dated, as they happen)*
