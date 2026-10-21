---
stage: prd
run: feature:decompose-lessons
date: 2026-10-20
ux: not-applicable
ux-reason: "CLI text output and skill text only; no screens or flows."
assumptions:
  - "Interview answered from autorun-brief.md in this directory; no live interview held. The brief holds three Owner answers (drive #988 after #987; pair source is re-plan, design-gap and review signals only; prepare-and-stop release). Everything else traces to the brief's sections marked as the orchestrator's reading of issue #988, or to idea.md."
  - "No interview question this stage offered named options with a recommended default that the brief left open, so no skill default was taken. No evidentiary question was left unanswered, so nothing was surfaced."
  - "The brief's ExpeL parameters are taken as requirements: a new lesson starts at importance 2, UPVOTE adds 1, DOWNVOTE subtracts 1, and a lesson at 0 is removed. The step size of 1 per vote is the ExpeL convention and the orchestrator's reading, not an Owner answer; Architect may confirm it."
  - "No PRD id assigned: the prd skill and TEMPLATE.md assign none, and the brief rules out work-order mirroring."
  - "What counts as a run of the same kind for a contrast pair, where the lessons file lives, whether it earns a new shared module, how Decompose reads it, and how the experiment is measured against the re-plan rate are left to Architect as open questions (orchestrator instruction); the brief settles none of them."
  - "The mechanism that applies ADD, EDIT, UPVOTE and DOWNVOTE (which outcome triggers which vote) is left to Architect; this PRD fixes only the observable behaviour of each operation."
---

# PRD: A ranked lessons file for Decompose

## Problem statement

