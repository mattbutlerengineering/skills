---
stage: review
run: maintenance:a-quoted-date-dodges-the-cutoff
date: 2026-10-17
assumptions:
  - "Both minors are deferred under the skill's default: minors may be deferred freely. Neither changes what a gate decides, and fixing the docstring line would mean regenerating the manifest for a cosmetic edit."
  - "Mutation (c), where O calls the helper with CAPTURE_ADOPTED, is an equivalent mutant: both constants are \"2026-09-21\". It is recorded as equivalent, not as a test gap. O's boundary is still pinned by the literal 2026-09-20/2026-09-21 fixtures, so a cutoff swap to a different value would be caught."
  - "The remaining-cleanup seed (dodge-shape selftest fixtures) is recorded here and left to Ship or the Owner to file in docs/backlog.md. The brief puts the selftest out of scope, and Review does not widen a run's scope."
---

# Review: a quoted date dodges the cutoff

## Scope

`git diff origin/main...HEAD` (origin/main `461803a`, HEAD `7e4a19a`),
five commits from `0a1cbb3` (RED tests) to `7e4a19a` (verify). Ten files
changed. The code is `gates.py` and its byte-identical payload copy
`factory/templates/tools/factory/gates.py`: the new `_grandfathered(date,
cutoff)`, the rename `ROLLUP_ISO_DATE` to `FRONTMATTER_ISO_DATE`, and
H's, O's and M's call sites. The rest of the diff is
`tests/test_gates.py` (55 added lines, 0 deleted), the
`factory/manifest.json` pin, the dated amendments to ADR-0073 and
ADR-0107, the `docs/backlog.md` claim, and this run's artifacts.
`.claude-plugin/plugin.json` is not in the diff (ADR-0095).

Predecessor `verification.md` exists: 11 of 11 PASS.

## Maintenance-run checks

- **The regression test proves the reproduction is gone.** Capture's
  reproduction was four dodge shapes per detector, each silent `[]` at
  `e1dbb9e`. The new `test_non_iso_or_quoted_post_cutoff_date_is_judged`
  in `TestPrdCoverage` and `TestCaptureCompleteness` asserts the exact
  existing problem strings for the same four shapes. Verify's
  raw-compare mutation fails all 8 O and M subtests, plus H's 5. My
  mutation (a) below fails the quoted shapes again. The test pins the
  reproduction, not just a green run.
