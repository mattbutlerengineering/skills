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

## Post-review fixes (2026-10-11)

The Owner answered the fix-or-defer question through the orchestrator:
fix majors 1–3 test-first, and write major 4 up as a provisional ADR
for the Owner to accept or reject. An Implement pass did both. Each fix
began with a new test that was seen to fail. Each landed as its own
commit, with decisions logged in breakdown.md's Notes (2026-10-11).

- **Major: nothing ties the merged tree to the reviewed tree. Fixed in
  d75e6e2.**
  - What is enforced: the review run's runner reads the item branch
    head before the review Worker starts. The `reviewed` row records it
    as `reviewed_head`, and the merge refuses a reviewed row without
    one. A merge turn that starts from `ship` diffs that head's tree
    against the branch before any Conductor commit. It stalls,
    recommending `block`, when any path changed except the run's
    `review.md`, `release.md` or `costs.jsonl`. This covers both a ship
    Worker's commits and a review Worker's own changes. It is a tree
    diff, so rewritten history is caught too. A turn resumed from a
    `merging` stall skips the check, because no Worker runs between
    that stall and the resumed turn.
  - What is still trust-based: a change made in the worktree by
    something other than a Worker step, between the check and the push.
- **Major: build spend is not re-priced or capped. Fixed in d6391ab.**
  - What is enforced: the gate ask names the build's price (unchecked
    rows × the build ceiling, with the item re-priced) and records it
    as `build_usd`, so the gate answer is the build's spend consent.
    Every `run` checks this month's spend under the ledger lock before
    it launches. That spend is origin/main's rows plus every launched
    item branch's, each row counted once, plus in-flight ceilings and
    its own ceiling. If the total would pass `monthly_cap_usd`, nothing
    launches, and dispatch pauses behind a batch-level `spend` ask.
  - The shape differs from the architecture: the price is rows ×
    ceiling, not `size:` bands. Architecture amendments 10 and 11
    record this.
  - Gaps that remain: a fix that skips the gate gets no re-pricing ask
    (the cap still bounds it), and the review's one automatic fix build
    is not re-asked.
- **Major: the tool list does not enforce "no push, no gh". Fixed in
  aa0f612.**
  - What is enforced: `Bash(make *)` is now `Bash(make check)`. The
    Worker's environment loses every `GH_*`, GitHub token, askpass and
    inherited `GIT_CONFIG_*` or `GIT_SSH*` variable.
    - `GH_CONFIG_DIR` points at an empty temporary directory, so gh
      reports "not logged into any GitHub hosts", the keychain token
      included.
    - `GIT_SSH_COMMAND=false` stops any ssh push.
    - Env git config rewrites an http(s) push URL given on the
      command line or as a remote's `url` to an impossible path, and
      resets the credential helper. It does not rewrite a remote's
      explicit `pushurl`, so a token embedded there, or a `~/.netrc`
      entry, is not blocked (corrected per re-review R3).
    - The tests assert the env handed to the harness and run real git
      pushes against it. `make check` passes under that env (rc 0).
  - What is still trust-based: a hostile Worker can restore any of this
    from `python3`, read the keychain or an unencrypted ssh key, or call
    the GitHub API with a token it finds. The environment stops a
    confused Worker, not a hostile one, the same caveat as
    `CONDUCTOR_WORKER`.
- **Major: ADR-0036 condition 3 is reinterpreted with no amending ADR.
  Drafted as ADR-0085 in fe57137.** It is provisional, and ADR-0036's
  status is untouched. The Owner's acceptance (amend ADR-0036's status
  line) or rejection (drop the train branch) is still owed before Ship.

Gates after the four commits: `python3 -m unittest discover tests`
`Ran 2336 tests`, `OK`; `python3 lint.py` `lint: 0 problem(s) across 32
skills`; `python3 gates.py` `gates: 0 problem(s)`; `python3 gates.py
--selftest` `selftest: ok`.

The verdict above still stands for what is not fixed: the ADR-0085
decision is the Owner's, the ten minors stay deferred, and the
real-batch criteria are NOT RUN.

## Re-review (2026-10-11)

A second Review pass over the post-review commits (`git diff
e63b081..HEAD`: d75e6e2, d6391ab, aa0f612, fe57137, a902935), plus a
skim of the first-pass fixes dcce1a8, 7d07599 and 309d2e7 for
regressions. No paid run, no gh write, no merge. Every finding below
was reproduced; the one item not reproduced is labelled a suspicion.

### Do the fixes close their majors?

