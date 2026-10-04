---
stage: ship
run: feature:factory-evolution-v1
date: 2026-10-04
assumptions:
  - "date: 2026-10-04 is the UTC date of this Ship pass (`date -u +%F` read 2026-10-04 at 01:36:55Z; the local PDT clock read 2026-10-03). This run dates its artifacts in UTC, as verification.md's first assumption records."
  - "Prepare and stop, per autorun-brief.md's 'Resumed 2026-10-03' section. This pass executed nothing externally visible: no merge, tag, push, PR, issue, label, comment, deploy, publish, plugin.json edit, manifest regeneration, `claude plugin` command or trigger operation. Its only write is this file."
  - "This file is written despite a not-ready verdict, on the orchestrator's instruction and the prepared-not-executed precedents (docs/fixes/a-dead-cli-scores-as-a-pass/release.md; draft PR #604's release.md). Under the protocol's artifact table its existence marks Ship complete, so `next` will offer Operate (see Orientation caveat)."
  - "Two readings are judged separately: (a) landing this branch's record on main, and (b) the run's Destination being met. (a) has no blocker in the branch's own lines: it is docs and ledger rows only, battery-green, secret-clean, and rehearsed to revert cleanly. (b) is not met: verification is red on four owner deferrals that no merge changes. The verdict 'not ready' is about (b), the run as a release; whether to merge (a) as a record is the owner's gate-3 call. The skill gives no default for this split, so it is logged here rather than decided."
  - "Version: no number is proposed. This branch touches nothing under skills/, factory/ or .claude-plugin/, so it needs no bump of its own. The bump since 0.2.0 is a single cross-run owner decision; draft PR #604's release.md already proposes 0.3.0 for it, and this file defers to that rather than competing."
  - "Rollback after merge offers two commands: a plain revert (removes the four costs.jsonl rows) and a revert that keeps them. The second is recommended because costs.jsonl is append-only and the rows record owner-session work that did happen. Both were rehearsed green. This is a judgement, not a skill default, so the choice is the owner's."
  - "The pilot trigger's live configuration and run history are unobserved by this pass, which may not touch the trigger API. Its post-release evidence is the orchestrator's capture of journal issue #590 (scratchpad groomer-journal-590.txt, fetched 2026-10-03T04:16:33Z), re-fetched read-only here at 2026-10-04T01:34Z and unchanged: three comments, the newest 2026-09-30T13:20:59Z."
  - "The installed-cache observation covers this machine only (~/.claude/plugins/cache/skills/idea-to-prod/0.2.0, installed 2026-09-30T04:42:24Z). Other machines, and stamped product repos, were not enumerated."
  - "The tracking-issue and PR wording in Release log part (b) is drafted by this pass from the #603/#604 and #605/#606 precedents. The orchestrator may reword prose, but not drop the `No work order:` line or the `Closes #<issue>` line, and the PR body must carry no work-order id token (the pipeline-board release's step 4 shows why)."
  - "The pairwise merge test covered only the five open branches that touch a file this branch touches or are sibling autorun PRs (#589, #595, #585, #604, #606), not every open PR."
---

# Release: factory evolution backlog seed (PRD-0006) — record landing, no plugin version

**Not ready. Prepared, not executed.**

- **Verdict: not ready as a release of the run.** `verification.md` is
  red (14 PASS / 4 FAIL, all four owner deferrals with no Implement
  route), and `review.md` carries four majors `open — needs owner
  decision`. The skill's rule is "never ship on a red verification".
- **What would make it ready:** the owner resolves the three deferrals
  (WO-0065, PRD-0006 §Success criteria: the hosting decision;
  WO-0069 and WO-0071, PRD-0006 §Success criteria: approving the two
  deferred triggers) and decides the four majors, after which Verify
  and Review re-run and this file is rewritten as an executed record.
  The ordering is in Owner-only steps below.
- **Landing this branch's record is a separate question** (see
  `assumptions:`). The branch is docs and ledger rows only. Nothing in
  it blocks a merge as a record, but merging does not make the run
  shipped. It is the owner's gate-3 call (ADR-0033 as amended by
  ADR-0036; `.github/CODEOWNERS` makes every merge owner-reviewed).
