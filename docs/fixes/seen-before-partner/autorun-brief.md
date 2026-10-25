# Autorun brief: seen-before-partner

Not an artifact. Written 2026-10-24 by the orchestrator. The Owner chose
#1069 as the next run in the autorun session and authorised the merge of
#1070 (done, ec8159f), because this fix amends ADR-0116. Merges of this
run's pull request are not authorised by this brief: a green pull request
waits for the Owner's own answer.

Source: issue #1069 and `docs/fixes/lessons-per-signal-seen/review.md`
(Major finding 1). The tool is `decompose_lessons.py` under ADR-0113 as
superseded in part by ADR-0116.

## The defect

A hit run measured before its clean partner exists is folded into `seen`
(`_measured` records it whatever its count), and `pairs(skip=seen)` then
skips it. When the clean partner arrives in a later `update`, no contrast
pair is derived and the lesson is never written. The issue carries a repro
script; update 1 over H alone then update 2 over H + C prints no
`ADD replan/feature/added`, while one update over H + C does. Pre-existing
on main; same class as #1061, different cause.

## Scope

1. Fold a run into `seen` for a signal only once it has been used (paired
   as a hit, or voted), not merely measured. Architect must check the
   symmetric case (a clean run seen before any hit exists) and that a second
   `update` stays idempotent (no lesson re-derived, no double vote).
2. A new provisional ADR superseding ADR-0116's seen-equals-measured rule
   (supersede, never rewrite; next free number on origin/main; update
   ADR-0116's status line and the ADR README row the way ADR-0116 did for
   ADR-0113). If the on-disk shape is unchanged, the old file stays loadable
   with no migration; Architect confirms, with a logged assumption.

## Constraints

- Entry depth is Capture (reproduce for real in a scratch clone), then
  Architect, Decompose, Implement test-first, Verify, Review, Ship.
- Stdlib only, root-only (no new import pair; dual-membership pin stays 55
  unless Architect proves otherwise), no network or model call, no paid run,
  LEDGER unchanged. `decompose_lessons.py` stays read-only on git history.
- No `skills/` edit and never `.claude-plugin/plugin.json`'s version
  (ADR-0095).
- No permanent test may assert a path is "unchanged against main".
- Never write `docs/factory/decompose-lessons.jsonl` in this repo.
- The PR closes #1069 (`Closes #1069`), says plainly what was fixed and what
  stayed a documented decision, and has a `No work order:` line.
- No `operate:` section: operate does not run.

stop-after: ship
