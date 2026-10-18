---
stage: review
run: maintenance:a-zero-count-names-nothing
date: 2026-10-17
assumptions:
  - "All five findings are minors and were first deferred under the skill's default (minors may be deferred freely). None of them opens a bypass that main lacked."
  - "Fix loop (2026-10-18): the Owner answered Fix now for Minors 1 and 3; both are fixed test-first in c2ef6e0. Minors 2, 4 and 5 stay deferred as backlog seeds, and Minor 2 is also an ADR-0108 Consequences line."
  - "Severity of the over-refusal (Minor 1) is judged against ADR-0108's own precedent: that ADR already accepts one honest-but-refused shape ('nothing was skipped except live dispatch') as fail-closed. The refused shapes here are rarer in this repo (6 ASCII ' - ' dash lines across all tracked verification.md files, against 828 em-dash lines), each refusal carries H's actionable string, and no tracked artifact changes outcome."
  - "ZERO_SHAPES is a literal tuple, not a derived collection, so the empty-the-collection vacuity hunt does not apply to it; the vacuity check was done by mutation instead (the Mutations table)."
  - "The review's probe scripts live in the session scratchpad, not the repo: review_zero_probe.py, review_sweep.py and mutate_review_zero.py under /private/tmp/claude-501/-Users-mbutler-github-skills/61791cec-ce5d-4fbf-a8e5-60dc748e0ec7/scratchpad/. The origin/main side ran on a detached worktree of 6a89ee3 in the same scratchpad, removed afterwards."
---

# Review: a zero count names nothing

## Scope

`git diff origin/main...HEAD` (origin/main `6a89ee3`, fetched, an
ancestor of HEAD; HEAD `7e017c6`), five commits from `9fc15c7` (RED
tests) to `7e017c6` (verify). Twelve files changed. The code is
`gates.py` and its byte-identical payload copy
`factory/templates/tools/factory/gates.py` (`cmp`: identical): the new
`SUMMARY_ZERO_COUNT`, the new `_names_unknown(line)`, the one changed
call in `verification_sections`, and the comment and docstring above
them. The rest is `tests/test_gates.py` (71 lines added, 0 deleted),
the `factory/manifest.json` pin, new ADR-0108 and its README row,
ADR-0107's status line, `skills/verify/TEMPLATE.md` line 11, the
`docs/backlog.md` claim, and this run's artifacts.
`.claude-plugin/plugin.json` is not in the diff (ADR-0095).

Predecessor `verification.md` exists: 13 of 13 PASS.

## Maintenance-run checks

- **The regression test pins the reproduction.** Capture's probe A
  (criterion 9 flipped to NOT RUN under "11 PASS, 0 FAIL, 0 NOT RUN")
  is `test_wrapper_refuses_the_retro_probe` and the first
  `ZERO_SHAPES` row, both asserting H's exact existing string. Reverting
  the call site brings back 12 failures (Verify), and each regex branch
  that carries a tested shape fails a named subtest when removed
  (Mutations below).
- **One parse, one owner.** `_names_unknown` is called inside
  `verification_sections`' existing per-line loop (`gates.py:1228`); no
  second walk of the text. The only readers of `SUMMARY_UNKNOWN_TERM`
  and `SUMMARY_ZERO_COUNT` outside tests are in `gates.py`
  (`git grep` over `*.py`, payload and tests excluded: lines 234 to
  1270 of `gates.py` only). `python3 one_owner.py` on HEAD differs from
  origin/main by a line shift only:
  ```
  < one-owner: gates.py:306 ARCH_PLAIN_PATH and md_claims.py:61 PATH_CHARS state the same value — one fact, one owner
  > one-owner: gates.py:320 ARCH_PLAIN_PATH and md_claims.py:61 PATH_CHARS state the same value — one fact, one owner
  ```
- **No tracked artifact changes outcome.** The roll-up's own pieces
  (`verification_sections` then `_rollup_problems`, grandfather
  skipped) over every tracked `verification.md`, origin/main against
  HEAD:
  ```
  summary names_unknown flips: docs/fixes/a-quoted-date-dodges-the-cutoff/verification.md 13
  files=93 refused_main=0 refused_head=0 outcome_changes=0 summary_flips=1
  ```
  The one flip is the expected one (its only hit is "0 NOT RUN", and
  it has no disclosure).
