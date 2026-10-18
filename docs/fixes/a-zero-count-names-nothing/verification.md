---
stage: verify
run: maintenance:a-zero-count-names-nothing
date: 2026-10-17
assumptions:
  - "No prd.md exists for a maintenance run, so the criteria walked below are the autorun brief's Success criteria and defect.md's Expected clause, plus each work item's Accept line that no criterion covers, plus the orchestrator's false-positive sweep. defect.md's Work items stand in for breakdown.md (re-entry: implement), and all nine are checked, so the soft gate holds."
  - "The mutation control edits the real gates.py in place from a scratchpad script (mutate_zero_verify.py) and restores it in a finally block, the convention earlier controls in this repo used. Only the root copy is mutated, so the root-to-payload parity test failing under the mutation is expected noise, not a behaviour test."
  - "The false-positive sweep ignores the grandfather by calling the roll-up's own pieces (verification_sections then _rollup_problems) directly, skipping _rollup_applies, with origin/main's gates.py and HEAD's loaded side by side. A file with no Summary section is never judged by the roll-up, under either version."
  - "origin/main had not moved: `git fetch origin` left it at 6a89ee3, and `git merge-base --is-ancestor origin/main HEAD` held, so no merge was needed before verifying."
---

# Verification: a zero count names nothing

## Summary

13 criteria: 13 PASS, 0 FAIL, 0 NOT RUN. On HEAD `c7a287f`, the
retro's probe (criterion 9 flipped to NOT RUN under a "0 NOT RUN"
Summary) now returns H's existing roll-up string where origin/main
returns `[]`. Every zero shape is refused over a disclosed criterion
and passes without one. Non-zero and named mentions still pass, and
H's existing tests are unedited and green. Reverting the fix's one call
site brings back 12 behaviour failures. Applied to all 92 tracked
verification.md files with the grandfather ignored, the fix refuses
no file that origin/main passed (0 refused before, 0 after). The whole battery is green and the
real tree reports `gates: 0 problem(s)`. Next stage: Review.

## Criteria & evidence

### 1. The retro's probe now returns the roll-up string (it returned [] before)

Source: brief Success criterion 1, defect.md Expected. Capture's own
scratch scripts, `repro_zero.py` (through `gates.evidence_problems`)
and `repro_zero_tree.py` (through `gates.check_evidence_honesty`), are
re-run unchanged. They run first on a throwaway detached worktree of
origin/main (`6a89ee3`), which was removed afterwards, and then on HEAD.
The fixture is the tracked
`docs/fixes/a-quoted-date-dodges-the-cutoff/verification.md` with
criterion 9 flipped in memory. The file on disk is never edited.

- Check: `python3 <scratchpad>/repro_zero.py <tree>` and
  `repro_zero_tree.py <tree>` against origin/main and against HEAD
- Evidence:
  ```
  $ (worktree at origin/main) git rev-parse --short HEAD
  6a89ee3
  probe A (crit 9 NOT RUN, Summary unchanged): line 15 = '11 criteria: 11 PASS, 0 FAIL, 0 NOT RUN. On HEAD `8745052`, every'
    evidence_problems -> []
  check_evidence_honesty A (Summary unchanged) -> []

  $ (HEAD) git rev-parse --short HEAD
  c7a287f
  control (unflipped, '0 NOT RUN'): line 15 = '11 criteria: 11 PASS, 0 FAIL, 0 NOT RUN. On HEAD `8745052`, every'
    evidence_problems -> []
  probe A (crit 9 NOT RUN, Summary unchanged): line 15 = '11 criteria: 11 PASS, 0 FAIL, 0 NOT RUN. On HEAD `8745052`, every'
    evidence_problems -> [(13, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass')]
  probe B (crit 9 NOT RUN, ', 0 NOT RUN' removed): line 15 = '11 criteria: 11 PASS, 0 FAIL. On HEAD `8745052`, every'
    evidence_problems -> [(13, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass')]
  check_evidence_honesty A (Summary unchanged) -> ['H: docs/fixes/a-quoted-date-dodges-the-cutoff/verification.md:13 summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass']
  check_evidence_honesty B (zero count removed) -> ['H: docs/fixes/a-quoted-date-dodges-the-cutoff/verification.md:13 summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass']
  ```
- Result: PASS

### 2. Each zero shape is refused over a disclosure and passes without one

