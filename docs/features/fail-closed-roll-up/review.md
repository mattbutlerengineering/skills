---
stage: review
run: feature:fail-closed-roll-up
date: 2026-10-17
assumptions:
  - "Unattended review (autorun): no live Owner to arbitrate severity. Severities are the reviewer's, against the caller's bar: critical = the gate fails an honest artifact on main or in a likely shape, or breaks CI or stamped repos. None met it."
  - "Recommended default taken (fix loop): a finding was fixed in this stage only when the fix was one condition plus one test, written first and seen failing. The slashless NA head met that bar and is fixed (d8d6895). Every other finding is recorded, not fixed; the two open majors need the Owner's fix-or-defer under the skill's step 9 and are surfaced in the Verdict, not deferred on the Owner's behalf."
  - "Recommended default taken (base): the diff reviewed is `git diff origin/main...HEAD`, the branch's own base (verification.md's assumption on the stale local main ref)."
---

# Review: Fail-closed roll-up for verification Summaries

## Scope

`git diff origin/main...HEAD` on `feat/fail-closed-roll-up`: 13 commits
from `207054d` to `3993112`, 20 files. Code: `gates.py` (`SUMMARY_TITLE`,
`SUMMARY_UNKNOWN_TERM`, `ROLLUP_ADOPTED`, the `names_unknown` flag,
`_rollup_applies`, `_rollup_problems`, the call in `evidence_problems`),
`gates_selftest.py` (one defect fixture and one expect substring), their
payload mirrors under `factory/templates/tools/factory/`, and
`factory/manifest.json`. Tests: `tests/test_gates.py`
`TestEvidenceRollUp`. Docs: `CONTEXT.md`, `docs/pipeline-protocol.md`,
`skills/verify/SKILL.md`, `skills/verify/TEMPLATE.md`,
`skills/review/TEMPLATE.md`, ADR-0107 and the ADR index, the backlog
claim, and the run's own artifacts. `verification.md` is present
(17 PASS, 0 FAIL, 0 NOT RUN), so the soft gate is met.

Method: every rule input shape was probed through the public
`gates.evidence_problems` with a scratch script outside the repo
(`probe.py` in the session scratchpad), and nine mutations of `gates.py`
were run against the whole suite, each checked as landed and reverted.

### Probe output (dishonest and honest shapes, pre-fix)

Each line is one artifact: frontmatter, `## Summary` with the quoted
text, one evidenced PASS criterion and one `- Result: NOT RUN` criterion.
`FIRES` means H reports the roll-up problem.

```
== date shapes (full-pass summary) ==
plain post-cutoff                                       -> FIRES
quoted post-cutoff                                      -> silent
single-quoted                                           -> silent
empty date:                                             -> silent
datetime                                                -> FIRES
dd/mm/yyyy                                              -> silent
date with comment                                       -> FIRES
no frontmatter                                          -> FIRES
Date: capital key                                       -> FIRES
date: today                                             -> FIRES
pre-cutoff                                              -> silent
== honest summaries that might FP ==
7 PASS; the live dispatch check could not be run without a second account. -> FIRES
7 PASS, 1 BLOCKED (live dispatch needs a second account). -> FIRES
7 PASS; live dispatch wasn't run.                       -> FIRES
7 PASS; live dispatch remains unexercised.              -> FIRES
7 PASS, 1 not applicable.                               -> FIRES
7 of 8 criteria pass; live dispatch is outstanding.     -> FIRES
7 PASS, 1 NOT-RUN.                                      -> silent
7 PASS, 1 NOT_RUN.                                      -> FIRES
7 PASS, 1 NOTRUN.                                       -> FIRES
7 PASS, 1 unverifiable.                                 -> FIRES
7 PASS, 1 open (live dispatch).                         -> FIRES
7 pass; live dispatch did not run.                      -> silent
7 PASS, 1 skip.                                         -> silent
7 PASS, 1 skips.                                        -> FIRES
7 PASS, 1 skipped-by-design.                            -> FIRES
7 PASS and 1 deferred/blocked.                          -> FIRES
7 PASS; 1 criterion not yet verified.                   -> silent
7 PASS, 1 N/A.                                          -> silent
7 PASS, 1 NA.                                           -> FIRES
**7 PASS, 1 NOT RUN**                                   -> silent
7 PASS, 1 `NOT RUN`                                     -> silent
7 PASS, 1 untested.                                     -> silent
== dishonest summaries that satisfy too easily ==
All criteria pass; nothing pending.                     -> silent
All pass. Next steps: TODO none.                        -> silent
All pass (n/a: see table).                              -> silent
| Criterion | Result | / |---|---| / | all | PASS | / | -> silent
All 8 criteria pass; we skip the boilerplate here.      -> silent
All pass; the unknown-term rule is satisfied.           -> FIRES
All pass with no unknowns.                              -> FIRES
All criteria pass; see docs/tbd.md                      -> FIRES
All pass. <!-- not run -->                              -> silent
All criteria pass; skip-free run.                       -> FIRES
All criteria pass. /  / > not run                       -> silent
== title shapes ==
title 'Summary'                                         -> FIRES
title 'summary'                                         -> FIRES
title 'SUMMARY'                                         -> FIRES
title 'Summary '                                        -> FIRES
title 'Summary:'                                        -> silent
title '1. Summary'                                      -> silent
title 'Summary of results'                              -> silent
title '**Summary**'                                     -> silent
title '`Summary`'                                       -> silent
== setext summary ==
setext [(6, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Live dispatch", line 21); unknown never rolls up to pass')]
```