- **One part is already in production and no merge changes it:** the
  live, recurring, paid pilot trigger `factory-weekly-queue-groomer`.

## What "production" means for this run

**1. Most of the run is already on `main`.** These are the merged PRs
`review.md`'s Scope lists: #515 (ADRs 0070-0072 and the run's planning
artifacts), #525 (`--metrics`), #527 (detectors N and O, the template
markers and the PRD clarify step), #532 (the three roster protocol
docs), #563 and #583 (the merge-queue blocker and deferral).

**2. This branch's remaining increment** is three commits on
`origin/main` at 661ffc7. The worktree is clean, and the branch does
not exist on the remote:

```
$ git rev-parse HEAD origin/main
e4c0ec335d9cc6364a7cbf2a5f3b165ead07c5bc
661ffc705e18dbc77185ffd498a6cbf943c5d8e8
$ git ls-remote origin refs/heads/main refs/heads/feat/factory-evolution-queue-groomer
661ffc705e18dbc77185ffd498a6cbf943c5d8e8	refs/heads/main
$ git diff --stat origin/main...HEAD
 AGENTS.md                                          |   4 +-
 CLAUDE.md                                          |   4 +-
 docs/backlog.md                                    |   1 +
 docs/factory/costs.jsonl                           |   4 +
 docs/factory/doc-gardener-routine.md               |   5 +
 docs/factory/queue-groomer-routine.md              |  24 +-
 docs/factory/retro-reflect-routine.md              |   5 +
 .../features/factory-evolution-v1/autorun-brief.md | 129 +++++
 docs/features/factory-evolution-v1/breakdown.md    |  55 +-
 docs/features/factory-evolution-v1/review.md       | 397 +++++++++++++
 docs/features/factory-evolution-v1/verification.md | 626 +++++++++++++++++++++
 11 files changed, 1237 insertions(+), 17 deletions(-)
$ git diff --stat origin/main...HEAD -- skills/ factory/ .claude-plugin/ | tail -1
                                                   # (empty: nothing plugin-facing)
```

**3. What a merge newly delivers:**

- **To plugin users: nothing functional.** No skill, template, tool or
  manifest file changes. A later version-gated cache re-copy would
  carry these docs along, but no skill reads them.
- **To agent sessions that check out `main`:** the live queue-groomer
  routine and the daily improvement routine both check out `main`, as
  does every Claude Code session in this repo. They would newly read:
  - `CLAUDE.md`/`AGENTS.md`: the roster pointer changes from "triggers
    not yet created" to "only the queue groomer's trigger exists". That
    is an absence claim nobody has observed (review Major 3).
  - `docs/factory/queue-groomer-routine.md` §Trigger: today `main`
    tells the live routine that its own trigger is "Not yet created".
    The merge corrects that record.
  - The dated deferral line in the retro/reflect and doc-gardener docs.
  - Backlog line 77 (the deferred-trigger seed). The groomer surveys
    `docs/backlog.md`, so it becomes part of the groomer's input.
- **To the record:** this run's `verification.md`, `review.md`,
  `autorun-brief.md`, the breakdown's four checked rows and Notes, and
  four ledger rows.

**4. The one external effect that already happened** is the pilot
trigger `factory-weekly-queue-groomer` (`trig_01W5PgiQb4G2qwMXnNVFtACx`).
The orchestrating session created it on 2026-09-29 at 04:11 UTC. It is
live, recurring, paid, and outside the repo. Merging, or not merging,
changes nothing about it. Its next scheduled fire is **Wednesday
2026-10-07 13:17 UTC** (cron `17 13 * * 3`):

```
$ python3 -c "...now(utc) vs datetime(2026,10,7,13,17,tzinfo=utc)..."
2026-10-04T01:34:37+00:00 Wednesday 3 days, 11:42:22.891867 83.70635885194446
```

So it fires again about **3 days 11 hours 42 minutes** after this pass
(~83.7 h). The only way to stop it is an owner action (O1 below).

**5. Installed plugin caches: this run's skill changes have already
reached this machine, under `0.2.0`.**
- The installed cache was reinstalled on 2026-09-30, after #527 and
  #517 merged.
