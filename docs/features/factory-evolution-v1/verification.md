---
stage: verify
run: feature:factory-evolution-v1
date: 2026-09-29
assumptions:
  - "date: 2026-09-29 is the UTC date of this Verify pass (the local clock read 2026-09-28 PDT). It matches the run's other 2026-09-29 entries in autorun-brief.md and breakdown.md's Notes."
  - "PRD-0006 success criteria 1 and 6 are judged on their literal text: an accepted ADR file, or a breakdown row, existing with the stated content. The deferred work their 'serves autonomy-per-human-hour' clauses motivate (the merge queue, two routine triggers) is judged separately as the WO-0065, WO-0069 and WO-0071 acceptance criteria, each FAIL below. If a 'serves' clause is read as part of the pass condition, criteria 1 and 6 also FAIL. Review should confirm the reading."
  - "PRD-0006 criterion 8 reads a 'WO-#### GitHub issue' as ADR-0032's mirrored work-order issue, which carries a wo:* lifecycle label. The five closed type:chore issues whose titles name this run's ids (#524, #526, #533, #562, #582) are PR tracking issues. The brief's Tracker default names them as this repo's detector-B convention, so they are not counted. All five were opened after the rows existed."
  - "WO-0070's trigger half is judged on the orchestrating session's capture of the live trigger (trigger-evidence.txt in the orchestrator's scratchpad, quoted verbatim below). This Verify pass may not list, create or run triggers, so the capture is labelled as the orchestrator's evidence, not as this pass's observation."
  - "WO-0072's acceptance criterion is read as requiring the PRD-0006 re-walk and the epic #439 Destination re-check to be performed, not to come out clean. The re-check's own outcome is recorded as a separate criterion (FAIL)."
  - "The skill routes failures back to Implement, but no Implement action can clear any of the four failures here. Each waits on an owner decision that is already seeded in docs/backlog.md, so they are routed to the owner. Orientation advances to Review once this file exists; whether to hold the run there is the orchestrator's or owner's call."
---

# Verification: Factory evolution backlog seed

## Summary

This pass walked 18 criteria: PRD-0006's nine success criteria, the
acceptance criteria of all eight breakdown rows (WO-0065 to WO-0072,
none of which a PRD criterion already covers), and epic #439's map
Destination, which WO-0072's row assigns to this artifact.
**14 PASS, 4 FAIL.** All nine PRD-0006 success criteria pass on their
literal text, and the battery is green on a fresh run. The four
failures are the three rows the owner deferred (WO-0065, the merge
queue; WO-0069 and WO-0071, the retro/reflect and doc-gardener
triggers) and the epic Destination, which those deferrals leave unmet.
None of the four is an implementation defect. Each waits on an owner
decision that is already on the record.

| # | Criterion | Result | Reason |
|---|-----------|--------|--------|
| 1 | PRD-0006 SC1: ADR-0070 accepted, composes with ADR-0036, honest cascade cost | PASS | The ADR's Status line reads accepted. It names the 40+-open-PR cascade cost and composes with ADR-0036 without amending it |
| 2 | PRD-0006 SC2: ADR-0071 accepted, marker + clarify pass + CI rule | PASS | All three are in its Decision section |
| 3 | PRD-0006 SC3: ADR-0072 accepted, reverse check + waiver grammar | PASS | Both are in its Decision section |
| 4 | PRD-0006 SC4: ADR index rows match Status lines | PASS | All three rows and all three files say accepted, and detector D is clean |
| 5 | PRD-0006 SC5: precision/recall/F1 breakdown row | PASS | The WO-0068 row exists and cites PRD-0006 §Success criteria |
| 6 | PRD-0006 SC6: three routine breakdown rows | PASS | WO-0069, WO-0070 and WO-0071 exist, each scoped to a protocol doc plus a trigger |
| 7 | PRD-0006 SC7: every row cites a PRD-0006 section and traces to ADR-0069 | PASS | All 8 rows cite §Success criteria; A, C and O are clean; the five serves clauses cover all seven items |
| 8 | PRD-0006 SC8: no work-order issue created | PASS | None of the 38 wo:*-labelled issues names WO-0065 to WO-0072 |
| 9 | PRD-0006 SC9: battery green | PASS | Green on a fresh run, and the check job succeeded on all six merged PRs |
| 10 | WO-0065 acceptance: merge queue enabled | FAIL | Deferred by owner decision on 2026-09-28. Branch protection returns HTTP 403 and there are no merge_group triggers |
| 11 | WO-0066 acceptance: markers, clarify pass, detector N | PASS | Templates, PRD skill step, detector N and the selftest are all present, and a fresh probe fires N correctly |
| 12 | WO-0067 acceptance: detector O with waiver | PASS | The selftest covers both cases, and a fresh probe agrees |
| 13 | WO-0068 acceptance: precision/recall/F1 function | PASS | 13 metric tests OK, evals/results untouched, and the backlog seed carries the number |
| 14 | WO-0069 acceptance: retro/reflect doc + trigger | FAIL | The doc landed. The trigger was deferred by owner decision on 2026-09-29 |
| 15 | WO-0070 acceptance: queue-groomer doc + trigger | PASS | The doc landed. The trigger exists per the orchestrator's capture; this pass did not observe it, and it has not run yet |
| 16 | WO-0071 acceptance: doc-gardener doc + trigger | FAIL | The doc landed. The trigger was deferred by owner decision on 2026-09-29 |
| 17 | WO-0072 acceptance: battery, re-walk, re-check | PASS | The battery is green, and this artifact performs the re-walk and the re-check |
| 18 | Epic #439 map Destination | FAIL | Three of the seven items still wait on an owner decision before building can start |