On main no tracked `verification.md` has a quoted `date:` and none lacks
one (`grep -rln '^date: *["'"'"']'` and `grep -rL '^date:'` over
`docs/**/verification.md` both printed nothing).

### Mutation results (whole suite, `python3 run_tests.py`, plus `gates.py --selftest`)

Every mutation also fails `test_every_mirrored_root_file_matches_its_payload_copy`,
because only the root copy was mutated; that line is the payload pin,
not a rule test, and is left out below.

```
== M1 rollup never fires: landed=True suite_rc=1 selftest_rc=1
    test_full_pass_summary_over_a_disclosed_criterion_fails
    test_selftest_passes
    test_the_selftest_flag_still_runs_through_gates_py
    test_two_disclosed_criteria_give_one_problem_counting_both
    test_undated_artifact_is_judged_fail_closed
    test_unknown_word_only_inside_a_fence_does_not_count
    test_wrapper_prefixes_the_rollup_problem
   selftest: selftest: FAIL
== M2 names_unknown never set: landed=True suite_rc=1 selftest_rc=0
    test_honest_summary_shapes_from_main_pass
    test_sections_record_an_unfenced_unknown_word
    test_summary_counting_the_not_run_item_passes
    test_summary_naming_a_different_unknown_kind_passes
== M3 cutoff ignored: landed=True suite_rc=1 selftest_rc=0
    test_artifact_dated_before_the_cutoff_is_grandfathered
== M4 missing date grandfathered: landed=True suite_rc=1 selftest_rc=0
    test_undated_artifact_is_judged_fail_closed
== M5 drop not-yet/unknown/unmet/unproven: landed=True suite_rc=1 selftest_rc=0
    test_honest_summary_shapes_from_main_pass
== M6 trigger on any section incl summary: landed=True suite_rc=1 selftest_rc=0
   suite tail: tests: 3303 tests across 106 modules in 19.0s on 8 workers, 1 problem(s)
   (only the payload pin fails: no rule test kills it)
== M7 rollup not wired in evidence_problems: landed=True suite_rc=1 selftest_rc=1
    (same seven rule tests as M1, plus both selftest tests)
== M8 fenced lines count toward names_unknown: landed=True rc=1
    FAIL: test_sections_record_an_unfenced_unknown_word
    FAIL: test_unknown_word_only_inside_a_fence_does_not_count
== M9 problem string counts 1, not len(disclosed): landed=True rc=1
    FAIL: test_two_disclosed_criteria_give_one_problem_counting_both
```

Eight of nine mutations are killed by a rule test that asserts the exact
problem string through `gates.evidence_problems` or
`gates.check_evidence_honesty`. M6 survives (minor finding below). The
selftest catches the rule's absence (M1, M7), so its new expect
substring is not vacuous.

## Findings

### Major: the Summary vocabulary missed the slashless `NA` disclosure head (fixed)

