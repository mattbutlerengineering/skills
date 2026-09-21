---
stage: capture
run: maintenance:a-malformed-timestamp-is-silently-dropped
date: 2026-09-20
re-entry: implement
intake: #491
assumptions:
  - "re-entry: implement, not architect. #326's architecture.md already made and recorded the one hard-to-reverse call — where a malformed timestamp is caught (label_events' existing drop rule, not a new mechanism) — and this run does not revisit it. What is missing is a count of what the drop rule already refuses, surfaced as a problem string by the two callers that can lose real information to a silent drop. That is an addition on top of a decision, not a new decision; issue #491 itself frames it as open between label_events, its callers, or an ADR amendment, and the caller-reports-it shape needs no new mechanism inside the pure module, so it clears none of ADR-0056's three ADR bars any more than #326's own fix did."
  - "No ADR amendment. ADR-0056's stay-partition invariant (queue label removed AND the pass label applied inside the window) is untouched — this run adds a count of dropped input, not a new reading of a stay. Nothing here is hard to reverse: deleting refused_timestamps and its two call sites restores exactly #326's shipped behavior."
  - "human_gates.py stays pure (ADR-0056: 'no gh, no ledger, no filesystem, no clock'). The count is exposed as a second pure function (refused_timestamps) over the same raw timeline label_events already walks, not as a problems channel bolted onto label_events itself — the shape architecture.md rejected by measured cost when it decided #326 (three production callers, ~15 test call sites touched for a list nobody would read from label_events directly)."
  - "dashboard.py is included, gate_digest.py is included, rejection_mining.py is not. The issue's acceptance criterion names gd:/dashboard: explicitly. rejection_mining calls label_events too but never reaches waited_seconds (defect.md's own table, cited below, confirms no duration arithmetic there), so a refused timestamp costs it nothing today; adding a third prefix there would be drive-by scope this run does not need to justify."
---

# Defect: a malformed timeline timestamp is refused with no problem string

## Defect

PR #326 (merged 2026-09-19, commit `9324d31`) gave `human_gates.label_events`
a third admission clause: a label flip's `created_at` must read as an
offset-aware timestamp (`_is_timestamp`), or the event is dropped. That
fix closed a real crash — an unparseable or naive `created_at` reaching
`waited_seconds` raised `ValueError`/`TypeError` out of `gate_digest.py`'s
scheduled daily run — and its own architecture record
(`docs/fixes/gate-timeline-timestamp-trust/architecture.md`) is explicit
that dropping the event was the chosen fix, not an accident: *"A malformed
event is dropped, exactly as a nameless or timestamp-less one already
is."*

**What #326 did not do: say so.** `label_events` returns fewer events than
the raw timeline carried, and neither `gate_digest.py` nor `dashboard.py`
— the two callers that turn those events into a duration a human reads —
notices the difference. `gate_digest.py`'s own module docstring states
this repo's CLI contract verbatim: *"functions return gd:-prefixed
problem strings; the CLI prints them and exits nonzero."* A refused
timestamp meets neither half: it is not reported, and (because nothing
raises) the run exits zero. The malformed event, and whatever real gate
wait or gate passage it represented, disappears with no trace anywhere a
human or the workflow log would see.

This is issue #491, opened against the still-open PR #490, which stops
before implementing a fix and instead records the gap: *"the fix silently
drops a malformed event with no gd:/dashboard: problem string, unlike
this run's stated success criteria and arguably the repo's problem-string
contract."*

## Reproduction / Evidence

Both reproductions below are the two shapes issue #491 names — defect.md
§1 and §3 of the independently-seeded, still-open
`docs/fixes/a-timestamp-the-digest-cannot-parse/defect.md` (PR #490,
unmerged at the time of writing) — re-run against this tree at `8e074d0`,
through the shipped public interface only (`human_gates.label_events`,
`gate_digest.run_daily`).

**1. The minimal raise (§1's timeline, a completed & confirmed stay whose
closing timestamp is not ISO):**

```
>>> events = human_gates.label_events(timeline)
>>> human_gates.completed_stays(events, human_gates.GATES[0])
[]
>>> human_gates.gate_passages(events)
[]
```