## Criteria & evidence

### 1. PRD-0006 SC1: ADR-0070 exists, accepted, composes with ADR-0036, honest cascade cost

- Check: read ADR-0070's Status line and grep for its ADR-0036
  composition and its cascade-cost accounting. This criterion is judged
  on its literal text, which asks for the ADR. The merge queue the ADR
  adopts is WO-0065's acceptance criterion, and that one FAILs (row 10).
- Evidence:
  ```
  $ grep -nE "^- Status:|composes with it|40\+-open-PR|cascade-cost tradeoff" docs/adr/0070-github-merge-queue-composes-with-agent-merge.md
  3:- Status: accepted
  34:- Honest accounting, not glossed over: at this repo's actual 40+-open-PR
  68:- The cascade-cost tradeoff at current backlog volumes is accepted
  88:- ADR-0036 is not amended: this ADR composes with it by dividing
  ```
- Result: PASS. The ADR exists, is accepted, composes with ADR-0036,
  and accounts for the cascade cost. The merge queue itself is not
  enabled (see row 10).

### 2. PRD-0006 SC2: ADR-0071 exists, accepted, defines marker, bounded clarify pass, CI enforcement

- Check: read ADR-0071's Status line and grep its Decision section for
  the three required parts.
- Evidence:
  ```
  $ grep -nE "^- Status:|^- \*\*Marker convention|^- \*\*Bounded clarify pass|usable ad hoc against|questions per pass|^- \*\*CI enforcement" docs/adr/0071-needs-clarification-markers.md
  3:- Status: accepted
  46:- **Marker convention.** `prd.md` and `architecture.md` drafts (the two
  56:- **Bounded clarify pass.** A clarify step, added to the PRD skill (and
  57:  usable ad hoc against `architecture.md`), resolves markers: at most 5
  58:  questions per pass, prioritized by a taxonomy derived from the
  68:- **CI enforcement, not just prompt enforcement.** A new `gates.py`
  ```
- Result: PASS. The marker convention, the 5-question clarify pass and
  gates.py enforcement are all decided in the accepted ADR.

### 3. PRD-0006 SC3: ADR-0072 exists, accepted, defines reverse check and waiver grammar

- Check: read ADR-0072's Status line and grep its Decision section.
- Evidence:
  ```
  $ grep -nE "^- Status:|check the \*\*reverse\*\* direction|^- \*\*Waiver grammar|coverage-waiver: <reason>" docs/adr/0072-prd-coverage-check.md
  3:- Status: accepted
  41:  check the **reverse** direction: every `§` section (or, where a PRD
  46:- **Waiver grammar**, matching the existing "declared, never assumed"
  49:  `<!-- coverage-waiver: <reason> -->` directly under the section
  ```
- Result: PASS. The ADR is accepted and defines both the reverse-direction
  check and the declared waiver.

### 4. PRD-0006 SC4: docs/adr/README.md indexes all three ADRs, status matching

- Check: print the index rows for 0070 to 0072 (title and status columns
  only, so this file does not carry their relative links), print each
  ADR's Status line, and run detector D through gates.py.
- Evidence:
  ```
  $ grep -nE '^\| \[007[0-2]\]' docs/adr/README.md | cut -d'|' -f1,3,4
  93:| Adopt GitHub's native merge queue, composing with agent-merge | accepted
  94:| Inline [NEEDS CLARIFICATION] markers, CI-enforced | accepted
  95:| Bidirectional PRD-requirement <-> work-item coverage check | accepted
  $ grep -n "^- Status:" docs/adr/0070-*.md docs/adr/0071-*.md docs/adr/0072-*.md
  docs/adr/0072-prd-coverage-check.md:3:- Status: accepted
  docs/adr/0070-github-merge-queue-composes-with-agent-merge.md:3:- Status: accepted
  docs/adr/0071-needs-clarification-markers.md:3:- Status: accepted
  $ python3 gates.py
  gates: 0 problem(s)
  ```
- Result: PASS. Each row's status matches its ADR file, and detector D
  reports no problems.

### 5. PRD-0006 SC5: a breakdown row exists for per-skill precision/recall/F1

- Check: grep breakdown.md for the row.
- Evidence:
  ```
  $ grep -nE "^- \[x\] \*\*WO-00(68|69|70|71)\*\*" docs/features/factory-evolution-v1/breakdown.md
  34:- [x] **WO-0068** derive per-skill precision/recall/F1 from `trigger_eval.py`'s existing confusion matrix — size:S, blocked by: — (PRD-0006 §Success criteria)
  ```
- Result: PASS. The row exists. Its body carries no new ADR, as the
  criterion requires.

### 6. PRD-0006 SC6: a breakdown row exists for each of the three roster routines

- Check: same grep, for the three routine rows. The criterion requires
  each row to be scoped to "design and land this routine's protocol doc
  + ADR-0044-style trigger". Whether those triggers exist is each row's
  own acceptance criterion (rows 14 to 16).