- Scenario: a criterion with `- Result: NA` is a labelled disclosure
  (`DISCLOSURE_VERDICT` reads `n/?a`), so it triggers the roll-up. Its
  honest Summary "7 PASS, 1 NA." counts it in the criterion's own word,
  but `SUMMARY_UNKNOWN_TERM` read only `n/a`, so H failed the artifact
  (probe line `7 PASS, 1 NA. -> FIRES`). ADR-0107 states the vocabulary
  is "H's disclosure heads"; the code disagreed with the ADR.
- Standard: none.
- Decision: fixed in `d8d6895`. The test
  `test_summary_naming_the_slashless_na_head_passes` was written first
  and seen failing (`FAILED (failures=1)`, the full roll-up problem at
  line 8), then `n/a` became `n/?a` in both copies of `gates.py`, the
  manifest was regenerated, and the test passed.

### Major: a quoted, empty or non-ISO `date:` grandfathers a post-cutoff Summary

- Scenario: `parse_frontmatter` returns the raw value, and
  `_rollup_applies` grandfathers any string that sorts before
  `"2026-10-17"`. `date: "2026-10-20"` (YAML-valid, quoted) begins with
  `"`, which sorts before `2`; `date:` with no value is `""`; and
  `date: 20/10/2026` begins with `1`. All three make a full-pass Summary
  over a NOT RUN criterion silent (probe: `quoted post-cutoff`,
  `single-quoted`, `empty date:`, `dd/mm/yyyy` -> silent). ADR-0107,
  the architecture and `docs/pipeline-protocol.md` all say a missing
  date is judged so "omitting the date cannot dodge the rule"; an empty
  `date:` is an omitted date that dodges it. This is a dishonest path
  ADR-0107 does not accept. No artifact on main has the shape, so
  nothing fails today.
- The same comparison is the precedent O (`COVERAGE_ADOPTED`) and M
  (`CAPTURE_ADOPTED`) already use, so the fix is a convention decision,
  not a one-line local change: grandfather only a value that matches
  `\d{4}-\d{2}-\d{2}` after stripping quotes, and judge everything
  else, in all three detectors or in a shared helper.
- Standard: none.
- Decision: open. Routed to the Owner (fix in Implement, or defer with
  a reason). Recommended: fix for H in this run with one test per shape,
  and file a backlog seed for O and M.

### Major: honest gap phrasings outside the vocabulary fail the gate

- Scenario: the author writes `- Result: NOT RUN` under a criterion and
  a Summary that names the gap in ordinary words. Each of these fails H
  (probe): "could not be run", "wasn't run", "remains unexercised",
  "1 not applicable", "is outstanding", "1 BLOCKED", "1 NOT_RUN",
  "1 NOTRUN", "1 unverifiable", "1 skips", "1 skipped-by-design",
  "1 deferred/blocked". The last two fail because the trailing
  `(?![\w/-])` boundary rejects a hyphen or slash after the word. The
  brief names false positives on honest Summaries as the top risk, since
  they teach authors to reword. Against that: all three honest
  disclosing Summaries on main count with a head word, the problem
  string says what to do, and the template now asks for a count. So this
  is not a likely shape on the evidence, which is why it is major and
  not critical.
- Standard: none.
- Decision: open. Routed to the Owner. Recommended: widen in a
  follow-up with evidence, not by fit (ADR-0107's own rule for its
  vocabulary): `not applicable`, `n't (been )?run`, `not be(en)? run`,
  and drop `-` and `/` from the trailing boundary.

### Minor: invisible and incidental words satisfy the rule

- Scenario: `All pass. <!-- not run -->` passes, though an HTML comment
  never renders, so the reader sees an unqualified pass. So do a
  blockquote (`> not run`), a verb ("we skip the boilerplate"),
  "TODO none" and an `n/a` table cell. ADR-0107 accepts the negation
  dodge only; the HTML comment is a dodge the ADR does not name.
- Standard: none.
- Decision: deferred. The rule is a floor against the silent case, and
  an author writing an invisible word is gaming, not drifting. Worth a
  line in ADR-0107's successor if a real artifact does it.

### Minor: heading variants other than a rename escape the rule

- Scenario: `## **Summary**`, `## Summary:`, `## 1. Summary` and
  `` ## `Summary` `` are not read as a Summary (probe), so a full-pass
  roll-up under them is silent. ADR-0107 accepts renames; these are the
  same word with formatting.
