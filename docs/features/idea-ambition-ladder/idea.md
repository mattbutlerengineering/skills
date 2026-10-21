---
stage: idea
run: feature:idea-ambition-ladder
date: 2026-10-20
origin: "Issue #994 (idea: ambition ladder with an achievable showstopper rung and a 30-second demo script), driven in session by the Owner's four answers recorded in autorun-brief.md in this directory. Not a backlog seed: docs/backlog.md has no matching line, so no seed claim is written. Interview answered from the brief and the issue; no live interview held. This brief is produced by the current idea skill, which has no ambition ladder yet, so the proposed ladder is deliberately not applied to it."
assumptions:
  - "In-flight check ran, nothing matches: `gh pr list --state open` returned no open PRs. The only open issue about this is #994 itself. Branches checked by name (idea, ambition, prd, demo, showstopper): docs/orchestrator-idea and docs/orchestrator-prd (orchestrator run docs), feat/launch-demo and its fix/refactor siblings (the launch-demo skill), feat/live-console-idea (the live console's idea run); none edits skills/idea or adds a ladder. This run's own feat/idea-ambition-ladder is the only branch carrying it."
  - "Adjacent shipped work, recorded rather than treated as a match: skills/idea/SKILL.md and TEMPLATE.md as they stand hold no ambition, bigger-version, demo or moonshot step (grep of ambition, bigger, stretch, showstopper, moonshot, wow, demo finds nothing in idea, prd, polish or lean); the idea rules ('don't replace their idea with yours', 'no solution design here') and the single Solution hunch slot are exactly the narrowing #994 names. skills/lean and skills/polish ask for smaller or tidier output, never a bigger or more presentable version of an idea. launch-demo records what a release shipped from ship's artifacts and has no earlier-stage demo input. plugin-evals/ holds suites lean, next, implement, knowledge-base and decompose; none for idea. docs/backlog.md has no ambition line, and its seed grammar (ADR-0029, protocol 'Seed backlog') is the format unchosen rungs would use, one line per seed ending (from: <run-ref>). The seed-backlog run built that inbox and its producers (Operate, Capture); Idea is not a producer today. Not a duplicate of any of them."
  - "Outside corroboration (the optional last30days check on why-now and evidence) was not run: the skill says never to run it unasked, and no human was present to ask. The interview alone is a complete result."
  - "The brief's four Owner answers are binding scope for this stage: demo reaches launch-demo via the PRD (prd gains one line, launch-demo unchanged); suite only, no paid run, no LEDGER movement, plugin-evals/records/ gets nothing; release is prepare-and-stop. The brief's other idea-stage inputs are the orchestrator's reading, recorded here as hunches and anecdote, not Owner decisions."
  - "No interview question this stage offered named options with a recommended default that the brief and issue left open, so no skill default was taken. No evidentiary question was left unanswered by the brief, so nothing was surfaced."
---

# Idea: An ambition ladder for the Idea stage, with an achievable showstopper as the default

## Problem

Every brief the Idea stage produces comes out achievable but never
memorable. Nothing in the interview asks "what is the bigger, more
presentable version of this?", so each run stays the size of the user's
opening framing. Three things hold it there: the rule "don't replace their
idea with yours", "no solution design here", and a single Solution hunch
slot.

## Who has it

- **The Owner**, who runs the pipeline and sees the pattern across runs.
- **Anyone running `idea`.** Today they add ambition by hand, or not at all.
- **The launch-demo skill**, second-hand: it has nothing worth recording
  when the brief that began the run named no demo moment.

## Why now

The launch-demo skill exists and shipped, and its first honest question,
"what do we show?", has no answer upstream. The gap is now visible at the
far end of the pipeline, not only in the briefs.

## Evidence

- **Anecdote, labelled:** the issue's own observation across runs that
  briefs are achievable and unmemorable. Nothing was measured; no count of
  past briefs was taken at this stage.
- **None for the target:** no source shows that offering a ladder produces
  better briefs or better shipped features.
- **Existing mechanism, adjacent:** none asks for a bigger version. The
  launch-demo skill is the downstream consumer that makes the absence cost
  something.

## Solution hunch

A hunch, not a design. Offered here because the issue proposes it:

- After the problem and evidence questions and before the solution hunch,
  the interview offers three rungs anchored on the user's own framing:
  Solid (fixes it, ships fast; the fallback), Showstopper (same problem
  plus one "wait, do that again" moment; recommended by default) and
  Moonshot (beyond this run's scale; saved as a `docs/backlog.md` seed in
  the existing grammar, never chosen here). The user picks and the pick is
  recorded.
- Four showstopper tests so "wow" is not taste: a 30-second demo exists
  (before and after in two sentences, the after something seen); it
  removes a step rather than speeding one; it rests on something only this
  product has; it is achievable, with the riskiest piece named and a spike
  of about two days that could prove it, else it drops to the moonshot.
- Three prompts: what would you show first in a demo; what does the user do
  today they would never have to do again; what does the product already
  know that it is not using. Feature runs get a scaled-down version.
- New `TEMPLATE.md` sections: Ambition rung, The demo, Riskiest piece +
  spike, Cheapest kill test.
- Owner decision, in scope: the PRD copies **The demo** into a success
  criterion ("the demo runs as written"), `verify` checks it, and
  `launch-demo` is unchanged; `skills/prd` gains one line carrying the
  script forward.
- A `plugin-evals/idea/` with/without-plugin suite, authored and tested
  statically, never run. Owner decision, in scope: no paid run, so LEDGER
  maturity does not move and `plugin-evals/records/` gets nothing
  (ADR-0012, ADR-0019, ADR-0081).

## Success in one sentence

A new idea.md names a chosen rung and a 30-second demo script that passes
the four tests, with the unchosen rungs landed as backlog seeds.

## Unknowns & risks

- **Ceremony.** Every brief picks Showstopper by default and the ladder
  becomes a form to fill; whether the scaled-down feature-run version
  stays light enough is unproven.
- **The tests turn into taste.** "Only this product has it" and "removes a
  step" are judgments; if a model or a hurried user can always pass them,
  the four tests guard nothing.
- **The user's framing gets replaced.** Recommending the showstopper
  against the rule "don't replace their idea with yours" is a real tension;
  the ladder must stay anchored on their words.
- **Seed grammar and gates.** Idea is not a backlog producer today, so
  appending seeds is a new write path; a malformed line or an example id in
  a seed trips gates (every doc, fences included).
- **Template change vs existing runs.** New TEMPLATE.md sections must not
  make old idea.md files fail artifact checks in `protocol.py` or lint;
  Architect's to check.
- **A spike that cannot be named.** For some ideas no two-day spike exists
  at the idea stage; the rule "drops to moonshot" may demote too much.
- **No measured effect.** With no paid run, this run produces no delta and
  no evidence the suite discriminates on a real model; a cited run is a
  follow-up needing the Owner's own say-so.
- **Release wave.** Changing `skills/idea` and `skills/prd` needs the wave
  release PR (ADR-0095); the branch never bumps the plugin version.
