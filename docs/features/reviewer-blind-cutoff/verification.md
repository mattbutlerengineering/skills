---
stage: verify
run: feature:reviewer-blind-cutoff
date: 2026-11-04
assumptions:
  - "Interview answers came from autorun-brief.md, prd.md and breakdown.md; verify asks none. The criteria list is the PRD's 15 success criteria plus the breakdown's acceptance lines already covered by them (the breakdown's Coverage table maps each to a PRD criterion, so none is extra)."
  - "The battery ran with `python3 run_tests.py -j 3` because five parallel runs share the machine (stage note); -j only sets worker count."
---

# Verification: Withhold the pass cutoff from the implement-queue reviewer

## Summary

14 of 15 PRD criteria PASS; 1 is UNKNOWN in part: criterion 4's "written
before the code and fails first" cannot be shown from this tree (the
test and the module landed in one commit, `d0aab9c`, and no artifact
quotes the failing run), so that half is unverified; its other half (the
test asserts 0 to 6 flag, 7 to 10 pass, and passes) is PASS. 0 criteria
FAIL. NOT RUN: none needed a paid run, and none was made; the routing
eval is not owed because no frontmatter `description` changed (its exact
command, were it owed, is `claude plugin eval`, NOT RUN). The battery is
green: 3999 tests, lint, kb drift, gates and selftest all report 0
problems. The change is verified as skill text, one stdlib tool and its
tests; whether the reviewer anchors to the line is not tested and not
claimed.

## Criteria & evidence

### 1. Reviewer-facing text contains no pass or flag threshold

- Check: grep the contract, the skill, the two routine docs and the queue profile for "7 or more" and "6 or less".
- Evidence:
  ```
  $ grep -rnE "7 or more|6 or less" skills/implement-queue docs/factory/merge-train-routine.md docs/factory/hourly-improvement-routine.md .claude/implement-queue.md
  (no output; grep exit 1)
  $ python3 -m unittest tests.test_reviewer_verdict tests.test_reviewer_data_rule
  Ran 11 tests in 0.003s
  OK
  ```
- Result: PASS

### 2. The output contract no longer asks for a `verdict`

- Check: read the contract's Output table.
- Evidence:
  ```
  | `score`      | 0 to 10 |
  | `issues`     | Each with `category` (...), `description`, and optional ... |
  | `assessment` | A short free-text judgement |

  The reviewer is handed no pass line and returns no `verdict`: the
  orchestrator derives it from `score` (ADR-0123). A `verdict` the
  reviewer returns anyway is ignored.
  ```
  Pinned by `test_contract_asks_for_no_verdict` (OK above).
- Result: PASS

### 3. One threshold, one place, value unchanged

