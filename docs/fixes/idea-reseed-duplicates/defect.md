---
stage: capture
run: maintenance:idea-reseed-duplicates
date: 2026-10-25
re-entry: implement
intake: #1064
---

# Defect: re-running Idea on a run appends its seeds twice

## Defect (or Condition)

The Idea skill's ladder step appends each unchosen larger rung to
`docs/backlog.md` as `- <seed text> (from: <run-ref>)`. The file is
append only and nothing tells the skill to look first, so running Idea a
second time on the same run (to revise the brief, or after a demotion)
appends the Moonshot again, and the Showstopper again when Solid is still
the pick.

Expected: a second pass on the same run seeds nothing it already seeded.

## Reproduction / Evidence

- Reported in #1064, from the Idea ladder review
  (`docs/features/idea-ambition-ladder/review.md`, shipped as #1052):
  "Showstopper and Moonshot are still seeded, and re-running Idea on the
  same run would append duplicate seeds."
- `skills/idea/SKILL.md` step 4 on origin/main states the append rules
  (append only, below the last line, never rewrite) and no read of the
  run's existing lines.

## Root-cause hypothesis

Hypothesis: the append-only rule was written for a single pass; the
re-run case was never stated, so the model has no instruction to check.

## Blast radius

Any repo using the Idea skill where a run's brief is revised. The cost is
noise in the seed inbox, which `next` lists when no run is active; no data
is lost. Since #1052 (2026-10-23).

## Ruled out

- A tool-side dedupe: Idea writes the backlog itself and the skill names
  no tool for the write (pinned by
  `test_the_skill_shows_no_real_slug_and_no_tool_for_the_write`).
- The rest of #1064, decided separately on the issue: the unconditional
  Showstopper default and a grader footer wait on the first paid
  `idea`/`decompose` eval runs; `decompose_grade.py`'s missing input size
  cap is not worth a guard (2.5 s at 1.2 MB, against real breakdowns of
  tens of KB, on files the Owner chooses).

## Work items

- [x] A test pins the re-run rule in `skills/idea/SKILL.md`, red on
      origin/main.
- [x] The skill tells a re-run to read the run's existing
      `(from: <run-ref>)` lines and append only a rung none carries.
