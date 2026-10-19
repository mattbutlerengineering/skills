---
stage: idea
run: feature:decompose-outcome-signals
date: 2026-10-18
origin: "Issue #986 (Decompose learning loop, step 1 of 4), chosen by the Owner as the first of five autorun answers. Not a backlog seed: docs/backlog.md has no matching line, so no seed claim is written. Interview answered from autorun-brief.md in this directory (five Owner answers, the rest the orchestrator's reading); no live interview held."
assumptions:
  - "In-flight check ran, nothing matches: `gh pr list --state open` returned one open PR, #1037 (docs(verify): skill body cites ADR-0108), which is unrelated; a search of open PRs for decompose / re-plan / outcome found nothing more; `git branch -a` showed feat/decompose-placeholder-scan (2a07ca1, a placeholder and name-drift check on the Decompose draft) and chore/retire-plans-ignore-beads, neither of which measures outcome signals; the open issues matching decompose are #986 itself and its siblings #987, #988 and #989, which are later steps of the same series."
  - "Outside corroboration (the optional last30days check on why-now and evidence) was not run: the skill says never to run it unasked, and no human was present to ask. The interview alone is a complete result."
---

# Idea: Decompose outcome signals from git history

## Problem

The Owner tunes the Decompose skill without knowing whether its plans
hold up. Nobody can say how often a breakdown gets re-planned during
Implement, how often Decompose had to send a design gap back to
Architect, or which breakdown items the review findings land on. So
changes to the skill get judged by feel. The signals already exist, in
git history and in `review.md` files, but nothing reads them.

## Who has it

- **The Owner**, who changes the Decompose skill and has no baseline to
  compare a change against.
- **Every later step of the Decompose learning loop**: #987 (cost
  metering and S/M/L calibration), #988 (the ranked lessons file) and
  #989 (the Decompose eval suite and prompt optimization). Each of them
  calibrates against these numbers, so none of their effects can be
  measured until this step exists.

How they cope today: they don't. The signals sit unread.

## Why now

The 2026-10-16 deep-research pass ranked an estimate-versus-actual
feedback loop as the best-evidenced way to improve planning. But the cost
data that loop needs is almost absent: #987 reports that 7 of 184 rows in
`docs/factory/costs.jsonl` record a cost. Git signals cost nothing to
collect, so they are the first feedback loop this repo can actually run.

## Evidence

- **Observed:** the pr-body-preflight run routed two design gaps from
  Decompose back to Architect. Commit 772e374 (2026-10-16,
  `docs(pr-body-preflight): decompose — … two design gaps routed to
  Architect`) is followed by 766633c (2026-10-16, `docs(pr-body-preflight):
  architect — …`).
- **Measured 2026-10-18 (this stage, `git ls-files`):** 47 tracked
  `breakdown.md` files, 12 of them test or eval fixtures, which leaves 35
  run directories with a breakdown.
- **Measured 2026-10-18 (this stage, `git log --all` over the refs this
  clone holds):** commits with a strict `docs(<slug>): decompose — …`
  subject exist for 3 runs: fail-closed-roll-up, pr-body-preflight and
  reviewer-token. Strict `architect — …` subjects exist for the same
  three, and strict `implement — …` subjects for six runs. The clone
  holds no `refs/pull/*/head` refs, while `git ls-remote` lists 488 on
  origin. So most boundary commits that squash merges removed from main
  may survive only on refs this clone has not fetched.
- **Discrepancy, recorded rather than resolved:** the brief's own count
  (the orchestrator's, PR head refs included) names factory,
  fail-closed-roll-up and pr-body-preflight. The factory run's decompose
  commit (0661682, `docs(factory): decompose PRD-0001 into …`) does not
  match the strict subject shape, and reviewer-token's does. Which runs
  count as "observed" depends on how strict the subject match is, and
  that is itself one of the unknowns below.
- **External reference (published, not ours):** about 10% of items are
  re-estimated after planning in open-source agile projects, 3–17% by
  project (Empirical Software Engineering, doi
  10.1007/s10664-022-10192-9), as cited in #986.

## Solution hunch

A root, stdlib-only Python tool that reads git through the `cli.py`
conventions. For each run directory with a breakdown, it would:

1. find the decompose and implement boundaries;
2. diff the breakdown's item rows between those two boundaries;
3. look for architect boundaries that come after the decompose one;
4. match `review.md` findings against item ids.

It prints per-run rows and an aggregate in the repo's problem-string /
count contract. Where to get boundaries is the Owner's decision 3: use
the boundary commit subjects when a run has them. Otherwise fall back to
the commit that first added `breakdown.md` as an inferred decompose
boundary, and the first checkbox tick as an inferred implement boundary.
Every boundary is labelled observed or inferred, and the aggregate
reports the two populations separately as well as combined. A run with
neither kind of boundary is named as unmeasurable, with a reason, and is
never counted as zero. The tool reads only the refs the clone already
has and says which ones it read. Fetching PR head refs is a documented
manual step.

## Success in one sentence

One command prints re-plan, design-gap and review-traced counts for
every measurable run and in aggregate, with each boundary labelled
observed or inferred, and the first real numbers for this repo are
recorded append-only by the tool's own output, never typed by hand.

## Unknowns & risks

- **Squashed history.** Main is squash-merged, so boundary commits
  survive only on run branches and PR head refs, and those can be pruned.
  This clone holds none of the 488 PR head refs. A tool that honestly
  measures 3 runs is worthless as a baseline.
- **Boundary inference can be wrong.** Most runs predate the
  commit-subject convention, so the fallback boundaries are guesses. An
  inferred number shown as observed would make the measurement a lie.
- **Subject-match strictness.** The factory and reviewer-token cases
  above show that a loose match and a strict match give different
  observed populations. Someone has to choose which one counts.
- **Breakdown row identity.** A split or a merge can only be detected if
  items carry stable ids (WO ids, row numbers, titles). The shape of
  breakdown rows has drifted across runs.
- **Review findings rarely name an item.** The third signal may be near
  zero for honest reasons, and a zero must not read as "no findings".
