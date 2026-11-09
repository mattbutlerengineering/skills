---
stage: verify
run: feature:kb-from-knowledge-work-plugins
date: 2026-11-08
assumptions:
  - "No live interview: Verify ran unattended for autorun. The criteria list is PRD-0022's 33 success criteria; breakdown.md's acceptance lines are covered through its Criterion trace, and the few not already named by a PRD criterion (K7's usage exit code, K12's manifest and stray-file checks) are checked inside the criterion they support."
  - "Branch diffs are taken against the merge base with origin/main (git diff origin/main...HEAD, merge base 6f921cb), because origin/main has moved on to 7623a0a since the branch was cut; a two-dot diff would show main's own new commits as this run's changes."
  - "The routing eval is recorded as its own disclosed NOT RUN entry, not counted as a 34th PRD criterion. PRD 30 (the description is unchanged) is judged on the diff and passes; the eval it conditions is not owed."
  - "PRD 4's 'note is gone' is read as the paragraph quoted in the criterion ('Re-check with the two commands above ... nothing in the repo records the setting'). The page body still opens with 'Re-check with these two commands', which K3's Accept line keeps as how to re-check, and the words 'nothing in this repo records the setting' now sit inside the checked-against declaration, which lint reads."
  - "The harvest demonstration for PRD 5, 6, 7 and 26 ran only against a fixture repo, projects directory and memory directory built for this stage in the session scratchpad, with fixture text; nothing under the real Claude Code directory was read, listed or printed."
---

# Verification: Teach the knowledge base what it cannot see yet

## Summary

31 of 33 PRD success criteria PASS and 0 FAIL. 2 criteria are NOT RUN,
both for the Owner because no offline check can do them: PRD 13
(precision of the human-turn kind, a hand count over real interactive
transcripts) and PRD 32 (the demo, whose last steps need the real memory
directory and a model session). The routing eval (`python3
trigger_eval.py`) is also NOT RUN: it is not owed, because the
knowledge-base skill's frontmatter `description` is byte-identical to
main's (PRD 30). This is not an unqualified pass: the precision of the new
candidate kind is unmeasured and the end-to-end demo is unshown. Every
other criterion was checked with a fresh run from this worktree at
19ab7cd, quoted below. The battery is green, each command on its own exit
code: `tests: 4141 tests across 132 modules in 27.5s on 8 workers, 0
problem(s)` (exit 0), `lint: 0 problem(s) across 36 skills` (exit 0),
`drift: 0 problem(s)` (exit 0), `kb: 0 problem(s)` (exit 0), `gates: 0
problem(s)` (exit 0) and `selftest: ok` (exit 0).

## Criteria & evidence

The three new or extended test modules, run whole first:

```
$ python3 -m unittest -v tests.test_kb        -> Ran 43 tests in 1.921s / OK
$ python3 -m unittest -v tests.test_kb_harvest -> Ran 51 tests in 1.338s / OK
$ python3 -m unittest -v tests.test_knowledge_base_shape -> Ran 17 tests in 0.003s / OK
```

Each criterion below names the cases it rests on, run by name in a fresh
`python3 -m unittest <cases>` call, with that call's own tail and exit code.

### PRD 1 — Age is flagged

- Check: `python3 -m unittest tests.test_kb.TestAge.test_one_day_past_due_is_one_problem tests.test_kb.TestAge.test_on_the_due_date_it_is_still_fresh tests.test_kb.TestAge.test_age_problems_reads_one_page`, plus `kb.lint` over this repo with an injected `today` (see PRD 4).
- Evidence:
  ```
  == P1
  Ran 3 tests in 0.006s
  OK
  exit=0
  ```
  The exact string, from `test_the_age_check_runs_nothing`'s expected list in `tests/test_kb.py`:
  ```
  "kb: docs/kb/gh.md is past its declared age: checked 2026-10-01, max-age 30d, due 2026-10-31 — re-check it"
  ```
