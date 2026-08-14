---
stage: decompose
run: feature:process-dashboard
date: 2026-08-13
---

# Breakdown: Process dashboard v1

Progress lives in the checkboxes below — Implement checks items off as
their acceptance criteria are met. Row grammar matches the factory's
(id, size class per ADR-0034, blocking edges on the row line, PRD-0002
citation for detector A); tracker mirror numbers are appended per
ADR-0032 after each row exists here first.

## Milestone 1: Gather (`dashboard.py gather <repo>` answers the glance in JSON)

- [x] **WO-0019** operator config + gather skeleton — size:S, blocked by: — (PRD-0002 §User stories) (tracker: #255)
  - Accept: `gather` on this repo prints its runs with correct stage and next step from protocol orientation, reading the repo set from argv or `~/.process-dashboard.json`; an unreadable path yields a problem string and nonzero exit per the cli.report convention.
- [x] **WO-0020** gate queues in gather — size:S, blocked by: WO-0019 (PRD-0002 §User stories) (tracker: #256)
  - Accept: canned issues and timelines (FakeGh) yield queue entries whose ages match gate_digest's math; a failing gh call lands in problems while the rest of the gather renders on.
- [x] **WO-0021** drift findings — size:S, blocked by: WO-0020 (PRD-0002 §Success criteria) (tracker: #257)
  - Accept: a closed-mirror-issue-with-unchecked-row fixture is flagged, as is the inverse (checked row, open issue); a clean fixture is silent.
- [x] **WO-0022** factory output join — size:S, blocked by: WO-0020 (PRD-0002 §User stories) (tracker: #258)
  - Accept: fixture rows join label state, PR, and ledger spend into lifecycle entries consistent with row and PR state; an absent ledger is silent.
- [x] **WO-0023** ledger metrics — size:S, blocked by: WO-0019 (PRD-0002 §Success criteria) (tracker: #259)
  - Accept: month spend vs factory.json caps, cost per work order, and gate-wait trend recompute from a fixture costs.jsonl; an absent ledger reads as "no runs recorded yet", never zero.
- [x] **WO-0024** derived improvement metrics — size:M, blocked by: WO-0022, WO-0023 (PRD-0002 §User stories) (tracker: #260)
  - Accept: acceptance/rework rates derive from canned gh review data on WO-cited PRs; docs/factory/corrections.jsonl folds in when present and its absence is silent.

## Milestone 2: Read-only console (the morning glance in a browser, ≥2 repos)

- [x] **WO-0025** server + read endpoints — size:S, blocked by: WO-0019 (PRD-0002 §Solution) (tracker: #261)
  - Accept: `serve --port --config` binds 127.0.0.1 only; GET /api/repos lists the configured set, GET /api/repo?i=N returns the state dict, out-of-range → 404 — all pinned by handler tests, no real network.
- [x] **WO-0026** page: glance sections — size:M, blocked by: WO-0025 (PRD-0002 §Success criteria) (tracker: #262)
  - Accept: dashboard.html fires one request per repo and fills progressively; needs-you strip (queues + drift), repo run cards, GitHub links, and per-section empty/error states all render from canned payloads.
- [x] **WO-0027** page: output + metrics sections — size:S, blocked by: WO-0026 (PRD-0002 §Success criteria) (tracker: #263)
  - Accept: factory output table and metrics (totals + per-repo rows) render from canned payloads with their empty states.

## Milestone 3: Backlog write (prioritize from the console)

- [x] **WO-0028** backlog reorder function — size:S, blocked by: WO-0019 (PRD-0002 §Success criteria) (tracker: #264)
  - Accept: reordering a fixture backlog preserves claim markers and non-seed lines; a non-permutation and a stale content hash are both refused with the exact problem strings.
- [x] **WO-0029** backlog save path — size:M, blocked by: WO-0025, WO-0028 (PRD-0002 §User stories) (tracker: #265)
  - Accept: POST /api/backlog-order honors the 409/400/500 contract; the page's drag + dirty-state + Save round-trip reorders a scratch repo's docs/backlog.md end to end, and a failed save keeps the dirty state.

## Design gaps found

None — the architecture's contracts covered every item; no gap routed
back to Architect.

## Notes

- 2026-08-13: owner-session ledger policy — this run's orders are
  implemented interactively (no dispatched agent, no execution file),
  so each tick appends an honest $0 ledger row via `budget_guard
  record`: run_id `session-<date>-wo-<n>`, tokens 0, cost 0.0, outcome
  `owner-session:unmetered` — work-order-keyed so detector G's
  merged-row cross-check stays meaningful, $0 because the owner's
  subscription session adds nothing to the factory's metered monthly
  spend, and the outcome string says plainly that tokens went unmetered
  rather than unconsumed.
- 2026-08-14: the metrics headline renders month spend vs summed caps
  only; the UX mock's cost-per-order and gate-wait trend arrows need
  trend arrays the v1 payload doesn't carry (architecture marked them
  TBD-simple), so those figures render per-repo without trend marks
  rather than inventing a headline aggregate the data can't support.
- 2026-08-13: WO numbering continues the repo-global sequence where the
  software-factory run's last order (0018) left off — one sequence per
  repo, so the mirror, ledger, and detectors never need a run
  qualifier. (This note deliberately avoids the full token form:
  detector A reads any line carrying one as a row needing a PRD
  citation — the same convention the software-factory breakdown's notes
  follow.)
