---
stage: capture
run: maintenance:seen-before-partner
date: 2026-10-24
re-entry: architect
origin: issue #1069 (filed from docs/fixes/lessons-per-signal-seen/review.md, Major finding 1), scoped by docs/fixes/seen-before-partner/autorun-brief.md
assumptions: ["re-entry: architect. The brief names Architect as the next stage and requires a new provisional ADR superseding ADR-0116's seen-equals-measured rule, so the fix is design-touching; the protocol sends design-touching work to Architect. Not an Owner answer", "Intake is #1069 named by the brief (type:chore, no intake marker), so no intake: field; the issue closes from the PR (Closes #1069)", "In-flight check ran: gh pr list --state open returned one PR, #1073 (docs ship write-back for the lessons-per-signal-seen run, branch chore/lessons-per-signal-seen-released), which does not touch this defect; no remote branch or merged PR matches seen-before-partner or #1069 (#1070 is the merged parent fix): nothing matched", "The next free ADR number is 0117 (docs/adr on origin/main ec8159f ends at 0116; #1073 is docs-only); Architect re-checks at write time", "The on-disk shape question (is the old file loadable with no migration) is left to Architect, which the brief requires to log it; Capture records only that the header entry shape in ADR-0116 is <signal>:<run ref> and the repro shows the shape is not what loses the lesson", "The repro was run in a scratch clone at ec8159f with tests.test_decompose_lessons helpers record/replan and decompose_lessons.treated stubbed, exactly as the issue's script does; the symmetric case uses the same stubs. Not an Owner answer"]
---

# Defect: a hit run seen before its clean partner exists never pairs

## Defect (or Condition)

Observed: `decompose_lessons.update` folds every (signal, run) it measured
into the line-1 `seen` header, whatever the run's count (`_measured`,
decompose_lessons.py:573-576, called from `fold` at :591). `pairs(records,
skip=set(seen))` then skips any hit run whose key is in `seen`
(decompose_lessons.py:385-386). A hit run measured in an `update` where no
clean partner of the same kind and label exists yet is therefore marked
seen without producing a pair. When the clean partner appears in a later
`update`, the hit run is skipped, no contrast pair is derived and the
lesson is never written.

Expected: the lesson a hit run and its clean partner jointly support is
derived once both exist in the measured history, however many `update`s
the two runs arrive across, exactly as one `update` over both derives it.
A run should be folded into `seen` for a signal only once it has been used
(paired as a hit, or voted), not merely measured. This is the same class
as the #1061 per-signal `seen` loss (ADR-0116) with a different cause:
there a signal not yet measurable was folded; here a signal measured but
not yet usable is folded.

## Reproduction / Evidence

