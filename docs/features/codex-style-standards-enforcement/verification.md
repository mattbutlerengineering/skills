---
stage: verify
run: feature:codex-style-standards-enforcement
date: 2026-09-28
assumptions:
  - "Criterion 7 (defect.md completeness) is read through the accepted ADR-0073 grandfather cutoff. The detector checks only briefs dated on or after 2026-09-21. That is 0 of this repo's 57 existing briefs, and all 57 runs are already past Verify. On that reading it is recorded PASS. Under PRD-0004's literal wording ('every maintenance run's defect.md') it would be FAIL. This is an interpretive call, not a skill default, and it needs a human ruling."
  - "Criterion 8 (battery green through every work item) is read per work-item commit, replayed in a local clone. Two rows' own commits were red, so it is recorded FAIL. Read per merge to main, it would PASS, because main was never red. This is an interpretive call, not a skill default, and it needs a human ruling."
---

# Verification: Codex-style standards enforcement

## Summary

There are 20 criteria: PRD-0004's nine success criteria, plus eleven breakdown acceptance criteria that no PRD criterion covers. Results: **16 PASS, 3 FAIL, 1 DEFERRED, 0 not verified.**

The machinery works as specified:

- The index regenerates deterministically.
- Detector K catches drift, and catches an `enforced` statement whose source ADR is not accepted.
- Detector M catches incomplete briefs.
- The selftest really depends on both detectors: stubbing either one turns it red.
- The four prose surfaces carry the load, cite and block steps.

The three failures:

- **Criterion 9.** The index's CLAUDE.md-sourced half is asserted, not verified. No detector reads it.
- **Criterion 8.** Two work items' own commits left the battery red. Main was never red, but the breakdown's close-out note says otherwise.
- **Criterion 14.** The shipped selftest never plants a missing `Reproduction / Evidence` section.

The promotion bar (WO-0064) is deferred by the owner, not passed.

Method:

- The battery ran at HEAD 6742c9f in this worktree.
- Every planted-defect scenario ran in a scratch copy of HEAD (`git archive HEAD`, never the worktree).
- The per-commit replay ran in a local `git clone` of this repo.
- Soft gate: every row in `breakdown.md` is checked.

## Criteria & evidence

### 1. `docs/standards.json` exists, one entry per statement, `{slug, statement, level, source, status, domain}` with the issue's enums (PRD-0004 §Success criteria)

- Check: loaded the committed index and checked every entry's key set and each enum.
- Evidence:
  ```
  $ python3 - <<'EOF'   # key-set and enum check over docs/standards.json
  4 entries
  adr0004-typed-ids-in-frontmatter keys_ok=True MUST advisory pipeline adr/0004#adr0004-typed-ids-in-frontmatter
  adr0032-one-way-mirror keys_ok=True MUST advisory factory adr/0032#adr0032-one-way-mirror
  eval-honesty keys_ok=True MUST advisory eval CLAUDE.md#eval-honesty
  stdlib-only keys_ok=True MUST advisory factory CLAUDE.md#stdlib-only
  level ⊆ {MUST,SHOULD}: True
  status ⊆ {advisory,enforced}: True
  domain ⊆ {factory,pipeline,eval,docs}: True
  sorted by slug: True
  ```
- Result: PASS

### 2. A stdlib-only regeneration script deterministically rebuilds the ADR-derived subset; hand-curated `CLAUDE.md#` entries survive regeneration untouched (PRD-0004 §Success criteria)

- Check (scratch copy):
  - Ran the regen twice, once through the `factory.py` router and once directly, hashing the file before and after each run.
  - Planted a new ADR bullet, regenerated, and compared the hand-curated entries before and after.
  - Read the module's imports.
- Evidence:
  ```
  $ shasum -a 256 docs/standards.json
  c155e7d5bc26221f8bbe9035968b403455f584b7b1fd32d49a8cfce585699711  docs/standards.json
  $ python3 factory.py standards-index update
  standards-index: 0 problem(s)
  c155e7d5bc26221f8bbe9035968b403455f584b7b1fd32d49a8cfce585699711  docs/standards.json
  $ python3 standards_index.py update
  standards-index: 0 problem(s)
  c155e7d5bc26221f8bbe9035968b403455f584b7b1fd32d49a8cfce585699711  docs/standards.json
  $ diff docs/standards.json <worktree>/docs/standards.json && echo "identical to committed"
  identical to committed

  # planted "- **zz-planted-new** (docs): A planted statement SHOULD appear after regen." into ADR-0032
  $ python3 standards_index.py update
  standards-index: 0 problem(s)
  hand-curated entries byte-identical across regen
  adr0004-typed-ids-in-frontmatter adr/0004#adr0004-typed-ids-in-frontmatter advisory
  adr0032-one-way-mirror adr/0032#adr0032-one-way-mirror advisory
  eval-honesty CLAUDE.md#eval-honesty advisory
  stdlib-only CLAUDE.md#stdlib-only advisory
  zz-planted-new adr/0032#zz-planted-new advisory

  $ grep -n "^import\|^from" standards_index.py
  60:import json
  61:import re
  62:import sys
  63:from pathlib import Path
  65:from cli import report
  66:from knowledge_plane import repo_root
  ```
