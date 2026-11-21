---
stage: verify
run: product | feature:<slug>
date: YYYY-MM-DD
---

# Verification: <title>

## Summary

<Pass/fail counts and the one-sentence verdict. Count or name every NOT RUN
/ unknown criterion, and never read as an unqualified pass over them (the
fail-closed roll-up; claim kinds in the plugin's CONTEXT.md). A zero count
("0 NOT RUN") names nothing: re-count after any criterion changes.>

## Criteria & evidence

### <Criterion (from prd.md or breakdown.md)>

- Check: <what was run/done>
- Evidence:
  ```
  <actual output — quoted, not summarized>
  ```
- Result: PASS | FAIL

## Failures

<Each failure and where it routes (usually back to Implement), or "none.">

## Not verified

<What wasn't checked and why — no silent gaps.>