- Its skill-facing files are byte-identical to `origin/main` at 661ffc7.
- The marketplace clone is also at 661ffc7.

```
$ grep -n -A6 '"idea-to-prod@skills"' ~/.claude/plugins/installed_plugins.json
  "installPath": ".../cache/skills/idea-to-prod/0.2.0", "version": "0.2.0",
  "installedAt": "2026-09-30T04:42:24.360Z", "lastUpdated": "2026-09-30T04:42:24.360Z"
$ for f in gates.py skills/prd/SKILL.md skills/prd/TEMPLATE.md skills/architect/TEMPLATE.md skills/review/SKILL.md; do cmp -s "$f" "$C/$f" && echo "same $f"; done
same gates.py
same skills/prd/SKILL.md
same skills/prd/TEMPLATE.md
same skills/architect/TEMPLATE.md
same skills/review/SKILL.md
$ grep -c -E 'check_prd_coverage|check_needs_clarification' "$C/gates.py"
7
$ git -C ~/.claude/plugins/marketplaces/skills log -1 --format='%h %cI'; git -C ... rev-parse --is-shallow-repository
661ffc7 2026-09-29T11:24:05Z
true
```

`diff -rq` of the worktree against the cache differs only in this
branch's eight modified files (its three added files are absent from
the cache), plus the cache's `.in_use` marker.

Two consequences:
- #604's `release.md` (dated 2026-09-28) says installed caches were "not
  reached". That is out of date for this machine, which got #527 and
  #517 through a reinstall, not a version bump.
- Machines still on a pre-2026-09-22 `0.2.0` cache will not receive
  them until `plugin.json` changes. That is the cross-run bump decision
  (O7).

## Pre-flight

- [ ] **Verification green: FAIL.** `verification.md` has 14 PASS and 4
  FAIL. All four are owner deferrals that no Implement action can clear
  (`verification.md` §Failures):
  - Row 10: WO-0065 (PRD-0006 §Success criteria), the merge queue. It is
    blocked on hosting (the repo is user-owned, private, on the free
    plan), deferred 2026-09-28, and seeded at backlog line 76.
  - Rows 14 and 16: WO-0069 and WO-0071 (PRD-0006 §Success criteria),
    the two deferred triggers. Deferred 2026-09-29, seeded at backlog
    line 77.
  - Row 18: the epic #439 Destination, which follows from the three
    above.

  The run is not ready to ship as a release. See the verdict above for
  how landing the record differs.
- [x] **Review gate passes the soft gate; four majors carried as owner
  actions.**
  - `review.md` has "Four major, six minor, no critical."
  - Every finding reads `Standard: none`.
  - `docs/standards.json` has four statements, all `advisory`, and
    none is `enforced`:
    ```
    $ python3 -c "...for s in statements: print(slug, status)"
    adr0004-typed-ids-in-frontmatter advisory
    adr0032-one-way-mirror advisory
    eval-honesty advisory
    stdlib-only advisory
    $ grep -c enforced docs/standards.json
    0
    ```
  - The majors are owner actions O1-O4 below, in `review.md`'s Verdict
    order. They are not release steps.
