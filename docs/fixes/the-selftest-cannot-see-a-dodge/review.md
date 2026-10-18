---
stage: review
run: maintenance:the-selftest-cannot-see-a-dodge
date: 2026-10-18
assumptions:
  - "All three findings are minors, and each is deferred under the skill's default (minors may be deferred freely). None opens a bypass that origin/main lacked: every regression shape below also leaves origin/main's selftest ok, and this repo's unit tests catch each one. Whether to fix any before Ship is the Owner's call; the Verdict says which are cheap."
  - "Severity of Minors 1 and 2 is judged against the brief's scope, which asked for one quoted post-cutoff row per detector and one '0 NOT RUN' row. The run delivered exactly that, so a further dodge shape is a widening, not a miss."
  - "Minor 3 cites a provisional ADR (ADR-0108). It is a stale statement of fact in Consequences, not a violation of its Decision, so the one-severity-lower rule for provisional ADRs has nothing to lower."
  - "The review's probe scripts live in the session scratchpad, not the repo: review_dodge_builders.py and review_dodge_mutate.py under /private/tmp/claude-501/-Users-mbutler-github-skills/61791cec-ce5d-4fbf-a8e5-60dc748e0ec7/scratchpad/. They ran in detached scratch worktrees of HEAD 0cbbdf9 and origin/main f8c16d9, and a stamped temp repo, all removed afterwards. The working tree was never edited by a probe."
---

# Review: the selftest cannot see a dodge

## Scope

`git diff origin/main...HEAD`. origin/main is `f8c16d9` (fetched, an
ancestor of HEAD), and HEAD is `0cbbdf9`. The diff is five commits, from
`d08c67d` (brief) to `0cbbdf9` (verify), and eight files. The code is
`gates_selftest.py` and its byte-identical payload copy
`factory/templates/tools/factory/gates_selftest.py`: the new optional
`date` on `prd_coverage_fixture` and `capture_completeness_defect_fixture`,
the new `evidence_rollup_defect_fixture`, the `QUOTED_POST_CUTOFF`
constant, and four new rows in `selftest()`. The rest is the
`factory/manifest.json` pin, two new `TestSelftest` tests in
`tests/test_gates.py` (32 lines added, 0 deleted), the `docs/backlog.md`
claim, and this run's artifacts. `gates.py` and
`.claude-plugin/plugin.json` are not in the diff (ADR-0095).

Predecessor `verification.md` exists: 8 of 8 PASS.

## Maintenance-run checks

