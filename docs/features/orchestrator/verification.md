---
stage: verify
run: feature:orchestrator
date: 2026-10-10
assumptions:
  - "Autorun-driven: no live interview. The brief's Spend section forbids paid model runs, so no real batch was run. Every PRD-0013 success criterion says 'checked on a real batch of at least four issues', so each is recorded as 'NOT RUN — unmet, pending the real batch (Owner spend consent)'. The verdict leads with NOT RUN, detector H's disclosure form, because none of them failed: they were not run. The template offers only PASS | FAIL."
  - "Breakdown acceptance criteria are verified through the unit tests that pin them (each row was test-first), quoted as module summary lines plus the test names that carry the criterion, not re-derived one assertion at a time."
  - "The offline demonstration drives conductor.main with an injected root under the session scratchpad: a hand-built one-item ledger and costs.jsonl, no git, gh, harness or network. It shows the mechanism only, and is not batch evidence."
---

# Verification: the Conductor, a batch orchestrator

## Summary

Offline: the full suite, lint, gates and the gates selftest are green, every
conductor test module passes, and 14 breakdown acceptance rows (0153 to
0164) pass on their pinned tests. An offline CLI demonstration shows the
decision queue's refusals and a scorecard that fails with a problem string.
**Against the PRD as of the offline run: 0 of 7 met, 0 failed, 7 unmet.** On the two real consumer batches recorded below (2026-10-12/13), the result is 3 pass, 2 fail and 2 unmet, on batches smaller than the four issues the PRD requires. Every
one is pending a real batch of at least four issues. That batch needs the
Owner's spend consent, and it has not happened. The mechanism behind each
criterion is built and tested with fakes. Whether the criteria hold on real
work is still unknown.

## Repo checks (run 2026-10-10 in this worktree, branch feat/orchestrator-implement at 527d305)

### Full test suite

- Check: `time python3 -m unittest discover tests`
- Evidence:
  ```
  Ran 2315 tests in 241.530s

  OK
  python3 -m unittest discover tests  31.44s user 48.11s system 32% cpu 4:04.13 total
  ```
  The output also carries expected stderr from tests that exercise
  failure paths. One example: `error: .../charter-evidence-gj84z5m1/cases.json
  case 'c1' has no require expectation`. The run ends `OK`.
- Result: PASS. It did not stall in this run. It ran at the same time as
  the merge-module run below, so the wall time is inflated.

### Lint

- Check: `python3 lint.py`
- Evidence:
  ```
  lint: 0 problem(s) across 32 skills
  lint exit 0
  ```
- Result: PASS

### Gates and selftest

- Check: `python3 gates.py && python3 gates.py --selftest` (before and after
  this artifact was written; detector C scans run artifacts)
- Evidence:
  ```
  gates: 0 problem(s)
  gates exit 0
  selftest: ok
  selftest exit 0
  ```
- Result: PASS. Detector B skips locally because there is no PR event
  payload, and the selftest exercises it.

### Targeted conductor and supporting modules

- Check: `time python3 -m unittest tests.<module>`, one module at a time
- Evidence:
  ```
  == test_conductor        Ran 41 tests in 0.300s   OK
  == test_conductor_plan   Ran 21 tests in 0.154s   OK
  == test_conductor_flow   Ran 45 tests in 0.165s   OK
  == test_conductor_run    Ran 24 tests in 0.765s   OK
  == test_conductor_close  Ran 17 tests in 0.451s   OK
  == test_cost_ledger      Ran 66 tests in 0.247s   OK
  == test_factory_config   Ran 42 tests in 0.156s   OK
  == test_conductor_merge  Ran 41 tests in 131.952s OK
     python3 -m unittest tests.test_conductor_merge  12.80s user 23.95s system 27% cpu 2:12.96 total
  ```
- Result: PASS. `test_conductor_merge` spawns real `git` over scratch repos.
  It took 132s here, while the full suite ran beside it. Implement measured
  about 96s alone.

### Offline CLI demonstration (scratch root, no network, no real PR/issue/merge)

