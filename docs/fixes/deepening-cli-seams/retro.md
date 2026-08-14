---
stage: operate
run: maintenance:deepening-cli-seams
date: 2026-08-14
assumptions:
  - "Signal window is one day (shipped 2026-08-13, retro 2026-08-14).
    Short, but not thin: a complete downstream feature run built on the
    deepened seams in that day, which is more real usage than most
    releases get in a week."
---

# Retro: deepening-cli-seams

The condition brief's target state had four clauses; each is scored
against what exists on `main` today.

## Outcomes vs. intent

### "The report seam has one owner of the summary line and the exit code"

- What happened: shipped — and stress-tested by arrival, not just by
  tests. The console (`dashboard.py`, built the very next day) imports
  eight `cli` names including `report` and `full_window` and retypes
  nothing: the first post-fold adopter to land *after* the sweep, clean.
  The gate-digest automation also ran on the shipped seam (8d9a5b4,
  gate-latency rows posted by the routine).
- Signal strength: measured (the console's imports are in the diff; its
  day of gathers against this repo ran `problems: []` throughout).

### "factory.py has one decided shape, recorded as a decision"

- What happened: ADR-0054 (front door routes humans) landed with the
  run; the release's post-check drove the previously-broken
  `charter-replay` dispatch on shipped code, and the dispatch has been
  pinned by tests across every green push since. The *live* replay has
  still not run post-fix (it costs money; the recorded-transcript path
  is what CI covers) — stated so the green isn't over-read.
- Signal strength: measured for dispatch; pending for a live replay.

### "The truncation policy no longer disagrees between callers"

- What happened: the safety half landed — the invented-drift defect is
  fixed, its reproduction is the regression test, and the two sites
  carrying the same hazard now agree. The uniformity half is at one of
  five declared window sites; the other four and two companion ADRs are
  `wo-huv`, open and untouched since the release day.
- Signal strength: measured for the fix; the sweep is deliberate,
  tracked residue — see Change below.

### "Candidates 3 and 4 have a recorded answer or a reasoned deferral"

- What happened: candidate 4's answer is recorded in the run's
  `architecture.md` (split `protocol.py`; amend ADR-0046's blocker) with
  its ADR riding `wo-huv`. Candidate 3's answer is the window-policy
  design above. Both are answers-on-record rather than shipped code,
  which is what the target state asked for.
- Signal strength: measured (the documents exist; nothing shipped is
  claimed beyond what shipped).

## Run retrospective

- Keep: enumerated evidence in the condition brief — call-site counts,
  `merge-base` ordering, zero-caller proofs. Scope arguments ended
  because the numbers were already on the page, and the ruled-out list
  kept six dead ends closed through the whole run.
- Keep: the release note's "inherit rather than rediscover" section
  actually got inherited — the two runs shipped since (process-dashboard,
  console-drag-ergonomics) decided their `Closes #N` targets before
  opening PRs and hit zero detector-B failures, and the `gh pr edit`
  trap never recurred (REST PATCH is now also a bd memory).
- Change: residue needs a pulse. `wo-huv` and `wo-bcs` sat untouched
  while two whole runs shipped past them — exactly the "cadence outruns
  sweeps" failure mode this run's own root-cause hypothesis names.
  Follow-up beads from a run should get a review-by date or a slot in
  the daily improvement routine's queue, not just an open state.
- Stop: nothing. The backfilled capture was the right call, was logged
  from both sides, and cost one honest note.

## Idea seeds

- A drift detector for retyped seam grammar — post-fold adopters are
  never re-checked: two mirrored tools retyped `cli.report`'s epilogue
  days after the ADR-0051 fold and only a manual deepening review
  caught it; the detector suite covers citations, checksums and
  staleness but not "a tool restates a seam it should call" (from:
  maintenance:deepening-cli-seams)

## Run complete

Closed 2026-08-14. Seed above appended to `docs/backlog.md`; `wo-huv`
and `wo-bcs` remain the tracked follow-ups in beads.
