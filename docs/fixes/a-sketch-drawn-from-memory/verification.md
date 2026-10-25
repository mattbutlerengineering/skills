---
stage: verify
run: maintenance:a-sketch-drawn-from-memory
date: 2026-10-25
---

# Verification: ux-design sketches from memory, checks scenarios last, and grades its own work

## Summary

7 PASS, 0 FAIL, 1 NOT RUN (criterion 8, a live run of the revised stage)
across 8 criteria. The regression test fails on `origin/main`'s skill text
and passes on HEAD `f48beb4`, and every repo check is clean. That shows the
three steps and the suggestion are written into the skill and template. It
does not show that a designer following the skill catches the defects
#1093 describes. That claim is unknown until criterion 8 runs.

## Criteria & evidence

### 1. Regression test fails on the old text and passes on the new

- Check: `python3 -m unittest tests.test_ux_design_grounding`, first in a
  detached scratchpad worktree at HEAD with `skills/ux-design/` checked out
  from `origin/main` (`98b220e`), then on HEAD. The worktree was removed after.
- Evidence:
  ```
  # origin/main's skills/ux-design/
  Ran 11 tests in 0.002s
  FAILED (failures=8, errors=3)

  # HEAD f48beb4
  Ran 11 tests in 0.001s
  OK
  ```
  The 3 errors are the order cases. `str.index` raises because the phrases
  they locate are absent on main, so they are red for the right reason.
- Result: PASS

### 2. Code facts before sketches

- Check: the `TestCodeFacts` cases (step text, "Never sketch an existing
  surface from memory.", order before **Sketch.**, `## Code facts` in the
  template).
- Evidence:
  ```
  test_code_facts_come_before_the_sketch ... ok
  test_the_skill_grounds_each_existing_surface_in_code ... ok
  test_the_template_has_the_section ... ok
  ```
- Result: PASS

### 3. Walkthroughs first

- Check: the `TestScenarioWalkthroughs` cases (hardest scenarios from
  `idea.md` and `prd.md`, "using only controls this doc defines", "A
  walkthrough that cannot finish is a gap", order before **Interview.**,
  `## Scenario walkthroughs` in the template).
- Evidence:
  ```
  test_the_skill_writes_the_hardest_scenarios_as_walkthroughs ... ok
  test_the_template_has_the_section ... ok
  test_walkthroughs_come_before_the_flow_interview ... ok
  ```
- Result: PASS

### 4. Independent review before hand-off, with a labelled inline fallback

- Check: the `TestIndependentReview` cases (files not conclusions,
  Critical and High only, fix or record before committing,
  `` `review: inline, not independent` ``, order before **Hand off.**,
  `## Review` in the template).
- Evidence:
  ```
  test_the_inline_fallback_is_labelled ... ok
  test_the_review_comes_before_the_hand_off ... ok
  test_the_reviewer_gets_files_not_conclusions ... ok
  test_the_template_has_the_section ... ok
  ```
- Result: PASS

### 5. ux-patterns suggestion, not a gate

- Check: `TestUxPatternsSuggestion`.
- Evidence:
  ```
  test_an_absent_patterns_file_draws_a_suggestion_not_a_gate ... ok
  ```
- Result: PASS

### 6. Each evidence class in the defect maps to a step that would catch it

- Check: a manual read of `skills/ux-design/SKILL.md` at HEAD against the
  defect brief's three quoted evidence lines, located by
  `grep -nE "what the form calls|the one-off|walk each one again|contradicts its flow|terms that drift" skills/ux-design/SKILL.md`.
  Five ungrounded wireframes (booking form, SMS, `Calendar`, roles, manage
  links) map to step 5's kinds of fact (line 51). The 3 of 6 scenarios that
  could not finish (a date-bounded change, one occurrence of a recurring
  closure, one setting across many templates) map to step 3's examples and
  its re-walk (lines 25, 28). The 8 Highs only a second reviewer found map to
  step 8's scope, which names two of the three classes the intake quotes
  (lines 68 to 69). This is a reading, not a run (see criterion 8).
- Evidence:
  ```
  25:   bulk edits, the one-off exception to a recurring rule) and write each
  28:   is written, walk each one again using only controls this doc defines.
  51:   depends on (what the form calls, which channels a message goes out
  68:   sketch that contradicts its flow, a code fact the design ignores,
  69:   terms that drift). Fix or record each finding before committing, and
  ```
- Result: PASS

### 7. Repo checks green, version untouched

- Check: the four CI commands on HEAD `f48beb4`, and the `plugin.json` diff.
- Evidence:
  ```
  tests: 3905 tests across 122 modules in 27.9s on 8 workers, 0 problem(s)
  lint: 0 problem(s) across 35 skills
  drift: 0 problem(s)
  gates: 0 problem(s)
  selftest: ok
  git diff origin/main...HEAD -- .claude-plugin/plugin.json | wc -l  ->  0
  ```
- Result: PASS

### 8. A designer following the revised skill catches these defects on a real run

- Check: none run. It needs a live ux-design session on a run with existing
  surfaces, such as a re-run of a venue-availability-style feature, or a
  `plugin-evals/` suite. Both are paid model runs, and no ux-design eval
  suite exists.
- Evidence: none.
- Result: NOT RUN

## Failures

None.

## Not verified

- Criterion 8: live behaviour. The phrase-pinning tests show the text is
  present, not that it is followed. The next real `ux: required` run is the
  first observation; its `ux.md` should carry Scenario walkthroughs, Code
  facts and a Review section with a named review kind.
- The earlier `ux.md` files in this repo (`pipeline-board`,
  `process-dashboard`) were not re-audited against the new steps. That is
  out of scope, per the defect brief's blast radius.
