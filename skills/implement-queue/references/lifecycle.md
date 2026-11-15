# The backlog's lifecycle edges

The queue claims only `ready` issues, so an issue that leaves `ready`
and never comes back is invisible to it. A queue can then report
"nothing to claim" pass after pass while the backlog grows (#1796).
This file owns the three edges the queue itself creates or depends on:
an issue resolved with no change, a `has-pr` issue that outlived its
PR, and an issue that never had a state label. It files no new
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
  decision, not a failure: returning it to `ready` would spend a worker
  and a CI run on every pass, and the Owner would close each PR again
  (#1801).
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

Phase 4's report carries both counts, as
"N open issues with no state label, M stale `has-pr` (K returned to
`ready`, J held at `needs-review`)", even when the batch is empty:
"nothing to claim" is never to be read as "backlog empty".

## The `promote` hook

The profile may name a command or rule that labels well-specified,
unblocked issues with no state label `ready`. Phase 1 runs it at most
once per iteration, and only when fewer than `max_workers` issues are
left after the drops, then lists and drops again. A promoted issue is
an ordinary `ready` issue from then on: it goes through every drop and
[the claim step](claim.md). With no `promote` hook nothing is promoted,
and the step 5 count is the report.