- Result: PASS

### PRD 2 — Lint stays offline

- Check: `python3 -m unittest tests.test_kb.TestAge.test_the_age_check_runs_nothing`. The case patches `kb.cli.runner` and `socket.socket` with a function that raises `AssertionError("the age check ran something")`, then calls both `lint` and `age_problems` and asserts the expected strings.
- Evidence:
  ```
  == P2
  Ran 1 test in 0.004s
  OK
  exit=0
  ```
- Result: PASS

### PRD 3 — Malformed declarations are reported

- Check: `python3 -m unittest` over `TestAge.test_checked_after_today`, `test_checked_that_is_not_a_date`, `test_checked_without_max_age_names_the_missing_field`, `test_empty_checked_against`, `test_max_age_alone_names_both_missing_fields`, `test_max_age_that_is_not_whole_days`.
- Evidence:
  ```
  == P3
  Ran 6 tests in 0.015s
  OK
  exit=0
  ```
  Two of the strings, from the offline case's expected list:
  ```
  "kb: docs/kb/bad.md declares an outside check but is missing field 'checked'"
  "kb: docs/kb/bad.md max-age 'thirty' is not a whole number of days like 30d"
  ```
- Result: PASS

### PRD 4 — This repo's page uses it

- Check: read `docs/kb/main-unprotected.md`; grep for the old note; compare with origin/main's copy; `python3 kb.py lint`; then `kb.lint(Path('.'), today=...)` through the public interface for today, the due date and the day after (no clock change).
- Evidence:
  ```
  checked-against: the GitHub API (main's branch protection and the repo's rulesets); not GitHub's merge-queue docs, and nothing in this repo records the setting
  checked: 2026-11-08
  max-age: 30d

  $ grep -c "nothing in the repo records the setting" docs/kb/main-unprotected.md
  0
  $ git show origin/main:docs/kb/main-unprotected.md | grep -n "Re-check\|nothing in the repo records"
  26:Re-check with the two commands above before relying on this page. They
  27:are the source of truth, and nothing in the repo records the setting.

  $ python3 kb.py lint
  kb: 0 problem(s)
  exit=0

  2026-11-08 []
  2026-12-08 []
  2026-12-09 ['kb: docs/kb/main-unprotected.md is past its declared age: checked 2026-11-08, max-age 30d, due 2026-12-08 — re-check it']
  exit=0
  ```
- Result: PASS

### PRD 5 — Memory duplicates are paired

- Check: `python3 -m unittest tests.test_kb_harvest.TestMemory.test_candidates_pair_three_and_leave_one_unpaired tests.test_kb_harvest.TestMemory.test_pair_by_shared_file_name_tokens tests.test_kb_harvest.TestMemory.test_harvest_pairs_with_the_kb_dir_it_is_given`; and `python3 kb.py harvest <fixture repo> --memory --projects-dir <fixture projects>` over a scratchpad fixture holding the three memory files and three pages the criterion names (fixture text).
- Evidence:
  ```
  == P5
  Ran 3 tests in 0.007s
  OK
  exit=0

  $ python3 kb.py harvest $FX/repo --memory --projects-dir $FX/projects
  exit=0
  "file": "cross-pr-hazard-pairwise-merge-test.md", ... "page": "docs/kb/cross-pr-merge-hazards.md", "shared": ["cross", "pr", "merge", "hazard"]
  "file": "manifest-regen-stray-patch-files.md", ... "page": "docs/kb/manifest-regen.md", "shared": ["manifest", "regen"]
  "file": "pr-body-no-work-order-waiver.md", ... "page": "docs/kb/pr-body-contract.md", "shared": ["pr", "body"]
  ```
- Result: PASS

### PRD 6 — A memory-only gotcha is unpaired