- **Related cleanup that remains.** `gates_selftest.py` has no
  zero-count row (Capture's Note, ADR-0108's last Consequence), and
  `skills/verify/SKILL.md` lines 31 to 33 (Minor 5). Both are recorded;
  neither is new scope for this review.

## Probes

One Summary line over the test fixture's two criteria (one evidenced
PASS, one `- Result: NOT RUN — needs a second account.`), through
`gates.evidence_problems`, on origin/main and on HEAD. `REFUSED` means
H's roll-up string came back. The script prints one `REFUSED|pass |
'<summary>'` line per case per tree; the excerpt below sets the two
runs' lines side by side, with the verdicts unchanged:

```
                                                               6a89ee3   7e017c6
'3 PASS, 0 FAIL NOT RUN: criterion 9.'                         pass      REFUSED
'3 PASS, no dispatch skipped (criterion 9).'                   pass      REFUSED
'3 PASS, 0 FAIL - NOT RUN: criterion 9.'                       pass      REFUSED
'3 PASS, 0 FAIL -- skipped: live dispatch.'                    pass      REFUSED
'3 PASS, 0 FAIL — NOT RUN: criterion 9.'                       pass      pass
'3 PASS, 0 FAIL; NOT RUN: criterion 9.'                        pass      pass
'3 PASS; no FAIL; 1 NOT RUN.'                                  pass      pass
'None failed, 1 skipped.'                                      pass      pass
'Nothing failed but criterion 3 was not run.'                  pass      pass
'0 regressions; NOT RUN: 1.'                                   pass      pass
'No failures. Skipped: live dispatch.'                         pass      pass
'3 PASS. No tests failed; live dispatch is NOT RUN.'           pass      pass
'3 of 4 pass, none failed. Live dispatch deferred.'            pass      pass
'there were no criteria skipped but criterion 9 was not run'   pass      pass
'1 PASS, 0 FAIL, 1/0 NOT RUN.'                                 pass      REFUSED
'0 (zero) NOT RUN'                                             pass      pass
'0x NOT RUN'                                                   pass      pass
'0 – NOT RUN'  (en dash)                                       pass      pass
'0: NOT RUN'                                                   pass      pass
'0 items: NOT RUN'                                             pass      pass
'NOT RUN: 0'                                                   pass      pass
'Not run: 0.'                                                  pass      pass
'| NOT RUN | 0 |'                                              pass      pass
'| PASS | FAIL | NOT RUN |\n|---|---|---|\n| 3 | 0 | 0 |'      pass      pass
'11 PASS, 0 FAIL, 0\nNOT RUN.'                                 pass      pass
'none NOT RUN'                                                 pass      REFUSED
'0 NOT RUN\n1'                                                 pass      REFUSED
'no live check was skipped'                                    pass      pass
```

The refused full-string for the dash shape, verbatim:

```
[(8, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Live dispatch", line 22); unknown never rolls up to pass')]
```

Reading of the brief's flagged cases and the hunted ones:

- "3 PASS, 0 FAIL NOT RUN: criterion 9" is refused because the one-word
  slot takes `FAIL` as the zero's noun. It names the criterion, so this
  is an honest Summary refused (Minor 1).
- "3 PASS, no dispatch skipped (criterion 9)" is refused. Its words say
  nothing was skipped; the parenthesis carries no unknown word. That is
  the stale Summary the rule exists for, so the refusal is correct.
- "no FAIL; 1 NOT RUN", "None failed, 1 skipped", "nothing failed but
  criterion 3 was not run" and "0 regressions; NOT RUN: 1" all still
  pass: the zero is followed by more than the grammar allows, or a
  later match names. Not a regression risk.

## Mutations (tests.test_gates, root `gates.py` only, each landed, each restored)

`mutate_review_zero.py` asserts each old text occurs exactly once,
rewrites it, runs `python3 -m unittest tests.test_gates`, and restores
the bytes in a `finally` block.

```
== m1_no_hyphen_tail landed=True rc=0 ['Ran 287 tests in 4.029s', 'OK']
== m2_no_emphasis_tail landed=True rc=1 ['Ran 287 tests in 4.049s', 'FAILED (failures=1)']
   FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (...) (summary='1 PASS, **0** NOT RUN.')
== m3_no_was_were landed=True rc=1 ['Ran 287 tests in 4.070s', 'FAILED (failures=1)']
   FAIL: test_zero_count_summary_over_a_disclosed_criterion_fails (...) (summary='1 PASS; no criteria were skipped.')
== m4_no_dot_lookbehind landed=True rc=0 ['Ran 287 tests in 4.067s', 'OK']
== m5_no_word_slot landed=True rc=1 ['Ran 287 tests in 4.069s', 'FAILED (failures=2)']
   FAIL: ... (summary='1 PASS, 0 criteria skipped.')
   FAIL: ... (summary='1 PASS; no criteria were skipped.')
== m6_no_negations landed=True rc=1 ['Ran 287 tests in 4.056s', 'FAILED (failures=3)']
   FAIL: ... (summary='1 PASS; no criteria were skipped.')
   FAIL: ... (summary='1 PASS; none skipped.')
   FAIL: ... (summary='1 PASS; nothing was skipped.')
restored: True
```

m1 and m4 survive (Minor 3). The rest are each caught by the subtest
for the shape the branch exists for.

## Findings

No critical and no major findings.

### Minor: honest named Summaries are refused when the zero's one-word slot or the hyphen tail swallows the separator

- Scenario: a judged artifact with one disclosed criterion and the
  Summary "3 PASS, 0 FAIL - NOT RUN: criterion 9." (ASCII spaced
  hyphen as a dash) or "3 PASS, 0 FAIL NOT RUN: criterion 9." (comma
  dropped). `SUMMARY_ZERO_COUNT` reads "0 FAIL -" / "0 FAIL" as a zero
  count directly before "NOT RUN": the `(?:\s+[^\W\d_]+)?` slot accepts
  a count label (`FAIL`, `PASS`) as the zero's noun, and the
  `[\s*_`-]*` tail accepts a spaced dash. H returns its roll-up string
  (probe above) for a Summary that names the criterion, which the
  brief's success criterion 3 says must pass. The em-dash and
  semicolon spellings of the same line pass. Only a Summary whose every
  unknown-kind mention is so shaped is refused, and no tracked artifact
  has the shape (sweep above; 6 ASCII " - " dash lines in all tracked
  verification.md files against 828 em-dash lines). The hyphen in the
  tail is untested (m1): the term's leading boundary already refuses a
  match straight after a hyphen, so the tail's hyphen only ever acts on
  a spaced dash.
- Standard: none
- Decision: fixed in `c2ef6e0` (Owner: Fix now). The one-word slot no
  longer takes a word starting `pass` or `fail`, and the tail no longer
  takes a hyphen. See "Fix loop" below.

### Minor: zero shapes that still name are not recorded as limits

- Scenario: a judged artifact with one disclosed criterion and a Summary
  written as a count after its word ("NOT RUN: 0", "Not run: 0."), a
  table (`| NOT RUN | 0 |`, or a header row over a counts row), a
  hard-wrapped line ("11 PASS, 0 FAIL, 0" then "NOT RUN." on the next
  line), "0: NOT RUN", "0 – NOT RUN" (en dash), "0 (zero) NOT RUN" or
  "0x NOT RUN". Each still passes over the disclosure on HEAD (probe
  above), so the stale-Summary drift slips through in those spellings.
  None is a regression (origin/main passes them too), and "directly
  precedes" in ADR-0108's Decision excludes them by its wording. But
  ADR-0108's Consequences record only the two-word negation as an
  accepted limit. The hard-wrap shape is the likeliest in this repo,
  whose artifacts wrap prose near 72 columns, and the table and
  count-after-word shapes are what an author following the template's
  "pass/fail counts" could reach for.
- Standard: none
- Decision: deferred. Prevention for a gap nobody has used (0 tracked
  artifacts have any of these shapes over a disclosure). Recorded as an
  accepted limit in ADR-0108's Consequences (`c2ef6e0`) and seeded in
  `docs/backlog.md` with a proposed fix, per ADR-0108's own "widen on a
  real artifact" rule.

### Minor: two `SUMMARY_ZERO_COUNT` branches are unpinned and one is undocumented

- Scenario: m1 (the tail's `-`) and m4 (the `.` in the leading
  lookbehind `(?<![\w.])`) both survive `tests.test_gates`. A later
  edit could drop either with every test green. Without the `.`,
  "1.0 NOT RUN" would read its `0` as a zero count. ADR-0108's Decision
  says "as a whole word" and never mentions the decimal guard, so the
  code holds a rule the ADR does not state.
- Standard: none
- Decision: fixed in `c2ef6e0` (Owner: Fix now). The hyphen branch is
  deleted and the deletion pinned; the dot guard is pinned and stated
  in ADR-0108. See "Fix loop" below.

### Minor: `_names_unknown` is quadratic in line length

- Scenario: for each `SUMMARY_UNKNOWN_TERM` match, `_names_unknown`
  runs `SUMMARY_ZERO_COUNT.search(line, 0, match.start())`, rescanning
  the whole prefix. It runs on every unfenced line of every section
  (not only Summaries). Measured on HEAD:
  ```
  200 2200 False 0.016 s
  2000 22000 False 1.57 s
  10000 110000 False 39.132 s
  ```
  (repetitions of "0 skipped, ", line length, result, time). A pasted
  110 kB single line in a `verification.md` makes `gates.py` spend
  about 40 s on one file. The longest line in any tracked
  `verification.md` is 1132 characters
  (`docs/features/first-live-dispatch/verification.md`), well under the
  point where this shows.
- Standard: none
- Decision: deferred. No real input reaches it, and it is a CI-time
  cost, not a wrong verdict. Seeded in `docs/backlog.md`: anchor the
  zero search to a bounded window before `match.start()`, with the
  window's width stated beside the grammar.

### Minor: `skills/verify/SKILL.md` still states the pre-ADR-0108 rule

- Scenario: decayed contract. Lines 31 to 33 say "Detector H refuses a
  Summary that names no unknown word over a criterion with a labelled
  NOT RUN verdict (ADR-0107)". Under ADR-0108 a Summary that holds an
  unknown word ("0 NOT RUN") is refused too, so a Verify author reading
  the skill body rather than the template is told the old rule. The
  template (line 11) was updated; the skill body was not. Implement
  logged this in defect.md's Notes as out of scope.
- Standard: none
- Decision: deferred. The template the author fills carries the rule,
  and the brief scoped only the template. Seeded in `docs/backlog.md`:
  cite ADR-0108 there and say a zero count names nothing.

## Passes with no findings

- **Correctness:** clean apart from Minors 1, 2 and 4. `$` with an
  explicit `endpos` anchors at the match start as intended, and
  per-match judging holds ("0 NOT RUN, 1 skipped" names on its second
  match; `test_sections_do_not_record_a_zero_count_as_naming`). "10
  NOT RUN" still names (the `\w` lookbehind; Verify's control).
- **Design:** clean. The helper stays private in `gates.py`, no new
  module, one parse, one owner (above). The trigger, cutoff, vocabulary
  and problem string are ADR-0107's, unchanged.
- **Security:** clean apart from Minor 4. Pure functions over artifact
  text, no I/O, stdlib only (standards slug `stdlib-only` met).
- **Complexity:** one 8-line helper and one regex; the cut-list finds
  nothing to cut beyond Minor 1's unused hyphen branch. The diff's one
  `lean:` marker names its ceiling (one word between the zero and the
  verb) and its trigger ("a real artifact that uses one").
- **ADR compliance:** clean. `adr_status.py` reports ADR-0107 as
  `partial` ("superseded in part by ADR-0108 (the naming clause;
  provisional)") and ADR-0108 as `provisional`. ADR-0107's Decision and
  Consequences are untouched; only its status line and README row
  changed, as the protocol's "Never rewrite" rule asks. ADR-0108's
  Decision matches the code (0/zero/no/none/nothing, at most one word,
  optional was/were, spaces, hyphens or emphasis), except the
  undocumented decimal guard (Minor 3). Its supersession of ADR-0107's
  negation consequence is partial, and its Consequences say so (the
  two-word negation). 0108 is free on origin/main and no PR is open
  (`gh pr list --state open` -> `[]`). ADR-0095: `plugin.json` is
  untouched.
- **Tests:** exact problem strings through the public
  `evidence_problems` and `check_evidence_honesty`. No existing test
  edited (0 deleted lines). The no-disclosure and hyphen tests pass
  before and after the fix by design (the brief's "stays green"
  guards), not vacuously: they would fail if a zero shape tripped
  another H rule or the roll-up began refusing without a disclosure.
- **Template:** `skills/verify/TEMPLATE.md` line 11 says a zero count
  names nothing and to re-count after a criterion changes, which matches
  the code.
- **Payload and manifest:** `cmp` identical; detector E clean
  (`python3 gates.py` below).
- **Domain passes:** none selected. No changed path matches payments,
  migrations or dependencies; `factory/manifest.json` is a checksum pin,
  not a package manifest.

## Final checks (HEAD `7e017c6`, before this review.md)

```
$ python3 run_tests.py
tests: 3318 tests across 106 modules in 14.4s on 8 workers, 0 problem(s)
$ python3 lint.py
lint: 0 problem(s) across 34 skills
$ python3 kb.py drift
drift: 0 problem(s)
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

## Fix loop (2026-10-18)

The Owner answered "Fix now" for Minors 1 and 3 and left 2, 4 and 5
deferred. Fixed test-first in `c2ef6e0`
(`fix(gates): a count label or a spaced dash after a zero leaves the
Summary naming`): `gates.py`, its payload copy (`cmp` identical), the
manifest regen (no stray `.orig`/`.rej`/`__pycache__` under
`factory/templates/`), three new tests in `tests/test_gates.py`, and
ADR-0108's amendment and Consequences line. No existing test's
expectation changed.

The regex, before and after:

```
before: (?<![\w.])(?:0|zero|no|none|nothing)(?:\s+[^\W\d_]+)?(?:\s+(?:were|was))?[\s*_`-]*$
after:  (?<![\w.])(?:0|zero|no|none|nothing)(?:\s+(?!pass|fail)[^\W\d_]+)?(?:\s+(?:were|was))?[\s*_`]*$
```

Excluding count labels from the one-word slot alone makes all three of
Minor 1's shapes name. The hyphen was dropped as well, by decision, not
necessity: a spaced ASCII dash is a clause separator, as the em and en
dash already were, and keeping it would only ever refuse an honest
"no regressions - NOT RUN: criterion 9" (ADR-0108's 2026-10-18
amendment). The cost is that "0 - NOT RUN" now names; ADR-0108 lists it
with the other accepted limits.

New tests, before the fix (gates.py at `b0a00e7`):

```
FAIL: test_named_summary_after_a_zero_count_label_passes (...) (summary='3 PASS, 0 FAIL NOT RUN: criterion 9.')
FAIL: test_named_summary_after_a_zero_count_label_passes (...) (summary='3 PASS, 0 FAIL - NOT RUN: criterion 9.')
FAIL: test_named_summary_after_a_zero_count_label_passes (...) (summary='3 PASS, 0 FAIL -- skipped: live dispatch.')
FAIL: test_named_summary_after_a_zero_count_label_passes (...) (summary='3 PASS, 0 FAILED NOT RUN: criterion 9.')
FAIL: test_named_summary_after_a_zero_count_label_passes (...) (summary='0 passed NOT RUN: criterion 9.')
FAIL: test_spaced_hyphen_after_a_zero_count_is_a_separator (...)
AssertionError: Lists differ: [(8, 'summary "Summary" neither counts nor[118 chars]ss')] != []
Ran 3 tests in 0.002s
FAILED (failures=6)
```

`test_a_decimal_is_not_a_zero_count` passed before the fix: it pins a
guard the code already had, so its red is shown by mutation m4 below.
After the fix, with the existing refusal tests alongside:

```
test_named_summary_after_a_zero_count_label_passes ... ok
test_spaced_hyphen_after_a_zero_count_is_a_separator ... ok
test_a_decimal_is_not_a_zero_count ... ok
test_zero_count_summary_over_a_disclosed_criterion_fails ... ok
test_hyphenated_zero_over_a_disclosure_stays_refused ... ok
Ran 5 tests in 0.001s
OK
```

Mutations re-derived for the new regex (`mutate_fixloop_zero.py` in
the session scratchpad; same harness as above, each landed, each
restored). Every one is now caught, m1 and m4 included:

```
== m1_hyphen_tail_restored landed=True rc=1 ['Ran 290 tests in 4.514s', 'FAILED (failures=1)']
   FAIL: test_spaced_hyphen_after_a_zero_count_is_a_separator
== m2_no_emphasis_tail landed=True rc=1 ['Ran 290 tests in 4.704s', 'FAILED (failures=1)']
   summary='1 PASS, **0** NOT RUN.'
== m3_no_was_were landed=True rc=1 ['Ran 290 tests in 4.195s', 'FAILED (failures=1)']
   summary='1 PASS; no criteria were skipped.'
== m4_no_dot_lookbehind landed=True rc=1 ['Ran 290 tests in 4.213s', 'FAILED (failures=1)']
   FAIL: test_a_decimal_is_not_a_zero_count
== m5_no_word_slot landed=True rc=1 ['Ran 290 tests in 4.224s', 'FAILED (failures=2)']
   summary='1 PASS, 0 criteria skipped.'
   summary='1 PASS; no criteria were skipped.'
== m6_no_negations landed=True rc=1 ['Ran 290 tests in 4.338s', 'FAILED (failures=3)']
   summary='1 PASS; no criteria were skipped.'
   summary='1 PASS; none skipped.'
   summary='1 PASS; nothing was skipped.'
== m7_no_label_exclusion landed=True rc=1 ['Ran 290 tests in 4.799s', 'FAILED (failures=3)']
   summary='3 PASS, 0 FAIL NOT RUN: criterion 9.'
   summary='3 PASS, 0 FAILED NOT RUN: criterion 9.'
   summary='0 passed NOT RUN: criterion 9.'
== m8_fail_only_exclusion landed=True rc=1 ['Ran 290 tests in 4.341s', 'FAILED (failures=1)']
   summary='0 passed NOT RUN: criterion 9.'
restored: True
```

The review's probe on the fixed tree: Minor 1's three shapes now
`pass`; "**0** NOT RUN", "ZERO deferred", "0 criteria skipped", "no
criteria were skipped", "none skipped", "nothing was skipped", "11
PASS, 0 FAIL, 0 NOT RUN.", "none NOT RUN" and "1/0 NOT RUN" stay
`REFUSED`; "1.0 NOT RUN" passes. The tracked-artifact sweep, `b0a00e7`
against the fixed tree: `files=93 refused_main=0 refused_head=0
outcome_changes=0 summary_flips=0`.

Deferred, each with a `docs/backlog.md` seed tagged
`(from: maintenance:a-zero-count-names-nothing)`: Minor 2 (also an
ADR-0108 Consequences line), Minor 4 and Minor 5.

Checks after the fix (`c2ef6e0` plus the seeds):

```
$ python3 run_tests.py
tests: 3321 tests across 106 modules in 16.8s on 8 workers, 0 problem(s)
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

Ready for Ship. All five passes and the test review ran; none was
skipped or left unknown, and the domain passes were not selected. No
critical or major finding. The Owner chose Fix now for Minors 1 and 3,
both fixed in `c2ef6e0` with the four checks green after. Three minors
stay deferred with reasons and a backlog seed each: the zero shapes
that still name (also an ADR-0108 accepted limit), the quadratic
rescan, and the stale sentence in `skills/verify/SKILL.md`.
