---
stage: verify
run: feature:fail-closed-roll-up
date: 2026-10-17
assumptions:
  - "Recommended default taken (criteria list): every PRD success criterion is judged, and a breakdown acceptance is judged on its own only when no PRD criterion already covers it (the skill's step 3). That gives 11 PRD criteria plus 6 breakdown-only acceptances. Breakdown acceptances that restate a PRD criterion are folded into that criterion's evidence."
  - "Environment default taken (base ref): PRD criterion 7 names `git diff --stat main`. The local `main` ref is stale at 7376d94. The branch's base is origin/main at 1290a4e (#991), which is an ancestor of HEAD, and Implement already logged this deviation in breakdown.md Notes. The check is judged against origin/main. The stale-main output is quoted too, with proof that the branch touches neither file it lists."
  - "Recommended default taken (end-to-end evidence): where a PRD criterion names `python3 gates.py` on a fixture, the real CLI ran in a throwaway clone of this branch outside the repo (the scratchpad), so no fixture ever entered the repo's tree. The detector function ran over a temp root that mirrors docs/features/<slug>/. The clone and the temp root were deleted afterwards."
  - "Recommended default taken (honest shapes): the PRD's 'three honest shapes re-dated past the cutoff' is judged two ways. The unit test pins the three Summary strings over a labelled disclosure, dated on the cutoff. The control below re-judges all 77 real files, unedited, with ROLLUP_ADOPTED moved to 0000-01-01, which re-dates every file past the cutoff, the three real honest files included."
---

# Verification: Fail-closed roll-up for verification Summaries

## Summary

**17 PASS, 0 FAIL, 0 NOT RUN** (11 PRD success criteria, 6 breakdown-only
acceptances). There is no unknown item to count. Every criterion was run
on this branch at `27467df`, and its output is quoted below. Detector H
refuses a post-cutoff or undated Summary that reads as a full pass over a
labelled NOT RUN criterion. It passes the same artifact once the Summary
counts the item, and it stays silent on pre-cutoff, prose-only and
no-Summary shapes. The real tree reports 0 problems with no shipped
artifact edited. The control shows that 0 means "judged and passed", not
"never judged". With the cutoff moved to 0000-01-01, all 77 real files are
judged and pass. Stripping the unknown words from one real Summary in
memory makes the rule fire. One gap sits outside the criteria and is
listed under "Not verified": the rule has not reached a stamped repo
through a real payload update.

## Criteria & evidence

### 1. A post-cutoff full-pass Summary over a labelled NOT RUN fails `python3 gates.py` with an exact `H:` string (PRD)

