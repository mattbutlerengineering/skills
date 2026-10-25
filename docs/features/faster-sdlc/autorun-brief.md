# Autorun brief: feature:faster-sdlc

Not an artifact. The brief autorun collects once, standing in for the
interviews the stages would otherwise run. Collected 2026-10-24.

## Run scale and entry

Feature, slug `faster-sdlc`, artifacts at `docs/features/faster-sdlc/`.
A resume: the run entered at Decompose on 2026-10-14 by the Owner's
choice to proceed with assumptions over a backfill (recorded in
`breakdown.md`'s `assumptions:`). Idea, PRD, UX Design and Architect are
not backfilled; the run orients at Implement.

## State at collection

Two breakdown rows were unchecked on 2026-10-24:

- **CI before/after record** — measured on 2026-10-15; the whole-run
  median missed (62.0s to 79.5s, runner queue time) while the `check`
  job halved (48.0s to 23.0s). Owner decision 2026-10-24: check the row
  on the job-level evidence. Recorded in `breakdown.md`'s Notes.
- **Merge-wait record** — readable on or after 2026-10-30, two weeks
  after the merge train's first run (2026-10-16 00:38 UTC), against the
  2026-10-14 baseline (median 0.64h, p90 13.5h, 96% of open-hours in
  PRs open longer than 4h). Checked only if p90 is under 4h, by its own
  rule.

## Resume

On or after 2026-10-30. No stage can do real work before then.
`stop-after:` is unset.

## Tracker

The rows already mirror #902 to #912, all closed. No new tracker
interaction.

## User-facing surface

None.

## Release authorization

**None.** Prepare-and-stop: Ship writes `release.md` with
`outcome: prepared` and `pending-merge:` naming the run's PR; no merge,
tag or plugin version bump (ADR-0095).

## Operate

operate:
  minimum-signal: the merge-wait read (median, p90 and the >4h
  open-hours share against the 2026-10-14 baseline) recorded in
  `breakdown.md`'s Notes, and Ship written back as `released`.

`users-observed:` is counted from the signal Operate finds; this brief
never supplies it.
