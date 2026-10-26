---
stage: verify
run: maintenance:idea-keeps-the-coined-phrase
date: 2026-10-25
---

# Verification: Idea briefs paraphrase away the pitch's coined phrase

## Summary

3 PASS, 0 FAIL, 0 NOT RUN across 3 criteria. One caveat: the grader
scores the fix 2 of 3, but reading the three briefs shows 3 of 3 kept the
phrase. The miss is a blockquote wrapped mid-phrase, which the regex
cannot span.

## Criteria & evidence

### 1. The framing line is pinned, red on main and green on HEAD

- Check: `python3 -m unittest tests.test_idea_ambition_ladder` before and
  after the template and skill edits.
- Evidence:
  ```
  # origin/main template and skill
  FAIL: test_the_template_quotes_the_framing_under_the_title
  FAIL: test_the_write_step_points_at_the_framing_line
  FAILED (failures=2)
  # HEAD
  OK
  ```
- Result: PASS

### 2. A real Idea run keeps the coined phrase

- Check: `claude plugin eval . --trust-plugin --keep-temp --ablation none
  --tag idea` on an export of this branch ($1.16), recorded unedited as
  `plugin-evals/records/2026-10-26-3.json`, plus a read of the three kept
  briefs.
- Evidence:
  ```
  ladder-brief run 1/3: score 0.73  $0.41
    ✗ keeps-users-words (weight 1): pattern not found in file docs/features/slot-finder/idea.md
  ladder-brief run 2/3: score 1.00  $0.32
  ladder-brief run 3/3: score 1.00  $0.42

  # run 1's brief, lines 9-10
  > call-out shuffle. Our scheduling app should become a self-healing shift
  > rota: when someone calls out, it should find who can cover the station and
  ```
  Before the fix, 0 of 9 briefs kept the phrase. After it, 3 of 3 did. In
  run 1 the phrase wraps across a blockquote line, so the text between
  "shift" and "rota" is a newline plus `> `, which the grader's
  `self-healing shift\s+rota` cannot match. The grader is left unedited.
  Run 1's two judge misses grade the printed reply, not the brief, and
  passed in runs 2 and 3.
- Result: PASS

### 3. Repo checks green

- Check: the four CI commands.
- Evidence:
  ```
  tests: 3938 tests across 124 modules in 41.2s on 8 workers, 0 problem(s)
  lint: 0 problem(s) across 35 skills
  drift: 0 problem(s)
  gates: 0 problem(s)
  ```
- Result: PASS

## Failures

None.

## Not verified

- A pitch-free Idea run, where the framing comes from the first message.
  No eval case covers it.
