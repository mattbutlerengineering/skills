---
stage: verify
run: maintenance:a-timestamp-the-digest-cannot-parse
date: 2026-09-22
assumptions:
  - "No prd.md exists for this maintenance run (protocol: maintenance runs skip PRD); the criteria walked below are defect.md's own Success criteria section, per breakdown.md's 'What Verify owes' instruction."
  - "Following breakdown.md's 'What Verify owes' literally: this stage assembles and re-runs the evidence architecture.md and breakdown.md already gathered rather than authoring new, duplicate regression tests — the existing suite already pins defect.md's exact §1/§3 shapes and cites defect.md/#491 by name in its own docstrings. Every command below was re-run fresh by this stage at its own HEAD, not copied from a prior stage's output."
  - "The rejection_mining forwarding deferral and the narrower dashboard/rejection_mining reporting-asymmetry are cited from a-malformed-timestamp-is-silently-dropped/release.md, not re-decided here, per explicit instruction in both breakdown.md and this run's dispatch."
  - "One command (python3 -m unittest discover tests) produced trailing stdout noise (a test's own gate_digest.main([\"nonsense\"]) call printing gate_digest's module docstring, buffered until process exit because stdout is fully buffered under a pipe while unittest's own summary goes to stderr). This is cosmetic output-ordering, not a test failure — the run still reports 'Ran 1700 tests ... OK', exit 0 — and is noted here rather than silently trimmed from the quoted evidence."
---

# Verification: a timestamp the digest cannot parse

## Summary

**All 7 success criteria in `defect.md` are met.** This run's Implement
stage added zero code (see "Why no code" below) — the gap was closed
upstream by two independently-seeded, already-merged, already-reviewed
PRs (#326 and #499) before this run's Architect stage even re-entered.
Verify's job here is to demonstrate that closure against the live tree,
not to generate new evidence for a fix this run didn't write. Every
command below was re-run for real at `HEAD` `47b6937` on 2026-09-22 and
its actual output is quoted. No failures, no discrepancies against
`breakdown.md`'s expectations.

## Why Implement added no code

`architecture.md` (2026-09-22) concluded that every gap `defect.md` was
opened to close was already closed on `main`: PR #326 (`9324d31`, merged
2026-09-20, fixed the crash by making the timestamp check part of the
admission walk) and PR #499 (`b6b365c`, merged 2026-09-21, added the
`gd:`/`dashboard:` problem-string reporting that was still missing).
`breakdown.md` independently re-verified that conclusion at Decompose
time and cut a single non-code closure checkbox (A1: re-confirm the tree
hasn't drifted immediately before handing off to Verify), which is now
checked. Confirmed again, independently, by this stage:

```
$ git merge-base --is-ancestor b6b365c HEAD && echo "b6b365c IS ancestor of HEAD"
b6b365c IS ancestor of HEAD
$ git merge-base --is-ancestor 9324d31 HEAD && echo "9324d31 IS ancestor of HEAD"
9324d31 IS ancestor of HEAD
$ git log -1 --format='%h %ad %s' --date=iso HEAD
47b6937 2026-09-21 20:38:57 -0700 fix(gates): detector J's own roster table still called it unused (#516)
```

`git status --short` at this stage shows no diff introduced by this run
beyond the pre-existing modified `.beads/issues.jsonl`,
`architecture.md`, `autorun-brief.md`, and `breakdown.md` already present
before Verify started — confirming this stage itself also added no
source/test/template/manifest changes.

## Criteria & evidence

### Criterion 1 — a malformed-but-truthy timestamp anywhere in a gate timeline produces a `gd:`-prefixed problem string and a nonzero exit, never a traceback

### Criterion 2 — both call sites are covered (completed-stay path `_capture_latency` → `gate_passages`, and open-stay path `_queues` → `waited_seconds`)

- Check: re-ran `defect.md` §1's history (completed, confirmed stay whose
  *closing* `unlabeled` event carries `"not-a-timestamp"`) and §3's
  history (an *open* stay whose only `labeled` event carries
  `"not-a-timestamp"`) through the real `gate_digest.run_daily` and
  `gate_digest.main`, against a real mirrored issue number taken from
  this repo's own `knowledge_plane.mirror_map`, with only the `gh` runner
  injected — the same harness shape `defect.md` §2 and `architecture.md`
  used, re-run fresh by this stage.
