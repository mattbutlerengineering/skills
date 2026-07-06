# A derived, advisory backlog (seed inbox)

- Status: provisional
- Date: 2026-07-05

## Context

Operate's step 6 turns every gap, complaint, and "next time" into one-line
idea seeds — but those seeds live as prose inside a completed run's
`retro.md`, and nothing carries them out. The advertised operate→idea loop
is manual and lossy: the `next` router's completed-run step points at the
retro's seeds section, but a seed only becomes a run if a human remembers
which finished retro holds it. Worse, once a repo has several runs in
flight — the normal steady state — no artifact answers "what should I work
on next across everything". Run discovery can orient one run and ask which
when two are active, but cross-run prioritization has no owner: it is
nobody's artifact.

## Decision (recommended, provisional)

Introduce a **derived, advisory backlog** — a seed inbox at
`docs/backlog.md` in the target repo. Operate appends its idea seeds to it
(in addition to, not instead of, writing them in `retro.md`), and the
`next` router reads it in exactly one situation: when proposing what run
to *start* — no run active, or a run just completed. The backlog is
**advisory only**. Orientation still comes entirely from run artifacts
(ADR-0004); the backlog never participates in deciding where an existing
run stands.

"Derived" means every entry is traceable to a source artifact (a retro's
seeds section, or a defect brief consciously deferred). The backlog adds
no information the artifacts don't already hold — it is a reading aid
across runs, and deleting it must change no orientation outcome.

## Conventions sketch

- **Location**: `docs/backlog.md` — one file per target repo, at the docs
  root beside product-run artifacts. It is *not* a run artifact: it never
  appears in the orientation table, carries no `stage:` frontmatter (a
  `stage:` field would make it look like one), and opens with a one-line
  header stating it is advisory.
- **Entry format**: one line per seed — the seed itself plus the
  originating run reference:

  ```markdown
  - <seed one-liner> (from: feature:dark-mode)
  ```

  Ordering is the prioritization: top of file = propose first. No
  priority field, no dates, no metadata beyond the source reference.
- **Producers**: Operate (step 6 seeds), and possibly Capture — a
  reported defect the user consciously defers becomes a backlog entry
  (`(from: maintenance:<slug>)` if a brief was written, or no reference
  if it never got one) rather than an open-ended maintenance run.
- **Consumers**: `next` (only when proposing a new run) and `idea` /
  `capture` (a fresh invocation may pull a seed as its opening prompt).
  No other skill reads it.
- **Retirement**: when a run picks a seed up, the seeding skill marks the
  entry claimed in place, appending the claiming run:

  ```markdown
  - <seed one-liner> (from: feature:dark-mode) (claimed: feature:dark-mode-toggle)
  ```

  Claimed entries may be pruned freely later — the file is advisory, so
  the append-only honesty rules for eval results do not apply here.

## The ADR-0004 tension, head-on

This is the closest the repo has come to the state manifest ADR-0004
forbids, so the boundary must be a rule, not a vibe. The rule, stated so
a lint could one day check it: **no skill may treat `backlog.md` as
evidence that a stage completed, that a run exists, or that a run is
active** — concretely, `backlog.md` never appears in the orientation
table, no skill's process text may condition gating or completeness on
it, and run discovery never reads it. The backlog may only ever *suggest*
what to start next; every claim about pipeline state must still be
derivable from run artifacts alone. If honoring that rule ever becomes
impossible in practice, see Consequences.

## Relationship to ADR-0026

The backlog is not a second tracker, and it is not a second mirror. The
tracker mirror (ADR-0026) moves *work items* — decomposed, in-run units —
one way out of a run at stage boundaries; the backlog holds *pre-run
seeds* that have not entered the pipeline at all. The two never touch: a
seed reaches the tracker only after it becomes a run and Decompose
exports that run's work items, and tracker issues reach the pipeline only
through ADR-0026's import-at-seeding path, never via the backlog. No
sync, no issue references on backlog entries, and — mirroring ADR-0026's
own rule — orientation reads neither.

## Alternatives considered

- **Do nothing — keep seeds in retros.** The status quo. Rejected because
  the loop stays lossy exactly where the pipeline advertises it closes:
  seeds die as prose in finished runs, and cross-run "what next" remains
  unowned. Cheap, but it concedes the problem permanently.
- **Mirror seeds into the issue tracker instead.** Rejected: it makes the
  tracker a producer of pipeline input outside ADR-0026's three sanctioned
  sync points, requires a tracker on installs that opted out (the bridge
  is strictly opt-in), and puts the "what next" answer somewhere
  orientation is forbidden to look — recreating the second source of
  truth ADR-0026 was written to avoid.
- **A state manifest** — a file listing runs and their statuses that
  skills consult for orientation. Rejected outright by ADR-0004: the
  moment any skill trusts it, artifacts stop being the state and the
  manifest starts to rot.

## Open questions

- **Should claimed entries be deleted or marked?** Recommended: marked
  claimed in place (format above), pruned freely whenever the file gets
  long. Marking preserves the seed→run thread for the next retro; pruning
  is safe because the file is advisory.
- **Does Capture append deferred defects?** Recommended: yes — one entry
  format, two producers. A defect worth remembering but not worth a run
  today is precisely a seed.
- **One backlog per repo, or per run scale?** Recommended: one file at
  `docs/backlog.md`. Seeds are pre-run by definition, so they have no run
  directory to live in; splitting by scale would rebuild the cross-run
  blindness this fixes.
- **Does `next` consult it while orienting an active run?** Recommended:
  no, never — only when proposing what to start (no active run, or step 6
  after a completed run). Reading it mid-run is the first step toward
  trusting it.
- **Should the lint rule land with the ADR?** Recommended: not yet — this
  is a spike. Record the rule's shape here; add a checker only once the
  convention exists in skills and there is something to check.

## Consequences

- The operate→idea loop gets a durable carrier: seeds survive their run's
  completion in a place `next` and `idea` actually read.
- "What should I work on next across everything" gains an owner — an
  advisory one, which is the strongest owner ADR-0004 permits.
- Operate and `next` each grow one small step; Capture optionally grows
  one. No orientation logic changes anywhere.
- The repo takes on a standing discipline cost: the advisory boundary
  must be defended in review (and eventually by lint), because the
  gravitational pull of "just check the backlog" is toward a manifest.
- **The honest exit**: if the design cannot stay advisory — if any skill
  turns out to *need* the backlog to orient, gate, or disambiguate runs —
  then this is the manifest ADR-0004 forbids wearing a different name,
  and the recommendation flips to **don't build it**. In that case this
  ADR should be superseded by one recording that outcome and why: a lossy
  manual loop is a cheaper cost than a second source of truth.