- Evidence:
  ```
  $ grep -nE "^- \[x\] \*\*WO-00(68|69|70|71)\*\*" docs/features/factory-evolution-v1/breakdown.md
  39:- [x] **WO-0069** design and land the weekly retro/reflect-deepening routine's protocol doc + ADR-0044-style trigger — size:M, blocked by: — (PRD-0006 §Success criteria)
  41:- [x] **WO-0070** design and land the queue-groomer routine's protocol doc + ADR-0044-style trigger — size:M, blocked by: — (PRD-0006 §Success criteria)
  43:- [x] **WO-0071** design and land the doc-gardener routine's protocol doc + ADR-0044-style trigger — size:M, blocked by: — (PRD-0006 §Success criteria)
  ```
- Result: PASS. All three rows exist and are scoped as the criterion
  requires. Two of their triggers are deferred (rows 14 and 16).

### 7. PRD-0006 SC7: every row cites a resolving PRD-0006 section and traces to ADR-0069

- Check: list each row's citation. Count the "serves
  autonomy-per-human-hour" clauses, which tie the item criteria to
  ADR-0069's metric, and find ADR-0069 in the PRD. Then run gates.py,
  where detector A covers row citations, C covers token resolution and
  O covers reverse coverage.
- Evidence:
  ```
  $ grep -nE "^- \[[ x]\] \*\*WO-" docs/features/factory-evolution-v1/breakdown.md | sed -E 's/^([0-9]+):- (\[[ x]\]) \*\*(WO-[0-9]+)\*\*.*(\(PRD-[0-9]+ §[^)]*\))$/\1: \2 \3 \4/'
  25: [x] WO-0065 (PRD-0006 §Success criteria)
  27: [x] WO-0066 (PRD-0006 §Success criteria)
  29: [x] WO-0067 (PRD-0006 §Success criteria)
  34: [x] WO-0068 (PRD-0006 §Success criteria)
  39: [x] WO-0069 (PRD-0006 §Success criteria)
  41: [x] WO-0070 (PRD-0006 §Success criteria)
  43: [x] WO-0071 (PRD-0006 §Success criteria)
  48: [x] WO-0072 (PRD-0006 §Success criteria)
  $ grep -n "serves" docs/features/factory-evolution-v1/prd.md
  45:why it serves autonomy-per-human-hour.
  100:      40+-open-PR backlog volumes — serves autonomy-per-human-hour by
  105:      clarify pass, and the gate-1 CI enforcement rule — serves
  111:      and its declared-waiver grammar — serves autonomy-per-human-hour
  120:      verdict) — serves autonomy-per-human-hour by turning an already-
  129:      bound for this ticket) — serves autonomy-per-human-hour by
  $ grep -n "ADR-0069" docs/features/factory-evolution-v1/prd.md
  25:gates, now pinned by ADR-0069 as accepted work orders per gate-wait
  78:   this PRD, ADR-0069's baseline metric, so I can tell at a glance why
  135:      to ADR-0069's baseline metric — no row exists that isn't
  171:- **Computing ADR-0069's actual baseline number.** ADR-0069 itself
  $ python3 gates.py
  gates: 0 problem(s)
  ```
- Result: PASS. All eight rows cite PRD-0006 §Success criteria. The five
  item criteria (lines 100 to 129, one of which covers all three
  routines) each carry a serves clause, and the PRD pins that metric to
  ADR-0069 at line 25.

### 8. PRD-0006 SC8: no WO-#### GitHub issue is created by this run

- Check: an ADR-0032 work-order issue carries a `wo:*` lifecycle label.
  This pass scanned every issue under each of the nine `wo:*` labels,
  open or closed, for WO-0065 to WO-0072 in the title or body. It also
  looked up the issues whose titles name these ids (see `assumptions:`).
  The first scan attempt hit a network timeout, so the scan was rerun one
  label at a time. Its output is below. `$SP` is this pass's scratchpad
  directory.
- Evidence:
  ```
  $ : > $SP/wo-label-scan.txt; for l in wo:draft wo:prd-approved wo:blueprint-approved wo:ready-for-agent wo:in-progress wo:needs-review wo:merged wo:failed wo:blocked; do n=$(gh issue list --state all --label "$l" --limit 300 --json number --jq 'length' 2>&1); hits=$(gh issue list --state all --label "$l" --limit 300 --json number,title,body --jq '.[] | select((.title + " " + (.body // "")) | test("WO-00(6[5-9]|7[0-2])\\b")) | "#\(.number) \(.title)"' 2>&1); echo "$l: $n issue(s) scanned; hits: ${hits:-none}" >> $SP/wo-label-scan.txt; done; cat $SP/wo-label-scan.txt
  wo:draft: 0 issue(s) scanned; hits: none
  wo:prd-approved: 0 issue(s) scanned; hits: none
  wo:blueprint-approved: 0 issue(s) scanned; hits: none
  wo:ready-for-agent: 0 issue(s) scanned; hits: none
  wo:in-progress: 0 issue(s) scanned; hits: none
  wo:needs-review: 0 issue(s) scanned; hits: none
  wo:merged: 38 issue(s) scanned; hits: none
  wo:failed: 0 issue(s) scanned; hits: none
  wo:blocked: 0 issue(s) scanned; hits: none
  $ for n in 524 526 533 562 582; do gh issue view $n --json number,state,createdAt,labels,title --jq '"#\(.number) \(.state) \(.createdAt) [\(.labels|map(.name)|join(","))] \(.title)"' 2>&1; done
  #524 CLOSED 2026-09-23T17:57:45Z [type:chore] Implement factory-evolution-v1 WO-0068: per-skill precision/recall/F1
  #526 CLOSED 2026-09-23T17:59:06Z [type:chore] Implement factory-evolution-v1 WO-0066 + WO-0067 (ADR-0071, ADR-0072)
  #533 CLOSED 2026-09-24T03:50:27Z [type:chore] Implement factory-evolution-v1 WO-0069 + WO-0070 + WO-0071: roster routine protocol docs
  #562 CLOSED 2026-09-25T18:55:51Z [type:chore] Record WO-0065's hosting blocker in the factory-evolution-v1 breakdown
  #582 CLOSED 2026-09-28T20:37:49Z [type:chore] Defer WO-0065 (merge queue) until the repo moves to an organization
  ```