- **The rows pin the reproduction.** Verify's criterion 2 replays the
  four reversions from defect.md and each fails only its own row; the
  control on origin/main's selftest stays `ok` for all four. Not
  re-run here (the protocol's floor).
- **The fixture builders' output is unchanged.** Every file the shared
  builders write, hashed, from origin/main's `gates_selftest.py` and
  from HEAD's, with the call shapes the selftest and `TestRoster` use:
  ```
  $ cmp builders_main.json builders_head.json && echo "builders: byte-identical"
  builders: byte-identical
  {'capture': (1, 'None'), 'evidence': (5, 'None'), 'prd_waive_false': (2, 'None'), 'prd_waive_kw_roster': (2, 'None'), 'prd_waive_true': (2, 'None')}
  ```
  (file count and return value per call). So the `rolledup` text is
  byte-identical, and `evidence_honesty_defect_fixture` still returns
  `None`, as `tests/test_knowledge_plane.py` line 243 expects.
- **Nothing in the payload imports a changed name.** `git grep` over
  every tracked `.py` for the three builders, the new builder,
  `QUOTED_POST_CUTOFF` and `gates_selftest`: the payload's only importer
  is `gates.py` lines 1872 to 1873 (`import gates_selftest`, then
  `selftest()`). The builders' other callers are root-only tests
  (`tests/test_gates.py` lines 22 and 1714 to 1720,
  `tests/test_knowledge_plane.py` lines 10 to 11 and 243).

## Probes

### Regression shapes the new rows do and do not see

`review_dodge_mutate.py` applies each shape alone to a scratch copy of
HEAD's `gates.py`, asserts the old text occurs once and the edit
landed, runs the selftest and `tests.test_gates`, and restores the
bytes:

- R1 strips only double quotes in `_grandfathered`.
- R2 strips quotes but drops the ISO match (`return value < cutoff`).
- R3 narrows `SUMMARY_ZERO_COUNT` to the digit (`(?:0)`).
- R4 keeps `0|zero` and drops the negation words.

```
baseline selftest: selftest: ok exit 0
=== R1_double_quotes_only (landed: True)
  selftest: selftest: ok exit 0
  unittest: ['Ran 292 tests in 5.280s', 'FAILED (failures=3)']
    FAIL: test_quoted_or_datetime_pre_cutoff_date_is_grandfathered (date="'2026-01-01'")
    FAIL: test_quoted_or_datetime_pre_cutoff_date_is_grandfathered (date="'2026-10-16'")
    FAIL: test_quoted_or_datetime_pre_cutoff_date_is_grandfathered (date="'2026-09-20'")
=== R2_strip_quotes_no_iso (landed: True)
  selftest: selftest: ok exit 0
  unittest: ['Ran 292 tests in 5.169s', 'FAILED (failures=7)']
    FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (date='')
    FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (date='20/10/2026')
    FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (date='')
    FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (date='16 Oct 2026')
    FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (date='20/10/2026')
    FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (date='')
    FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (date='20/10/2026')
=== R3_zero_digit_only (landed: True)
  selftest: selftest: ok exit 0
  unittest: ['Ran 292 tests in 5.204s', 'FAILED (failures=5)']
    FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (summary='1 PASS, ZERO deferred.')
    FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (summary='1 PASS, zero skipped.')
    FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (summary='1 PASS; no criteria were skipped.')
    FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (summary='1 PASS; none skipped.')
    FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (summary='1 PASS; nothing was skipped.')
=== R4_no_negation_words (landed: True)
  selftest: selftest: ok exit 0
  unittest: ['Ran 292 tests in 5.077s', 'FAILED (failures=3)']
    FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (summary='1 PASS; no criteria were skipped.')
    FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (summary='1 PASS; none skipped.')
    FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (summary='1 PASS; nothing was skipped.')
restored: True
```

R1 is not a dodge. A single-quoted post-cutoff date stays unstripped,
fails the ISO match and is judged, so R1 only over-refuses a
single-quoted pre-cutoff date. That is not the selftest's concern.
R2, R3 and R4 each partly undo a fix this run exists to guard (#1018
fixed the quoted, empty and non-ISO dates together; ADR-0108 names
`0`, `zero`, `no`, `none` and `nothing`), and each leaves the selftest
`ok` (Minors 1 and 2).

A candidate costing two tuple lines in the H loop, tried in the scratch
copy only and then reset: `("H empty date", "", "All criteria pass.")`
and `("H none skipped", gates.ROLLUP_ADOPTED, "1 PASS; none skipped.")`.
The selftest prints `selftest: ok` on HEAD's `gates.py` with them, and
the same four shapes replayed give:

```
=== R1_double_quotes_only (landed: True)
  selftest: selftest: ok exit 0
=== R2_strip_quotes_no_iso (landed: True)
  selftest: H empty date: expected a problem containing 'docs/features/rollup/verification.md:7 summary "Summary" neither counts nor names', got [] | selftest: FAIL exit 1
=== R3_zero_digit_only (landed: True)
  selftest: H none skipped: expected a problem containing 'docs/features/rollup/verification.md:7 summary "Summary" neither counts nor names', got [] | selftest: FAIL exit 1
=== R4_no_negation_words (landed: True)
  selftest: H none skipped: expected a problem containing 'docs/features/rollup/verification.md:7 summary "Summary" neither counts nor names', got [] | selftest: FAIL exit 1
restored: True
```

`_grandfathered` is the one owner of the date reading for H, O and M,
so one empty-date row covers R2 for all three, as the existing H row
covers the seed's combined reversion.

### Brittleness of the pinned fragments

The new rows assert `<path>:7 summary "Summary" neither counts nor
names` (H) and `docs/features/demo/prd.md:12 ... §Actors is cited by no
breakdown row` (O). Pinning a line is the existing precedent (`J`
asserts `Makefile:2`, `N` asserts `demo/prd.md:4`). The line is fixed
by the fixture text in the same file, not by `gates.py`. The `H:
{rel}:{lineno} {suffix}` format comes from `gates.py`, and the unit
tests already pin it. Probe: in this repo's scratch copy, change that
format to `H: {rel} line {lineno}: {suffix}` and run
`tests.test_gates`:

```
   1 FAIL: test_asserted_but_unevidenced_criterion_is_flagged
   1 FAIL: test_selftest_fails_when_a_zero_count_names_the_unknown
   1 FAIL: test_selftest_fails_when_the_date_checks_compare_the_raw_string
   1 FAIL: test_selftest_passes
   1 FAIL: test_the_selftest_flag_still_runs_through_gates_py
   1 FAIL: test_wrapper_prefixes_the_rollup_problem
   1 FAIL: test_wrapper_refuses_the_retro_probe
   1 FAILED (failures=7)
   1 Ran 292 tests in 4.918s
```

So such an edit goes red here before it ships. The selftest
rows add no new coupling. In a freshly stamped temp repo, the same edit
to `tools/factory/gates.py` turns both H rows red. But detector E reports
the hand edit in the same run, so the red is not false:

```
H quoted date: expected a problem containing 'docs/features/rollup/verification.md:7 summary "Summary" neither counts nor names', got ['H: docs/features/rollup/verification.md line 7: summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Live dispatch", line 21); unknown never rolls up to pass']
H zero count: expected a problem containing 'docs/features/rollup/verification.md:7 summary "Summary" neither counts nor names', got [the same one-item list as above; elided here]
selftest: FAIL
E: tools/factory/gates.py does not match factory/templates/tools/factory/gates.py (hand-edited stamped file — restore it from the mirror or re-stamp, never keep the edit)
gates: 1 problem(s)
```

`gates.py` and `gates_selftest.py` are both identity `MIRRORS` entries
under `tools/factory/` (`factory_init.py` lines 251 to 252, inside
`FACTORY_OWNED`), so an update ships them together.

### The two `TestSelftest` pins

Run in one process with `test_selftest_passes` on HEAD (whose
run prints the `selftest: ok` line), then against
origin/main's `gates_selftest.py` (rows absent):

```
--- HEAD selftest, plus leak check
selftest: ok
ran 3 failures 0 errors 0
same gates module as tests: True and as fixtures: True
restored after run: True True
--- origin/main selftest (rows absent)
FAIL: test_selftest_fails_when_the_date_checks_compare_the_raw_string
AssertionError: 0 != 1
FAIL: test_selftest_fails_when_a_zero_count_names_the_unknown
AssertionError: 0 != 1
Ran 2 tests in 0.834s
FAILED (failures=2)
```

They are not vacuous: the patch alone does not turn the selftest red,
the rows do. The patch reaches the detectors, because `tests.test_gates`,
`gates_selftest` and the patched module are one `gates` object. Both
`_grandfathered` and `_names_unknown` are the originals after the run,
so no patch state leaks. The exact-set label assert also fails if a
reversion knocks over a row it should not.

## Findings

No critical and no major findings.

### Minor: the date rows see only the quoted shape; dropping the ISO match reopens the empty and non-ISO dodges with the selftest ok

- Scenario: a later payload edit "simplifies" `gates._grandfathered`
  to strip quotes and compare the raw string (R2 above). A
  verification.md, PRD or defect.md dated `date:` (empty) or
  `date: 20/10/2026` after the cutoff is then grandfathered again: `''`
  and `'20/…'` both sort below `'2026-…'`. That is two of the three
  dodges #1018 closed. Every stamped repo's `gates.py --selftest`
  prints `selftest: ok` (probe above). This repo's unit tests catch it
  (7 failures), so the gap is only in a stamped repo, which is the gap
  this run exists for. One extra tuple, `("H empty date", "", "All
  criteria pass.")`, turns R2 red (probe above).
- Standard: none
- Decision: deferred (skill default for minors). The brief scoped one
  quoted row per detector, and that is delivered. It is cheap to take
  before Ship; see the Verdict.

### Minor: the zero-count row sees only the digit; narrowing the zero vocabulary leaves the selftest ok

- Scenario: a later payload edit to `SUMMARY_ZERO_COUNT` drops `zero`,
  `no`, `none` and `nothing` (R3), or just the negation words (R4).
  The regex was retuned once already, in a-zero-count-names-nothing's
  fix loop. A Summary reading "1 PASS; none skipped." over a criterion
  disclosed NOT RUN then names the unknown kind again and passes H.
  The selftest prints `ok`; the unit tests catch it (5 and 3
  failures). One extra tuple, `("H none skipped", gates.ROLLUP_ADOPTED,
  "1 PASS; none skipped.")`, turns R3 and R4 red, and it also fails on
  the full zero-blind reversion, since "none" is a zero.
- Standard: none
- Decision: deferred (skill default for minors). The brief named "0
  NOT RUN" as the row, and that is delivered. It is cheap to take
  before Ship; see the Verdict.

### Minor: ADR-0108's Consequences still say the selftest has no zero-count row

- Scenario: decayed contract. `docs/adr/0108-a-zero-count-names-nothing.md`
  lines 85 to 87 read "`gates.py` ships into stamped repos, so the
  change reaches them on their next payload update. The
  `gates_selftest.py` fixture has no zero-count row." After this run
  the selftest has the `H zero count` row, so a reader of the ADR (the
  live record, unlike dated run artifacts) is told a guard is missing
  that now exists. `git grep` finds no other living document with the
  claim; the remaining hits are dated run artifacts and the claimed
  backlog line.
- Standard: none
- Decision: deferred (skill default for minors). The fix is a dated
  amendment line under that consequence, not an edit to the Decision,
  as ADR-0107 and ADR-0108 already do. It is doc-only, and Ship can
  take it.

## Passes with no findings

- **Correctness:** clean apart from Minors 1 and 2. Each new row is in
  its own temporary tree. Each asserts a fragment that carries its own
  artifact path, and passes on today's `gates.py` (`selftest: ok`
  below). The H loop's two rows write the same slug in separate trees,
  so `mkdir(parents=True)` without `exist_ok` cannot collide. The
  builder refactor is byte-identical (probe above).
