---
stage: verify
run: maintenance:gate-timeline-timestamp-trust
date: 2026-08-23
re-verified: 2026-08-23, after review reopened A1
assumptions:
  - "There is no prd.md — this is a maintenance run entering at capture — so the criteria list is breakdown.md's two acceptance criteria plus defect.md's stated Expected behaviour. Nothing was invented to pad it."
  - "The pre-fix crash is reproduced by restoring the old admission rule as a local function in a scratch script and calling the shipped gate_passages with it, rather than by editing human_gates.py and restoring it. A same-length in-place edit restored inside one second can leave a stale __pycache__ entry serving the mutated module, which would make this evidence a lie in either direction."
---

# Verification: the admission gate rejects a timestamp that is not one

## Summary

Six criteria checked, all pass. The regression is demonstrated at the
caller that actually crashed (`gate_passages`), against the same input
`defect.md` recorded, and the well-formed path is shown unchanged in the
same breath.

**This is the second pass.** The first found five criteria green against a
guard that Review then holed — see *The naive-timestamp hole*, below. Every
command was re-run against `c16a84e` rather than reused; the test count
moved 1347 → 1348 and the four cases below replace the earlier three. No
evidence in this file predates the fix.

## Criteria & evidence

### The defect no longer reproduces (defect.md, Expected)

- Check: the exact timeline from `defect.md`'s reproduction — a completed,
  confirmed `prd` stay whose closing timestamp is `"yesterday"` — driven
  through `gate_passages` twice: once with the pre-fix admission rule
  (`if name and ts`) restored as a local function, once with the shipped
  one. Script at the scratchpad, not in the repo.
- Evidence:
  ```
  pre-fix  gate_passages raised ValueError: Invalid isoformat string: 'yesterday'
  post-fix gate_passages -> []
  ```
- Result: PASS

### A1 — the drop rule covers an unparseable timestamp

- Check: `python3 -m unittest tests.test_human_gates -v`, the four cases
  added by this run. The first two were watched to fail before the guard
  landed (recorded in commit `b4dd17a`); the third is the sibling proving
  a well-formed timeline still passes the gate.
- Evidence:
  ```
  test_a_malformed_timestamp_does_not_reach_the_parse (tests.test_human_gates.TestLabelEvents.test_a_malformed_timestamp_does_not_reach_the_parse) ... ok
  test_a_naive_timestamp_is_not_one_either (tests.test_human_gates.TestLabelEvents.test_a_naive_timestamp_is_not_one_either) ... ok
  test_a_timestamp_that_is_not_one_is_not_a_well_formed_flip (tests.test_human_gates.TestLabelEvents.test_a_timestamp_that_is_not_one_is_not_a_well_formed_flip) ... ok
  test_a_well_formed_timeline_is_unchanged_by_the_third_clause (tests.test_human_gates.TestLabelEvents.test_a_well_formed_timeline_is_unchanged_by_the_third_clause) ... ok
  ```
- Result: PASS

### A2 — the policy keeps one owner

- Check: `grep -n except human_gates.py`. The module's only exception
  handler must be the one inside the admission guard; `waited_seconds`
  (`human_gates.py:122` calls it) and `gate_digest.py:149` must carry
  none.
- Evidence:
  ```
  79:    except ValueError:
  ```
- Result: PASS — line 79 is inside `_is_timestamp`, the admission
  guard's own test. No other handler exists in the module, and neither
  call site gained one (see the next criterion's diffstat).

### breakdown.md's "the one thing that must not happen" — no call site changes

- Check: `git diff --stat main..HEAD -- '*.py' ':!tests' ':!factory'`.
  `gate_digest.py`, `dashboard.py` and `rejection_mining.py` must not
  appear.
- Evidence:
  ```
   human_gates.py | 41 ++++++++++++++++++++++++++++++++++++++---
   1 file changed, 38 insertions(+), 3 deletions(-)
  ```
- Result: PASS — one non-test, non-payload file in the whole run.

### The full battery is green, including the mirror pin

- Check: the repo's three commands, per CLAUDE.md. The mirror pin
  (`test_every_mirrored_root_file_matches_its_payload_copy`) is the one
  that caught this run's manifest churn, so its passing is the evidence
  that `factory/templates/tools/factory/human_gates.py` and
  `factory/manifest.json` were regenerated rather than forgotten.
- Evidence:
  ```
  Ran 1348 tests in 15.936s

  OK
  lint: 0 problem(s) across 24 skills
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

### The naive-timestamp hole — the precondition is the aware one

- Check: the guard's first form tested only that
  `datetime.fromisoformat` accepted the value. `"2026-08-01"` does
  parse — to a *naive* datetime — so it was admitted, and the
  subtraction downstream raised `TypeError` rather than `ValueError`.
  Re-probed at `_is_timestamp` across every shape GitHub emits and the
  neighbours a fetcher might hand over.
- Evidence:
  ```
    _is_timestamp('2026-08-01T00:00:00Z') -> True
    _is_timestamp('2026-08-01T00:00:00+00:00') -> True
    _is_timestamp('2026-08-01T00:00:00.123456Z') -> True
    _is_timestamp('2026-08-01T00:00:00.123Z') -> True
    _is_timestamp('2026-08-01 00:00:00+00:00') -> True
    _is_timestamp('2026-08-01') -> False
    _is_timestamp('') -> False
    _is_timestamp(None) -> False
    _is_timestamp(0) -> False
    _is_timestamp(1754006400) -> False
    _is_timestamp({'x': 1}) -> False
    _is_timestamp('yesterday') -> False
    _is_timestamp('2026-13-01T00:00:00Z') -> False
  ```
- Result: PASS — every real GitHub shape still admitted, including both
  fractional-second forms and an explicit `+00:00`; every shape that
  would crash a caller dropped.

## Failures

None outstanding. One was found *between* the two passes of this stage and
is recorded above rather than hidden: the first guard admitted a naive
timestamp, which Review caught and Implement fixed at `c16a84e`. A stage
that ran twice is worth more in the record than a stage that looks like it
ran once.

## Not verified

- **The daily digest end to end.** `gate_digest.run_daily` fetches real
  timelines from GitHub and posts to issue #178; nothing here drove it.
  The claim this run makes is narrower and is what was checked: the value
  that crashed it can no longer reach `waited_seconds`. Whether the digest
  survives some *other* malformed field is untested and unclaimed.
- **A non-string `created_at`.** `_is_timestamp` rejects one via its
  `isinstance` test, and no unittest case covers it — only the probe
  above does — because GitHub's API does not emit one — the guard is there so the failure mode is a drop rather than
  an `AttributeError` from `.replace`, not because it was observed.
  Recorded here rather than tested so the gap is not silent.
- **The other timestamp consumers.** `dashboard.py` and
  `rejection_mining.py` read events from the same walk and are therefore
  covered by construction, but no test in this run drives either one.
  Their own suites pass unchanged, which is the whole claim.
