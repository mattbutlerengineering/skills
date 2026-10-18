---
stage: capture
run: maintenance:the-selftest-cannot-see-a-dodge
date: 2026-10-18
re-entry: implement
origin: docs/backlog.md seed (from session:2026-10-17), the selftest has no dodge-shape row for detectors H, O or M (the a-quoted-date-dodges-the-cutoff review's deferred Minor 2), widened by Owner decision 1 to one H zero-count roll-up row (the gap a-zero-count-names-nothing's Capture noted in its Notes)
assumptions: ["re-entry: implement, taken from the brief's reading (the orchestrator's, not an Owner answer) under the skill's rule that a scoped fix with no design decisions re-enters at Implement. The rows follow the existing expect/expect_clean pattern in selftest(), and Capture found no design question: the mutation proof is a scratchpad step, not a selftest that mutates itself", "Reproduction reverted O's and M's date checks at their call sites (a raw compare in place of the _grandfathered call), as the orchestrator allowed. The seed's own shape, a raw compare inside _grandfathered, was also run once and blinds O, M and H together; both shapes leave the selftest ok", "Each new selftest row is asserted under its own label and on a problem string that names its own artifact path, so a reverted fix fails the row that guards it. Read from the success criterion that the selftest prints a failure naming that row: H's existing expect() matches 'neither counts nor names' in any problem, so a new artifact added to the shared rolledup fixture would be masked by the existing rolledup row", "No meta-rule seed (a rule that every gate dodge test has a selftest twin). The brief leaves seeding it to Capture's judgement, and a unit test has no mechanical link to a selftest row, so a detector for it would have nothing to read; this run's rows close the four known gaps"]
---

# Defect: the selftest cannot see a dodge

## Defect (or Condition)

