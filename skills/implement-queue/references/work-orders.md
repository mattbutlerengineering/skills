# Work orders: implement-queue under `source: work-orders`

This page holds what changes when the queue drains factory work orders
instead of plain `ready` issues. Its source is the queue profile's
`source: work-orders`, or an invocation that asks for work orders, which
overrides the profile for that run. Everything not named here runs as
SKILL.md says. This page replaced the `work-queue` skill (ADR-0127).

The queue is **opt-in by construction**. A work order is eligible only
when both planes agree (ADR-0032): its breakdown row is unchecked with
every `blocked by:` edge satisfied, *and* its mirrored issue carries
`wo:ready-for-agent`, a label only the repo owner applies. No mode works
"everything not done yet".

**This mode never merges.** `source: work-orders` forces `merge: off`,
whatever the profile's `merge:` says. The merged PR is the human
approval record (ADR-0033 gate 3), and required code-owner review is what
makes it one. An agent merging its own work erases the only gate the
factory has. The same rule covers approving the PR, applying `wo:merged`
by hand, and re-running a failed check until it passes. Phase 3 still
updates branches that fell behind or conflict. It never merges one.

## Pre-flight

SKILL.md's Phase 0 applies. In addition, `git status` must be clean on an
up-to-date default branch, and `make check` must pass. A red tree is the
work, and fixing it beats starting three new things on top of it.

## Plan the batch, never by hand

    python3 work_queue.py plan          # or tools/factory/work_queue.py

This replaces Phase 1's issue list, priority sort and `max_workers`. The
planner owns every selection rule: eligibility across both planes,
`blocked by:` edges, `wip_cap`, cheapest-band-first ordering, and pricing
each `size:` band against month-to-date ledger spend and `monthly_cap_usd`
(ADR-0034). Read its output. Never re-derive a decision it already made,
and never widen or reorder the batch it returned.

Its deferral lines are the useful half when the batch is empty. Each one
names the plane that is holding a work order back: an unmet blocker, a
row with no `(tracker: #N)` mirror, an issue without the ready label, the
wip cap, or the monthly cap. Report them. An empty queue and a mis-wired
queue must never read the same.

`wq:` problems are refusals, not warnings. Stop on them.

The month-to-date figure is only as good as what has been recorded. Runs
dispatched through the cloud fallback record nothing on success (#222), so
a month that mixed both paths reads low. Say so rather than let the output
imply otherwise.

## Claim before spending anything

For every work order the planner returned:

    make wo-in-progress ISSUE=<n>

`wo:ready-for-agent -> wo:in-progress`, through the lifecycle machine, one
issue at a time. Until the claim lands, the dispatch plane still reads the
order as available. A second queue session would pick the same orders,
the gate digest would count them as waiting rather than in flight, and
the ready label would stay armed for `assembler.yml`. The claim is what
makes "one session at a time" a fact instead of a request.

A claim that will not flip is a refusal for that work order. Drop it from
the batch and report it. Never dispatch an agent against an order the
dispatch plane did not agree to hand over.

In this mode the `wo:*` lifecycle labels replace SKILL.md's Labels table.

## Worker brief

This replaces SKILL.md's Worker brief. Dispatch still happens in one
message, one worktree per worker. Each worker's prompt must carry:

1. The work order id, its breakdown row, and its `Accept:` criteria. The
   row is the scope, and anything outside it belongs to another order.
2. Its mirrored issue number, for `Closes #N` in the PR body.
3. The repo's own conventions: write the failing test first, then the
   implementation; `make check` must pass before it declares itself done.
4. Its dollar budget from the plan, and the ADR-0034 rule that exhausting
   it means stopping and handing off, never quietly continuing.
5. The PR body follows the protocol's Pull request body section
   (`../idea-to-prod-runtime/docs/pipeline-protocol.md`, relative to this skill's base
   directory), with item 2's `Closes #N` line and the work-order id
   citation detector B reads kept first.
6. Confirm the branch base is the remote's default-branch tip before
   writing anything, and reset onto that tip if it is not.
7. Merge or rebase the remote's default-branch tip into the branch before
   declaring done, so the branch applies cleanly to the tip as of hand-off.
8. **Open a PR and stop.** Do not merge. Do not approve. Do not apply
   `wo:merged`.
9. **Say what it doubts.** Finished work it is unsure of goes in a
   `## Concerns` section of the PR body, one line per doubt, rather than
   shipping as if it were certain. Unfinished work escalates instead.
10. Stay inside your worktree. Stop only processes you started, by PID;
    never `pkill -f` or `killall`, which match machine-wide. Never run
    `git stash`, `git gc` or `git worktree prune`: they act on state
    shared by every worktree of the repo. After any investigative
    checkout (a bisect, `git checkout <sha> -- <paths>`) restore the
    worktree to a clean state, confirm it with `git status --porcelain`
    and `git diff`, and say so in the result.
11. Say in the result which checks were not verified locally: list under
    `not verified locally` every CI check the PR will face that you did
    not or could not run, each with the reason.

Model per work order follows `factory.json`'s routing bands. Mechanical
work does not need the implementation model.

## Report and release

Report per work order: the PR, whether `make check` passed inside the
worktree, the budget it actually used, and any concerns its PR raised.
A PR with concerns is reported with them, never as a clean result. Two
orders in one batch may still touch the same files; name the PRs that
overlap rather than pretending the batch was disjoint.

Then record that spend, once per work order:

    python3 budget_guard.py record <WO-####> <run-id> <model> <tokens> <cost>

The numbers come from the harness's own report of that worker's usage.
Never estimate them, never round them to something plausible, and never
record a run that did not happen. This is an append-only ledger under the
same honesty rule as `evals/results/`. `record` refuses a malformed row
and a `(wo, run_id)` it has already seen, both *before* the append, so a
retry cannot double-count. A refusal is a stop, not a prompt to try
different numbers. Skipping this step makes the next batch price against
a total it knows is wrong.

A work order whose worker produced nothing usable is **released**, not
just reported:

    make wo-failed ISSUE=<n>

An order left on `wo:in-progress` after its worker died is the bug
ADR-0045's writer exists to prevent: the digest counts it as in flight
forever and no sweep frees it. Every order this mode claims gets a
terminal state before the round ends, a PR or `wo:failed`. Claiming is a
debt.

Do not retry inside the round. A second attempt at the same work order is
a human's call, because the first failure is evidence about the order (an
under-specified row, a stale blocker, a missing `Accept:`) at least as
often as it is evidence about the agent. SKILL.md's three-failure circuit
breaker still ends the round; release each claimed order first.

Never create a `WO-####` issue, and never write a breakdown row, to make
something eligible. The mirror is one-way (ADR-0032). An empty queue is an
answer.

## Cloud fallback

When the local harness cannot run agents (no worktree support, or the
work must happen unattended), the shipped assembler can dispatch the same
batch. Choose this **before** claiming, because the assembler does its
own claim: leave `wo:ready-for-agent` in place and re-apply it to each
planned issue, and `assembler.yml` resolves, claims and dispatches one
order per label event. Claiming, the workers and the report are then the
workflow's job.

That path is serial per label event and depends on GitHub Actions, so
prefer local. Say which path a run used either way. The two cannot be told
apart afterwards from the artifacts alone, and the cloud leg records no
spend on success (#222).