- Evidence:
  ```
  using real mirrored issue: 106 -> WO-0001

  === S1: completed-confirmed stay, malformed closing timestamp ===
  gate_digest.run_daily -> {'changed': 'false', 'reason': 'gd: 0 item(s) waiting, 0 new gate-latency row(s)'} ['gd: timeline for #106 refused 1 malformed timestamp(s)']
  gd: 0 item(s) waiting, 0 new gate-latency row(s)
  gd: timeline for #106 refused 1 malformed timestamp(s)
  gate_digest: 1 problem(s)
  gate_digest.main -> exit 1
  rejection_mining.run_mine -> outputs: {'reason': 'rm: 0 candidate WO(s), 0 correction(s) mined'}
    problems: []

  === S3: open stay, malformed labeled timestamp ===
  gate_digest.run_daily -> {'changed': 'false', 'reason': 'gd: 0 item(s) waiting, 0 new gate-latency row(s)'} ['gd: timeline for #106 refused 1 malformed timestamp(s)']
  gd: 0 item(s) waiting, 0 new gate-latency row(s)
  gd: timeline for #106 refused 1 malformed timestamp(s)
  gate_digest: 1 problem(s)
  gate_digest.main -> exit 1
  rejection_mining.run_mine -> outputs: {'reason': 'rm: 0 candidate WO(s), 0 correction(s) mined'}
    problems: []
  ```
- No traceback on either history, on either independently-reachable call
  site: `main -> exit 1` with the `gd: timeline for #106 refused 1
  malformed timestamp(s)` problem string on both S1 (which exercises
  `_capture_latency` → `gate_passages`) and S3 (which exercises `_queues`
  → `waited_seconds`, since an open stay needs no completed pair at all).
  Reading `gate_digest._timelines` (`gate_digest.py`) confirms the
  mechanism: it computes `refused_timestamps(raw)` on the *raw* timeline
  before narrowing to `label_events(raw)`, so the count and the admitted
  list can never drift apart, and `main`'s exit code comes from
  `cli.report`, which is nonzero whenever `problems` is non-empty.
- Result: **PASS** (both criteria)

### Criterion 3 — the §1 repro is a passing regression test, and a second test covers the §3 open-stay history that `gate_passages` returns `[]` for

- Check: ran the three specifically-named tests, then the full
  four-module suite.
- Evidence:
  ```
  $ python3 -m unittest tests.test_gate_digest.TestRunDaily.test_a_malformed_closing_timestamp_is_refused_not_swallowed tests.test_gate_digest.TestRunDaily.test_a_malformed_labeled_timestamp_is_refused_not_swallowed tests.test_dashboard.TestQueues.test_a_malformed_timestamp_is_refused_not_swallowed -v
  test_a_malformed_closing_timestamp_is_refused_not_swallowed (tests.test_gate_digest.TestRunDaily.test_a_malformed_closing_timestamp_is_refused_not_swallowed)
  #491, defect.md §1 shape: a completed, confirmed stay whose ... ok
  test_a_malformed_labeled_timestamp_is_refused_not_swallowed (tests.test_gate_digest.TestRunDaily.test_a_malformed_labeled_timestamp_is_refused_not_swallowed)
  #491, defect.md §3 shape: an OPEN stay whose only labeled ... ok
  test_a_malformed_timestamp_is_refused_not_swallowed (tests.test_dashboard.TestQueues.test_a_malformed_timestamp_is_refused_not_swallowed)
  #491: a labeled event whose created_at does not read as a ... ok

  ----------------------------------------------------------------------
  Ran 3 tests in 0.003s

  OK
  ```
  ```
  $ python3 -m unittest tests.test_human_gates tests.test_gate_digest tests.test_dashboard tests.test_rejection_mining
  ----------------------------------------------------------------------
  Ran 193 tests in 0.133s

  OK
  ```
  (The second run's stdout additionally showed `gate_digest.py`'s module
  docstring and a `gate_digest: 0 problem(s)` line trailing after `OK` —
  this is `tests/test_gate_digest.py`'s own
  `test_...` that calls `gate_digest.main(["nonsense"], env={})` and
  asserts it returns `2`; that call prints the docstring to `stdout`,
  which is fully buffered under a pipe and flushes at process exit,
  after `unittest`'s `stderr`-written summary. Cosmetic ordering only —
  the suite still reports `Ran 193 tests ... OK`.)
- The two named `test_gate_digest` tests assert `problems == ["gd:
  timeline for #123 refused 1 malformed timestamp(s)"]` against fixture
  timelines that are `defect.md`'s own §1 and §3 histories (confirmed by
  reading `tests/test_gate_digest.py:422` and `:444` — their docstrings
  cite `#491, defect.md §1 shape` and `#491, defect.md §3 shape` by
  name). `tests/test_dashboard.py:296` covers the same open-stay shape
  for the `dashboard:`-prefixed path.
