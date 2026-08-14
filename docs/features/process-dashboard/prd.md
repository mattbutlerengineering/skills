---
stage: prd
run: feature:process-dashboard
date: 2026-08-13
id: PRD-0002
ux: required
---

# PRD: Process dashboard v1

## Problem statement

The Operator can't see where anything stands without spelunking. Run
state, gate queues, spend, and drift live in breakdown checkboxes,
pinned issues, weekly cost-report issues, `costs.jsonl`, and
`LEDGER.md` — orienting means shell commands against each surface in
turn, and disagreements between surfaces (a closed mirror issue over an
unchecked row, #123) go unnoticed for weeks. The process is about to
run in multiple repos, multiplying every one of those surfaces.

## Solution

A console the Operator opens — data gathered fresh at open — showing
every configured repo in one overview: each run and its stage, the
three human-gate queues with ages, the seed backlog (reorderable — its
order *is* the prioritization, ADR-0029), the factory's output (work
orders → PRs → merges, spend against caps), improvement trends, and
flags wherever two state surfaces disagree. Backlog reorder is v1's
only write. Improvement metrics the existing records can't answer get
their recording added as part of this work, so the "are we improving"
view is powered by real data, not partial proxies.

## Actors

- **Operator** — Matt: sole human running the pipeline and factory
  across every repo that adopts them.

## User stories

1. As the Operator, I want a cross-repo overview of every run and its
   current stage, so that orientation takes a glance instead of shell
   spelunking.
2. As the Operator, I want each human gate's queue with waiting ages,
   so that nothing stalls on me invisibly.
3. As the Operator, I want to see and reorder the seed backlog, so
   that prioritizing is arranging a list, not editing a file.
4. As the Operator, I want work orders traced to PRs and merges with
   spend against caps, so that I can see what the factory produced and
   what it cost.
5. As the Operator, I want improvement trends — cost per work order,
   gate latency, acceptance/rework — so that autonomy decisions ride
   data (the PRD-0001 story-4 metrics, finally rendered).
6. As the Operator, I want disagreements between state surfaces
   flagged, so that mirror drift is seen within a day, not weeks.

## Success criteria

- [ ] A cold open shows every configured repo's runs with stage and
      next step, matching what the `next` router would say, with no
      terminal involved.
- [ ] Gate queues with ages match the pinned gate digest.
- [ ] Reordering the backlog in the UI reorders `docs/backlog.md`'s
      lines with claim markers intact.
- [ ] Every work order shows a lifecycle consistent with its breakdown
      row and PR state.
- [ ] Spend vs caps, cost per work order, and gate-latency trends
      render from `costs.jsonl`.
- [ ] A closed-mirror-issue-with-unchecked-row fixture (#123's class)
      is visibly flagged.
- [ ] At least two repos appear in one overview.

## Out of scope

- **Multi-user & auth** — one Operator, their existing credentials; no
  accounts, roles, or sharing.
- **Editing run artifacts** — idea/prd/architecture/breakdown content
  stays in files edited in the repo; the backlog's *order* is the only
  mutable surface.

Deliberately *not* excluded — later versions, not v1: control-plane
actions (approving, dispatching, merging from the console — the gate
stays the human's judgment, ADR-0033 gates the judgment not the
medium) and alerting/push. V1 forecloses neither.

## Open questions

- Where does the UI live and run, given a stdlib-only, plugin-vended
  repo? — Architect.
- How does backlog reorder write back (direct file write vs commit vs
  PR), and on which repo's checkout? — Architect.
- How does the console discover which repos to observe, and with what
  read access? — Architect.
- Which improvement metrics are derivable from existing records
  (`costs.jsonl`, PR history) vs need new instrumentation, and what is
  that recording? — Architect, then Decompose.