- Standard: none.
- Decision: deferred. All 29 Summary headings on main are spelled
  exactly `Summary`, and the template spells it.

### Minor: the disclosure heads are stated twice in `gates.py`

- `gates.py` `SUMMARY_UNKNOWN_TERM` (line 235) — `reuse`: its word
  list restates `DISCLOSURE_VERDICT`'s heads (line 217). What replaces
  it: one shared heads alternation, used anchored by the verdict regex
  and unanchored by the Summary regex. Evidence that the copies drift:
  the `NA` finding above was exactly that drift. `one_owner.py` does not
  see it (it compares values across modules, and these are two different
  patterns in one module): its 9 problems are the same before and after
  this branch, none naming a new constant.
- Standard: none.
- Decision: deferred. Behaviour is now identical on the heads; the
  refactor is its own change.

### Minor: two docs overstate what the gate does

- Scenario: `skills/verify/SKILL.md` says "Detector H refuses one that
  does not". H refuses only when another section holds a labelled
  disclosure, the Summary is titled exactly `Summary`, and the date is
  not grandfathered; a Summary over a prose-only gap passes.
  `docs/pipeline-protocol.md` says H judges "undated ones", which the
  empty-`date:` scenario above contradicts.
- Standard: none.
- Decision: deferred. The protocol line becomes true once the date
  major is fixed; the SKILL.md line is a pointer, and the protocol
  carries the precise rule.

### Minor: no test pins that a Summary's own labelled disclosure is not a trigger

- Scenario: mutation M6 (count the Summary's own `results` as disclosed)
  survives the whole suite. The only observable case is a Summary with
  `Result: NA`-style text that the vocabulary misses; after the fix the
  mutation is close to equivalent. Title matching (`casefold`, `strip`)
  also has no test of its own; the probe shows it works.
- Standard: none.
- Decision: deferred.

## Passes with no findings

- Correctness: fence handling (M8 killed; a Setext `Summary` is read;
  the unclosed-fence path is unchanged), the problem-string contract
  (exact strings asserted through `evidence_problems` and
  `check_evidence_honesty`), one problem per artifact, and the backstop
  never firing together with the roll-up all hold. Datetime and
  commented dates sort correctly.
- Design: one section parse (a flag on `verification_sections`, no
  second walk); the vocabulary is owned by `CONTEXT.md` and only pointed
  to from the protocol and templates; the import widens
  `from protocol import` with no new module edge. Matches
  `architecture.md`. ADR-0107 records the decision.
- Security: pure text parsing, no new I/O, no secrets.
- Complexity: one `reuse` cut (the minor above); no `lean:` marker added
  (`grep -c "lean:"` over the diff printed `0`).
- ADR compliance (`python3 adr_status.py .`: 78 active, 19 provisional,
  10 partial): ADR-0095 holds (`.claude-plugin/plugin.json` untouched);
  ADR-0050 and detector E hold (payload copies regenerated, manifest
  committed with each change); ADR-0091 holds (no new import edge);
  ADR-0082 holds (ADR-0107 written); ADR-0029 holds (backlog seed
  claimed, not removed). No shipped `verification.md` or `review.md` was
  edited. Standards: `stdlib-only` holds.
- Domain passes: none selected (no changed path matches the payments,
  migrations or dependencies table).

### Final checks after the fix (`d8d6895`)

```
$ python3 run_tests.py 2>&1 | tail -1
tests: 3304 tests across 106 modules in 19.0s on 8 workers, 0 problem(s)
$ python3 lint.py | tail -1
lint: 0 problem(s) across 34 skills
$ python3 kb.py drift | tail -1
drift: 0 problem(s)
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
```

## Verdict

Not ready to ship unattended: two majors are open and need the Owner's
fix-or-defer (step 9). Count: 1 major fixed, 2 majors open (the
quoted/empty `date:` dodge, and honest phrasings outside the
vocabulary), 5 minors deferred with reasons, 0 critical. Every review
pass ran; no pass is unknown. The gate is green on main and in CI, it
breaks no stamped repo (its existing artifacts predate the cutoff), and
8 of 9 mutations are killed by exact-string tests. Once the Owner fixes
or defers the two open majors, this is ready for Ship.
