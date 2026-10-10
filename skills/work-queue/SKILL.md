---
name: work-queue
description: Use when several ready work orders should be worked at once rather than one at a time — "drain the queue", "work the backlog in parallel", "run the ready work orders", "take the next few work orders", or a direct invocation. Plans a batch bounded by factory.json's wip_cap, prices it against the monthly cap before spending anything, then runs one worktree-isolated agent per work order and reports merge-ready PRs. It never merges; the human merge is gate 3 (ADR-0033). Not the router (next advances one run by one stage) and not autorun (one run, every stage, sequentially) — this is many work orders through one stage, concurrently. Requires work orders already at wo:ready-for-agent; when none are, it says which plane is holding each one back rather than reporting an empty queue.
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

One caveat to state plainly rather than let the output imply: the
month-to-date figure is only as good as what has been recorded, and until
recently **nothing wrote a ledger row when a run succeeded** (#222) — only
budget exhaustion did. Step 5 is what fixes that for this path, and it is
not optional bookkeeping: skip it and the next batch prices against a
total it knows is wrong. Runs dispatched through the cloud fallback still
record nothing, so a month that mixed both paths reads low.

### 3. Claim the batch before spending anything

For every work order the planner returned:

    make wo-in-progress ISSUE=<n>

`wo:ready-for-agent -> wo:in-progress`, through the lifecycle machine, one
issue at a time. This is not bookkeeping. Until the claim lands the
dispatch plane still reads the order as available, and three things act on
that: a second `work-queue` session picks the same orders, the gate digest
counts them as waiting rather than in flight, and the ready label stays
armed for `assembler.yml`. The claim is what makes "one session at a time"
a fact instead of a request.

A claim that will not flip is a refusal for that work order — drop it from
the batch and report it. Never dispatch an agent against an order the
dispatch plane did not agree to hand over.

### 4. Run the batch in parallel

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
5. The PR body follows the protocol's Pull request body section
   (`../../docs/pipeline-protocol.md`), with item 2's `Closes #N` line
   and the work-order id citation detector B reads kept first.
6. Confirm the branch base is the remote's default-branch tip before
   writing anything, and reset onto that tip if it is not.
7. Merge or rebase the remote's default-branch tip into the branch before
   declaring done, so the branch applies cleanly to the tip as of hand-off.
8. **Open a PR and stop.** Do not merge. Do not approve. Do not apply
   `wo:merged`.
6. **Say what it doubts.** Finished work it is unsure of goes in a
   `## Concerns` section of the PR body, one line per doubt, rather than
   shipping as if it were certain. Unfinished work escalates instead.

Model per work order follows `factory.json`'s routing bands — mechanical
work does not need the implementation model.

### 5. Report — and stop at the gate

Report per work order: the PR, whether `make check` passed inside the
worktree, the budget it actually used, and any concerns its PR raised.
A PR with concerns is reported with them, never as a clean result.

Then record that spend, once per work order:

    python3 budget_guard.py record <WO-####> <run-id> <model> <tokens> <cost>

The numbers come from the harness's own report of that subagent's usage.
Never estimate them, never round them to something plausible, and never
record a run that did not happen — this is an append-only ledger under the
same honesty rule as `evals/results/`, and a line written to make a total
look right is worse than the missing line it replaces. `record` refuses a
malformed row and a `(wo, run_id)` it has already seen, both *before* the
append, so a retry cannot double-count; a refusal is a stop, not a prompt
to try different numbers.

Then stop.

**Never merge.** The merged PR is the human approval record (ADR-0033
gate 3) and required code-owner review is what makes it one. An agent
merging its own work erases the only gate the factory has. The same rule
covers approving the PR, applying `wo:merged` by hand, and re-running a
failed check until it passes.

A work order whose agent produced nothing usable is **released**, not
just reported:

    make wo-failed ISSUE=<n>

An order left on `wo:in-progress` after its agent died is the exact bug
ADR-0045's writer exists to prevent — the digest counts it as work in
flight forever and no sweep will ever free it. The claim in step 3 is what
makes this leg mandatory: having taken the order out of the queue, this
skill owes it a terminal state.

Do not retry inside the round. A second attempt at the same work order is
a human's call, because the first failure is evidence about the order —
an under-specified row, a stale blocker, a missing `Accept:` — at least as
often as it is evidence about the agent.

**Circuit breaker: three consecutive agent failures ends the round.**
Release each claimed order, report, and stop. Past three, the common cause
is the tree or the queue rather than any one work order, and the next
agent buys nothing but another failure at full price.

### 6. Cloud fallback

When the local harness cannot run agents — no worktree support, or the
work must happen unattended — the same batch can be dispatched by the
shipped assembler instead. Choose this **before** step 3, because the
assembler does its own claim: leave `wo:ready-for-agent` in place and
re-apply it to each planned issue, and `assembler.yml` resolves, claims,
and dispatches one order per label event. Steps 3 through 5 are then the
workflow's job, not yours.

That path is serial per label event and depends on GitHub Actions, so
prefer local. Say which path a run used either way — the two are not
distinguishable after the fact from the artifacts alone, and the cloud leg
still records no spend on success (#222), so the ledger will not answer it
for you.

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
- Every order this skill claims gets a terminal state before the round
  ends — a PR, or `wo:failed`. Claiming is a debt.
- One session at a time, and the claim in step 3 is what enforces it. Two
  concurrent sessions racing the same queue is the failure this ordering
  exists to prevent.
- Two orders in one batch may still touch the same files. There is no
  merge train here to tax — nothing merges — so the cost lands as a
  conflict the human resolves at merge time, not as re-run CI. Say which
  PRs overlap in the report rather than pretending the batch was disjoint.
- Report the deferrals. "Nothing to do" without them is indistinguishable
  from a broken queue.