- Result: PASS. No `wo:*`-labelled issue names any of this run's ids.
  The five issues that do name them are `type:chore` PR tracking issues
  with no lifecycle label. All five were opened after PR #515 merged the
  rows on 2026-09-22, so even the looser reading finds no issue ahead of
  its row.

### 9. PRD-0006 SC9: the battery stays green through every artifact this run writes

- Check: run the battery fresh from this worktree, with every
  Implement change present, including the uncommitted 2026-09-29
  changes. Then read the `check` job (`make check`, the same battery) on
  the six merged PRs that carried this run's artifacts.
- Evidence:
  ```
  $ python3 -m unittest discover tests
  ----------------------------------------------------------------------
  Ran 1793 tests in 20.343s

  OK
  unittest exit=0
  $ python3 lint.py
  lint: 0 problem(s) across 25 skills
  lint exit=0
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  gates chain exit=0
  $ for n in 515 525 527 532 563 583; do gh pr view $n --json number,mergedAt,statusCheckRollup --jq '"#\(.number) merged \(.mergedAt) check: " + ([.statusCheckRollup[] | select(.name=="check") | .conclusion] | join(","))'; done
  #515 merged 2026-09-22T03:26:10Z check: SKIPPED,SKIPPED,SUCCESS,SUCCESS,SUCCESS,SUCCESS
  #525 merged 2026-09-24T03:46:54Z check: SKIPPED,SUCCESS,SUCCESS
  #527 merged 2026-09-24T03:49:18Z check: SKIPPED,SUCCESS,SUCCESS
  #532 merged 2026-09-24T03:54:22Z check: SKIPPED,SUCCESS,SUCCESS
  #563 merged 2026-09-25T18:56:47Z check: SKIPPED,SUCCESS,SUCCESS
  #583 merged 2026-09-28T20:39:01Z check: SKIPPED,SUCCESS,SUCCESS
  ```
  (The unittest lines quoted are the run's summary lines. Its full output
  also carries stdout that the tests emit. The `exit=` lines are this
  pass's own echo of each command's exit code.)
- Result: PASS. The battery is green on a fresh run over the whole
  current tree, and no `check` run on this run's six merged PRs failed.
  The uncommitted 2026-09-29 changes have no PR yet, so the fresh local
  run is their only evidence.

### 10. WO-0065 acceptance: GitHub merge queue enabled, merge_group triggers added

- Check: look for any `merge_group` trigger in the workflows and the
  template payload, and read `main`'s branch protection (a read-only
  GET). The row is checked in breakdown.md as deferred by owner decision.
  That records a decision; it does not mean the work landed.
- Evidence:
  ```
  $ grep -rln "merge_group" .github/workflows factory/templates 2>&1; echo "grep exit=$?"; ls .github/workflows | wc -l; gh api repos/mattbutlerengineering/skills/branches/main/protection 2>&1 | head -3
  grep exit=1
         8
  {"message":"Upgrade to GitHub Pro or make this repository public to enable this feature.","documentation_url":"https://docs.github.com/rest/branches/branch-protection#get-branch-protection","status":"403"}gh: Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403)
  $ grep -nE "^- Adopt GitHub's merge queue once hosting" docs/backlog.md
  76:- Adopt GitHub's merge queue once hosting allows it (WO-0065, PRD-0006 §Success criteria; ADR-0070; owner deferred it 2026-09-28): the repo is user-owned, private, and on the free plan, so branch protection, rulesets, and the merge queue all return HTTP 403 or are unavailable, and no status check is enforced on `main` today. What unblocks it: the repo moves to an organization (public, or private on Enterprise Cloud). Then add `merge_group` to the mirrored required-check workflows (update-manifest in the same commit) and enable the queue on `main`'s protection rule, resolving ADR-0070's cascade-cost and review-composition questions in that run's verification (from: feature:factory-evolution-v1)
  ```
- Result: FAIL, deferred by owner decision (2026-09-28). The merge queue
  is not enabled, none of the 8 workflows has a `merge_group` trigger,
  and branch protection is unavailable on this plan (HTTP 403).
  ADR-0070's cascade-cost and review-composition questions, which this
  row wanted resolved and recorded here, remain open. The revisit is
  seeded at docs/backlog.md line 76.

### 11. WO-0066 acceptance: marker syntax in both templates, bounded clarify step, detector N with selftest

