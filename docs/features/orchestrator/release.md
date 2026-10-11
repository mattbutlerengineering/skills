---
stage: ship
run: feature:orchestrator
date: 2026-10-11
assumptions:
  - "Autorun-driven: no live interview. The brief's Release authorization is 'Prepare and stop': no merge, tag, publish or deploy. This stage ran read-only pre-flight, simulated the merges without touching any branch, and committed this file (and the launch brief) to feat/orchestrator-implement only. Nothing in the Release steps below was executed."
  - "Review's final verdict is 'ready to ship, subject to the Owner's decisions', with no unfixed critical. The soft gate passes; the Owner's decisions are listed as gates on the release, not skipped."
  - "Conflict default for #675 after #670 and #673 are squashed: take the branch side, because a stacked branch is strictly newer than the parents it contains (the repo's proven stack-merge procedure). The simulation shows that resolution reproduces #675's own tree exactly."
  - "Rollback default: revert the three squash commits and move the plugin version forward (0.8.2), never back to 0.7.3, because installed plugin caches refresh only when the version moves."
  - "docs/launch-demo.json says when: ship, so the launch-demo hook ran. Nothing has shipped, so the copy describes the release as prepared and states that it is unproven on a real batch."
  - "Stale worktree default: recommend discarding it, because its draft is an earlier Architect attempt that #670 supersedes. This stage did not touch it."
---

# Release: the Conductor, plugin 0.8.1 (PRs #670, #673, #675)

Production for this repo is the installable plugin. Work reaches users
when it is merged to `main`, and installed caches pick it up when
`.claude-plugin/plugin.json`'s version moves. Product repos stamped
with the factory get the mirrored payload when they next run the
factory's update. This release takes the plugin from 0.7.3 (origin/main)
to 0.8.1.

The autorun brief authorizes "Prepare and stop". This stage merged,
tagged, published and deployed nothing. It changed no PR, label or
issue. Every step under Release steps is the Owner's.

## Pre-flight

- [x] Verification green (no unresolved failures). `verification.md`
  lists no failures in its offline checks. Its seven PRD-0013 success
  criteria are **NOT RUN — unmet, pending the real batch (Owner spend
  consent)**. They are not failed. They stay unmet after this release
  (see "Real-batch criteria" below).
- [x] Review: no unfixed critical. The final verdict (`review.md`,
  "Verdict (re-review fixes)") is "Ready to ship, subject to the
  Owner's decisions". Minors m1–m10 are deferred.
- [x] No secrets in the diff; target config present. A secret-pattern
  scan of `git diff origin/main` (key, secret, token and password
  assignments with a literal of 12 or more characters) found nothing.
  No file in the diff is a migration, `.env` or secret file. The
  Conductor needs only `factory.json`, which the diff extends with an
  `effort` table (`factory/templates/factory.json`).
- [x] Migrations and data changes have a tested forward path. There is
  no schema migration. The cost ledger accepts issue-keyed rows
  (ADR-0084) alongside work-order rows, and old rows still parse
  (`test_cost_ledger`, 66 tests). Batch ledgers are new files under
  `docs/factory/batches/`, and nothing reads them until a batch runs.
