# When a worker finishes: telemetry, the wall-clock bound, reconcile

Moved verbatim from [SKILL.md](../SKILL.md), which links here from the step
that needs it. A phrase such as "this file", "above", "below" or
"the Rules" can name SKILL.md or a part of it.

## Telemetry

A field the harness reports no usage for (tokens in and out, tool uses,
model tier, cost) is left empty and never estimated. A row without
usage is still written, with the fields it has (issue, outcome,
duration, PR). A duration the harness does not
report may be read from the issue's label-event timestamps, and is
reported as derived.

## Wall-clock bound

**Wall-clock bound.** At 45 minutes from dispatch the orchestrator sends
the worker one check-in asking for its status and its plan to stop. The
worker answers, then within 10 minutes commits what works and opens a
draft PR if anything is usable, or posts its evidence. A worker that
has not answered or ended 10 minutes after the check-in, or that the
harness cannot message, is stopped, counts as stalled and has its issue
reconciled below. Wall-clock is the portable bound: the `telemetry`
hook sees usage only after a worker finishes, so there is no spend
bound.

## Reconcile before Phase 4

**Reconcile before Phase 4.** A worker's `transition` can fail without
a trace, so the orchestrator checks it instead of trusting it. Skip
any issue a live worker still holds. For every other issue claimed this
session that still carries `in-progress` or no state label, read the
PRs that close it (`Closes #<N>` on the PR list) and run the
`transition` hook where the label disagrees with the table: an open PR
with green or pending gates → `has-pr` (the gate still runs); a draft
PR → `needs-review`; an open PR with red gates, a PR closed unmerged,
or no PR at all (unless the evidence outcome below applies) →
`agent-failed`. A worker that reported the evidence outcome and posted
its comment on the issue has no PR by design: its issue is
`needs-review`. One that reported the already-resolved outcome and
posted its evidence has none either: close its issue as
[lifecycle.md](lifecycle.md#already-resolved) says. An issue whose PR merged is
delivered: leave it to GitHub's close. Never remove a `hold_labels`
label or `stealable`, whatever the PR looks like: the gate put them
there on purpose. A worker resumed twice with no new commit counts as
stalled: stop it, do not resume it again, and reconcile its issue the
same way. Report each repair as drift, with the count of issues claimed
against the count repaired.