- Check: (a) the unit tests that assert the exact string through
  `gates.evidence_problems` and through `gates.check_evidence_honesty`.
  (b) The real CLI. A throwaway clone of this branch was made in the
  scratchpad, the failing fixture (dated `2026-10-17`, Summary "All
  criteria pass. The change is ready for review.", criterion "Live
  dispatch" with `Result: NOT RUN — no credentials in this sandbox`)
  was written at `docs/features/rollup-cli-fixture/verification.md`,
  and `python3 gates.py` was run there.
- Evidence:
  ```
  $ python3 -m unittest tests.test_gates.TestEvidenceRollUp -v
  test_artifact_dated_before_the_cutoff_is_grandfathered (tests.test_gates.TestEvidenceRollUp.test_artifact_dated_before_the_cutoff_is_grandfathered) ... ok
  test_cutoff_is_pinned (tests.test_gates.TestEvidenceRollUp.test_cutoff_is_pinned) ... ok
  test_full_pass_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_full_pass_summary_over_a_disclosed_criterion_fails) ... ok
  test_honest_summary_shapes_from_main_pass (tests.test_gates.TestEvidenceRollUp.test_honest_summary_shapes_from_main_pass) ... ok
  test_no_disclosed_criterion_is_silent (tests.test_gates.TestEvidenceRollUp.test_no_disclosed_criterion_is_silent) ... ok
  test_no_summary_section_is_silent (tests.test_gates.TestEvidenceRollUp.test_no_summary_section_is_silent) ... ok
  test_prose_only_not_run_without_a_labelled_disclosure_is_silent (tests.test_gates.TestEvidenceRollUp.test_prose_only_not_run_without_a_labelled_disclosure_is_silent) ... ok
  test_sections_record_an_unfenced_unknown_word (tests.test_gates.TestEvidenceRollUp.test_sections_record_an_unfenced_unknown_word) ... ok
  test_summary_counting_the_not_run_item_passes (tests.test_gates.TestEvidenceRollUp.test_summary_counting_the_not_run_item_passes) ... ok
  test_summary_naming_a_different_unknown_kind_passes (tests.test_gates.TestEvidenceRollUp.test_summary_naming_a_different_unknown_kind_passes) ... ok
  test_two_disclosed_criteria_give_one_problem_counting_both (tests.test_gates.TestEvidenceRollUp.test_two_disclosed_criteria_give_one_problem_counting_both) ... ok
  test_undated_artifact_is_judged_fail_closed (tests.test_gates.TestEvidenceRollUp.test_undated_artifact_is_judged_fail_closed) ... ok
  test_unknown_word_only_inside_a_fence_does_not_count (tests.test_gates.TestEvidenceRollUp.test_unknown_word_only_inside_a_fence_does_not_count) ... ok
  test_wrapper_prefixes_the_rollup_problem (tests.test_gates.TestEvidenceRollUp.test_wrapper_prefixes_the_rollup_problem) ... ok

  ----------------------------------------------------------------------
  Ran 14 tests in 0.001s

  OK
  ```
  ```
  27467df
  $ python3 gates.py   # failing fixture
  H: docs/features/rollup-cli-fixture/verification.md:9 summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Live dispatch", line 27); unknown never rolls up to pass
  gates: 1 problem(s)
  exit=1
  ```
- Result: PASS

### 2. The same fixture passes once its Summary counts the NOT RUN item, and so does one with no disclosed criterion (PRD)

- Check: in the same scratch clone, the fixture's Summary was replaced
  with "1 PASS, 0 FAIL, 1 NOT RUN." and `python3 gates.py` was run again.
  The no-disclosed-criterion case is
  `test_no_disclosed_criterion_is_silent` (criterion 1's run, `ok`).
- Evidence:
  ```
  $ python3 gates.py   # same fixture, Summary counts the NOT RUN
  gates: 0 problem(s)
  exit=0
  ```
  ```
  test_no_disclosed_criterion_is_silent (tests.test_gates.TestEvidenceRollUp.test_no_disclosed_criterion_is_silent) ... ok
  test_summary_counting_the_not_run_item_passes (tests.test_gates.TestEvidenceRollUp.test_summary_counting_the_not_run_item_passes) ... ok
  ```
- Result: PASS

### 3. The three honest shapes on main pass when re-dated past the cutoff (PRD)

- Check: (a) the unit test pins the three Summary strings, each over a
  labelled disclosure and dated on the cutoff. (b) The control (criterion
  7's second block) moved `ROLLUP_ADOPTED` to `0000-01-01`, which re-dates
  all 77 real files past the cutoff, the three honest files included, and
  re-ran `check_evidence_honesty` on the real tree, unedited.
- Evidence:
  ```
  $ sed -n 2861,2867p tests/test_gates.py
      def test_honest_summary_shapes_from_main_pass(self):
          for summary in ("0 of 7 met, 0 failed, 7 unmet.",
                          "7 PASS, 0 FAIL, 2 NOT YET VERIFIABLE.",
                          "16 PASS, 3 FAIL, 1 DEFERRED."):
              with self.subTest(summary=summary):
                  self.assertEqual(gates.evidence_problems(
                      self.DATED + self.body(summary)), [])
  ```
  ```
    (b) cutoff 0000-01-01, unedited: 0 H problem(s); artifacts judged: 77
  ```
- Result: PASS

### 4. A criterion that mentions "not run" only in prose, with no labelled disclosure, does not trigger the rule (PRD)

- Check: `test_prose_only_not_run_without_a_labelled_disclosure_is_silent`,
  plus the `prose-only-not-run` fixture (post-cutoff, full-pass Summary,
  criterion text "This was not run here; the unit suite stands in for
  it." and no `Result:` line) run through `gates.check_evidence_honesty`
  over a temp root by the scratch script
  (`/private/tmp/claude-501/-Users-mbutler-github-skills/61791cec-ce5d-4fbf-a8e5-60dc748e0ec7/scratchpad/e2e-script/e2e.py`).
- Evidence:
  ```
  ROLLUP_ADOPTED = '2026-10-17'
  check_evidence_honesty over the fixture root:
    failing-post-cutoff: ['H: docs/features/failing-post-cutoff/verification.md:9 summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Live dispatch", line 27); unknown never rolls up to pass']
    counted: [] (0 problems)
    pre-cutoff: [] (0 problems)
    prose-only-not-run: [] (0 problems)
    no-summary: [] (0 problems)
    undated: ['H: docs/features/undated/verification.md:8 summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Live dispatch", line 26); unknown never rolls up to pass']
    total: 2 problem(s)
  ```
- Result: PASS

### 5. The failing fixture, dated before the cutoff, passes (PRD)

- Check: the `pre-cutoff` row above (dated `2026-10-16`, otherwise the
  failing shape), `test_artifact_dated_before_the_cutoff_is_grandfathered`,
  and the real CLI in the scratch clone with the fixture re-dated
  `2026-10-16`.
- Evidence:
  ```
  4:date: 2026-10-16
  $ python3 gates.py   # failing shape dated 2026-10-16
  gates: 0 problem(s)
  exit=0
  ```
- Result: PASS

### 6. The cutoff is one named constant compared with frontmatter `date:`, pinned by a test (PRD)

- Check: grep for the constant and its one comparison in `gates.py`, and
  the pinning test.
- Evidence:
  ```
  $ grep -n "ROLLUP_ADOPTED = \|date < ROLLUP_ADOPTED" gates.py
  245:ROLLUP_ADOPTED = "2026-10-17"
  1200:    return not (isinstance(date, str) and date < ROLLUP_ADOPTED)
  $ sed -n 2799,2800p tests/test_gates.py
      def test_cutoff_is_pinned(self):
          self.assertEqual(gates.ROLLUP_ADOPTED, "2026-10-17")
  ```
- Result: PASS

### 7. `python3 gates.py` reports 0 problems on the real tree with no shipped verification.md or review.md edited (PRD)

- Check: `python3 gates.py` on the real tree, then the diff against the
  branch base. The control: `parse_run` on the real tree, then the
  rule re-run (a) as shipped, (b) with `ROLLUP_ADOPTED` moved to
  `0000-01-01`, (c) also with one real Summary
  (`docs/fixes/toolsmith-mine-pr-permissions/verification.md`) stripped
  of every `SUMMARY_UNKNOWN_TERM` match in memory, and (d) the stripped
  text at the real cutoff. The local `main` ref is stale (see
  `assumptions:`), so the diff runs against `origin/main`. The
  stale-`main` output is quoted too.
- Evidence:
  ```
  $ python3 gates.py
  gates: 0 problem(s)
  $ git rev-parse --short HEAD; git rev-parse --short origin/main; git rev-parse --short main
  27467df
  1290a4e
  7376d94
  $ git merge-base --is-ancestor origin/main HEAD && echo "origin/main is an ancestor of HEAD"
  origin/main is an ancestor of HEAD
  $ git diff --stat origin/main -- 'docs/**/verification.md' 'docs/**/review.md'
  $ git diff --stat main -- 'docs/**/verification.md' 'docs/**/review.md'
   docs/features/pr-body-preflight/review.md       | 512 ++++++++++++++++++++++++
   docs/features/pr-body-preflight/verification.md | 509 +++++++++++++++++++++++
   2 files changed, 1021 insertions(+)
  $ git log --oneline origin/main..HEAD -- docs/features/pr-body-preflight/ | wc -l
         0
  $ git log --oneline -1 origin/main -- docs/features/pr-body-preflight/verification.md
  1290a4e feat: refuse a gh pr create whose body would fail detector B (#991)
  ```
  ```
  control: real tree, 77 run(s) with a verification.md
    (a) cutoff 2026-10-17, unedited: 0 H problem(s)
        artifacts the roll-up judges at the real cutoff: 0
    (b) cutoff 0000-01-01, unedited: 0 H problem(s); artifacts judged: 77
        in-memory edit of docs/fixes/toolsmith-mine-pr-permissions/verification.md Summary:
          before: ['**7 PASS, 0 FAIL, 2 NOT YET VERIFIABLE.** Every criterion that can be', 'is not yet *proven*, and the proof is a Ship obligation, not an offline']
          after:  ['**7 PASS, 0 FAIL, 2  VERIFIABLE.** Every criterion that can be', 'is  *proven*, and the proof is a Ship obligation, not an offline']
    (c) cutoff 0000-01-01, Summary stripped: ['H: docs/fixes/toolsmith-mine-pr-permissions/verification.md:16 summary "Summary" neither counts nor names the 2 criterion section(s) disclosed as not run (first: "Criterion 5 (brief) — the live check: a post-merge `workflow_dispatch` run whose output has no `rm: gh pr list failed: …` line", line 208); unknown never rolls up to pass']
    (d) cutoff 2026-10-17, Summary stripped: []
    file on disk unchanged: True
  ```
  Reading the control: (a) alone would be vacuous, because the real
  cutoff judges none of the 77 shipped files (all are dated before
  `2026-10-17`). (b) judges all 77 and finds 0, so every shipped Summary
  that sits over a labelled disclosure already names the kind. (c) shows
  the rule fires on real text once the naming is removed. (d) shows that
  the cutoff, not the content, is what grandfathers it.
- Result: PASS

### 8. CONTEXT.md defines the four claim kinds and the roll-up rule; the protocol states the rule once and links CONTEXT.md without redefining the kinds (PRD)

- Check: read both entries and the protocol section, count the rule
  phrase, and grep the protocol for a redefinition.
- Evidence:
  ```
  $ sed -n 113,125p CONTEXT.md
  **Claim kind**:
  What a line in a verification or review artifact rests on. Four kinds:
  **observed** (quoted output), **derived** (computed from observed),
  **inferred** (judgement) and **unknown** (not examined; what NOT RUN,
  skipped, deferred and n/a disclose).
  _Avoid_: confidence level

  **Fail-closed roll-up**:
  Unknown, unsupported, truncated and skipped never aggregate to pass. A
  Summary or Verdict counts or names every such item, and never reads as an
  unqualified pass over them. Detector H enforces it on a `verification.md`
  Summary dated on or after `ROLLUP_ADOPTED`.
  _Avoid_: rounding up, all green
  $ grep -c "never aggregate to pass" CONTEXT.md
  1
  $ sed -n 370,375p docs/pipeline-protocol.md
  ## Fail-closed roll-up

  Unknown, unsupported, truncated and skipped never aggregate to pass. A
  `verification.md` Summary and a `review.md` Verdict count or name every
  criterion that was not run, skipped, deferred or otherwise not examined,
  and never read as an unqualified pass over them. The claim kinds this
  $ grep -c 'rests on are defined in \[CONTEXT.md\]' docs/pipeline-protocol.md
  1
  $ sed -n 377,382p docs/pipeline-protocol.md
  Detector H enforces the verification half (ADR-0107): a `## Summary` must
  name the unknown kind when another section discloses NOT RUN under a
  labelled verdict. It judges artifacts whose frontmatter `date:` is on or
  after `ROLLUP_ADOPTED` in `gates.py`, and undated ones; earlier artifacts
  are grandfathered. Nothing gates `review.md`; its template carries the
  $ grep -n "derived (computed" docs/pipeline-protocol.md; echo "protocol-grep exit=$?"
  protocol-grep exit=1
  ```
  Line 376 is not quoted, on purpose: it holds the protocol's relative
  link to CONTEXT.md, and detector I resolves links inside fences from
  this file's directory, where that link would dangle. The `grep -c`
  above shows the link is there.
- Result: PASS

### 9. The verify template's Summary guidance and the review template's Verdict guidance carry the rule (PRD)

- Check: read both placeholders, plus `skills/verify/SKILL.md` step 4
  (the breakdown adds that one).
- Evidence:
  ```
  $ sed -n 9,13p skills/verify/TEMPLATE.md
  ## Summary

  <Pass/fail counts and the one-sentence verdict. Count or name every NOT RUN
  / unknown criterion, and never read as an unqualified pass over them (the
  fail-closed roll-up; claim kinds in the plugin's CONTEXT.md).>
  $ grep -n -A4 "## Verdict" skills/review/TEMPLATE.md
  26:## Verdict
  27-
  28-<Ready to ship, or what blocks it. Count or name every pass that was not
  29-run or is unknown, and never read as an unqualified pass over them (the
  30-fail-closed roll-up; claim kinds in the plugin's CONTEXT.md).>
  $ sed -n 29,32p skills/verify/SKILL.md
     summary of it), and pass/fail. The artifact's `## Summary` counts or
     names every NOT RUN / unknown criterion and never reads as an
     unqualified pass over them (the fail-closed roll-up; claim kinds in
     `../../CONTEXT.md`). Detector H refuses one that does not (ADR-0107).
  ```
- Result: PASS

### 10. An ADR recording the rule and the cutoff exists, marked provisional (PRD)

- Check: list the ADR and read its head.
- Evidence:
  ```
  $ ls docs/adr | grep 0107
  0107-a-summary-never-rolls-unknown-up-to-pass.md
  $ head -8 docs/adr/0107-a-summary-never-rolls-unknown-up-to-pass.md
  # A verification Summary never rolls a disclosed NOT RUN up into a pass

  - Status: provisional
  - Date: 2026-10-17

  Recorded by the `fail-closed-roll-up` feature run
  (`docs/features/fail-closed-roll-up/`), unattended, so it is provisional.
  ```
- Result: PASS

### 11. The CI battery passes and detector E is clean after `update-manifest`, with the gates.py payload mirror updated (PRD)

- Check: the four CI commands, then detector E directly, a stray-patch
  sweep, `update-manifest`, and `git status --porcelain` (regenerating
  changes nothing, so the committed manifest is already current), and a
  byte-compare of the payload copies.
- Evidence:
  ```
  $ python3 run_tests.py; echo "run_tests exit=$?"
  run_tests exit=0
  tests: 3303 tests across 106 modules in 18.8s on 8 workers, 0 problem(s)
  $ python3 lint.py; echo "lint exit=$?"
  lint: 0 problem(s) across 34 skills
  lint exit=0
  $ python3 kb.py drift; echo "drift exit=$?"
  drift: 0 problem(s)
  drift exit=0
  $ python3 gates.py && python3 gates.py --selftest; echo "gates exit=$?"
  gates: 0 problem(s)
  selftest: ok
  gates exit=0
  ```
  ```
  detector E (check_scaffold_sync): []
  $ find factory/templates \( -name '*.orig' -o -name '*.rej' \) | wc -l
         0
  $ python3 factory_init.py update-manifest; echo "update-manifest exit=$?"
  factory-init: 0 problem(s)
  update-manifest exit=0
  $ git status --porcelain; echo "--- porcelain end"
  --- porcelain end
  $ cmp gates.py factory/templates/tools/factory/gates.py && cmp gates_selftest.py factory/templates/tools/factory/gates_selftest.py && echo "payload copies byte-identical"
  payload copies byte-identical
  ```
- Result: PASS

### B1. Every section dict from `verification_sections` carries `names_unknown`, true for an unfenced `unknown` and false when the word is only fenced (breakdown, Roll-up rule tests)

- Check: the dedicated test, and the fence case, both from criterion 1's run.
- Evidence:
  ```
  test_sections_record_an_unfenced_unknown_word (tests.test_gates.TestEvidenceRollUp.test_sections_record_an_unfenced_unknown_word) ... ok
  test_unknown_word_only_inside_a_fence_does_not_count (tests.test_gates.TestEvidenceRollUp.test_unknown_word_only_inside_a_fence_does_not_count) ... ok
  ```
- Result: PASS

### B2. The selftest defect fixture plants a rolled-up Summary and H's expect requires `neither counts nor names` (breakdown, Roll-up rule tests)

- Check: grep the selftest module, then run the selftest (it fails if the
  planted defect is not caught).
- Evidence:
  ```
  $ grep -n "neither counts nor names" gates_selftest.py
  620:               "neither counts nor names")
  $ python3 gates.py --selftest
  selftest: ok
  ```
- Result: PASS

### B3. One section parse, `check_evidence_honesty` unchanged in code, and no new import edge (breakdown, Roll-up rule in detector H)

- Check: the hunks of `gates.py` against the base, whether any changed
  line mentions `check_evidence_honesty`, the import lines that changed,
  and the dual-membership pin.
- Evidence:
  ```
  --- hunks of gates.py vs origin/main:
  @@ -44,2 +44,5 @@ ai-tooling suite where the rule is the same idea):
  @@ -99 +102 @@ from knowledge_plane import (ADR_TOKEN, CLOSES_TOKEN, PRD_TOKEN, WO_TOKEN,
  @@ -222,0 +226,20 @@ VERDICT_LEAD = re.compile(r"^[\s*_`\"'“‘([]+")
  @@ -1129,2 +1152,4 @@ def verification_sections(text):
  @@ -1140 +1165 @@ def verification_sections(text):
  @@ -1160,0 +1186,2 @@ def verification_sections(text):
  @@ -1167,0 +1195,38 @@ def verification_sections(text):
  @@ -1204,0 +1270,4 @@ def evidence_problems(text):
  --- check_evidence_honesty lines changed:
  0
  --- import lines:
  -from protocol import read_frontmatter
  +from protocol import parse_frontmatter, read_frontmatter
  $ python3 -m unittest tests.test_dual_membership
  Ran 3 tests in 0.317s

  OK
  ```
  `_rollup_problems` reads the dicts that `verification_sections` returns
  and calls `_is_disclosure` (gates.py lines 1203-1230, read in full). No
  heading regex was added.
- Result: PASS

### B4. Payload copies byte-identical, `tests.test_factory_init` green, and `.claude-plugin/plugin.json` untouched (breakdown, Payload mirror)

- Check: the byte-compare is in criterion 11. Run the factory-init tests
  and diff `plugin.json` against the base.
- Evidence:
  ```
  $ python3 -m unittest tests.test_factory_init
  Ran 83 tests in 4.301s

  OK
  $ git diff --name-only origin/main -- .claude-plugin/plugin.json; echo "--- end"
  --- end
  ```
- Result: PASS

### B5. `skills/review/SKILL.md` unchanged, and the verify template's heading is still exactly `## Summary` (breakdown, Templates)

- Check: diff the review SKILL.md against the base, and grep the heading.
- Evidence:
  ```
  $ git diff --stat origin/main -- skills/review/SKILL.md; echo "--- end"
  --- end
  $ grep -n '^## Summary' skills/verify/TEMPLATE.md
  9:## Summary
  ```
- Result: PASS

### B6. `python3 one_owner.py` reports no `one-owner:` problem naming the new constants (breakdown, Whole-repo verify)

- Check: run the advisory pass on HEAD and count lines that name the new
  constants. Run it on a clean clone at the base (`1290a4e`) and diff the
  two problem lists, to show the 9 findings come from before this run.
- Evidence:
  ```
  $ python3 one_owner.py > one_owner.out; echo "one_owner exit=$?"
  one_owner exit=1
  $ tail -1 one_owner.out
  one-owner: 9 problem(s)
  $ grep -c -E "ROLLUP_ADOPTED|SUMMARY_UNKNOWN_TERM|SUMMARY_TITLE" one_owner.out
  0
  $ diff <(sort one_owner_base.out) <(sort one_owner.out)   # base clone at 1290a4e vs HEAD
  10c10
  < one-owner: gates.py:265 ARCH_PLAIN_PATH and md_claims.py:61 PATH_CHARS state the same value — one fact, one owner
  ---
  > one-owner: gates.py:288 ARCH_PLAIN_PATH and md_claims.py:61 PATH_CHARS state the same value — one fact, one owner
  ```
  The `.out` files sit in the session scratchpad. Their paths are
  shortened above, and the output is unedited. The one difference is a
  line number. `ARCH_PLAIN_PATH` moved down 23
  lines because constants were added above it. The finding itself is the
  same.
- Result: PASS

## This artifact under its own rule

This file is dated `2026-10-17`, on the cutoff, so the roll-up judges
it. It holds 17 labelled verdicts and no labelled disclosure, so the rule
has nothing to fire on. Its Summary still names the kind ("0 NOT RUN"),
so it would pass if a disclosure were added. Output from the final run
before commit:

```
$ python3 -c "import gates; ..."  # this file
rollup applies: True
evidence_problems: []
summary names_unknown: [True]
labelled verdicts: 17
labelled disclosures: 0
$ python3 gates.py; echo "gates exit=$?"
gates: 0 problem(s)
gates exit=0
```

## Failures

None.

## Not verified

- A stamped repo receiving the new rule through a real payload update
  (PRD user story 6). This is not a success criterion. Detector E and
  `tests.test_factory_init` show the payload copy is current and
  byte-identical, but no stamped repo was updated here, so whether its
  pre-cutoff artifacts stay green is inferred, not observed. The
  `0000-01-01` control is the nearest evidence: once judged, every one of
  this repo's 77 artifacts passes.
- The review half of the rule is carried by the template only and is
  not gated. This is out of scope by design (PRD), so a non-compliant
  `review.md` Verdict would not be caught mechanically.
- The known dodges ADR-0107 records were not exercised end to end. The
  architecture accepts that a Summary which names the kind only in
  negation ("nothing was skipped") passes, and that renaming the heading
  escapes the rule.