Source: brief Success criterion 2, and the Accept line for the
"Zero-shape tests first" work item. The probe C rows replay Capture's
four shapes on the real fixture. On origin/main, three of them returned
`[]`, and "0-skipped" was already refused. The new test methods cover
ten shapes, each one over a disclosed criterion and again with every
criterion passed.

- Check: probe C rows of `repro_zero.py` on origin/main and on HEAD;
  the new test methods run verbosely
- Evidence:
  ```
  (origin/main 6a89ee3)
  probe C [0 not run]: line 15 = '11 criteria: 11 PASS, 0 FAIL, 0 not run. On HEAD `8745052`, every'
    evidence_problems -> []
  probe C [zero skipped]: line 15 = '11 criteria: 11 PASS, 0 FAIL, zero skipped. On HEAD `8745052`, every'
    evidence_problems -> []
  probe C [0 N/A]: line 15 = '11 criteria: 11 PASS, 0 FAIL, 0 N/A. On HEAD `8745052`, every'
    evidence_problems -> []
  probe C [0-skipped]: line 15 = '11 criteria: 11 PASS, 0 FAIL, 0-skipped. On HEAD `8745052`, every'
    evidence_problems -> [(13, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass')]

  (HEAD c7a287f)
  probe C [0 not run]: line 15 = '11 criteria: 11 PASS, 0 FAIL, 0 not run. On HEAD `8745052`, every'
    evidence_problems -> [(13, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass')]
  probe C [zero skipped]: line 15 = '11 criteria: 11 PASS, 0 FAIL, zero skipped. On HEAD `8745052`, every'
    evidence_problems -> [(13, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass')]
  probe C [0 N/A]: line 15 = '11 criteria: 11 PASS, 0 FAIL, 0 N/A. On HEAD `8745052`, every'
    evidence_problems -> [(13, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass')]
  probe C [0-skipped]: line 15 = '11 criteria: 11 PASS, 0 FAIL, 0-skipped. On HEAD `8745052`, every'
    evidence_problems -> [(13, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass')]

  $ python3 -m unittest -v tests.test_gates.TestEvidenceRollUp tests.test_gates.TestEvidenceHonesty 2>&1 | grep -E "zero|retro_probe|hyphenated|named_mention|^Ran|^OK|FAIL|ERROR"
  test_hyphenated_zero_over_a_disclosure_stays_refused (tests.test_gates.TestEvidenceRollUp.test_hyphenated_zero_over_a_disclosure_stays_refused) ... ok
  test_non_zero_or_named_mention_over_a_disclosure_passes (tests.test_gates.TestEvidenceRollUp.test_non_zero_or_named_mention_over_a_disclosure_passes) ... ok
  test_sections_do_not_record_a_zero_count_as_naming (tests.test_gates.TestEvidenceRollUp.test_sections_do_not_record_a_zero_count_as_naming) ... ok
  test_wrapper_refuses_the_retro_probe (tests.test_gates.TestEvidenceRollUp.test_wrapper_refuses_the_retro_probe) ... ok
  test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) ... ok
  test_zero_count_summary_with_no_disclosure_passes (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_with_no_disclosure_passes) ... ok
  Ran 68 tests in 0.085s
  OK
  ```
- Result: PASS

### 3. Non-zero and named mentions still pass, and H's existing tests are unedited

Source: brief Success criterion 3, and the Accept line for the "Guards
that stay green" work item. The branch adds 71 lines to
`tests/test_gates.py` and deletes none, so every existing H test runs
unedited. The guard method covers "1 NOT RUN", "2 skipped", "criterion
4 was not run", the mixed "0 NOT RUN, 1 skipped", "10 NOT RUN" and
three more. It passes in criterion 2's run and stays green under the
mutation in criterion 4.

- Check: `git diff --numstat` over `tests/`; the guard test from
  criterion 2's run
- Evidence:
  ```
  $ git diff --numstat origin/main...HEAD -- tests/
  71	0	tests/test_gates.py
  test_non_zero_or_named_mention_over_a_disclosure_passes (tests.test_gates.TestEvidenceRollUp.test_non_zero_or_named_mention_over_a_disclosure_passes) ... ok
  test_hyphenated_zero_over_a_disclosure_stays_refused (tests.test_gates.TestEvidenceRollUp.test_hyphenated_zero_over_a_disclosure_stays_refused) ... ok
  ```
