---
stage: operate
run: feature:process-dashboard
date: 2026-08-14
---

# Retro: Process dashboard v1

## Outcomes vs. intent

### "A quick glance gives me an overview … without a terminal" (idea.md)

- What happened: the operator's first real open (2026-08-14, real
  config: skills + eat-sheet.com): "yes, this is a good start" — the
  glance answered "what's going on and what needs me" on first use.
- Signal strength: anecdote (one operator, one morning).

### The needs-you strip surfaces real work (PRD: drift flagged, queues aged)

- What happened: the strip's one live finding (WO-0018 row unchecked,
  mirror #123 closed) drove an actual operator action on day one:
  investigation showed #123 was manually closed on 2026-07-28 with no
  landing PR, no implementation, and no corrections stream — the row
  was honest, so #123 was reopened per ADR-0032 and the drift finding
  cleared on the next gather. The console caught a real cross-plane
  lie and got it fixed.
- Signal strength: measured (one complete detect → investigate →
  resolve cycle, evidence in #123's timeline).

### Backlog prioritization from the console (PRD: reorder with markers intact)

- What happened: mixed. The save path is verified end-to-end at the
  HTTP layer (204 rewrite, claim markers intact, 409 on stale hash —
  release.md's evidence), but the operator found the browser drag
  "difficult" and only "think[s] it works" — and `docs/backlog.md`
  shows no rewrite, so no reorder actually landed from the browser.
  The one flow Verify flagged as browser-unverified is exactly the one
  that came back rough.
- Signal strength: anecdote, corroborated by the untouched file.

### Metrics show whether we're improving (PRD: spend, cost/WO, trends)

- What happened: spend vs cap, cost/WO, gate-wait median, and
  acceptance/rework render truthfully ($0 owner-session run reads as
  $0 recorded, not free-and-measured). Trend *history* was deferred by
  design; the headline can't yet say "improving", only "current".
  Whether these numbers change operator behavior is unobserved after
  one morning.
- Signal strength: measured for correctness; unobserved for usefulness.

## Run retrospective

- Keep: item-sized PRs with the merge gate green each time — eleven
  clean merges, zero red CI runs, and the one mid-run test failure was
  an honest intermediate state, not flake. Keep the node-harness trick
  (pure render half + guarded DOM shim): it let a stdlib-only repo pin
  browser rendering against canned payloads.
- Keep: verification with quoted evidence — its "Not verified:
  hand-in-browser drag" line predicted the exact rough edge first use
  found.
- Change: anything drag-and-drop ships with a hand-in-browser check in
  the same work order, not deferred to Operate — the harness can't
  fake a pointer, so the item isn't done until a human drags. A
  click-to-move fallback would also have made the flow keyboard-usable
  and trivially testable.
- Change: mirror hygiene — #123 sat wrongly closed for 17 days because
  a manual sweep closed it past the row. The sweeps reconcile (#204)
  and this console both catch it now; sweeps that close issues should
  check the row first (ADR-0032 cuts both ways).
- Stop: nothing — no stage was skipped or backfilled this run, and
  none of the artifacts failed to earn its keep.

## Idea seeds

- Console backlog drag is finicky in a real browser — add click-to-move
  controls (or larger drop targets) and verify one reorder lands from
  the page (from: feature:process-dashboard)
- Metrics trend history — persist per-month cost/WO and gate-wait so
  the console headline can say "improving", not just "current" (from:
  feature:process-dashboard)
- Issue sweeps should refuse to close a mirror whose breakdown row is
  unchecked — the #123 class at its source (from:
  feature:process-dashboard)

## Run complete

Closed 2026-08-14. Seeds above appended to `docs/backlog.md` — natural
inputs to the next Idea-stage run.
