# Autorun brief: decompose-lessons

Not an artifact. Written 2026-10-20 by the orchestrator under the `/goal`
"complete remaining gh issues". The Owner answered in session, taking the
recommended option each time:

1. What to drive: "#987 first, then carry on" (the 2026-10-20 merge answer
   for #1047 named #988 as the next run), the third step of the Decompose
   learning loop.
2. Pair source: "Re-plan, design-gap, review signals only (Recommended)".
   Contrast pairs are built from the three outcome signals
   `decompose_signals.py` measures today. Band-miss pairs are out of scope
   until a band clears the n >= 5 floor in `size_band_calibration.py`
   (PR #1047); the PRD records that gap. No lesson is invented from data
   that does not exist, and raw retro prose never feeds the file.
3. Release (the Owner's choice on #986 and #987, carried over as the
   default here, an orchestrator reading): prepare-and-stop. Ship pushes
   the branch and opens one PR and does not merge. A merge needs the
   Owner's own answer.

The rest of this brief is the orchestrator's reading of issue #988 and of
the repo. When a stage needs an answer this brief doesn't hold, it follows
the autorun rule: take the skill-supplied default and log it, or else stop
and surface the question.

## What and why (orchestrator's reading of #988)

Step 3 of 4 in the Decompose learning loop; steps 1 and 2 are merged
(#1040 `decompose_signals.py`, #1047 `size_band_calibration.py`). ExpeL
(Zhao et al., AAAI 2024, arXiv 2308.10144) keeps a flat list of insights
mined by contrasting a failed run with a successful run of the same kind,
maintained with ADD / EDIT / UPVOTE / DOWNVOTE and an importance count: a
new insight starts at 2 and is dropped at 0. Feeding raw self-reflections
made it worse, so free-text retro notes must not feed it.

- **Source:** contrast pairs built from outcome signals, never retro prose.
- **Shape:** one lesson per line, each with an importance count; votes from
  later outcomes; dropped at 0, so the file forgets.
- **Use:** read by the Decompose skill at draft time.
- **Caveat (from the issue):** no verified source shows this improving
  software decomposition; treat it as an experiment and measure it against
  the re-plan rate.

## Acceptance (from the issue)

- Every lesson cites the runs it came from; no lesson without a source run.
- Voting and decay are tested; a lesson at 0 is removed.
- Decompose reads the file. A skill change rides the wave's release PR
  (ADR-0095): this branch never touches `.claude-plugin/plugin.json`'s
  version.

## Idea-stage inputs (orchestrator's reading)

- **Problem, from the sufferer's view.** Decompose drafts each breakdown
  from scratch. What past breakdowns got wrong (re-plans, design gaps sent
  back to Architect, review findings that trace to an item) is measured
  now but never reaches the next draft.
- **Who has it, and how they cope today.** The Owner and every Decompose
  run. They rely on memory and on the skill text, which only changes by
  hand.
- **Why now.** #986 made the outcomes measurable and #987 added the cost
  band; this step is the first consumer that feeds a measurement back.
- **Evidence.** Anecdote, labelled: ExpeL's reported HotpotQA gain and its
  drop from raw reflections, from the issue. None for software decomposition.
- **Rough shape.** A stdlib-only root tool that derives contrast pairs from
  `decompose_signals.py`'s records, keeps a lessons file with importance
  counts, votes and decay, and a Decompose skill step that reads it. A
  hunch, not a design.
- **Success.** A lesson exists only with source runs, decays to removal at
  0, and the Decompose skill reads the file at draft time.
- **Ways this dies.** Too few runs yield any contrast pair; lessons are
  noise that raise re-plan rate; a hand-written lesson creeps in.

## Scope, constraints and tracker

- In: pair derivation from the three measured signals, the lessons file
  format, ADD/EDIT/UPVOTE/DOWNVOTE with decay, source-run citation, the
  Decompose skill read step.
- Out: band-miss pairs, retro-prose input, prompt optimization (#989),
  any hand-written lesson, any plugin.json version bump.
- Stdlib only. A new shared module needs multiple real callers and observed
  divergence (CLAUDE.md seam rule).
- Issue #988 seeds the run and the PR closes it. No work order is mirrored;
  the PR body carries a `No work order:` line.
- No user-facing surface beyond the skill text and CLI output
  (`ux:` not applicable).

## Operate

operate:
  minimum-signal: step 4 (#989) reads this tool's output, either using
    the numbers or failing on them

Operate does not run in this invocation.

stop-after: ship
