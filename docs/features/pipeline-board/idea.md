---
stage: idea
run: feature:pipeline-board
date: 2026-08-24
---

# Idea: Pipeline board — see which run is on which step

## Problem

When doing work, it's difficult to observe what's going on. Several runs are
in flight at once, each somewhere along Idea → PRD → … → Operate, and there
is no way to *see* which task is on which step — knowing where anything
stands means running commands (`next`, `bd ready`) or mentally walking
directory trees. The user wants a diagram, in the editorial style of
[cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)
(self-contained HTML+SVG, deliberate layout, single accent — no mermaid
slop), that also shows which task sits on which step.

## Who has it

Matt, as the operator of this repo's pipeline — and by extension anyone
running these skills on a target repo with more than one active run. Coping
today: re-running the `next` router per run, `bd ready`, ad-hoc shell loops
over `docs/features/*/` and `docs/fixes/*/`, or just holding it in his head.
Secondary sufferer: anyone Matt wants to show status to (or future Matt at
session pickup), who today gets a directory listing at best.

## Why now

Three pressures arrived together:

- **Too many runs.** Concurrency is now normal — at interview time three
  runs were active at once (`feature:first-live-dispatch`,
  `maintenance:marker-diagnostics-that-lie`, `maintenance:one-labels-walk`),
  each at a different stage, and the factory work-queue makes parallel runs
  the intended mode, not an accident.
- **Session orientation.** Every fresh session re-derives state from
  artifacts and bd; a picture would make pickup instant.
- **Sharing status.** Showing anyone where things stand needs something
  better than a directory listing.

## Evidence

- Direct observation at interview time (2026-08-24): answering "where does
  each active run stand?" required a shell loop over three directory trees
  checking artifact existence against the orientation table. Three active
  runs, three different stages, zero glanceable surface. (Anecdote, but a
  reproducible one — the state model guarantees it recurs.)
- The user's own report: "it's difficult to observe what's going on" —
  named unprompted as a why-now alongside the offered options.
- The backlog carries adjacent demand (process-dashboard console seeds,
  metrics-trend seed), suggesting observability of the factory is a
  recurring want, not a one-off.

## Solution hunch

A new **utility skill** (directly invoked, owns no run artifact — sibling of
`architecture-diagram`) that reads run state off disk and emits one
self-contained board figure on demand: the pipeline's stages as columns (or
a flow), each active run as a labeled token sitting on its current stage,
rendered in the diagram-design editorial aesthetic. Run discovery and
stage orientation already derive this from which artifacts exist, so the
data is free. A hunch, not a design — column board vs. flow diagram,
SVG vs. HTML, and how maintenance runs' shorter stage ladder is drawn are
all open.

## Success in one sentence

One look at the board tells me every active task and which step it's on,
without running a single command.

## Unknowns & risks

- **Aesthetic gap** (user's top risk): the diagram-design look — editorial
  serif, hairlines, deliberate layout — is hard to reproduce reliably from
  a skill prompt; output could land as exactly the "mermaid slop" it's
  meant to replace. The linked repo's templates are external and not
  vendored here.
- **Never invoked** (user's second risk): on-demand means remembering to
  ask; if the board isn't part of session pickup it quietly stops being
  looked at.
- Flagged by interviewer, not selected by user as top risks: the skill
  re-derives "which stage is this run on," which the protocol's orientation
  table already owns — a retyped copy is the one-fact-many-owners class
  this repo just spent a run hunting; and the process-dashboard console is
  already a status surface a second one could drift from. Both are design
  constraints for the PRD/architect stages rather than idea-stage blockers.
