# A hit run seen before its clean partner still pairs when the partner arrives

- Status: provisional
- Date: 2026-10-24

Recorded by the `seen-before-partner` maintenance run
(`docs/fixes/seen-before-partner/`), unattended, so it is provisional.
Supersedes in part [ADR-0116](0116-the-lessons-seen-header-is-one-entry-per-signal-and-run.md):
the sentence in its Decision that "Pairing skips a hit run seen for the
pair's signal". What puts an entry in `seen` (a signal measured for the
run when the fold ran, whatever its count), the entry shape
`<signal>:<run ref>`, the refusal of the old per-run shape, the size bound,
the vote guard, the file's path, the lesson lines, the derived-only rule,
the single writer and the root-only import edges all stand.

## Context

ADR-0116 folds every measured (signal, run) into `seen`, and pairing skips
a hit run (count above 0) whose key is in `seen`. A hit run measured in an
`update` where no clean run of its kind and label exists yet is folded
without having paired, and when its clean partner arrives in a later
`update` the hit run is skipped and the lesson is never derived. One
`update` over both runs derives it. The loss is permanent (the same input
keeps writing nothing); it is reproduced through the real `update` in
`docs/fixes/seen-before-partner/defect.md`. The reverse order, a clean run
folded before any hit exists, loses nothing: pairing applies `skip` to the
hit run only and finds the clean partner in the full record list.

The header does two jobs. It stops a lesson dropped at 0 from being
re-derived from the same runs (ADR-0113 Consequences), and it stops a run
from voting on a lesson derived after the run was first measured. The
issue proposes folding a run only once it was used (paired as a hit, or
voted). That repairs the first job and breaks the second: reproduced in a
scratch clone over random update sequences, an unpaired hit run left
unseen downvotes every lesson derived after it, so a fresh lesson is
dropped by runs that never read it and a second `update` over unchanged
input changes the file (211 of 1,500 sequences). Folding it on a vote
instead reproduces the original loss through the vote path.

## Decision

- `seen` is unchanged: same entries, same fold, same vote guard. Pairing
  changes who it skips. A hit run seen for a signal is skipped only when
  it already had its chance, that is, when a clean run of the same kind
  and label, measured for that signal, is also seen. A seen hit run with
  no seen clean partner is offered to pairing again, and pairs with the
  first clean run in record order, as an unseen one does.
- The skip is decided in `fold`, from `seen` at the start of the update,
  and `pairs` keeps its signature and meaning: it skips the keys it is
  given. A hit run and its partner first measured in one `update` pair in
  that `update` and are both seen after it, so a lesson dropped at 0 is
  still not re-derived from them, and a clean run that arrives later,
  even earlier in record order, does not re-open the pair.
- The header's entry shape, `load`, `serialize`, validation, the vote
  guard and `MAX_LESSONS_BYTES` do not change. No migration: a header
  written under ADR-0116 is loaded as it is, and it heals the case this
  ADR is about (a seen hit run whose partner arrives afterwards). The
  trace of a hit run and its partner already both seen by the earlier rule
  is the trace of a dropped lesson, so the tool cannot tell a stranded
  pair from a dropped lesson and does not try; the recovery is ADR-0116's:
  delete the file and run `update`.

## Rejected alternatives

- **Fold a run only once it paired as a hit or voted**, the issue's
  rule, for the reasons in Context.
- **Fold a hit run only once it paired, and every other measured run as
  now.** Reproduced: the vote guard no longer covers an unpaired hit run,
  so it votes on lessons derived after it was first measured (211 of
  1,500 sequences changed the file on a second update).
- **Two header sets (measured and paired)**, which keeps the vote guard
  and fixes pairing but adds a second shape and a decision on every old
  entry, for a distinction the partner test recovers from the one set.
- **Upgrade an ADR-0116-era header on load.** Nothing in a header says why
  an entry is there, so any mapping guesses.

## Consequences

- The header is byte-for-byte what ADR-0116 writes: same size, same bound.
  Vote behaviour is unchanged.
- A hit run with no seen partner costs one scan of the records per
  update and no git call.
- A header written by the ADR-0116 tool before this change keeps one
  known gap: a hit run and its late partner that were both folded without
  pairing stay unpaired.
- A change to what `pairs` skips again needs a superseding ADR.