Reproduced for real in a scratch clone (`git clone` of this repo, checked
out at origin/main ec8159f, which contains the #1061 test helpers), with
no write to this repo's `docs/factory/decompose-lessons.jsonl`. Script:
`/private/tmp/claude-501/-Users-mbutler-github-skills/2c98a723-2833-4868-8bbf-e4099b478ada/scratchpad/repro_issue.py`
(the issue's script plus a third update and the symmetric case), run as
`cd <scratch clone> && python3 repro_issue.py <scratch clone>`. Runs:
H = `feature:h` replan 2 of 10 observed, MH = `maintenance:m` 6 of 7
inferred, MC = `maintenance:n` 0 of 5 inferred, C = `feature:c` 0 of 8
observed. MH and MC exist only so the file is written at update 1.

Case 1, the issue (hit seen before its clean partner):

```
stage1 (H only): (['decompose-lessons: ADD replan/maintenance/dropped', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
header after 1: {"seen": ["replan:feature:h", "replan:maintenance:m", "replan:maintenance:n"]}
stage2 (H + C): (['decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
stage3 (H + C again): (['decompose-lessons: unchanged'], [])
lesson ids: ['replan/maintenance/dropped']
control (H + C once): (['decompose-lessons: ADD replan/feature/added', 'decompose-lessons: ADD replan/maintenance/dropped', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
```

Stage 2 prints no `ADD replan/feature/added` and the lesson is absent
from the file; the control, one `update` over the same four runs, derives
it. Stage 3 shows the loss is permanent, not deferred: the same input
keeps writing nothing. The header after stage 1 shows the cause:
`replan:feature:h` is seen though H paired with nothing.

Case 2, the symmetric case (clean run seen before any hit exists): does
not lose the lesson.

```
stage1 (C only): (['decompose-lessons: ADD replan/maintenance/dropped', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
header after 1: {"seen": ["replan:feature:c", "replan:maintenance:m", "replan:maintenance:n"]}
stage2 (H + C): (['decompose-lessons: ADD replan/feature/added', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
lesson ids: ['replan/feature/added', 'replan/maintenance/dropped']
header after 2: {"seen": ["replan:feature:c", "replan:feature:h", "replan:maintenance:m", "replan:maintenance:n"]}
```

`replan:feature:c` is in `seen` after stage 1 yet the pair still forms at
stage 2: `pairs` applies `skip` only to the hit run and looks the clean
partner up in the full record list, so a seen clean run still partners.
The asymmetry is by construction, not a second defect; Architect should
keep it true (a clean run seen early must stay usable as a partner).

Unverified, for Architect to check rather than assume: `_ballot` and
`votes` also skip a run whose key is in `seen`, so a clean (or hit) run
folded into `seen` before the lesson it would vote on exists may lose
that vote the same way. The brief's "paired as a hit, or voted" wording
covers it; this stage did not reproduce a lost vote.

## Root-cause hypothesis

Hypothesis (the code reading and the repro agree, but the fix design is
open): `seen` is defined by ADR-0116 as "that signal was measured for the
run when the fold ran, whatever its count", so `_measured` folds a hit run
that `pairs` could not yet use. The run is skipped from then on by the
same set that exists to stop a dropped lesson re-deriving (ADR-0113
Consequences). Candidate fix, from the issue and the brief: fold a run for
a signal only once it was used (paired as a hit, or voted). Open questions
for Architect: whether a measured-but-unused clean run, or a hit run with
no partner, must stay re-derivable without re-deriving a dropped lesson;
and that a second `update` stays idempotent (case 1 stage 3 and the
control must both end `unchanged`, no double vote).

## Blast radius

`decompose_lessons.py` only, a root-only on-demand tool (CLAUDE.md,
"on demand only", free, no network). The lessons file does not exist on
main, so no committed data is wrong. A real `update` run on an existing
ledger silently under-derives: a hit run's lesson is permanently missing
whenever its clean partner (same kind, same hit label) is measured in a
later update than the hit. That is the common order for a new kind or a
new hit label, since the partner needs a clean run of that kind and label.
Pre-existing since ADR-0113 (the seen-on-measure rule predates ADR-0116;
the review confirmed origin/main behaves identically); ADR-0116 kept it.
Severity: low to medium, silent undercount of the Decompose lessons
ledger (ADR-0113), which feeds a human-read lessons list, not a gate.
Scale: small, one module, one provisional ADR.

## Ruled out

- Not introduced by the #1061/ADR-0116 change: review.md, Major finding 1,
  records origin/main behaving identically with the old per-run header.
- Not the header entry shape: the per-signal `<signal>:<run ref>` shape is
  not the cause; the defect is the rule for when an entry is folded.
- Not the symmetric order: case 2 above derives the lesson, so only a hit
  run seen before its partner loses it.
- Not an idempotence bug: stage 3 and the control both end `unchanged` on
  a repeated input.
- Not fixable inside the #1061 PR: the issue and the Owner deferred it,
  and it amends ADR-0116, which needs a new ADR (supersede, never
  rewrite).

## Notes

- Entry depth is Capture then Architect, Decompose, Implement test-first,
  Verify, Review, Ship (brief). No `operate:` section.
- The permanent regression test must not assert a path is "unchanged
  against main" (brief constraint).
- Reproduction evidence above becomes the regression test: update 1 over
  H alone then update 2 over H + C must print `ADD replan/feature/added`
  and match the single-update control; a repeat update must end
  `unchanged`; the clean-first order must keep deriving the lesson.