- Check: `python3 -m unittest tests.test_kb_harvest.TestMemory.test_candidates_pair_three_and_leave_one_unpaired tests.test_kb_harvest.TestMemory.test_no_kb_dir_leaves_every_candidate_unpaired`; and the same fixture harvest.
- Evidence:
  ```
  == P6
  Ran 2 tests in 0.006s
  OK
  exit=0

  "file": "gh-pr-edit-broken-use-rest.md", "name": "gh pr edit is broken", "type": "project",
  "description": "Use the REST API to edit a PR body.", "page": null, "shared": []
  ```
- Result: PASS

### PRD 7 — User scope is excluded

- Check: `python3 -m unittest tests.test_kb_harvest.TestMemory.test_user_scope_and_the_index_never_reach_the_output tests.test_kb_harvest.TestMemory.test_memory_type_reads_one_scope tests.test_kb_harvest.TestMemory.test_every_skip_reason_is_counted`; and in the fixture harvest a `type: user` file `owner-personal-note.md` whose description is `SENTINEL-PERSONAL-XYZ`, plus a `MEMORY.md` index holding `SENTINEL-INDEX`, then a grep of the printed JSON.
- Evidence:
  ```
  == P7
  Ran 3 tests in 0.008s
  OK
  exit=0

  "listed": 4, "user_scoped": 1, "skipped": 0,
  $ grep -c "SENTINEL\|owner-personal\|MEMORY.md" harvest.json
  0
  ```
- Result: PASS

### PRD 8 — Harness-neutral skill text

- Check: `python3 -m unittest tests.test_knowledge_base_shape.TestNeutrality.test_no_harness_specific_path tests.test_knowledge_base_shape.TestSkill.test_harvest_names_the_new_kinds_without_a_path`; and a grep over `skills/knowledge-base/`.
- Evidence:
  ```
  == P8
  Ran 2 tests in 0.001s
  OK
  exit=0

  $ grep -rn "~/.claude\|\.claude/projects\|CLAUDE_CONFIG_DIR\|MEMORY.md\|/memory/\|projects/<slug>" skills/knowledge-base
  neutral-grep-exit=1
  ```
- Result: PASS

### PRD 9 — A correction is listed

- Check: `python3 -m unittest tests.test_kb_harvest.TestHumanTurns.test_a_correction_after_an_agent_action tests.test_kb_harvest.TestHumanTurns.test_excerpts_are_capped tests.test_kb_harvest.TestHumanTurns.test_an_edit_is_named_by_its_path`.
- Evidence:
  ```
  == P9
  Ran 3 tests in 0.039s
  OK
  exit=0
  ```
- Result: PASS

### PRD 10 — An answered question is listed

- Check: `python3 -m unittest tests.test_kb_harvest.TestHumanTurns.test_an_answer_to_a_text_question tests.test_kb_harvest.TestHumanTurns.test_an_answer_through_the_question_tool tests.test_kb_harvest.TestHumanTurns.test_a_question_tool_error_is_no_answer`; and the fixture harvest's transcript (agent asks "Should I keep the old section?", human answers).
- Evidence:
  ```
  == P10
  Ran 3 tests in 0.039s
  OK
  exit=0

  "human_turns": [
    {
      "kind": "answer",
      "signal": "after-agent-question",
      "human": "Drop it, it is obsolete.",
      "agent": "Should I keep the old section?",
      "session": "s1",
      "at": "2026-11-08T00:00:02Z"
    }
  ],
  ```
- Result: PASS

### PRD 11 — Plain turns are not listed

- Check: `python3 -m unittest` over `TestHumanTurns.test_a_plain_instruction_is_not_listed`, `test_approvals_are_not_answers`, `test_an_autonomous_transcript_yields_none`, `test_meta_and_tagged_turns_are_skipped`, `test_two_human_turns_in_a_row_yield_at_most_one`, `test_a_subagent_file_yields_none`, `test_sidechain_records_yield_none`. In the fixture harvest the opening instruction "tidy the docs" was not listed (one entry only, above).
- Evidence:
  ```
  == P11
  Ran 7 tests in 0.133s
  OK
  exit=0
  ```
