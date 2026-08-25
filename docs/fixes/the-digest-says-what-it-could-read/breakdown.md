---
stage: decompose
run: maintenance:the-digest-says-what-it-could-read
date: 2026-08-25
assumptions:
  - "No tracker mirror. This run implements no work order — intake #346 is a defect issue, not a WO — so no item carries a (tracker: #NNN) reference and ADR-0032's dispatch mirror is untouched."
  - "Two milestones split by FACT, not by file. Both touch gate_digest.py, but M1 is complete and demonstrable on its own (the per-item mark works with the footer still absent), which is the milestone bar the decompose skill sets."
---

# Breakdown: the digest states its own coverage

## M1 — the per-item fact: an unreadable timeline is marked

- [x] **I1** `Item` record, and `_queues` stops defaulting — size:S, blocked by: —
      (architecture.md §Contracts)
      *Acceptance:* `_queues` emits an item whose `aged` is False for an
      issue absent from `events_by_issue`, and True for one present with
      an empty event list. A test drives both through `run_daily` with the
      repo's injected gh fake and asserts the two items differ.

- [x] **I2** `compose_digest` renders the per-item mark — size:S, blocked by: I1
      (architecture.md §Contracts, table row 3)
      *Acceptance:* the digest line for an unaged item reads
      `- #123 title — age unknown (timeline unreadable)`. The two lines
      that the defect brief measured as identical are now different, and a
      test asserts that inequality directly rather than asserting one
      string.

## M2 — the whole-digest fact: a truncated listing is stated

- [x] **I3** `compose_digest` takes `listing_truncated` and renders the footer — size:S, blocked by: I2
      (architecture.md §Contracts)
      *Acceptance:* the parameter is required (no default — calling with
      two arguments raises `TypeError`, and a test pins that). With it
      True the footer carries a sentence naming the consequence; with it
      False the footer is byte-for-byte what it is today.

- [x] **I4** `run_daily` passes `read.truncated` — size:S, blocked by: I3
      (architecture.md §Components)
      *Acceptance:* the full-window run from the defect brief now produces
      a digest body that is NOT equal to the healthy run's body, and the
      existing problem-string assertion in
      `test_a_full_issue_window_is_reported_and_the_digest_still_posts`
      still passes unchanged.

## M3 — the payload stays in lockstep

- [x] **I5** mirror `gate_digest.py` and regenerate the manifest — size:S, blocked by: I4
      (CLAUDE.md §Factory templates are checksum-pinned)
      *Acceptance:* `python3 factory_init.py update-manifest` run and
      committed; `python3 gates.py` reports `gates: 0 problem(s)` (detector
      E green) and `tests/test_factory_init.py` passes.

## Coverage check

Every component named in `architecture.md §Components` appears above:
`_queues` (I1), `compose_digest` (I2, I3), `run_daily` (I4). Every row of
the requirement-traceability table maps to an item: truncation to I3+I4,
the timeline mark to I1+I2, the body-asserting tests to the acceptance
criteria of I2 and I4.

## Notes

**2026-08-25 — I1 and I2 implemented as one item.** I1's acceptance
criterion asked for a test that drives `_queues` and asserts two items
differ. `_queues` is private, and the repo's convention (CLAUDE.md: *tests
assert the exact strings through public interfaces*) has exactly one
counter-example in ~1350 tests. Splitting the data change from its
rendering would have needed a private-function test to satisfy I1 alone,
so both land together and the acceptance is met at the `compose_digest`
and `run_daily` seams instead. The criterion was written wrong, not the
change.

**2026-08-25 — two pre-existing tests changed their assertion.**
`test_a_failing_timeline_still_posts_the_digest` and
`test_an_unparseable_timeline_still_posts_the_digest` each asserted
the unmarked item line — number, title, no
suffix — on a run whose timeline could NOT be read — the exact line `defect.md` measured as indistinguishable from a
readable-but-eventless history. They pinned the defect as intended
behaviour. Both now assert the marked line; both keep their
problem-string assertions byte-for-byte, which is the half that must not
move. Flagged here because editing a test to make a change pass is
normally the wrong move, and this is the case where it is not.