- **Design:** clean apart from Minor 3. The rows follow the existing
  `expect`/`expect_clean` pattern. The two optional `date` parameters
  default to the old value, so no caller changed. The new builder has
  two callers (the `rolledup` artifact and the H loop), so the roll-up
  body has one copy. No decision here passes the ADR test.
- **Security:** clean. Fixture text written to `tempfile` directories,
  no input from outside, no I/O beyond them, stdlib only (standards slug
  `stdlib-only` met).
- **Complexity:** the cut-list finds nothing to cut. `QUOTED_POST_CUTOFF`
  has three readers, `_selftest_failures` two, and
  `evidence_rollup_defect_fixture` two. Each `date` parameter has one
  setter, and its default keeps every other caller unedited. That
  parameter is the smallest way to reuse the builder, not a speculative
  option. The diff adds no `lean:` marker.
- **ADR compliance:** clean apart from Minor 3. `adr_status.py` reports
  78 active, 19 provisional and 11 partial ADRs. Checked against the
  ones the diff reaches:
  - ADR-0050: identity mirror; `cmp` identical, and E is clean below.
  - ADR-0072 (O) and ADR-0073 (M's grandfather): the rows exercise
    each as decided.
  - ADR-0095: `plugin.json` is untouched.
  - ADR-0107 (`partial`) and ADR-0108 (`provisional`): the roll-up
    rows match the standing clauses, with a full-pass Summary refused
    over a disclosure and a zero count naming nothing.

  The rest are out of scope: no tracker, gate-label, routing, eval or
  skill-body change.
- **Tests:** the two `TestSelftest` pins are not vacuous and leak no
  patch state (probe above). They read the selftest's own failure lines
  through its public `selftest()` and stdout, as
  `test_selftest_fails_when_f_misses_the_planted_effort` does.
- **Payload and manifest:** root and payload `gates_selftest.py` both
  hash `a99ad94afaa70636…`, the manifest pins that hash, there are 0
  stray `.orig`/`.rej` files under `factory/templates/`, and
  `gates.check_scaffold_sync` returns `[]`.
- **Domain passes:** none selected. No changed path matches payments,
  migrations or dependencies; `factory/manifest.json` is a checksum pin,
  not a package manifest.

## Final checks (HEAD `0cbbdf9`, before this review.md)

```
$ python3 run_tests.py
tests: 3325 tests across 106 modules in 14.3s on 8 workers, 0 problem(s)
$ python3 lint.py
lint: 0 problem(s) across 34 skills
$ python3 kb.py drift
drift: 0 problem(s)
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

## Verdict

Ready for Ship. All five passes ran, plus the test, payload and
builder-identity checks. None was skipped or left unknown, and no domain
pass was selected. There is no critical and no major finding, and no
finding cites an `enforced` standard. Three minors are deferred under
the skill's default, each with its reason above.

Recommended before Ship, because each is cheap and inside the run's
own purpose:

- Minors 1 and 2: two tuple lines in the H loop, mirrored and
  re-manifested. The probe above shows they pass today and catch R2,
  R3 and R4.
- Minor 3: a one-line dated amendment to ADR-0108's Consequences.

Deferring all three is also sound. No shape above is a regression
against origin/main, and this repo's unit tests catch every one before
a payload ships.
