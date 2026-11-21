# Work orders: implement-queue under `source: work-orders`

This page holds what changes when the queue drains factory work orders
instead of plain `ready` issues. Its source is the queue profile's
`source: work-orders`, or an invocation that asks for work orders, which
overrides the profile for that run. Everything not named here runs as
SKILL.md says. This page replaced the `work-queue` skill (ADR-0127).

The queue is **opt-in by construction**. A work order is eligible only
when both planes agree (ADR-0032): its breakdown row is unchecked with
every `blocked by:` edge satisfied, *and* its mirrored issue carries
`wo:ready-for-agent`, a label only the repo owner applies. The planner
checks who applied it: the latest labeled event's actor must be the repo
owner, so anyone else's label is inert, and a labeler it cannot read
holds the order back. No mode works "everything not done yet".

**This mode never merges.** `source: work-orders` forces `merge: off`,
whatever the profile's `merge:` says. The merged PR is the human
approval record (ADR-0033 gate 3), and required code-owner review is what
makes it one. An agent merging its own work erases the only gate the
factory has. The same rule covers approving the PR, applying `wo:merged`
by hand, and re-running a failed check until it passes. Phase 3 still
updates branches that fell behind or conflict. It never merges one.

Phase 0's single re-run of a red check, once per head SHA and only when
the log shows an infrastructure cause ([preflight.md](preflight.md) steps
2 and 3), still applies in this mode. It is not re-running until it
passes: a second red on the same head stands as a failure, and nothing
re-runs it again.

## Pre-flight

SKILL.md's Phase 0 applies. In addition, `git status` must be clean on an
up-to-date default branch, and `make check` must pass. A red tree is the
work, and fixing it beats starting three new things on top of it.

### Which open PRs are this queue's

Phase 0 step 3 reads SKILL.md's issue labels to decide which open PRs
belong to this queue. A work order's issue never carries them, so in
this mode the rule reads the `wo:*` labels instead: a PR belongs to this
queue when it closes an issue carrying `wo:in-progress`,
`wo:needs-review` or `wo:failed` *and* its body carries the line
`Driver: implement-queue` (Worker brief item 5 below), wherever it
sits, so a `## Concerns` section after it does not make the PR foreign.
The `Driver:` line is required here, not merely uncontradicted, because
the cloud fallback's assembler claims through the same labels and its
PRs are not this queue's. Every other PR is foreign, and step 3 treats it as
foreign. Everything else step 3 does with a PR of this queue still
applies: green ones go to the gate, failed ones block claiming until
released.

A failed PR of this queue, from this round or an earlier one, is not
given a second worker to make it green. After Phase 0's single
infrastructure re-run, a PR still red goes straight to `make wo-failed`.
This mode sets that rule because a second attempt at a work order is a
human's call. The only worker a PR of this queue gets after its first
is the reviewer gate's one same-branch fix after a first flag (Report
and release), which finishes the same attempt. Phase 3's branch updates
are not a worker and still apply.