- [x] **No secrets in the diff.**
  - **Pattern scan.** The 1237 added lines of `git diff
    origin/main...HEAD` were scanned for seven credential patterns,
    each run separately. Each pattern was also run against a
    positive-control file planted only in the scratchpad (`ship-control.txt`):
    ```
    pattern AKIA[0-9A-Z]{16} -> diff 0 / control 1
    pattern BEGIN [A-Z ]*PRIVATE KEY -> diff 0 / control 1
    pattern gh[pousr]_[A-Za-z0-9]{20,} -> diff 0 / control 1
    pattern xox[abprs]-[A-Za-z0-9-]{10,} -> diff 0 / control 1
    pattern sk-[A-Za-z0-9_-]{20,} -> diff 0 / control 2
    pattern eyJ[A-Za-z0-9_-]{10,}[.]eyJ -> diff 0 / control 1
    pattern (postgres|mysql|mongodb)(\+srv)?://[^ ]*:[^ ]*@ -> diff 0 / control 1
    ```
    Every pattern matched its planted line, so each zero means no
    match, not a blind scan.
  - **Keyword sweep.** `password|secret|token|api[_-]?key|credential|oauth`
    hit 15 added lines, and none is a credential:
    - four ledger rows with `"tokens": 0`;
    - the `oauth_scope_insufficient` error text and "this session's
      token" prose;
    - "password reset" in review's example scenario;
    - assumption and rubric prose.
  - **Identifiers:**
    ```
    $ grep -oE '(trig|env|req)_[A-Za-z0-9]{10,}' added-lines | sort | uniq -c
       2 env_012GDG167Tpz55u8MEpDkL2y
       2 req_011CfeDGQbQGam1pPRUbRjTQ
       2 req_011CfeDGUihvDbAedZPRsaQB
       2 req_011CfgKcdBTN4CPcybhCUvtD
       2 req_011CfgKcdnAnPg3tUGTPT5fK
      11 trig_01W5PgiQb4G2qwMXnNVFtACx
    ```
    - `trig_…` is the routine's id.
    - `env_…` is the id of the cloud environment the routine runs in.
    - `req_…` are API request ids from the two refused calls.

    None of them is a credential. They name resources, and acting on
    the trigger or environment needs the owner's authenticated session.
    The orchestrator's own token was refused even a read with HTTP 401.
    They do reveal account-resource names, in a private repo.
- [x] **Target config / mirrors: nothing to regenerate.**
  - Neither `CLAUDE.md` nor `AGENTS.md` is in `factory_init.MIRRORS`.
    The tuple's 26 entries are the root tools, six workflows,
    `.github/CODEOWNERS` and `Makefile`.
  - `grep -n -E "CLAUDE\.md|AGENTS\.md" factory_init.py` returns
    nothing.
  - The branch touches nothing under `factory/templates/**`.
  - Detector E is green at HEAD (`gates: 0 problem(s)`, below).
  - No `python3 factory_init.py update-manifest` is needed, and none
    was run.
  - The routine needs no new configuration in the repo. Its
    environment-side configuration is unobserved (Post-release).
