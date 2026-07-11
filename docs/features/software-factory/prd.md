---
stage: prd
run: feature:software-factory
date: 2026-07-11
id: PRD-0001
ux: not-applicable
ux-reason: infrastructure feature — labels, workflows, detectors; no UI surface in v1
---

# PRD: Software factory v1 (self-host)

## Problem statement

Matt operates the lifecycle pipeline alone and synchronously. Work only
moves when he is at the keyboard, unattended agents have no bounded, safe
way to execute, and there is no mechanical enforcement that requirements,
decisions, and code stay linked. He wants as much of the line as possible
to run while he is AFK, with his time reserved for a small number of
judgment gates.

## Solution

A GitHub-native factory layered onto the existing pipeline, built and
proven on this repo first (self-host). When this ships:

- Work orders exist as GitHub issues, mirrored **one-way** from breakdown
  rows (dispatch plane; knowledge plane stays authoritative per ADR-0004).
- Applying `wo:ready-for-agent` (owner only) dispatches the order to
  claude-code-action on Actions, which works under a hard token budget and
  opens a PR citing its work order; exhaustion produces a structured
  handoff comment, never a runaway.
- Exactly three human gates bound the line — PRD approval, blueprint/ADR
  approval, PR merge — physically enforced by CODEOWNERS + branch
  protection, with agent review pre-chewing every PR.
- Offline CI detectors (audit-evals.py conventions) gate link integrity
  between PRDs, ADRs, work orders, and PRs, so drift is caught rather
  than trusted away.
- A cost ledger records every run; weekly rollups report acceptance rate,
  churn, defect escapes, MTTR, cost per merged order, and gate latency.

The M1 work-order set (factory-init, labels, detectors, assembler,
budget guard, routing, sweeps, cost report, design pipeline, charters,
orientation pack, charter regression suite, gate digest, rejection
mining) is decomposed in `breakdown.md` after this PRD and its ADRs
(ADR-0032..0034) are approved.

## Actors

- **Matt (editor-in-chief)** — the only human; approves at the three
  gates, applies `wo:ready-for-agent`, owns taste and irreversible calls.
- **Stage agents** — chartered agent roles (PM, architect, UX, planner,
  SWE, QA, reviewer, support, toolsmith) executing between the gates.

## User stories

1. As Matt, I want to label a work order and walk away, so that a
   reviewed, budgeted PR is waiting in my queue instead of a to-do.
2. As Matt, I want every PR mechanically traceable to a work order and a
   PRD section, so that scope creep and orphan work fail CI instead of
   needing my vigilance.
3. As Matt, I want an agent that exhausts its budget to stop, commit WIP,
   and hand off, so that a bad run costs a bounded amount, never a month
   of spend.
4. As Matt, I want weekly factory metrics (acceptance, churn, escapes,
   MTTR, cost/WO, gate latency), so that autonomy graduates on data, not
   vibes.

## Success criteria

- [ ] ≥ 8 work orders merged through the factory's own three gates.
- [ ] ≥ 3 work orders executed fully AFK: label → agent PR → batched
      review → merge, with zero human touches in between.
- [ ] One deliberate budget-exhaustion test produced a hard stop, a
      pushed WIP branch, and a correct handoff comment.
- [ ] An issue labeled `wo:ready-for-agent` by a non-owner does NOT
      trigger the assembler (injection guard verified).
- [ ] A deliberately broken cross-link (dangling PRD/ADR token) fails CI.
- [ ] First weekly cost report posted with all merged orders present in
      the ledger (reconciliation detector green).

## Out of scope

- Multi-tenant anything, custom control-plane app, dashboards beyond the
  weekly report issue, merge queues, self-hosted runners (M3 decisions).
- Auto-merge of any class (graduates in M2 on ≥20 PRs / ≥90% acceptance /
  0 escapes / churn ≤10%, with auto-revoke).
- A graph database — cross-links + detectors only, until link-checking
  provably stops scaling.
- Real external product (M2).

## Open questions

- Budget table calibration (S≈$5 / M≈$15 / L≈$40 is the starting point) —
  answered by `costs.jsonl` actuals during M1.
- beads adoption timing (not installed yet; dependencies ride issue links
  until its work order lands) — answered at decompose.
