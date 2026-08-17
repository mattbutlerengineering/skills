---
stage: verify
run: feature:software-factory
date: 2026-08-17
---

# Verification: software-factory

Re-verification after Milestone E (the review's fix loop, WO-0030..0035,
merged via PRs #286–#293). Supersedes the 2026-08-14 verification (git
history); the breakdown's 2026-08-14 note — "Verify and Review re-run
after Milestone E" — is the mandate for this pass.

## Summary

Against PRD-0001's eight success criteria: **3 PASS, 2 PARTIAL, 3 FAIL**
— the same tally as 2026-08-14, but the ground under it moved. All six
Milestone E acceptance criteria verify in-tree with quoted evidence (the
review's critical and its persistence/gating majors are fixed and
test-pinned). The three FAILs still share the one cause: no work order
has ever traversed the label gates live — and that gap is now
operator-adjudicated, not merely observed: the 2026-08-15 /goal directed
close-out with the first end-to-end traversal reseeded in
`docs/backlog.md` (breakdown note, 2026-08-16), no run evidence
fabricated.

Amended 2026-08-17 during Ship pre-flight: detector H failed this
artifact's own first draft — five criteria sections asserted verdicts
without fenced evidence — so the evidence below is now quoted, and the
2026-08-17 weekly report (posted this morning) is folded into
criterion 8. The gate catching its own factory's verification artifact
is criterion 6 exercised live.

Offline battery on this tree (2026-08-17, after the amendment):

```
Ran 1234 tests in 15.245s

OK
lint: 0 problem(s) across 23 skills
gates: 0 problem(s)
selftest: ok
```

## Criteria & evidence

### 1. ≥ 8 work orders merged through the factory's own three gates — FAIL

- Check: gate-label queries + ledger grep.
- Evidence:
  ```
  $ gh issue list --state all --label wo:prd-approved --json number --jq 'length'
  0
  $ gh issue list --state all --label wo:blueprint-approved --json number --jq 'length'
  0
  $ gh issue list --state all --label wo:merged --json number --jq 'length'
  29
  $ grep -c "gate_wait" docs/factory/costs.jsonl
  18
  ```
- Result: FAIL. 29 orders carry `wo:merged` and 18 merge-gate passages
  are in the ledger, but zero orders have ever carried
  `wo:prd-approved` or `wo:blueprint-approved` — approval still happens
  in-artifact during owner sessions, not through the first two label
  gates. Unchanged from 2026-08-14.

### 2. ≥ 3 work orders fully unattended (dispatch → PR → review → merge) — FAIL

- Check: assembler run history.
- Evidence:
  ```
  $ gh run list --workflow assembler.yml --limit 10 --json status,conclusion,event \
      --jq '[.[] | .conclusion] | group_by(.) | map({(.[0]): length}) | add'
  {"cancelled":3,"skipped":7}
  ```
- Result: FAIL. Zero assembler runs have ever executed their steps
  (7 skipped at the job `if:`, 3 cancelled). The dispatch path was
  pre-flighted offline 2026-08-14 (resolve → claim → agent → spend →
  find-pr, Accept criterion confirmed in the resolved prompt — breakdown
  note), but the repo carries no ANTHROPIC_API_KEY Actions secret and
  the owner did not drive the label gates in the supervision window, so
  no live dispatch exists. Reseeded in `docs/backlog.md` per the
  2026-08-15 /goal rather than claimed.

### 3. Budget-exhaustion test: hard stop, preserved WIP, handoff — PARTIAL

- Check: the deliberate exhaustion suite at the unit seam, now
  including WO-0032's persistence ordering, run verbosely 2026-08-17.
- Evidence:
  ```
  $ python3 -m unittest tests.test_budget_guard -v 2>&1 | grep -E "over_budget|exhaustion|push_failure"
  test_a_deliberately_over_budget_run_hard_stops_and_hands_off (...TestAcceptanceScenario...) ... ok
  test_push_failure_still_produces_handoff_and_ledger (...TestHardStop...) ... ok
  test_the_exhaustion_row_is_inside_the_pushed_commit (...TestHardStop...) ... ok
  ```
  `budget_guard.py:140-145` pins the order in the `hard_stop`
  docstring: "the append comes FIRST so the row is on disk when
  push_wip's `add -A` stages the tree, and the pushed WIP commit
  carries it off the ephemeral runner (WO-0032)".
