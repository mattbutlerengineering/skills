---
stage: idea
run: feature:size-band-calibration
date: 2026-10-20
origin: "Issue #987 (Decompose learning loop, step 2 of 4), chosen by the Owner in session as the first of the six remaining real issues. Not a backlog seed: docs/backlog.md has no matching line, so no seed claim is written. Interview answered from autorun-brief.md in this directory (three Owner answers, the rest the orchestrator's reading); no live interview held."
assumptions:
  - "In-flight check ran, nothing matches: `gh pr list --state open` returned [] (no open PRs); a search of open PRs for size band / calibration returned nothing; open issues matching are #987 itself and its siblings #988 and #989 (later steps of the same series); local and remote branches with cost or calibrate in the name (feat/799-per-step-actuals-calibrate, fix/940-calibrate-warns-below-the-floor, fix/936-review-weight-by-band, fix/937-runner-lost-is-metered, fix/815-owner-session-marker-cost, fix/736-cost-ledger-guarded-write, fix/cost-runs-and-scorecard-history, routine/2026-10-12-retry-up-top-band) are all behind squash merges already on main (#971, #967, #953 and earlier) and none holds size-band interval work."
  - "Adjacent shipped work, recorded rather than treated as a match: `conductor_calibrate` (`conductor.py calibrate`) already calibrates per-step weights (plan units) from closed Conductor batch ledgers. It does not compute a per-size-band error interval and does not guard against size inflation, so this run is not a duplicate; whether to reuse its ledger walk is for Architect."
  - "Outside corroboration (the optional last30days check on why-now and evidence) was not run: the skill says never to run it unasked, and no human was present to ask. The interview alone is a complete result."
  - "The brief's Owner answer 2 (exclude unmetered owner sessions, report the count) is taken as binding scope for this stage; the brief's other idea-stage inputs are the orchestrator's reading and are recorded here as hunches and anecdote, not as Owner decisions."
---

# Idea: Calibrate S/M/L size bands from past error

## Problem

The Owner sizes work items S, M or L without knowing how far off the bands
run. Nobody can say what an M actually costs or how often one overruns, so
a size is a feel, and a miss is accepted rather than measured. Judged
effort ranges are known to be overconfident, and nothing here corrects for
it.

## Who has it

- **The Owner**, and every Decompose run: they size by feel and accept
  the miss.
- **Steps 3 and 4 of the loop**: #988 (ranked lessons file) and #989
  (Decompose eval suite and prompt optimization) calibrate against what
  this step measures, so neither can show an effect until it exists.

How they cope today: they don't measure. They size, build, and move on.

## Why now

#986 shipped as #1040 (`decompose_signals.py`): the re-plan rate now
exists, and it is the number that keeps this loop honest, because size
inflation would show up there and in cost. The cost half is the blocker:
the ledger holds almost no usable cost data yet (see Evidence), so metering
has to come first or calibration has nothing to read.

## Evidence

- **Measured 2026-10-16 (orchestrator, cited from #987, not re-measured at
  this stage):** 7 of 184 rows in `docs/factory/costs.jsonl` record a
  cost; 145 are `owner-session:unmetered`; 2 rows join to a breakdown
  row's `size:` band (both S); `origin/main` holds 0 Conductor batch
  ledgers.
- **Anecdote, labelled:** the Owner's experience that sizes are felt, not
  measured. No tracked miss history exists to cite.
- **External reference (published, not ours):** estimation-literature
  evidence that effort intervals are overconfident (Jorgensen, Teigen and
  Molokken, JSS 2004), as cited in #987. Anecdote at literature scale, not
  proof about this repo.
- **Existing seed, adjacent:** docs/backlog.md already carries a
  step-weight seed (re-weight `DEFAULT_STEP_WEIGHTS` once each step has
  n >= 5), the origin of the n >= 5 minimum the brief names.

## Solution hunch

A hunch, not a design. Two parts, in order:

1. **Meter first.** Make work-item cost land in the ledger with a joinable
   size band; Conductor batches are the expected source.
2. **Then calibrate.** A stdlib-only root tool, like `decompose_signals.py`,
   joins metered ledger rows to a breakdown row's `size:` band and prints,
   per band, a Balanced Relative Error percentile interval from past error
   (it needs only sorting). Below the minimum n (the backlog seed uses 5)
   it prints a refusal that says why, not a number. It reports band misses
   next to cost and the re-plan rate from `decompose_signals.py`, so
   inflating sizes shows up as cost.

Owner decision, in scope: unmetered owner sessions are excluded, and the
tool prints how many rows it excluded and why. No cost is ever estimated
for an unmetered session.

## Success in one sentence

The tool prints a size band's interval only when that band's n meets the
minimum and otherwise says why not, with every number computed from ledger
rows and none typed by hand.

## Unknowns & risks

- **Too few metered rows may ever exist.** Today 2 rows join, both S; M and
  L have none. If metering does not produce volume, the tool may refuse
  everywhere indefinitely, which is honest but gives steps 3 and 4 nothing.
- **A hand-set number creeping in** defeats the eval-honesty rule; the
  acceptance bar is that no calibration number is ever written by hand.
- **Sizes inflate** once they are measured; the guard is reporting misses
  beside cost and re-plan rate, and whether that guard is enough is
  unproven.
- **Overlap with `conductor_calibrate`.** Both read cost ledgers; where the
  seam sits, and whether the join and the closed-batch-ledger walk are
  reused, is unresolved and goes to Architect.
- **The join key.** Whether a ledger row can carry a size band at write
  time, or must be joined later through breakdown rows whose shape has
  drifted, is unknown.
- **Scope edge.** Transcript-based metering of owner sessions and any
  Decompose prompt change are out (#988, #989); excluding unmetered
  sessions means owner-session work stays invisible to calibration.