- [x] ADR numbers are free on the base branch and indexed. origin/main
  (cc6ef9f) ends at ADR-0083. The run adds ADR-0084 (in #670) and
  ADR-0085 (in #675). Both are indexed in `docs/adr/README.md` as
  `provisional`. No open PR other than this stack touches `docs/adr/`:
  `gh pr list --state open` lists only #670, #673 and #675. One
  collision risk sits outside git, in the stale worktree (Owner
  decision 6).
- [x] Rollback plan concrete (commands below).

### Checks run (2026-10-11, this worktree, `feat/orchestrator-implement` at b5fe2d8)

```
$ python3 -m unittest discover tests
Ran 2344 tests in 55.711s

OK
exit=0

$ python3 lint.py
lint: 0 problem(s) across 32 skills
lint exit=0

$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
gates exit=0
```

Detector B skips locally because there is no PR event payload. Each
PR's CI ran it (below).

### PR state and CI (read-only: `gh pr view`, `gh pr checks`)

| PR | base ← head | head sha | mergeable | draft |
| --- | --- | --- | --- | --- |
| #670 | main ← docs/orchestrator-architect | 7670750 | MERGEABLE | no |
| #673 | docs/orchestrator-architect ← docs/orchestrator-decompose | 75e3bf7 | MERGEABLE | no |
| #675 | docs/orchestrator-decompose ← feat/orchestrator-implement | b5fe2d8 | MERGEABLE | no |

Each local branch head equals its `origin/` head.

```
#670  check pass 31s | merged-label skipping | needs-review-label skipping | review skipping
      check pass 30s | merged-label skipping | needs-review-label skipping | review skipping
#673  check pass 27s | needs-review-label pass 7s | review pass 36s | merged-label skipping
      check pass 31s | merged-label skipping | needs-review-label skipping | review skipping
#675  check pass 35s | review pass 35s | merged-label skipping | needs-review-label skipping
      check pass 35s | merged-label skipping | review skipping | needs-review-label skipping
(gh pr checks exit 0 for all three)
```

`main` has no branch protection (`docs/kb/main-unprotected.md`), so
green checks are a convention the merger keeps. GitHub does not
enforce them.

Each PR body carries its traceability lines, so detector B holds:

- #670: a `No work order:` line and `Closes #671`;
- #673: a `No work order:` line and `Closes #672`;
- #675: a `No work order:` line and `Closes #674`.

### Merge-safety: the stack chained against origin/main

The merge order is known, so the stage simulated it as
`docs/kb/cross-pr-merge-hazards.md` describes. For each PR, bottom-up,
it ran `git merge-tree --write-tree <acc> <pr-head>` and wrapped the
tree with `git commit-tree -p <acc>`. That is a single-parent commit,
the shape a squash leaves. No branch, ref or worktree of the stack was
touched.

```
start origin/main cc6ef9f  (origin/main is an ancestor of #670's head; 0 commits on main since)
#670 merge-tree rc=0 tree=fee8f75  == #670 head tree   sim commit 21fe9d3
#673 merge-tree rc=0 tree=86bce29  == #673 head tree   sim commit ba7bacf
#675 merge-tree rc=1  CONFLICT:
  CONFLICT (content): Merge conflict in docs/adr/README.md
  CONFLICT (add/add): Merge conflict in docs/features/orchestrator/architecture.md
  CONFLICT (add/add): Merge conflict in docs/features/orchestrator/breakdown.md
```

The #675 conflict is the squash-stack shape, not a real disagreement.
After #670 and #673 are squashed, main holds their content but not
their commits. The merge base of the new main and #675 is therefore
still cc6ef9f, so each file that both #673 and #675 added or edited
looks like an add/add. Resolved branch-side, as the stack procedure
does it:

```
resolved tree 2c398c6  == #675 head tree 2c398c6   sim commit 040ef10
```

The triad was run at each link. #670 and #673 were run in a detached
scratch worktree at the simulated commit, and that worktree was then
removed. The final link's tree is identical to this worktree's tree,
so the checks above cover it.

```
link #670 (21fe9d3): Ran 2109 tests OK | lint: 0 problem(s) across 31 skills | gates: 0 problem(s) | selftest: ok
link #673 (ba7bacf): Ran 2109 tests OK | lint: 0 problem(s) across 31 skills | gates: 0 problem(s) | selftest: ok
link #675 (tree 2c398c6): Ran 2344 tests OK | lint: 0 problem(s) across 32 skills | gates: 0 problem(s) | selftest: ok
```

This verdict was taken against origin/main at cc6ef9f on 2026-10-11.
It expires as soon as anything else lands on main, so re-run it then.
This file's own commit adds new paths only (`release.md` and the
launch brief), so it adds no conflict.

## Owner decisions that gate the release

The release steps must not start until each of these is answered.

1. **ADR-0084 (cost ledger keyed by issue): accept or reject.**
   Recommended: accept. The Conductor's ledger rows, detector G and the
   cost report all depend on it. If accepted, flip its status to
   `accepted` and ADR-0034's status line to "amended by ADR-0041,
   ADR-0084", with matching index rows. If rejected, the
   issue-keyed-row work in #675 has to be reworked before #675
   merges.
2. **ADR-0085 (an Owner answer executed by the Conductor is the human
   merge): accept or reject.**
   - If accepted: set ADR-0085's status to `accepted`. Amend ADR-0036's
     status line from `accepted` to "accepted; amended by ADR-0085",
     and its index row to match. The Decision section stays as
     written.
   - If rejected: drop the train branch of the merge precondition, as
     breakdown assumption 8 describes. The Conductor then merges only
     on each item's own answer. Delete ADR-0085 and its index row.
   - Either way, this is a change to #675 before it merges, made on
     the branch.
3. **The merge-consent reading.** These three PRs touch `docs/adr/**`
   and the run's `architecture.md`, so ADR-0036 condition 3 needs a
   human code-owner merge. The Owner merges them, or tells an agent to
   in an explicit in-session answer. A goal alone does not authorize
   `gh pr merge`. ADR-0085, even if accepted, covers merges the
   Conductor performs inside a batch. It does not cover these PRs.
4. **Review's deferred minors m1–m10.** Recommended: ship with all ten
   deferred and file each as a seed or issue afterwards. Each one is
   low blast radius and inert until a real batch runs:
   - m1: runner rows stamped with the launch time;
   - m2: duplicate issue numbers make two items;
   - m3: unchecked `covers` and `gate_blobs` grammar;
   - m4: the merge base can move during the check wait;
   - m5: reusing a batch name crashes `open`;
   - m6: a failed close appends the scorecard twice;
   - m7: the expected-output stall goes vacuous after step one;
   - m8: a broken wait timeout hangs the suite;
   - m9: small grammar gaps;
   - m10: two duplicated helpers.

   Suspicion S1 (a shell profile that re-exports a token into the
   Worker's shell) is still unreproduced.
5. **Closing issues #671, #672 and #674.** #670's base is main, so its
   `Closes #671` fires on merge. GitHub honours `Closes` only on a
   merge into the default branch (`docs/kb/pr-body-contract.md`). So
   `Closes #672` and `Closes #674` fire only if #673 and #675 are
   retargeted to main before they merge, as the steps below do. If
   either merges into its stacked parent instead, close its issue by
   hand. After the stack lands, check all three with
   `gh issue view <n> --json state`.
6. **Stale worktree `.claude/worktrees/agent-a69e0f4d056b70568`.** It
   is on branch `worktree-agent-a69e0f4d056b70568` at 008dd34 (the
   PRD-0013 merge). Read-only `git status --short`:

   ```
    M docs/adr/README.md
   ?? docs/adr/0084-the-cost-ledger-keys-a-run-by-issue-when-it-has-no-work-order.md
   ?? docs/adr/0085-an-owner-answer-in-session-is-the-merge-decision.md
   ?? docs/features/orchestrator/architecture.md
   ```

   This is an uncommitted earlier Architect draft. Its ADR-0084 has the
   same file name as #670's. Its ADR-0085 has a different slug from
   #675's, so committing it later would collide on the number.
   Recommended: discard it (`git worktree remove --force` on that path,
   then `git branch -D worktree-agent-a69e0f4d056b70568`) once the
   Owner confirms nothing in it is wanted. This stage did not touch it.
7. **Spend consent for the real batch.** This does not gate the merge.
   It is the only route to the PRD's success criteria (see
   "Real-batch criteria" below).

## Release steps (prepared, not executed)

These are the repo's stack procedure, bottom-up. Retarget each child
to main through REST before its parent's branch is deleted, because
deleting a base branch closes its child PR. `gh pr edit` does not work
on this repo.

```
# 0. Re-check: nothing new on main, all three green
git fetch origin && git log --oneline origin/main -1     # expect cc6ef9f, else re-run the chain simulation
gh pr checks 670 && gh pr checks 673 && gh pr checks 675

# 1. Apply the Owner's ADR decisions (1, 2) on feat/orchestrator-implement, commit, push, wait for green

# 2. Retarget #673 to main, then squash-merge #670
gh api repos/mattbutlerengineering/skills/pulls/673 -X PATCH -f base=main
gh pr merge 670 --squash --delete-branch        # closes #671

# 3. Retarget #675 to main, then squash-merge #673 (merges clean, per the simulation)
gh api repos/mattbutlerengineering/skills/pulls/675 -X PATCH -f base=main
gh pr merge 673 --squash --delete-branch        # closes #672 (base is main now)

# 4. #675 now conflicts with main (3 files, the add/add shape). Resolve branch-side on its branch:
git -C .claude/worktrees/orchestrator-implement fetch origin
git -C .claude/worktrees/orchestrator-implement merge origin/main
git -C .claude/worktrees/orchestrator-implement status --short | grep -E '^(UU|AA|U.|.U)'   # enumerate every conflict
git -C .claude/worktrees/orchestrator-implement checkout --ours -- docs/adr/README.md docs/features/orchestrator/architecture.md docs/features/orchestrator/breakdown.md
git -C .claude/worktrees/orchestrator-implement add docs/adr/README.md docs/features/orchestrator/architecture.md docs/features/orchestrator/breakdown.md
git -C .claude/worktrees/orchestrator-implement commit --no-edit
#    if factory/manifest.json also conflicts: delete any .orig/.rej, then python3 factory_init.py update-manifest
python3 -m unittest discover tests && python3 lint.py && python3 gates.py && python3 gates.py --selftest
git -C .claude/worktrees/orchestrator-implement push            # wait for #675 checks green

# 5. Squash-merge #675
gh pr merge 675 --squash --delete-branch        # closes #674 (base is main)

# 6. Confirm on main
git fetch origin && git checkout --detach origin/main
python3 -m unittest discover tests && python3 lint.py && python3 gates.py && python3 gates.py --selftest
grep '"version"' .claude-plugin/plugin.json      # expect 0.8.1
gh issue view 671 --json state; gh issue view 672 --json state; gh issue view 674 --json state
```

No tag. The repo versions by `plugin.json` alone, and #675 already
carries 0.8.1. That version was bumped from 0.8.0 in d6391ab, after
verification quoted 0.8.0.

In step 4, a merge of main into the branch makes the branch "ours". So
`git checkout --ours` keeps the branch's version, which is what the
simulation resolved to. Expect the merge commit's tree to equal
2c398c6 plus this file and the launch brief.

## Rollback plan

Door: two-way. Every change is code, docs and a plugin version, and
each is undone by reverting the three squash commits. The one-way
parts are outside this release:

- a real batch's spend and merges;
- the ADR acceptances, which are status-line edits, superseded by a
  new ADR rather than reverted.

Blast radius:

- Every installed copy of the plugin picks up the `conduct` skill and
  the changed `cost_ledger`, `cost_report`, `factory_config`, `gates`
  and `protocol` tools on its next update.
- Every stamped product repo that runs the factory update gets the
  changed mirrored payload under `factory/templates/tools/factory/`
  and the new `effort` table in `factory.json`.
- Nothing runs a batch, and nothing spends, until an Owner invokes
  `conduct` and answers its spend ask.

(#670's PR body makes the two-way call for its docs-only scope. #675's
body has no Door or Blast radius line. This file is the record for the
whole stack.)

```
# Before any merge (current state): nothing to undo. Close nothing; the PRs stay open.

# After the merges: revert the three squash commits on main, newest first
git fetch origin && git switch -c revert/orchestrator origin/main
git revert --no-edit <squash-675> <squash-673> <squash-670>
# Move the version forward so installed caches refresh (never back to 0.7.3)
#   edit .claude-plugin/plugin.json: "version": "0.8.2"
rm -f $(git ls-files --others --exclude-standard | grep -E '\.(orig|rej)$')
python3 factory_init.py update-manifest            # detector E: manifest == payload
python3 -m unittest discover tests && python3 lint.py && python3 gates.py && python3 gates.py --selftest
git add .claude-plugin/plugin.json factory/manifest.json && git commit -m "revert: the Conductor stack (plugin 0.8.2)"
git push -u origin revert/orchestrator && gh pr create --base main   # body: "No work order: rollback" + Closes #<rollback issue>
# Reopen the closed tracking issues
gh issue reopen 671; gh issue reopen 672; gh issue reopen 674
# Installed caches: claude plugin update idea-to-prod@skills
#   (or: claude plugin uninstall idea-to-prod@skills && claude plugin install idea-to-prod@skills)
# Stamped repos already updated to the 0.8.1 payload: re-run the factory update after 0.8.2 lands
```

A partial rollback is also two-way. If only #675 has merged badly,
revert its squash commit alone. #670 and #673 are docs.

## Release log

1. Pre-flight triad in this worktree → `Ran 2344 tests … OK`, `lint: 0
   problem(s) across 32 skills`, `gates: 0 problem(s)`, `selftest: ok`
   (quoted above).
2. `gh pr view` and `gh pr checks` for #670, #673 and #675 (read-only)
   → all three OPEN, MERGEABLE and not draft. Every check is pass or
   skipping.
3. Chain simulation with `git merge-tree` and `git commit-tree`
   (read-only) → #670 and #673 merge clean. #675 has three add/add or
   content conflicts. The branch-side resolution reproduces #675's
   tree exactly, and every link is green.
4. Stale worktree inspected read-only → uncommitted draft with
   colliding ADR-0084 and ADR-0085 files (Owner decision 6).
5. Launch brief (`docs/launch-demo.json`, `when: ship`): the
   launch-demo skill ran. Its tool's reason lines and verdicts:
   - `config` → `launch-demo: 0 problem(s)`.
   - `probe` → `READY`, `launch-demo: 0 problem(s)`.
   - The happy path is source 2: the commands verification ran (its
     offline ask and answer refusals). They were replayed against a
     throwaway copy of the tools in a `mktemp -d` directory, so the
     recording wrote nothing to the repo.
   - `render orchestrator` → `launch-demo: wrote
     docs/launches/orchestrator/demo.tape`, `launch-demo: wrote
     docs/launches/orchestrator/launch.mp4` (h264 and aac,
     `duration=47.924989`), `PRODUCED`, `launch-demo: 0 problem(s)`.
   - Hiccups, from frames checked by eye: the typing runs ahead of
     command output, so a stray echoed character appears before some
     output lines ("pcd:", "Ccd:"). The final scene ends while the
     ledger `cat` is still being typed. Both are cosmetic, and the
     storyboard was not re-cut.
   - The copy says the release is prepared and unproven on a real
     batch.
6. This file and the launch brief committed to
   `feat/orchestrator-implement` and pushed. That is the only push. No
   merge, tag, PR edit, label or issue change.

## Release executed (2026-10-11)

The Owner answered "Merge all three" in session (2026-10-11), after
accepting ADR-0084 and ADR-0085 and discarding the stale worktree. The
orchestrator then ran the steps above:

1. `origin/main` re-checked at cc6ef9f, unchanged since the simulation;
   `gh pr checks` pass or skipping on all three.
2. #673 retargeted to main via `gh api -X PATCH`, then #670 squashed →
   b6548a0. #671 closed.
3. #675 retargeted to main, #673's checks re-run green, #673 squashed →
   569695a. #672 closed.
4. `git merge origin/main` in #675's worktree → conflicts in
   `docs/adr/README.md`, `architecture.md`, `breakdown.md` (as
   simulated) and `docs/adr/0084-…md` (the acceptance edit, added after
   the simulation). All four resolved branch-side; the resulting tree
   was byte-identical to the already-verified branch head 72c1593.
   Pushed as 3c9193e; checks green.
5. #675 squashed with `--match-head-commit 3c9193e` → 09ab22e. #674
   closed.

## Post-release checks

Run on `main` at 09ab22e:

- `python3 -m unittest discover tests` → `Ran 2344 tests in 53.809s`,
  `OK`; `python3 lint.py` → `lint: 0 problem(s) across 32 skills`;
  `python3 gates.py` → `gates: 0 problem(s)`; `--selftest` → `selftest: ok`.
- `.claude-plugin/plugin.json` → `0.8.1`.
- `claude plugin update idea-to-prod@skills` → `Plugin "idea-to-prod"
  updated from 0.7.3 to 0.8.1`; the cache holds
  `0.8.1/skills/conduct/SKILL.md`.
- `python3 conductor.py next nosuchbatch` → `cd: no batch ledger at
  docs/factory/batches/nosuchbatch/ledger.jsonl`, `cd: 1 problem(s)`,
  exit 1 (the CLI loads and fails closed; no batch, no spend).
- #671, #672 and #674 → CLOSED.

The checklist as prepared:

- Step 6 above: the triad on origin/main, and `plugin.json` at 0.8.1.
- `claude plugin update idea-to-prod@skills`, then in a fresh session
  confirm that `/conduct` loads from the 0.8.1 cache and that
  `python3 conductor.py next <batch>` prints its usage or problem
  lines. That is a smoke check, with no batch and no spend.
- `gh issue view` for #671, #672 and #674 shows CLOSED.

### Real-batch criteria

All seven PRD-0013 success criteria remain **NOT RUN — unmet, pending
the real batch (Owner spend consent)**. Each needs a real batch of four
or more owner-authored issues labelled with a type and a size, run
through `conduct`. That spends money, and the brief forbids it without
the Owner's consent. Merging this stack does not meet them. It only
makes the mechanism available.

## Outcome

Executed 2026-10-11 (09ab22e). It was first prepared, not executed. Pre-flight is green, and the stack's merge
order is simulated: #675 needs a branch-side conflict resolution after
#673, and the steps above give it. The Owner decisions 1–6 gate the
merges, and decision 7 gates the success criteria. No merge, tag,
publish or deploy happened in this stage.

## Owner decisions (2026-10-11)

Answered in session, through the orchestrator's questions:

- **ADR-0084: accepted.** Status set to accepted. ADR-0034's status line
  now reads "amended by ADR-0084 (and earlier by ADR-0041)".
- **ADR-0085: accepted, trains included.** Status set to accepted.
  ADR-0036's status line now reads "amended by ADR-0085".