- Check: `python3 conductor.py --help`, then a driver calling
  `conductor.main(argv, root=<scratchpad>/demo)`. The root holds a
  hand-built one-item plan row, a spend ask and answer through the CLI, and
  hand-written build, review and merge rows with two `costs.jsonl` rows. The
  driver then breaks the ledger three ways.
- Evidence (abridged to the command lines and their result lines):
  ```
  $ python3 conductor.py --help      -> prints the module usage, exit 2 (unknown verb path)

  $ conductor ask demo --kind spend ... --option approve --option decline --recommended approve
  ask-1                               -> exit 0
  $ conductor answer demo ask-1 maybe
  cd: 'maybe' is not an option of ask ask-1 (approve, decline)          -> exit 1
  $ conductor answer demo ask-1 approve   [env CONDUCTOR_WORKER=1]
  cd: answer refused: CONDUCTOR_WORKER is set, and a Worker never answers an ask   -> exit 1
  $ conductor answer demo ask-9 approve
  cd: no ask ask-9 in this batch                                        -> exit 1
  $ conductor answer demo ask-1 approve                                 -> exit 0
  $ conductor answer demo ask-1 approve
  cd: ask ask-1 is already answered ('approve')                         -> exit 1

  $ conductor scorecard demo
  { "batch": "demo", "items": 1, "merged": 1, "blocked": 0,
    "owner_touches_per_merged": 1.0, "metered_usd": 4.0,
    "metered_usd_per_merged": 4.0, "estimate_usd": 4,
    "estimate_error_pct": 0.0, "collisions": 0, "stalls": 0,
    "escalations": 0, "review_changes_per_item": 0.0,
    "start_to_last_merge_s": 11400, "merged_per_owner_wait_hour": null,
    "policy_compliance": 1.0, "conductor_session": "unmetered" }        -> exit 0

  [truncated JSON line appended]
  cd: docs/factory/batches/demo/ledger.jsonl:11 is not valid JSON: Expecting ',' delimiter: line 1 column 63 (char 62)   -> exit 1
  [state row with no reason appended]
  cd: docs/factory/batches/demo/ledger.jsonl:11 state row is missing field(s): reason                                 -> exit 1
  [review run's costs.jsonl row removed]
  cd: docs/factory/batches/demo/ledger.jsonl:7 run conductor-demo-900-review-1 has no docs/factory/costs.jsonl row with its run_id   -> exit 1
  [plan row removed]
  cd: docs/factory/batches/demo/ledger.jsonl has no plan row             -> exit 1
  scorecards.jsonl exists: False
  ```
  The ask and the answer carry the same fixed clock, so the wait is zero
  and `merged_per_owner_wait_hour` is null. That is the tool's rule for a
  zero denominator, not a defect.
- Result: PASS, for the mechanism only.

## Real consumer batches (2026-10-12 and 2026-10-13)

Two paid batches ran in mattbutlerengineering/mattbutlerengineering, with
the Owner's spend consent in session (#688). Their ledgers and scorecards
are on that repo's main: `docs/factory/batches/b20261012/ledger.jsonl`
(30 rows), `docs/factory/batches/b20261013/ledger.jsonl` (42 rows) and
`docs/factory/scorecards.jsonl`.

```text
b20261012  items 2  merged 0  blocked 2  metered $9.33   estimate $30  estimate_error_pct -68.9  collisions 0  stalls 3  escalations 4  policy_compliance 1.0
b20261013  items 1  merged 0  blocked 1  metered $21.64  estimate $15  estimate_error_pct +44.3  collisions 0  stalls 3  escalations 3  policy_compliance 1.0
```

**Neither batch met the PRD's condition of at least four issues** (they had
2 and 1), because the consumer had no four workable issues. Everything
below is measured on those undersized batches, so none of it can be called
met against the PRD as written. The Owner chose to record these results and
close #688, and to track a batch of at least four items separately.