- Result: PASS

### 4. Control: the new tests catch a revert of the fix

Source: the Accept line for the "Zero-shape tests first" work item
("each fails before the fix"), and the orchestrator's instruction for
this stage. The scratch script `mutate_zero_verify.py` changes the fix's
one call site, `if _names_unknown(line):`, back to origin/main's `if
SUMMARY_UNKNOWN_TERM.search(line):`. It proves that the mutation landed,
both textually and by probing the reloaded parser. Then it runs the
WHOLE suite through `run_tests.py`, restores the file, and compares the
bytes. Under the mutation there are 12 behaviour failures: all 10
zero-shape subtests, the wrapper's retro probe, and the section-level
`names_unknown` test. The 13th failure is the parity test, expected
because only the root copy was mutated. The no-disclosure, guard and
hyphen tests stay green, as they should, because they pass both before
and after the fix.

- Check: `python3 <scratchpad>/mutate_zero_verify.py`, then `git status --short`
- Evidence:
  ```
  landed: True
  probe names_unknown for '0 NOT RUN' -> True
  suite rc: 1
  suite tail: tests: 3318 tests across 106 modules in 14.0s on 8 workers, 2 problem(s)
     FAIL: test_every_mirrored_root_file_matches_its_payload_copy (tests.test_factory_init.TestRealTreeMirrors.test_every_mirrored_root_file_matches_its_payload_copy) (mirror='gates.py')
     FAIL: test_sections_do_not_record_a_zero_count_as_naming (tests.test_gates.TestEvidenceRollUp.test_sections_do_not_record_a_zero_count_as_naming)
     FAIL: test_wrapper_refuses_the_retro_probe (tests.test_gates.TestEvidenceRollUp.test_wrapper_refuses_the_retro_probe)
     FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, **0** NOT RUN.')
     FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, 0 FAIL, 0 NOT RUN.')
     FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, 0 N/A.')
     FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, 0 criteria skipped.')
     FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, 0 not run.')
     FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, ZERO deferred.')
     FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, zero skipped.')
     FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS; no criteria were skipped.')
     FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS; none skipped.')
     FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS; nothing was skipped.')
  restored: True
  $ git status --short
  $
  ```
- Result: PASS

### 5. The negated zero is pinned, and its limit is written down

Source: the Accept line for the "Negated zero" work item. Three of the
zero shapes are negations, and criterion 4 shows each one failing
under the revert. The two-word limit carries a `lean:` marker in
`gates.py` and appears in ADR-0108's Consequences, together with the
"nothing was skipped except" side effect.

- Check: grep the subtests, the `lean:` marker and the ADR
- Evidence:
  ```
  $ grep -nE "no criteria were skipped|none skipped|nothing was skipped" tests/test_gates.py
  3003:                   "1 PASS; no criteria were skipped.",
  3004:                   "1 PASS; none skipped.",
  3005:                   "1 PASS; nothing was skipped.")
  $ grep -n "lean: a longer" gates.py
  258:# lean: a longer negation ("no live check was skipped") still names; widen
  $ grep -n -i "no live check\|nothing was skipped except" docs/adr/0108-a-zero-count-names-nothing.md
  60:- A longer negation ("no live check was skipped", two words between the
  65:  one criterion it disclosed ("nothing was skipped except live
  ```
- Result: PASS

### 6. The fix stays inside the one section parse

Source: the Accept line for "The fix" work item. There is still one
`verification_sections`. Its per-line loop calls `_names_unknown`,
which reads `SUMMARY_ZERO_COUNT` over the text before each match. The
comment's "naming covers counting" premise and the docstring both say
"except at zero". The RED to GREEN half of the Accept line is shown in
criteria 2 and 4.

- Check: grep for the parser, the helper and the comment
- Evidence:
  ```
  $ grep -cF 'def verification_sections' gates.py
  1
  $ grep -n "_names_unknown\|SUMMARY_ZERO_COUNT\|def verification_sections" gates.py
  234:# item is unknown, so a match SUMMARY_ZERO_COUNT ends right before names
  260:SUMMARY_ZERO_COUNT = re.compile(
  1166:def _names_unknown(line):
  1169:    count (SUMMARY_ZERO_COUNT). Judged per match, so "0 NOT RUN, 1
  1171:    return any(not SUMMARY_ZERO_COUNT.search(line, 0, match.start())
  1175:def verification_sections(text):
  1195:    unfenced SUMMARY_UNKNOWN_TERM word that no SUMMARY_ZERO_COUNT directly
  1196:    precedes, judged per match: see _names_unknown) is recorded for every
  1228:            if _names_unknown(line):
  ```
- Result: PASS

### 7. The verify template says a zero count names nothing

Source: the Accept line for the "Verify template wording" work item.

- Check: `sed -n 11,14p skills/verify/TEMPLATE.md`
- Evidence:
  ```
  <Pass/fail counts and the one-sentence verdict. Count or name every NOT RUN
  / unknown criterion, and never read as an unqualified pass over them (the
  fail-closed roll-up; claim kinds in the plugin's CONTEXT.md). A zero count
  ("0 NOT RUN") names nothing: re-count after any criterion changes.>
  ```
- Result: PASS

### 8. ADR-0108 states the rule and supersedes ADR-0107's naming clause

Source: the Accept line for the "ADR" work item. ADR-0108 is
provisional, records the rejected "count must match" option, and is
indexed. ADR-0107's status and index row read "superseded in part".
Criterion 13 shows `gates.py` and `kb.py drift` clean.

- Check: the ADR head, the rejected option, the index rows (link column cut,
  since gates resolve links even inside fences), ADR-0107's status
- Evidence:
  ```
  # A zero count in a verification Summary names nothing
  - Status: provisional
  - Date: 2026-10-17
  48:- **The count must match** (compare the Summary's numbers with the
  $ grep -n "^| \[010[78]\]" docs/adr/README.md | cut -d'|' -f1,3,4
  130:| A verification Summary never rolls a disclosed NOT RUN up into a pass | superseded in part by ADR-0108 (the naming clause; provisional) 
  131:| A zero count in a verification Summary names nothing | provisional 
  3:- Status: superseded in part by ADR-0108 (the naming clause; provisional)
  ```
- Result: PASS

### 9. Payload mirror and manifest are coherent (detector E)

Source: brief Success criterion 5, and the Accept line for the
"Payload mirror and manifest" work item. `.claude-plugin/plugin.json`
does not appear in the branch diff.

- Check: `cmp`, `shasum`, the manifest entry, a `find` for stray
  patch files, and `gates.check_scaffold_sync`
- Evidence:
  ```
  $ cmp gates.py factory/templates/tools/factory/gates.py && echo "cmp: identical"
  cmp: identical
  $ shasum -a 256 gates.py factory/templates/tools/factory/gates.py
  bc9614eba47c68c58145a10cfee7336cf99649171d11261fdadbe820782edb0f  gates.py
  bc9614eba47c68c58145a10cfee7336cf99649171d11261fdadbe820782edb0f  factory/templates/tools/factory/gates.py
  44:    "templates/tools/factory/gates.py": "bc9614eba47c68c58145a10cfee7336cf99649171d11261fdadbe820782edb0f",
  stray patch files: 0
  check_scaffold_sync (E) -> []
  $ git diff origin/main...HEAD --stat -- skills/ factory/templates/ .claude-plugin/
   factory/templates/tools/factory/gates.py | 32 ++++++++++++++++++++++++++++----
   skills/verify/TEMPLATE.md                |  3 ++-
   2 files changed, 30 insertions(+), 5 deletions(-)
  ```
- Result: PASS

### 10. The backlog claim is in place

Source: the Accept line for the "Backlog claim" work item.

- Check: grep for the claim on `docs/backlog.md`
- Evidence:
  ```
  $ grep -n 'claimed: maintenance:a-zero-count-names-nothing' docs/backlog.md | grep -o '^[0-9]*:\|(claimed: [^)]*)$'
  125:
  (claimed: maintenance:a-zero-count-names-nothing)
  ```
- Result: PASS

### 11. The real tree has 0 problems, and no shipped artifact was edited

Source: brief Success criterion 4. Over every prd.md, defect.md,
verification.md and review.md, the diff from origin/main lists only
this run's own new defect.md. This file is added by this stage's
commit.

- Check: `git diff --stat origin/main` over the four artifact kinds; `python3 gates.py`
- Evidence:
  ```
  $ git diff --stat origin/main -- 'docs/**/prd.md' 'docs/**/defect.md' 'docs/**/verification.md' 'docs/**/review.md'
   docs/fixes/a-zero-count-names-nothing/defect.md | 257 ++++++++++++++++++++++++
   1 file changed, 257 insertions(+)
  $ python3 gates.py
  gates: 0 problem(s)
  ```
- Result: PASS

### 12. False-positive sweep: no honest artifact is newly refused

Source: the orchestrator's instruction for this stage, which tests
Expected's "an honest Summary that passes today keeps passing" beyond
the cutoff. `fp_sweep.py` applies the roll-up to every tracked
verification.md, grandfather ignored, with origin/main's and HEAD's
`gates.py`. `fp_detail.py` lists the files that have a disclosed
criterion and their Summary hits. Four of those files have no Summary
section, so the roll-up never judges them. The other three each name the
unknown kind with a mention that no zero precedes. One of them,
codex-style-standards-enforcement, also has a real "0 not verified" hit
that now correctly names nothing, next to a "1 DEFERRED" that names.

- Check: `python3 <scratchpad>/fp_sweep.py`, then `fp_detail.py`
- Evidence:
  ```
  tracked verification.md: 92; with >=1 disclosed criterion: 7
  roll-up refusals, grandfather ignored: before (origin/main) 0, after (HEAD) 0
  newly refused: 0; newly cleared: 0
  ```
  ```
  - docs/features/codex-style-standards-enforcement/verification.md disclosed=1 summary hits (line, term, zero-preceded)=[(14, 'DEFERRED', False), (14, 'not verified', True), (26, 'not verified', False), (30, 'deferred', False)]
  - docs/features/orchestrator/verification.md disclosed=7 summary hits (line, term, zero-preceded)=[(19, 'unmet', False), (19, 'unmet', False), (20, 'pending', False), (23, 'unknown', False)]
  - docs/fixes/a-dead-cli-scores-as-a-pass/verification.md disclosed=1 summary hits (line, term, zero-preceded)=[]
  - docs/fixes/a-forbid-only-case-checks-nothing/verification.md disclosed=1 summary hits (line, term, zero-preceded)=[]
  - docs/fixes/a-gate-wait-is-not-spend/verification.md disclosed=1 summary hits (line, term, zero-preceded)=[]
  - docs/fixes/the-front-door-miscounts-its-own-tools/verification.md disclosed=1 summary hits (line, term, zero-preceded)=[]
  - docs/fixes/toolsmith-mine-pr-permissions/verification.md disclosed=2 summary hits (line, term, zero-preceded)=[(18, 'NOT YET', False), (31, 'not yet', False)]
  $ for f in a-dead-cli-scores-as-a-pass a-forbid-only-case-checks-nothing a-gate-wait-is-not-spend the-front-door-miscounts-its-own-tools; do echo "$f: $(grep -c '^#* *Summary' docs/fixes/$f/verification.md)"; done
  a-dead-cli-scores-as-a-pass: 0
  a-forbid-only-case-checks-nothing: 0
  a-gate-wait-is-not-spend: 0
  the-front-door-miscounts-its-own-tools: 0
  ```
- Result: PASS

### 13. The whole-repo battery passes

Source: brief Success criterion 5, and the Accept line for the
"Whole-repo checks" work item.

- Check: the four CI commands, run on HEAD `c7a287f` with the tree clean
- Evidence:
  ```
  $ python3 run_tests.py
  tests: 3318 tests across 106 modules in 14.1s on 8 workers, 0 problem(s)
  $ python3 lint.py
  lint: 0 problem(s) across 34 skills
  $ python3 kb.py drift
  drift: 0 problem(s)
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

## Failures

none.

## Not verified

- **Behaviour in a stamped repo after its next payload update.** Not
  exercised. Criterion 9 proves that the payload copy equals the root
  copy and matches its manifest pin.
- **Zero-count cases in `gates.py --selftest`.** These are out of scope
  per the brief, and Capture's note records it. The selftest's
  `rolledup` fixture has no zero-count row, so a stamped repo, which
  runs only the selftest, would not catch a regression of this fix.
- **Over-refusal edge shapes.** Probed by hand, not tested. "0 FAIL NOT
  RUN: criterion 9", with no punctuation after the zero's one word,
  reads as a zero, and so does "no dispatch skipped (criterion 9)". Both
  fail closed with H's actionable string. No tracked artifact uses
  either shape (criterion 12). This is for Review to weigh.