- Result: PASS. `cli` and `knowledge_plane` are the repo's own stdlib-only seams.

### 3. A new `gates.py` detector fails on committed-vs-regenerated drift, and separately on an `enforced` statement whose source ADR is not `accepted`, reusing detector D's status machinery (PRD-0004 §Success criteria)

- Check (scratch copy, a fresh tree per scenario): called `gates.check_standards_drift` in five planted scenarios, then read how K reads ADR status.
- Evidence:
  ```
  (a) committed statement text hand-edited:
  ['K: docs/standards.json has drifted from a fresh ADR regeneration (run `python3 standards_index.py update`)']
  (b) ADR gains a bullet, index not regenerated:
  ['K: docs/standards.json has drifted from a fresh ADR regeneration (run `python3 standards_index.py update`)']
  (c) control: adr0032 entry enforced, ADR-0032 accepted:
  []
  (d) same enforced entry, ADR-0032 Status line flipped to superseded:
  - Status: superseded by ADR-0073
  ["K: enforced statement 'adr0032-one-way-mirror' cites ADR-0032, status 'superseded by ADR-0073' (not accepted)"]

  $ grep -n "_adr_status_by_number" -A 8 gates.py
  1399:def _adr_status_by_number(parsed):
  1400-    """{ADR number: raw Status text (None when absent or unparseable)} —
  1401-    reuses D's own _adr_status_from_lines over parsed["adr_files"], never
  1402-    a second status parser. ...
  1406-    return {path.name[:4]: _adr_status_from_lines(lines)[1]
  1407-            for path, lines in parsed["adr_files"]}
  ```
- Result: PASS

### 4. `python3 gates.py --selftest` covers the new detectors with planted-defect fixtures (PRD-0004 §Success criteria)

- Check: ran the selftest as-is. Then ran it twice more with a stub replacing one detector each time: K (`check_standards_drift`) in one run, M (`check_capture_completeness`) in the other. This proves the fixtures depend on the detectors rather than passing vacuously.
- Evidence:
  ```
  $ python3 gates.py --selftest
  selftest: ok

  check_standards_drift stubbed -> selftest rc=1; 3 line(s)
      K: expected a problem containing 'docs/standards.json has drifted', got []
      K: expected a problem containing "enforced statement 'enforced-slug' cites ADR-0002, status 'provisional' (not accepted)", got []
      selftest: FAIL
  check_capture_completeness stubbed -> selftest rc=1; 5 line(s)
      M: expected a problem containing "missing required section 'Root-cause hypothesis'", got []
      M: expected a problem containing "missing required section 'Blast radius'", got []
      M: expected a problem containing "required section 'Defect (or Condition)' is present but placeholder-only", got []
      M: expected a problem containing "required section 'Ruled out' is present but placeholder-only", got []
  none stubbed -> selftest rc=0; 1 line(s)
      selftest: ok
  ```
- Result: PASS. Criterion 14 below has a narrower gap in M's fixture.

### 5. `skills/review/SKILL.md` and `factory/charters/reviewer/CHARTER.md` load the index filtered by touched-path domain, cite slugs, block on an unresolved `enforced` finding, and keep advisory findings non-blocking (PRD-0004 §Success criteria)