- Result: PASS

### PRD 12 — The kind is separate

- Check: `python3 -m unittest tests.test_kb_harvest.TestHumanTurns.test_existing_kinds_are_unchanged_and_the_key_is_empty tests.test_kb_harvest.TestHumanTurns.test_main_prints_the_key tests.test_kb_harvest.TestMine`; and a branch diff showing no line of the existing harvest tests removed or changed.
- Evidence:
  ```
  == P12
  Ran 9 tests in 0.122s
  OK
  exit=0

  $ git diff origin/main...HEAD -- tests/test_kb.py tests/test_kb_harvest.py | grep -E '^-[^-]'
  removed-lines-grep-exit=1
   tests/test_kb.py         | 159 ++++++++++++++++++++
   tests/test_kb_harvest.py | 379 +++++++++++++++++++++++++++++++++++++++++++++++
   2 files changed, 538 insertions(+)
  ```
- Result: PASS

### PRD 13 — Precision is measured

- Check: none; no offline check can measure it, because a fixture only confirms the heuristic it was written for.
- Evidence: none collected. Procedure for the Owner, on the Owner's machine: run `python3 kb.py harvest --days N` from this repo over its interactive transcripts; hand-label each `human_turns` candidate as a real correction or answered question, or not; record both counts. No threshold is set (an open question for the Owner); the counts decide whether human turns stay on by default.
- Result: NOT RUN — needs real interactive transcripts and a human labeller on the Owner's machine.

### PRD 14 — Class-page guidance exists

- Check: `python3 -m unittest tests.test_knowledge_base_shape.TestRubric.test_admit_proposes_a_class_page_at_three tests.test_knowledge_base_shape.TestIngest.test_one_rule_over_many_instances tests.test_knowledge_base_shape.TestSkill.test_over_budget_names_a_class_page`; and the over-budget text in `SKILL.md`.
- Evidence:
  ```
  == P14
  Ran 3 tests in 0.001s
  OK
  exit=0

  - **over budget** — shorten summaries, merge pages, fold three or more
    pages that share a cause into one class page
    (`references/page-rubric.md`), or delete the page that pays least.
  ```
- Result: PASS

### PRD 15 — Class pages are valid pages

- Check: `python3 -m unittest tests.test_kb.TestPageShapes.test_new_shapes_lint_clean_both_ways`, whose `absent-is-not-zero` page states one rule over three cited instances (`src/a.py, src/b.py, src/c.py`) and asserts `kb.index` and `lint` both return `[]`.
- Evidence:
  ```
  == P15/17/22
  Ran 1 test in 0.003s
  OK
  exit=0
  ```
- Result: PASS

### PRD 16 — Symptom-first guidance exists

- Check: `python3 -m unittest tests.test_knowledge_base_shape.TestRubric.test_gotcha_summary_leads_with_the_symptom_inside_the_cap`; grep of the rubric.
- Evidence:
  ```
  == P16
  Ran 1 test in 0.000s
  OK
  exit=0

  56:  gotcha page the summary leads with the symptom an agent meets when
  ```
- Result: PASS

### PRD 17 — No new failure on existing summaries

- Check: the same `TestPageShapes` case; its `topic-summary` page ("Notes about the cache.") leads with no symptom and lints clean. Also `python3 kb.py lint` over this repo's six pages, none of which was reshaped (PRD 25).
- Evidence:
  ```
  == P15/17/22
  Ran 1 test in 0.003s
  OK
  exit=0
  ```
- Result: PASS

### PRD 18 — Setup asks

- Check: `python3 -m unittest tests.test_knowledge_base_shape.TestSkill.test_setup_asks_the_newcomer_question tests.test_knowledge_base_shape.TestSkill.test_the_flow_table_runs_the_question_alone`; `SKILL.md` setup item 3.
- Evidence:
  ```
  == P18/19/20
  Ran 2 tests in 0.000s
  OK
  exit=0

  3. Ask the human for what the record does not hold: "What mistake do
     people new to this repo make that the code would not warn them
     about?" Ask one question per turn, at most three, and give each a
     recommendation drawn from the strongest candidate item 2 found (its
     one line and its source), for the human to confirm, correct or
     replace.
  ```