- Result: **PASS**

### Criterion 4 — the §6 asymmetry is either removed or recorded as intentional in an ADR, with ADR-0056 amended or superseded rather than rewritten

- Check: re-ran `defect.md` §6's identical timeline through
  `rejection_mining.run_mine` (same harness as Criterion 1+2's run,
  above) to confirm the *crash*-shaped asymmetry §6 evidenced —
  `gate_rejections` surviving a history that raised out of
  `gate_passages` — no longer exists, since neither path raises at all
  any more. Then cited the existing record of the narrower,
  reporting-only asymmetry rather than re-deciding it.
- Evidence (from the Criterion 1+2 run above, both S1 and S3):
  ```
  rejection_mining.run_mine -> outputs: {'reason': 'rm: 0 candidate WO(s), 0 correction(s) mined'}
    problems: []
  ```
  Clean exit, no problems, on both histories — the same as
  `gate_digest`'s own clean (non-traceback) exit on the same histories.
  There is no longer a "which side of the partition crashes" question:
  both `gate_passages` and `gate_rejections` walk the same
  `label_events`-admitted list, and a refused timestamp simply isn't in
  it.
- A **narrower, different** asymmetry is real and already recorded,
  cited here rather than re-decided: `gate_digest` and `dashboard` emit a
  `gd:`/`dashboard:` problem string when `label_events` refuses an event
  (confirmed above); `rejection_mining` does not, because it imports
  `label_events` only —
  ```
  $ grep -n "^from human_gates" rejection_mining.py
  42:from human_gates import gate_rejections, label_events
  ```
  — no `refused_timestamps`. This was found, evaluated, and knowingly
  deferred by PR #499 itself, recorded in
  `docs/fixes/a-malformed-timestamp-is-silently-dropped/release.md`,
  *Follow-up recorded, not actioned*, item 1: *"`rejection_mining.py`
  stays silent about a refused timestamp the same way ... Not costing it
  anything observable today (it never reaches `waited_seconds`); the same
  `refused_timestamps` call is one line to add there if a future caller
  of `gate_rejections` starts to need it."* This run's own `defect.md`
  scoped `rejection_mining` behavior out of scope from the start, and
  `architecture.md`'s Decisions & alternatives section already weighed
  and declined reopening it. Not re-litigated here.
- ADR-0056 confirmed unamended:
  ```
  $ grep -n "^- Status:" docs/adr/0056-human-gates-module.md
  3:- Status: accepted
  ```
  No amendment was needed because the criterion's own disjunction is
  satisfied on the "removed" branch for the asymmetry §6 actually
  evidenced (the crash). No ADR was written or is required.
- Result: **PASS** (on the criterion's "removed" branch, which is the
  branch §6's own evidence falls on; the narrower reporting-only gap is a
  distinct, smaller, already-recorded item — see "Not verified" below)

### Criterion 5 — the payload twins and `factory/manifest.json` match root; `python3 factory_init.py update-manifest` is run and committed with the change; detector E is green

- Check: re-diffed the three mirrored production files against their
  payload twins, confirmed `dashboard.py` has no twin (it is not a
  `factory_init.MIRRORS` entry), and ran the gate detectors including
  detector E.
