---
stage: idea
run: feature:review-interface-pass
date: 2026-11-04
assumptions:
  - "Ambition rung: the autorun brief names no pick, so the skill's recommended default, Showstopper, is taken."
  - "In-flight check: the orchestrator ran the guard on 2026-11-04 before this stage (no open PR, unmerged branch or worktree does this seed's work; the only open PR is #1153, a release bump). This stage did not rerun it."
  - "The larger rung, Moonshot, is seeded with text written by this stage; the brief supplies none."
  - "The four Showstopper tests are answered from the brief's Idea inputs, not from a run on a real UI diff; none exists."
---

# Idea: An Interface domain pass for review

> An Interface domain pass for `review`.

Origin: the seed at `docs/backlog.md` line 139, claimed in place as
`(claimed: feature:review-interface-pass)`. Source of the method:
`docs/research/jakubkrehel-skills-2026-10-31.md`, shortlist row 1.

In-flight check: ran, clean. The orchestrator ran the guard on 2026-11-04
and found no open pull request, unmerged branch or worktree doing this
seed's work; the only open PR is #1153, a release bump. This stage took
that result and did not run it again.

## Problem

When a pipeline run changes interface code, nothing in `review` looks at
it. No domain pass covers UI paths and the skill never mentions
accessibility. A deleted `aria-label` or focus style is invisible in the
post-change state, so a reader of the changed file sees nothing wrong and
the loss ships.

## Who has it

Adopters whose repos have a UI. They cope with `polish` (a draft skill,
run on demand against a rendered surface, not against the diff) or with
nothing. `review`'s domain passes cover payments, migrations and
dependencies only.

## Why now

The research note of 2026-10-31 found that the domain-pass contract ("Read
the whole changed file", "Evidence or silence") already fits this work, so
the cost is one table row and one reference, with no description change.

## Evidence

- An external practitioner's method: jakubkrehel/skills' `interface-review`
  reads the removed side of a diff, looks for an equivalent replacement and
  gives each finding a status by cause. It publishes no evals.
- A coverage gap, observed in this repo: `domain-reviewers.md` has three
  rows, none for interface paths.
- Not evidence: no adopter UI diff was available to test on (the research
  note's "Couldn't verify"). The pass is unmeasured on real diffs.

## Ambition rung

Chosen: Showstopper (the recommended default; the brief names no pick), in
the seed's words: "reads the removed side of every hunk for deleted
accessibility and rendering signals ... clears the equivalent replacements
before reporting, and statuses each finding by cause".
Not taken: Solid: the row and a reference that report every deleted
signal, with no replacement check, so a refactor that moves a focus style
is reported as a loss (this rung is never seeded); Moonshot: render the
changed interface before and after in a browser and compare the
accessibility tree and focus order (seeded).
Demo: pass — a review of a diff that deletes an `aria-label` reports it,
and one that swaps `outline` for a `box-shadow` focus ring on the same
selector reports nothing; both outcomes are read in the review text.
Removes a step: pass — the reviewer no longer has to think to read the
removed side of a UI hunk, and the author no longer has to defend a
refactor that kept the signal.
Only this product: pass — the pass sits in the pipeline's review of the
diff, where the removed side is in hand; `polish` reads a rendered
surface and never sees what was deleted.
Achievable: pass — one row and one reference, no script and no
description change; riskiest piece is the replacement-clearing rule (what
counts as an equivalent); spike of about two days: write the reference,
then walk it by hand over two or three fixture UI diffs (a bare deletion,
an `outline` to `box-shadow` swap, a token to literal swap) and see
whether the verdicts match the success statement.

## The demo

Before: a diff drops `aria-label="Close"` from an icon button and `review`
says nothing, because the changed file reads fine. After: `review` lists a
finding for that line, and the same review stays silent on a second hunk
that replaces `outline: none` with a `box-shadow` focus ring on the same
selector.

## Riskiest piece + spike

The replacement-clearing rule: deciding that a removed signal has an
equivalent on the added side without clearing a real loss. Spike of about
two days: draft the reference, then hand-walk it over fixture diffs,
including at least one where the replacement is on another selector and
must not clear. No model run is involved.

## Cheapest kill test

Take three UI diffs by hand: a bare `aria-label` deletion, an `outline` to
`box-shadow` swap on the same selector, and the same swap on a different
selector. If the drafted rule cannot tell the first and third (report)
from the second (silent) in plain words, the idea fails at this scale.

## Solution hunch

One new row in `skills/review/references/domain-reviewers.md`, selected by
UI paths, and one new reference restated in this repo's words. The
reference reads the removed side of every hunk for deleted signals
(`aria-label`, `alt=`, `:focus-visible`/`outline`, `tabindex`,
`prefers-reduced-motion`, logical properties, `lang=`/`dir=`, a token
swapped for a literal), clears equivalent replacements before reporting
and gives each finding a status by cause. A credit line goes in the skill
and in the README credits paragraph. The source is MIT and nothing is
copied, so `NOTICE` does not change.

## Success in one sentence

A review of a UI diff that deletes an `aria-label` with no replacement
reports it, one that swaps `outline` for a `box-shadow` focus ring on the
same selector does not, the pass is not selected on a diff with no UI
paths, and the skill's description is unchanged.

## Unknowns & risks

- How broad the selection globs should be: "templates" is vague, and the
  payments row is broad on purpose, so this row needs the same care.
- False positives that teach readers to skip the pass.
- Where the line falls between `polish` (live surfaces) and this pass (the
  diff). Another run owns any `polish` change.
- How findings get a status by cause (introduced, regression,
  pre-existing) inside `review`'s existing severity model.
- No adopter UI diff exists to test on, so the pass stays unmeasured on
  real diffs, and the source publishes no evals to lean on.
