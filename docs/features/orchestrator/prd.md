---
stage: prd
run: feature:orchestrator
date: 2026-10-10
id: PRD-0013
ux: not-applicable
ux-reason: CLI and text artifacts only; the decision queue reuses the established one-question-at-a-time format, and plan, ledger and scorecard are text like every other run artifact
---

# PRD: the Conductor — a batch orchestrator

## Problem statement

Coordinating several pieces of work at once happens only while the Owner
drives one long interactive session. Holding a batch of issues, fanning out
agents, choosing a model and context budget for each, reserving shared
numbers, ordering merges and resolving the collisions between them, and
bringing decisions back one at a time are all done by hand, and stop when
the session stops. `autorun` covers one run's stages and `work-queue`
covers the Implement stage for ready work orders; nothing holds the whole
batch. The measured cost of not holding it: overlapping agent PRs conflict
41.7% of the time across agents (idea.md, Evidence), and this repo has
already renumbered work orders, ADRs and manifests after collisions.

## Solution

A Conductor role the Owner hands a batch of issues in one repository. It
returns a priced plan before spending anything, reserves the shared numbers
and versions the batch will need, briefs one Worker per item from the
Owner's model-and-effort policy, has every item reviewed by a Worker that
did not write it, and orders the merges. Decisions wait in a durable queue
and reach the Owner one at a time; anything needing the Owner's consent
(merge, ADR, spend) is confirmed in the Owner's session. Every item comes
back merged or blocked with a reason, and each batch ends with a scorecard
that accumulates into a trend.

## Actors

- **Owner** — the human who files issues, answers queued decisions, and
  confirms merges, ADRs and spend. Reached only through the decision queue;
  no agent message counts as Owner consent.
- **Conductor** — the single coordinator for a batch: plans, prices,
  reserves shared numbers, briefs Workers, orders merges, asks questions,
  and is the only writer to shared files. It never reviews an item it
  dispatched. ("Conductor" is a role name, not a marketed skill name.)
- **Worker** — an agent that does one item through the existing skills
  (`autorun`, `work-queue`, stage skills), or reviews one item with the
  existing reviewer charter. A Worker never coordinates other Workers.

GitHub (CI, issues, pull requests, a merge queue where the repo has one)
is a system the Conductor uses, not an actor.

## User stories

1. As the Owner, I want to hand the Conductor a batch of issues and get a
   priced plan (order, model and effort per item, estimated cost) before
   anything is spent, so that I approve the spend knowingly.
2. As the Owner, I want decisions to queue durably and reach me one at a
   time, with anything needing my consent (merge, ADR, spend) confirmed in
   my next session, so that I don't drive a live session and can come back
   after a break.
3. As the Owner, I want a ledger — the batch plan plus a timestamped row
   for every item state change — so that I can see where every item stands.
4. As the Conductor, I want to reserve shared numbers and versions (ADR and
   work-order numbers, plugin version, template manifest) before dispatch,
   so that parallel Workers never collide.
5. As a Worker, I want a fixed brief (objective, output, tools, boundaries,
   model, effort, context budget) whose model and effort come from the
   Owner's written policy, so that I do one item well on the cheapest model
   the policy allows.
6. As the Conductor, I want to queue an item for merge only after a
   Reviewer pass by a Worker that neither dispatched nor wrote it and green
   checks, and to merge in my order — through the merge queue where the
   repo has one, otherwise one at a time after rebasing on the base branch
   and re-running checks — so that merged work is reviewed and never
   green-alone-red-together.
7. As the Owner, I want every item back merged or blocked with a reason,
   with a stalled item escalated to me rather than retried in a loop, so
   that nothing silently stalls.
8. As the Owner, I want a scorecard at the end of every batch, computed
   from the ledger and accumulated append-only, so that I can see whether
   the Conductor is getting better.

## Success criteria

Checked on a real batch of at least four issues in one repository.

- [ ] Every Owner action during the batch is an answer to a queued decision
      or a consent confirmation; the decision-queue log shows each one and
      no other Owner coordination step exists.
- [ ] Zero shared-number collisions: every ADR number, work-order number
      and version in the merged files matches a reservation the Conductor
      made, and no two items hold the same one.
- [ ] Every Worker run writes a metered ledger row carrying the cost its
      harness reported, and the plan's estimate is within ±50% of the sum
      of those rows.
- [ ] The ledger holds a timestamped row for every item state change, and
      each item's final ledger state (merged / blocked with reason) matches
      its pull request or issue state on GitHub.
- [ ] Every merged item has a ledger record naming the Worker that wrote
      it and a different Worker that reviewed it, and the commit that
      merged has green checks.
- [ ] Every Worker ran on the model and effort the Owner's policy names
      for its item type (100%, from the ledger).
- [ ] A scorecard is produced for the batch from ledger rows alone —
      Owner touches per merged item, metered cost per merged item, estimate
      error %, collisions, stalls and escalations, Reviewer-requested
      changes per item, batch start to last merge, and ADR-0080's accepted
      orders per gate-wait hour — and appended to the scorecard history; a
      deliberately malformed ledger row makes it fail with a problem string
      rather than report a number.

## Out of scope

- Parallel writers on the same files — items that touch the same files run
  in sequence (single-threaded writes).
- Nested coordinators — one Conductor per batch.
- Unattended merges — no merge without the Owner's in-session confirmation.
- Cross-repo batches — one repository per batch (one pipeline root, #644).
- Replacing `autorun`, `work-queue` or the factory assembler — the
  Conductor calls them.
- Third-party orchestrators (Gas Town, claude-flow, Conductor.build) and
  JS/TS Claude Code mods — the repo is stdlib-only.
- A console or dashboard view of the ledger or scorecard.
- Choosing models or effort on the Conductor's own judgement — the Owner's
  policy decides.

## Open questions

- Can a merge queue be enabled on this user-owned public repository at all?
  GitHub's docs do not say; ADR-0070 assumed it. — the Owner, by trying the
  "Require merge queue" setting.
- Where the decision queue lives so it survives sessions (a pinned issue
  like the gate queue, a run artifact, both), and how a queued answer is
  confirmed in-session. — Architect.
- How a Worker run inside a session is metered in dollars (headless
  `claude -p --output-format json`, the assembler, or another harness
  path). — Architect.
- What an "item type" is for the model-and-effort policy, and where the
  policy lives (`factory.json` is the likely home). — Architect, with the
  Owner.
- Stall rule: how many failed attempts or how long before an item
  escalates. — Architect.
