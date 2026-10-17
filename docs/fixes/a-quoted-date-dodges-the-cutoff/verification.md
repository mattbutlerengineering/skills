---
stage: verify
run: maintenance:a-quoted-date-dodges-the-cutoff
date: 2026-10-17
assumptions:
  - "No prd.md exists for a maintenance run, so the criteria walked below are the autorun brief's Success criteria and defect.md's Expected clause, plus each work item's Accept line that no criterion covers. defect.md's Work items stand in for breakdown.md (re-entry: implement), and all eight are checked, so the soft gate holds."
  - "The mutation control edits the real gates.py in place from a scratchpad script (mutate_verify.py) and restores it in a finally block, the convention earlier controls in this repo used. Only the root copy is mutated, so the root-to-payload parity test failing under the mutation is expected noise, not a behaviour test."
  - "origin/main had not moved: `git fetch origin` then `git merge-base --is-ancestor origin/main HEAD` held (origin/main 461803a), so no merge was needed before verifying."
---

# Verification: a quoted date dodges the cutoff

## Summary

11 criteria: 11 PASS, 0 FAIL, 0 NOT RUN. On HEAD `8745052`, every
dodge shape (double-quoted, single-quoted, empty, non-ISO post-cutoff
dates) is judged by O, M and H through the one `_grandfathered`
helper, and ISO pre-cutoff dates (plain, quoted, datetime) stay
grandfathered. The mutation control shows the new tests are not
vacuous. The whole battery is green and the real tree reports
`gates: 0 problem(s)`. Next stage: Review.

## Criteria & evidence

### 1. Capture's reproduction on HEAD: O and M judge every dodge shape

Source: brief Success criterion 1, defect.md Expected. This is the
defect brief's own scratch script, `repro_om.py`, re-run unchanged on
HEAD. It uses the same fixtures, the same real parse, and the public
functions `gates.check_prd_coverage(root)` and
`gates.check_capture_completeness(root)`. At `e1dbb9e`, Capture quoted
`[]` for all eight dodge rows. Each one now returns the detector's
existing problem string. The ISO pre-cutoff control is still `[]`.

- Check: `python3 <scratchpad>/repro_om.py` at HEAD
- Evidence:
  ```
  $ git rev-parse --short HEAD
  8745052
  O  date: 2026-10-20     [control: ISO post-cutoff] -> ['O: docs/features/demo/prd.md:17 PRD-0001 §Out of scope is cited by no breakdown row and carries no coverage waiver']
  M  date: 2026-10-20     [control: ISO post-cutoff] -> ["M: docs/fixes/demo/defect.md missing required section 'Reproduction / Evidence'", "M: docs/fixes/demo/defect.md missing required section 'Root-cause hypothesis'", "M: docs/fixes/demo/defect.md missing required section 'Blast radius'", "M: docs/fixes/demo/defect.md missing required section 'Ruled out'"]
  O  date: "2026-10-20"   [double-quoted post-cutoff] -> ['O: docs/features/demo/prd.md:17 PRD-0001 §Out of scope is cited by no breakdown row and carries no coverage waiver']
  M  date: "2026-10-20"   [double-quoted post-cutoff] -> ["M: docs/fixes/demo/defect.md missing required section 'Reproduction / Evidence'", "M: docs/fixes/demo/defect.md missing required section 'Root-cause hypothesis'", "M: docs/fixes/demo/defect.md missing required section 'Blast radius'", "M: docs/fixes/demo/defect.md missing required section 'Ruled out'"]
  O  date: '2026-10-20'   [single-quoted post-cutoff] -> ['O: docs/features/demo/prd.md:17 PRD-0001 §Out of scope is cited by no breakdown row and carries no coverage waiver']
  M  date: '2026-10-20'   [single-quoted post-cutoff] -> ["M: docs/fixes/demo/defect.md missing required section 'Reproduction / Evidence'", "M: docs/fixes/demo/defect.md missing required section 'Root-cause hypothesis'", "M: docs/fixes/demo/defect.md missing required section 'Blast radius'", "M: docs/fixes/demo/defect.md missing required section 'Ruled out'"]
  O  date:                [empty] -> ['O: docs/features/demo/prd.md:17 PRD-0001 §Out of scope is cited by no breakdown row and carries no coverage waiver']
  M  date:                [empty] -> ["M: docs/fixes/demo/defect.md missing required section 'Reproduction / Evidence'", "M: docs/fixes/demo/defect.md missing required section 'Root-cause hypothesis'", "M: docs/fixes/demo/defect.md missing required section 'Blast radius'", "M: docs/fixes/demo/defect.md missing required section 'Ruled out'"]
  O  date: 20/10/2026     [non-ISO post-cutoff] -> ['O: docs/features/demo/prd.md:17 PRD-0001 §Out of scope is cited by no breakdown row and carries no coverage waiver']
  M  date: 20/10/2026     [non-ISO post-cutoff] -> ["M: docs/fixes/demo/defect.md missing required section 'Reproduction / Evidence'", "M: docs/fixes/demo/defect.md missing required section 'Root-cause hypothesis'", "M: docs/fixes/demo/defect.md missing required section 'Blast radius'", "M: docs/fixes/demo/defect.md missing required section 'Ruled out'"]
  O  date: 2026-01-01     [control: ISO pre-cutoff] -> []
  M  date: 2026-01-01     [control: ISO pre-cutoff] -> []
  ```
