# Autorun brief — maintenance:gate-timeline-timestamp-trust

Collected 2026-08-23. Not an artifact: no frontmatter, never counts toward
orientation or run discovery.

## Origin

Backlog seed `docs/backlog.md:26` (from: maintenance:deepening-tool-seams),
claimed as `(claimed: maintenance:gate-timeline-timestamp-trust)`. Selected
by autorun without a fresh interview: the only other active run
(`feature:first-live-dispatch`) is blocked on operator-minted secrets, and
the operator has now driven two consecutive loop iterations asking autorun
to keep working the backlog.

## Scale and slug

Maintenance run, slug `gate-timeline-timestamp-trust`, artifacts under
`docs/fixes/gate-timeline-timestamp-trust/`.

## What and why

`human_gates.label_events` admits a timeline event when its label name and
`created_at` are merely truthy, while `human_gates.waited_seconds` assumes
`created_at` is ISO-8601. A completed gate stay carrying a non-ISO
timestamp therefore raises `ValueError` out of `gate_passages` — through
`gate_digest.run_daily`, which catches only `GH_FAILURES`, and out of the
scheduled `gate-digest` workflow as a traceback rather than the
label-prefixed problem string this repo's tools contract for.

## Scope

In: where a timeline timestamp is trusted, and which of `label_events` or
`waited_seconds` owns rejecting a malformed one. Out: `_parse_ts`'s
`Z`-suffix shim (correct and unrelated); the `gh` fetch path and its
`GH_FAILURES` handling (already correct); `dashboard.py`'s separate
duration helper, which the seed's own run already distinguished.

## Constraints

Stdlib only. Problem-string contracts. Tests assert exact strings through
public interfaces. Full battery green before Ship. `human_gates.py` is the
ADR-0056 seam for what a gate is, so a contract change there is a decision
to record, not a tweak.

## Tracker

No tracker seeding. An issue is opened at Ship for the PR to close, per
the repo's detector-B traceability grammar.

## Release authorization

None. Ship prepares and stops — branch, commit, push, issue and PR are how
this repo records work; merge and tag are not authorized, and ADR-0036
clause 2 reserves merge to a non-authoring reviewer regardless.
