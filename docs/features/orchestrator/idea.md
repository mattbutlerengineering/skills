---
stage: idea
run: feature:orchestrator
date: 2026-10-10
---

# Idea: an orchestrator for the development workflow

## Problem

Coordinating several pieces of work at once only happens when the owner
drives one long interactive session. Holding a batch of issues, fanning
out research and build agents, choosing which model and how much context
each one gets, sequencing merges and resolving the conflicts between them
(plugin version, ADR and WO numbers, the template manifest), and bringing
decisions back one at a time — all of it is done by hand, inside a live
`/goal` session, and stops when the session does. `autorun` covers one
run's stages and `work-queue` covers the Implement stage for ready work
orders; nothing holds the whole batch.

## Who has it

The repo owner, a solo developer who files issues faster than one session
can coordinate them. Today they cope by running a long interactive session
under `/goal`, answering `AskUserQuestion` prompts one at a time, and
re-issuing the goal when the session stalls; model choice and context are
whatever the session happens to use.

## Why now

Volume plus new capability. On 2026-10-10 six issues were filed in two
hours; closing them took one session through four research agents, four
build agents, a four-PR merge order with an ADR renumbering, and a
hand-tracked $25 paid-eval budget — after a 53-PR backlog close-out in
September and a 13-PR merge on 2026-10-07. Meanwhile Claude Code shipped
the building blocks: dynamic workflows (model per stage, resumable, but no
mid-run human input), cloud routines, per-agent model and effort, agent
teams and cross-session messaging, and `claude plugin eval` to measure the
result (survey: `docs/research/orchestrator.md`).

## Evidence

From this repo (first-party):
- 141 PRs merged in the 30 days to 2026-10-10.
- Identifier collisions across parallel branches already happened: WO ids
  renumbered after colliding with pipeline-board (#506), a manifest
  collision recorded (#464), ADR-0078 claimed by two PRs on 2026-10-10.
- A pairwise merge audit found two PR pairs green alone and red together.
- ADR-0070 adopted GitHub's merge queue, but it was never switched on:
  on 2026-10-10 `main` has no rulesets or branch rules and GraphQL
  `mergeQueue(branch: "main")` returns null.
- Merges still need an explicit owner answer; a goal alone never unlocks
  them.

From outside (survey; strength as tagged there):
- Measured: cross-agent PR pairs conflict 41.7% of the time when they
  overlap (19.8% within one agent) — arXiv 2607.04697, 33.6k agent PRs.
- Measured, vendor: multi-agent runs use ~15x the tokens of chat;
  Anthropic's 90.2% multi-agent gain was on research, and it says coding
  has fewer truly parallel tasks.
- Expert judgment: Cognition (2026-04) — parallel writers still don't
  work; one writer at a time, a fresh-context reviewer, and a manager with
  child agents do.
- Vendor telemetry (secondary): AI lifts PR count ~98% and review time
  ~91% with no company-level delivery gain.
- Anecdote: an open request (anthropics/claude-code#95190) for setting
  model and effort on orchestrator-spawned sessions — the owner's exact
  model-control pain. The last-30-days community sweep found tool launches
  and no one reporting a measured orchestrator win.

No controlled study shows multi-agent orchestration improving coding
outcomes; that absence is recorded, not read as proof against.

## Solution hunch

A thin conductor over what already exists rather than a new swarm: it
takes a batch of issues, reserves shared numbers and versions before
dispatch, briefs each item with a model, effort level and context budget,
reuses `autorun` and `work-queue` for the work itself, keeps writes to a
shared file single-threaded, queues decisions back to the owner one at a
time, and drives merges in order (possibly through the merge queue
ADR-0070 already chose). Measured against today's `/goal` session.

## Success in one sentence

The owner files a batch of issues, answers a handful of decision questions
one at a time, and gets the issues back merged or blocked-with-reason
without driving a live session — each piece of work on the cheapest model
that meets the bar, with the cost known up front.

## Unknowns & risks

- **Review bottleneck (owner's top risk).** More output does not speed up
  the gates that need the owner — ADR-0033/0036 merge and ADR gates, the
  merge-permission classifier, eval honesty. The queue may just move from
  "issues waiting for a session" to "PRs and questions waiting for the
  owner"; the survey's review-time evidence points the same way.
- **Coordination cost.** Multi-agent work costs ~4–15x the tokens and
  loses context between agents; the saving from cheaper models has to
  outrun that.
- **Overlap and sprawl.** It could duplicate `autorun`, `work-queue` and
  the factory assembler, and the owner has named a habit of
  over-investing in tooling before shipping.
- **Platform churn.** Workflows and agent teams are previews; workflows
  take no mid-run human input, which is exactly where the owner's
  decisions sit.
- **Unverified:** whether turning on the already-decided merge queue
  (ADR-0070) alone removes much of the merge-ordering pain; the AdaptOrch and SWE-bench-style orchestrator
  claims; the agent-teams cost multiplier.