- Result: PASS

### 2. A quoted or datetime pre-cutoff date is still grandfathered (O, M)

Source: brief Success criterion 1, second sentence. This is a
supplementary scratch script (`repro_extra.py`), using the same O and M
fixtures as `repro_om.py`.

- Check: `python3 <scratchpad>/repro_extra.py` (O/M rows)
- Evidence:
  ```
  O  date: "2026-01-01"           [quoted pre-cutoff] -> []
  M  date: "2026-01-01"           [quoted pre-cutoff] -> []
  O  date: 2026-01-01T09:30:00Z   [datetime pre-cutoff] -> []
  M  date: 2026-01-01T09:30:00Z   [datetime pre-cutoff] -> []
  ```
- Result: PASS

### 3. H's behaviour is unchanged, and H's shapes go through the shared helper

Source: brief Success criterion 2. The branch adds 55 lines to
`tests/test_gates.py` and deletes none. The added lines sit only in
`TestCaptureCompleteness` (M) and `TestPrdCoverage` (O), so H's
`TestEvidenceRollUp` and `TestEvidenceHonesty` are untouched and pass.
Through the public `gates.evidence_problems`, H judges every dodge
shape against `ROLLUP_ADOPTED` and grandfathers the three pre-cutoff
spellings, the same as O and M.

- Check: `git diff --numstat` and the hunk headers over `tests/`; the
  four affected test classes run verbosely; the H rows of
  `repro_extra.py`
