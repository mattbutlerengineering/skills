---
stage: review
run: feature:orchestrator
date: 2026-10-11
assumptions:
  - "Autorun-driven: no live interview. Severities were ranked at this stage's own judgement; the Owner arbitrates them."
  - "The skill fixes critical findings before Ship and lets the user fix or defer majors. With no live user, this stage fixed the one critical and the two majors whose fix was small and test-first (one commit each, all gates re-run). The four majors that need a design decision are recorded, not fixed, and wait for the Owner's fix-or-defer call. Implement is the route for any the Owner wants fixed."
  - "The fix to the build-loop finding changed the fixture of one existing test (test_a_completed_build_writes_one_run_row_and_one_spend_row). That fixture showed a completed build that left its row unchecked, and the fix makes that run a stall. The test's Worker now checks its row off. Its assertions are unchanged, and it gains one: no stall."
  - "No paid model run, no gh write, no merge. Every finding below was reproduced (by test, a python3 probe, or a mutation run) or is cited at file:line with its scenario. The one finding not reproduced is labelled a suspicion."
  - "On resume, an uncommitted edit in conductor_merge.py turned out to be a mutation probe: wait_checks' 30-minute timeout replaced with `if False:`. This stage ran it (finding m8), then restored the file. It was never committed."
---

# Review: the Conductor, a batch orchestrator

## Scope

