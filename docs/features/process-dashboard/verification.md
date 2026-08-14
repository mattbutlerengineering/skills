---
stage: verify
run: feature:process-dashboard
date: 2026-08-14
---

# Verification: Process dashboard v1

## Summary

7 of 7 PRD success criteria PASS (one with a logged deviation on trend
marks), and every breakdown acceptance criterion not subsumed by a PRD
criterion is pinned by the suite — 1189 tests, lint, and both gates
runs green. No failures; the un-verified remainder (hand-in-browser
passes, trend arrays) is listed below, not silently absent.

## Criteria & evidence

### A cold open shows every configured repo's runs with stage and next step, matching the `next` router, with no terminal involved

- Check: served the console over a two-repo config (this repo + a
  scratch repo) and read `GET /api/repo?i=0`'s `runs`; compared against
  the protocol orientation the router uses (`protocol.next_stage` is
  the shared seam, so page and router cannot disagree by
  construction).
- Evidence:
  ```
  "runs": [
   {"ref": "feature:process-dashboard",
    "dir": "docs/features/process-dashboard", "stage": "verify"},
   {"ref": "feature:software-factory",
    "dir": "docs/features/software-factory", "stage": "implement"},
   {"ref": "maintenance:deepening-cli-seams",
    "dir": "docs/fixes/deepening-cli-seams", "stage": "operate"}]
  ```
  (Gathered mid-Verify: this run correctly reports `verify`.) The page
  renders these as repo cards (`ref ▸ stage`) — render functions pinned
  under node in `tests/test_dashboard.py` `TestPage`.
- Result: PASS

### Gate queues with ages match the pinned gate digest

- Check: `TestQueues` pins queue entries whose ages come from
  `gate_digest.waiting_since` over canned label timelines — the same
  functions the digest itself uses — and
  `test_wait_ages_match_the_gate_digest_format` pins the page's
  `fmtWait` against `_format_wait`'s exact grammar.
- Evidence:
  ```
  wait: ["2d 4h", "2h", "<1h", null]   (node harness, fmtWait)
  live queues: []  — no mirrored issue currently waits at a gate
                     (all this run's mirrors are closed)
  ```
- Result: PASS (fixture-pinned; the live view is legitimately empty
  today)

### Reordering the backlog in the UI reorders `docs/backlog.md` with claim markers intact

- Check: live save round-trip against a scratch repo through the
  running server, then a stale-hash replay; drag/dirty logic
  (`applyMove`, `renderBacklog`) pinned under node.
- Evidence:
  ```
  save -> 204
  # Backlog

  - seed one (from: product)
  - seed two (from: feature:alpha) (claimed: feature:beta)
  - seed three (from: session:2026-08-01)
  stale replay -> {"problems": ["dashboard: backlog changed
  underneath; refresh"]} 409
  ```
  The claimed seed moved wholesale with its marker; header prose kept
  its position.
- Result: PASS

### Every work order shows a lifecycle consistent with its breakdown row and PR state

- Check: live gather of this repo joined 29 work orders; sampled rows
  against the tracker and PRs.
- Evidence:
  ```
  output rows: 29
  {"wo": "WO-0019", "title": "operator config + gather skeleton",
   "size": "S", "state": "merged", "pr": 266,
   "url": ".../pull/266", "spend": 0.0}
  ```
  All of WO-0019…WO-0029 report `merged` with their real PR links —
  matching their checked rows and closed mirrors. `TestOutput` pins the
  join (label state, best-PR ranking, spend) on fixtures.
- Result: PASS

### Spend vs caps, cost per work order, and gate-latency trends render from `costs.jsonl`

- Check: live gather of this repo (real ledger, real cap) plus
  `TestMetrics` fixture recomputation.
- Evidence:
  ```
  "metrics": {"month_spend": 0.0, "cap": 300, "cost_per_wo": 0.0,
              "gate_wait_median": 2379, "acceptance": 1.0,
              "rework": 0.0}
  ```
  ($0 figures are honest: this run's orders were owner-session work,
  recorded as `owner-session:unmetered`.) Deviation, logged dated in
  the breakdown's Notes: trend *marks* (the UX mock's ↓ arrows) are
  deferred — the v1 payload carries medians and totals, no trend
  arrays.
- Result: PASS (with the logged deviation)

### A closed-mirror-issue-with-unchecked-row fixture (#123's class) is visibly flagged

- Check: live gather of this repo — the actual #123 disagreement still
  exists in the software-factory run — plus `TestDrift`'s fixtures in
  both directions.
- Evidence:
  ```
  "drift": ["drift: WO-0018 row is unchecked but its mirror #123 is
  closed"]
  ```
  The page renders drift in the needs-you strip with #123 linkified
  (node pin: `test_needs_you_renders_queues_and_drift_with_links`).
- Result: PASS

### At least two repos appear in one overview

- Check: served a two-repo config; listed and gathered both.
- Evidence:
  ```
  {"repos": [{"i": 0, "path": "/Users/mbutler/github/skills",
    "name": "skills"}, {"i": 1, "path": ".../tinyrepo",
    "name": "tinyrepo"}]}
  ```
  Both `/api/repo?i=N` answers returned full state dicts (quoted
  above).
- Result: PASS

### Breakdown acceptance criteria not subsumed above

- Check: the suite — `python3 -m unittest discover tests`; each
  criterion's pinning class listed.
- Evidence:
  ```
  Ran 1189 tests in 14.523s

  OK
  lint: 0 problem(s) across 23 skills
  gates: 0 problem(s)
  selftest: ok
  ```
  - WO-0019 unreadable path/config → problem strings, nonzero exit:
    `TestRepoSet`, `TestMain`.
  - WO-0020 failing gh call lands in problems while the gather renders
    on: `TestQueues`.
  - WO-0025 localhost-only bind, endpoint statuses, no real network:
    `TestServe` (bind + URL print), `TestRespond` (404/500 contract);
    off-box unreachability was also checked live when the item landed.
  - WO-0026/0027 per-section empty/error states from canned payloads:
    `TestPage` node pins ("Nothing waits on you.", "No active runs.",
    "No factory stamped in this repo.", "No runs recorded yet.",
    error-in-place, escaping).
  - WO-0028 exact refusal strings: `TestReorderBacklog` (stale hash,
    non-permutation, malformed-bullet immobility).
  - WO-0029 409/400/500 contract: `TestRespondPost` (9 cases,
    including unwritable-file 500 with the OS detail); failed-save
    render state (dirty kept, error beside Save): `TestPage` backlog
    pins.
- Result: PASS

## Failures

None.

## Not verified

- **Hand-in-browser passes.** The render half is node-pinned and the
  HTTP layer curl-verified, but no human opened the page this session:
  the physical drag gesture, the progressive fill as watched behavior,
  and failed-save-keeps-dirty as a lived flow remain unexercised in a
  real browser. First morning use is the natural check.
- **Trend arrays/arrows.** Deferred by design (dated breakdown note,
  2026-08-14); the payload has no trend history to render yet.
- **Live gate-queue ages.** No mirrored issue currently waits at any
  gate, so the live queue view is empty; the age math is
  fixture-pinned only.