Where step 3 would label a failed PR's issue `agent-failed`, this mode
runs `make wo-failed ISSUE=<n>` instead and never applies
`agent-failed` to a work order's issue. The `agent-failed` cause in
[preflight.md](preflight.md#step-3-failed-pr-causes-and-settled-green-prs)
reads `wo:failed` in its place. A failed PR of this queue whose issue
carries `wo:failed` is not fixed or re-run again. It is reported, with
its failing job linked, for a human to close or take over, and it does
not block claiming.

So Phase 0 can put `wo:failed` on an order whose PR is still open,
while [Reconcile in this mode](#reconcile-in-this-mode) treats an open
PR as the terminal state. The two do not conflict: Reconcile runs at a
round's end on orders still on `wo:in-progress` or with no `wo:*`
label, and `make wo-failed` goes through the lifecycle machine either
way.

## Plan the batch, never by hand

    python3 tools/work_queue.py plan          # or tools/factory/work_queue.py

This replaces Phase 1's issue list, priority sort and `max_workers`. The
planner owns every selection rule: eligibility across both planes, the
owner-only ready label, `blocked by:` edges, `wip_cap`, cheapest-band-first
ordering, and pricing each `size:` band against month-to-date ledger spend
and `monthly_cap_usd` (ADR-0034). Orders already on `wo:in-progress` count
against both caps: each holds a `wip_cap` slot, and its band's budget is
added to the month's spend before any new order is priced, because the
ledger records a run only once it ends. Read its output. Never re-derive a
decision it already made, and never widen or reorder the batch it
returned.

Its deferral lines are the useful half when the batch is empty. Each one
names the plane that is holding a work order back: an unmet blocker, a
row with no `(tracker: #N)` mirror, an issue without the ready label, a
ready label someone other than the owner applied, an order already in
flight, the wip cap, or the monthly cap. Report them. An empty queue and
a mis-wired queue must never read the same.

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
   citation detector B reads kept first. End the body with the line
   `Driver: implement-queue`, as SKILL.md's Worker brief item 5 says.
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
12. Run every subprocess in the foreground under a time bound
    (`timeout 600 <cmd>` or the tool's own timeout; state a longer bound
    for a slow step). Never start a background or watch process and wait
    on it. A command that hits its bound is killed and its output
    recorded, never retried unchanged. Stall-abort: after two resumes
    without a new commit, or two resumes that each hit a bound, stop:
    commit what works, open a draft PR if anything is usable, and report
    the blocking command.
13. Evidence outcome: when no repo change can fix the order (for example
    a scheduled routine that never fired), post the evidence on the
    issue, open no PR and report the evidence outcome. Already-resolved
    outcome: when the order is already fixed on the default branch, post
    the merged PR or a repeatable measurement on the issue, open no PR
    and report the already-resolved outcome. Never invent a change to
    have something to push. Neither outcome closes the issue or checks
    the breakdown row; the orchestrator releases the order with
    `make wo-failed ISSUE=<n>` (Reconcile in this mode).
14. Finish or hand off within 45 minutes from dispatch, and answer the
    orchestrator's check-in at once.
15. Before opening the PR, check your diff against the four catch classes
    of the reviewer contract: hallucination (code that runs but does not
    do what the order asked), regression (tests removed or behaviour
    changed without a reason), gate bypass (lint, typecheck or test
    output misread as passing) and criteria gap (acceptance criteria
    skipped or met poorly). Check the diff against each acceptance
    criterion of the row's `Accept:` too, and list in the result each
    criterion with how you verified it. Change nothing the order does not
    ask for: a case found outside its row is named in the PR body, not
    implemented.

Model per work order follows `factory.json`'s routing bands. Mechanical
work does not need the implementation model.

## Report and release

Report per work order: the PR, whether `make check` passed inside the
worktree, the budget it actually used, and any concerns its PR raised.
A PR with concerns is reported with them, never as a clean result. Two
orders in one batch may still touch the same files; name the PRs that
overlap rather than pretending the batch was disjoint.

Then record that spend, once per work order:

    python3 tools/budget_guard.py record <WO-####> <run-id> <model> <tokens> <cost>   # or tools/factory/budget_guard.py

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

The reviewer gate's one same-branch fix after a first flag
([reviewer-contract.md](reviewer-contract.md), Retry policy) still
applies, because it finishes the same attempt on the same PR rather than
starting a second one. A second flag ends that attempt: the order is not
retried, and its PR is reported with the reviewer's output.

## Reconcile in this mode

This replaces the label mapping in
[Reconcile before Phase 4](worker-finish.md#reconcile-before-phase-4);
its other rules (check rather than trust, skip any order a live worker
still holds, reconcile a stalled worker's order, report each repair as
drift with claimed against repaired) still apply. For every order this
session claimed that still carries `wo:in-progress` or no `wo:*` label,
read the PRs that close its mirrored issue and give it the terminal state
"Claiming is a debt" requires:

- **An open PR, draft or ready, green, pending or red** → leave it. The
  PR is the terminal state. Report a draft or red one as such; Phase 0's
  single infrastructure re-run is the only re-run it gets. The PR-open
  leg (`make wo-needs-review`, from the PR event) writes
  `wo:needs-review`. An order still on `wo:in-progress` beside an open PR
  is drift to report, never a label to apply by hand. Report it with
  its repair route for a human to run, the dispatch shim
  `gh workflow run validator.yml -f pr=N`. The shim re-runs the whole
  validator for that PR (its check, review and label legs), not just
  the label flip. A red PR of this queue is
  still released in Phase 0 by
  [its own rule](#which-open-prs-are-this-queues).
- **A merged PR** → leave it. The PR-merge leg writes `wo:merged`, and
  this mode never applies it.
- **No PR at all**, including a worker that reported the evidence or
  already-resolved outcome and posted its comment → `make wo-failed
  ISSUE=<n>`. In this mode only a PR or `wo:failed` ends a claim, so the
  evidence comment is input to the human's retry decision, not a state.
  Never close the issue or check the breakdown row: both planes are a
  human's to move. SKILL.md's evidence and already-resolved outcomes
  apply in this mode as Worker brief item 13 defines them, and as in
  SKILL.md Phase 4 neither is a failure: a `wo:failed` from either
  leaves the three-failure circuit-breaker count unchanged. Only a
  worker that produced nothing usable counts.
- **No open or merged PR and at least one closed unmerged** →
  `make wo-failed ISSUE=<n>`. This replaces the
  [closed-unmerged rule](lifecycle.md#a-pr-closed-unmerged): under "Do
  not retry inside the round" the order is not returned to
  `wo:ready-for-agent`. The closed PR still counts as a failure toward
  SKILL.md's three-failure circuit breaker.

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
workflow's job. The assembler applies the same knowledge-plane check as
the planner: a label re-applied to an order whose row is checked off
dispatches nothing, and one on an order whose blockers are unmet or
unreadable fails the run so the owner sees it.

That path is serial per label event and depends on GitHub Actions, so
prefer local. Say which path a run used either way. The two cannot be told
apart afterwards from the artifacts alone, and the cloud leg records no
spend on success (#222).
