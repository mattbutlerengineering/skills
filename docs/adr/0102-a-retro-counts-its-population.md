# A retro counts its population, and a run is complete once it has

- Status: provisional
- Date: 2026-10-16

Amends ADR-0021's run-complete rule. "A run is complete when retro.md
exists" becomes "when retro.md exists and carries its population
line"; orientation still reads only the working tree (ADR-0100), and
the shape is the Ship outcome's (`outcome:` in `release.md`, decided
in pull request #968) — a frontmatter field the predicate reads, with
the field's absence read as legacy.

## Context

Three consumer autorun retros closed their runs with no one observed
and nothing saying so. One graded eleven of its own Review deferrals,
filed thirty-seven minutes before the run's merge with bodies opening
"Deferred from the Review stage", as post-ship findings; two of them
were user-facing defects still live. The operate skill listed feedback
sources and said to let the release breathe, and autorun said to run
operate only when feedback existed — but under autorun the brief had
no Operate section, so the stage inherited Ship's authorization,
answered its own interview, and a run's own deferrals looked exactly
like feedback (issue #944).

## Decision

1. **The population line.** `retro.md` frontmatter carries
   `users-observed: <N>` and `signal-source: <where>`
   (`protocol.RETRO_POPULATION_FIELDS`). `0` is a valid count and
   changes the verdict vocabulary: nothing is landing, adopted or used
   with no one there, so each outcome's signal is `unobserved` and
   "what happened" records state, not use.
2. **Operate completes on it.** `protocol._retro_populated`, wired
   into both walk tables, reads the two fields: a count of zero or
   more with a source completes the stage; a placeholder, a bad count,
   or either field alone leaves it pending. The retro short-circuit
   keeps retro.md's rank — a populated retro is a complete run whatever
   lies before it, an unpopulated one is Operate not yet complete
   whatever lies before it — and `stage_states` now takes its one
   "current" row from `next_stage` instead of re-deriving it, so the
   invariant holds by construction. `board.py` asks orientation
   whether a run is complete instead of testing for retro.md itself.
3. **A retro with neither field is complete.** Every retro written
   before this line — twelve in this repo — would otherwise reopen as
   an active run, and run discovery would list them all. The same call
   the Ship outcome made for `outcome:` (#968); strictness later means
   backfilling, not changing the rule.
4. **The run's own debt is never feedback.** An issue is the run's own
   when it was created before the run's merge (the pull request
   `release.md` names, or the release log's date), its body says it
   was deferred from the Review stage, or it cites the run's
   `review.md` or `verification.md`. Operate lists those under Open
   debt and counts them toward nothing.
5. **Autorun's brief gets an `operate:` section** — `wait: <N days>`,
   `minimum-signal: <what must exist>`, or `skip` — and operate runs on
   it, never on Ship's authorization. `skip` is a protocol-sanctioned
   skip recorded in the report; the run stays active until someone has
   feedback. The brief never supplies the count.
6. **The router restates it, and lint pins the restatement.**
   `lint.ROUTER_CONDITIONALS` gains the `users-observed:`/`retro.md`
   conditional, as `ux:` and `re-entry:` already have.

## Alternatives that lost

- **A prose rule only.** The skill already said to let it breathe and
  listed real feedback sources; three retros walked past both. A field
  the predicate reads cannot be walked past.
- **A gates detector on retro.md.** Would catch it in CI, after the
  run had already read as complete to `next`, the board and the
  dashboard; orientation is where "complete" lives.
- **Strict legacy (absent means pending).** Twelve finished runs
  reopen; see Decision 3.
- **The count as a section, not frontmatter.** Sections are prose the
  predicate cannot read offline without a second grammar.

## Consequences

- A retro that honestly says `users-observed: 0` is a complete run;
  the pipeline no longer rewards a retro for finding feedback that is
  not there.
- `stage_states` is now a thin view over `next_stage`; the two can no
  longer disagree, and `board.py` has one fewer owner of "complete".
  The board's "complete without retro.md" branch is now unreachable
  (Operate complete implies retro.md) and is left for a cleanup.
- The autorun brief has one more section to collect; a brief that
  omits it leaves operate un-run, which is the previous behaviour made
  explicit.
