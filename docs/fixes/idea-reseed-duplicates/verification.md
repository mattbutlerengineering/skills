---
stage: verify
run: maintenance:idea-reseed-duplicates
date: 2026-10-25
---

# Verification: re-running Idea on a run appends its seeds twice

## Summary

2 PASS, 0 FAIL, 1 NOT RUN (criterion 3, a live Idea re-run) across 3
criteria. The new case fails on origin/main's `skills/idea/SKILL.md` and
passes on HEAD `dc6b734`, and every repo check is clean. Whether a model
following the skill actually skips the duplicate is unknown until a real
re-run happens.

## Criteria & evidence

### 1. The re-run rule is pinned, red on main and green on HEAD

- Check: `python3 -m unittest tests.test_idea_ambition_ladder`, once with
  `skills/idea/SKILL.md` copied from origin/main (`3fe622b`) and restored
  after, once on HEAD.
- Evidence:
  ```
  # origin/main skill
  FAIL: test_a_re_run_appends_no_rung_its_run_already_seeded (tests.test_idea_ambition_ladder.TestSeedInstruction.test_a_re_run_appends_no_rung_its_run_already_seeded)
  Ran 26 tests in 0.006s
  FAILED (failures=1)
  # HEAD
  Ran 26 tests in 0.006s
  OK
  ```
- Result: PASS

### 2. Repo checks green

- Check: the four CI commands on HEAD `dc6b734`.
- Evidence:
  ```
  tests: 3936 tests across 124 modules in 28.7s on 8 workers, 0 problem(s)
  lint: 0 problem(s) across 35 skills
  drift: 0 problem(s)
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

### 3. A real re-run of Idea on a seeded run appends nothing twice

- Check: none run. It needs a model run of the Idea skill on a run that
  already has seeds; the `idea` plugin-eval suite has no re-run case.
- Evidence: none.
- Result: NOT RUN

## Failures

None.

## Not verified

- Criterion 3. The test pins the instruction, not the behaviour; only a
  model run shows the model follows it.
