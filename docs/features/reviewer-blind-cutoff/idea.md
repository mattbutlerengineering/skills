---
stage: idea
run: feature:reviewer-blind-cutoff
date: 2026-11-04
origin: docs/backlog.md seed "Withhold the pass cutoff from the implement-queue reviewer" (from: session:2026-10-31), claimed as (claimed: feature:reviewer-blind-cutoff)
in-flight-check: ran 2026-11-04 (by the orchestrator, before this stage) and found nothing matching; no open PR, unmerged branch or worktree does this seed's work, and the only open PR is #1153, a release bump
assumptions:
  - "The brief does not state an ambition-rung pick. The skill's recommended default is Showstopper, so Showstopper was taken as the starting pick; it then failed test 2, was re-scoped once and still failed, so per the skill Solid is the recorded pick and the demoted Showstopper is seeded."
  - "The brief's Idea inputs are the orchestrator's reading of the seed and the research note, not the Owner's words; the quoted framing below is the seed's own sentence."
  - "PR #927 and its 'score 6' are taken from the brief; this stage did not re-derive the 150-PR scan. `gh pr view 927` returns state MERGED, title 'feat(factory): hourly self-merging improvement routine'."
  - "The Idea inputs call the rubric bands a possible leak; the contract's rubric table was read at lines 38 to 52 and the 7 and 5 to 6 band edges do coincide with the 7 or more passes line."
---

# Idea: Withhold the pass cutoff from the implement-queue reviewer

> Withhold the pass cutoff from the implement-queue reviewer: `reviewer-contract.md:31` tells the scorer "7 or more passes, 6 or less flags" and lets it return its own `verdict`; have the orchestrator derive the verdict from the score instead, and post the score in the verdict comment so a clustering-at-7 check becomes possible.

## Problem

The Owner lets the implement-queue reviewer's verdict merge pull requests
unattended (`merge: auto` in `.claude/implement-queue.md`; ADR-0087,
ADR-0096). That reviewer is told where the line is and returns its own
pass or flag. A judge that knows the line can score to it. And the
scores are never posted, so nobody can tell whether it does.

## Who has it

The Owner, and the two routines that merge on this verdict:
`factory-merge-train` (every 4 hours) and `factory-hourly-improvement`
(hourly). They cope today by trusting the verdict as returned. Only one
reviewer score is findable in the last 150 PRs (PR #927, "score 6").

## Why now

Both routines have auto-merged on this verdict several times a day since
2026-10-15, and the research note dated 2026-10-31
(`docs/research/desloppify-2026-10-31.md`, shortlist row 2) identified
the anchor.

## Evidence

- Anecdote, from the research note: desloppify redacts its target score
  from the review packet and flags scores that land on it. That was read
  from its code; nothing shows the redaction works.
- Here, no anchoring incident is on record. The evidence is the absence
  of scores: one findable in 150 PRs, which is why posting scores comes
  first.
- Label: prevention plus making the problem measurable. It is not a fix
  for an observed failure.

## Ambition rung

Chosen: Solid, in the user's words: "have the orchestrator derive the verdict from the score instead, and post the score in the verdict comment". The pick was not stated in the brief; Showstopper (the default) was tried, failed test 2 twice, and Solid is the fallback the skill prescribes.
Not taken: Showstopper: a stdlib check that reads the posted scores and flags clustering just above the threshold; Moonshot: a calibration harness scoring labelled diffs blind on a schedule
Demo: pass — a verdict comment on a PR shows the score and the verdict derived from it, which a person can read without running anything.
Removes a step: fail — it adds a posted field and moves one derivation; no step a person or routine performs today disappears. Re-scoped once to "nobody has to take the reviewer's pass on trust", but that needs the clustering check, which the brief puts out of scope, so it still fails.
Only this product: pass — the verdict is the auto-merge gate of this plugin's own queue, and only it holds the scores and the threshold.
Achievable: pass — riskiest piece is that readers of the `verdict` field (orchestrator prose, any parser or journal code, the merge-train routine doc, tests) break when the field moves; a two-day spike is a grep and a read of every consumer, then one test of the derivation.

The Showstopper and the Moonshot are seeded in `docs/backlog.md` (the clustering check is named out of scope by the brief and "worth seeding once scores exist").

## The demo

None — Solid chosen. (For the record, the Solid moment: a PR's verdict comment reads "score 7, pass", and the reviewer's own prompt names no threshold.)

## Riskiest piece + spike

Every reader of the reviewer's `verdict` field, which must be found before the shape changes: `skills/implement-queue/SKILL.md` (lines 177 and 217 mention the verdict), the contract, any tool or test that parses reviewer output, and the routine docs. Spike, about two days: list all readers with grep across `skills/`, `docs/`, tools and tests; write the derivation as one function with its test; confirm no reader still takes `verdict` from the reviewer. The threshold must have one owner, which `one_owner.py` can check.

## Cheapest kill test

Read the contract and ask whether the rubric bands (lines 38 to 52) still imply the line: 7 to 8 is "minor nits only" and 5 to 6 is "a non-trivial issue", so a reader can place the cutoff between them without being told. If the bands leak the line as clearly as line 31 does, withholding the number buys little and the change stands only on posting scores. That does not kill the idea, since measurability is the point, but it changes the claim.

## Solution hunch

Remove the cutoff from what the reviewer reads. The orchestrator computes pass or flag from `score` against a threshold that it alone owns, in one place. Every verdict comment posts the score. A hunch, not a design.

## Success in one sentence

The reviewer prompt names no pass threshold, the verdict is derived from the score in one place, and every future verdict comment carries the score, so clustering can be checked over PRs.

## Unknowns & risks

- Readers of the reviewer's `verdict` field are not yet enumerated; the field moving may break the orchestrator prose, parsers, the merge-train routine doc or tests. Find every reader first.
- The threshold must have one owner (`one_owner.py`), not a copy in the skill and another in code.
- The rubric bands may leak the line anyway; Decide whether they do.
- Anchoring may not exist. The change stands on making it measurable, and it is not evidence that it happens.
- Scope: threshold value and rubric scale do not change; the `review` pipeline stage and any live implement-queue run are out.
