---
stage: verify
run: maintenance:dashboard-timeline-unreadable-age
date: 2026-10-11
assumptions:
  - "No prd.md exists for a maintenance run, so the criteria walked below are the Accept lines of defect.md's two work items, plus the repo's verify battery and the no-mirror confirmation the brief asked for."
  - "The red-first run below is trimmed with grep to the FAIL/ERROR heading and the assertion line of each failing test. The full tracebacks were run but are not quoted."
---

# Verification: the dashboard cannot tell an unreadable age from an unknown one

## Summary

5 criteria, 5 PASS, 0 FAIL. The dashboard now tells an unreadable age
(`aged: false`, marked on its own line) from an unknown one
(`aged: true`, unmarked). The failed-fetch problem string is unchanged.
The full battery is green at `55aac3b`.

## Criteria & evidence

### Red first: the new tests fail on the unfixed code for the right reason

- Check: added the tests to `tests/test_dashboard.py` before touching
  `dashboard.py` or `dashboard.html`, then ran the module at `60bf38a`
  (the capture commit, with no code fix yet).
- Evidence:
  ```
  $ python3 -m unittest tests.test_dashboard 2>&1 | grep -E "^(ERROR|FAIL):|^KeyError|^AssertionError: '|^Ran|^FAILED"
  ERROR: test_a_failing_timeline_lists_the_item_without_an_age (tests.test_dashboard.TestQueues.test_a_failing_timeline_lists_the_item_without_an_age)
  KeyError: 'aged'
  ERROR: test_a_read_timeline_with_no_arrival_is_aged_not_unreadable (tests.test_dashboard.TestQueues.test_a_read_timeline_with_no_arrival_is_aged_not_unreadable)
  KeyError: 'aged'
  ERROR: test_an_unparseable_timeline_is_unreadable_not_empty (tests.test_dashboard.TestQueues.test_an_unparseable_timeline_is_unreadable_not_empty)
  KeyError: 'aged'
  FAIL: test_needs_you_marks_an_unreadable_age_on_its_own_line (tests.test_dashboard.TestPage.test_needs_you_marks_an_unreadable_age_on_its_own_line)
  AssertionError: ' — age unknown (timeline unreadable)' not found in '<h2>Needs you (2)</h2><ul><li class="queue">● prd gate — <a href="https://github.com/octo/alpha/issues/10" target="_blank">#10 unread</a> <span class="repo">[alpha]</span>'
  FAIL: test_queued_issues_carry_gate_age_and_url (tests.test_dashboard.TestQueues.test_queued_issues_carry_gate_age_and_url)
  Ran 113 tests in 0.123s
  FAILED (failures=2, errors=3)
  ```
- Every failure is the missing `aged` field or the missing marker. None
  is a fixture or harness error.
- Result: PASS

### Data: a failed fetch yields `aged: False`, a read-but-empty timeline `aged: True`, both `waited_s: None`, problem strings unchanged

- Check: after the fix, ran the module, then re-ran the reproduction
  script from `defect.md`.
- Evidence:
  ```
  $ python3 -m unittest tests.test_dashboard 2>&1 | tail -3
  Ran 113 tests in 0.117s

  OK
  $ python3 scratchpad/repro.py
  failed fetch:
     {'gate': 'prd', 'issue': 7, 'title': 'WO-0101: first', 'waited_s': None, 'aged': False, 'url': 'https://github.com/o/r/issues/7'}
     {'gate': 'merge', 'issue': 8, 'title': 'WO-0102: second', 'waited_s': None, 'aged': False, 'url': 'https://github.com/o/r/issues/8'}
     problems: ['dashboard: gh api timeline for #7 failed: boom', 'dashboard: gh api timeline for #8 failed: boom']
  read, no arrival:
     {'gate': 'prd', 'issue': 7, 'title': 'WO-0101: first', 'waited_s': None, 'aged': True, 'url': 'https://github.com/o/r/issues/7'}
     {'gate': 'merge', 'issue': 8, 'title': 'WO-0102: second', 'waited_s': None, 'aged': True, 'url': 'https://github.com/o/r/issues/8'}
     problems: []
  ```
- The two cases that were byte-identical in `defect.md`'s reproduction
  now differ in `aged`. The failed-fetch problem strings are the same
  strings as before, and `test_a_failing_timeline_lists_the_item_without_an_age`
  still asserts them exactly. The unparseable-JSON path is pinned by
  `test_an_unparseable_timeline_is_unreadable_not_empty`.
- Result: PASS

### Render: the marker shows on an `aged: false` line and not on an `aged: true` line with no age

- Check: the node render harness test
  `test_needs_you_marks_an_unreadable_age_on_its_own_line`. It renders
  two entries with `waited_s: null`, one `aged: false` and one
  `aged: true`, and asserts the marker is on the first `<li>` only. It
  is part of the green module run above (113 tests, OK).
- Evidence:
  ```
  $ python3 -m unittest tests.test_dashboard.TestPage.test_needs_you_marks_an_unreadable_age_on_its_own_line tests.test_dashboard.TestPage.test_needs_you_renders_queues_and_drift_with_links -v 2>&1 | tail -6
  test_needs_you_renders_queues_and_drift_with_links (tests.test_dashboard.TestPage.test_needs_you_renders_queues_and_drift_with_links) ... ok

  ----------------------------------------------------------------------
  Ran 2 tests in 0.042s

  OK
  ```
- The existing payload has no `aged` key, and its line still renders
  `waiting 2d 4h` without a marker, because the page checks
  `q.aged === false` and does not test for a missing key.
- Result: PASS

### `dashboard.py` is not mirrored, so no manifest regen applies

- Check: listed `factory_init.MIRRORS` entries naming the dashboard.
- Evidence:
  ```
  $ python3 -c "import factory_init as f; print([m for m in f.MIRRORS if 'dash' in str(m)]); print(len(f.MIRRORS))"
  []
  26
  ```
- No entry names the dashboard, so `update-manifest` was not run.
  Detector E is part of the green `gates.py` run below.
- Result: PASS

### The full verify battery is green

- Check: ran all three commands at `55aac3b`, plus `one_owner.py` as a
  regression check.
- Evidence:
  ```
  $ python3 -m unittest discover tests 2>&1 | grep -E "^Ran|^OK|^FAILED"
  Ran 2109 tests in 28.564s
  OK
  $ python3 lint.py
  lint: 0 problem(s) across 31 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  $ python3 one_owner.py | grep dashboard
  one-owner: dashboard.py:195 _pr_by_issue, gate_digest.py:236 run_daily and rejection_mining.py:252 run_mine read the same payload keys (body, number, state) — one fact, one owner
  ```
- The one `one_owner` line naming the dashboard is a pre-existing
  finding about `_pr_by_issue`. Only its line number moved, because the
  edited docstrings above it grew. The total stays at 7 problems.
- Result: PASS

## Failures

none.

## Not verified

- **A live console session.** The page was exercised through the node
  render harness, not in a browser against a real repo with a failing
  `gh`. The render path is the same function the browser calls.
- **`gate_digest` is unchanged and was not re-verified beyond the
  suite.** The brief kept this fix to the dashboard (ADR-0056), so
  `gate_digest.py` and `human_gates.py` were not edited.