- **Major 1 (merged = reviewed), d75e6e2: mostly, with one hole
  (major R1 below).** The drift check at `conductor_merge.py:548-563`
  is a real tree diff of the committed branch against `reviewed_head`.
  A Worker's staged-but-uncommitted edit cannot slip past it: the
  runner's spend commit (`conductor_run.py` `_spend`) commits the whole
  index after every run, so it lands before the check. A merge turn can
  start only from `ship` or from a `merging` stall (`_stalled_problems`),
  so skipping the check on any other state opens no route. A drift
  stall answered `retry` re-runs `ship` and is checked again.
- **Major 2 (build re-priced, cap at launch), d6391ab: closed.**
  `run_step` is the only code that writes a launch row (grep for
  `state_row(`/`flow.move(`), and it now goes through `_launch` under
  the ledger lock. `_launch`'s pending-ask reuse excludes `merge` asks,
  so a pending train ask is never named as the cap pause. The gaps the
  fix commit names (no re-pricing for a gate-less fix, the automatic
  fix build, origin/main counted as of the last fetch) are stated
  honestly in breakdown.md's Notes.
- **Major 3 (no push, no gh), aa0f612: closed for the stated threat
  model, with one overstated claim (minor R3).** Probed under
  `worker_env(os.environ, ...)` on this machine: `gh auth status`
  reports "not logged into any GitHub hosts" and `gh api user` exits 4;
  `git credential fill` against a URL-scoped helper that hands out a
  token returns "terminal prompts disabled", so the `credential.helper`
  reset clears URL-scoped helpers too (the Owner's `~/.gitconfig` has
  `credential.https://github.com.helper = !gh auth git-credential`).
- **Major 4 (ADR-0036 reading), fe57137: well-formed.** ADR-0085 is
  `Status: provisional`, indexed as provisional in `docs/adr/README.md`,
  and ADR-0036 has no diff in `e63b081..HEAD`. 0085 exists on no other
  local or remote branch (checked every ref on 2026-10-11). It says
  plainly that the answer-row guard stops a confused Worker only, and
  that the ADR itself needs a human code-owner merge. Its decision 4
  describes the drift check accurately as a check at merge-turn start,
  but it inherits R1's hole.

### Findings

**Major R1. Uncommitted Worker edits under `factory/` or to
`.claude-plugin/plugin.json` are merged after the drift check.**
`_drift` diffs committed trees only (`conductor_merge.py:561`). The
merge turn then commits from the item worktree with `git add -A --
factory` (`conductor_merge.py:215`, manifest-conflict path) and `git
add -A -- .claude-plugin/plugin.json factory` (`conductor_merge.py:250`,
version bump, which runs whenever the item touched `skills/`). Both
pathspecs sweep in any unstaged or untracked file a Worker left there.
`update-manifest` also re-pins it. Scenario, reproduced with the
suite's own `TurnCase` (real git, local bare origin): the item commits
`skills/x/SKILL.md`, the review head is taken, the ship step commits
`release.md`, and the ship Worker leaves an untracked
`factory/templates/unreviewed.yml` (a plausible slip, since its brief
now says "commit nothing but release.md"). `merge_turn` returns `stall:
None` and the item reaches `merged`. `git show
<branch>:factory/templates/unreviewed.yml` prints the file, and `git
diff --name-only <reviewed_head> <branch>` lists it. So an unreviewed
change to the template payload stamped into product repos can merge.
The Owner's merge answer and green CI still stand in front of it, so
this is ranked major, not critical. Fix (not applied; route to
Implement): refuse or stall the turn when `git -C <worktree> status
--porcelain` is non-empty before the first Conductor commit, or stage
only the exact paths the Conductor wrote (`factory/manifest.json`,
`.claude-plugin/plugin.json`). The Notes' "still trust-based" list
(breakdown.md, 2026-10-11, major 1) does not name this route, and
neither does review.md's post-review section.

**Minor R2. The test pinning `reviewed_head` cannot tell the head
before the review run from the head after it.** The fake `Git` in
`tests/test_conductor_run.py` answers every `rev-parse` with `c0ffee`
(asserted at line 621). Mutation: pass a `rev-parse` of the branch
taken *after* the Worker ran to `record_verdict`, instead of
`ctx["head"]` (`conductor_run.py:526`). All 37 tests in
`tests.test_conductor_run` still pass. That ordering is what makes a
review Worker's own commits visible to the drift check, so a
regression there would go unnoticed. The code is correct today.