- Check: grep both templates and the PRD skill. Probe detector N
  against fresh fixture trees (a probe script in this pass's scratchpad,
  independent of gates.py's own selftest fixtures) with a live marker
  and with a marker quoted in a code span. Then run the selftest.
  `$SP` is this pass's scratchpad directory.
- Evidence:
  ```
  $ grep -n "NEEDS CLARIFICATION" skills/prd/TEMPLATE.md skills/architect/TEMPLATE.md
  skills/architect/TEMPLATE.md:11:     `[NEEDS CLARIFICATION: <question>]`. The clarify pass resolves every
  skills/prd/TEMPLATE.md:12:     `[NEEDS CLARIFICATION: <question>]`. The clarify pass resolves every
  $ grep -nE "Clarify \(bounded\)|at most \*\*5\*\*|### Clarifications / Session|detector N fails" skills/prd/SKILL.md
  46:5. **Clarify (bounded).** If `prd.md` carries markers, run one clarify
  48:   - Ask at most **5** questions per pass, one at a time, prioritized by
  52:     `### Clarifications / Session YYYY-MM-DD` heading in `prd.md`, and
  57:     `gates.py` detector N fails any `prd.md` or `architecture.md` that
  $ python3 $SP/probe_n_o.py "$PWD"
  N live marker in prd.md: ['N: docs/features/probe/prd.md:3 unresolved [NEEDS CLARIFICATION] marker']
  N marker quoted in a code span: []
  $ grep -nE "# N: a live marker|expect\(\"N\"" gates.py
  2352:    # N: a live marker in each gated artifact fires; the quoted one in a
  2358:        expect("N", problems, "demo/prd.md:4 unresolved",
  $ python3 gates.py --selftest
  selftest: ok
  ```
- Result: PASS. Both templates document the marker, the PRD skill has
  the bounded clarify step, detector N fires on a live marker and stays
  silent on a quoted one, and the selftest covers it.

### 12. WO-0067 acceptance: reverse coverage detector with declared waiver, selftest both cases

- Check: probe detector O against fresh fixture trees, with an uncited
  section unwaived and then waived. Grep the selftest for both cases,
  then run gates.py and the selftest.
- Evidence:
  ```
  $ python3 $SP/probe_n_o.py "$PWD"
  O uncited, unwaived §Actors: ['O: docs/features/probe/prd.md:12 PRD-0001 §Actors is cited by no breakdown row and carries no coverage waiver']
  O uncited, waived §Actors: []
  $ grep -nE "# O: an uncited|expect\(\"O\"|expect_clean\(\"O waived\"" gates.py
  2363:    # O: an uncited, unwaived PRD section fires; the same section with a
  2368:        expect("O", check_prd_coverage(root),
  2373:        expect_clean("O waived", check_prd_coverage(root))
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS. Detector O is a sibling letter, not a widening of A, as
  breakdown.md's 2026-09-23 note records. It fails an uncited, unwaived
  section and passes a declared waiver, and the selftest covers both
  cases.

### 13. WO-0068 acceptance: pure precision/recall/F1 function, unit tests, evals/results untouched, backlog seed answered

- Check: run the metric unit tests. Confirm that the landing commit
  (#525) did not touch `evals/results/`. Read the backlog seed the row
  says the function answers. `trigger_eval.py` itself was not run (see
  Not verified).
- Evidence:
  ```
  $ python3 -m unittest tests.test_trigger_eval_metrics -v
  test_prints_the_report_for_a_recorded_file (tests.test_trigger_eval_metrics.TestMetricsCli.test_prints_the_report_for_a_recorded_file) ... ok
  test_unreadable_file_exits_nonzero_with_an_error (tests.test_trigger_eval_metrics.TestMetricsCli.test_unreadable_file_exits_nonzero_with_an_error) ... ok
  test_kind_filter_recomputes_confusion_from_that_kind_only (tests.test_trigger_eval_metrics.TestMetricsReport.test_kind_filter_recomputes_confusion_from_that_kind_only) ... ok
  test_unknown_kind_reports_no_cases (tests.test_trigger_eval_metrics.TestMetricsReport.test_unknown_kind_reports_no_cases) ... ok
  test_whole_record_micro_recall (tests.test_trigger_eval_metrics.TestMetricsReport.test_whole_record_micro_recall) ... ok
  test_counts_read_rows_as_expected_and_columns_as_fired (tests.test_trigger_eval_metrics.TestSkillMetrics.test_counts_read_rows_as_expected_and_columns_as_fired) ... ok
  test_empty_confusion_gives_no_skills (tests.test_trigger_eval_metrics.TestSkillMetrics.test_empty_confusion_gives_no_skills) ... ok
  test_input_is_not_mutated (tests.test_trigger_eval_metrics.TestSkillMetrics.test_input_is_not_mutated) ... ok
  test_never_expected_skill_has_undefined_recall (tests.test_trigger_eval_metrics.TestSkillMetrics.test_never_expected_skill_has_undefined_recall) ... ok
  test_never_fired_skill_has_undefined_precision (tests.test_trigger_eval_metrics.TestSkillMetrics.test_never_fired_skill_has_undefined_precision) ... ok
  test_none_is_the_negative_class_not_a_skill (tests.test_trigger_eval_metrics.TestSkillMetrics.test_none_is_the_negative_class_not_a_skill) ... ok
  test_precision_recall_f1 (tests.test_trigger_eval_metrics.TestSkillMetrics.test_precision_recall_f1) ... ok
  test_zero_precision_and_recall_gives_zero_f1 (tests.test_trigger_eval_metrics.TestSkillMetrics.test_zero_precision_and_recall_gives_zero_f1) ... ok

  ----------------------------------------------------------------------
  Ran 13 tests in 0.002s

  OK
  $ git show --stat --format="%h %s" 90432bf
  90432bf feat(trigger-eval): derive per-skill precision/recall/F1 from the confusion matrix (#525)

   docs/backlog.md                                 |   2 +-
   docs/factory/costs.jsonl                        |   1 +
   docs/features/factory-evolution-v1/breakdown.md |   2 +-
   tests/test_trigger_eval_metrics.py              | 160 ++++++++++++++++++++++++
   trigger_eval.py                                 |  94 ++++++++++++++
   5 files changed, 257 insertions(+), 2 deletions(-)
  $ git log --oneline -1 -- evals/results/
  680e142 feat: run the routing eval-set through the omp harness (#88) (#101)
  $ grep -n "under-trigger" docs/backlog.md | head -1
  3:- omp near-miss under-triggering: 8/16 near-miss cases under-trigger on omp vs Claude Code; tracked as near-miss micro recall 18/39 = 0.462 via `python3 trigger_eval.py --metrics evals/results/trigger-omp-2026-07-05.json --kind near-miss` (from: session:2026-07-05)
  ```
- Result: PASS. The function is tested, the commit that landed it
  touched nothing under `evals/results/`, and the backlog seed now
  carries a trackable number and the command that derives it.

### 14. WO-0069 acceptance: retro/reflect protocol doc + weekly Sonnet no-MCP trigger

- Check: list the protocol doc's sections and read its §Trigger. This
  pass cannot list triggers. The trigger's absence is taken from the
  doc's dated line, the brief and breakdown.md's 2026-09-29 note. It was
  not observed.
- Evidence:
  ```
  $ grep -nE "^## " docs/factory/retro-reflect-routine.md
  34:## 1 Preconditions and degrade ladder
  51:## 2 Orient (read-only)
  75:## 3 Consolidate
  89:## 4 Pick exactly one
  104:## 5 Implement
  124:## 6 Report and journal
  152:## 7 Non-negotiables
  172:## 8 Amending this playbook
  179:## Trigger
  $ grep -nE "deferred by owner decision|is not an approval|^\*\*Not yet created" docs/factory/retro-reflect-routine.md
  181:**2026-09-29: deferred by owner decision** while the
  184:is not an approval: nothing authorizes creating this trigger.
  186:**Not yet created.** A scheduled trigger is recurring paid spend, and
  ```
- Result: FAIL, deferred by owner decision (2026-09-29). The protocol
  doc has landed in improvement-routine.md's shape. The weekly trigger
  the row requires does not exist, because the owner chose to pilot the
  queue groomer's trigger first. The revisit is seeded at
  docs/backlog.md line 77.

### 15. WO-0070 acceptance: queue-groomer protocol doc + weekly Sonnet no-MCP cost-ledger-excluded trigger

- Check: list the protocol doc's sections and read its §Trigger. For
  the trigger, quote the orchestrating session's capture of the live
  trigger verbatim. **This Verify pass did not observe the trigger**: it
  may not list, create or run triggers, and the evidence below was
  captured by the orchestrator. The trigger has not run yet. Its first
  run is 2026-09-30 13:17 UTC.
- Evidence (protocol doc, observed by this pass):
  ```
  $ grep -nE "^## " docs/factory/queue-groomer-routine.md
  35:## 1 Preconditions and degrade ladder
  51:## 2 Orient (read-only)
  70:## 3 Survey
  97:## 4 Pick exactly one
  115:## 5 Implement
  133:## 6 Report and journal
  157:## 7 Non-negotiables
  176:## 8 Amending this playbook
  183:## Trigger
  $ sed -n 192,206p docs/factory/queue-groomer-routine.md
  - **Trigger id:** `trig_01W5PgiQb4G2qwMXnNVFtACx`, created 2026-09-29
    04:11 UTC. First run 2026-09-30 13:17 UTC.
  - **Cadence:** weekly — Wednesday 13:17 UTC (`17 13 * * 3`), off the
    daily routine's slot and the other roster routines' days.
  - **Model:** Sonnet (`claude-sonnet-5-5`).
  - **Connectors:** none — no MCP connectors; `gh` and `git` only. The
    create call attaches every account connector by default; they were
    cleared at 04:11:48 UTC, before any run.
  - **Prompt:** a thin pointer to this file, plus duplicated hard limits
    as defense in depth: one PR, never merge, never relabel a work order,
    no self-edit. A change to any of those updates prompt and playbook
    together.
  - **Reporting:** the marker-found journal issue in §6.
  - **Spend:** reported in the journal; excluded from the cost ledger
    exactly as ADR-0044 decided.
  ```
- Evidence (the live trigger, **captured by the orchestrating session,
  not by this Verify pass**, quoted verbatim from its
  `trigger-evidence.txt`):

```
Captured by the orchestrating session with RemoteTrigger action "get" on
2026-09-29 (UTC), trigger_id trig_01W5PgiQb4G2qwMXnNVFtACx. Fields copied
verbatim from the HTTP 200 response:

  "name": "factory-weekly-queue-groomer"
  "id": "trig_01W5PgiQb4G2qwMXnNVFtACx"
  "enabled": true
  "cron_expression": "17 13 * * 3"
  "model": "claude-sonnet-5-5"
  "environment_id": "env_012GDG167Tpz55u8MEpDkL2y"
  "allowed_tools": ["Bash","Read","Write","Edit","Glob","Grep"]
  "sources": [{"git_repository":{"url":"https://github.com/mattbutlerengineering/skills"}}]
  "mcp_connections": []
  "next_run_at": "2026-09-30T13:17:00Z"
  "created_at": "2026-09-29T04:11:42.480782Z"
  "updated_at": "2026-09-29T04:11:48.766881Z"
  prompt begins: "You are the skills repo's weekly queue-groomer routine, operating under the factory toolsmith charter. ... Read docs/factory/queue-groomer-routine.md and follow it exactly ..."
```

- Result: PASS, on the orchestrator's capture. The protocol doc has
  landed in the sibling shape. The captured trigger matches its §Trigger
  field for field: weekly cron `17 13 * * 3`, model `claude-sonnet-5-5`,
  `mcp_connections: []`, enabled, next run 2026-09-30T13:17:00Z. The doc
  states the cost-ledger exclusion. Whether the routine actually runs
  well is not yet knowable (see Not verified).

### 16. WO-0071 acceptance: doc-gardener protocol doc + weekly Sonnet no-MCP trigger

- Check: the same as row 14, for the doc gardener.
- Evidence:
  ```
  $ grep -nE "^## " docs/factory/doc-gardener-routine.md
  33:## 1 Preconditions and degrade ladder
  50:## 2 Orient (read-only)
  64:## 3 Survey
  94:## 4 Pick exactly one
  109:## 5 Implement
  128:## 6 Report and journal
  152:## 7 Non-negotiables
  174:## 8 Amending this playbook
  181:## Trigger
  $ grep -nE "deferred by owner decision|is not an approval|^\*\*Not yet created" docs/factory/doc-gardener-routine.md
  183:**2026-09-29: deferred by owner decision** while the
  186:is not an approval: nothing authorizes creating this trigger.
  188:**Not yet created.** A scheduled trigger is recurring paid spend, and
  ```
- Result: FAIL, deferred by owner decision (2026-09-29). The protocol
  doc has landed. The weekly trigger the row requires does not exist.
  The revisit is seeded at docs/backlog.md line 77.

### 17. WO-0072 acceptance: battery green with every prior row present; PRD-0006 re-walk; epic #439 Destination re-check

- Check: rows 1 to 16 of this file re-walk PRD-0006's criteria and the
  row acceptance criteria against what landed, and row 18 re-checks the
  Destination. The battery was run fresh with orders 65 to 71 all
  checked.
- Evidence:
  ```
  $ grep -cE "^- \[x\] \*\*WO-00(6[5-9]|7[0-1])\*\*" docs/features/factory-evolution-v1/breakdown.md
  7
  $ python3 -m unittest discover tests
  Ran 1793 tests in 20.343s

  OK
  $ python3 lint.py
  lint: 0 problem(s) across 25 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS on the row's literal wording. The battery is green, the
  re-walk is rows 1 to 16, and the re-check is row 18. The re-check's
  own outcome is FAIL. This PASS covers only that the close-out work was
  done, not that the Destination was met.

### 18. Epic #439 map Destination: "Done when nothing is left to decide before building starts"

- Check: read the epic and its eight tickets (read-only). Then, for each
  of the seven backlog items (orders 65 to 71), ask whether any decision
  remains before its building can start.
- Evidence:
  ```
  $ gh issue view 439 --json number,title,state,labels --jq '"#\(.number) \(.state) [\(.labels|map(.name)|join(","))] \(.title)"'
  #439 CLOSED [] Map: Factory evolution — best AI SDLC workflow
  $ gh issue view 439 --json body --jq .body | sed -n 3p
  A ratified evolution blueprint for the factory: the four-family open-source survey distilled into adopt/adapt/reject ADRs, a routine roster v2 decided, and a seeded work-order backlog (breakdown rows first, per ADR-0032) that the factory's own dispatch loop executes. Done when nothing is left to decide before building starts.
  $ for n in 431 432 433 434 435 436 437 438; do gh issue view $n --json number,state,title --jq '"#\(.number) \(.state) \(.title)"'; done
  #431 CLOSED Survey: autonomous coding agent harnesses (OpenHands, SWE-agent, Aider, claude-flow)
  #432 CLOSED Survey: AI review & CI automation (CodeRabbit-class bots, merge queues, agentic CI)
  #433 CLOSED Survey: eval harnesses & agent memory (promptfoo, DeepEval, mem0, Letta)
  #434 CLOSED Baseline: pin the autonomy-per-human-hour metric to ledger actuals
  #435 CLOSED Decide paid-eval funding: budget line and which LEDGER maturities graduate first
  #436 CLOSED Ratify: adopt/adapt/reject pass over the four survey shortlists
  #437 CLOSED Decide routine roster v2: which scheduled routines exist, cadences, budgets
  #438 CLOSED Seed the evolution backlog: ADR set + breakdown rows from ratified decisions
  $ grep -nE "^- (Adopt GitHub's merge queue once hosting|Create the retro/reflect and doc-gardener weekly triggers)" docs/backlog.md | cut -c1-400
  76:- Adopt GitHub's merge queue once hosting allows it (WO-0065, PRD-0006 §Success criteria; ADR-0070; owner deferred it 2026-09-28): the repo is user-owned, private, and on the free plan, so branch protection, rulesets, and the merge queue all return HTTP 403 or are unavailable, and no status check is enforced on `main` today. What unblocks it: the repo moves to an organization (public, or privat
  77:- Create the retro/reflect and doc-gardener weekly triggers once the queue-groomer pilot has run (WO-0069, WO-0071, PRD-0006 §Success criteria; owner deferred both 2026-09-29): the queue groomer's trigger (trig_01W5PgiQb4G2qwMXnNVFtACx, first run 2026-09-30) pilots first so its journal shows the real weekly cost. What unblocks it: a few groomer journal entries with spend, then the owner's appro
  $ grep -E '"WO-00(6[5-9]|7[0-2])"' docs/factory/costs.jsonl | cut -c1-160 | grep -c 'owner-session:unmetered'
  8
  ```
  State of the seven items, from rows 10 to 16 and the evidence above:

  | Item | Built? | Left to decide before building starts |
  |------|--------|----------------------------------------|
  | WO-0065 merge queue | no | Yes: whether the repo moves to an organization (hosting), and then ADR-0070's cascade-cost and review-composition tuning |
  | WO-0066 clarification markers | yes | nothing |
  | WO-0067 PRD coverage check | yes | nothing |
  | WO-0068 precision/recall/F1 | yes | nothing |
  | WO-0069 retro/reflect routine | doc only | Yes: the owner's approval of its recurring spend, after the pilot's journal shows cost |
  | WO-0070 queue groomer | yes (trigger per the orchestrator's capture) | nothing |
  | WO-0071 doc gardener routine | doc only | Yes: the same approval as WO-0069 |

- Result: FAIL, the Destination is not met. Three of the seven items
  (WO-0065, WO-0069, WO-0071) still have an owner decision outstanding
  before their building can start. Each is deferred by owner decision
  and seeded in docs/backlog.md (lines 76 and 77). The epic and all
  eight of its tickets are already CLOSED, so the tracker shows the map
  as finished while the Destination's own done-condition is not. Also,
  all eight rows were executed by owner sessions: every one of their
  ledger rows says `owner-session:unmetered`. None ran through the
  factory's dispatch loop that the Destination names.

## Failures

Four failures. None of them is an implementation defect, so none routes
back to Implement (see `assumptions:`). Each waits on an owner decision
already recorded in docs/backlog.md.

- **WO-0065 (row 10)**: the merge queue is not enabled. It routes to
  the owner, whose hosting decision (move the repo to an organization)
  unblocks it, per the docs/backlog.md line 76 seed. ADR-0070's open
  tuning questions stay open until then.
- **WO-0069 (row 14)** and **WO-0071 (row 16)**: the retro/reflect and
  doc-gardener triggers do not exist. They route to the owner's approval
  of the two recurring costs once the queue-groomer pilot's journal
  shows real spend, per the docs/backlog.md line 77 seed. Creating
  either trigger stays with the orchestrating or owner session. No stage
  subagent may create one.
- **Epic #439 Destination (row 18)**: not met. It follows from the three
  failures above and clears when they do.

## Not verified

- **The queue-groomer trigger was not observed by this pass.** Its
  evidence is the orchestrating session's capture, quoted verbatim in
  row 15. Its first run (2026-09-30 13:17 UTC) has not happened. Whether
  the routine runs, stays in its lane, and reports spend to the journal
  as its protocol requires is not verified. The capture elides the middle
  of the prompt ("..."), so whether the prompt repeats the doc's hard
  limits (one PR, never merge, never relabel, no self-edit) is also not
  verified.
- **The absence of the retro/reflect and doc-gardener triggers was not
  observed.** It is taken from the docs' dated deferral lines, the brief
  and breakdown.md's notes, because listing triggers is outside this
  pass's limits.
- **Re-deriving the backlog's 18/39 = 0.462 near-miss micro recall was
  not run.** Its command runs `trigger_eval.py`, which this pass is
  forbidden to run, even in its zero-spend `--metrics` mode. The number
  is quoted from docs/backlog.md as recorded, and the derivation is
  covered only by the unit tests in row 13.
- **Paid checks were not run**: `trigger_eval.py` (routing eval) and
  `charter_replay.py`. Both need the `claude` CLI and spend money, and
  this run's brief allows no spend.
- **Detector B was not run against a live PR event.** Locally it skips
  without an event payload. `python3 gates.py --selftest` exercises it
  on a fixture. The uncommitted 2026-09-29 Implement changes have no PR
  yet, so their CI has not run.
- **The battery at each intermediate commit was not checked.** Only
  the current tree (a fresh run) and the `check` job on the six merged
  PRs (row 9) were. On those same PRs the `needs-review-label` and
  `merged-label` jobs show FAILURE conclusions. Those jobs are lifecycle
  labelling, not the battery, and this pass did not investigate them.
- **The epic's "Not yet specified" list was not re-checked item by
  item.** That covers metric instrumentation gaps, ADR-0033 graduation
  tooling, and omp implications. Row 18 re-checks the Destination
  against the seven backlog items, the scope WO-0072's row names.
