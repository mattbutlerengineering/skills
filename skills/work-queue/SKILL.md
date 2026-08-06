---
name: work-queue
description: Use when several ready work orders should be worked at once rather than one at a time — "drain the queue", "work the backlog in parallel", "run the ready work orders", "take the next few work orders", or a direct invocation. Plans a batch bounded by factory.json's wip_cap, prices it against the monthly cap before spending anything, then runs one worktree-isolated agent per work order and reports merge-ready PRs. It never merges: the human merge is gate 3 (ADR-0033). Not the router (next advances one run by one stage) and not autorun (one run, every stage, sequentially) — this is many work orders through one stage, concurrently. Requires work orders already at wo:ready-for-agent; when none are, it says which plane is holding each one back rather than reporting an empty queue.
---

# Work Queue

Run several ready work orders in parallel, each in its own worktree, and
stop at merge-ready PRs.

The queue is **opt-in by construction**. A work order is eligible only
when both planes agree (ADR-0032): its breakdown row is unchecked with
every `blocked by:` edge satisfied, *and* its mirrored issue carries
`wo:ready-for-agent` — the label only the repo owner applies. There is no
mode that works "everything not done yet".

## Process

### 1. Preflight

- `git status` is clean and you are on an up-to-date default branch.
- `make check` passes. A red tree is the work; fixing it beats starting
  three new things on top of it.
- Open PRs come before new work. An unfinished PR is closer to value than
  a fresh work order, and merging it first is what keeps the batch's
  branches from stacking conflicts.

### 2. Plan the batch — never by hand

    python3 work_queue.py plan          # or tools/factory/work_queue.py

The planner owns every selection rule: eligibility across both planes,
`blocked by:` edges, `wip_cap`, cheapest-band-first ordering, and pricing
each `size:` band against month-to-date ledger spend and `monthly_cap_usd`
(ADR-0034). Read its output; never re-derive a decision it already made,
and never widen the batch past what it returned.

Its deferral lines are the useful half when the batch is empty. Each one
names the plane that is holding a work order back — an unmet blocker, a
row with no `(tracker: #N)` mirror, an issue without the ready label, the
wip cap, or the monthly cap. Report them; an empty queue and a mis-wired
queue must never read the same.

`wq:` problems are refusals, not warnings. Stop on them.

### 3. Run the batch in parallel

One agent per work order, **all dispatched in a single message** so they
run concurrently, each with `isolation: "worktree"` — they will write to
the same paths otherwise, and the whole point of the cap is that this many
can run without colliding.

Each agent's prompt must carry:

1. The work order id, its breakdown row, and its `Accept:` criteria — the
   row is the scope, and anything outside it belongs to another order.
2. Its mirrored issue number, for `Closes #N` in the PR body.
3. The repo's own conventions: write the failing test first, then the
   implementation; `make check` must pass before it declares itself done.
4. Its dollar budget from the plan, and the ADR-0034 rule that exhausting
   it means stopping and handing off, never quietly continuing.
5. **Open a PR and stop.** Do not merge. Do not approve. Do not apply
   `wo:merged`.

Model per work order follows `factory.json`'s routing bands — mechanical
work does not need the implementation model.

### 4. Report — and stop at the gate

Report per work order: the PR, whether `make check` passed inside the
worktree, and the budget it actually used. Then stop.

**Never merge.** The merged PR is the human approval record (ADR-0033
gate 3) and required code-owner review is what makes it one. An agent
merging its own work erases the only gate the factory has. The same rule
covers approving the PR, applying `wo:merged` by hand, and re-running a
failed check until it passes.

A work order whose agent produced nothing usable is reported as failed,
with the reason. Do not silently retry it into the next batch.

### 5. Cloud fallback

When the local harness cannot run agents — no worktree support, or the
work must happen unattended — the same batch can be dispatched by the
shipped assembler instead: apply `wo:ready-for-agent` to the planned
issues and let `assembler.yml` claim each one. That path is serial per
label event and depends on GitHub Actions, so prefer local; say which
path you used, because the cost ledger records them the same way and the
run evidence should not be ambiguous.

## Rules

- The planner decides the batch. This skill executes it and never
  second-guesses, widens, or reorders it.
- Never merge, approve, or advance a lifecycle label past
  `wo:needs-review`. Opening the PR is the end of the job.
- One work order per agent, one worktree per agent. Two agents in one tree
  is a conflict generator, not parallelism.
- Never create a `WO-####` issue, and never write a breakdown row, to make
  something eligible. The mirror is one-way (ADR-0032); if the queue is
  empty, that is an answer.
- Report the deferrals. "Nothing to do" without them is indistinguishable
  from a broken queue.
