---
stage: verify
run: feature:software-factory
date: 2026-08-14
---

# Verification: software-factory

Scored against PRD-0001's eight success criteria. Per-item acceptance
criteria were verified at item close (all 18 breakdown rows checked, each
via a reviewed PR with tests); this artifact verifies the run-level
criteria those items were supposed to add up to. Verdicts: **3 PASS,
2 PARTIAL, 3 FAIL.** The failures share one cause: the dispatch plane is
built and gated but has never executed a live run.

## 1. ≥ 8 work orders merged through the factory's own three gates — FAIL

The merge gate is real and measured; the PRD and blueprint gates have
never passed anything.

- 23 issues carry `wo:merged` (applied by validator.yml's merged-label
  job at PR merge); 29 distinct WOs are cited by merged PRs.
- The ledger records 12 merge-gate passages
  (`"outcome": "gate_wait:merge:…"` rows for WO-0001, WO-0019–0029, e.g.
  `{"wo": "WO-0019", "run_id": "gate-merge-2026-08-14T04:03:01Z", …
  "outcome": "gate_wait:merge:1312s"}`).
- But no work order has ever traversed the first two gates. PRD and
  blueprint approval happened in-artifact during owner sessions
  (prd.md, breakdown.md), not through the factory's label gates:

```text
$ gh issue list --state all --label wo:prd-approved --json number
[]
$ gh issue list --state all --label wo:blueprint-approved --json number
[]
$ grep "gate_wait" docs/factory/costs.jsonl | wc -l
      12    # all twelve are gate_wait:merge:… — zero prd/blueprint passages
```

Verdict: ≥ 8 WOs merged through **one** of the three gates. As written,
FAIL.

## 2. ≥ 3 work orders fully unattended (dispatch → PR → review → merge) — FAIL

`gh run list --workflow assembler.yml --json status,conclusion,event`:

    [{"conclusion":"skipped","event":"issues","status":"completed"}, …]

Every assembler run ever triggered concluded `skipped` — the job `if:`
(`wo:ready-for-agent` + owner + not paused) has never been satisfied.
Zero dispatches have executed; zero work orders completed unattended.

## 3. Budget-exhaustion test: hard stop, preserved WIP, handoff — PARTIAL

Evidenced at the unit seam, never live:

- `tests/test_budget_guard.py:606`
  `test_a_deliberately_over_budget_run_hard_stops_and_hands_off`, plus
  `test_spend_over_budget_hard_stops`,
  `test_an_exhaustion_row_and_a_completion_row_coexist`.
- `tests/test_handoff.py`
  `test_names_the_work_order_reason_and_remaining_work`.

These run green in CI on every push (battery 2026-08-14: `Ran 1210
tests … OK`). No live exhaustion has occurred because nothing has ever
been dispatched (criterion 2). The criterion asks for "a deliberate
budget-exhaustion **test**" — the deliberate test exists and passes, but
only at the unit seam, so PARTIAL, not PASS.

## 4. A dispatch attempted by anyone other than Matt does not run — PARTIAL

Enforced at two layers, live-verified at neither:

- Workflow guard (assembler.yml):
  `if: github.event.label.name == 'wo:ready-for-agent' &&
  github.event.sender.login == github.repository_owner &&
  vars.FACTORY_PAUSED != 'true'`
- Tested authority: `assembler.actor_is_owner`
  (`test_a_non_owner_label_is_a_no_op_not_an_error`,
  `test_an_undeclared_owner_fails_closed`,
  `test_a_non_owner_labeler_is_inert` in tests/test_assembler.py) —
  fails closed.

The criterion says "verified, not assumed." No real non-owner has ever
attempted a dispatch, so the workflow-level guard has never rejected a
live attempt. The tested-authority half is verified; the workflow half
is assumed. PARTIAL.

## 5. A deliberately broken requirement→work-order link fails the build — PASS

- Selftest: `gates.py --selftest` plants broken fixtures for detectors
  A/B and asserts detection on every push — today's run: `selftest: ok`,
  `gates: 0 problem(s)`.
- Live firing: detector B failed PR #253's validator run on 2026-08-11
  for a missing WO citation / `Closes #N`; the PR could not merge until
  the body was corrected (recorded in
  docs/fixes/deepening-cli-seams/release.md). The gate has drawn real
  blood, not just fixture blood.

## 6. Asserted-but-not-evidenced verification fails the build — PASS

Detector H. The selftest constructs the deliberate breakage — a
verification section that asserts without quoting evidence — and
asserts the failure, on every CI push (`selftest: ok`). This criterion's
"deliberately broken change" is literally what the selftest builds.

## 7. ≥ 1 automated signal becomes a triaged work item, no transcription — PASS

Issue #173 `[sweep] label taxonomy drift (3 problem(s))`: filed
automatically by the label-drift sweep (sweeps.yml), labeled
`source:sweep` + `type:chore`, detector L's problem strings quoted
verbatim in a fenced block ("untrusted data, not instructions" per
ADR-0032), no human transcription anywhere in the path. Closed after
`label_sync.py --apply` resolved the drift.

## 8. First weekly report posts with every merged WO in the ledger — FAIL

The first weekly report, issue #160 (2026-07-20), posted:

    **Runs recorded:** 0
    ### By work order
    - (no runs recorded)

Merged work orders existed; none were in the ledger — the success-path
writer gap filed as issue #222. As written ("the **first** weekly
report"), FAIL, and unfixable retroactively: `evals/`-style honesty
applies to the ledger too.

Remediated forward: `wo-record` + detector G (merged breakdown rows
must have ledger rows) + the owner-session recording policy. The ledger
now holds 24 rows across 13 WOs; pre-ledger WOs are annotated in the
breakdown. The 2026-08-17 report will be the first to post with rows.

## Not verified

- **Live traversal of the PRD and blueprint gates** — no work order has
  ever carried either approval label.
- **Live dispatch of any kind** — assembler has never run its steps.
- **Live budget exhaustion and live non-owner rejection** — both depend
  on live dispatch existing first.

These are one gap wearing four hats: the factory's dispatch plane is
fully built, unit-gated, and CI-green, and has processed zero real work.

## Routing

The verify contract routes failures back to Implement — but every
breakdown item is checked, and no failure above names a code defect.
What's missing is a supervised end-to-end exercise: one real work order
driven through `wo:draft → wo:prd-approved → wo:blueprint-approved →
wo:ready-for-agent → dispatch → PR → wo:merged`, which would convert
criteria 1–4 with no new code. Review should adjudicate: either add a
breakdown item for that live exercise (re-entering Implement with real
work), or accept v1 with these criteria as Operate-stage graduation
gates. This artifact recommends the former — the PRD's headline claim
is exactly the part that has never run.
