---
stage: review
run: maintenance:gate-timeline-timestamp-trust
date: 2026-08-23
assumptions:
  - "Severity was not arbitrated live — this run is autorun-driven. F1 was called major and fixed inside the run rather than deferred, on the ground that it is the run's own defect surviving the run's own fix; F2 and F3 are called minor and deferred, which the review skill permits freely. An operator who disagrees with F1's severity gets the same outcome either way, since it is already fixed."
  - "The review went past the diff on one axis only: it re-read the two call sites the design promised not to touch, and dashboard._age_seconds, because the run's whole claim is about a precondition those functions rely on. Nothing else outside the diff was reviewed."
---

# Review: the admission gate rejects a timestamp that is not one

## Scope

Commits `b4dd17a`, `159b6c6`, `c16a84e` — the whole of
`agent/gate-timeline-timestamp-trust` against `main`. Files: `human_gates.py`
(+38/−3), `tests/test_human_gates.py` (+45), the mirrored payload copy and
`factory/manifest.json`, the run's artifacts, and one claimed seed line in
`docs/backlog.md`.

Read alongside the diff, because the design's central promise is about them:
`human_gates.gate_passages` (:122), `gate_digest.py:149`, `dashboard.py:158`
and `dashboard._age_seconds` (:137).

## Findings

### Major: the first guard admitted a naive timestamp, which still crashed

- Scenario: `_parses` tested only that `datetime.fromisoformat` accepted the
  value. `"2026-08-01"` does — as a *naive* datetime — so it was admitted,
  and `gate_passages` over a completed confirmed stay then raised
  `TypeError: can't subtract offset-naive and offset-aware datetimes`. That
  is the run's own defect, one step further along: the guard established
  "parses", but `waited_seconds` needs "parses and carries an offset".
  Reachable from any timeline whose `created_at` is date-only.
- Decision: **fixed** at `c16a84e` — renamed `_is_timestamp`, second clause
  added (`.tzinfo is not None`), case written first and watched to fail,
  Verify re-run rather than reused. Every shape GitHub actually emits still
  admits; `verification.md` carries the probe.
- Note on how it was found: not from the diff reading well — it does — but
  from asking what `_parses` returns for each shape a fetcher could hand
  over. The routed finding was the `ValueError`; this one was underneath it.

### Minor: a dropped event removes a stay silently, and nothing counts it

- Scenario: a malformed *opening* timestamp (`wo:draft` labeled at
  `"yesterday"`, passed and unlabeled at real timestamps) now yields
  `gate_passages -> []` and `waiting_since -> None`. A work order that
  really did pass its gate simply does not appear in the latency ledger,
  and no problem string, count or log line says an event was discarded.
  Pre-fix the same input produced a *rejection* — `completed_stays` scored
  the stay unconfirmed because `"yesterday"` sorts after the confirmation —
  so the change trades a fabricated rejection for an honest absence, which
  is the better of the two. It is still silence.
- Decision: **deferred**, with the reason on the record: the informative
  fix is a problems channel on `label_events`, and `architecture.md`
  rejected exactly that on measured cost — three production callers and
  ~15 test sites threading a list nobody reads, in a module where all
  eight functions are pure. Reversing that inside the fix run would make
  the design decision on the way past. Seeded at Operate instead.

### Minor: `dashboard._age_seconds` is a second reader of GitHub timestamps

- Scenario: the decayed contract, not a defect. `human_gates` now owns
  "what a timestamp is" — `_is_timestamp` plus `_parse_ts` — while
  `dashboard._age_seconds` (dashboard.py:143) does its own
  `datetime.fromisoformat(since.replace("Z", "+00:00"))`. Its docstring
  already acknowledges the duplication and explains why the *function*
  differs (one live `datetime`, not two strings), which is fair; what it
  now also duplicates is the Z-suffix compat rule. If `_parse_ts` ever
  gains a clause, the dashboard will not get it.
- Decision: **deferred** — pre-existing, out of this run's scope, and the
  surgical-scope rule says flag rather than fix. `one_owner.py` does not
  catch it (it compares stated values and payload keys, not parse logic),
  which is itself the interesting part. Seeded at Operate.

## Passes with no findings

- **Design.** The change matches `architecture.md`: `label_events` keeps
  its signature and its purity, no caller moved (`git diff --stat` over
  non-test non-payload Python is one file), no problems channel appeared,
  `_parse_ts` kept its contract, and neither `waited_seconds` call site
  gained a handler. The one deviation is a name — `architecture.md` did
  not name a helper, and `_parses` became `_is_timestamp` when its second
  clause landed — which changes no contract. `human_gates.py` remains the
  ADR-0056 seam with no new responsibility: deciding what a well-formed
  flip is was always its job.
- **Security.** The run tightens input validation at the boundary it
  concerns; a decoded API response is untrusted, and one more field of it
  is now checked before use. No secrets, no injection surface, no new
  external call, and the guard leaks nothing — it drops rather than
  reporting what it saw.
- **Correctness, beyond F1.** The partition invariant still holds over the
  admitted events (`TestThePartition` green, 1348 tests OK); the empty
  string and `None` cases behave exactly as before the change; every
  existing expectation in the suite is unmoved.

## Verdict

Ready to ship. F1 is fixed and re-verified; F2 and F3 are minor, deferred
with reasons, and owe two backlog seeds at Operate. The battery is green in
full, and the payload mirror plus manifest were regenerated in the same
commits as the edits that moved them.