| Criterion | Result on the real batches | Evidence |
|---|---|---|
| SC 1: every Owner action is a queued answer | **FAIL** | All 12 asks were answered from the queue. But the batches also needed Owner merges outside it: the tools-only stamp (#6364) and its re-stamp (#6527), plus hand workarounds at close (prettier on the run evidence, `HUSKY=0`, a `needs-human` label, closing a superseded blueprint PR). |
| SC 2: zero shared-number collisions | **UNMET** (nothing merged) | The scorecards show 0 collisions, but no item merged, so no reservation reached a merged file. The reservations themselves were wrong for this consumer: b20261013 reserved ADR 88-90 in a repo whose ADRs are `ADR-020`..`ADR-026`, and both batches reserved PRD-1 and overlapping WO numbers. |
| SC 3: every run metered; estimate within ±50% | **FAIL** | All 13 Worker runs wrote a spend row. b20261013 is within ±50% (+44.3%), but b20261012 is not (-68.9%, three spec runs at the even-split $3 ceiling). |
| SC 4: timestamped state rows; final state matches GitHub | **PASS** (on these batches) | 23 state rows, all timestamped. Both #5995 and #6367 are blocked in the ledger and open with `needs-human` on GitHub. |
| SC 5: merged items have writer + distinct reviewer, green merge | **UNMET** (nothing merged) | 0 items merged. #6367's review stalled twice at the $2.14 ceiling. |
| SC 6: every Worker on the policy's model and effort | **PASS** | `policy_compliance` 1.0 in both scorecards. Every run row names the band's model and effort. |
| SC 7: scorecard from ledger rows alone, appended, fails loudly | **PASS** | Both scorecards were computed at close and appended to the consumer's `scorecards.jsonl`. The malformed-row refusal is pinned offline (`test_conductor_close`). |

**Tally on the real batches: 3 pass, 2 fail, 2 unmet.** Each failure and
each unmet criterion was filed and fixed through plugin 0.14.0:
- spec pricing (#724, then weighted ceilings)
- retries blind to committed work (#725)
- close hardening (#726, #728)
- launch refusals (#708, #709)
- worktree anchoring (#710)
- defer labels (#711)
- landing on a checked head (#770)
- spend identity (#771, #772)

Still open: the closing-merge race with a consumer's own auto-merge (#807),
and the reservation scan reading the payload's own ADR citations (filed
with this change).

## Real consumer batches, round 2 (2026-10-13 to 2026-10-16)

The second consumer round (#946, the Owner's write-up, read against the
consumer's `conductor/*` ledgers, `docs/factory/costs.jsonl` and
`runs/*.json`) covers four batches in mattbutlerengineering/mattbutlerengineering
on three payload versions: b20261013 (tools 0.12.2, one item), b20261014
(0.15.0, one item), b20261014c (0.19.0, five items) and sdlc-ci (0.19.0,
three items). b20261014c is the first batch at PRD-0013's stated size.
None of the four has closed yet (see the standing tracker below), so no
scorecard row exists for them and nothing here re-scores SC 1-7.

### What worked, and where it is protected

- **The `cause` taxonomy (#819)** made every stall in four ledgers
  classifiable by grep; every finding below was found that way.
  `conductor.CAUSES` is the one vocabulary and every new stall path flows
  through it (`tests/test_conductor_flow.py`, `tests/test_conductor_next.py`).
- **`NO_HOOKS` (#833)** removed the husky stall class at one port; the
  0.19.0 batches show none.
- **The ledger-as-state design held through a 20-hour dead session.**
  sdlc-ci's three spec runners were lost at 04:47Z; `next` found them at
  01:09Z the next day, asked once per item, and the retries completed in
  about a minute each because #725's retry note told the Worker its
  artifacts were already committed. State was never in doubt. The money
  was: see #937 below.
- **Gate re-pricing told the truth before build spent it**: every M item
  re-priced from $15 to $21-26 at the gate, and the Owner saw the number
  first. The estimate was wrong (#940); the honesty was right.
- **The manifest's sha256 entries doubled as an upgrade check** for a
  tools-only install; #941 made that a command.
- **`kb.py harvest` from a worktree finds the main checkout (#710)**,
  verified by use.
- **Five items ran concurrently to the WIP cap**, asks arriving one at a
  time in finishing order: the one-question interaction model from #713
  still holds at that size.

### What was fixed from this round

| Finding | Issue | Fixed by | What changed |
|---|---|---|---|
| Review priced at verify's slice, so review never completed | #936 | #953 | review weighs three shares like spec; the gate ask states the review ceiling; a first budget stop that never let the Worker start recommends retry-up or block |
| A lost runner left its spend unmetered | #937 | #967 | `next` writes the run row and charges the step's ceiling through the one spend path (`conductor_spend`); fail-closed |
| An item PR merged outside the batch was invisible | #938 | #973 | `next` reads the PR every tick; `deliver` finds a merged PR before opening another; close and scorecards reconcile as merged outside the batch |
| A stall after the Worker finished relaunched the Worker | #939 | #972 (and #954) | a `delivery-failed` retry redoes only the spend commit, push and PR (`conductor_next`); stall reasons carry stderr; a closed issue stalls with a clarify ask before any launch |
| `calibrate` silent below the floor | #940 | #971 | per-step ceiling warnings at any sample size, repeated by `plan`; `conductor.calibrate_floor`; pre-work-order build rows set aside |
| No update path for a tools-only install | #941 | #957 | `factory-init stamp/update --tools-only`; `conductor.py --version` |
| A prepared release never written back; Ship complete on file existence | #942 | #968 | `release.md` records `outcome:` and `pending-merge:`; Ship completes on a reached outcome; Operate resolves or stops |
| Stage artifacts left uncommitted for nine days | #943 | #958 | every stage commits its artifact at its boundary; autorun refuses to advance past an uncommitted one |
| A run's own Review deferrals read as post-ship feedback | #944 | #970 | `retro.md` carries `users-observed:` and `signal-source:`; the run's own debt is listed, never counted; autorun briefs get an `operate:` section |
| GraphQL-backed `gh` calls fail in Claude Code Remote | #945 | #951 | every such call in skill text names its `gh api` REST twin |

The Owner's one-line reading of the round stands: the Conductor
delivered real code (b20261014c merged four item PRs within 90 minutes
of plan) and lost money in three ways. Ceilings that could not fit the
model they priced are #953 and #971; runs that died unmetered are #967;
retries that relaunched finished work are #972. #938 is what makes the
scorecard agree with GitHub.

### The standing tracker

#822 stays open by the Owner's decision. The next step is the Owner's:
upgrade the consumer's tools to the release carrying the fixes above
(`factory-init update --tools-only`), run `next` on b20261014,
b20261014c and sdlc-ci so the bookkeeping retries commit and push the
spend rows `close` refused on, close the batches, then
`conductor.py scorecards` and `conductor.py calibrate`, and re-score
SC 1-7 here from those rows.

## Criteria & evidence: PRD-0013 success criteria

All seven read "Checked on a real batch of at least four issues in one
repository." No batch has run: `docs/factory/batches/` and
`docs/factory/scorecards.jsonl` do not exist on this branch.

### SC 1: every Owner action is an answer to a queued decision or a consent confirmation, logged

- Check: offline, the decision-queue tests and the demonstration's ask and
  answer refusals.
- Evidence: `test_conductor` 41 OK, including
  `test_only_the_oldest_unanswered_ask_is_returned`,
  `test_a_worker_may_never_answer`, `test_an_already_answered_ask_is_refused`
  and `test_a_choice_outside_the_options_is_refused`. The demo refusals are
  quoted above. Not yet shown: whether a real batch needed any Owner step
  outside the queue. Only a real batch can show that.
- Result: **NOT RUN — unmet, pending the real batch (Owner spend consent)**

### SC 2: zero shared-number collisions

- Check: offline, the reservation and merge-turn renumber tests.
- Evidence: `test_conductor_plan` 21 OK (`test_no_two_items_blocks_share_a_number`,
  `test_the_highest_of_each_kind_on_origin_main`). `test_conductor_merge`
  41 OK (`test_a_free_number_is_confirmed_untouched`,
  `test_a_number_taken_on_main_is_renumbered_mechanically`,
  `test_a_number_that_cannot_be_renumbered_stalls`).
- Result: **NOT RUN — unmet, pending the real batch (Owner spend consent)**

### SC 3: a metered ledger row per Worker run; plan estimate within ±50% of their sum

- Check: offline, runner tests with an injected harness, and the
  scorecard's `estimate_error_pct`.
- Evidence: `test_conductor_run` 24 OK
  (`test_a_completed_build_writes_one_run_row_and_one_spend_row`,
  `test_a_missing_harness_is_agent_failed_at_cost_zero`,
  `test_a_wall_clock_kill_records_the_ceiling_and_stalls`). The demo
  scorecard reports `"estimate_error_pct": 0.0` over hand-written costs.
  No harness-reported cost exists yet. The ±50% accuracy of the v1 estimate
  (`budgets_usd` by size, split across steps) is entirely unmeasured.
- Result: **NOT RUN — unmet, pending the real batch (Owner spend consent)**

### SC 4: a timestamped row per state change; final ledger state matches GitHub

- Check: offline, the state-machine and close tests.
- Evidence: `test_conductor_flow` 45 OK (`test_states_cannot_be_skipped`,
  `test_blocked_is_reached_only_through_an_answer`).
  `test_conductor` (`test_at_must_be_a_utc_timestamp_to_the_second`).
  `test_conductor_close` 17 OK
  (`test_close_carries_blocked_spend_scores_commits_and_asks`, which
  labels blocked issues through FakeGh). Matching against real GitHub
  state needs real PRs and issues.
- Result: **NOT RUN — unmet, pending the real batch (Owner spend consent)**

### SC 5: a distinct writer and reviewer per merged item; green checks on the merging commit

- Check: offline, the merge-precondition and merge-turn tests.
- Evidence: `test_a_reviewer_who_wrote_the_item_cannot_pass_it`,
  `test_a_reviewer_among_the_author_runs_is_refused`,
  `test_a_red_check_run_stalls_without_merging` and
  `test_the_eight_steps_run_in_order_and_record_merged`, all OK. The checks
  were faked through gh. gh's behaviour with `--squash` on a
  queue-required branch is unverified offline (breakdown Notes, row 0161).
- Result: **NOT RUN — unmet, pending the real batch (Owner spend consent)**

### SC 6: every Worker ran on the policy's model and effort (100%, from the ledger)

- Check: offline, the flag-composition and policy tests, plus
  `policy_compliance`.
- Evidence: `test_every_flag_is_composed_in_one_place`,
  `test_the_harness_runs_bound_by_policy_in_the_item_worktree`,
  `test_retry_up_runs_one_band_up` and `test_factory_config` 42 OK
  (`resolve_effort`). The demo scorecard reports `"policy_compliance": 1.0`
  over hand-written rows. No real `models_reported` value exists yet.
- Result: **NOT RUN — unmet, pending the real batch (Owner spend consent)**

### SC 7: a scorecard from ledger rows alone, appended to history; a malformed row fails with a problem string

- Check: offline, the scorecard tests and the demonstration above.
- Evidence: `test_conductor_close` 17 OK
  (`test_every_field_comes_from_the_ledger_and_its_costs`,
  `test_a_malformed_ledger_exits_nonzero_with_no_number`,
  `test_a_failing_scorecard_leaves_scorecards_byte_identical`). The demo's
  four `cd:` failures are quoted above, each exiting 1 with no number. The
  failure half of this criterion is shown offline. The criterion as written
  needs a scorecard for a real batch appended to history, and none exists.
- Result: **NOT RUN — unmet, pending the real batch (Owner spend consent)**

## Criteria & evidence: breakdown acceptance rows (offline)

Each row was test-first, so its `Accept:` line is pinned by tests through
the public interface. All 12 rows in `breakdown.md` are checked.

| Row | Acceptance, in short | Evidence (all OK in the runs above) | Result |
|---|---|---|---|
| 0153 | issue-keyed `wo` in cost_ledger, G, report, dashboard | `test_cost_ledger` 66 OK; full suite OK; gates 0 | PASS |
| 0154 | `resolve_effort`, `effort` table, F selftest | `test_factory_config` 42 OK; `selftest: ok`; template `"effort": {"mechanical": "low", ...}` | PASS |
| 0155 | ledger grammar, lock, ask/answer refusals, oldest ask | `test_conductor` 41 OK (`test_an_append_holds_an_exclusive_lock_on_the_ledger`); demo refusals | PASS |
| 0156 | priced plan, deferrals, reserved blocks, open | `test_conductor_plan` 21 OK (`test_every_deferral_has_its_own_line`, `test_a_config_problem_plans_nothing`) | PASS |
| 0157 | state machine, stall rule, wip cap, pause | `test_conductor_flow` 45 OK (`test_three_consecutive_failures_pause_dispatch`, `test_a_dead_runner_with_no_finishing_row_stalls`) | PASS |
| 0158 | metered headless runner | `test_conductor_run` 24 OK | PASS |
| 0159 | autorun honours `stop-after:` | `test_a_stop_after_line_stops_autorun_at_that_stage` OK; `lint: 0 problem(s)` | PASS |
| 0160 | merge precondition, train, gate blobs | `test_a_changed_gate_blob_is_refused_on_a_train` and the precondition tests OK | PASS |
| 0161 | the eight-step merge turn | `test_conductor_merge` 41 OK; `.gitattributes`: `docs/factory/costs.jsonl merge=union` | PASS |
| 0162 | scorecard from ledger alone, fails loudly | `test_conductor_close` OK; demo | PASS |
| 0163 | close a batch | `test_a_batch_with_an_item_in_flight_is_refused`, `test_carried_spend_is_never_appended_twice` OK | PASS |
| 0164 | `conduct` skill, vocabulary, packaging, all green | `"version": "0.8.0"`; `conduct` in `protocol.UTILITY_SKILLS`; suite `OK`, `lint: 0 problem(s)`, `gates: 0 problem(s)`, `selftest: ok` | PASS |

## Failures

None in the offline checks. The seven PRD success criteria are unmet, not
failed: they have not been run. They route to a real batch of at least four
owner-authored, `type:`- and `size:`-labelled issues once the Owner gives
spend consent. They do not route back to Implement.

## Not verified

- **All seven PRD-0013 success criteria on a real batch.** No headless
  Worker run, real PR, real merge, or GitHub state comparison has happened.
  Paid runs are forbidden by the autorun brief's Spend section.
- **The `conduct` skill's own behaviour** when an agent follows it: the
  one-at-a-time asks, launching background runners, and never writing an
  answer without the Owner's pick. Its four routing cases are unrun
  (LEDGER `draft`, no eval evidence). `trigger_eval.py` and `claude plugin
  eval` are paid.
- **Real harness metering.** The `claude -p --output-format json` result
  event is faked. The `total_cost_usd` path through `cli.read_execution` is
  covered only by existing tests of that reader.
- **The merge-queue path.** Whether this repo can enable a merge queue is
  the Owner's open question. gh's `--squash` against a queue-required
  branch is unverified.
- **`conductor.py plan`, `open`, `next`, `run`, `merge` and `close` against
  real gh and git.** They were exercised only through injected ports and
  scratch repos (tests), not in the demonstration, because each touches
  GitHub or git state.
- **Suite stability.** One full-suite run during Implement (M5) stalled
  once with no output, and a rerun passed. It did not recur in this stage's
  single run (2315 tests, OK, 241.5s). One clean run does not rule out a
  flake. `test_conductor_merge`'s real-git spawning (about 96 to 132s)
  makes it the likely place for a stall.
- **`--help`** prints usage and exits 2, the unknown-verb path. That is
  harmless, but no `--help` verb exists.
- **Post-review fixes (2026-10-11).** The review majors 1–3 fixes
  (review.md, "Post-review fixes") are verified only offline, by tests
  that failed first and a `make check` run under the Worker's scrubbed
  environment (rc 0). No real Worker has run under that environment.
  The "no push, no gh" boundary is enforced against a confused Worker
  only; against a hostile one it remains trust-based.