- Evidence:
  ```
  $ for f in human_gates.py gate_digest.py rejection_mining.py; do
      diff "$f" "factory/templates/tools/factory/$f" && echo "$f identical"
    done
  human_gates.py identical
  gate_digest.py identical
  rejection_mining.py identical

  $ grep -n "dashboard.py" factory_init.py
  (no output — dashboard.py is not a MIRRORS entry)

  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- No twin drift exists to reconcile, so no `update-manifest` run was
  needed this stage — the manifest already matches root (detector E is
  part of the `gates: 0 problem(s)` result above, and confirms this).
  This run added no file under `factory/templates/**` and touched no
  `factory_init.MIRRORS` root file, so there is nothing for this
  criterion's "run and commit `update-manifest`" clause to apply to.
- Result: **PASS**

### Criterion 6 — the full battery is green: `python3 -m unittest discover tests`, `python3 lint.py` (`lint: 0 problem(s)`), `python3 gates.py && python3 gates.py --selftest` (`gates: 0 problem(s)`, `selftest: ok`)

- Check: ran all three, fresh, at this stage's `HEAD`.
- Evidence:
  ```
  $ python3 -m unittest discover tests
  Ran 1700 tests in 20.767s

  OK
  ```
  (exit code 0, confirmed separately)
  ```
  $ python3 lint.py
  lint: 0 problem(s) across 25 skills
  ```
  ```
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: **PASS**

### Criterion 7 — `python3 one_owner.py` gains no new problems (baseline: 9 at capture time, down to 7 confirmed by both Architect and Decompose today)

- Check: ran `one_owner.py` and compared the full output against the
  7-problem baseline `architecture.md` and `breakdown.md` both confirmed
  today, then checked whether any finding touches
  `human_gates.py`/`gate_digest.py`/`dashboard.py`/`rejection_mining.py`
  timestamp handling.
- Evidence:
  ```
  $ python3 one_owner.py
  one-owner: assembler.py:55 READY_LABEL, validator.py:95 READY_LABEL and work_queue.py:39 READY_LABEL state the same value — one fact, one owner
  one-owner: budget_guard.py:55 CONTINUE and cost_report.py:44 CONTINUE state the same value — one fact, one owner
  one-owner: charter_replay.py:49 ROOT and trigger_eval.py:42 ROOT state the same value — one fact, one owner
  one-owner: dashboard.py:189 _pr_by_issue, gate_digest.py:236 run_daily and rejection_mining.py:252 run_mine read the same payload keys (body, number, state) — one fact, one owner
  one-owner: eval_schema.py:243 validate and trigger_eval.py:303 score_case read the same payload keys (expected, id, kind, query) — one fact, one owner
  one-owner: gate_digest.py:124 LIST_ARGS and rejection_mining.py:54 ISSUE_ARGS state the same value — one fact, one owner
  one-owner: label_sync.py:90 plan, label_sync.py:136 sync and sweeps.py:289 ensure_labels read the same payload keys (color, description, name) — one fact, one owner
  one-owner: 7 problem(s)
  ```
- 7 problems, matching the baseline exactly (down from 9 at this run's
  2026-09-15 capture, per `defect.md`'s own success criterion text and
  `architecture.md`'s traceability table). One finding does name
  `dashboard.py`, `gate_digest.py`, and `rejection_mining.py` together
  (`dashboard.py:189`/`gate_digest.py:236`/`rejection_mining.py:252`),
  and a second names `gate_digest.py`/`rejection_mining.py`
  (`LIST_ARGS`/`ISSUE_ARGS`) — but both are about shared *issue-listing*
  payload keys (`body`, `number`, `state`) and shared `gh issue list`
  argument tuples, respectively, not about timestamp parsing or
  timestamp field handling. No finding involves `human_gates.py` at all,
  and none of the 7 concerns timestamp handling in any of the four named
  modules.
- Result: **PASS**

## Failures

None.

## Not verified

- **The narrower, reporting-only asymmetry** (`rejection_mining.py` never
  calls `refused_timestamps`, so a refused timestamp there produces no
  problem string, unlike `gate_digest`/`dashboard`) is **not** re-verified
  or re-decided here, by explicit instruction in `breakdown.md`'s "What
  Verify owes" section and `architecture.md`'s Decisions & alternatives.
  It is a real, smaller gap than the one `defect.md` §6 evidenced,
  already found and recorded in
  `docs/fixes/a-malformed-timestamp-is-silently-dropped/release.md`
  (*Follow-up recorded, not actioned*, item 1) by an independent,
  already-reviewed run. Citing it here, not reopening it.
- **Live production occurrence.** As `defect.md` §8 records and no
  evidence gathered by this or any prior stage changes: this defect has
  never actually fired against real GitHub data (55 scheduled
  `gate-digest.yml` runs since 2026-07-23, one unrelated push-race
  failure, zero parse failures). This stage did not re-run `gh run list`
  against the live workflow history — the fix's correctness was verified
  against `defect.md`'s own reproduction histories instead, which is what
  `breakdown.md` asks for, and re-confirming zero live incidence would
  add no information (the fix does not change whether the trigger
  condition has ever occurred, only what happens the day it does).
- **`dashboard._age_seconds`'s third exposure** is closed incidentally by
  the admission-gate design (#326) and confirmed by
  `tests/test_dashboard.py`'s own passing coverage (`Criterion 3`
  evidence, above) — not independently re-derived from first principles
  by this stage beyond running that test, per `breakdown.md`'s guidance
  that this exposure needed no follow-up item.

## Handoff

All 7 success criteria met, no failures, no discrepancy found against
`breakdown.md`'s expectations for what to run and quote. Next stage is
Review.
