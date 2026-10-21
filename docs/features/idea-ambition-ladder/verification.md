---
stage: verify
run: feature:idea-ambition-ladder
date: 2026-10-20
assumptions:
  - "No live interview: the autorun brief holds no Verify-specific answers, so the skill's defaults were taken. The criteria list is prd.md's twelve success criteria plus the breakdown acceptance criteria no PRD criterion covers, plus a judgement of the breakdown Notes' two deviations."
  - "Every piece of evidence was run on HEAD 9cb1827 in this session; nothing is carried over from the Implement stage's report."
  - "Protected paths were compared with the three-dot form origin/main...HEAD. origin/main (c0035bf) equals the merge-base, so the diff holds exactly this run's work."
  - "Mutations were applied only in git archive copies under the scratchpad directory; this tree was never mutated, and the real docs/backlog.md was never edited (the sample seed went into a scratch copy)."
  - "Nothing here invoked claude plugin eval or any model; the harness case is judged statically only."
---

# Verification: An ambition ladder for the Idea stage

## Summary

12 of 12 PRD success criteria PASS, 0 FAIL, on HEAD 9cb1827. The breakdown
acceptance criteria no PRD criterion covers also pass. Full suite green on
five runs (3674 tests, 113 modules: two at 8 workers, one at -j 16, one at
-j 2, plus the first). Six mutations of load-bearing behaviour each applied
(diff shown) and each made tests fail. The two Implement deviations do not
contradict a PRD criterion or architecture.md. Two things are UNKNOWN and
stay UNKNOWN by design (no paid run is allowed): whether the harness
accepts the `ladder-brief` case, and whether the ladder produces better
briefs. Those are named under Not verified and are not covered by this
verdict.

## Criteria & evidence

### 1. The ladder step sits after the problem and evidence questions, before the solution hunch; names Solid, Showstopper, Moonshot with Showstopper the recommended default

