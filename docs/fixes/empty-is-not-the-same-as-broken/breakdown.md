---
stage: decompose
run: maintenance:empty-is-not-the-same-as-broken
date: 2026-08-25
assumptions: ["One milestone, four items. The distinction (I1) lands before the rendering (I2) because rendering a fact the module cannot yet compute would mean writing the test against a hard-coded value."]
---

# Breakdown: say what was read

## Milestone 1 — the body distinguishes a failed stream from an empty one

- [x] **I1 — `_change_requests` stops answering `[]` for a failed listing.**
  Return `None` on failure, `[]` on a successful empty read; `problems` is
  untouched.
  *Acceptance:* a test drives `run_mine` with `failing=["pr", "list"]` and
  asserts `_change_requests` returned `None` while the healthy-empty run
  returned `[]`, with the same problem string as today in the failing case.

- [x] **I2 — `compose_queue` renders a `Sources:` line.**
  New `sources=None` argument; `None` renders today's body byte-for-byte.
  *Acceptance:* the existing body tests pass unedited, and a new test pins
  both worded forms — complete, and partial with a named unreadable stream.

- [x] **I3 — `run_mine` words the two gaps.**
  Compute the timeline gap from `set(mirrored) - set(events_by_issue)` and
  the change-request gap from I1's `None`, word both, pass them down.
  *Acceptance:* the regression from `defect.md` inverts — a healthy-empty
  run and a failed-listing run now produce **different** bodies, and the
  difference names the stream that failed. A run with an unreadable timeline
  says how many of how many.

- [x] **I4 — mirror and manifest.**
  `python3 factory_init.py update-manifest`, committed with the change.
  *Acceptance:* `python3 gates.py` reports no `E:` problem and
  `tests/test_factory_init.py` passes.

## Notes

*(deviations logged here, dated, as they happen)*

**2026-08-25 — I5 added during Review: a truncated listing is a third
partial harvest.** The Review stage's first pass found that I1–I3 fixed
two of the three ways this harvest goes short and left the quietest one
in place. `cli.gh_read` treats a full window as a SUCCESS — "a full
window leaves the value usable and flips `truncated`" — so a listing cut
at its window returns a usable, short value, `_change_requests` maps it
like any other, and the new `Sources:` line asserted a clean read of a
listing it had only seen the top of. Measured before the fix, with both
listings full:

    Sources: gate rejections from 1 of 1 issue timelines; change requests
    from the PR listing.

Identical to a healthy harvest. This is the defect the run exists to
remove, reproduced inside the run's own fix, so it is repaired here
rather than seeded: I5 below, test-first like the rest. The design's D1
holds — `None` still answers only "was it read", and truncation rides
the caller-owned `truncated` list the way `problems` already does,
because a full window is read, usable, and short: two facts, two
channels.

- [x] **I5 — a truncated listing is named in the body.**
  Both listings, since both feed counts the line prints; the issue
  listing also shortens `mirrored`, so truncation there understates the
  printed denominator and the clause is the only correction available.
  *Acceptance:* two tests build a real full window (the convention
  `test_gate_digest` already uses — no patched constants) and assert both
  the unchanged `gh_read` problem string and a body naming the cut
  listing.
