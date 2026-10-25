# The lessons file's seen header is one entry per signal and run

- Status: superseded in part by ADR-0117 (the pairing skip rule; provisional)
- Date: 2026-10-23

Recorded by the `lessons-per-signal-seen` maintenance run
(`docs/fixes/lessons-per-signal-seen/`), unattended, so it is provisional.
Supersedes in part [ADR-0113](0113-the-lessons-file-is-a-jsonl-ledger-of-voted-sourced-lessons.md):
the line-1 `seen` header's entry shape, `{"seen": [<run refs>]}`, in its
Decision. The file's path, the lesson lines, the derived-only rule, the
single writer and the root-only import edges stand.

## Context

ADR-0113's header lists one ref per run, folded in once the run has an
implement boundary. The three signals mature on different dates: re-plan
and design gaps exist at the implement boundary, review exists only once
`review.md` is written, after Implement. An `update` between the two folds
the run into `seen` with its review unmeasurable, and the run can then
never produce or vote on a review lesson (reproduced through the real
`update` in `docs/fixes/lessons-per-signal-seen/defect.md`). The header
stays necessary: it is what stops a lesson dropped at 0 from being
re-derived (ADR-0113 Consequences), so it cannot shrink to fix this.

## Decision

- Line 1 stays `{"seen": [...]}`. Each entry is `<signal>:<run ref>`, with
  `<signal>` one of `replan`, `design_gaps`, `review` (the
  `decompose_signals` field names, which are also the first part of a
  lesson id). A run is seen for a signal exactly when that signal was
  measured for it when the fold ran, whatever its count; a run
  unmeasurable for a signal is never seen for it. Pairing skips a hit run
  seen for the pair's signal, and a vote skips a run seen for the
  lesson's signal.
- `load` refuses a header entry in the old per-run shape with a labelled
  problem and does not upgrade it. Any upgrade guesses: marking an old run
  seen for all three signals reproduces the loss for review; marking it
  for two re-derives dropped review lessons. No lessons file exists on
  `main`, so a refusal costs no data.
- `load` refuses a file above `MAX_LESSONS_BYTES` (1 MiB) before reading
  it.
- Lesson lines are unchanged, so the Decompose skill, which reads lessons
  and not the header, needs no edit.

## Rejected alternatives

- **Keep the per-run key and fold only fully measured runs**, which keeps
  a run out of `seen` until review lands but then re-derives a dropped
  lesson from any run that never gets a review.
- **Upgrade old entries on load**, by either mapping above.
- **A new header key** (for example `seen_signals`), which would make a
  stale tool refuse the file loudly but would put the skill's
  "`seen` header" wording out of date and force a skill release for no
  reader of the header.

## Consequences

- The header grows to up to three entries per run (measured: 41 runs,
  1,430 bytes today, 5,336 bytes with all three signals).
- A tool older than this ADR that loads a new header treats every
  `signal:run` entry as an unknown run and re-derives from scratch; the
  tool is root-only and the Owner runs it from one checkout, so the skew
  is a single repo state, not a deployed one.
- A change to the header's entry form again needs a superseding ADR.