- Evidence:
  ```
  $ git diff --numstat origin/main...HEAD -- tests/
  55	0	tests/test_gates.py
  $ git diff origin/main...HEAD -- tests/ | grep -E "^@@|^[-+] *(class|def) "
  @@ -1050,6 +1050,45 @@ class TestCaptureCompleteness(unittest.TestCase):
  +    def dated(self, tree, value):
  +    def test_non_iso_or_quoted_post_cutoff_date_is_judged(self):
  +    def test_quoted_or_datetime_pre_cutoff_date_is_grandfathered(self):
  @@ -1854,6 +1893,22 @@ class TestPrdCoverage(unittest.TestCase):
  +    def test_non_iso_or_quoted_post_cutoff_date_is_judged(self):
  +    def test_quoted_or_datetime_pre_cutoff_date_is_grandfathered(self):

  $ python3 -m unittest -v tests.test_gates.TestEvidenceRollUp tests.test_gates.TestEvidenceHonesty tests.test_gates.TestPrdCoverage tests.test_gates.TestCaptureCompleteness 2>&1 | grep -E "grandfathered|cutoff|^Ran|^OK|FAIL|ERROR"
  test_artifact_dated_before_the_cutoff_is_grandfathered (tests.test_gates.TestEvidenceRollUp.test_artifact_dated_before_the_cutoff_is_grandfathered) ... ok
  test_cutoff_is_pinned (tests.test_gates.TestEvidenceRollUp.test_cutoff_is_pinned) ... ok
  test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestEvidenceRollUp.test_non_iso_or_quoted_post_cutoff_date_is_judged) ... ok
  test_quoted_or_datetime_pre_cutoff_date_is_grandfathered (tests.test_gates.TestEvidenceRollUp.test_quoted_or_datetime_pre_cutoff_date_is_grandfathered) ... ok
  test_a_missing_date_is_not_grandfathered (tests.test_gates.TestPrdCoverage.test_a_missing_date_is_not_grandfathered) ... ok
  test_a_prd_predating_adoption_is_grandfathered (tests.test_gates.TestPrdCoverage.test_a_prd_predating_adoption_is_grandfathered) ... ok
  test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestPrdCoverage.test_non_iso_or_quoted_post_cutoff_date_is_judged) ... ok
  test_quoted_or_datetime_pre_cutoff_date_is_grandfathered (tests.test_gates.TestPrdCoverage.test_quoted_or_datetime_pre_cutoff_date_is_grandfathered) ... ok
  test_a_brief_dated_before_adoption_is_grandfathered (tests.test_gates.TestCaptureCompleteness.test_a_brief_dated_before_adoption_is_grandfathered) ... ok
  test_a_brief_dated_on_adoption_day_is_not_grandfathered (tests.test_gates.TestCaptureCompleteness.test_a_brief_dated_on_adoption_day_is_not_grandfathered) ... ok
  test_a_missing_date_is_not_grandfathered (tests.test_gates.TestCaptureCompleteness.test_a_missing_date_is_not_grandfathered) ... ok
  test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestCaptureCompleteness.test_non_iso_or_quoted_post_cutoff_date_is_judged) ... ok
  test_quoted_or_datetime_pre_cutoff_date_is_grandfathered (tests.test_gates.TestCaptureCompleteness.test_quoted_or_datetime_pre_cutoff_date_is_grandfathered) ... ok
  Ran 89 tests in 0.113s
  OK

  $ python3 <scratchpad>/repro_extra.py   (H rows)
  H  date: 2026-10-20             [control: ISO post-cutoff] -> [(9, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Criterion two", line 25); unknown never rolls up to pass')]
  H  date: "2026-10-20"           [double-quoted post-cutoff] -> [(9, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Criterion two", line 25); unknown never rolls up to pass')]
  H  date: '2026-10-20'           [single-quoted post-cutoff] -> [(9, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Criterion two", line 25); unknown never rolls up to pass')]
  H  date:                        [empty] -> [(9, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Criterion two", line 25); unknown never rolls up to pass')]
  H  date: 20/10/2026             [non-ISO post-cutoff] -> [(9, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Criterion two", line 25); unknown never rolls up to pass')]
  H  date: 2026-01-01             [control: ISO pre-cutoff] -> []
  H  date: "2026-01-01"           [quoted pre-cutoff] -> []
  H  date: 2026-01-01T09:30:00Z   [datetime pre-cutoff] -> []
  ```
- Result: PASS

### 4. Control: the new tests are not vacuous

Source: the brief's standing instruction for this stage. The scratch
script `mutate_verify.py` puts the body of `_grandfathered` back to
`return isinstance(date, str) and date < cutoff`. It proves that the
mutation landed, both textually and by probing the reloaded function.
Then it runs the WHOLE suite through `run_tests.py`, restores the
file, and compares the bytes.

