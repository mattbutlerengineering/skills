---
stage: prd
run: feature:decompose-outcome-signals
date: 2026-10-18
ux: not-applicable
ux-reason: "CLI measurement tool with text output only; no screens or flows."
assumptions:
  - "Interview answered from autorun-brief.md in this directory; no live interview held. Every requirement below traces to the brief's five Owner answers or to its sections marked as the orchestrator's reading of issue #986."
  - "No PRD id assigned: the prd skill and its TEMPLATE.md assign none, and recent feature PRDs (for example pr-body-preflight's) carry no id. Nothing in this run cites one, because the brief rules out work-order mirroring."
  - "The 'a zero is never read as no data' requirement on the review-traced signal (story 4, the last success criterion) is derived, not quoted. It extends Owner decision 3's rule that an unmeasurable run is never counted as zero to the case idea.md names as its fourth unknown."
  - "Which refs the tool reads by default, and how strictly boundary subjects match, are left to Architect as open questions (orchestrator instruction). The PRD only requires that both be stated in the tool's output."
---

# PRD: Decompose outcome signals from git history

## Problem statement

The Owner changes the Decompose skill and can't tell whether its plans
hold up. Nobody can say how often a breakdown was re-planned during
Implement, how often Decompose sent a design gap back to Architect, or
which breakdown items review findings land on. So every change to the
skill gets judged by feel. Steps 2 to 4 of the Decompose learning loop
(#987, #988, #989) are meant to calibrate against these numbers, so none
of them can show an effect until this step exists.

The signals already exist, in git history and in `review.md` files.
Nothing reads them, and the history is hard to read. Main is
squash-merged, so boundary commits survive only on run branches and PR
head refs. Most runs also predate the `docs(<slug>): <stage> — …` subject
convention. Measured on 2026-10-18 with this clone's 488 PR head refs
fetched under `refs/remotes/pr/*`: 35 run directories hold a
`breakdown.md`. Strict `decompose — ` subjects exist for 3 runs
(fail-closed-roll-up, pr-body-preflight and reviewer-token). A looser
match adds a fourth, factory, whose decompose commit reads `decompose
PRD-0001 into …`.

## Solution

One command, run at the repo root, reads git history from the refs the
clone already holds. For every run directory with a `breakdown.md` it
prints a per-run row with three signals, then an aggregate:

- **Re-plan count.** Breakdown items added, split, merged or dropped
  between the run's decompose boundary and its implement boundary.
- **Design gaps routed to Architect.** Architect boundaries that come
  after the run's decompose boundary.
- **Review findings traced to an item.** Findings in the run's
  `review.md` that name a breakdown item, out of all its findings.

Each boundary is labelled **observed** (the run has a matching
boundary commit subject) or **inferred**. An inferred decompose boundary
is the commit that first added the run's `breakdown.md`. An inferred
implement boundary is the first commit that ticks one of its
checkboxes. The aggregate reports the observed and inferred populations
separately as well as combined. A run with no boundary of either kind is
named as unmeasurable, with the reason, and is never counted as zero.
The output says which refs were read and which subject-match rule was
applied. The tool never fetches. Fetching PR head refs is a documented
manual step.

The first real numbers for this repo are recorded append-only, written
by the tool's own output and never typed by hand.

## Actors

- **Owner**: maintains this repo and tunes the Decompose skill. Runs the
  command and reads its output.
- **Calibration step**: a later step of the Decompose learning loop
  (#987 cost calibration, #988 lessons file, #989 eval and prompt
  optimization). It reads this tool's output or recorded numbers as its
  baseline.
- **Reviewer**: whoever examines the run's PR at the merge gate and
  judges whether a number is trustworthy.

## User stories

1. As the Owner, I want one command that prints re-plan, design-gap and
   review-traced counts for every run with a breakdown, so that I can
   judge a Decompose change against a baseline and not by feel.
2. As the Owner, I want every boundary labelled observed or inferred, and
   the aggregate split by population, so that a guessed number never
   passes for a measured one.
3. As the Owner, I want each unmeasurable run named with its reason, so
   that a gap in history reads as a gap and not as a clean zero.
4. As the Owner, I want a run whose review findings name no item to read
   differently from a run with no `review.md`, so that a zero traced count
   is never mistaken for "no findings".
5. As a Calibration step, I want the first real numbers recorded
   append-only from the tool's own output, so that later steps can compare
   against a fixed baseline nobody edited.
6. As a Reviewer, I want the output to state which refs were read and
   which subject-match rule was used, so that I can tell how much of the
   history the numbers cover.

## Success criteria

- [ ] One invocation measures every run directory holding a
      `breakdown.md` and prints a per-run row for each one plus an
      aggregate, in the repo's problem-string / count contract.
- [ ] Every per-run boundary is labelled `observed` or `inferred`, and the
      aggregate prints observed, inferred and combined figures for each of
      the three signals.
- [ ] Each unmeasurable run is printed by name with a reason and is left
      out of every aggregate count.
- [ ] The output names the refs that were read and the subject-match rule
      that was applied.
- [ ] The tool makes no network call. A test or a code read shows that
      it runs no fetch, and its only external CLI is git through `cli.py`.
- [ ] Tests through the public interface cover at least these fixtures: a
      run with no re-plans, a run with a split item, a run routed back to
      Architect, a run with only inferred boundaries, and an unmeasurable
      run. Each asserts the exact output strings.
- [ ] For the review-traced signal, a run with findings that name no item
      and a run with no `review.md` print different strings. A test
      asserts both.
- [ ] The first real numbers for this repo are committed append-only, as
      the tool's unedited output. Rerunning the tool on the same refs gives
      the same numbers.
- [ ] `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
      `python3 gates.py` and `python3 gates.py --selftest` all pass.

## Out of scope

- Cost metering and S/M/L calibration (#987), the lessons file (#988),
  and the Decompose eval suite and prompt optimization (#989).
- Changing the Decompose skill or the boundary-commit subject convention.
- Fetching from the network inside the tool, including PR head refs.
- Mirroring this run's items to work orders. ADR-0032 mirroring belongs
  to the factory, not to this run.
- A plugin version bump (ADR-0095). This run does not touch `skills/`.
- Maintenance runs that keep their breakdown inline in `defect.md` with
  no `breakdown.md`. The brief scopes the tool to runs with a breakdown
  file.

## Open questions

- Which refs does the tool read by default? The candidates are local
  branches, `refs/remotes/origin/*`, and PR head refs, which this clone
  holds under `refs/remotes/pr/*` (488) rather than `refs/pull/*`. It
  also holds 13 refs under `refs/pr/`. Is the ref set configurable? The
  output must name it either way. For Architect.
- How strictly are boundary subjects matched? Strict
  `docs(<slug>): decompose — ` gives 3 runs. A loose match also counts
  factory's `docs(factory): decompose PRD-0001 into …`. Does a
  loose-only match count as observed, inferred, or a third label? For
  Architect, and for the Owner if the choice changes what "observed"
  promises.
- How is a breakdown item identified across two versions of the file,
  so that a split or merge can be told apart from an add and a drop? WO
  ids, row numbers and titles have all been used as breakdown rows
  drifted across runs. For Architect.
- When a run has no `architect — ` subject, is a design gap inferred
  from a later commit touching `architecture.md`, or is that signal
  unmeasurable for the run? The brief defines inferred boundaries only
  for decompose and implement. For Architect, labelled under the
  observed/inferred rule either way.
- What counts as a "finding" in a `review.md`, and what counts as
  naming an item? The template's shape has changed over time. For
  Architect.
- Where are the recorded numbers kept, and how are they named?
  Precedents are `evals/results/` and `plugin-evals/records/`. For
  Architect (brief, Scope).
