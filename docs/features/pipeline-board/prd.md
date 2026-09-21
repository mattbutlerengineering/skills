---
stage: prd
run: feature:pipeline-board
date: 2026-08-25
id: PRD-0005
ux: required
assumptions:
  - "Out-of-scope list (gate-level view, auto-refresh, interactivity) taken
    from interviewer recommendations — the exclusions question went
    unanswered in the interview; console integration left as an open
    question rather than assumed excluded."
---

# PRD: Pipeline board

## Problem statement

With several runs in flight at once, observing what's going on is hard:
"which task is on which step?" has no glanceable answer — only commands
(`next`, `bd ready`) and mental walks over `docs/features/*/` and
`docs/fixes/*/`. At interview time four runs were active at four different
stages and enumerating them took a shell loop.

## Solution

A directly-invoked utility skill. Asking for the board generates one
self-contained file and opens it: the pipeline's stages laid out in the
editorial style of the referenced diagram-design system, with every active
run placed on its current stage. Nothing is committed; the board is an
on-demand snapshot of run state, sharable as-is because the file carries no
external dependencies.

## Actors

- **Operator** — the person running the pipeline in a target repo (today:
  Matt in this skills repo); invokes the board and reads it to orient.
- **Viewer** — anyone the operator shows the board to (a teammate, a status
  update, future-self at session pickup); opens the file with no repo and
  no tooling.

## User stories

1. As an **operator**, I want one board showing every active run placed on
   its current stage, so that orientation is a glance instead of commands.
2. As an **operator**, I want run kinds distinguished (feature /
   maintenance / product) including maintenance runs' shorter stage ladder,
   so that the board never implies a stage a run doesn't have.
3. As an **operator**, I want the board generated on demand from artifact
   state at that moment, so that there is nothing to keep fresh and nothing
   committed to the repo.
4. As a **viewer**, I want the board as a single self-contained file, so
   that I can open or receive it without the repo, the tooling, or a
   network connection.

## Success criteria

- [ ] **Placement parity** — for every run shown, its stage placement
  equals what the protocol's orientation table derives at generation time
  (honoring the `ux:` conditional, `re-entry:` depth, and the Implement
  checkbox rule). Checkable by running orientation per run and comparing.
- [ ] **Completeness** — every active run (per the protocol's run-discovery
  rules; active = has artifacts, no `retro.md`) appears exactly once, and
  no run is invented. Completed runs do not appear.
- [ ] **Glance test** — a person shown only the file answers "which step is
  <run> on?" correctly for each active run, no commands run.
- [ ] **Aesthetic checklist** — the output passes a written checklist
  drawn from the diagram-design system (self-contained, single accent
  color, 1px hairline strokes, editorial type hierarchy, deliberate
  layout — visibly not default-mermaid output). The checklist is authored
  at UX Design time; Verify applies it item by item.
- [ ] **Self-containment** — the file renders fully with the network
  disabled; no external fetches, fonts included or safely fallen back.

## Out of scope

- **Gate-level view** — work orders across `wo:` lifecycle labels stay off
  this board; Idea already scoped this to runs-across-stages.
- **Auto-refresh** — no scheduling, no daily-routine or CI integration,
  no committed always-current figure. On-demand only, accepting the named
  "never invoked" risk for v1.
- **Interactivity** — no click-to-inspect, no presenter mode; a still
  figure. The sibling interactive/animated diagram skills exist if this
  changes later.
- **State editing** — the board is read-only orientation; it never
  advances, claims, or modifies a run.

## Open questions

- How does the skill derive orientation without becoming a second owner of
  the protocol's orientation table (the one-fact-many-owners class this
  repo actively hunts)? — Architect.
- SVG or HTML as the output medium, given self-containment and
  open-anywhere? — Architect, informed by UX Design's layout choice.
- Is any part of the diagram-design reference vendored (style tokens, a
  template) or is the aesthetic reproduced from a written checklist alone?
  — Architect; interacts with the aesthetic-gap risk.
- Does the process-dashboard console eventually embed or link the board,
  or stay fully separate? — Operator, after v1 has been used for a while.
- Mitigation for "never invoked": should session-pickup guidance (e.g.
  `next`'s completed-run moment or README) mention the board? — Operator,
  post-v1.
