---
run: maintenance:row-done-guard
date: 2026-08-23
scale: maintenance
---

# Autorun brief: the checked-row grammar disagrees with the row grammar

## What and why

`knowledge_plane.row_done` matches `DONE_ROW` without the `ROW.match`
guard every sibling accessor applies, so a checkbox row with no space
after the bracket is "done" to one accessor and "not a row" to the other
four. The one place that difference escapes is `gates.merged_wo_rows`
(detector G), which reaches `row_done` through a raw `WO_TOKEN.search`
rather than through a sibling — so G can count a line as a merged work
order that `work_queue`, the reconcile sweep and the dashboard all treat
as no row at all.

Raised as `docs/backlog.md:41` (from: session:2026-08-22), which recorded
that ADR-0058's run found it while collapsing the fourth checkbox-regex
owner and deliberately left it alone: adding the guard moves what a
shipped detector counts.

## Scope

**In:** `knowledge_plane.row_done` and its grammar; the detector-G call
site if the design requires it; tests pinning the agreement.

**Out:** the other three `row_*` call sites (already guarded by a
sibling); ADR-0058's roster decision, which is settled; `protocol._CHECKBOX`,
the second checkbox owner the ADR deliberately kept.

## Success criteria

A malformed checkbox line is treated the same way by `row_done` as by
every other `row_*` accessor, detector G no longer counts it as a merged
work order, and the change to what G counts is stated rather than
discovered.

## Constraints

Stdlib only. `knowledge_plane.py` is a factory seam (ADR-0037, ADR-0039)
and a `factory_init.MIRRORS` entry, so any edit needs
`python3 factory_init.py update-manifest` in the same commit. The full
battery is green at every item.

## Tracker

Issue #327 exists as the run's tracking issue and the PR closes it. No
`WO-####` is minted — this is a backlog-seed maintenance run, not
dispatched work, so nothing enters the dispatch plane (ADR-0032).

## Release authorization

None. Ship prepares and stops — branch, commit, push, issue and PR are how
this repo records work; merge and tag are not authorized, and ADR-0036
clause 2 reserves merge to a non-authoring reviewer regardless.