No crash (#326 holds) — and no `ValueError` was expected here since #326
already fixed that. The observation is what is *missing*: nothing records
that the timeline carried an event `label_events` refused.

**2. Both call sites, driven through the real tools, matching §3's two
shapes:**

Completed-confirmed-stay path (`gate_digest._capture_latency` via
`gate_passages`) — a mirrored issue whose stay closed on a malformed
timestamp:

```python
outputs, problems = gate_digest.run_daily(root, run=fake_run, clock=clock)
# outputs -> {'changed': 'false', 'reason': 'gd: 0 item(s) waiting, 0 new gate-latency row(s)'}
# problems -> []
```

Open-stay path (`gate_digest._queues` via `waiting_since`) — a mirrored
issue whose only labeled event carries a malformed timestamp, no
completed stay needed at all:

```python
outputs, problems = gate_digest.run_daily(root, run=fake_run, clock=clock)
# outputs -> {'changed': 'false', 'reason': 'gd: 1 item(s) waiting, 0 new gate-latency row(s)'}
# problems -> []
```

Both runs exit clean. `problems == []` in both, `changed` is `'false'` in
both. The scheduled `gate-digest` workflow reports nothing happened; in
fact a GitHub timeline event the tool could not use was silently thrown
away, once per malformed event, every day it stays inside the fetched
window. `dashboard.gather` reaches the identical code path through its
own `_timeline` (`label_events` over the same raw event, `waiting_since`
over the result) and is silent the same way.

Verified before writing a single line of the fix: these two `assertEqual`
calls, added first, fail against `8e074d0` (`problems == []` where a
`gd:`-prefixed string is expected) and pass only once `_timelines` and
`_timeline` are changed to compute and report the refused count.

## Root-cause hypothesis

Not a hypothesis — this is #326's design, working as designed, one layer
short. `label_events`' admission gate correctly refuses the malformed
event (closing the crash), and its docstring says the refusal is
deliberate: *"Anything that is not a well-formed label flip is not this
module's business."* What nothing does is answer the question a caller
with a problems list actually needs: **how many** were refused. The gap
is not a missing guard; it is a missing count at the one seam (the raw
timeline, before `label_events` narrows it) where the count is cheap to
compute and the two callers that need it already have a `problems` list
in scope.

## Blast radius

**Who.** The scheduled `gate-digest` workflow (`gate_digest.py`, mirrored
into every stamped repo via `factory_init.MIRRORS`) and the operator
dashboard (`dashboard.py`, root-only). Both read gate timelines through
`human_gates.label_events`.

**How badly.** Exactly as low as #326's own defect.md scored it, because
this is the same trigger with the crash already removed: GitHub's API
emits well-formed ISO-8601 `created_at` values, so a live occurrence
needs a hand-authored or replayed fixture, a proxy in front of `gh`, or a
non-GitHub harness (ADR-0027/ADR-0031). The severity this run answers is
narrower than #326's — not "does the tool crash" but "does the tool say
anything at all when it quietly loses data" — and the honest answer before
this fix is no.

**Since when.** Since #326 shipped the drop rule (`9324d31`,
2026-09-19). Before that commit the same input crashed loudly instead;
this is a one-day-old gap, not an aged one.

## Ruled out

- **Not a reason to revisit where the check happens.** #326's own
  breakdown ruled out redesigning `_is_timestamp()` or moving the check
  ("one rule, one spelling"); this run does not touch `_is_timestamp` or
  the admission clause it guards.
- **Not a problems channel on `label_events`.** Considered and rejected
  for the same measured-cost reason #326's architecture.md already gave
  for the admission decision itself: `human_gates.py` has no
  problems-returning function today, and adding one would touch three
  production callers (`gate_digest.py`, `dashboard.py`,
  `rejection_mining.py`) plus every existing `label_events` test call
  site for a value most of them do not need.
- **Not `rejection_mining.py`.** It imports `label_events` but never
  calls `waited_seconds` (confirmed in the cited defect.md's caller
  table: *"No — no duration arithmetic"*), so a refused timestamp costs
  it nothing observable today. Out of scope; not fixed here.
- **Not an ADR.** ADR-0056's stay-partition invariant is unchanged; this
  adds a count of what the admission gate already refuses, not a new
  reading of a stay.

## Work items

- [x] **A1** a shared pure walk answers both "which events are admitted"
  and "how many were refused" from one raw timeline — size:S, blocked
  by: —
  - Accept: `human_gates.refused_timestamps(timeline)` returns the count
    of well-formed-except-for-timestamp label flips in a raw timeline;
    `human_gates.label_events(timeline)` is behaviorally unchanged for
    every existing test case. Both read the raw dict keys exactly once,
    inside one private walk (`_admit`), so the two questions cannot
    drift apart. `tests/test_human_gates.py::TestRefusedTimestamps` pins
    six cases: a malformed timestamp counted, a well-formed timeline
    counting zero, a naive (offset-less) timestamp also counted, a
    nameless flip and a non-flip event both NOT counted, and the refused
    event confirmed absent from `label_events`' own output. Full battery
    green.
- [x] **A2** `gate_digest._timelines` and `dashboard._timeline` report
  what they refused — size:S, blocked by: A1
  - Accept: both functions call `refused_timestamps` on the raw fetched
    timeline (before `label_events` narrows it) and, when the count is
    nonzero, append `"gd: timeline for #<N> refused <count> malformed
    timestamp(s)"` / `"dashboard: timeline for #<N> refused <count>
    malformed timestamp(s)"` to the caller's existing `problems` list —
    the same list a failed fetch already reports through, so a malformed
    event is reported exactly where a lost one already is. Regression
    tests reproduce both shapes from Reproduction / Evidence above
    (`tests/test_gate_digest.py::TestRunDaily::
    test_a_malformed_closing_timestamp_is_refused_not_swallowed`,
    `::test_a_malformed_labeled_timestamp_is_refused_not_swallowed`,
    `tests/test_dashboard.py::TestQueues::
    test_a_malformed_timestamp_is_refused_not_swallowed`), each written
    first and confirmed to fail against `8e074d0` before the fix, and to
    pass after. No `ValueError`/`TypeError` on either path, before or
    after. Full battery green.
- [x] **A3** manifest and payload stay pinned — size:XS, blocked by: A2
  - Accept: `human_gates.py` and `gate_digest.py` are
    `factory_init.MIRRORS` entries; `python3 factory_init.py
    update-manifest` ran, the payload copies under
    `factory/templates/tools/factory/` are byte-identical to root again,
    and the regenerated `factory/manifest.json` is committed with the
    change. Detector E green. `dashboard.py` is root-only (its own
    module docstring: *"not in factory_init.MIRRORS"*) — no payload
    twin to update.

## Notes

None.