Under the mutation, every dodge subtest fails in all three detectors:
O 4, M 4, H 5 (H's existing test also carries `16 Oct 2026`). The one
other failure is the root-to-payload parity test, which is expected
because only the root copy was mutated. The quoted and datetime
pre-cutoff tests still pass under the mutation. That is correct: a raw
compare also grandfathers them (`"` and `2026-01-01T…` both sort
before the cutoff). Those tests guard against over-correction, not
against this regression.

- Check: `python3 <scratchpad>/mutate_verify.py`, then `git status --short`
- Evidence:
  ```
  landed: True
  probe _grandfathered('"2026-10-20"', '2026-09-21') -> True
  suite rc: 1
  suite tail: tests: 3312 tests across 106 modules in 14.3s on 8 workers, 2 problem(s)
     FAIL: test_every_mirrored_root_file_matches_its_payload_copy (tests.test_factory_init.TestRealTreeMirrors.test_every_mirrored_root_file_matches_its_payload_copy) (mirror='gates.py')
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestCaptureCompleteness.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date="'2026-10-20'")
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestCaptureCompleteness.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='"2026-10-20"')
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestCaptureCompleteness.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='')
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestCaptureCompleteness.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='20/10/2026')
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestEvidenceRollUp.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date="'2026-10-20'")
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestEvidenceRollUp.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='"2026-10-20"')
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestEvidenceRollUp.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='')
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestEvidenceRollUp.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='16 Oct 2026')
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestEvidenceRollUp.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='20/10/2026')
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestPrdCoverage.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date="'2026-10-20'")
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestPrdCoverage.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='"2026-10-20"')
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestPrdCoverage.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='')
     FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestPrdCoverage.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='20/10/2026')
  restored: True
  $ git status --short
  $
  ```
- Result: PASS

### 5. One owner: the ISO-date pattern and the normalization appear once

Source: brief Success criterion 3, and the Accept line for the "One
helper" work item. These are fixed-string grep counts over `gates.py`.
The pattern literal, the quote-strip test, the one `.match` use and
the helper definition each appear once. The old `ROLLUP_ISO_DATE` name
is gone. `_grandfathered(` appears 4 times: the definition and the
three callers.

- Check: `grep -cF` per fixed string
- Evidence:
  ```
  grep -cF '\d{4}-\d{2}-\d{2}'          gates.py -> 1
  grep -cF 'in "\"'"'                   gates.py -> 1
  grep -cF 'ROLLUP_ISO_DATE'            gates.py -> 0
  grep -cF 'FRONTMATTER_ISO_DATE.match' gates.py -> 1
  grep -cF 'date < '                    gates.py -> 0
  grep -cF 'def _grandfathered'         gates.py -> 1
  grep -cF '_grandfathered('            gates.py -> 4
  ```
- Result: PASS

### 6. Three callers, and no raw compare is left

Source: the Accept line for the "Three callers" work item. H, O and M
each call the helper. No `isinstance(date, str) and date <` compare
remains in either copy, and grep exits 1 when nothing matches.

- Check: `grep -n` for the call sites and for the raw compare, in both copies
- Evidence:
  ```
  262:    r"^(\d{4}-\d{2}-\d{2})(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?"
  1213:def _grandfathered(date, cutoff):
  1222:    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
  1233:    return not _grandfathered(date, ROLLUP_ADOPTED)
  1445:        if _grandfathered(entry["prd_date"], COVERAGE_ADOPTED):
  1717:        if _grandfathered(frontmatter.get("date"), CAPTURE_ADOPTED):
  $ grep -nE 'isinstance\(date, str\) and date <' gates.py factory/templates/tools/factory/gates.py; echo "raw-compare hits: $?"
  raw-compare hits: 1
  ```
- Result: PASS

### 7. No comment or ADR text describes O or M as a live raw-string compare

Source: the Accept line for the "Comment and ADR text" work item. The
grep finds three mentions of a raw-string compare. All three are in
the past tense and say the compare has been replaced: the comment on
`FRONTMATTER_ISO_DATE` in `gates.py`, ADR-0073's new amendment, and
ADR-0107's two amendments. The ADR additions on this branch are shown
below.

- Check: grep for compare descriptions; the `+` lines of the ADR diff
- Evidence:
  ```
  gates.py:259:# raw-string compare let a quoted, empty or non-ISO value sort before the
  docs/adr/0073-standards-index-seam-and-detector-letters-k-m.md:175:compared the raw string, so a quoted, empty or non-ISO `date:` sorted
  docs/adr/0107-a-summary-never-rolls-unknown-up-to-pass.md:106:- **Grandfathered only by an ISO date.** The raw-string compare let a
  docs/adr/0107-a-summary-never-rolls-unknown-up-to-pass.md:125:seed above is done. Detectors O and M no longer keep their compare; H, O
  ---
  +Amended 2026-10-17 (maintenance run a-quoted-date-dodges-the-cutoff): "a
  +missing or unparseable date is NOT exempted" was false until now. `M`
  +compared the raw string, so a quoted, empty or non-ISO `date:` sorted
  +before `CAPTURE_ADOPTED` and was exempted. `M` now reads the date through
  +`gates._grandfathered`, shared with H and O: only a `YYYY-MM-DD` value
  +(quoted or a datetime is fine) before the cutoff is exempt, and anything
  +else is judged.
  +Amended 2026-10-17 (maintenance run a-quoted-date-dodges-the-cutoff): the
  +seed above is done. Detectors O and M no longer keep their compare; H, O
  +and M all grandfather through one private `gates._grandfathered(date,
  +cutoff)`, and `ROLLUP_ISO_DATE` is renamed `FRONTMATTER_ISO_DATE`, with
  +that helper as its only user.
  ```
- Result: PASS

### 8. Payload mirror and manifest are coherent (detector E)

Source: brief Success criterion 5, and the Accept line for the
"Payload mirror and manifest" work item. The two copies are
byte-identical. Their sha256 matches the manifest's pin. No stray
`.orig` or `.rej` file exists. Detector E returns no problems.

- Check: `cmp`, `shasum`, the manifest entry, `find`, and
  `gates.check_scaffold_sync`
- Evidence:
  ```
  $ cmp gates.py factory/templates/tools/factory/gates.py && echo "cmp: identical"
  cmp: identical
  $ shasum -a 256 gates.py factory/templates/tools/factory/gates.py
  b5d8e11b78cc8b6948dfb966d43d87e76f6b3c6c5a69c55b2e42ac795bfd1f62  gates.py
  b5d8e11b78cc8b6948dfb966d43d87e76f6b3c6c5a69c55b2e42ac795bfd1f62  factory/templates/tools/factory/gates.py
  $ grep -n "gates.py" factory/manifest.json
  44:    "templates/tools/factory/gates.py": "b5d8e11b78cc8b6948dfb966d43d87e76f6b3c6c5a69c55b2e42ac795bfd1f62",
  stray patch files:        0
  check_scaffold_sync (E) -> []
  ```
- Result: PASS

### 9. The backlog claim is in place

Source: the Accept line for the "Backlog claim" work item.

- Check: the tail of `docs/backlog.md` line 123
- Evidence:
  ```
  $ sed -n 123p docs/backlog.md | grep -o '(claimed: [^)]*)$'
  (claimed: maintenance:a-quoted-date-dodges-the-cutoff)
  ```
- Result: PASS

### 10. The real tree has 0 problems, and no shipped artifact was edited

Source: brief Success criterion 4. Over every shipped prd.md,
defect.md, verification.md and review.md, the diff from `origin/main`
lists only this run's own new defect.md. `python3 gates.py` passes on
the real tree.

- Check: `git diff --stat origin/main` over those four artifact kinds; `python3 gates.py`
- Evidence:
  ```
  $ git diff --stat origin/main -- 'docs/**/prd.md' 'docs/**/defect.md' 'docs/**/verification.md' 'docs/**/review.md'
   .../a-quoted-date-dodges-the-cutoff/defect.md      | 258 +++++++++++++++++++++
   1 file changed, 258 insertions(+)
  $ python3 gates.py
  gates: 0 problem(s)
  ```
- Result: PASS

### 11. The whole-repo battery passes

Source: brief Success criterion 5, and the Accept line for the
"Whole-repo checks" work item.

- Check: the four CI commands, run on HEAD with the tree clean
- Evidence:
  ```
  $ python3 run_tests.py
  tests: 3312 tests across 106 modules in 14.1s on 8 workers, 0 problem(s)
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
  exercised. No stamped repo was updated in this stage. Criterion 8
  proves that the payload copy equals the root copy and matches its
  manifest pin, and the root copy's behaviour is what criteria 1 to 4
  show.
- **Dodge-shape cases in `gates.py --selftest`.** These are out of
  scope by the brief, as Capture's note records. The selftest passes,
  but it has no quoted or non-ISO date fixture for O or M. A stamped
  repo, which runs only the selftest, would not catch a regression of
  this fix. This is a possible follow-up seed.
- **The pre-cutoff guard tests under the mutation.** By construction,
  they cannot distinguish the raw compare from the fix (criterion 4).
  They pin over-correction only. That is by design, not a gap in the
  dodge coverage.
