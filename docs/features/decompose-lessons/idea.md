---
stage: idea
run: feature:decompose-lessons
date: 2026-10-20
origin: "Issue #988 (Decompose learning loop, step 3 of 4), driven in session by the Owner's answer '#987 first, then carry on'. Not a backlog seed: docs/backlog.md has no matching line, so no seed claim is written. Interview answered from autorun-brief.md in this directory (three Owner answers, the rest the orchestrator's reading); no live interview held."
assumptions:
  - "In-flight check ran, nothing matches: `gh pr list --state open` returned one PR, #1049 (docs(ship): record the #1040 and #1047 releases, branch docs/ship-writeback-986-987), a release.md write-back for steps 1 and 2 that builds no lessons file. Open issues matching are #988 itself and its sibling #989 (step 4); #1048 is the write-back issue #1049 closes. Branches with lessons or decompose in the name: feat/decompose-outcome-signals (merged as #1040), feat/decompose-placeholder-scan (a placeholder and drifting-name check on the draft, no lessons file), feat/kb-weknora-lessons (stale, last merged against plugin 0.12.x, a knowledge-base change), docs/decompose-outcome-signals-released, and this run's own feat/decompose-lessons. None holds lessons-file work."
  - "Adjacent shipped work, recorded rather than treated as a match: decompose_signals.py (#1040) measures re-plan, design-gap and review-traced signals per run from git history; it keeps no lessons and feeds nothing back. size_band_calibration.py (#1047) prints per-band cost error only above its n >= 5 floor; it too feeds nothing back. The knowledge-base skill and docs/kb hold hand-reviewed, non-inferable project facts promoted by a human; they are neither derived from outcome signals nor voted and decayed, and Decompose does not read them as lessons. Not a duplicate of any of the three; whether lesson derivation reuses decompose_signals.py's records through an import is for Architect."
  - "Outside corroboration (the optional last30days check on why-now and evidence) was not run: the skill says never to run it unasked, and no human was present to ask. The interview alone is a complete result."
  - "The brief's Owner answer 2 (pair source is the three measured outcome signals only; band-miss pairs and retro prose out of scope) is taken as binding scope for this stage. The brief's other idea-stage inputs are the orchestrator's reading, recorded here as hunches and anecdote, not as Owner decisions."
  - "No interview question this stage offered named options with a recommended default that the brief left open, so no skill default was taken. No evidentiary question was left unanswered by the brief, so nothing was surfaced."
---

# Idea: An ExpeL-style ranked lessons file for Decompose

## Problem

Decompose drafts each breakdown from scratch. What past breakdowns got
wrong, a re-plan, a design gap sent back to Architect, a review finding
that traces to an item, is measured now but never reaches the next draft.
The same mistakes can be made again, and the only fix today is someone
editing the skill text by hand.

## Who has it

- **The Owner**, and every Decompose run: they rely on memory and on the
  skill text, which changes only by hand.
- **Step 4** (#989, Decompose eval suite and prompt optimization): it reads
  this tool's output, either using the numbers or failing on them, so it
  has nothing to measure until this exists.

## Why now

#986 shipped as #1040 (`decompose_signals.py`), so outcomes are measurable,
and #987 shipped as #1047 (`size_band_calibration.py`), so cost has a band.
This step is the first consumer that feeds a measurement back into the
draft.

## Evidence

- **Anecdote, labelled:** ExpeL (Zhao et al., AAAI 2024, arXiv 2308.10144)
  reports 39% on HotpotQA against ReAct's 28%, and 29% when raw
  self-reflections feed the list, as cited in #988. QA and agent
  benchmarks, not software decomposition.
- **None for the target:** no verified source shows this improves
  decomposition, and #988 says so. No count of how many runs yield a
  contrast pair has been taken at this stage.
- **Existing mechanism, adjacent:** the three outcome signals exist and are
  git-derived (#1040); the repo has no lessons mechanism.

## Solution hunch

A hunch, not a design. A stdlib-only root tool, like `decompose_signals.py`,
that:

- derives contrast pairs (a run that hit a signal against a run of the same
  kind that did not) from `decompose_signals.py`'s records only;
- keeps a flat lessons file, one lesson per line, each with an importance
  count and the source runs it cites; a new lesson starts at 2, later
  outcomes UPVOTE or DOWNVOTE it, and it is removed at 0, so the file
  forgets (ADD, EDIT, UPVOTE, DOWNVOTE);
- never takes retro prose or a hand-written lesson as input.

Plus a Decompose skill step that reads the file at draft time. The skill
change rides the wave's release PR; this branch never bumps
`.claude-plugin/plugin.json`'s version (ADR-0095).

Owner decision, in scope: pairs come from re-plan, design-gap and review
signals only. Band-miss pairs wait until a band clears the n >= 5 floor in
`size_band_calibration.py`; the PRD records that gap.

## Success in one sentence

A lesson exists only with source runs cited, decays to removal at 0, and
the Decompose skill reads the file at draft time.

## Unknowns & risks

- **Too few runs may yield any contrast pair.** If the history holds none,
  the file stays empty, which is honest but gives step 4 nothing.
- **Lessons may be noise that raises the re-plan rate.** The loop is an
  experiment, measured against the re-plan rate; whether that measure can
  detect harm at this run count is unproven.
- **A hand-written lesson creeping in** defeats the "every lesson cites its
  runs" rule; the acceptance bar is that no lesson exists without a source.
- **What counts as "a run of the same kind"** for a contrast pair is
  undefined; the choice is Architect's, and a bad one produces false
  contrasts.
- **Overlap with `decompose_signals.py`.** Whether pair derivation imports
  its records or re-walks git, and whether this earns a new shared module
  under the seam rule (multiple real callers and observed divergence), is
  unresolved.
- **Scope edge.** Excluding band-miss pairs leaves cost-based failures
  invisible to the lessons until a band clears the floor.