- Check: read the added steps in both files.
- Evidence:
  ```
  $ sed -n 34,39p skills/review/SKILL.md
  5. **Load applicable standards.** Read `../../docs/standards.json` if
     present (an unbootstrapped repo has none yet — proceed). Filter to
     statements whose `domain` matches what the diff touches: `factory` for
     root-tool/`factory/**` changes, `pipeline` or `docs` for skill-body/
     `docs/**` changes, `eval` for eval-set/harness changes. A finding that
     matches a filtered statement cites its `slug`.
  $ sed -n 49,55p skills/review/SKILL.md
  8. **Fix loop.** Critical findings — and any unresolved finding that cites
     an `enforced` standards-index statement, whatever severity it was ranked
     at — are fixed before Ship (...); the enforced-statement trigger sits alongside the
     critical-finding one, it doesn't redefine what "critical" means. Majors
     are fixed or explicitly deferred by the user. Minors, and findings
     against `advisory` statements, may be deferred freely.
  $ sed -n 47,51p factory/charters/reviewer/CHARTER.md
  7. Load `docs/standards.json` if present, filtered to statements whose
     `domain` matches what the diff touches (...). A finding that
     matches one cites its `slug`.
  $ sed -n 136,139p factory/charters/reviewer/CHARTER.md
  - Approve-with-nits when any `enforced` standards-index finding is
    open: an unresolved finding against an `enforced` statement blocks
    the verdict the same way an open security finding does, until
    resolved or explicitly escalated.
  ```
- Result: PASS on the text. It has not been exercised live (see Not verified). There is also a path concern for Review: see Findings outside the criteria.

### 6. `skills/architect/SKILL.md` and `factory/charters/architect/CHARTER.md` load the `factory`/`pipeline` slice before drafting and cite bearing statements (PRD-0004 §Success criteria)

- Check: read the added steps. The skill's step 4 comes before step 5 "Draft", and the charter's step 2 comes before step 3 "Design".
- Evidence:
  ```
  $ sed -n 28,32p skills/architect/SKILL.md
  4. **Load applicable standards.** Read `../../docs/standards.json` if
     present (an unbootstrapped repo has none yet — proceed). Filter to
     statements whose `domain` is `factory` or `pipeline` — the
     design-relevant slice. A decision below that bears on one cites its
     `slug` in `TEMPLATE.md`'s "Decisions & alternatives" section.
  $ sed -n 31,34p factory/charters/architect/CHARTER.md
  2. Load `docs/standards.json` if present, filtered to statements whose
     `domain` is `factory` or `pipeline` — the design-relevant slice.
     Cite a matching `slug` alongside any ADR number when a design
     decision bears on one.
  ```
- Result: PASS on the text. It has not been exercised live, and the same path concern as criterion 5 applies.

### 7. A new gate detector validates every maintenance run's `defect.md` for the protocol's required sections, non-placeholder, with exact problem strings and unit-test coverage (PRD-0004 §Success criteria)

- Check (scratch copy): planted four briefs:
  - complete, dated 2026-09-28
  - incomplete, dated 2026-09-28
  - incomplete, with no `date:`
  - incomplete, dated 2026-09-20

  Then ran M on them, compared its required list with the capture template's headings, measured M's coverage of the real corpus, and ran M's unit tests.
- Evidence:
  ```
  $ grep -n "^## " skills/capture/TEMPLATE.md
  15:## Defect (or Condition)
  20:## Reproduction / Evidence
  26:## Root-cause hypothesis
  30:## Blast radius
  35:## Ruled out
  39:## Work items
  48:## Notes

  # planted briefs -> gates.check_capture_completeness
  M: docs/fixes/zz-planted-incomplete/defect.md required section 'Reproduction / Evidence' is present but placeholder-only (template text was never filled in)
  M: docs/fixes/zz-planted-incomplete/defect.md missing required section 'Root-cause hypothesis'
  M: docs/fixes/zz-planted-incomplete/defect.md missing required section 'Ruled out'
  M: docs/fixes/zz-planted-nodate/defect.md required section 'Reproduction / Evidence' is present but placeholder-only (template text was never filled in)
  M: docs/fixes/zz-planted-nodate/defect.md missing required section 'Root-cause hypothesis'
  M: docs/fixes/zz-planted-nodate/defect.md missing required section 'Ruled out'
  # no lines for zz-planted-complete (2026-09-28, all five filled) or zz-planted-old (2026-09-20, grandfathered)

  # real corpus
  CAPTURE_ADOPTED = 2026-09-21
  57 defect.md files; 57 grandfathered (date < cutoff); 0 checked in full
  57 of the grandfathered briefs would fail M without the cutoff
  0 of 57 maintenance runs have no verification.md yet

  $ python3 -m unittest -v tests.test_gates.TestCaptureCompleteness
  test_a_brief_dated_before_adoption_is_grandfathered ... ok
  test_a_brief_dated_on_adoption_day_is_not_grandfathered ... ok
  test_a_fully_filled_brief_is_silent ... ok
  test_a_missing_date_is_not_grandfathered ... ok
  test_a_missing_section_is_flagged ... ok
  test_a_placeholder_only_section_is_flagged ... ok
  test_heading_case_does_not_matter ... ok
  test_multiple_defects_across_runs_are_each_reported ... ok
  test_no_defect_md_in_a_run_is_out_of_scope ... ok
  test_no_docs_fixes_directory_is_silent ... ok
  ```
- Result: PASS, on ADR-0073's scope. That ADR is accepted, was merged in #517, and records the cutoff in its Consequences.
  - The detector checks every brief dated on or after 2026-09-21. It fails closed on a missing date, and its problem strings are exact.
  - On this repo it checks **0 of 57** real briefs, and all 57 would fail without the cutoff.
  - All 57 runs already have a `verification.md`, so the cutoff loses nothing the criterion exists to catch: an incomplete brief caught before Verify.
  - Under PRD-0004's literal "every maintenance run's `defect.md`", this would be FAIL. The reading is logged in `assumptions:` for a human ruling.

### 8. `python3 -m unittest discover tests`, `python3 lint.py`, and `python3 gates.py && python3 gates.py --selftest` stay green through every work item (PRD-0004 §Success criteria)

- Check:
  - Ran the battery at HEAD.
  - Read #517's CI runs and their failure lines.
  - Replayed the full battery at each commit of #517's branch in a local clone (`git checkout --detach`, `git clean -fdx`).
- Evidence:
  ```
  $ python3 -m unittest discover tests        # at HEAD 6742c9f
  Ran 1793 tests in 21.406s
  OK
  $ python3 lint.py
  lint: 0 problem(s) across 25 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok

  # per-commit replay of #517's branch, then the squash on main
  # (commit | unittest | lint | gates | selftest)
  b134423 | Ran 1700 tests in 21.510s OK | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
  13ecee2 | Ran 1733 tests in 21.547s FAILED (failures=1) | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
  c9c2243 | Ran 1733 tests in 21.246s FAILED (failures=5) | lint: 0 problem(s) across 25 skills | E: factory/templates/tools/factory/standards_index.py is not in the manifest gates: 1 problem(s) | selftest: ok
  1a1f5da | Ran 1754 tests in 21.236s OK | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
  773166c | Ran 1754 tests in 21.223s OK | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
  5f30760 | Ran 1754 tests in 21.407s OK | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
  f49d517 | Ran 1754 tests in 21.544s OK | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
  ba82988 | Ran 1754 tests in 21.549s OK | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
  e0ff761 | Ran 1754 tests in 21.819s OK | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
  bc336b5 | Ran 1754 tests in 23.104s OK | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
  78c96c4 | Ran 1754 tests in 20.995s OK | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
  69ecd19 | Ran 1754 tests in 20.337s OK | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok

  == 13ecee2: feat(standards-index): add the normative-statement index seam module
  FAIL: test_every_cli_bearing_root_module_has_exactly_one_verb (test_factory_cli.TestVerbTableIsDerived.test_every_cli_bearing_root_module_has_exactly_one_verb)
  == c9c2243: chore(factory): wire standards_index.py into the VERBS router and the payload   (2 of 5 failures shown)
  FAIL: test_stamped_repo_passes_its_own_gates (test_factory_init.TestAcceptanceStampRealRepo.test_stamped_repo_passes_its_own_gates)
  AssertionError: Lists differ: ['E: factory/templates/tools/factory/standards_index.py is not in the manifest'] != []
  FAIL: test_the_totals_sentence_matches_the_manifest (test_factory_init.TestSetupDocCounts.test_the_totals_sentence_matches_the_manifest)
  AssertionError: Tuples differ: (77, 38) != (75, 37)
  $ git show --name-only --format= 1a1f5da
  factory/manifest.json
  factory/templates/tools/factory/gates.py
  gates.py
  tests/test_gates.py

  $ gh run list --branch feat/standards-enforcement-448 ...   # the two failed runs
  2026-09-22T04:54:42Z e0ff761 validator pull_request failure
  2026-09-22T04:56:18Z bc336b5 validator pull_request failure
  $ gh run view 35688670138 --log-failed | grep "B:\|gates:"
  check	Detectors and tests	2026-09-22T04:54:50.3366066Z B: PR body has no Closes #N link
  check	Detectors and tests	2026-09-22T04:54:50.3375367Z gates: 1 problem(s)
  $ gh run view 35688769087 --log-failed | grep "B:\|gates:"
  check	UNKNOWN STEP	2026-09-22T04:56:26.4353101Z B: PR body has no Closes #N link
  check	UNKNOWN STEP	2026-09-22T04:56:26.4354272Z gates: 1 problem(s)
  $ gh pr view 517 --json mergedBy,mergedAt,statusCheckRollup
  #517 MERGED mergedBy=mattbutlerengineering at=2026-09-24T03:12:16Z
    check: SUCCESS
  ```
- Result: FAIL.
  - Green now, and green at #517's squash merge. The branch's two red CI runs were detector B on the PR body, not code. Main was never red.
  - The replay shows two work items left the battery red at their own commits:
    - WO-0052's commit failed the verb-table test. It was fixed when WO-0053 added the verb.
    - WO-0053's commit shipped the payload copy without regenerating the manifest: 5 test failures plus detector E. It was fixed one commit later, inside WO-0054's commit.
  - This contradicts the breakdown's close-out traceability note (WO-0063), which says the battery "stayed green through every one of orders 51 through 62."
  - Nothing needs re-implementing. The reading is logged in `assumptions:`.

### 9. No parallel docs tree: `docs/standards.json` is derived data, the ADRs and CLAUDE.md stay the sources of truth, verified by the drift detector itself, not asserted (PRD-0004 §Success criteria)

- Check (scratch copy): the ADR-derived half is covered by criterion 3's scenarios. For the CLAUDE.md-sourced half, I pointed `stdlib-only` at an anchor that does not exist, inverted its statement, and ran K, the full gates, and lint.
- Evidence:
  ```
  stdlib-only | CLAUDE.md#no-such-anchor | SHOULD | Root Python scripts SHOULD pull in any third-party dependency they like.
  $ grep -c "no-such-anchor" CLAUDE.md
  0
  K:
  []
  $ python3 gates.py
  gates: 0 problem(s)
  $ python3 lint.py
  lint: 0 problem(s) across 25 skills

  $ grep -n "Eval honesty\|Stdlib only" CLAUDE.md      # what the two real entries paraphrase
  39:- **Stdlib only.** Every script is standalone Python 3 standard library.
  79:## Eval honesty (non-negotiable)
  ```
- Result: FAIL.
  - The ADR-derived half holds: 2 of 4 entries are regenerated from their ADRs and diffed by K, as criterion 3 shows.
  - The CLAUDE.md-sourced half does not: 2 of 4 entries are hand-maintained paraphrases of CLAUDE.md. K excludes them by design (`HAND_CURATED_PREFIX`, pinned by `test_a_hand_curated_entry_never_drifts`), and nothing else reads them. An inverted statement with a dangling anchor leaves every gate green, so that half is asserted, not verified.
  - PRD-0004 §Open questions asked for a CLAUDE.md `source` form "that the drift detector can still verify". `architecture.md` did not resolve that, and the WO-0057 row relaxed it to "resolvable by a human/reviewer".

### 10. WO-0051: a real ADR records the seam module, the K/M letter choice (and why not J), and enforcement status living in the index; its README row is `accepted`; standard human code-owner merge (PRD-0004 §Out of scope)

- Check: read ADR-0073's status, its decision headings and its README row, then read #517's merge record and CODEOWNERS.
- Evidence:
  ```
  $ grep -n "^- Status\|^\*\*(a)\|^\*\*(b)\|^(\`CAPTURE-COMPLETENESS\`), not\|^\*\*(c)" docs/adr/0073-standards-index-seam-and-detector-letters-k-m.md
  3:- Status: accepted
  31:**(a) `standards_index.py` joins the factory's seam-module set
  55:**(b) Detector letters `K` (`STANDARDS-DRIFT`) and `M`
  56:(`CAPTURE-COMPLETENESS`), not `J`.** Verified against `gates.py` as it
  91:**(c) Enforcement status (`advisory` / `enforced`) lives only in
  $ grep -n "0073" docs/adr/README.md | cut -d'|' -f1,3-
  96:| Standards index as a seam module; detector letters K and M | accepted |
  $ gh pr view 517 --json mergedBy,mergedAt
  #517 MERGED mergedBy=mattbutlerengineering at=2026-09-24T03:12:16Z
  $ grep "docs/adr/" .github/CODEOWNERS
  docs/adr/ @mattbutlerengineering
  ```
- Result: PASS

### 11. WO-0052: a malformed `## Normative statements` bullet is a returned problem string, never a silent skip; unit tests cover the parser and the regen/preserve behavior (PRD-0004 §Success criteria)

- Check (scratch copy): planted five malformed bullets in ADR-0032 and ran the regen, hashing the index before and after. Then ran the module's unit tests.
- Evidence:
  ```
  c155e7d5bc26221f8bbe9035968b403455f584b7b1fd32d49a8cfce585699711  docs/standards.json
  $ python3 standards_index.py update
  standards-index: docs/adr/0032-factory-dispatch-plane.md:66 missing or invalid slug '' (expected lowercase-kebab, e.g. 'adr0032-one-way-mirror')
  standards-index: docs/adr/0032-factory-dispatch-plane.md:67 statement carries no RFC-2119 keyword (MUST/MUST NOT/SHOULD/SHOULD NOT)
  standards-index: docs/adr/0032-factory-dispatch-plane.md:68 statement carries 2 RFC-2119 keywords, exactly one required: ['MUST', 'SHOULD']
  standards-index: docs/adr/0032-factory-dispatch-plane.md:69 domain 'ui' is not one of factory, pipeline, eval, docs
  standards-index: docs/adr/0032-factory-dispatch-plane.md:70 unreadable normative-statement bullet '- not a normative bullet at all' (expected '- **<slug>** (<domain>): <statement>')
  standards-index: 5 problem(s)
  rc=1
  c155e7d5bc26221f8bbe9035968b403455f584b7b1fd32d49a8cfce585699711  docs/standards.json   # refused to write

  $ python3 -m unittest -v tests.test_standards_index   # 33 tests, excerpt
  test_a_malformed_bullet_refuses_to_write ... ok
  test_preserves_hand_curated_entries_untouched ... ok
  test_regen_replaces_the_previous_adr_derived_subset ... ok
  test_a_doubled_keyword_is_a_problem ... ok
  test_a_missing_slug_is_a_problem ... ok
  test_a_must_not_keyword_buckets_to_must ... ok
  ```
- Result: PASS

### 12. WO-0053: `python3 factory.py standards-index update` works; `factory_init.MIRRORS` gains the `standards_index.py` entry; the manifest is regenerated in the same change; detector E green (PRD-0004 §Success criteria)

- Check:
  - Ran the router verb in the scratch copy.
  - Read the MIRRORS entry, and compared the payload copy with the root module.
  - Read what the #517 squash commit carries.
  - Ran the verb-table test.
- Evidence:
  ```
  $ python3 factory.py standards-index update
  standards-index: 0 problem(s)
  $ sed -n 231p factory_init.py
      ("standards_index.py", "tools/factory/standards_index.py", identity),
  $ cmp factory/templates/tools/factory/standards_index.py standards_index.py && echo ...
  payload copy identical to root module
  $ git show 69ecd19 --stat -- factory/manifest.json factory_init.py factory.py ...
   factory.py                                         |   1 +
   factory/manifest.json                              |   3 +-
   factory/templates/tools/factory/standards_index.py | 299 +++++++++++++++++++++
   factory_init.py                                    |   7 +-
  test_every_cli_bearing_root_module_has_exactly_one_verb ... ok
  ```
- Result: PASS. "Same change" here means #517, where the wiring and the regenerated manifest land together and detector E is green. At the row's own commit, detector E was red. That is counted under criterion 8, not twice.

### 13. WO-0054 / WO-0055: an absent index is not a K problem; a run with no `defect.md` is out of M's scope; M generalizes H's section engine; the `DETECTORS` table and roster docstring agree on K and M (PRD-0004 §Success criteria)

- Check: ran K with the index removed (scratch copy). Then grepped M's engine, the roster, the table and the checker tuple, and ran the scope unit tests.
- Evidence:
  ```
  (e) docs/standards.json absent:
  []
  $ grep -n "body = _skip_frontmatter(lines)\|_walk_sections(lines, body)\|^def verification_sections\|^def capture_sections" gates.py
  1138:def verification_sections(text):
  1170:    body = _skip_frontmatter(lines)
  1174:    for kind, lineno, payload in _walk_sections(lines, body):
  1561:def capture_sections(text):
  1576:    body = _skip_frontmatter(lines)
  1579:    for kind, lineno, payload in _walk_sections(lines, body):
  $ grep -n '^  K STANDARDS-DRIFT\|^  M CAPTURE-COMPLETENESS\|"K": (\|"M": (' gates.py
  45:  K STANDARDS-DRIFT — docs/standards.json's ADR-derived entries match a
  49:  M CAPTURE-COMPLETENESS — every docs/fixes/<slug>/defect.md that exists
  1679:    "K": ("STANDARDS-DRIFT", "gates.py", "offline"),
  1681:    "M": ("CAPTURE-COMPLETENESS", "gates.py", "offline"),
  1689:            check_staleness, check_standards_drift, check_capture_completeness,
  test_an_absent_index_is_silent ... ok
  test_no_defect_md_in_a_run_is_out_of_scope ... ok
  ```
- Result: PASS

### 14. WO-0055: `python3 gates.py --selftest` covers a fixture missing each required section (PRD-0004 §Success criteria)

- Check: read the selftest's M fixture and assertions, compared them with the unit tests, and checked whether the unit tests ship to stamped repos.
- Evidence:
  ```
  $ sed -n 1892,1897p gates.py        # the selftest's one M fixture (body)
          "## Defect (or Condition)\n\n<What is broken — observed vs"
          " expected behavior.>\n\n"
          "## Reproduction / Evidence\n\nRun `make check`; it fails with"
          " a traceback.\n\n"
          "## Ruled out\n\n- <Dead ends already investigated and why"
          " they're not it — or \"none yet\".>\n",
  $ sed -n 2219,2228p gates.py
          expect("M", check_capture_completeness(root),
                 "missing required section 'Root-cause hypothesis'",
                 "missing required section 'Blast radius'",
                 "required section 'Defect (or Condition)' is present but"
                 " placeholder-only",
                 "required section 'Ruled out' is present but"
                 " placeholder-only")
          if any("Reproduction / Evidence" in p
                 for p in check_capture_completeness(root)):
              failures.append("M: Reproduction / Evidence should be clean,"
  $ grep -c '"templates/tests/' factory/manifest.json
  0
  $ grep -n "selftest" factory/templates/Makefile
  38:	python3 tools/factory/gates.py --selftest
  ```
- Result: FAIL (minor).
  - The selftest plants two sections missing and two placeholder-only. It asserts `Reproduction / Evidence` clean, and no selftest fixture has that section missing or placeholder.
  - The unit tests do cover it (`test_a_missing_section_is_flagged`). But `tests/` does not ship to stamped repos, where the Makefile runs only `gates.py --selftest`. So in a stamped repo, nothing would catch M losing that section.

### 15. WO-0056: first ADR back-fill: `## Normative statements` bullets with stable slugs, exactly one RFC-2119 keyword each, all `advisory`, through the standard `docs/adr/**` merge gate (PRD-0004 §Solution)

- Check: grepped the sections in the two back-filled ADRs. The regen parses them with 0 problems (criterion 2), and every committed status is `advisory`.
- Evidence:
  ```
  docs/adr/0004-artifacts-are-the-state.md:13:## Normative statements
  docs/adr/0004-artifacts-are-the-state.md-15-- **adr0004-typed-ids-in-frontmatter** (pipeline): A run artifact's typed identifier MUST live in that artifact's own frontmatter, never in a separate manifest or parallel tracking tree.
  docs/adr/0032-factory-dispatch-plane.md:64:## Normative statements
  docs/adr/0032-factory-dispatch-plane.md-66-- **adr0032-one-way-mirror** (factory): A work-order issue MUST be created only after its breakdown row exists.
  $ python3 -c "... {e['status'] for e in json.load(open('docs/standards.json'))}"
  {'advisory'}
  ```
- Result: PASS. The third candidate (stdlib-only) went to the CLAUDE.md half instead, as recorded in the breakdown's Milestone C note. "Human-reviewed" rests on the owner-account merge of #517 (criterion 10); see Not verified.

### 16. WO-0057: first CLAUDE.md-sourced entries: `source: CLAUDE.md#<anchor>`, `status: advisory`, anchor resolvable by a reader of CLAUDE.md (PRD-0004 §Solution)

- Check: matched each entry's anchor to the CLAUDE.md passage it names.
- Evidence:
  ```
  eval-honesty keys_ok=True MUST advisory eval CLAUDE.md#eval-honesty
  stdlib-only keys_ok=True MUST advisory factory CLAUDE.md#stdlib-only
  $ grep -n "Eval honesty\|Stdlib only" CLAUDE.md
  39:- **Stdlib only.** Every script is standalone Python 3 standard library.
  79:## Eval honesty (non-negotiable)
  ```
- Result: PASS. This is against the row's own bar, a human-resolvable anchor. That nothing verifies these entries is recorded under criterion 9.

### 17. WO-0058: regeneration through `factory.py` produces both back-fills; K and the selftest green (PRD-0004 §Success criteria)

- Check: see criterion 2. `factory.py standards-index update` on a copy of HEAD reproduces the committed four-entry file byte for byte: two ADR-derived entries and two `CLAUDE.md#` entries.
- Evidence:
  ```
  $ python3 factory.py standards-index update
  standards-index: 0 problem(s)
  c155e7d5bc26221f8bbe9035968b403455f584b7b1fd32d49a8cfce585699711  docs/standards.json
  identical to committed
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

### 18. WO-0059 / WO-0061: `skills/review/TEMPLATE.md` gains a slug-citation line per finding; `skills/architect/TEMPLATE.md`'s "Decisions & alternatives" guidance gains the citation clause (PRD-0004 §Success criteria)

- Check: grepped both templates.
- Evidence:
  ```
  skills/review/TEMPLATE.md:18:- Standard: <matching docs/standards.json slug this finding cites, or "none">
  skills/architect/TEMPLATE.md:44:- **<Decision>** over <alternative> — <why it lost, one line; cite a matching `docs/standards.json` slug alongside any ADR number when the decision bears on one>
  ```
- Result: PASS

### 19. WO-0060: the reviewer-charter edit leaves ADR-0036's merge-decision conditions unchanged (PRD-0004 §Success criteria)

- Check: listed every added and removed line in #517's diff of the reviewer charter.
- Evidence:
  ```
  $ git show 69ecd19 --format= -- factory/charters/reviewer/CHARTER.md | grep -E "^[+-][^+-]"
  -7. Filter findings by confidence; report only what clears the bar,
  +7. Load `docs/standards.json` if present, filtered to statements whose
  +   ... A finding that matches one cites its `slug`.
  +8. Filter findings by confidence; report only what clears the bar,
  -8. Post the verdict; on pass apply `gate:merge` and run the merge
  +9. Post the verdict; on pass apply `gate:merge` and run the merge
  +  open: an unresolved finding against an `enforced` statement blocks
  +  the verdict the same way an open security finding does, until
  +  resolved or explicitly escalated.
  $ git log --format="%h %s" 69ecd19..HEAD -- factory/charters/reviewer/CHARTER.md
  (none)
  ```
- Result: PASS. The only removals are two renumbered steps. The `## Merge decision (ADR-0036)` section is untouched.

### 20. WO-0064: three real advisory→enforced promotions with prior evidence (PRD-0004 §Out of scope, §Open questions)

- Check: read the owner's deferral record in the breakdown, the backlog seed, issue #518's state, #569's merge record, and the index's statuses.
- Evidence:
  ```
  $ grep -n "2026-09-28: \*\*WO-0064" -A 3 docs/features/codex-style-standards-enforcement/breakdown.md
  326:- 2026-09-28: **WO-0064 (PRD-0004 §Out of scope, §Open questions)
  327-  resolved by option (b), deferral.** The owner chose to defer the "3
  328-  real advisory→enforced promotions" bar to a later run. At decision
  329-  time `docs/standards.json` held 4 statements, all `status: advisory`,
  $ grep -n "PRD-0004" docs/backlog.md
  75:- Revisit PRD-0004's deferred promotion bar (WO-0064, PRD-0004 §Open questions; owner deferred it 2026-09-28, issue #518): ...
  $ gh issue view 518 --json state,stateReason,closedAt
  #518 CLOSED COMPLETED closedAt=2026-09-28T17:53:29Z labels=ready-for-human,type:chore
  $ gh pr view 569 --json mergedBy,mergedAt
  #569 MERGED mergedBy=mattbutlerengineering at=2026-09-28T17:53:28Z
  {'advisory'}
  ```
- Result: DEFERRED. The owner deferred this on 2026-09-28 (#569; breakdown Notes; `docs/backlog.md` line 75). No statement was promoted and no prior evidence was claimed. Issue #448's acceptance #4 remains unmet by this run.

## Failures

- **Criterion 9: the CLAUDE.md-sourced entries are unverified.** This routes to Implement. The fix is a K check that each `CLAUDE.md#` anchor and its statement still resolve against CLAUDE.md. If a human instead accepts the WO-0057 relaxation, the route is back to PRD-0004 to reword the criterion.
- **Criterion 8: two work items' commits left the battery red.** Nothing needs re-implementing; HEAD and main are green. A human rules whether per-merge greenness satisfies "through every work item". Separately, the breakdown's WO-0063 close-out note overstates, and should be corrected by whoever owns that artifact (Verify edits nothing but this file).
- **Criterion 14: the selftest's M fixture never fails `Reproduction / Evidence`.** This routes to Implement: add that section missing or placeholder to the selftest fixture, then re-run `factory_init.py update-manifest`, because `gates.py` is mirrored.

## Findings outside the criteria (for Review)

- **The skills' index path resolves to the plugin's copy.**
  - `skills/review/SKILL.md` and `skills/architect/SKILL.md` read `../../docs/standards.json`. That is the same skill-relative prefix they use for the plugin's own `../../docs/pipeline-protocol.md`, and the installed plugin cache does ship `docs/pipeline-protocol.md`.
  - In any repo other than this one, that path would resolve to the plugin's bundled index (this repo's four statements), not the target repo's.
  - The charters use repo-relative `docs/standards.json`.
  - This is a static reading; it was not exercised in another repo.
- **A regen silently demotes a promoted ADR-derived entry.**
  - In a scratch copy, marking `adr0032-one-way-mirror` and `eval-honesty` `enforced` and running `standards_index.py update` gave: `adr0032-one-way-mirror advisory`, `eval-honesty enforced`.
  - ADR-0073's Consequences record this as a known open edge, left to whoever exercises WO-0064. That row is now deferred, so the edge stays open. It will bite the first real promotion.
- **The installed plugin is stale** (Ship concern). The local cache `idea-to-prod/0.2.0` has no "Load applicable standards" step, and `plugin.json` is still `0.2.0` after `skills/` changed in #517.

## Not verified

- **Live behavior of the four prose changes: NOT RUN.** This covers the review and architect skills and both charters actually loading, filtering, citing and blocking. No `review.md` or `architecture.md` in this repo is dated after #517 merged (0 found), so no real run has exercised them. Exercising one needs a live model run, which spends money and needs a human to authorize. Criteria 5, 6 and 18 pass on their text only.
- **"Human-reviewed" for the ADR back-fill (criterion 15).** The record shows #517 merged by the owner account under CODEOWNERS. It cannot show whether a human read the bullets or a delegated session merged, the same limit `first-live-dispatch/verification.md` records for label timelines.
- **`trigger_eval.py` and `charter_replay.py`: NOT RUN.** Both spend money, and no criterion requires them.