Decompose drafts each breakdown from scratch. What past breakdowns got
wrong (a re-plan, a design gap sent back to Architect, a review finding
that traces to an item) is measured now by `decompose_signals.py` (#1040)
but never reaches the next draft. The only fix today is someone editing
the skill text by hand, so the same mistakes can be made again.

No verified source shows that feeding such lessons back improves software
decomposition (ExpeL, arXiv 2308.10144, reports gains on QA benchmarks
only, as cited in #988). This is an experiment, measured against the
re-plan rate. It may also find too few runs to yield any contrast pair, in
which case the file stays empty. Step 4 (#989) reads this tool's output, so
it has nothing to measure until the tool exists.

## Solution

1. **A lessons file and a tool that maintains it.** A stdlib-only tool
   derives contrast pairs (a run that hit a signal against a run of the
   same kind that did not) from re-plan, design-gap and review signals only,
   and keeps a flat file of lessons, one per line, each with an importance
   count and the source runs it cites. Operations are ADD, EDIT, UPVOTE and
   DOWNVOTE. A new lesson starts at importance 2; a lesson that reaches 0 is
   removed, so the file forgets. A lesson with no source run is refused.
   Retro prose and hand-written lessons are never input.
2. **A Decompose read step.** The Decompose skill reads the file at draft
   time. The skill change rides the wave's release PR; this branch never
   touches `.claude-plugin/plugin.json`'s version (ADR-0095).

Band-miss pairs are out of scope: they wait until a band clears the n >= 5
floor in `size_band_calibration.py` (#1047). Until then, cost-based
failures are invisible to the lessons. That gap is recorded here and not
filled with invented data.

## Actors

- **Owner**: maintains this repo, runs Decompose, and runs the tool to
  update and read the lessons file.
- **Decompose run**: the stage skill drafting a `breakdown.md`; reads the
  lessons file at draft time.
- **Step 4 (#989)**: the later Decompose eval and prompt optimization that
  reads this tool's output as its baseline.
- **Reviewer**: whoever examines the run's PR at the merge gate and judges
  whether a lesson can be trusted.

## User stories

1. As the Owner, I want lessons derived from contrast pairs of re-plan,
   design-gap and review signals, so that what past breakdowns got wrong is
   written down without my hand.
2. As the Owner, I want every lesson to cite the runs it came from, so that
   I can check a lesson against its evidence.
3. As the Owner, I want a lesson with no source run refused, so that a
   hand-written or invented lesson cannot enter the file.
4. As the Owner, I want later outcomes to raise or lower a lesson's
   importance and a lesson at 0 removed, so that a lesson that stops
   predicting outcomes is forgotten.
5. As a Decompose run, I want to read the lessons file at draft time, so
   that past mistakes inform the next breakdown.
6. As step 4 (#989), I want the lessons file and the tool's output to be
   computed from run records alone, so that I measure against a baseline
   nobody edited.
7. As a Reviewer, I want voting, decay, removal and the source-run rule
   pinned by tests on exact output strings, so that I can trust the
   behaviour without a live history.

## Success criteria

Exact line and message wording is fixed by Architect; each criterion below
is tested by asserting the exact strings the tool emits.

- [ ] A lesson is added only with at least one cited source run. An ADD with
      no source run exits nonzero, prints a problem string naming the
      missing source, and leaves the file byte-identical. A test asserts
      that string and the unchanged file.
- [ ] A lesson that passes ADD is written at importance 2 and its line
      carries its source runs. A test reads the file back and asserts the
      importance of 2 and each cited run.
- [ ] UPVOTE on a lesson raises its importance by 1 and DOWNVOTE lowers it
      by 1. A test asserts 2 -> 3 and 2 -> 1, and that each vote leaves the
      lesson's source runs intact.
- [ ] A DOWNVOTE that brings a lesson to 0 removes its line from the file;
      the lesson is not kept at 0 and not written with a negative count. A
      test asserts the line is absent at 0 and that a lesson at 1 remains.
- [ ] A vote or EDIT naming a lesson that does not exist exits nonzero with
      a problem string and does not create it. A test asserts this.
- [ ] EDIT changes a lesson's text and keeps its importance and its source
      runs. An EDIT that would leave a lesson with no source run is refused
      like an ADD. A test asserts both.
- [ ] Contrast pairs are built from re-plan, design-gap and review signals
      only. No band-miss pair and no retro prose reaches the file: a test
      with a fixture history that holds a band miss and a retro note
      asserts no lesson cites them.
- [ ] A history that yields no contrast pair leaves the lessons file empty
      or absent, and the tool prints that no pair was found; it never
      writes a default lesson. A test asserts the string and the empty
      result.
- [ ] The Decompose skill text instructs reading the lessons file at draft
      time and says what to do when the file is absent or empty. A test on
      the skill text asserts the reference to the file and to the
      absent-or-empty case.
- [ ] Every figure the tool prints (a pair count, an importance count) is
      computed from run records, and no lesson ships in the repo as a
      hand-written seed. A test with a fixture history asserts the figures.
- [ ] The tool is stdlib only and makes no network call.
- [ ] `.claude-plugin/plugin.json`'s version is unchanged on this branch.
- [ ] `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
      `python3 gates.py` and `python3 gates.py --selftest` all pass.

## Out of scope

- Band-miss pairs, until a band clears the n >= 5 floor in
  `size_band_calibration.py`.
- Retro prose, or any free-text note, as input to the file.
- Any hand-written lesson, including a seeded default.
- Prompt optimization and the Decompose eval suite (#989).
- A plugin version bump (ADR-0095).
- Mirroring this run's items to work orders; the PR body carries a
  `No work order:` line.
- Changing `decompose_signals.py`'s signal definitions.

## Open questions

- What counts as "a run of the same kind" for a contrast pair? A bad choice
  produces false contrasts. For Architect.
- Where does the lessons file live, and what is its line format? For
  Architect.
- Does pair derivation import `decompose_signals.py`'s records or re-walk
  git, and does the tool earn a new shared module under the seam rule
  (multiple real callers and observed divergence)? For Architect.
- How does Decompose read the file: the skill text names a path, or a tool
  prints the file? For Architect.
- Which later outcome triggers an UPVOTE and which a DOWNVOTE, and who runs
  that update (the Owner, or a step in an existing stage)? For Architect.
- How is the experiment measured against the re-plan rate, and can that
  measure detect harm at this run count? A fixed comparison window is not
  settled. For Architect, read by Operate.
- Will the history ever yield pairs? If not, the file stays empty, which is
  honest but gives step 4 nothing. The brief's minimum signal is that #989
  uses the output or fails on it.