- Result: PARTIAL. Stronger than 2026-08-14 — the exhaustion row now
  provably survives the runner — but still unit-seam only; no live
  exhaustion has occurred because nothing has ever been dispatched
  (criterion 2). NOT RUN live, for that reason.

### 4. A dispatch attempted by anyone other than Matt does not run — PARTIAL

- Check: workflow guard quoted + tested authority run verbosely
  2026-08-17 (both unchanged since 2026-08-14).
- Evidence:
  ```
  # .github/workflows/assembler.yml, the job gate:
  if: >-
    github.event.label.name == 'wo:ready-for-agent'
    && github.event.sender.login == github.repository_owner
    && vars.FACTORY_PAUSED != 'true'

  $ python3 -m unittest tests.test_assembler -v 2>&1 | grep -E "non_owner|undeclared"
  test_a_non_owner_labeler_is_inert (...TestActorIsOwner...) ... ok
  test_an_undeclared_owner_fails_closed (...TestActorIsOwner...) ... ok
  test_a_non_owner_label_is_a_no_op_not_an_error (...TestRunResolve...) ... ok
  ```
- Result: PARTIAL. The tested-authority half is verified and fails
  closed; no real non-owner has ever attempted a live dispatch, so the
  workflow half remains assumed ("verified, not assumed" is the
  criterion's bar). NOT RUN live, for that reason.

### 5. A deliberately broken requirement→work-order link fails the build — PASS

- Check: gates selftest on this tree (detectors A/B plant and catch
  broken fixtures on every push) + the recorded live firing.
- Evidence:
  ```
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
  Live: detector B failed PR #253's validator run 2026-08-11 for a
  missing WO citation / `Closes #N`; the PR could not merge until the
  body was corrected (recorded in
  docs/fixes/deepening-cli-seams/release.md).
- Result: PASS.

### 6. Asserted-but-not-evidenced verification fails the build — PASS

- Check: detector H selftest on this tree — and a live firing today,
  against this very artifact: the first draft of this verification
  asserted verdicts in prose, and Ship's pre-flight battery failed on
  it.
- Evidence:
  ```
  # 2026-08-17 pre-flight, against this artifact's own first draft:
  H: docs/features/software-factory/verification.md:91 criterion "3. Budget-exhaustion
  test: hard stop, preserved WIP, handoff — PARTIAL" asserts PARTIAL. ... with neither
  literal evidence nor a NOT-RUN disclaimer (evidence must be a fenced code block in
  this section)
  gates: 5 problem(s)

  # after the evidence was fenced (this revision):
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS — proven by selftest on every push, and now by the gate
  rejecting the factory's own verification artifact in the wild.

### 7. ≥ 1 automated signal becomes a triaged work item, no transcription — PASS

- Check: sweep-filed issue re-read 2026-08-17 (unchanged since
  2026-08-14).
- Evidence:
  ```
  $ gh issue view 173 --json number,title,labels,author \
      --jq '{number, title, labels: [.labels[].name], author: .author.login}'
  {"author":"app/github-actions","labels":["type:chore","source:sweep"],
   "number":173,"title":"[sweep] label taxonomy drift (3 problem(s))"}
  ```
  Detector L's problem strings ride the issue body verbatim in a
  fenced block; no human transcription anywhere in the path; closed
  after `label_sync.py --apply` resolved the drift.
- Result: PASS.

### 8. First weekly report posts with every merged WO in the ledger — FAIL

- Check: the first report's body, and this morning's report (#296,
  posted 2026-08-17T08:01Z, while this run sat at Ship).
- Evidence:
  ```
  # The first report — the criterion's subject — posted 2026-07-20:
  $ gh issue view 160 --json body   # excerpt
  **Runs recorded:** 0
  ### By work order
  - (no runs recorded)

  # This morning's report:
  $ gh issue view 296 --json body --jq .body | head -8
  ## Factory cost report — 2026-08-17
  **Spend this month (2026-08):** $0.00 of $300.00 monthly cap (lifetime: $0.00)
  **Runs recorded:** 18
  **Total tokens:** 0

  ### By work order (lifetime)
  - WO-0018: $0.00
  - WO-0019: $0.00
  ```
- Result: FAIL as written and unfixable retroactively — the first
  report (#160, 2026-07-20) posted "Runs recorded: 0" while merged WOs
  existed, and every report through #244 (2026-08-10) predates the
  ledger's first rows (2026-08-13/14). The forward remediation
  (`wo-record` + detector G + WO-0031's commit step) is now
  demonstrated live: #296 is the first report recomputed from real
  ledger rows — 18 runs, at $0.00/0 tokens because every row so far is
  a gate-latency or owner-session row, no paid dispatch having run.

## Milestone E acceptance criteria (breakdown rows not covered above)

All six verified in-tree:

- **WO-0030** — validator.yml:27-31 gains `workflow_dispatch` with a
  required `pr` input, checks out `refs/pull/{pr}/head` and synthesizes
  the PR event payload (lines 47-56); assembler.yml:187 hands off with
  `gh workflow run validator.yml -f pr=${{ steps.find.outputs.pr }}` —
  the one event GitHub exempts from GITHUB_TOKEN suppression (comment,
  assembler.yml:170). The review's critical is closed. Live firing
  awaits the first real dispatch.
- **WO-0031** — assembler.yml:161-164 appends the run's spend row in a
  scratch checkout, commits, and pushes to main (gate-digest.yml's
  pattern); the row no longer dies with the runner.
- **WO-0032** — append-before-push pinned in code
  (budget_guard.py:140-145) and test
  (`test_the_exhaustion_row_is_inside_the_pushed_commit`,
  tests/test_budget_guard.py:235).
- **WO-0033** — cost-report.yml:73-75: the pause step is gated
  `always() && steps.report.outputs.pause == 'true'`, so fail-closed
  verdicts (nonzero exit with pause=true) still set FACTORY_PAUSED.
- **WO-0034** — assembler.yml:50 `timeout-minutes: 60`, line 119
  `--max-turns 100` (ADR-0034's two uncorrelated mechanical stops);
  docs/setup.md:150-153 discloses that the payload ships the dispatch
  workflow without charters (stamped-repo dispatch fails closed at the
  charter lookup); ADR-0055 records the budget-hook and payload-charter
  deferrals.
- **WO-0035** — rejection_mining.py imports sweeps' `sanitize`
  (line 42) and applies it to every excerpt (line 102); excerpts are
  emitted inside a ```text fence whose closing runs are pre-defanged
  (lines 150-156); duplicate Closes refs dedup via `dict.fromkeys`
  (lines 113-118) so one review never double-counts.

## Failures

Criteria 1, 2, and 8 FAIL. None names a code defect, and none routes
back to Implement: 8 is historically unfixable (its forward remediation
is built, verified above, and demonstrates live on the 2026-08-17
report), and 1–2 are one gap — no live gate traversal — that the
operator has already adjudicated (2026-08-15 /goal): close out v1 with
the supervised end-to-end traversal reseeded in `docs/backlog.md`,
becoming the next run's headline rather than this run's blocker. The
2026-08-14 verification recommended routing that exercise to Implement;
it was routed (WO-0035), the supervision window came and went without
the owner driving the gates, and the operator chose reseed over
fabricated evidence. This pass records the FAILs unsoftened and hands
the run to Review with that disposition on the record.

## Not verified

- **Live traversal of the PRD and blueprint gates** — zero orders have
  carried either approval label (criterion 1 evidence).
- **Live dispatch of any kind** — zero assembler executions
  (criterion 2 evidence); consequently WO-0030's validator hand-off,
  WO-0031's spend-row commit, and WO-0034's mechanical stops have never
  fired in a real run — all are workflow/test-pinned only.
- **Live budget exhaustion and live non-owner rejection** — both
  presuppose live dispatch (criteria 3–4 PARTIAL).
- ~~The 2026-08-17 weekly report~~ — observed after all: it posted at
  08:01Z with 18 recorded runs while this artifact sat at Ship
  (criterion 8's evidence).

One gap wearing every hat: the dispatch plane is built, gated, fixed
per review, and test-pinned — and has processed zero real work. That
gap is now a named backlog seed, not an unrecorded absence.
