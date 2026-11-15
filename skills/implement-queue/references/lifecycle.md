# The backlog's lifecycle edges

The queue claims only `ready` issues, so an issue that leaves `ready`
and never comes back is invisible to it. A queue can then report
"nothing to claim" pass after pass while the backlog grows (#1796).
This file owns the edges the queue itself creates or depends on: an
issue resolved with no change, a `has-pr` issue that outlived its PR,
an issue that never had a state label, an `agent-failed` issue, and an
`in-progress` claim its session never released. It files no new
findings: discovery still feeds the queue (the Rules).

Labels are those of the [Labels table](../SKILL.md#labels). The
cloud twins of every command here are in
[cloud-sessions.md](cloud-sessions.md).

## Already resolved

A worker that finds its issue already fixed on `main`, by a merged PR
or a measurement anyone can repeat, posts that evidence on the issue,
opens no PR and reports the already-resolved outcome
([worker brief](worker-brief.md) item 9). The orchestrator closes the
issue: it removes `in-progress` with the `transition` hook, then runs
`gh issue close <N> --reason completed`. It closes only once the
evidence comment is on the issue. A worker that reports the outcome
with no comment posted is the "No usable change" row. A wrong close is
cheap to undo, since the Owner reopens it with the evidence beside it.
An open issue with no state label leaks out of the queue for good.

## Phase 0 step 5: count the leaks

Run after step 4, every iteration, before Phase 1.

**Stale `has-pr`.** List the open issues carrying `has-pr`:
`gh issue list --label has-pr --state open --limit 1000 --json number`.
Skip any issue whose PR is in this session's gate or train. For each
of the others, read the PRs that refer to it from its timeline:

    gh api repos/{owner}/{repo}/issues/<N>/timeline --paginate --jq '.[] | select(.event == "cross-referenced" and .source.issue.pull_request != null and .source.issue.repository.full_name == "{owner}/{repo}") | [.source.issue.number, .source.issue.state, (.source.issue.pull_request.merged_at // "-")] | @tsv' | sort -u

A PR appears once per event that references the issue, so `sort -u`
leaves one row per PR, and every count below counts distinct PR
numbers. The timeline catches a PR that only `Refs` the issue, which a
closing-reference read misses. It also catches a PR that only mentions
the issue, so every reading below errs toward leaving the label alone:

- An open PR: not stale. Leave it.
- No open PR, and at least one merged: report it as stale with the
  merged PR. The merged work may be partial or may have meant to close
  it; that is the Owner's call, so change nothing.
- Every PR closed unmerged: apply
  [the closed-unmerged rule](#a-pr-closed-unmerged) below, from
  `has-pr`.
- No PR at all, or a timeline that cannot be read: report it, change
  nothing.

Never remove a `hold_labels` label or `stealable` here; a returned
issue that carries one is still dropped by Phase 1.

### A PR closed unmerged

One rule decides an issue whose referring PRs all closed unmerged,
wherever the queue meets it: step 5 here, and the
[reconcile before Phase 4](worker-finish.md#reconcile-before-phase-4),
which defers to it. Count the distinct PRs the timeline read above
lists as closed with no merge time (`-`), every session's, not only
this one's. A PR that only mentions the issue still counts: an
over-count can only hold the issue for a human, never spend a worker,
so the error falls on the cheap side:

- Exactly one: run the `transition` hook to `ready`, and report it as
  returned. One closed attempt earns one more.
- Two or more: run the `transition` hook to `needs-review`, and report
  it with its closed PRs. A second closed PR reads as the Owner's
  decision, not a failure to retry, though it still counts toward
  Phase 4's three-consecutive-failures stop: returning it to `ready`
  would spend a worker and a CI run on every pass, and the Owner would
  close each PR again (#1801).
- A timeline that cannot be read: the count is unknown. Step 5 changes
  nothing and reports it; the reconcile, which must not leave
  `in-progress` behind, runs the `transition` hook to `agent-failed`
  and reports it, as for no PR at all.

**No state label.** Count the open issues that carry none of the
Labels table's labels, no `hold_labels` label and no `wo:*` label:
`gh issue list --state open --limit 1000 --json number,labels`. A
count that reaches the limit is reported as "at least" that count.
Count only; this queue never labels them. The `promote` hook below is
the one way one of them becomes `ready` here.

**`agent-failed`.** Count the open issues carrying `agent-failed`:
`gh issue list --label agent-failed --state open --limit 1000 --json number`.
A count that reaches the limit is reported as "at least" that count.
Count only: nothing here returns one to `ready`
([the second failure](#agent-failed-and-the-second-failure) says who
does).

**Stale `in-progress`.** The stale bound is **24 hours**. Take
[step 4](preflight.md#step-4-another-queue-session)'s list: the open
`in-progress` issues this session did not claim, each with its claim
time (when `in-progress` was last applied). The
[reconcile](worker-finish.md#reconcile-before-phase-4) owns the ones
this session claimed. Count an issue as stale when its claim time is
older than the stale bound and the timeline read under **Stale `has-pr`** lists
no open PR for it. An open PR, or a claim time or timeline that cannot
be read, is not counted: the count errs toward leaving another
session's claim alone. Count only, as step 4 says: never relabel
another session's `in-progress` issue.

Phase 4's report carries all four counts, as
"N open issues with no state label, M stale `has-pr` (K returned to
`ready`, J held at `needs-review`), F `agent-failed`, S stale
`in-progress`", even when the batch is empty: "nothing to claim" is
never to be read as "backlog empty".

## `agent-failed` and the second failure

Nothing in this skill moves an `agent-failed` issue back to `ready`;
returning one requires a human, who relabels it `ready`, usually after
sharpening the issue. Step 5 counts the ones nobody has returned yet.
The Outcome table's "Second failure on the same issue" row applies
only on the worker-outcome path: when a worker's outcome is "No usable
change" and the issue's timeline already shows an `agent-failed`
labeled event (any line from
`gh api repos/{owner}/{repo}/issues/<N>/timeline --paginate --jq '.[] | select(.event == "labeled" and .label.name == "agent-failed") | .created_at'`),
the `transition` hook then sets `stealable` instead of `agent-failed`.
A worker on an issue with no earlier `agent-failed` event takes the
"No usable change" row. So does one whose timeline cannot be read, or
a session with no `gh` (the GitHub MCP server has no timeline read):
without evidence of an earlier failure the queue sets `agent-failed`,
the less aggressive outcome, and never escalates to `stealable`.
Every other setter of `agent-failed` always sets it, earlier event or
not: [the reconcile](worker-finish.md#reconcile-before-phase-4), the
closed-unmerged rule's unreadable-timeline case above,
[Phase 0 step 3's `agent-failed` cause](preflight.md#step-3-failed-pr-causes-and-settled-green-prs)
and [the merge train's CI-fix issue](merge-train.md).
A second closed PR is not this row: it follows
[the closed-unmerged rule](#a-pr-closed-unmerged).

## The `promote` hook

The profile may name a command or rule that labels well-specified,
unblocked issues with no state label `ready`. Phase 1 runs it at most
once per iteration, and only when fewer than `max_workers` issues are
left after the drops, then lists and drops again. A promoted issue is
an ordinary `ready` issue from then on: it goes through every drop and
[the claim step](claim.md). With no `promote` hook nothing is promoted,
and the step 5 count is the report.
