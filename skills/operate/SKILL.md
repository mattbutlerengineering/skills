---
name: operate
description: Use when shipped work has been in users' hands and it's time to capture feedback and run a retrospective — closing the loop into the next idea — or when the user asks how the release is landing or doing in production, or what we learned post-launch. Produces retro.md, completing the run.
---

# Operate

Close the loop: gather what actually happened after shipping, compare it to
what the run intended, and turn the difference into the next run's input.
Scoped to feedback capture and retrospective — not monitoring infrastructure.

## Process

1. Read `../../docs/pipeline-protocol.md` for run discovery, gating, and
   frontmatter conventions.

2. **Soft gate.** Predecessor artifact: `release.md`. If missing, apply soft
   gating.

3. **Let it breathe.** If the release just happened, say so and offer to
   return once there's real usage to reflect on — a retro written an hour
   after shipping reflects hopes, not outcomes.

4. **Capture outcomes.** Against `prd.md`'s success criteria and `idea.md`'s
   success-in-one-sentence: what actually happened? Gather whatever signal
   exists — user feedback, your own usage, error reports, the absence of
   complaints. Label the strength of each signal honestly (anecdote vs.
   pattern).

5. **Retrospect on the run itself.** Walk the stages: where did the pipeline
   help, where did it drag, which artifact earned its keep, which stage got
   skipped or backfilled and was that right? Keep / change / stop — a few
   sharp entries beat an exhaustive ceremony.

6. **Retrospect on the environment.** The run's own record of its
   mistakes is `verification.md`'s failures, `review.md`'s findings and
   `breakdown.md`'s Notes. For each mistake, name the check, pointer or
   rule that would have caught it, and classify it: **mechanical** (a
   deterministic check would have caught it — a lint rule, a hook, a CI
   job, a gate detector) or **judgement** (only a reader could — a
   `CLAUDE.md` or `AGENTS.md` line, or a standards statement). A
   mechanical mistake gets a check, never a prose rule; a prose rule is
   what the mistake already slipped past. Propose the carrier as an
   existing thing — the checker, detector, hook, job or file that would
   hold it. A repo whose own check command runs under no hook and no CI
   job has no guardrail at all; record that as a finding rather than
   treating it as the baseline. The structure restates the `retro` skill
   in mattpocock/skills (MIT, Matt Pocock); the words are this pipeline's.

7. **Seed the next runs.** Every gap, complaint, and "next time" becomes a
   one-line idea seed — the natural input to the next Idea-stage run. For
   maintenance runs, the defect or degradation itself becomes a seed for
   preventive work: if the same bug recurs, the retro asks whether the
   pipeline missed a regression test, a review finding, or a design
   constraint that should have been captured earlier. Append each seed to
   `docs/backlog.md` as a well-formed entry per the protocol's seed-backlog
   section, creating the file if absent — never rewrite existing lines.

8. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `retro.md` with protocol frontmatter. This
   completes the run.

## Rules

- Outcomes over activity: "we shipped it" is not an outcome; "it gets used
  for X" or "nobody used it" is.
- The retro judges the process and the bet, not the people.
- Don't skip seeding: a retro that produces no next-idea seeds usually means
  the outcome questions weren't really answered.
