---
stage: prd
run: feature:software-factory
date: 2026-07-11
id: PRD-0001
ux: not-applicable
ux-reason: infrastructure feature — no user-facing surface in v1; the operator's surface is the tracker and PRs
---

# PRD: Software factory v1 (self-host)

## Problem statement

Matt operates the lifecycle pipeline alone and synchronously. Work only
moves while he is at the keyboard; an unattended agent has no bounded,
safe way to pick up work; and nothing mechanical guarantees that
requirements, decisions, and shipped code stay connected. His attention
goes to execution instead of judgment, and the pipeline's throughput is
capped by his working hours.

## Solution

A factory layered onto the existing pipeline, proven on this repo first
(self-host). When this ships, Matt can approve a piece of work, walk
away, and return to a reviewed, budgeted, fully traceable pull request
waiting at his merge queue:

- Work enters as signals, not only as Matt's ideas: a production error, a
  filed issue, or a scheduled sweep becomes a triaged, traceable work
  item without Matt transcribing it.
- Work orders are dispatchable: an approved, decomposed unit of work can
  be handed to an unattended agent with a single owner action.
- The dispatch contract is agent-agnostic: a work order carries
  everything needed to execute it, so the coding agent behind the slot is
  swappable — the factory is never coupled to one agent.
- Every dispatched run has a hard spending limit and no more access than
  its work class grants; running out produces a clean handoff
  (work-in-progress preserved, remaining work stated), not a runaway or a
  loss.
- No work is verified or approved by the agent that produced it —
  generation and verification are separate actors producing separate
  artifacts, and verification is evidence, not assertion.
- Exactly three human decisions bound the line — requirements approval,
  design approval, and merge — and each is enforced by the platform, not
  by convention.
- Every work order traces to an approved requirement, and every change
  traces to a work order; a broken link fails the build rather than
  waiting for a human to notice.
- The factory reports on itself weekly: how much of its work is accepted,
  how much gets rewritten, what escapes to defects, what each unit of
  work costs, and how long work waits on Matt. Spend rolls up per
  requirement, so "was this feature worth what it cost?" has an answer.

## Actors

- **Matt (editor-in-chief)** — the only human; approves at the three
  gates, dispatches work orders, owns taste and irreversible calls.
- **Stage agents** — chartered agent roles (PM, architect, UX designer,
  planner, engineer, QA, reviewer, support, toolsmith) executing all work
  between the gates.

## User stories

1. As Matt, I want to dispatch an approved work order and walk away, so
   that a reviewed pull request is waiting in my queue instead of a to-do
   on my list.
2. As Matt, I want every change mechanically traceable to a work order
   and a requirement, so that scope creep and orphan work fail the build
   instead of needing my vigilance.
3. As Matt, I want an agent that exhausts its budget to stop, preserve
   its work, and hand off, so that a bad run costs a bounded, known
   amount.
4. As Matt, I want weekly factory metrics — acceptance, rework, escaped
   defects, time-to-repair, cost per work order, and how long work waits
   on me — so that autonomy grows on data, not vibes.
5. As a stage agent, I want the work order to carry everything I need
   (requirement links, acceptance criteria, budget), so that I can
   execute without guessing intent.

## Success criteria

- [ ] ≥ 8 work orders merged through the factory's own three gates.
- [ ] ≥ 3 work orders completed fully unattended: dispatch → agent pull
      request → batched review → merge, with zero human touches between.
- [ ] A deliberate budget-exhaustion test produces a hard stop, preserved
      work-in-progress, and a handoff that names the remaining work.
- [ ] A dispatch attempted by anyone other than Matt does not run
      (verified, not assumed).
- [ ] A deliberately broken requirement→work-order link fails the build.
- [ ] A change whose verification is asserted but not evidenced fails the
      build.
- [ ] At least one automated signal (error, sweep, or filed issue)
      becomes a triaged work item with no human transcription.
- [ ] The first weekly report posts with every merged work order present
      in the cost ledger.

## Out of scope

- Serving anyone but Matt: multi-tenant anything, a control-plane app,
  dashboards beyond the weekly report.
- Unattended merges of any kind — every merge is human in v1; classes
  graduate later on evidence, and one escape revokes a class.
- A knowledge-graph database — typed cross-links with build-time checking
  only, until link-checking measurably stops scaling.
- A real external product (that is Milestone 2, after the factory has
  built itself).

## Open questions

- Budget calibration per size class (starting table is a guess) — answered
  by the cost ledger during Milestone 1; planner role owns the loop.
- Dependency-graph tooling (beads) adoption timing — answered at
  decompose.
- Physical merge-gate enforcement on a private free-plan repo is
  unavailable (requires a paid plan or a public repo) — Matt decides;
  until then the merge gate is convention plus CI.
- Design decisions for dispatch, gating, and budgets are recorded in
  ADR-0032, ADR-0033, ADR-0034 (companion change) — parked there per the
  requirements-not-design rule.