- Check: grep for `PASS_AT`; run the hook at the boundary; run `one_owner.py`.
- Evidence:
  ```
  ./reviewer_verdict.py:24:PASS_AT = 7
  ./reviewer_verdict.py:43:    return ("pass" if number >= PASS_AT else "flag"), value
  reviewer-verdict: flag (score 6/10)   exit 1
  reviewer-verdict: pass (score 7/10)   exit 0
  one-owner: 0 problem(s)
  ```
  The value is written nowhere else (criterion 1's grep finds no prose copy).
- Result: PASS

### 4. The derivation is testable, test first

- Check: `tests/test_reviewer_verdict.py` calls `derive` for 0 through 10 (`test_whole_scores`: flag for <= 6, pass otherwise); ran it. Test-first order checked in git history.
- Evidence:
  ```
  Ran 11 tests in 0.003s
  OK
  $ git show --stat d0aab9c
  feat(reviewer-blind-cutoff): reviewer_verdict.py owns the pass threshold, test first
   reviewer_verdict.py            | 59 +++
   tests/test_reviewer_verdict.py | 77 +++
  ```
  Test and module are one commit; no quoted failing run exists in the run's artifacts (the breakdown said the Implement record would quote it).
- Result: PASS for the 0-to-10 assertions; the fail-first ordering is UNKNOWN (not verifiable here). Not a product defect; a gap in the record, listed under Not verified.

### 5. An unusable score is `error`, never `pass`; no merge under `merge: auto`

- Check: ran the hook on non-numeric, out-of-range and missing arguments; read the orchestrator step 5 and the profile's hook section.
- Evidence:
  ```
  reviewer-verdict: error (score is not a number ('abc'))   exit 2
  reviewer-verdict: error (score outside 0 to 10 ('11'))    exit 2
  usage: python3 reviewer_verdict.py <score>                exit 2
  SKILL.md step 5: "Exit 2, a hook that did not run, a missing hook, or a reviewer that
  returned no usable `score` is `error`: re-dispatch the reviewer once, then hold the PR for
  a human, and under `merge: auto` never merge."
  ```
  The NaN, infinity, bool and missing cases are asserted in `tests/test_reviewer_verdict.py` (passing).
- Result: PASS

### 6. A `verdict` the reviewer returns itself is ignored

- Check: read SKILL.md step 5 and the contract.
- Evidence:
  ```
  SKILL.md: "act on its exit code only: the reviewer is handed no pass line and returns no
  verdict, and a `verdict` it returns anyway is ignored whichever way it points."
  ```
- Result: PASS (a text rule; there is no code path that reads the field, and no live run was made to exercise it)

### 7. Every verdict comment carries the score and the derived verdict

- Check: read SKILL.md step 5, the profile's `verdict` hook, and the hook's output.
- Evidence:
  ```
  SKILL.md: "Post a verdict comment on the PR whose first line is the line the hook printed,
  verbatim, so every comment carries the score."
  hook: reviewer-verdict: pass (score 8/10)
  ```
  Readable without running anything: the line is plain text.
- Result: PASS

### 8. Every reader of the reviewer's `verdict` field is listed and handled

- Check: re-ran the reader search over `skills/`, `factory/`, `docs/factory`, `docs/kb`, root tools and `.claude` for `verdict`; compared with architecture.md's Reader list.
- Evidence:
  ```
  skills/implement-queue/SKILL.md:51:  | `verdict` | none: a missing hook is an `error` verdict, never a pass (fail closed) |
  skills/implement-queue/SKILL.md:181-188: step 5 "Verdict": run the hook, act on exit code only, comment line verbatim
  skills/implement-queue/SKILL.md:227: Comment the derived verdict line (step 5) on the PR
  skills/implement-queue/references/reviewer-contract.md:34-35: returns no `verdict` ... A `verdict` the reviewer returns anyway is ignored.
  other hits: launch-demo, ship, audit, doctor, verify, knowledge-base skills (own verdict words);
              factory/charters/reviewer, factory/agents, factory/charters/qa (the factory Reviewer's pass/bounce verdict)
  ```
  Other-skill and factory hits are different reviewers or tools that do not read the scored reviewer's output. architecture.md's Reader list names the contract, SKILL.md, both routine docs, the research note and backlog (history, unchanged) and `conductor.py`/`conductor_flow.py` (unaffected), and states no Python tool or test reads the reviewer's output.
- Result: PASS

### 9. No stale "7 or more passes" wording in the skill, contract or routine docs

- Check: same grep and pin test as criterion 1.
- Evidence:
  ```
  $ grep -rnE "7 or more|6 or less" skills/implement-queue docs/factory/merge-train-routine.md docs/factory/hourly-improvement-routine.md .claude/implement-queue.md
  (no output; grep exit 1)
  test_no_cutoff_wording ... ok   (Ran 11 tests in 0.003s, OK)
  ```
- Result: PASS

### 10. Docs and routine protocols updated or recorded unchanged

- Check: `git diff eff46d2 HEAD` over `docs/factory` and `.claude/implement-queue.md`.
- Evidence:
  ```
  merge-train-routine.md: a derived `flag` (the orchestrator's `verdict` hook on the reviewer's
  score; the gate comment's first line carries the score) or a `block`
  hourly-improvement-routine.md: the profile's `verdict` hook runs on its score, as the orchestrator's
  gate step 5 states, and the PR comment's first line is the line the hook printed, score included.
  hourly-improvement-routine.md: - Gate: <check result, fast path or derived reviewer verdict with its score, merge result or denial>
  ```
  The research note and backlog lines are intentionally unchanged (history; architecture.md Reader list).
- Result: PASS

### 11. Rubric bands rewritten or kept with a recorded reason

- Check: read the contract's Scoring table and architecture.md Decisions & alternatives.
- Evidence:
  ```
  | 9–10  | Every criterion met, no defects, tests pass                               |
  | 7–8   | Every criterion met, minor nits only                                      |
  | 5–6   | Every criterion met, a non-trivial issue (a missed edge case, messy code) |
  | 3–4   | A criterion missed or broken; needs rework                                |
  | 0–2   | Hallucination, regression, a security defect, or no tests                 |
  architecture.md:172: - **Rubric bands kept as written** over rewriting them to hide the
  architecture.md:173:   6-to-7 step. The bands describe a defect, not a disposition ("minor
  ```
  The bands are unchanged and the 0 to 10 scale stays; the reason is recorded in architecture.md.
- Result: PASS

### 12. No skill frontmatter `description` changed

- Check: diff `description:` lines under `skills/` from `eff46d2` to HEAD.
- Evidence:
  ```
  $ git diff eff46d2 HEAD -- skills | grep -E "^[-+]description:"
  (no output)
  ```
  Files changed under `skills/`: `implement-queue/SKILL.md` (body) and `references/reviewer-contract.md` only. The routing eval is not owed.
- Result: PASS

### 13. The battery passes; manifest regenerated if owed

- Check: ran each command from the worktree.
- Evidence:
  ```
  tests: 3999 tests across 127 modules in 79.4s on 3 workers, 0 problem(s)     (run_tests.py -j 3, exit 0)
  lint: 0 problem(s) across 35 skills                                           (exit 0)
  drift: 0 problem(s)                                                           (kb.py drift, exit 0)
  gates: 0 problem(s)                                                           (gates.py, exit 0)
  selftest: ok                                                                  (gates.py --selftest, exit 0)
  $ git diff --name-only eff46d2 HEAD | grep -E "^factory/templates"
  (no output)
  ```
  No file under `factory/templates/**` changed, and `reviewer_verdict.py` is root-only (breakdown, ADR-0060), so `update-manifest` was not owed and was not run. `factory.py` gained a VERB entry (not mirrored).
- Result: PASS

### 14. No paid model run

- Check: grep the run's artifacts for the paid commands; this stage ran none.
- Evidence:
  ```
  $ grep -rnE "claude plugin eval|trigger_eval|charter_replay|claude -p" docs/features/reviewer-blind-cutoff/{idea,prd,architecture}.md
  docs/features/reviewer-blind-cutoff/prd.md:88:- [ ] No paid model run was made: no `claude plugin eval`, `trig...
  $ git diff --stat eff46d2 HEAD -- evals
  (no output)
  ```
  The one hit is the PRD's own statement of the ban; `evals/` is unchanged, so nothing was added under `evals/results/`. This stage ran none of the commands.
- Result: PASS

### 15. Anchoring is not claimed to exist

- Check: grep the run's artifacts for "anchor".
- Evidence:
  ```
  $ grep -rniE "anchor" docs/features/reviewer-blind-cutoff/{idea,prd,architecture}.md
  idea.md:38:the anchor.
  idea.md:45:- Here, no anchoring incident is on record. The evidence is the absence
  idea.md:87:- Anchoring may not exist. The change stands on making it measurable, and
  prd.md:35:This is prevention plus making the problem measurable. No anchoring
  prd.md:89:- [ ] Anchoring is not claimed to exist: no artifact in this run states th...
  prd.md:99:- Any live implement-queue run, and any measurement of whether anchoring h...
  architecture.md:234:| 15 anchoring not claimed | all wording |
  ```
  `idea.md:38` is the research note's phrase for the risk the seed names; every other hit disclaims it. None says the reviewer anchors.
- Result: PASS

## Failures

none.

## Not verified

- Criterion 4's fail-first ordering: the test and module share one commit and no failing run is quoted in the run's artifacts. The tests pass now; whether they failed first is not shown.
- Behaviour of a live implement-queue run: the orchestrator's step 5 is prose read by a model, so "ignores a returned `verdict`", "posts the score line" and "holds on exit 2" are verified as stated text and as the hook's exit codes, not by a run. A live run is out of scope (PRD) and would be a paid or merging action.
- Whether the reviewer anchors to 7: not tested, not claimed (criterion 15).
- No consumer outside this repo's single queue profile `.claude/implement-queue.md` is visible from here (architecture.md assumption).
