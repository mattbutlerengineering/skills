# The issue-tracker bridge is an opt-in one-way mirror

- Status: accepted
- Date: 2026-07-03

Work that lives in an issue tracker could not reach a run: Decompose's
breakdown is checkboxes in a file, tracker issues never seed a run, and
work filed while a session was closed is invisible to the pipeline. The
tempting fix — letting orientation read tracker state — would create a
second source of truth and break resume-after-close whenever the tracker
is unreachable, weakening ADR-0004.

Decision: the bridge is an **opt-in, one-way mirror** that syncs only at
stage boundaries:

- **Import at run seeding** — existing tracker issues become work items in
  the breakdown artifact, each recording its originating issue reference.
- **Export at Decompose** — the breakdown's work items may optionally be
  published as tracker issues, with the item-to-issue mapping recorded in
  the breakdown artifact.
- **Close at Implement item boundaries** — completing a work item closes
  its mirrored issue.

No background sync, no webhooks, and **orientation never reads tracker
state** — the artifacts remain the single source of truth
(ADR-0004 unweakened); the tracker is a mirror, never the state. The
shared protocol carries only the mirror conventions (issue references on
work items, close-at-item-boundary); no tracker CLI is named in skill
process text, preserving harness neutrality — tracker specifics live in
packaging-facing text only. On a bare install without a tracker, nothing
changes: the bridge is strictly opt-in.