**Minor R3. "Every http(s) push URL is rewritten" is false for a
remote with an explicit `pushurl`.** `url.<base>.pushInsteadOf` is not
applied to `remote.<name>.pushurl`. Reproduced: with `worker_env`, a
remote whose `pushurl` is `https://127.0.0.1:9/o/r.git` tries the
network (`Failed to connect to 127.0.0.1 port 9`). The same URL given
on the command line is rewritten (`'/dev/null/conductor-worker-may-not-
push/...' does not appear to be a git repository`). The push still has
no credential, because the helper reset and `GIT_TERMINAL_PROMPT=0`
both hold. A token embedded in a configured `pushurl`, or a `~/.netrc`
entry (none exists on the Owner's machine), would get through. The
claim is overstated at `architecture.md:643`, `breakdown.md:427` (which
names `.netrc` as covered) and `review.md:334`. The test
`test_a_worker_push_to_any_remote_url_fails` pushes only to
command-line URLs, so it cannot see this.

**Minor R4. The after-review allowlist is wider than "this run's
artifacts".** `AFTER_REVIEW` (`conductor_merge.py`, above
`review_drift`) admits any run's `review.md` or `release.md`
(`docs/features/<any>/` and `docs/fixes/<any>/`, plus root
`docs/review.md` and `docs/release.md`). It also admits a whole-file
rewrite of `docs/factory/costs.jsonl`, not only appended rows:
`review_drift("#12", "h", ["docs/factory/costs.jsonl",
"docs/features/other/review.md"])` returns `None`. A ship Worker that
dropped spend rows would also lower `month_spend`'s figure for the
cap. Defer: docs-only and trust-based like the rest of the Worker
boundary. Hold costs.jsonl to an append-only diff if R1's fix touches
this code.

**Suspicion S1 (not reproduced). The Worker's shell may put a token
back.** Claude Code's Bash tool initialises its shell from the user's
profile, so an `export GH_TOKEN=...` in a profile would undo the
stripping inside the Worker's Bash. On this machine `~/.zprofile` and
`~/.zshrc` set none of the stripped variables, and
`~/.claude/settings.json` has no `env` block, so nothing reproduces
here. Worth one line in the conduct skill's prerequisites for other
Owners.

### First-pass fixes: no regression found

- dcce1a8 (in-flight launch refused): `_launch` calls
  `transition_problems` inside the lock, so it still applies.
- 7d07599 (dead merge turn stalls): the drift stall is queued before
  the move to `merging`, so it is not a dead turn.
- 309d2e7 (unchecked build row stalls): `run_step` is unchanged on
  that path.