- [x] **Migrations / data: append-only ledger, forward path tested.**
  `docs/factory/costs.jsonl` gains four rows, one per checked order,
  appended at the end:
  - WO-0069, WO-0070, WO-0071 and WO-0072 (PRD-0006 §Success criteria);
  - `owner-session:unmetered`, `cost: 0.0`, `at: 2026-09-29`.

  Forward path: a squash merge appends them. A simulated squash onto
  661ffc7 kept `gates: 0 problem(s)`; detector G pairs them with the
  checked rows.

  A revert would delete four rows from an append-only ledger. R2 below
  therefore offers a revert that keeps them (rehearsed green: G
  tolerates rows for unchecked orders). It also offers a plain revert
  (rehearsed green).

  There is a pairwise hazard with open PR #589 (the groomer's own PR):
  - Both append to the end of `docs/backlog.md`, and a test merge
    conflicts there.
  - Keeping both sides (line 77, then #589's eight lines) resolves it:
    `gates: 0 problem(s)` and `lint: 0 problem(s)`.
  - The other four branches tested merge clean, with gates green:
    #595, #585 (both touch `CLAUDE.md`/`AGENTS.md`), #604 and #606.
- [x] **Rollback plan concrete.** See below. The git-side revert was
  rehearsed in a scratch clone under the session scratchpad, and the
  clone was deleted afterwards. The trigger-side rollback is owner-only
  and was not exercised.
- **Version: unchanged, and the bump is a cross-run owner decision.**
  ```
  $ grep -n '"version"' .claude-plugin/plugin.json factory/manifest.json package.json
  .claude-plugin/plugin.json:4:  "version": "0.2.0",
  package.json:3:  "version": "0.1.0",
  factory/manifest.json:3:  "version": "0.2.0",
  $ git tag --list | wc -l
  0
  $ git log --oneline -1 -- .claude-plugin/plugin.json
  04c6efe feat(skills): pipeline-board — every active run on its stage, at a glance (#484)
  $ git log --oneline 04c6efe..origin/main -- skills/
  40ac3dd feat(gates): detectors N and O - clarification markers and PRD coverage (#527)
  69ecd19 feat(standards): implement Codex-style standards enforcement (Milestones A-E) (#517)
  ```
  - There is no tag convention.
  - Since the last bump, `skills/` changed through #527 (this run) and
    #517 (another run).
  - #604's `release.md` already proposes `0.3.0` for that bump and notes
    that it ships #527. This file proposes no number. The one bump is
    O7.
- **Battery at HEAD e4c0ec3, before writing this file:**
  ```
  $ python3 -m unittest discover tests 2>&1 | grep -E '^Ran |^OK|^FAILED'
  Ran 1793 tests in 22.252s
  OK
  $ python3 lint.py
  lint: 0 problem(s) across 25 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
  A green battery does not make verification green.

## Rollback plan

**R0: now (nothing pushed).** Nothing was executed, so nothing needs
undoing. The branch is local only.

**R1: draft PR open, not merged.** Close it, delete the remote branch,
and close the tracking issue as not planned:
```
gh pr close <PR> --delete-branch --comment "Withdrawn; release.md records the run as prepared, not executed."
gh issue close <ISSUE> --reason "not planned"
```

**R2: merged (squash commit `<SQUASH>` on `main`).** This is a docs
and data revert. No manifest regeneration is involved, because no
mirrored or template file is in the diff.

Recommended: keep the append-only ledger rows.
```
git fetch origin && git switch -c revert/factory-evolution-record origin/main
git revert --no-commit <SQUASH>
git checkout HEAD -- docs/factory/costs.jsonl      # keep the four owner-session rows
python3 -m unittest discover tests && python3 lint.py && python3 gates.py && python3 gates.py --selftest
git commit -m "revert: withdraw factory-evolution-v1's record landing (ledger rows kept, append-only)"
git push -u origin revert/factory-evolution-record   # then PR (No work order: line) and owner merge
```

Alternative, a full revert:
```
git revert --no-edit <SQUASH>
```

Rehearsal: a scratch clone, squash-merged onto 661ffc7 as `bba9517`.
- Plain revert: tree equals 661ffc7's tree; `gates: 0 problem(s)`,
  `selftest: ok`, `lint: 0 problem(s) across 25 skills`.
- Ledger-keeping revert: 10 files changed, 17 insertions(+), 1233
  deletions(-), and 0 lines staged for `costs.jsonl`. `gates: 0
  problem(s)`, `selftest: ok`, `lint: 0 problem(s) across 25 skills`,
  `Ran 1793 tests` / `OK`, and the four rows are still present.
- If later appends to `costs.jsonl` or `docs/backlog.md` (for example
  #589) make the revert conflict, keep every line that is not this
  commit's. Both files are append-only.

**R3: the pilot trigger (owner-only, independent of R1 and R2).**
- Stopping it is the only rollback of what is already in production.
- None of this was exercised: the trigger API refused the
  orchestrator's token twice, and this pass may not call it.
- Steps:
  1. Re-authenticate. In Claude Code run `/login` as
     mattbutlerengineering. The refusals were `HTTP 401
     oauth_scope_insufficient`, so the fix is a fresh login that grants
     the routines scope.
  2. Confirm what exists. Through the `/schedule` skill (RemoteTrigger),
     `list` all triggers, then `get` and `list_runs` for
     `trig_01W5PgiQb4G2qwMXnNVFtACx`. Delete any second
     queue-groomer trigger (review Major 3).
  3. Stop it, in one of two ways:
     - Pause, reversible: disable the trigger on its routine page,
       `https://claude.ai/code/routines/trig_01W5PgiQb4G2qwMXnNVFtACx`.
       The URL pattern comes from the daily routine's recorded manage
       URL. This pass did not open it.
     - Remove: delete it there or through `/schedule`.
  4. Record it with a human PR. Edit `docs/factory/queue-groomer-routine.md`
     §Trigger and the `CLAUDE.md`/`AGENTS.md` roster line to say the
     trigger is disabled or deleted, and when. The routine itself may
     not edit its own doc (§8).
- To stop it before its next fire, step 3 must finish before
  **2026-10-07 13:17 UTC**.

## Release log

### (a) Executed by this Ship pass: nothing external

- Read-only commands only:
  - `git` reads and `git ls-remote`;
  - read-only `gh api`, `gh pr view/list`, `gh issue view`, `gh label
    list`, `gh variable list`;
  - reads of the installed plugin cache and the marketplace clone.
- The battery above.
- A secret scan, with its positive control planted only in the
  scratchpad.
- The rollback and pairwise-merge rehearsals, in a scratch clone under
  the scratchpad (deleted afterwards).
- One write: this file.
- Not run: no commit, push, stash, PR, issue, label, comment, trigger
  call, `claude` CLI, `trigger_eval.py`, `charter_replay.py`,
  `plugin.json` edit or manifest regeneration.

Hiccups:
1. The first `grep -rn ... --include=*.md` for trigger ids aborted
   under zsh NOMATCH (`no matches found: --include=*.md`). It was
   re-run as `git grep` over `origin/main`. That found no trigger or
   environment id anywhere in `origin/main`'s `docs/` or `CLAUDE.md`,
   so this branch is the first to commit them.
2. While resolving the #589 conflict in the rehearsal, `git diff`
   printed the conflict markers before the resolution script ran. That
   was expected. The resolved file was checked by `gates.py` and
   `lint.py`, then the clone was reset and deleted.

### (b) Prepared: the orchestrator executes these next (operator-approved 2026-10-03)

Run them from the worktree, in this order, with
`SP=/private/tmp/claude-501/-Users-mbutler-github-skills/ee622348-c85b-44f3-8ebf-f048e89ab1b3/scratchpad`.
Write the bodies to the
scratchpad and pass them with `-F`/`--body-file`, never inline: a
backtick in a double-quoted argument executes.

1. Gate this file and commit it alone:
   ```
   python3 gates.py && python3 lint.py
   git add docs/features/factory-evolution-v1/release.md
   git commit -F "$SP/commit-release.txt"
   ```
   The subject line is `docs(factory-evolution): prepare PRD-0006's
   release — not ready, prepared and stopped (autorun)`. Give the body
   and trailer this branch's commits use.
2. Push:
   ```
   git push -u origin feat/factory-evolution-queue-groomer
   ```
3. Create the tracking issue:
   ```
   gh issue create --label type:chore \
     --title "Verify, review and prepare the release of PRD-0006 (factory evolution)" \
     --body-file "$SP/tracking-issue.md"
   ```
   Body: "Autorun resume 2026-10-03: land verification.md, review.md and
   release.md for docs/features/factory-evolution-v1/. Ship prepared and
   stopped; nothing was released. Verification has 4 failures (all owner
   deferrals) and review has 4 open majors awaiting owner decisions. The
   queue-groomer pilot trigger is live and unobserved since creation."
   Record the issue number as `<ISSUE>`.
4. Open the draft PR:
   ```
   gh pr create --draft --base main --head feat/factory-evolution-queue-groomer \
     --title "docs(factory-evolution): verify, review and prepare release for PRD-0006 (autorun)" \
     --body-file "$SP/pr-body.md"
   ```
   The body follows #604's shape:
   - one paragraph per artifact;
   - "Owner decisions this PR surfaces": O1-O7 below, by title;
   - the battery checklist;
   - this exact line: `No work order: stage artifacts and the pilot
     trigger's record for an already-implemented run; no breakdown row
     covers implement close-out, verify, review or ship.`;
   - `Closes #<ISSUE>`;
   - the PR attribution line.

   The body must contain no work-order id token: detector B's flipper
   pairs cited ids with mirrored issues, and this run has none. Record
   the PR number as `<PR>`.
5. Fill in "(b) results" below with what actually happened (numbers,
   CI rollup, any retry). Then commit and push that edit:
   ```
   git add docs/features/factory-evolution-v1/release.md
   git commit -m "docs(factory-evolution): record release.md's prepared steps as executed"
   git push
   ```
   Run `python3 gates.py` after the edit. Detector C reads run
   artifacts.

#### (b) results — placeholder, filled by the orchestrator

- Commit of this file: `<not yet run>`
- Push: `<not yet run>`
- Tracking issue: `<not yet run>`
- Draft PR: `<not yet run>`
- PR checks: `<not yet run>`

### (c) Owner-only steps

These are listed in `review.md`'s Verdict order. **O1-O3 come before
#589 is merged and before the two deferred triggers are approved.**

- **O1. Restore trigger read access and settle the double run** (Major
  3). Do R3 steps 1-2: `/login`, then `list`, `get` and `list_runs` for
  `trig_01W5PgiQb4G2qwMXnNVFtACx`. Confirm there is one trigger and one
  run per Wednesday. Delete any duplicate. Decide whether §1 of the
  queue-groomer doc gains a same-day guard ("the journal already has an
  entry dated today → stop").
  - Recommended: do O1 before merging this PR too. The merge publishes
    the unobserved "only the queue groomer's trigger exists" line into
    the `CLAUDE.md` every session loads.
  - If O1 finds a duplicate trigger, correct that line on this branch
    first.
- **O2. Amend the roster docs' pause precondition** (Major 2). In a
  human PR, amend §1 of `queue-groomer-routine.md`,
  `retro-reflect-routine.md` and `doc-gardener-routine.md`:
  - an unverifiable `FACTORY_PAUSED` means propose-only;
  - name the GitHub access the cloud environment really has;
  - correct each §Trigger's "`gh` and `git` only".
- **O3. Decide where the pilot's real cost is read** (Major 4). Either
  append a new `docs/backlog.md` line amending line 77's unblock
  condition (the account's usage for this trigger's sessions, not the
  journal), or amend §6 to say the journal's `Spend:` line excludes the
  session's own model usage.
- **O4. Decide detector O's granularity** (Major 1). Either (a) write an
  amending ADR that records section-level coverage as the bound, or
  (b) route to Implement for per-criterion coverage, using numbered
  criteria and a `§Success criteria N` citation form.
- **O5. Decide whether the trigger keeps running before O1-O3 land.**
  Its next fire is 2026-10-07 13:17 UTC. While #589 stays unmerged, it
  runs propose-only (§1.3), so its lane risk is low. Its cost per
  Wednesday is unobserved, and may be doubled (Major 3). To stop it,
  use R3 step 3.
- **O6. Merge or close this PR** (gate 3). If you merge #589 too:
  - resolve the `docs/backlog.md` conflict by keeping both appended
    blocks (rehearsed green);
  - merge #589 only after O1-O3.
- **O7. The plugin version bump, once, across runs.** `0.2.0` now covers
  #517 and #527. #604's `release.md` proposes `0.3.0` for that bump.
  This run adds nothing plugin-facing to it.
- **O8 (optional; review Minor 6). Append one dated correcting Note to
  `breakdown.md`**, as a new line at the end of Notes, never rewriting
  the 2026-09-29 Note:
  ```
  - 2026-10-04: **correction to the 2026-09-29 Note on WO-0069 and WO-0071 (PRD-0006 §Success criteria).** That Note says no `docs/backlog.md` seed was added; the same commit adds backlog line 77, which is the revisit seed for both.
  ```
  Ship may not edit `breakdown.md`. The owner or a later pass applies
  it and runs `python3 gates.py` afterwards.
- **Deferred minors 1-5** (detector O's date and setext handling, Notes
  as citing rows, N and indented code, `--metrics` on a non-results
  file): seed them as one maintenance run whenever it suits. `review.md`
  asks whoever closes this run to do it.

## Post-release checks

**Observed (read-only, this pass):**

```
$ gh api repos/mattbutlerengineering/skills/issues/590/comments --jq '.[] | "\(.id) \(.created_at) \(.body[0:80] | gsub("\n";" "))"'
5879079505 2026-09-28T21:30:26Z <!-- queue-groomer-state last-scan=2026-09-28T21:15:00Z --> **2026-09-28 — PR**:
5912133888 2026-09-30T13:19:51Z <!-- queue-groomer-state last-scan=2026-09-30T13:19:16Z --> **2026-09-30 — propo
5912152378 2026-09-30T13:20:59Z **Correction / addendum to the comment above (issuecomment-5912133888).**  Two t
$ gh api repos/mattbutlerengineering/skills/issues/590 --jq '"#\(.number) \(.state) \(.title) comments=\(.comments) updated=\(.updated_at)"'
#590 open Factory queue-groomer journal comments=3 updated=2026-09-30T13:21:38Z
$ gh pr view 589 --json state,mergedAt --jq '"#589 \(.state) merged=\(.mergedAt)"'
#589 OPEN merged=null
$ gh variable list
FACTORY_PAUSED	false	2026-09-28T15:31:01Z
```

- The 2026-09-28 entry predates the trigger, so it was a one-off
  session.
- The 2026-09-30 13:19:51Z entry landed two minutes after the first
  scheduled fire. It is indirect evidence that the trigger ran on
  schedule. It reports propose-only (#589 open) and "no `claude` CLI
  or model-API spend". It also reports no `gh` CLI and an unverified
  pause state.
- The 13:20:59Z entry reports a second, independent run for the same
  day.
- There is no entry for any later date. The trigger has had no
  scheduled fire since 2026-09-30, because the next is 2026-10-07.

These rest on the orchestrator's capture
(`groomer-journal-590.txt`, fetched 2026-10-03T04:16:33Z), re-fetched
here and unchanged.

**Not observed by anyone since the trigger's creating session:**
- the trigger's live configuration: model, cron, enabled state,
  connectors after the 04:11:48Z clear, and prompt;
- its run history;
- whether one or two triggers exist;
- the real model spend of either 2026-09-30 session.

The orchestrator's two attempts were refused:
- `get` and `list_runs`, `HTTP 401 oauth_scope_insufficient`, at
  2026-10-03T04:1xZ (`req_011CfeDGQbQGam1pPRUbRjTQ`,
  `req_011CfeDGUihvDbAedZPRsaQB`);
- the same calls at 2026-10-04T01:2xZ (`req_011CfgKcdBTN4CPcybhCUvtD`,
  `req_011CfgKcdnAnPg3tUGTPT5fK`).

**Prepared, for after O6 (merge):**
```
git fetch origin && git show origin/main:CLAUDE.md | grep -n 'only the queue groomer'
git show origin/main:docs/factory/queue-groomer-routine.md | grep -n 'trig_01W5PgiQb4G2qwMXnNVFtACx'
python3 gates.py && python3 gates.py --selftest
```
The next Wednesday's journal entry on #590 should then cite the
updated §Trigger and backlog line 77. Read it after 2026-10-07 13:17
UTC.

## Outcome

**Not shipped. Prepared, not executed.**
- The run is not ready as a release. Verification is red on four owner
  deferrals, and review has four majors open.
- The branch's increment is a record landing: docs and ledger rows,
  nothing plugin-facing, battery-green, secret-clean, revert rehearsed.
- The pilot trigger is the one piece of this run in production. It is
  live and unobserved since creation. Only the owner can see it or stop
  it (O1, R3).

## Orientation caveat

By the protocol's artifact table, this file's existence marks Ship
complete, and `next` will offer Operate.

**What that means:**
- The run's stage record is written.
- One thing is genuinely in users' hands and can be operated on: the
  pilot trigger, whose weekly journal is Operate's natural evidence.

**What it does not mean:**
- The run is not released. The draft PR is unmerged, and the plugin is
  unbumped.
- The Destination is not met.
- The four majors are not resolved.

Clearing the four failures goes through the owner (O1-O4, and the
hosting and trigger-approval decisions). Then Verify, Review and Ship
are re-entered by hand, and Ship rewrites this file as an executed
record. Operate's retro should not start before O1, because until then
there is no observable production evidence to retro on.

## Questions for the owner

1. Merge this PR before or after O1? Recommended: after. It is a quick
   re-login and list, and it is the only way to verify the absence
   claim the merge writes into `CLAUDE.md`/`AGENTS.md`.
2. Keep the pilot firing on 2026-10-07 13:17 UTC, or pause it until
   O1-O3 land (O5)? Recommended: keep it, provided #589 stays
   unmerged. It is then propose-only, and the next entry is the only
   new evidence the run can get. Pause it if the possible double spend
   matters more than one more data point.
3. On rollback after merge, keep or drop the four ledger rows (R2)?
   Recommended: keep them, because the ledger is append-only and the
   work happened.
4. Majors 1-4 (O1-O4) and the cross-run version bump (O7): yours to
   decide, as `review.md` and #604 frame them.
