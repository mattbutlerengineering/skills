# The claim step

The one way any driver takes a `ready` issue in a repo that runs this
queue (ADR-0130).
The queue runs it in Phase 1 for each issue of its batch. Any other
driver that picks up `ready` issues in the same repo, a scheduled
routine, a loop, a drain script or an Owner's session, runs the same
steps before it starts work on an issue. Starting work means
dispatching a worker, cutting a branch, or spending anything on the
issue. A driver that claims this way is visible to the queue: its issue
leaves `ready` and carries `in-progress`, so the queue's Phase 1 drops
it, its Phase 0 step 4 lists it and never touches it, and the files of
its open PR count against the queue's batch.

Labels are those of the [Labels table](../SKILL.md#labels). Commands
are the target repo's queue profile hooks
([the queue profile](../SKILL.md#the-queue-profile)) where it has them,
else the defaults there. Under `source: work-orders` the `wo:*` claim
in [work-orders.md](work-orders.md) replaces this file.

## What may be claimed

An issue the queue's Phase 1 drop list drops is not claimable by any
driver. For a driver other than the queue, "an issue already taken in
this batch" in that list reads as an issue this driver holds.

## The claim transition

For the claim transition only, the removal of `ready` comes first and
the add of `in-progress` follows; every other
transition keeps the `transition` hook's order. Run the steps below as
written even when the profile's `transition` hook is one swap command.
Read `gh api -i repos/{owner}/{repo}/issues/<N>` just before the claim:
if `ready` is gone or `in-progress` is already there, another session
took it, so skip the issue and never touch its labels. Note the
whole-second time in that response's `Date` header, which is GitHub's
clock. Read the issue's timeline with
`gh api repos/{owner}/{repo}/issues/<N>/timeline --paginate --jq '.[] | select(.event == "labeled") | [.label.name, .created_at, .actor.login] | @tsv'`
to take the time of its last `ready` labeled event; when the timeline
cannot be read, or holds no `ready` labeled event, claim nothing for
it. Then remove `ready` with
`gh api -X DELETE repos/{owner}/{repo}/issues/<N>/labels/ready`. Hold
the claim only on a 200. On any other status, a 404 included (the
documentation gives it for a label that does not exist, which this
session takes to mean another session removed `ready` first), skip the
issue, never touch its labels and report it. This claim narrows the race
window and is not a lock: the documentation gives a 404 only for a label
that does not exist, so if two removals both returned 200 two sessions
would each hold the claim. The queue's Rules keep one queue session per
repo at a time; between drivers the label claim is a best-effort mutex
that makes a collision unlikely and detectable by the secondary check.
Then add `in-progress` with
the `transition` hook's add. Start no work before that 200 and the
add of `in-progress`. A failed add means this session won the removal
but holds no complete claim: start no work on that issue, skip it and
report it for the Owner, since it then has neither state label. After
the add, read the timeline again
with the same command and confirm, as a secondary check, exactly one
`in-progress` labeled event since the last `ready` labeled event, whose
`created_at` is at or after the time noted, comparing whole seconds, which
shows only that the event was created after this session's read. There
is no MCP twin for the removal,
the `Date` read or the timeline read, so a session with no `gh` cannot
run this check and must claim nothing. On an unreadable timeline after
the add, skip the issue, start no work on it, leave the label as
it is and report it. With no `in-progress` labeled event after the add
(the timeline lags, or the transition failed), skip the issue, start
no work on it, leave the label as it is and report it. With two or
more `in-progress` labeled events, or one whose `created_at` is earlier
than the time noted, this session lost the race, so skip the issue,
start no work on it, leave the label as it is and report it. Never
move the issue back to `ready` after a lost race, because the session
that holds it may already have started work. An issue skipped here is
not claimed by this session, so the queue's Reconcile before Phase 4
leaves it alone, a looping session's Phase 0 step 4 does not subtract
it, and the report names it for the Owner to free. An open issue with no
queue state label that was last labelled by a claim attempt, after a
failed add or a session that died, is stuck and fails closed, and the
Owner frees it by adding `ready`. An issue left with `in-progress` by
two sessions that both skipped is freed by removing `in-progress` and
adding `ready`.

## While a driver other than the queue holds the claim

- Its PR closes the issue (`Closes #<N>`) and ends its body with the
  line `Driver: <name>`, the driver's own name. The queue's Phase 0
  step 3 reads that line: a PR whose `Driver:` line names another
  driver is foreign to the queue whatever its issue's labels, so the
  queue never fixes, re-runs or updates it, and its failure never
  blocks the queue's claiming. A PR closing an `in-progress` issue with
  no `Driver:` line is the queue's.
- When it finishes with the issue it labels it by the queue's worker
  outcome table ([Worker brief](../SKILL.md#worker-brief)) with the
  `transition` hook. A driver that stops before starting work moves the
  issue from `in-progress` back to `ready`. It never leaves
  `in-progress` on an issue it no longer works.

## The zone lock

Before a driver touches an open PR's branch (an `update-branch`, a
rebase, a push other than its own worker's) or merges it, it takes the
profile's `lock` hook lock for the PR's zone, as the queue's Phase 3
step 2 does, and releases every lock it took when it is done, on any
exit. If another session holds it, the driver leaves that zone alone and
reports it. With no `lock` hook there is no zone lock, and the label
claim above is the only coordination between drivers. A lock kept in
the local git common dir cannot be seen by a cloud session, so a repo
whose drivers run in the cloud names a lock both can read, or has
none.