A stamped repo runs only `python3 tools/factory/gates.py --selftest`,
never this repo's `tests/`. That selftest (`gates_selftest.py`,
`selftest()`) exercises none of the three dodges fixed on 2026-10-17 and
2026-10-18 (#1002, #1018).

- **Observed.** The O fixture (`prd_coverage_fixture`) dates its PRD
  `{gates.COVERAGE_ADOPTED}`. The M fixtures date their defect.md
  `{gates.CAPTURE_ADOPTED}` or `2026-01-01`. The H `rolledup` artifact
  (`evidence_honesty_defect_fixture`) dates itself `2026-10-17` and its
  Summary reads "All criteria pass.". No fixture carries a quoted
  post-cutoff `date:`, and no Summary carries a zero count over a
  disclosed NOT RUN criterion. So a payload change that put back any of
  the four fixes below still prints `selftest: ok`, and every stamped
  repo keeps passing its `make check`.
- **Expected.** Each of the four fixes has a selftest row that turns the
  selftest red, naming that row, when the fix is reverted:
  1. O grandfathers a PRD only by an ISO `date:` before the cutoff
     (`_grandfathered`, called from `check_prd_coverage`).
  2. M does the same for a defect.md (`check_capture_completeness`).
  3. H's roll-up does the same for a verification.md
     (`_rollup_applies`).
  4. H's roll-up does not count a zero ("0 NOT RUN") as naming the
     unknown kind (`_names_unknown`, ADR-0108).

## Reproduction / Evidence

Reproduced for real on 2026-10-18 at `d08c67d`, in a detached scratch
worktree under the session scratchpad (removed afterwards). The working
tree's `gates.py` was never edited. Baseline on the unedited copy:
`selftest: ok`, and `python3 -m unittest tests.test_gates` ran 290 tests,
`OK`. Each reversion below was applied alone, run, then reset with
`git checkout -- gates.py`. The unit-test output is filtered with
`grep -E "^(FAIL|ERROR):|^Ran|^OK|^FAILED"`; the lines are verbatim.

**1. O's date check**, a raw compare at its call in `check_prd_coverage`:

```
-        if _grandfathered(entry["prd_date"], COVERAGE_ADOPTED):
+        if isinstance(entry["prd_date"], str) and entry["prd_date"] < COVERAGE_ADOPTED:
--- selftest
selftest: ok
exit=0
--- unittest tests.test_gates
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestPrdCoverage.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='"2026-10-20"')
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestPrdCoverage.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date="'2026-10-20'")
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestPrdCoverage.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='')
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestPrdCoverage.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='20/10/2026')
Ran 290 tests in 4.209s
FAILED (failures=4)
```

Each failure reads `AssertionError: Lists differ: [] != ['O:
docs/features/demo/prd.md:17 PRD-0001 §Out of scope is cited by no
breakdown row and carries no coverage waiver']` (from the unfiltered
`tests.test_gates.TestPrdCoverage` run: `Ran 15 tests`, `FAILED
(failures=4)`).

**2. M's date check**, a raw compare at its call in
`check_capture_completeness`:

```
-        if _grandfathered(frontmatter.get("date"), CAPTURE_ADOPTED):
+        if isinstance(frontmatter.get("date"), str) and frontmatter.get("date") < CAPTURE_ADOPTED:
--- selftest
selftest: ok
exit=0
--- unittest TestCaptureCompleteness
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestCaptureCompleteness.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='"2026-10-20"')
AssertionError: Lists differ: [] != ["M: docs/fixes/demo/defect.md missing req[258 chars]ut'"]
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestCaptureCompleteness.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date="'2026-10-20'")
AssertionError: Lists differ: [] != ["M: docs/fixes/demo/defect.md missing req[258 chars]ut'"]
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestCaptureCompleteness.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='')
AssertionError: Lists differ: [] != ["M: docs/fixes/demo/defect.md missing req[258 chars]ut'"]
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestCaptureCompleteness.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='20/10/2026')
AssertionError: Lists differ: [] != ["M: docs/fixes/demo/defect.md missing req[258 chars]ut'"]
Ran 12 tests in 0.016s
FAILED (failures=4)
--- unittest tests.test_gates
(the same four FAIL lines)
Ran 290 tests in 4.182s
FAILED (failures=4)
```

**3. H's date check**, a raw compare in `_rollup_applies`:

```
-    return not _grandfathered(date, ROLLUP_ADOPTED)
+    return not (isinstance(date, str) and date < ROLLUP_ADOPTED)
--- selftest
selftest: ok
exit=0
--- unittest TestEvidenceRollUp
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestEvidenceRollUp.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='"2026-10-20"')
AssertionError: Lists differ: [] != [(8, 'summary "Summary" neither counts nor[118 chars]ss')]
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestEvidenceRollUp.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date="'2026-10-20'")
AssertionError: Lists differ: [] != [(8, 'summary "Summary" neither counts nor[118 chars]ss')]
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestEvidenceRollUp.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='')
AssertionError: Lists differ: [] != [(8, 'summary "Summary" neither counts nor[118 chars]ss')]
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestEvidenceRollUp.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='20/10/2026')
AssertionError: Lists differ: [] != [(8, 'summary "Summary" neither counts nor[118 chars]ss')]
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestEvidenceRollUp.test_non_iso_or_quoted_post_cutoff_date_is_judged) (date='16 Oct 2026')
AssertionError: Lists differ: [] != [(8, 'summary "Summary" neither counts nor[118 chars]ss')]
Ran 28 tests in 0.005s
FAILED (failures=5)
--- unittest tests.test_gates
(the same five FAIL lines)
Ran 290 tests in 4.236s
FAILED (failures=5)
```

**4. H's zero count**, `_names_unknown` ignoring `SUMMARY_ZERO_COUNT`:

```
-    return any(not SUMMARY_ZERO_COUNT.search(line, 0, match.start())
-               for match in SUMMARY_UNKNOWN_TERM.finditer(line))
+    return bool(SUMMARY_UNKNOWN_TERM.search(line))
--- selftest
selftest: ok
exit=0
--- unittest TestEvidenceRollUp
FAIL: test_sections_do_not_record_a_zero_count_as_naming (tests.test_gates.TestEvidenceRollUp.test_sections_do_not_record_a_zero_count_as_naming)
FAIL: test_wrapper_refuses_the_retro_probe (tests.test_gates.TestEvidenceRollUp.test_wrapper_refuses_the_retro_probe)
FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, 0 FAIL, 0 NOT RUN.')
FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, 0 not run.')
FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, zero skipped.')
FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, 0 N/A.')
FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, ZERO deferred.')
FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, **0** NOT RUN.')
FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS, 0 criteria skipped.')
FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS; no criteria were skipped.')
FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS; none skipped.')
FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (tests.test_gates.TestEvidenceRollUp.test_zero_count_summary_over_a_disclosed_criterion_fails) (summary='1 PASS; nothing was skipped.')
Ran 28 tests in 0.007s
FAILED (failures=12)
--- unittest tests.test_gates
Ran 290 tests in 4.717s
FAILED (failures=12)
```

**Also run: the seed's exact shape**, a raw compare inside
`_grandfathered` (blinds O, M and H's date checks at once):

```
-    if not isinstance(date, str):
-        return False
+    return isinstance(date, str) and date < cutoff
--- selftest
selftest: ok
exit=0
--- unittest tests.test_gates
Ran 290 tests in 4.943s
FAILED (failures=13)
```

The 13 are the four O, four M and five H date subtests above.

So all four reversions, and the seed's combined one, are caught by the
repo's unit tests and missed by the shipped selftest. No reversion
escaped the unit tests. **Evidence it bites today: none.** No stamped
repo is known to have regressed. This is prevention: stamped repos took
these fixes in 0.21.0 (#1026), and from then on only the selftest guards
them there.

## Root-cause hypothesis

Hypothesis: #1002 and #1018 each added their dodge tests to
`tests/test_gates.py` and no row to `gates_selftest.py`. Nothing asks a
gate fix for a selftest twin. The review that found the gap deferred it
as a minor (the seed's origin), so it never reached a work item.

## Blast radius

- **Code.** `gates_selftest.py` and its payload copy
  `factory/templates/tools/factory/gates_selftest.py`. Today they are
  byte-identical (`cmp`), and the copy is manifest-pinned.
- **Behaviour.** No gate changes. The selftest gains rows that pass on
  today's code. It goes red only on a regression of one of the four
  fixes.
- **Callers to keep working.** The fixture builders are shared:
  `tests/test_gates.py` `TestRoster.defects()` (line 1703) plants H, M
  and O through `evidence_honesty_defect_fixture`,
  `capture_completeness_defect_fixture` and `prd_coverage_fixture`.
  `tests/test_knowledge_plane.py` line 243 reads
  `evidence_honesty_defect_fixture`'s `demo` and `gamed` artifacts. A
  changed builder signature or a new artifact in a shared fixture must
  leave those passing.
- **Who.** Every stamped repo, once it updates the payload. Severity:
  low. It is a missing guard, and nothing has regressed.
- **Since.** #1002 and #1018, 2026-10-17 and 2026-10-18.

## Ruled out

- **A gap in the unit tests too.** All four reversions fail
  `tests.test_gates` (above). Only the selftest is blind.
- **Changing `gates.py`.** Today's code is correct. Out of scope.
- **A design question for Architect.** The rows follow the existing
  `expect`/`expect_clean` pattern, one isolated tree per scenario. The
  mutation proof is a scratchpad step this run does once. It is not a
  selftest that mutates itself.
- **In flight.** The check ran on 2026-10-18 and nothing matches.
  `gh pr list --state open` returned `[]`. `gh issue list --state open
  --search` for "selftest" returned only journals (#925, #586, #181).
  "dodge", "gates_selftest" and "_grandfathered" returned nothing.
  `git log --all --not HEAD` over `gates_selftest.py` and its payload
  copy finds only merges and the fail-closed-roll-up commits. None adds
  a post-cutoff date or zero-count row. No branch named for this work
  exists apart from this run's own branch.

## Work items

Re-entry is Implement, so these checkboxes are the run's breakdown.

- [ ] **O dodge row**: a selftest scenario with a PRD dated quoted and
  after `COVERAGE_ADOPTED` (for example `date: "2026-10-20"`), in its
  own tree, beside an uncited, unwaived section. Assert O's coverage
  string under its own label (for example `"O quoted date"`).
  - Accept: passes on today's code, and the expected string names the
    fixture's `prd.md` path.
- [ ] **M dodge row**: a selftest scenario with a defect.md dated quoted
  and after `CAPTURE_ADOPTED`, missing a required section, in its own
  tree. Assert M's string under its own label.
  - Accept: passes on today's code, and the expected string names the
    fixture's `defect.md` path.
- [ ] **H date dodge row**: a verification.md dated quoted and after
  `ROLLUP_ADOPTED`, its Summary reading as a full pass over a criterion
  disclosed NOT RUN. Assert H's roll-up string on that artifact's own
  path, under its own label.
  - Accept: passes on today's code. The assert is path-specific, so the
    existing `rolledup` row's "neither counts nor names" cannot satisfy
    it.
- [ ] **H zero-count row**: a verification.md dated on or after
  `ROLLUP_ADOPTED` (unquoted), its Summary reading "N PASS, 0 FAIL, 0
  NOT RUN" over a criterion disclosed NOT RUN. Assert the roll-up string
  on that artifact's own path, under its own label.
  - Accept: passes on today's code, and is path-specific as above.
- [ ] **Shared builders stay green**: whether a new row gets its own
  builder or a parameter on an existing one, the `TestRoster.defects()`
  and `tests/test_knowledge_plane.py` callers keep passing unedited, or
  are edited only to follow a changed signature.
  - Accept: `python3 -m unittest tests.test_gates
    tests.test_knowledge_plane` passes.
- [ ] **Mutation proof (scratchpad only)**: in a scratch worktree or
  copy, never the working tree, apply each reversion from Reproduction
  in turn (O's call, M's call, `_rollup_applies`, `_names_unknown`), and
  run `python3 gates.py --selftest` against the new rows.
  - Accept: each of the four runs prints `selftest: FAIL` with a failure
    line naming that reversion's row, and the expected output is quoted
    in Notes from a real run. The scratch copy is removed afterwards.
- [ ] **Payload mirror and manifest**: copy `gates_selftest.py` to
  `factory/templates/tools/factory/gates_selftest.py`. Delete any stray
  `.orig`/`.rej` files first, then run `python3 factory_init.py
  update-manifest` and commit the manifest.
  - Accept: `cmp` shows the two files are identical, and detector E is
    clean.
- [ ] **Backlog claim**: the claim on `docs/backlog.md` line 124 landed
  with this capture commit. Confirm it is still there and well-formed,
  then check this box.
  - Accept: the seed line ends in
    `(claimed: maintenance:the-selftest-cannot-see-a-dodge)`.
- [ ] **Whole-repo checks**: `python3 run_tests.py`, `python3 lint.py`,
  `python3 kb.py drift`, and `python3 gates.py && python3 gates.py
  --selftest`.
  - Accept: all pass. `gates.py --selftest` prints `selftest: ok` on the
    fixed tree, and `gates.py` reports `gates: 0 problem(s)`.

## Notes

- 2026-10-18 (Capture): H's existing `expect("H", ...)` matches
  "neither counts nor names" in any H problem. A new artifact dropped
  into the shared `rolledup` fixture with only that substring would be
  masked by the existing `rolledup` row, so the rows above assert on
  their own paths and labels.
- 2026-10-18 (Capture): `TestSelftest` already holds the pattern for a
  durable in-repo mutation pin
  (`test_selftest_fails_when_f_misses_the_planted_effort` patches a
  detector with `mock.patch.object` and asserts `selftest() == 1`).
  Patching `gates._grandfathered` or `gates._names_unknown` the same way
  would keep the mutation proof running after this run. It is not in
  the brief's scope. Implement may add it if it is cheap, and should log
  that choice here.
- 2026-10-18 (Capture): out of scope, per the brief: any `gates.py`
  change, the other open H seeds (backlog lines 126 to 132), and
  `.claude-plugin/plugin.json` (ADR-0095). The payload changes, so a
  later `chore(release)` PR is owed.
- Next stage: Implement.