- **The producing boundary has one owner.** It does. The defect was one
  fact with three owners (H fixed in #998, O and M not). There is now one
  normalizer, and all three detectors go through it.
  ```
  $ grep -n "_grandfathered(\|FRONTMATTER_ISO_DATE\|date < " gates.py
  262 (pattern), 1213 def, 1224 .match, 1233 H, 1445 O, 1717 M
  ```
  None of the three callers pre-processes the value first, because they
  all read it through `protocol.parse_frontmatter`:
  - H: `parse_frontmatter(text)`.
  - O: `knowledge_plane.parse_run` sets `"prd_date":
    prd_fields.get("date")` from `parse_frontmatter(prd_text) or {}`
    (`knowledge_plane.py:757-764`).
  - M: `read_frontmatter`, which calls the same parser.

  So the helper gets the same value shape from each: a `str` with any
  quotes kept, `""` for an empty `date:`, or `None` when the key is
  absent.
- **Related cleanup that remains.**
  - `gates_selftest.py` has no dodge-shape fixture for H, O or M. Its O
    and M fixtures date themselves `{gates.COVERAGE_ADOPTED}` /
    `{gates.CAPTURE_ADOPTED}` (lines 153, 373) or `2026-01-01`
    (line 171). A stamped repo runs only the selftest, so it would not
    catch a regression of this fix. Capture and Verify both flagged
    this. See Minor 2.
  - `ROLLUP_ISO_DATE` still appears in `docs/backlog.md:123`,
    `docs/features/fail-closed-roll-up/review.md:330` and this run's own
    artifacts. All of these are history and stay as written.
    ADR-0107:127 records the rename. Nothing live (no `.py`, no test, no
    payload file, no `one_owner.py` marker) names it:
    ```
    $ git grep -n "ROLLUP_ISO_DATE" -- '*.py'
    $ (no output)
    ```

## Mutations (whole suite, each landed, each restored)

The scratch script is
`/private/tmp/claude-501/-Users-mbutler-github-skills/61791cec-ce5d-4fbf-a8e5-60dc748e0ec7/scratchpad/mutate_review.py`.
It mutates the root `gates.py` only, asserts that the old text occurs
exactly once, and probes the reloaded helper. It then runs
`python3 run_tests.py` and restores the bytes in a `finally` block.
Because only the root copy is mutated, the root-to-payload parity
failure (`test_every_mirrored_root_file_matches_its_payload_copy`) is
expected noise in every row. A first pass that mutated both copies added
manifest-mismatch noise (stamp acceptance and summary-line tests) to all
three rows alike, so the root-only pass below is the one cited. The
baseline before the mutations was `tests: 3312 tests across 106 modules
in 13.8s on 8 workers, 0 problem(s)`.

| Mutant | Probe | Result |
|---|---|---|
| (a) ignore the cutoff: `return bool(iso)` | `"2026-10-20"` vs 2026-09-21 -> True | **caught**: the quoted dodge subtests in O, M and H, plus O's and M's ordinary flagged-fixture tests, TestRoster O/M, and the selftest |
| (b) drop the quote-strip | `'"2026-01-01"'` -> False | **caught**: the 4 quoted pre-cutoff guard subtests (O and M); the dodge tests still pass, which is correct, since an unstripped quote fails the regex and is judged |
| (c) O calls with `CAPTURE_ADOPTED` | n/a | **survived; equivalent mutant**: both constants are `"2026-09-21"`, so behaviour is identical |

```
== a_ignore_cutoff (root only)
landed: True
probe quoted pre-cutoff '"2026-01-01"' -> True | ISO post '2026-10-20' -> True
suite rc: 1
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestCaptureCompleteness...) (date='"2026-10-20"')
FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged (tests.test_gates.TestPrdCoverage...) (date="'2026-10-20'")
FAIL: test_uncovered_unwaived_section_is_flagged (tests.test_gates.TestPrdCoverage...)
FAIL: test_each_row_reports_its_planted_defect_under_its_own_letter (tests.test_gates.TestRoster...) (letter='O')
FAIL: test_selftest_passes (tests.test_gates.TestSelftest.test_selftest_passes)
  ... (21 gates failures in all, plus the parity noise)
tests: 3312 tests across 106 modules in 13.9s on 8 workers, 2 problem(s)
restored: True
== b_no_quote_strip (root only)
landed: True
probe quoted pre-cutoff '"2026-01-01"' -> False | ISO post '2026-10-20' -> False
suite rc: 1
FAIL: test_quoted_or_datetime_pre_cutoff_date_is_grandfathered (tests.test_gates.TestCaptureCompleteness...) (date='"2026-01-01"')
FAIL: test_quoted_or_datetime_pre_cutoff_date_is_grandfathered (tests.test_gates.TestCaptureCompleteness...) (date="'2026-01-01'")
FAIL: test_quoted_or_datetime_pre_cutoff_date_is_grandfathered (tests.test_gates.TestPrdCoverage...) (date='"2026-09-20"')
FAIL: test_quoted_or_datetime_pre_cutoff_date_is_grandfathered (tests.test_gates.TestPrdCoverage...) (date="'2026-09-20'")
FAIL: test_every_mirrored_root_file_matches_its_payload_copy (...) (mirror='gates.py')
tests: 3312 tests across 106 modules in 13.8s on 8 workers, 2 problem(s)
restored: True
== c_O_uses_capture (root only)
landed: True
suite rc: 1
FAIL: test_every_mirrored_root_file_matches_its_payload_copy (...) (mirror='gates.py')
tests: 3312 tests across 106 modules in 13.8s on 8 workers, 1 problem(s)
restored: True
```

Mutant (b) answers Verify's open point. The pre-cutoff guard tests
cannot catch a raw-compare regression, but they are what catches the
over-correction regression. H's quoted-pre-cutoff subtests fail under
(b) as well (`TestEvidenceRollUp`, the `"2026-10-16"` and
`'2026-10-16'` rows). The dual-copy pass printed them. My root-only
printout filtered most `TestEvidenceRollUp` lines for length, so they
are not in the excerpt above.

## Findings

No critical and no major findings.

### Minor: `check_capture_completeness` docstring line not reflowed (105 chars)

- Scenario: this is a decayed contract, not a behaviour change. At
  `gates.py:1706` (and the payload copy), the edit joined the new
  sentence onto the next one without rewrapping, giving
  `unparseable date is NOT grandfathered, fail closed. Bare `root`, no
  `parsed`: defect.md is not one of`. The diff takes the file from 12
  lines over 79 characters to 13. No lint rule enforces the width, so
  CI is unaffected.
- Standard: none
- Decision: deferred. It is cosmetic, and fixing it means a manifest
  regen for a docstring. Any later edit to `gates.py` should reflow it.

### Minor: no dodge-shape fixture in `gates.py --selftest` (stamped repos cannot see a regression)

- Scenario: a later change puts back a raw compare in `_grandfathered`
  in the payload. A stamped repo runs only `gates.py --selftest`,
  which has no quoted, empty or non-ISO `date:` row for H, O or M. It
  stays `selftest: ok` while the dodge returns. This repo's own
  `tests/test_gates.py` would catch it (mutant (a) above), so main
  is protected. Stamped repos are not.
- Standard: none
- Decision: deferred. The brief puts it out of scope, and Capture's
  Notes and Verify's Not verified section both record it. It is a
  follow-up seed for `docs/backlog.md`: one selftest row per detector
  with a quoted post-cutoff date. File it at Ship or after.

## Passes with no findings

- **Correctness: clean.** `None`, which is what a missing `date:` key
  gives, still returns False from `_grandfathered`. So O and M still
  judge it, as before
  (`test_a_missing_date_is_not_grandfathered` passes in both classes).
  O's input path matches M's: both go through
  `protocol.parse_frontmatter` with no extra pre-processing, as shown
  above. Some shapes were grandfathered before and are now judged.
  - A pre-cutoff ISO date with trailing text (`date: 2026-01-01 # x`),
    or a non-ISO pre-cutoff spelling. Neither exists on the real tree:
    `python3 gates.py` -> `gates: 0 problem(s)`, and Capture counted 0
    such shapes over all 106 tracked `prd.md`/`defect.md` files. H
    already treated them this way.
  - A `date: |` block scalar. `parse_frontmatter` gives a multi-line
    string, which is now judged; it sorted before the cutoff before.
    No artifact uses this shape.

  An ISO-shaped but impossible date (`1999-99-99`) is still
  grandfathered. That is not a new hole: a false ISO date dodges any
  cutoff, by design.
- **Design: clean.** The helper stays private inside `gates.py`, with no
  new module, matching the CLAUDE.md seam rule. No cutoff value
  changed. `_rollup_applies` stays as H's one-line adapter.
  `python3 one_owner.py` on HEAD differs from `origin/main` only by a
  line-number shift (`gates.py:305` -> `:306`, `ARCH_PLAIN_PATH`), so
  the fix adds no finding.
- **Security: clean.** It is a pure function over a frontmatter string,
  with no I/O, and the regex is anchored and linear.
- **Complexity: clean.** The diff adds one 12-line helper and removes
  two copies of the compare. Nothing on the cut-list applies, and the
  diff adds no `lean:` marker.
- **ADR compliance: clean.** `adr_status.py` lists ADR-0073 and
  ADR-0107 as live. Both got dated amendment paragraphs appended at the
  end, and neither Decision section was rewritten. Each amendment
  matches the code:
  - ADR-0073: M now goes through `gates._grandfathered`, and only a
    `YYYY-MM-DD` value, quoted or as a datetime, is exempt.
  - ADR-0107: the O/M seed is done, and the rename is recorded.

  ADR-0072 says nothing about how O compares the date, so it needed no
  change. ADR-0095: `plugin.json` is untouched. Stdlib only, and the
  problem-string contract is kept (standards slug `stdlib-only` is met).
  The tests assert exact strings through the public `check_prd_coverage`
  and `check_capture_completeness`. The O test injects `parsed`, which
  is that function's public signature, and the on-disk `parse_run` path
  is covered by Capture's and Verify's `repro_om.py` runs.
- **Payload and manifest: coherent.** `cmp` shows the two copies are
  identical. Both sha256 values equal the manifest pin
  `b5d8e11b…bf1f62`. Detector E is clean (Verify criterion 8; the gates
  run below repeats it).
- **Domain passes: none selected.** No changed path matches payments,
  migrations or dependencies. `factory/manifest.json` is a checksum pin,
  not a package manifest.

Process note: a stray `git checkout origin/main --` during this review
briefly detached HEAD. I switched back to
`fix/a-quoted-date-dodges-the-cutoff` at `7e4a19a`, with a clean
`git status`, before running any check quoted here. Nothing was
written in the detached state.

## Final checks (HEAD `7e4a19a` plus this review.md, uncommitted)

```
$ python3 run_tests.py
tests: 3312 tests across 106 modules in 14.5s on 8 workers, 0 problem(s)
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

Ready for Ship. There is no critical or major finding, and the fix loop
was not entered. Two minors are deferred with reasons: the docstring
wrap, and the selftest dodge fixtures as a follow-up seed.