- Result: PASS

### PRD 19 — Answers are candidates

- Check: the same two cases; the same setup item.
- Evidence:
  ```
  == P18/19/20
  Ran 2 tests in 0.000s
  OK
  exit=0

     Answers are candidates like the others: they go into item
     4's list, inside the same five-page cap, and nothing is written
     until the user promotes it (`references/ingest.md` says how to judge
     one).
  ```
- Result: PASS

### PRD 20 — No human, no question

- Check: the same two cases; the same setup item.
- Evidence:
  ```
  == P18/19/20
  Ran 2 tests in 0.000s
  OK
  exit=0

     When no human is present (an autonomous run), skip this item
     and say that you skipped it.
  ```
- Result: PASS

### PRD 21 — Shape allows a wrong/right pair

- Check: `python3 -m unittest tests.test_knowledge_base_shape.TestRubric.test_shape_allows_one_optional_wrong_right_pair`; grep of the rubric.
- Evidence:
  ```
  == P21
  Ran 1 test in 0.000s
  OK
  exit=0

  88:- A gotcha page may add one short wrong/right pair: a `Wrong:` line
  ```
- Result: PASS

### PRD 22 — Pair optional both ways

- Check: the `TestPageShapes` case: page `pair` carries `Wrong: make check` / `Right: make check -v`, page `no-pair` carries none, and both lint clean.
- Evidence:
  ```
  == P15/17/22
  Ran 1 test in 0.003s
  OK
  exit=0
  ```
- Result: PASS

### PRD 23 — A page can say what it was verified against

- Check: `python3 -m unittest tests.test_knowledge_base_shape.TestRubric.test_frontmatter_names_three_optional_fields`; grep of the rubric.
- Evidence:
  ```
  == P23
  Ran 1 test in 0.000s
  OK
  exit=0

  47:checked-against: <what the claims were checked against; what they were not>
  68:- `checked-against` (optional) — what the claims were checked against,
  72:- `checked` and `max-age` (optional, always as a pair, and only beside
  ```
- Result: PASS

### PRD 24 — Verified-against optional both ways

- Check: `python3 -m unittest tests.test_kb.TestAge.test_checked_against_alone_never_ages tests.test_kb.TestAge.test_a_page_with_none_of_the_fields_has_no_age tests.test_kb.TestAge.test_empty_checked_against`. The first lints a page carrying `checked-against: macOS zsh with gh 2.62; not Linux CI` clean with today 2036-01-01; the second lints a page with none of the fields clean; the third gives a malformed (empty) declaration its problem string, since Architect made the line a declaration lint reads (ADR-0125).
- Evidence:
  ```
  == P24
  Ran 3 tests in 0.007s
  OK
  exit=0
  ```
- Result: PASS

### PRD 25 — Existing pages are unaffected

- Check: every pre-existing case in the two kb modules run by class; the branch diff shows no existing test line removed or edited (PRD 12); `docs/kb/` files changed on the branch; `python3 kb.py lint`.
- Evidence:
  ```
  == P25-index  (TestAge.test_the_index_line_never_carries_the_fields, test_kb.TestLint/TestStale/TestIndex/TestMain,
                 test_kb_harvest.TestMine/TestSelect/TestLocate/TestLinkedWorktree/TestMain)
  Ran 51 tests in 1.270s
  OK
  exit=0

  $ git diff --name-only origin/main...HEAD -- docs/kb/
  docs/kb/main-unprotected.md

  $ python3 kb.py lint
  kb: 0 problem(s)
  exit=0
  ```
- Result: PASS

### PRD 26 — Harvest stays read-only