`git diff origin/main...HEAD` on `feat/orchestrator-implement` (PR #675,
stacked on #673 and #670), through 846b38c. The code got the closest read:

- `conductor.py`, `conductor_plan.py`, `conductor_flow.py`,
  `conductor_run.py`, `conductor_merge.py`, `conductor_close.py`, and their
  six test modules;
- the edits to `cost_ledger.py`, `cost_report.py`, `dashboard.py`,
  `factory_config.py`, `gates.py`, `protocol.py` and `factory.py`;
- `skills/conduct/SKILL.md`, the `stop-after:` edit to
  `skills/autorun/SKILL.md`, and `.gitattributes`.

They were read against `architecture.md` (Amendments included),
`breakdown.md`'s Notes, ADR-0036 and ADR-0084. `docs/standards.json` holds
only advisory statements, and no finding matches one except where cited.

Predecessor: `verification.md` exists. Its verdict is NOT RUN, because no
real batch has run yet (the Owner's spend consent). So this review covers
the mechanism, not real-batch behaviour.

Fix commits made by this stage: dcce1a8, 7d07599 and 309d2e7.

## Findings

### Critical: a build run that completes without checking its row off loops forever, spending without consent (fixed)

- Scenario: a feature item's build Worker is briefed with the first
  unchecked `breakdown.md` row (`conductor_run.py` `_work`). Suppose it ends
  with `subtype: success` but leaves that row unchecked, for example by
  saying "I can't do this because X". `conductor_flow._after_step` sees
  unchecked rows and reports `build` ready again (`conductor_flow.py:380`
  before the fix). The skill launches every ready step, so the loop
  repeats. Each run spends up to the step's ceiling, and none of it is
  covered by the Owner's spend answer. No stall fires, because the only
  "expected output" check is that `pr-body.md` exists. Stall rule 1
  (architecture: "a completed run carrying its step's expected output")
  was unimplemented for build.
- Standard: none
- Decision: fixed in 309d2e7. After a completed feature or fix build, the
  runner re-reads the branch. If the row it briefed is still unchecked, it
  stalls with "the build run completed but left WO-#### unchecked". Pinned
  by `test_a_build_that_leaves_its_row_unchecked_stalls`, which failed
  before the change.

### Major: a second runner could launch a step that is still in flight (fixed)

- Scenario: build → build is a legal move, and so is stalled → build. `run`
  needs seconds before it writes its launch row: a gh read,
  `git worktree add`, and `orientation_pack`. If another runner exits in
  that window, the skill runs `next` again and gets the same `build` as
  ready. The second `run` then passes `transition_problems` too. Both
  computed the same `seq` before the lock, so two Workers run in one
  worktree under one `run_id`, which also breaks the scorecard's
  run-to-spend join and the `wip_cap`.
- Standard: none
- Decision: fixed in dcce1a8. `transition_problems` refuses any move but
  `stalled` while the item's last state row carries a `run_id` that has no
  finishing `run` row. `merge_problems` now checks the ship run before the
  transition, so its own refusal text is unchanged. Pinned by
  `test_a_step_still_in_flight_is_never_launched_twice`, which failed
  before the change.

### Major: an interrupted merge turn left its item at `merging` forever, silently (fixed)

- Scenario: the session closes, or the Owner hits Ctrl-C, during
  `wait_checks`' 30-minute poll, or the process crashes after `merging` is
  written. Then `_candidate` returned nothing for `merging`: no ready step,
  no stall, nothing in `merge_due` (`conductor_flow.py`, the
  `state == "merging"` branch before the fix). `close` refuses the batch,
  and the only way out is an ask worded by hand and a `block` answer.
  PRD story 7 says "nothing silently stalls".
- Standard: none
- Decision: fixed in 7d07599. The `merging` state row records the turn's
  pid. `next` stalls an item whose merge turn is gone with no merged row,
  recommending `retry`, and a retry resumes it as `merge`. Pinned by
  `test_a_dead_merge_turn_stalls_and_resumes_as_a_merge` and a `pid`
  assertion in `test_the_eight_steps_run_in_order_and_record_merged`.
  Both failed before the change.

### Major: nothing ties the merged tree to the reviewed tree

- Scenario: the review step passes and writes `reviewed`. The `ship` step
  then runs in the same worktree, with the same `ALLOWED_TOOLS`, which
  include Edit, Write and `git commit` (`conductor_run.py:34`). Anything
  the ship Worker commits, say a "fix" to make a test pass, is merged
  unreviewed. `merge_problems` (`conductor_merge.py:98`) checks only
  ledger rows. The same goes for the review Worker: it can commit code
  changes and then pass them, and those commits are not counted as author
  runs. PRD story 6 and SC 5 ("a different Worker that reviewed it") hold
  in the ledger, not in the tree.
- Standard: none
- Decision: deferred to the Owner, because it needs a design answer. The
  recommended fix is to record the reviewed head sha on the `reviewed` row
  and refuse the merge when commits after it touch anything except the
  ship step's `release.md` and `costs.jsonl`, the merge of main aside.

### Major: build spend is not re-priced at the gate and not checked against the cap at run time

- Scenario: `plan` prices a feature at `budgets_usd[size]`, split equally
  across its five steps (`conductor_plan.py:157`). But build runs once per
  breakdown row, each run with the build step's full ceiling. A 10-row
  breakdown can spend 10× the build ceiling under the one spend answer.
  The architecture's contract (Interfaces, `plan`: "the blueprint gate ask
  re-prices the item from its breakdown rows' `size:` bands, and that ask
  doubles as the build-spend question") is not built. The gate ask
  (`conductor_flow.py:371`) carries no price, and Amendment 3 does not
  record that it was dropped. `run_step` never consults
  `work_queue.month_to_date`, so the monthly cap is checked only at plan
  time.
- Standard: none
- Decision: deferred to the Owner, as an undocumented deviation from the
  design. Either build the re-pricing gate ask plus a run-time cap check,
  or record its removal in an amendment. The critical fix above bounds
  the loop to one run per row. It does not restore spend consent.

### Major: the Worker's tool list does not enforce "no push, no gh"

- Scenario: `ALLOWED_TOOLS` (`conductor_run.py:34-37`) includes
  `Bash(python3 *)` and `Bash(make *)`, and the Worker inherits the
  Owner's full environment and gh/git credentials (`conductor_run.py:195`,
  `cli.child_env`). `make wo-failed ISSUE=<n>` and `make wo-merged` run
  gh label writes through `validator.py`. `python3 -c` can run
  `git push origin HEAD:main`, and main has no branch protection
  (docs/kb/main-unprotected.md). The brief's "never git push, never any
  gh" is prose. `test_every_flag_is_composed_in_one_place`
  (`tests/test_conductor_run.py:149`) asserts that no tool string
  contains "push" or "gh". It passes while both are reachable, so it pins
  the list, not the boundary. The architecture's own caveat ("an
  environment flag stops a confused Worker, not a hostile one") covers
  `CONDUCTOR_WORKER`, not this.
- Standard: none
- Decision: deferred to the Owner. The list was accepted as decision 9
  (breakdown Notes), so this stage did not narrow it. Cheapest hardening:
  narrow `Bash(make *)` to `Bash(make check)`. Then run Workers without gh
  credentials (`GH_TOKEN` unset and an empty `GH_CONFIG_DIR`) and with a
  disabled push URL that the runner overrides only for its own push.

### Major: ADR-0036 condition 3 is reinterpreted with no amending ADR

- Scenario: ADR-0036 says any PR touching `docs/adr/**`, `prd.md`,
  `architecture.md` or `docs/design/**` "still requires a human code-owner
  merge". Here an agent runs `gh pr merge` on such PRs. It does so on the
  Owner's in-session answer, or on a train answer when the gate blobs
  match (`conductor_merge.py:110` `cover_problems`, `_train_problems`).
  Condition 2's "pass is recorded on the PR" is also overridden: the
  review brief posts no comment. This changes how gate 3 is given. It is
  recorded only as an architecture assumption, and the architecture argued
  that it needed no ADR because it is reversible. The protocol ("Never
  rewrite": a changed decision gets an ADR that amends the old one) and
  ADR-0036's own "an agent cannot widen its own authority" point the
  other way. The code does enforce what architecture.md claims: an own
  merge answer, or a train with the earlier items merged and identical
  gate blobs, re-checked after the update.
- Standard: none
- Decision: deferred to the Owner, who was already asked to rule on the
  train reading. If accepted, a provisional ADR amending ADR-0036 is owed
  before Ship. If rejected, drop the train branch, as breakdown
  assumption 8 describes.

### Minor findings (all deferred: low blast radius; each is a candidate seed for a follow-up)

1. **Runner rows carry the launch time.** `conductor.main` takes `now`
   once, and `run_step` stamps the `run` row, the spend row and any stall
   ask with it (`conductor_run.py:373`, `:387`). A stall ask after a
   90-minute run is stamped 90 minutes early, so
   `merged_per_owner_wait_hour` counts the run as Owner wait. Fix: pass the
   clock.
2. **Duplicate issue numbers make two items.** Probe:
   `conductor_plan._issue_numbers(["#5", "#5"])` returns `[5, 5]`
   (`conductor_plan.py:300`). `plan_batch` then plans "#5" twice, with two
   blocks and a doubled estimate. `plan_entry` sees only the first.
3. **The `covers` and `gate_blobs` grammars are unchecked.** Probe: an ask
   row with `"covers": "#13"` passes `row_problems` (`conductor.py:118`),
   and `conductor_flow.consents(rows, "#1")` then counts #1 as covered,
   because `in` on a string matches a substring. The CLI always writes a
   list, so only a hand-written row gets there. But it is a field that
   grants consent, and the reader is meant to fail closed.
4. **The merge base can move between the check wait and the squash.** With
   no queue, `land` (`conductor_merge.py:447`) re-checks only the PR head.
   A merge that lands on main from outside the batch during the wait goes
   unchecked against this item. ADR-0036 condition 1 says "on the
   merge-result commit". Suspicion, related: `wait_checks`
   (`conductor_merge.py:427`) treats whatever check runs exist at a poll as
   the full set. This repo's PR workflows have no `needs:` jobs, so the
   race was not reproduced.
5. **A reused batch name crashes `open`.** If a closed batch's ledger is on
   main and its branch was deleted, `open(ledger, "x")`
   (`conductor_plan.py:265`) raises an uncaught `FileExistsError` after
   `git worktree add` has created the worktree.
6. **A failed close can append the scorecard twice.** `close` appends the
   scorecard (`conductor_close.py:310`) before `_record_close`. If the
   ledger write fails, the scorecard row is on disk, and a re-run appends
   a second one to the append-only history.
7. **"Expected output" is vacuous after the first step.** `pr-body.md` is
   left uncommitted and never removed, so from the second step on, the
   no-`pr-body.md` stall (`conductor_run.py:364`) can never fire. A verify
   run that writes no `verification.md` still advances to review.
8. **A broken wait timeout hangs the suite.** Mutation run: with
   `wait_checks`' timeout replaced by `if False:`,
   `test_checks_that_never_finish_time_out_after_30_minutes` hangs. It was
   killed by SIGALRM after 30s, exit 142, instead of failing. The fake
   clock only ever advances, so a broken bound loops forever. This is a
   plausible cause of the one unexplained full-suite stall in
   verification.md. That stall did not recur here: three full-suite runs,
   all OK, 45–112s, and `test_conductor_merge` alone took 14s, not 96–130s.
9. **Small grammar gaps.** `cost_ledger.py:192` still says "is not a
   WO-#### token" for a value that may now be an issue key.
   `factory_config.py:183` skips an `effort` that is not a dict, and band
   keys outside `BANDS`, so detector F passes `"effort": "high"`. The
   reader still fails closed on it.
10. **Complexity, reuse (cut-list).** `conductor_run.py:69` `_span`
    duplicates `conductor_plan.py:207` `_span` byte for byte; replace it
    with an import. `conductor_close.py:41` `_at` duplicates
    `conductor_flow.py:329` `_at`; replace it with an import. Net: about 6
    lines.

## Passes with no findings

- Security, injection: every subprocess call is an argv list, never a
  shell string. Batch names are slug-checked (`BATCH_NAME`), items
  `ISSUE_KEY`-checked, steps checked against `STEPS`. Issue titles and
  bodies reach only argv elements and the `-p` prompt. Only owner-authored
  issues are planned, and only a spec step sees the body. `answer` refuses
  under `CONDUCTOR_WORKER`, which the runner sets
  (`tests/test_conductor_run.py`, `env["CONDUCTOR_WORKER"]`).
- Ledger: appends read and write under one exclusive `flock`, and reads
  take a shared lock. Any malformed line fails the reader with file and
  line. No path rewrites or truncates the ledger or `scorecards.jsonl`.
- Merge turn, destructive steps: no force push anywhere. A non-mechanical
  conflict aborts the merge. Renumbering rewrites only lines the item
  added, renames only ADR files the item added, and refuses an existing
  target or an id past 9999. The version bump is idempotent per main
  value, and the manifest is regenerated in both places that need it. The
  gate re-check re-runs after the update.
- Repo conventions: stdlib only. Every module is under 800 lines (largest:
  `conductor_flow.py` at 606). `python3 one_owner.py` reports nothing in
  the diff's modules (its seven findings are all pre-existing). Problem
  strings carry the `cd:` prefix and are asserted exactly. plugin.json
  moved 0.7.3 to 0.8.0 with the `skills/` changes. The manifest was
  regenerated for the mirrored edits (detector E is green), and the
  conductor modules stay root-only as designed. LEDGER has `conduct` at
  `draft` with no eval evidence, and the four routing cases are unrun and
  claimed as nothing. Every `lean:` marker names its ceiling and trigger.
- Over-building against PRD-0013: no cut beyond m10. The merge-queue path
  and the renumbering machinery are both required by the PRD or the
  architecture (story 6 "where the repo has one"; story 4 and the
  protocol's merge-time renumbering).

## Gates (after the fixes and this artifact)

- `python3 -m unittest discover tests`: `Ran 2318 tests`, `OK`.
- `python3 lint.py`: `lint: 0 problem(s) across 32 skills`.
- `python3 gates.py`: `gates: 0 problem(s)`.
- `python3 gates.py --selftest`: `selftest: ok`.

## Verdict

Not ready to ship as is. The critical finding and two majors are fixed and
pinned by tests that failed first. Four majors wait for the Owner's
fix-or-defer decision:

- unreviewed post-review commits;
- the missing build re-pricing and run-time cap check;
- the tool list that does not enforce "no push, no gh";
- the ADR-0036 condition-3 reading with no amending ADR.

The last two touch consent and authority, which this PRD exists to
protect. Separately, the real-batch success criteria are still NOT RUN,
pending the Owner's spend consent (verification.md). The ten minors are
deferred with reasons above.