### Mutation results (one line per fix, each restored with `git
checkout`, none committed)

| Mutation | Result |
| --- | --- |
| drift stall skipped (`if drift is not None` → `if False`) | killed: `test_a_code_change_after_the_review_stalls_the_merge` |
| reviewed-head refusal removed | killed: `test_a_reviewed_row_without_its_head_is_refused` |
| `record_verdict` stores a constant head | killed: 2 tests (flow, run) |
| head read after the review Worker | **survived** (R2) |
| cap never refuses (`month <= cap` → `True`) | killed: 3 `TestMonthlyCap` tests |
| in-flight ceilings ignored | killed: `test_in_flight_ceilings_and_item_branch_spend_count` |
| item branches' spend not read | killed: same test |
| build priced at one row | killed: 2 gate-ask tests |
| cap pause resets the failure streak | killed: `test_a_cap_pause_does_not_reset_the_failure_streak` |
| harness given the unscrubbed env | killed: `test_the_harness_gets_the_scrubbed_env_and_an_empty_gh_dir` |
| `Bash(make check)` → `Bash(make *)` | killed: `test_make_is_narrowed_to_make_check` |
| `GH_*` no longer stripped | killed: 2 `TestWorkerEnv` tests |
| `credential.helper` reset dropped | killed: `test_the_owners_git_config_entries_are_replaced` |

A seemingly surviving variant (`head = "c0ffee"` in `_prepare`) only
matches the fake's fixed answer, so it counts as equivalent, not as a
survivor.

### Gates (re-review)

- `python3 -m unittest discover tests`: `Ran 2336 tests`, `OK`.
- `python3 lint.py`: `lint: 0 problem(s) across 32 skills`.
- `python3 gates.py`: `gates: 0 problem(s)`.
- `python3 gates.py --selftest`: `selftest: ok`.

### Verdict (re-review)

Not ready to ship. Majors 2 and 3 are closed by tests that kill their
mutations. Major 1 is closed for committed changes, but R1 is a
reproduced route by which an unreviewed `factory/` change merges. It
needs a fix, or an explicit deferral by the Owner. Once R1 is fixed or
deferred, the run is ready to ship, subject to the Owner's decisions:
accept or reject ADR-0085, and give spend consent for the real-batch
criteria, which are still NOT RUN. R2–R4 are minor and may be deferred:
R2 and R3 are each a one-line test or doc fix, and R4 waits on R1's
fix.

## Re-review fixes (2026-10-11)

Implement fixed R1–R4, test-first, one commit each. Each new test was
seen to fail before its fix, or, for a test-gap or doc finding, its
mutation or limit was shown. No paid run, no gh write, no merge.
`skills/` is untouched, so the plugin version and manifest stay as
they were.

- **R1 (major): resolved in f9124f7.** A merge turn that starts from
  `ship` now stalls, recommending `block`, when `git status --porcelain
  --untracked-files=all` in the item worktree is non-empty. The check
  runs with the reviewed-tree diff, before any Conductor commit. The
  Conductor's own commits now stage by name only the files it writes:
  `factory/manifest.json`, `.claude-plugin/plugin.json` on a version
  bump, and the payload mirrors `update-manifest` refreshes
  (`factory_init.MIRRORS`). They never use `-A`. The re-review's
  scenario is now a test,
  `test_a_file_a_worker_left_uncommitted_stalls_the_merge`: the item
  touches `skills/`, and the ship Worker leaves an untracked
  `factory/templates/unreviewed.yml`. The turn stalls, and the file is
  on neither the branch nor `origin`. Two `TestConductorCommits` tests
  hold each half on its own, by calling the version bump and the
  manifest-conflict merge with a stray file present. All three failed
  before the fix.
- **R2 (minor): resolved in 22e1138.** A new test,
  `test_the_reviewed_head_is_read_before_the_review_worker_runs`,
  moves the fake branch head once the review Worker has run. It asserts
  that the reviewed row records the head from before the run. The
  re-review's mutant, which passes a `rev-parse` of the branch taken
  after the run to `record_verdict`, is now killed by that test. The
  file was restored with `git checkout`.
- **R3 (minor): resolved in 81d05e0, as an honest doc fix.**
  `architecture.md` amendment 12, breakdown.md's major-3 note, this
  file's post-review section and `worker_env`'s docstring now say that
  the `pushInsteadOf` rewrite covers a URL given on the command line or
  as a remote's `url`, but not a remote's explicit `pushurl`. They also
  say that a token embedded in a `pushurl`, or a `~/.netrc` entry, is
  not blocked. Nothing cheap closes this for every remote. Env config
  cannot unset a `pushurl`; adding one makes git push to both URLs.
  Moving `HOME` to hide `.netrc` would also hide the harness's own
  config. `test_a_configured_pushurl_is_not_rewritten` pins the limit,
  so a change in git's behaviour shows up.
- **R4 (minor): resolved in e6f8da9.** The run directory is now the
  one whose `verification.md` the item changed between origin/main and
  the reviewed head. Every item type runs `verify` before `review`.
  Only that directory's `review.md` and `release.md` may change after
  the review. `costs.jsonl` may change only by appending: its text at
  the reviewed head must be a prefix of the branch's.
  `test_another_runs_review_after_the_review_stalls_the_merge` (a
  foreign run's `review.md` and the root `docs/release.md`) and
  `test_a_dropped_spend_row_after_the_review_stalls_the_merge` both
  stall. A mutant that lets any rewrite of `costs.jsonl` through is
  killed, and so is one that allows the foreign paths. ADR-0085's
  draft decision 4 is updated to match. Two existing fixtures now
  commit a `verification.md` before the review.

### Gates (re-review fixes)

- `python3 -m unittest discover tests`: `Ran 2344 tests`, `OK`.
- `python3 lint.py`: `lint: 0 problem(s) across 32 skills`.
- `python3 gates.py`: `gates: 0 problem(s)`.
- `python3 gates.py --selftest`: `selftest: ok`.

### Verdict (re-review fixes)

Ready to ship, subject to the Owner's decisions. Every finding from
both review passes is fixed or recorded as a stated gap. What remains
is the Owner's to decide:

- accept or reject ADR-0085, and ADR-0084;
- merge the PR stack;
- give spend consent for the real batch, whose criteria are still NOT
  RUN.

Suspicion S1 (a profile that re-exports a token into the Worker's
shell) is still unreproduced on this machine.
