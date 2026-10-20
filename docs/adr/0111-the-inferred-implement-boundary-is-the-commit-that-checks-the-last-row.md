# The inferred implement boundary is the commit that checks the last row

- Status: provisional
- Date: 2026-10-18

Supersedes in part ADR-0109: the inferred implement boundary in its
Decision, and its Consequences bullet that says the two implement windows
agree. The observed rule, the inferred decompose boundary and the two
labels stand. The decision is the Owner's, taken live in session as
decision 7 of the `decompose-outcome-signals` autorun brief
(`docs/features/decompose-outcome-signals/autorun-brief.md`). The details
below it were filled in by an unattended Architect re-entry, so this ADR is
provisional until the Owner confirms them.

## Context

`decompose_signals.py` reads re-plans and design gaps from a window that
runs from the decompose boundary D to the implement boundary I. An
observed I is the protocol's `docs(<scope>): implement` commit. That
commit closes Implement, and the protocol counts Implement done when every
checkbox in the breakdown is checked. ADR-0109 inferred I as the first
commit after D that checks any row, which is the start of Implement. It
then claimed the two windows agree, because the work-item keys at the
first tick equalled the keys at the implement commit on the 3 runs that
had both.

Review falsified that claim on this run's own row. The committed record
(`evals/results/decompose-signals-2026-10-18.json`) measured
`decompose-outcome-signals` with `implement inferred a8dbcb9; re-plan 0
of 13`. Once its implement commit existed, the same run read `implement
observed 56baba9; re-plan 2 of 13 (added 2 …); design gaps 1 observed`.
The re-plans and the route back to Architect came after the first tick,
which is where they happen. Under the first-tick rule the inferred window
ends almost as soon as it starts.

Measured 2026-10-18 over the 1086 refs this clone holds (refs/stash
excluded), on the 4 runs that have an observed I: the observed implement
commit is, in every one, the first commit after D at which every row is
checked. So that commit is what an inferred I has to find.

## Decision

The inferred implement boundary is the earliest commit after D, in walk
order, whose breakdown version has at least one row and checks every row.
Rows are read with `knowledge_plane.breakdown_rows`, as before. Rows that
are later unchecked, or rows added unchecked later, do not move I: the
boundary is the first time Implement was complete, just as the observed
boundary is the earliest implement commit. A run whose breakdown is never
fully checked on the refs read has no implement boundary. Its re-plan
signal is unmeasurable with the reason `no implement boundary: no later
commit checks every row`, and so is its design-gap signal when D is
observed. That reason replaces `no implement boundary: no later commit
checks a row`. The tool's rule sentence names the inferred rule, so each
record shows which rule it was taken under.

The first record stays as written. A second dated record is taken under
this rule. The two are compared run by run, never as one series.

## Rejected alternatives

- **Keep the first tick (Owner decision 3 as written).** The window it
  measures is near-empty by construction, as this run's own row shows.
- **The latest commit that checks a row, when no version checks every
  row.** Implement is not finished on those refs, so any end chosen is a
  guess. Unmeasurable is the fail-closed reading. It costs 1 run today
  (faster-sdlc, with 9 of 11 rows checked in the working tree), and that
  run would read `re-plan 0 of 11` under the latest tick.
- **The commit after which every row stays checked.** Across every ref,
  later waves add unchecked rows (fail-closed-roll-up goes from 7 of 7 to
  7 of 12). The window would then stretch over the next wave's plan. On
  5 inferred runs I would move onto a later wave, or be lost where the
  last wave is unfinished. The first time every row is checked matches
  the observed I on all 4 runs that have one.
- **The last commit before Verify's artifact** (Review's example). The
  walk reads only `breakdown.md` and `architecture.md`, so this widens it
  to a third artifact. On the 4 observed runs the all-checked commit
  already equals the implement commit.

## Consequences

- ADR-0109's claim that the two windows agree is retracted. It held only
  for keys at the first tick, and it was false for this run.
- Accepted behaviour changes, from running both rules over the 36 runs
  in this clone on 2026-10-18. 24 runs change their inferred I.
  - 22 move I later with the same re-plan figures.
  - first-live-dispatch goes from `re-plan 1 of 8 (added 1, …)` to
    `re-plan 4 of 8 (added 3, dropped 0, split 1, merged 0; …)`.
  - faster-sdlc becomes re-plan unmeasurable.
  - On today's refs the inferred re-plan aggregate goes from 7/219 over
    26 runs to 10/208 over 25 (the first record, on earlier refs, reads
    7/232 over 27). Design gaps and review-traced do not change. No
    observed figure changes.
- The widened window adds only 3 re-plans. A low inferred re-plan rate
  was therefore mostly not the window's fault, and #987 can read the new
  figure as a measurement rather than as an artifact of the rule.
- A record taken under ADR-0109's first-tick rule and one taken under
  this rule are not comparable for inferred rows. Each record carries its
  rule sentence and a ref-tip digest, so a reader can tell them apart.