- Check: read `skills/idea/SKILL.md` step 4 and ran the order tests.
- Evidence (SKILL.md, step 4 bullets in order):
  ```
     - What evidence exists that the problem is real (even anecdote counts —
       label it as such)?
     - **Ambition ladder.** How big should this be? Offer three rungs,
       Showstopper (recommended), and let the user pick — see the block
       below.
     - What's the rough shape of a solution? (A hunch, not a design.)
  ...
     - **Solid** — fixes the problem and ships fast. The fallback.
     - **Showstopper** — the same problem plus one moment that makes a viewer
       say "wait, do that again". Showstopper (recommended).
     - **Moonshot** — not achievable at this run's scale.
  tests: test_the_bullet_sits_between_evidence_and_the_hunch ... ok
         test_the_bullet_comes_before_the_block ... ok
         test_the_block_precedes_the_write_step ... ok
         test_each_rung_name_appears_more_than_once ... ok
  ```
  Reading judgement: the bullet is terse ("Offer three rungs, Showstopper
  (recommended), and let the user pick") but the block that follows states
  the anchoring ("quote their opening sentence and build each rung from it,
  never renaming their idea") and each rung on its own line, so an agent
  has what it needs.
- Result: PASS

### 2. The four showstopper tests and three prompts are present, asserted by exact phrase

- Evidence:
  ```
  1. A 30-second demo exists: the before and the after fit in two
     sentences, and the after is something you see, not a metric.
  2. It removes a step instead of speeding one up: zero clicks, zero setup,
     or it is done before you ask.
  3. It is built on something only this product has: its data, its place
     in the workflow, or context a competitor cannot see.
  4. It is achievable: it fits this run's scale, and its riskiest technical
     piece is named with a spike of about two days that could prove it.
  - What would you show first in a demo?
  - What does the user do today that they would never have to do again?
  - What does the product already know that it is not using?
  tests: test_every_pinned_phrase_is_in_the_skill ... ok
         test_the_four_tests_appear_in_order ... ok
  ```
- Result: PASS

### 3. Pick recorded; Moonshot seeded and never chosen; unachievable showstopper drops to Moonshot; feature runs get a scaled-down version

- Evidence:
  ```
  The pick is the user's, and it is recorded in idea.md. The Moonshot is
  never chosen in this run and is always saved as a seed; if the user picks
  it, say so and ask for the Showstopper or Solid pick.
  When a test fails, say which one and re-scope it once. If it still
  fails, or no spike could prove it, record it as the Moonshot and make
  Solid the pick.
  For a feature run, ask the ladder as one question: three one-line rungs
  built from the user's own sentence, Showstopper recommended, pick or
  correct. Ask the prompts only when their framing names no demo moment, at
  most two. Run the four tests silently and surface only a failure; keep
  the spike to one sentence. A product run asks all three prompts in full,
  one at a time.
  Rules: ... The ladder offers a bigger version anchored on their words; it never swaps
  their idea for yours.
  tests: test_every_pinned_phrase_is_in_the_skill ... ok
         test_the_rules_keep_the_existing_line ... ok
  ```
  The user's framing is kept (anchor sentence plus the retained "don't
  replace their idea with yours" rule). Showstopper is the default
  recommendation; an unachievable one is demoted and seeded.
- Result: PASS

### 4. `skills/idea/TEMPLATE.md` has the four headings

- Evidence:
  ```
  ## Evidence
  ## Ambition rung      (Chosen / Not taken / Demo / Removes a step / Only this product / Achievable lines, each pass | fail)
  ## The demo
  ## Riskiest piece + spike
  ## Cheapest kill test
  ## Solution hunch
  tests: test_the_four_sections_sit_between_evidence_and_the_hunch ... ok
         test_the_four_test_labels_have_pass_or_fail_slots ... ok
         test_the_template_carries_no_typed_id ... ok
  ```
- Result: PASS

### 5. An idea.md written before this change still validates

- Check: ran `protocol.stage_states` and `protocol.parse_frontmatter` on two real old briefs (copied to temp dirs), neither containing `Ambition rung`, then `python3 lint.py` over the repo, which also carries all twenty old idea.md files.
- Evidence:
  ```
  docs/features/codex-style-standards-enforcement/idea.md has Ambition rung: False
   stage_states: [('idea', 'done'), ('prd', 'current'), ('ux-design', 'ahead'), ...]
   frontmatter: {'stage': 'idea', 'run': 'feature:codex-style-standards-enforcement', 'date': '2026-09-20', ...}
  docs/features/decompose-eval-suite/idea.md has Ambition rung: False
   stage_states: [('idea', 'done'), ('prd', 'current'), ('ux-design', 'ahead'), ...]
   frontmatter: {'stage': 'idea', 'run': 'feature:decompose-eval-suite', 'date': '2026-10-20', ...}
  lint: 0 problem(s) across 34 skills
  tests: test_an_old_idea_md_is_a_finished_idea_stage ... ok
  ```
- Result: PASS

### 6. A seed line for an unchosen rung passes the seed grammar and gates; moonshot seed ends `(from: <run-ref>)`

- Check: in a `git archive` scratch copy, appended a sample moonshot line to its docs/backlog.md and ran protocol.check_backlog, lint.check_backlog, lint.py, gates.py. Read the skill's seed instruction (quoted under 3 and here).
- Evidence:
  ```
  Append one line each to `docs/backlog.md` in the form
  `- <seed text> (from: <run-ref>)`, with the run-ref being feature: plus
  the slug on a feature run and product on a product run.
  ... append only ... never rewrite an existing one ...

  appended: - A moonshot rung for the sample scheduling tool that books across every calendar (from: feature:sample-run)
  protocol.check_backlog: []
  last parsed: {'line': 133, 'text': 'A moonshot rung ...', 'origin': 'feature:sample-run', 'claimed': None}
  lint.check_backlog: []
  bad (no suffix): ["backlog: line 134: entry does not match '- <seed text> (from: <run-ref>)'"]
  lint: 0 problem(s) across 34 skills
  gates: 0 problem(s)
  tests: test_a_seed_in_the_documented_form_passes_the_protocol_check ... ok
         test_a_line_missing_the_suffix_is_a_problem ... ok
         test_a_product_run_seed_passes ... ok
  ```
  The real docs/backlog.md is unchanged vs origin/main (`git diff --stat` empty).
- Result: PASS

### 7. `skills/prd/SKILL.md` carries the demo line; `skills/launch-demo` byte-identical (and `skills/verify` too)

- Evidence:
  ```
  PRD SKILL.md step 4: When the run's `idea.md` has a
  `## The demo` holding a script, copy it into a success criterion worded
  "the demo runs as written", with the script as its checkable body; an
  absent or none demo writes no criterion.
  $ git diff --quiet origin/main -- skills/launch-demo skills/verify && echo identical
  launch-demo+verify identical
  tests: test_the_prd_skill_copies_the_demo_into_a_criterion ... ok
         test_launch_demo_and_verify_are_byte_identical_to_main ... ok
         test_only_idea_and_prd_change_under_skills ... ok
  ```
- Result: PASS

### 8. The `plugin-evals/idea/` suite exists, tagged `idea`, selected by `--tag idea` (static), layout matches existing suites

- Check: compared file by file with `plugin-evals/decompose/csv-export-cut`. Both: `case.yaml` (identical shape, schema_version "1.1", `context.scaffold_script: scaffold.sh`), `prompt.md` (frontmatter description, tags, max_turns 30, timeout_seconds 900, allowed_tools identical; prose gives every interview answer up front and fixes the output path), `scaffold.sh` (set -euo pipefail, git init, one commit), `graders/` (skill-fired is the same `tool_used` form with `idea` for `decompose`; regex and llm graders in the same front-matter form). Manifest has `"evals": "plugin-evals"`.
- Evidence:
  ```
  plugin-evals/idea/ladder-brief/prompt.md ['idea']      (tests.test_plugin_eval_tags.case_tags)
  tests: test_every_idea_case_carries_the_idea_tag ... ok
         test_the_manifest_points_evals_at_the_plugin_evals_directory ... ok
         test_the_case_directory_holds_the_four_parts ... ok
         test_case_yaml_names_the_case_and_its_scaffold ... ok
  ```
  (The other row printed, `plugin-evals/next/idea-exists`, is tagged `next`, not `idea`; it matched only my path filter.)
- Result: PASS

### 9. Cases cover the three checks, each with a with-plugin and without-plugin arm

- Check: the harness runs every case under both arms, as for the existing suites; the case has one grader per check. Graders: `showstopper-passes-four-tests` (llm), `rung-anchored-on-framing` (llm), `moonshot-not-chosen` (llm), `keeps-users-words` (regex on the planted phrase), `moonshot-seed-appended` (regex `^- .+ \(from: feature:slot-finder\)$`), plus skill-fired, idea-exists and four heading regexes.
- Evidence:
  ```
  tests: test_the_grader_files_are_exactly_the_eleven ... ok
         test_each_llm_grader_names_one_check ... ok
         test_the_moonshot_seed_regex_accepts_the_seed_form ... ok
         test_keeps_users_words_greps_the_planted_phrase ... ok
  ```
  Arms are the harness's, not authored per case; that is the same as every other suite, so the criterion reads PASS on the existing convention. Whether the arms actually discriminate is not measurable here (see Not verified).
- Result: PASS

### 10. No paid run: LEDGER, records, plugin.json version unchanged

- Evidence:
  ```
  $ git diff --stat origin/main -- skills/launch-demo skills/verify .claude-plugin factory/templates evals plugin-evals/records LEDGER.md docs/backlog.md
  (empty)
  $ git diff --name-only origin/main...HEAD | grep -E "^(\.claude-plugin|factory/templates|evals|plugin-evals/records|LEDGER|docs/backlog)"
  (empty)
  tests: test_the_case_never_names_the_paid_command ... ok
         test_nothing_imports_a_network_or_subprocess_module ... ok
  ```
  No `claude plugin eval` or model call was made by this stage either.
- Result: PASS

### 11. No existing eval definition edited

- Evidence:
  ```
  $ git diff --name-only origin/main...HEAD -- plugin-evals | grep -v '^plugin-evals/idea/'
  (empty)
  $ git diff --name-only origin/main...HEAD -- evals
  (empty)
  tests: test_the_protected_paths_match_the_base ... ok
         test_no_untracked_file_appears_under_the_protected_paths ... ok
  ```
- Result: PASS

### 12. The repo's checks all pass

- Evidence:
  ```
  tests: 3674 tests across 113 modules in 25.9s on 8 workers, 0 problem(s)
  tests: 3674 tests across 113 modules in 25.5s on 8 workers, 0 problem(s)
  tests: 3674 tests across 113 modules in 24.0s on 16 workers, 0 problem(s)
  tests: 3674 tests across 113 modules in 52.6s on 2 workers, 0 problem(s)
  lint: 0 problem(s) across 34 skills
  drift: 0 problem(s)
  gates: 0 problem(s)
  selftest: ok
  one-owner: 9 problem(s)      (on-demand pass, baseline 9; unchanged)
  ```
  The two new modules alone: `Ran 42 tests ... OK`.
- Result: PASS

### Breakdown: `docs/pipeline-protocol.md` changed by exactly one sentence

- Evidence:
  ```
  $ git diff --numstat origin/main...HEAD -- docs/pipeline-protocol.md
  1	1	docs/pipeline-protocol.md
  -deferred defect. Producers append well-formed entries only and never
  +deferred defect. Idea appends the rungs it did not take. Producers append well-formed entries only and never
  tests: test_the_producers_sentence_names_idea_beside_the_others ... ok
  ```
- Result: PASS

### Breakdown: skills/ changes limited to skills/idea and skills/prd

- Evidence:
  ```
  $ git diff --name-only origin/main...HEAD -- skills
  skills/idea/SKILL.md
  skills/idea/TEMPLATE.md
  skills/prd/SKILL.md
  tests: test_only_idea_and_prd_change_under_skills ... ok
  ```
- Result: PASS

### Breakdown: scaffold runs offline

- Check: ran `plugin-evals/idea/ladder-brief/scaffold.sh` in a fresh temp dir with a scrubbed environment (`env -i`), no model call.
- Evidence:
  ```
  d1e43e1 chore: seed the pitch and backlog
  docs/: backlog.md pitch.md
  scaffold backlog check: []      (protocol.check_backlog over the seeded backlog)
  ```
- Result: PASS

### Mutation checks (load-bearing behaviours)

Each applied in a `git archive` copy; this tree untouched (`git status --porcelain` prints nothing).

```
M1 remove the Showstopper-default phrase:
-     Showstopper (recommended), and let the user pick
+     Showstopper, and let the user pick
-     say "wait, do that again". Showstopper (recommended).
+     say "wait, do that again". Showstopper.
FAIL: test_every_pinned_phrase_is_in_the_skill        Ran 23, FAILED (failures=1)

M2 move the ladder bullet after the solution hunch:
FAIL: test_the_bullet_sits_between_evidence_and_the_hunch   Ran 23, FAILED (failures=1)

M3 drop the PRD carrying clause (skills/prd/SKILL.md, 4 lines removed):
FAIL: test_the_prd_skill_copies_the_demo_into_a_criterion
ERROR: test_the_carrying_clause_adds_no_typed_id       Ran 23, FAILED (failures=1, errors=1)

M4 delete graders/moonshot-not-chosen.md:
FAIL: test_the_grader_files_are_exactly_the_eleven
ERROR: test_each_grader_has_its_type_and_none_runs_code
ERROR: test_each_llm_grader_names_one_check            Ran 19, FAILED (failures=1, errors=2)

M5 drop the demotion rule:
-   fails, or no spike could prove it, record it as the Moonshot and make
-   Solid the pick.
+   fails, or no spike could prove it, carry on.
FAIL: test_every_pinned_phrase_is_in_the_skill         Ran 23, FAILED (failures=1)

M6 retag the case [lean] instead of [idea]:
FAIL: test_every_idea_case_carries_the_idea_tag
FAIL: test_the_prompt_frontmatter_carries_the_harness_keys   Ran 19, FAILED (failures=2)
```

Result: PASS (6 of 6 mutations detected).

## Deviation judgement

1. S8, Producers sentence placed on the existing line (one changed line,
   physically long): consistent with the PRD (the sentence is the one
   change beyond skills and suite scope architecture.md flagged) and with
   the "exactly one sentence" instruction; the long line is cosmetic only.
   Accepted.
2. S9/S11, scope tests diff against the merge-base with `origin/main`
   (else `main`), and the PRD-clause typed-id check is limited to the
   clause's neighbourhood: accepted. The first choice keeps the PRD's
   "byte-identical to main" check honest when local `main` trails; today
   `origin/main` equals the merge-base, so the result matches the literal
   criterion. The narrowed typed-id check is needed because
   `skills/prd/SKILL.md` already cites an ADR elsewhere.

## Failures

none.

## Not verified

- UNKNOWN: whether the plugin-eval harness accepts the `ladder-brief` case
  and whether the with-plugin arm beats the without-plugin arm. The
  suite is authored and checked statically only; a paid run is out of
  scope (Owner's decision) and the issue's cited-run box stays unchecked.
- UNKNOWN: whether the ladder improves briefs or shipped features; the
  PRD records no measurement.
- Not judged by any test: that a hurried user or model cannot pass "only
  this product has it" and "removes a step" by assertion. The tests pin
  that the text asks, not that the answers are honest (a known limit the
  PRD hands to Review). Likewise "drops to the moonshot" may demote too
  much when no spike can be named at idea time.
- `one_owner.py` is an on-demand review pre-pass, not a gate; run for
  completeness only. It is blind to tests/.