- Check: `python3 -m unittest tests.test_kb_harvest.TestMemory.test_harvest_writes_nothing tests.test_kb_harvest.TestMemory.test_descriptions_are_capped tests.test_kb_harvest.TestHumanTurns.test_excerpts_are_capped`; a `shasum` of every file in the scratchpad fixture before and after the fixture harvest; a grep of `kb_harvest.py` for write calls.
- Evidence:
  ```
  == P26
  Ran 3 tests in 0.019s
  OK
  exit=0

  $ find $FX -type f -exec shasum {} \; | sort | diff - before.sha
  byte-identical-diff-exit=0

  $ grep -nE "write_text|open\(.*['\"]w|\.write\(|mkdir|unlink|rename\(" kb_harvest.py
  write-grep-exit=1
  ```
- Result: PASS

### PRD 27 — Fixtures only

- Check: grep of the three new or extended test modules for a home-directory path; the new harvest cases pass `projects=` or `--projects-dir` a temporary directory (seen in the diff: `kb_harvest.harvest(self.repo, self.projects, ...)`, `kb.main(["harvest", REPO, "--projects-dir", str(self.projects)])`).
- Evidence:
  ```
  $ grep -rn "Path.home\|~/.claude\|expanduser" tests/test_kb.py tests/test_kb_harvest.py tests/test_knowledge_base_shape.py
  tests/test_knowledge_base_shape.py:22:FORBIDDEN = ("~/.claude", ".claude/projects", "CLAUDE_CONFIG_DIR",
  ```
  The one hit is the neutrality test's own forbidden-string list.
- Result: PASS

### PRD 28 — Human still promotes

- Check: `python3 -m unittest` over `TestIngest.test_new_kinds_go_through_the_verbs_and_a_human_promotes`, `test_paired_and_unpaired_memory_verbs`, `test_user_scoped_facts_are_never_proposed`, `test_a_lead_cites_the_repo_and_restates`; `references/ingest.md`; harvest writes nothing (PRD 26).
- Evidence:
  ```
  == P28
  Ran 4 tests in 0.001s
  OK
  exit=0

  The newer kinds, and a **setup answer** (the reply to setup's newcomer
  question in SKILL.md step 1), are judged with the same verb table
  (ADD, UPDATE, DELETE, CONFLICT, NOOP), and a human promotes every item; none of them adds a way to write to
  `docs/kb/`.
  ```
- Result: PASS

### PRD 29 — Source credited

- Check: `python3 -m unittest tests.test_knowledge_base_shape.TestSkill.test_credits_knowledge_work_plugins`; `SKILL.md` `## Credit`.
- Evidence:
  ```
  == P29
  Ran 1 test in 0.000s
  OK
  exit=0

  against all adapt practices from anthropics/knowledge-work-plugins
  ([github.com/anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins),
  Apache-2.0). They are restated here in this pipeline's terms; none of
  its text is copied.
  ```
- Result: PASS

### PRD 30 — Routing unchanged

- Check: diff the frontmatter block of `skills/knowledge-base/SKILL.md` against origin/main's; hash the `description:` line on both sides; list the first hunks of the branch diff.
- Evidence:
  ```
  $ diff <(origin/main frontmatter) <(HEAD frontmatter)
  frontmatter-diff-exit=0
  14ee758a08f512adf8aa25cc19fdba67e2fbcc858bedf4359756e2526a43fe2b  -   (origin/main description line)
  14ee758a08f512adf8aa25cc19fdba67e2fbcc858bedf4359756e2526a43fe2b  -   (HEAD description line)
  $ git diff origin/main...HEAD -- skills/knowledge-base/SKILL.md | grep -n '^@@' | head -3
  5:@@ -23,6 +23,7 @@ artifact. The run artifacts are the **knowledge plane**; this is the
  ```
- Result: PASS

### Routing eval (conditioned by PRD 30)

