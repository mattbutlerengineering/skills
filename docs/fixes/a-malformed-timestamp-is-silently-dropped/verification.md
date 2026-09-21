---
stage: verify
run: maintenance:a-malformed-timestamp-is-silently-dropped
date: 2026-09-20
assumptions: []
---

# Verification: a malformed timeline timestamp is refused with no problem string

## 1. Reproduced before any test was written — PASS

Against `8e074d0`, through the public interface, both shapes issue #491
names (defect.md §1 and §3 of the cited, still-open
`docs/fixes/a-timestamp-the-digest-cannot-parse/defect.md`):

```
>>> events = human_gates.label_events(timeline)   # closing ts = "not-a-timestamp"
>>> human_gates.gate_passages(events)
[]
```

```python
# completed-confirmed-stay path, through gate_digest.run_daily
outputs -> {'changed': 'false', 'reason': 'gd: 0 item(s) waiting, 0 new gate-latency row(s)'}
problems -> []

# open-stay path, through gate_digest.run_daily
outputs -> {'changed': 'false', 'reason': 'gd: 1 item(s) waiting, 0 new gate-latency row(s)'}
problems -> []
```

No `ValueError`/`TypeError` either way — #326 already holds — and
`problems == []` in both: exactly the gap issue #491 reports.

## 2. Red before green — PASS

The three regression tests were written first, against the unfixed
source (`git apply`'d implementation reverted via a saved patch, source
files back at `8e074d0`+intervening-main), and confirmed to fail before
any implementation change:

```
FAIL: test_a_malformed_closing_timestamp_is_refused_not_swallowed
AssertionError: Lists differ: [] != ['gd: timeline for #123 refused 1 malformed timestamp(s)']

FAIL: test_a_malformed_labeled_timestamp_is_refused_not_swallowed
AssertionError: Lists differ: [] != ['gd: timeline for #123 refused 1 malformed timestamp(s)']

FAIL: test_a_malformed_timestamp_is_refused_not_swallowed (dashboard)
AssertionError: Lists differ: [] != ['dashboard: timeline for #7 refused 1 malformed timestamp(s)']

Ran 3 tests in 0.010s
FAILED (failures=3)
```

The six `TestRefusedTimestamps` cases in `tests/test_human_gates.py`
failed at import time before the implementation (`refused_timestamps`
did not exist): `ImportError: cannot import name 'refused_timestamps'
from 'human_gates'`.

## 3. Green after — PASS

```
test_a_malformed_timestamp_is_refused ... ok
test_a_naive_timestamp_is_refused_by_the_same_second_clause ... ok
test_a_nameless_flip_is_not_a_refused_timestamp ... ok
test_a_non_flip_event_is_not_a_refused_timestamp ... ok
test_a_well_formed_timeline_refuses_nothing ... ok
test_the_refused_count_never_shows_up_in_label_events ... ok
test_a_malformed_closing_timestamp_is_refused_not_swallowed ... ok
test_a_malformed_labeled_timestamp_is_refused_not_swallowed ... ok
test_a_malformed_timestamp_is_refused_not_swallowed ... ok

Ran 9 tests in 0.005s
OK
```

## 4. No existing caller sees a different value on well-formed input — PASS

Every pre-existing `test_human_gates.py`, `test_gate_digest.py` and
`test_dashboard.py` case keeps its original expectation unmodified
(the diff only adds tests and two import-line insertions); all pass
unchanged, which is the check that `label_events`' behavior for every
well-formed timeline did not move.

## 5. Full battery — PASS

```
Ran 1626 tests in 20.993s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
```

1617 on `origin/main` (`8e074d0`) + 9 new = 1626 — 6 in
`tests/test_human_gates.py::TestRefusedTimestamps`, 2 in
`tests/test_gate_digest.py::TestRunDaily`, 1 in
`tests/test_dashboard.py::TestQueues`.

`python3 one_owner.py` reports the same 7 pre-existing problems as
`main`, none of them touching `human_gates.py`, `gate_digest.py` or
`dashboard.py`'s new code — confirmed by running it before and after the
change and diffing the two outputs byte for byte.

## 6. Mirrors and manifest — PASS

`human_gates.py` and `gate_digest.py` are `factory_init.MIRRORS`
entries. `python3 factory_init.py update-manifest` ran
(`factory-init: 0 problem(s)`); `diff` between each root file and its
`factory/templates/tools/factory/` twin is now clean, and the
regenerated `factory/manifest.json` is committed with the change.
`dashboard.py` is root-only (its own docstring states it is "not in
factory_init.MIRRORS"), so it has no payload twin to update.

## Not fixed — disclosed

**`rejection_mining.py`** imports `label_events` over its own `_timelines`
fetch and stays silent about a refused timestamp the same way
`gate_digest.py` did before this fix. It is not changed here: the cited
defect.md's own caller table (reproduced in `defect.md`'s Ruled out)
confirms it never calls `waited_seconds`, so a refused timestamp costs it
nothing observable today, and issue #491's acceptance criterion names
`gd:`/`dashboard:` specifically. If a future caller of `gate_rejections`
starts to care about a dropped `unlabeled` event closing a stay, the same
`refused_timestamps` call is one line to add there too.

## Not verified

- **Live occurrence.** Exactly like #326's own defect.md, this was never
  observed against real GitHub timeline data — every repro here is a
  hand-built fixture. The scheduled `gate-digest` workflow's own history
  carries no confirmed instance of this shape (see the cited defect.md's
  §8, unchanged by this fix).
- **A stamped product repo's live workflow run.** Payload-identity with
  root is verified by `diff` and detector E; an actual `gate-digest.yml`
  run against a stamped repo's own GitHub API was not exercised.