- Check: none. `python3 trigger_eval.py` is owed only if the skill's `description` changes; it did not (PRD 30). It is a paid model run, excluded from this stage.
- Evidence: none collected. Command for the Owner, if a later stage changes the description: `python3 trigger_eval.py`.
- Result: NOT RUN — not owed, the description is byte-identical.

### PRD 31 — The battery passes

- Check: each command run on its own, its exit code captured directly (never piped first); stray patch files searched; `python3 factory_init.py update-manifest` and `git status --porcelain` after it.
- Evidence:
  ```
  $ python3 run_tests.py
  tests: 4141 tests across 132 modules in 27.5s on 8 workers, 0 problem(s)
  exit=0
  == python3 lint.py
  lint: 0 problem(s) across 36 skills
  exit=0
  == python3 kb.py drift
  drift: 0 problem(s)
  exit=0
  == python3 kb.py lint
  kb: 0 problem(s)
  exit=0
  == python3 gates.py
  gates: 0 problem(s)
  exit=0
  == python3 gates.py --selftest
  selftest: ok
  exit=0

  $ find . -path ./.git -prune -o \( -name '*.orig' -o -name '*.rej' \) -print
  find-done
  $ python3 factory_init.py update-manifest
  factory-init: 0 problem(s)
  exit=0
  $ git status --porcelain | wc -l
         0
  $ python3 kb.py harvest --bogus
  usage: kb.py harvest [root] [--days N] [--session ID] [--projects-dir DIR] [--memory]
  exit=2
  ```
- Result: PASS

### PRD 32 — The demo runs as written

- Check: steps 1 and 2 are shown offline above (PRD 4: `kb: 0 problem(s)` today, and the past-age string with today injected as 2026-12-09); the fixture harvest (PRD 5 to 7) shows the pairing shape. The criterion as written, against the real memory directory with a model session proposing NOOP, CONFLICT and ADD, was not run.
- Evidence: none for steps 3 and 4. Procedure for the Owner, on the Owner's machine: (1) before, `python3 kb.py lint` prints `kb: 0 problem(s)` over a page whose GitHub claim nothing re-checks; (2) after, lint flags `docs/kb/main-unprotected.md` once it is past its declared age (set `checked` back, or wait until 2026-12-09); (3) `python3 kb.py harvest --memory` over this repo pairs the three known duplicate memories with `cross-pr-merge-hazards`, `manifest-regen` and `pr-body-contract` and lists the memory-only gotchas unpaired; (4) a model session runs the knowledge-base skill's ingest on that output and proposes NOOP or CONFLICT for the pairs and ADD for an unpaired gotcha, each waiting for a human to promote it.
- Result: NOT RUN — steps 3 and 4 need the real memory directory and a model session on the Owner's machine.

### PRD 33 — LEDGER untouched

- Check: branch diff of `LEDGER.md` and `.claude-plugin/plugin.json`.
- Evidence:
  ```
  $ git diff origin/main...HEAD -- LEDGER.md .claude-plugin/plugin.json | wc -l
         0
  ```
- Result: PASS

## Failures

none.

## Not verified

- PRD 13, the precision of the `human_turns` kind: NOT RUN, for the Owner
  (procedure under PRD 13). Its false-positive rate is a stated risk and
  no figure is claimed.
- PRD 32, the demo: NOT RUN for steps 3 and 4, for the Owner (procedure
  under PRD 32). Steps 1 and 2 were shown offline only.
- The routing eval `python3 trigger_eval.py`: NOT RUN, not owed, because
  the description is unchanged; owed if a later stage changes it.
- No sentence of anthropics/knowledge-work-plugins was compared against
  the new skill text at this stage. The "restated, never copied" half of
  PRD 29 rests on Implement's note that no source text was read in; the
  shape test checks only that the credit is present.
- Two items rest on fixture shapes Architect assumed, not on the real
  harness formats: the memory frontmatter (`type:` top-level or under
  `metadata:`) and the transcript record shape. They are checked only
  against fixtures written for them, by design (PRD 27).
