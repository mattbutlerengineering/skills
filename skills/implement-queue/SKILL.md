---
name: implement-queue
description: Use when a repo's backlog of ready GitHub issues, or of factory work orders, should be drained without the Owner answering each step — "work the queue", "drain the backlog", "implement the ready issues", "run the queue on a loop", a scheduled routine, or a direct invocation. Claims a batch of independent ready issues, implements each in its own worktree with a TDD worker agent, gates every PR through CI and a review by a distinct agent (held unreviewed when the profile has no `verdict` hook), then runs a serial merge train. It stops at reviewed, green PRs unless the repo's queue profile opts in to auto-merge (ADR-0087). Everything repo-specific — label transitions, gate commands, the required check, specialist reviewers, locks — comes from the repo's queue profile, never improvised. Work orders never merge here (ADR-0033 gate 3). Many items, nobody present — not conduct (the Owner present, answering every ask in session) and not autorun (one run through every stage).
---

# Implement Queue

Drain a repo's `ready` issues: parallel implementation, serial merging.
This skill is the loop; the repo's **queue profile** supplies every
fact about that repo. It is the unattended one of the three skills that
drive work; the README's "Driving a run: which one" table says when
`autorun` or `conduct` fits instead.

```
Phase 0: Pre-flight   main green? open PRs first
Phase 1: Claim        a batch of independent ready issues
Phase 2: Implement    one worktree worker per issue, then CI + review gate
Phase 3: Merge train  unstick and land gated PRs, one zone at a time
Phase 4: Loop or stop reap, persist, report
```

## The queue profile

Read `.claude/implement-queue.md` in the target repo before anything
else. It is the Owner's written configuration: YAML frontmatter for the
policy, and one `## <hook>` section per hook below. If the file is
missing, run with the defaults and say so in the report; never invent a
hook's command.

Frontmatter keys (all optional):

| Key              | Default                                                        | Meaning                                                                                |
| ---------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `source`         | `issues`                                                       | `issues`: plain `ready` issues. `work-orders`: factory work orders, per [references/work-orders.md](references/work-orders.md). An invocation that asks for work orders overrides it for that run. |
| `merge`          | `off`                                                          | `off`: stop at reviewed, green PRs. `auto`: enqueue them for merge (see Merge policy). |
| `max_workers`    | `3`                                                            | Workers in flight at once.                                                             |
| `required_check` | none                                                           | The check name that must be present and green (e.g. a CI gate job).                    |
| `hold_labels`    | `[needs-review]`                                               | A PR or issue carrying one is never merged by this skill.                              |
| `priority`       | `[security, ci-fix, feature, audit]`                           | Label order for claiming; oldest first within a tier.                                  |
| `gate_paths`     | `[docs/adr/**, docs/design/**, **/prd.md, **/architecture.md]` | A PR changing a match, old path of a rename included, always needs a human merge (ADR-0036). |

Hooks (each a `## <name>` section with the exact command or rule):

| Hook             | Default when absent                                                                                   |
| ---------------- | ----------------------------------------------------------------------------------------------------- |
| `preflight`      | the gate's own green on the head SHA of `origin/main`, read from its check runs (Phase 0, step 2)     |
| `transition`     | `gh issue edit` swapping the state labels in the Labels table                                         |
| `compose`        | take candidates in priority order, skipping any that names the same files as one already taken        |
| `base-freshness` | `git fetch origin` and confirm this checkout shares history with `origin/main`                        |
| `worker`         | a general worker agent given the Worker brief below                                                   |
| `model`          | the worker's default model                                                                            |
| `ci-status`      | `gh pr checks <N>` plus the presence check below                                                      |
| `fast-path`      | none: every PR is reviewed (with no `verdict` hook, every PR off the fast path is held unreviewed, gate step 4) |
| `verdict`        | none: a missing hook is an `error` verdict, never a pass (fail closed)                                |
| `reviewers`      | one universal reviewer using [the reviewer contract](references/reviewer-contract.md); no specialists |
| `merge-command`  | `gh pr merge <N> --auto --squash --delete-branch --match-head-commit <sha>`                           |
| `update-branch`  | `gh pr update-branch <N>`                                                                             |
| `changed-files`  | `gh api repos/{owner}/{repo}/pulls/<N>/files --paginate`: every `filename` plus every `previous_filename`; its length must equal `gh api repos/{owner}/{repo}/pulls/<N> --jq .changed_files`, else fail closed |
| `lock`           | none: one session at a time is the only lock                                                          |
| `reap`           | none: report worker worktrees left behind                                                             |
| `telemetry`      | none                                                                                                  |

In every `merge-command`, `<sha>` is the gated head (gate step 1), never
a head read at merge time. A merge refused because the PR's head is no
longer `<sha>` is a moved head, not a failure to retry: the PR goes back
through the gate. The pin guards the moment the merge is requested; a
push after `--auto` is enabled is Phase 3's to catch.

**Cloud sessions.** Each `gh` command in this file states an intent;
the environment may offer only the GitHub MCP tools or the REST API
through `gh api`, and either carries it out. In Claude Code Remote the
GraphQL-backed `gh issue|pr` subcommands (`list`, `view`, `edit`,
`checks`, `merge`, `update-branch`) return HTTP 403 while `gh api`
REST calls succeed, so a profile written for a cloud session names the
REST twin of each default above (`preflight`'s check-runs read is REST
already). Where `gh` is absent altogether (`spawn gh ENOENT`), the REST
twins have no binary to run through, and the MCP twin is the way:

- `preflight`: REST `gh api repos/{owner}/{repo}/commits/<sha>/check-runs`
  (Phase 0, step 2), with `<sha>` from
  `gh api repos/{owner}/{repo}/branches/main --jq .commit.sha` and the
  push-run read as `gh api 'repos/{owner}/{repo}/actions/runs?head_sha=<sha>&event=push'`.
  MCP: `actions_list` with `method: list_workflow_runs`, filtered to
  `branch: main` and `event: push`, keeping only runs whose `head_sha`
  is the head; with a `required_check`, `method: list_workflow_jobs` on
  each kept run to find the job of that name (missing once every kept
  run has settled is red, as above). The re-run: REST
  `gh api -X POST repos/{owner}/{repo}/actions/runs/<run-id>/rerun-failed-jobs`;
  MCP `actions_run_trigger` with `method: rerun_failed_jobs`.
- Open PRs (Phase 0): MCP `list_pull_requests`, state open.
- Claim (Phase 1): MCP `list_issues` with `labels: ["ready"]`, state
  open; no entry carries a `pull_request` key there, so nothing to drop.
- `transition`: `gh api -X POST repos/{owner}/{repo}/issues/<N>/labels -f 'labels[]=<to>'`
  then `gh api -X DELETE repos/{owner}/{repo}/issues/<N>/labels/<from>`,
  one pair per swap in the Labels table. MCP: `issue_read` with
  `method: get_labels`, then `issue_write` with `method: update` and
  `labels` set to the full resulting set, never only the label added.
- `ci-status`: `gh api repos/{owner}/{repo}/commits/<head-sha>/check-runs`,
  with `<head-sha>` from `gh api repos/{owner}/{repo}/pulls/<N> --jq .head.sha`.
  MCP: `pull_request_read` with `method: get_check_runs`.
- `changed-files`: no MCP twin. `pull_request_read` with
  `method: get_files` is not a source until a run records that it
  reports a rename's `previous_filename`. With no `gh` the default
  cannot run, so every PR needs a human merge, unless the profile's own
  `changed-files` hook names another source that lists both paths of a
  rename.
- `merge-command`: `gh api -X PUT repos/{owner}/{repo}/pulls/<N>/merge -f merge_method=squash -f sha=<sha>`
  once `ci-status` is green (the endpoint answers 409 when the head is
  no longer `<sha>`), then
  `gh api -X DELETE repos/{owner}/{repo}/git/refs/heads/<branch>`.
  REST has no `--auto`: the train merges a green PR itself instead of
  enqueuing it, so the pin at merge time is the whole protection and
  nothing is left to disable. MCP: `merge_pull_request` with
  `merge_method: squash` and `expectedHeadSha` set to the gated head;
  it merges at once too, and has no branch-delete twin, so the branch
  is left to the repo's delete-on-merge setting and reported.
- `update-branch`: `gh api -X PUT repos/{owner}/{repo}/pulls/<N>/update-branch`.
  MCP: `update_pull_request_branch`.
- The verdict comment (gate step 5): MCP `add_issue_comment`, which
  takes a pull request number too.

Tool names are the GitHub MCP server's; a host may prefix them. With
neither `gh` nor an MCP tool for the intent, a stated hook cannot run:
fail closed. Claim nothing you cannot transition, merge nothing you
cannot check, and report the missing capability.

A hook can tighten a default rule; it can never loosen a rule in this
file's Rules section.

## Phase 0: Pre-flight

1. Check the profile against the two tables above and
   [references/profile-migration.md](references/profile-migration.md):
   every `## <name>` section is a row of the hook table, every
   frontmatter key a row of the key table. Report each hook the profile
   lacks together with the consequence the reference gives for it (a
   profile that predates `verdict` holds every PR off the fast path for
   a human, unreviewed (gate step 4), even under `merge: auto`, and
   nothing else says so), and each section
   or key the tables do not name as ignored, never run. A gap never
   stops the run and never loosens a rule; the findings lead the final
   report.
2. Run the `preflight` hook. Its default judges the head SHA of
   `origin/main` by the gate's own definition, never the last few runs
   of any workflow (event-driven workflows crowd a run-list window, and
   a cancelled run whose gate job failed passes a failure-only filter).
   `git fetch origin`, take `<sha>` from `git rev-parse refs/remotes/origin/main`,
   then:
   - With a `required_check`: read
     `gh api repos/{owner}/{repo}/commits/<sha>/check-runs --paginate`
     for that check, and
     `gh api 'repos/{owner}/{repo}/actions/runs?head_sha=<sha>&event=push'`
     for the head's push-triggered runs (issue-triggered workflows also
     run against the head and never decide it). That check present and
     `completed` with `success` is green. Queued or in progress is
     pending. Red is every completed conclusion other than `success`
     (`failure`, `cancelled`, `timed_out`, `skipped`, `neutral`,
     `action_required`, `startup_failure`, `stale`), and the check
     missing once every push-triggered run of the head has settled.
     Missing while a push-triggered run of the head is still queued or
     in progress is pending.
   - Without one: read
     `gh run list --branch main --commit <sha> --event push --json databaseId,name,status,conclusion`.
     A failed, cancelled or timed-out run is red; a run still queued or
     in progress is pending; green needs at least one completed
     `success` and no red run. No completed push run at all is not green.
   - Pending, or no push run yet, waits: poll the same read once a
     minute for up to 15 minutes (a profile's `preflight` hook may set
     another bound). Still not settled is unproven: claim nothing,
     report main as unproven and stop the iteration. Never claim a
     CI-fix issue or new work on an unproven main.
   - If main is red, read the failing job's log first. When it shows no
     repo cause (a runner or network failure, a cancelled or timed-out
     job), re-run the failed jobs once per head SHA: a run whose
     `run_attempt` is above 1 (`gh run view <run-id> --json attempt`)
     has had its re-run, so a later iteration on the same red head does
     not re-run it again. The `<run-id>` of a check run is in its
     `details_url` (`/actions/runs/<run-id>/job/<job-id>`; the check
     run's own `id` is the job id), and the push-runs read above lists
     it directly. Re-run with `gh run rerun <run-id> --failed` (cloud
     twin in the list above), then wait and judge the head again by the
     same read. Green on that final run is green. Only a second failure,
     or a failure with a repo cause, makes fixing main **this**
     iteration: claim or file the CI-fix issue, work it through Phase 2,
     and skip to Phase 3. A profile's `preflight` hook may say how to
     re-run instead. The re-run is never a way to skip CI or to declare
     main green without the check present and successful on the final
     run.
3. Read every open PR (`gh pr list --state open --limit 1000 --json number,title,headRefOid,labels,body`;
   cloud twin in the list above). The REST twin is paged, so read every
   page of `gh api 'repos/{owner}/{repo}/pulls?state=open&per_page=100'`
   (`.head.sha` is the head). A list that may be truncated (its count
   equals the limit, or a page is missing) fails closed: claim nothing
   and report it. A PR belongs to this queue when it closes an issue
   carrying `in-progress`, `has-pr`, `needs-review`, `agent-failed` or
   `stealable`; every other PR is foreign (another agent's, a bot's, a
   routine's). A PR the evidence says must not merge (the third cause
   below) is never gated, re-run toward green or merged by this queue
   in any CI state, a revert someone else re-ran to green included; it
   is reported. Unfinished PRs come before new issues: green ones go to
   the Phase 2 gate, pending ones wait, failed ones of this queue get
   fixed or their issue labelled `agent-failed`. A foreign green PR goes
   to the Phase 2 gate unchanged, because the gate and the Merge policy
   run per PR and protect any PR. A foreign failed PR is never fixed by
   this queue unless a ready issue says so, is reported, and does not
   block claiming. Never fixed means never edited, pushed to or
   updated; the infrastructure re-run of the last cause below applies to
   a foreign PR too, whichever of the no-linked-issue and held causes it
   matched, unless it matches the must-not-merge cause: it is not a fix,
   and the PR stays foreign and non-blocking whatever the outcome. Claim
   nothing new while a failed PR of this queue is
   open and matches none of the causes below. This is the protocol's
   "Open pull requests first" pre-flight
   (`../../docs/pipeline-protocol.md`) with this skill's mechanics;
   merges still follow the Merge policy below.

   A failed PR is sorted by these causes before it can block, in this
   order, and the first match wins:

   - A failed PR with no linked issue (a dependency bot's, the release
     bot's) has nothing to label, is reported, and does not block
     claiming.
   - A failed PR that carries a `hold_labels` label, or whose issue
     does, is handed to a human, is reported, and does not block
     claiming.
   - A PR the evidence says must not merge (an automated revert whose
     red was infrastructure) is never fixed, re-run or updated toward
     green, is reported, and does not block claiming.
   - A failed PR whose failing jobs show no repo cause (a runner or
     network failure, a cancelled or timed-out job) gets its failed jobs
     re-run once per head SHA by the re-run rule of step 2, and is
     judged again. A PR still red after its re-run counts as failed
     and, when it is this queue's and matches no earlier cause, blocks
     claiming; the re-run is no exemption.

   A green PR is settled when its head commit is at least 15 minutes
   old and its head SHA has not changed since this session recorded it.
   Step 3 records every open PR's head SHA in each iteration. A PR with
   no record is judged on age alone, so a PR first seen with an old head
   commit goes to the gate at once, which keeps a one-pass session
   (nothing claimed) gating its green PRs. A young head waits until its
   commit is 15 minutes old, whatever the iteration. A head that changed
   since it was recorded is not settled whatever its date, and is
   recorded anew. A head named in this session's own worker result as
   the head that worker pushed counts as settled at once while the PR's
   head still equals it; this wins over the changed-since-recorded rule
   for that head only, and a head pushed by anyone else gets no such
   exception. The head commit's date is read first with
   `gh api repos/{owner}/{repo}/commits/<headRefOid> --jq .commit.committer.date`,
   `<headRefOid>` being the head from the list above (no MCP twin is
   verified). Where `gh` cannot read it, run
   `git fetch --depth=1 origin pull/<N>/head`, confirm
   `git rev-parse FETCH_HEAD` equals the head SHA, then run
   `git show -s --format=%cI <sha>`. A date read from any commit other
   than the PR's current head SHA leaves the PR not settled. The
   committer date is a proxy, since GitHub does not expose push time:
   `git rebase` resets it, and the real failure is a commit made earlier
   and pushed later, which looks old when it was just pushed; the
   recorded-head comparison catches that from the second iteration on,
   and a one-pass session accepts it. A date that cannot be read by
   either source
   leaves the PR not settled. An unsettled green PR waits this
   iteration, is not reviewed, and is reported; a failed PR keeps its
   disposition above.
4. Look for another queue session, and report it before claiming. List
   the open issues that carry `in-progress` and that this session did
   not claim, with `gh issue list --label in-progress --state open --json number,title,updatedAt`
   (cloud: `gh api 'repos/{owner}/{repo}/issues?labels=in-progress&state=open&per_page=100'`,
   dropping every entry that carries a `pull_request` key; MCP:
   `list_issues` with `labels: ["in-progress"]`, state open). A fresh
   session has claimed none, so every one counts, and a looping session
   subtracts the issues it claimed in earlier iterations, never one Phase 1
   skipped. Give each its
   claim time, the last line of
   `gh api repos/{owner}/{repo}/issues/<N>/timeline --paginate --jq '.[] | select(.event == "labeled" and .label.name == "in-progress") | .created_at'`
   (the timeline lists events oldest first). There is no MCP twin for
   the timeline in the GitHub MCP server's `issue_read` methods, so an
   MCP-only session reports each issue without a time. List the open
   PRs this session did not open whose head commit is under 15 minutes
   old, with the head from `gh api repos/{owner}/{repo}/pulls/<N> --jq .head.sha`
   and its time from `gh api repos/{owner}/{repo}/commits/<sha> --jq .commit.committer.date`;
   the commit's date stands in for the push time. Report both lists
   before Phase 1 claims anything. The label claim is the mutex, so
   this session proceeds to Phase 1 and never stops for what this step
   finds. A hard stop is not used, because one stale `in-progress`
   label, a crashed worker's, would block the queue for ever. What the
   report narrows is what this session touches: never touch an issue or
   PR listed here (no claim, relabel, merge or branch update, except that Phase 3
   step 1's head comparison and `--disable-auto` still run, since they
   only tighten), and claim
   only issues that pass the post-claim check in Phase 1. A `lock` hook
   that keeps its lock in the local git common dir cannot see a cloud
   session, so it does not replace this step or the Rules' One queue
   session per repo at a time. Under `source: work-orders` the issue
   list does not apply, because the claim there is `wo:in-progress`
   through the lifecycle machine in
   [references/work-orders.md](references/work-orders.md), and the pull
   request list still applies.

## Phase 1: Claim a batch

Under `source: work-orders`, the planner and the `wo:*` claim in
[references/work-orders.md](references/work-orders.md) replace this
phase.

    gh issue list --label ready --state open --json number,title,body,labels

In a cloud session (see Cloud sessions above):
`gh api 'repos/{owner}/{repo}/issues?labels=ready&state=open&per_page=100'`,
dropping every entry that carries a `pull_request` key — the REST
issues endpoint lists pull requests too.

Sort by the profile's `priority`, oldest first within a tier; a security
issue always gets a slot. Drop any issue that:

- names an open dependency (`Depends on: #N` with `#N` open);
- carries `in-progress`, `stealable`, or a `hold_labels` label;
- carries a `wo:*` label: a factory work order belongs to
  `source: work-orders`, so the two sources never race for one issue;
- would touch the same files as an issue already taken (run the
  `compose` hook when the profile has one).

Take at most `max_workers`. Move each claimed issue to `in-progress`
with the `transition` hook.

For the claim transition only, the removal of `ready` comes first and
the add of `in-progress` follows; every other
transition keeps the `transition` hook's order. Run the steps below as
written even when the profile's `transition` hook is one swap command.
Read `gh api -i repos/{owner}/{repo}/issues/<N>` just before the claim:
if `ready` is gone or `in-progress` is already there, another session
took it, so skip the issue and never touch its labels. Note the
whole-second time in that response's `Date` header, which is GitHub's
clock. Read the issue's timeline with
`gh api repos/{owner}/{repo}/issues/<N>/timeline --paginate --jq '.[] | select(.event == "labeled") | [.label.name, .created_at, .actor.login] | @tsv'`
to take the time of its last `ready` labeled event; when the timeline
cannot be read, or holds no `ready` labeled event, claim nothing for
it. Then remove `ready` with
`gh api -X DELETE repos/{owner}/{repo}/issues/<N>/labels/ready`. Hold
the claim only on a 200. On any other status, a 404 included (the
documentation gives it for a label that does not exist, which this
session takes to mean another session removed `ready` first), skip the
issue, never touch its labels and report it. This claim narrows the race
window and is not a lock: the documentation gives a 404 only for a label
that does not exist, so if two removals both returned 200 two sessions
would each hold the claim, and One queue session per repo at a time in
the Rules stays the guarantee, the label claim being a best-effort mutex
that makes a collision unlikely and detectable by the secondary check.
Then add `in-progress` with
the `transition` hook's add. Dispatch no worker before that 200 and the
add of `in-progress`. A failed add means this session won the removal
but holds no complete claim: dispatch nothing for that issue, skip it and
report it for the Owner, since it then has neither state label. After the add, read the timeline again
with the same command and confirm, as a secondary check, exactly one
`in-progress` labeled event since the last `ready` labeled event, whose
`created_at` is at or after the time noted, comparing whole seconds, which
shows only that the event was created after this session's read. There is no MCP twin for the removal,
the `Date` read or the timeline read, so a session with no `gh` cannot
run this check and must claim nothing. On an unreadable timeline after
the add, skip the issue, dispatch no worker for it, leave the label as
it is and report it. With no `in-progress` labeled event after the add
(the timeline lags, or the transition failed), skip the issue, dispatch
no worker for it, leave the label as it is and report it. With two or
more `in-progress` labeled events, or one whose `created_at` is earlier
than the time noted, this session lost the race, so skip the issue,
dispatch no worker for it, leave the label as it is and report it. Never
move the issue back to `ready` after a lost race, because the session
that holds it may already have dispatched a worker. An issue skipped in
this phase is not claimed by this session, so Reconcile before Phase 4
leaves it alone, a looping session's Phase 0 step 4 does not subtract
it, and the report names it for the Owner to free. An open issue with no
queue state label that was last labelled by a claim attempt, after a
failed add or a session that died, is stuck and fails closed, and the
Owner frees it by adding `ready`. An issue left with `in-progress` by
two sessions that both skipped is freed by removing `in-progress` and
adding `ready`.

## Phase 2: Implement, then gate

**Before dispatching**, run the `base-freshness` hook. Worktrees are cut
from this checkout's object store, so a stale or unrelated base is
inherited by every worker. Fail closed: an undeterminable base is never
usable.

Dispatch one worker per issue, **all in one message**, each with its own
worktree (`isolation: "worktree"`) and the model the `model` hook
resolves. Dispatch is never held by the merge-train lock: capacity
(`max_workers`) is the only limit on starting work.

**Harness needs.** The dispatch above is written for Claude Code's Agent
tool. A harness that lacks one of these features uses its fallback, and
under `source: issues` none of them stops the run.

- Per-worker worktree. Absent (no `isolation` argument): the
  orchestrator cuts each worktree after `base-freshness`, under
  `.claude/worktrees/`, with `git -C <repo> worktree add --no-track
  <path> -b <branch> refs/remotes/origin/main`. Without `--no-track`,
  a remote-tracking start point makes `origin/main` the new branch's
  upstream, so a push that names no branch can target `main`. Tell
  that worker in its brief to push with `git push -u origin <branch>`,
  never a bare `git push`. The orchestrator removes the worktree: by
  the Phase 4 empty-worktree rule when the worker ended with no commit,
  by the `reap` hook once its PR merged.
- Per-worker model. Absent (the harness refuses a per-call model):
  dispatch on the harness's default model, treat the `model` hook's
  answer as advisory, and say so once in the run report; never fail
  the batch over it. A dispatch refused with an error naming the model
  argument is re-sent once without it. A re-send that is refused too
  failed for another reason and is handled as a worker failure.
- Usage on completion. Absent: leave the usage fields empty and still
  write the row (the `telemetry` rule below).
- Messaging a running worker. Absent: dispatch needs none, and the
  45-minute check-in becomes stopping the worker at the bound (the
  Wall-clock bound below).

Under `source: work-orders`, a worker with no usage gets no
`budget_guard.py record` row, and the run report names each unrecorded
order, because the ledger then reads low. Under `source: work-orders`,
a harness without worktree isolation follows the Cloud fallback in
[references/work-orders.md](references/work-orders.md), not the
orchestrator-cut worktree.

### Worker brief

Under `source: work-orders`, use the work-order brief in
[references/work-orders.md](references/work-orders.md) instead.

Every worker prompt carries:

1. The issue number, title and full body.
2. First steps: the base-freshness check and the repo's dependency
   install (worktrees have none).
3. TDD per vertical slice: a failing test first, then the minimal code.
4. The repo's gates on the affected code before declaring done, typecheck
   included where the language has one.
5. Push the branch and open a PR with `Closes #<N>`; confirm its base is
   `main`. Never merge.
6. Never commit secrets or credentials; validate external input at
   boundaries; an existing vulnerability found on the way is fixed first.
7. Run every subprocess in the foreground under a time bound
   (`timeout 600 <cmd>` or the tool's own timeout; state a longer bound
   for a slow step such as a code regeneration or a CLI build). Never
   start a background or watch process and wait on it. A command that
   hits its bound is killed and its output recorded, never retried
   unchanged. Stall-abort: after two resumes without a new commit, or
   two resumes that each hit a bound, stop: commit what works, open a
   draft PR if anything is usable, and report the blocking command.
8. Stay inside your worktree. Stop only processes you started, by PID;
   never `pkill -f` or `killall`, which match machine-wide. Never run
   `git stash`, `git gc` or `git worktree prune`: they act on state
   shared by every worktree of the repo. After any investigative
   checkout (a bisect, `git checkout <sha> -- <paths>`) restore the
   worktree to a clean state, confirm it with `git status --porcelain`
   and `git diff`, and say so in the result.
9. An evidence comment with no PR is a valid result when the cause is
   outside the repo (for example a scheduled routine that never fired):
   post the evidence on the issue, open no PR and report the evidence
   outcome. Never invent a change to have something to push.
10. Say in the result which checks were not verified locally: list under
   `not verified locally` every CI check the PR will face that you did
   not or could not run, each with the reason. `has-pr` then means local
   gates green, so the orchestrator knows which checks to watch first.
   A profile may name checks that commonly fail only in CI (a secret
   scan, bundle size, generated-artifact drift) in its own prose, as a
   hint; when it does, the orchestrator repeats it in the brief.
11. Finish or hand off within 45 minutes from dispatch, and answer the
   orchestrator's check-in at once.

When a worker finishes, label its issue with the `transition` hook:

| Outcome                                                  | State          |
| -------------------------------------------------------- | -------------- |
| PR open, gates green                                     | `has-pr`       |
| Partial work (draft PR)                                  | `needs-review` |
| Investigated: no repo change can fix it, evidence posted | `needs-review` |
| No usable change                                         | `agent-failed` |
| Second failure on the same issue                         | `stealable`    |

Then run the `telemetry` hook, if any, with the worker's real usage.
Leave cost empty when the usage carries none; never estimate it.
A field the harness reports no usage for (tokens in and out, tool uses,
model tier, cost) is left empty and never estimated. A row without
usage is still written, with the fields it has (issue, outcome,
duration, PR). A duration the harness does not
report may be read from the issue's label-event timestamps, and is
reported as derived.

**Wall-clock bound.** At 45 minutes from dispatch the orchestrator sends
the worker one check-in asking for its status and its plan to stop. The
worker answers, then within 10 minutes commits what works and opens a
draft PR if anything is usable, or posts its evidence. A worker that
has not answered or ended 10 minutes after the check-in, or that the
harness cannot message, is stopped, counts as stalled and has its issue
reconciled below. Wall-clock is the portable bound: the `telemetry`
hook sees usage only after a worker finishes, so there is no spend
bound.

**Reconcile before Phase 4.** A worker's `transition` can fail without
a trace, so the orchestrator checks it instead of trusting it. Skip
any issue a live worker still holds. For every other issue claimed this
session that still carries `in-progress` or no state label, read the
PRs that close it (`Closes #<N>` on the PR list) and run the
`transition` hook where the label disagrees with the table: an open PR
with green or pending gates → `has-pr` (the gate still runs); a draft
PR → `needs-review`; an open PR with red gates, a PR closed unmerged,
or no PR at all (unless the evidence outcome below applies) →
`agent-failed`. A worker that reported the evidence outcome and posted
its comment on the issue has no PR by design: its issue is
`needs-review`. An issue whose PR merged is
delivered: leave it to GitHub's close. Never remove a `hold_labels`
label or `stealable`, whatever the PR looks like: the gate put them
there on purpose. A worker resumed twice with no new commit counts as
stalled: stop it, do not resume it again, and reconcile its issue the
same way. Report each repair as drift, with the count of issues claimed
against the count repaired.

### The gate, per PR

This is the last check before a merge. Run it for each worker PR as soon
as that PR's CI settles; it can overlap with workers still running.

1. **CI.** Record the PR's head SHA once, here: `gh pr view <N> --json
   headRefOid`, or REST `gh api repos/{owner}/{repo}/pulls/<N> --jq
   .head.sha`, or MCP `pull_request_read`. That SHA is the gated head,
   the recorded head, and every later step uses it: the checks below,
   the fast-path classification, the `changed-files` list, the
   reviewer's worktree, the verdict comment and the `merge-command`.
   Read the PR's head again before the review is dispatched, before the
   verdict comment and immediately before the merge; if it differs from
   the recorded head, the gate restarts from step 1 on the new head and
   nothing recorded for the old one counts. Run the `ci-status` hook.
   With a `required_check`, green
   means that check is **present and successful**. A rollup with no
   failures and no pending checks is not green when the required check
   never ran: treat a missing check as its own state, re-trigger CI once
   if the repo's hook says how, and never enqueue on it.
2. **Holds.** A `hold_labels` label on the PR or its issue ends the gate
   here: no review, no merge.
3. **Fast path.** If the `fast-path` hook says the diff at the recorded
   head is low-risk
   **and** no specialist reviewer matches it, skip step 4. That
   classification counts as the review for the Merge policy (ADR-0088). If the hook
   cannot prove its own inputs are current (a stale build, an unreadable
   classifier), fail closed: review the PR and dispatch every specialist.
4. **Review.** When Phase 0's profile check found no `verdict` hook, no
   verdict can be derived and a review could not lead to a merge, so
   for a PR that is not on the fast path (step 3) this step does not
   run: dispatch no reviewer, report the PR as unreviewed and held for a
   human, and go to step 5, whose `no verdict hook` comment is its
   record. That PR never merges, under any `merge` setting; the human
   merging can request a review. A fast-path PR is unaffected: the
   fast path stays open, its classification is the Owner's written
   review (ADR-0088), and under `merge: auto` it can still merge. Otherwise dispatch the universal reviewer, plus each specialist
   the `reviewers` hook matches to the changed files, with the input
   [the reviewer contract](references/reviewer-contract.md) defines. A
   reviewer is never the PR's author.
   - Dispatch each reviewer into its own detached worktree at the
     recorded head (`git worktree add --detach <path> <head-sha>`,
     `<head-sha>` being the recorded head), never into
     the shared checkout, and never let it switch that checkout's
     branch. A reviewer with no worktree reads through the API and
     cannot run code. Remove the worktree (`git worktree remove
     <path>`) once the review is recorded.
   - Snapshot `git status --porcelain`, the current branch and `HEAD`
     before each reviewer dispatch and compare all three afterwards.
     The snapshot detects a change, it does not prevent one. A reviewer
     that changed the checkout has produced an invalid review: restore
     it by the procedure in
     [the reviewer contract](references/reviewer-contract.md), then
     re-dispatch.
   - A review that timed out or errored is recorded as `error`, never as
     `pass`.
5. **Verdict.** Run the `verdict` hook on the universal reviewer's
   `score`, passed as one quoted argument and only after it reads as a
   usable score, a bare finite number from 0 to 10 (the score is the
   reviewer's text, never a shell fragment; a score that fails the check
   never reaches the hook), and act on its exit code only: the reviewer is handed no pass
   line and returns no verdict, and a `verdict` it returns anyway is
   ignored whichever way it points. Exit 0 is `pass`, exit 1 is `flag`.
   Anything else is `error`, and the cause sets the remedy. A
   reviewer-side error (the review timed out, or the reviewer's score is
   not usable) gets one re-dispatch of the reviewer, then holds
   the PR for a human. A hook-side error (a missing hook, a hook that
   did not run, or any exit code other than 0 or 1 on a usable score: a
   wrong argument count gives 2, a killed process 137) gets no re-dispatch, because a second review
   cannot change it: hold the PR for a human at once. Under
   `merge: auto` an `error` never merges.
   Post a verdict comment on the PR whose first line is the line the
   hook printed, verbatim, so every comment carries the score, and whose
   second line is `Head: <sha>`, the recorded head, so the comment says
   which head it covers. When the hook printed no `reviewer-verdict:`
   line, the first line is `reviewer-verdict: error (<reason>)`, with
   `<reason>` one of `no verdict hook`, `hook did not run`, `hook exit
   <code>` (an exit code other than 0 or 1 that printed no such line),
   `reviewer timed out` or
   `no usable score`, so the comment still parses like the hook's own
   lines. The comment carries the score and the findings whenever the
   reviewer returned a score. All pass
   → the Merge policy. A derived `flag` or a specialist `block` → the
   contract's retry policy (one retry on the same branch, then
   `needs-review` and no merge).

## Merge policy

Under `merge: off` (the default) a PR that passes the gate is labelled
for the human merge, ADR-0033's gate 3, and the report lists it as
**reviewed, green, awaiting merge**. This skill merges nothing.

Under `source: work-orders` the merge is always off, whatever `merge:`
says: a work order's merge is the human's (ADR-0033 gate 3).

Under `merge: auto` (ADR-0087) the profile is the Owner's standing
consent, and a PR that passes every gate step is enqueued with the
`merge-command` hook. The consent never covers a PR that:

- lacks a pass from a reviewer distinct from its author, unless it took
  the fast path (step 3): the `fast-path` hook's low-risk
  classification is the Owner's written review for it (ADR-0088);
- lacks the `required_check` present and green;
- has a head other than the gated head: a pass covers only the head
  the gate recorded, so the PR is merged, or left enqueued, only at
  that head;
- carries a `hold_labels` label.
- changes a file `gate_paths` matches, judged on the `changed-files`
  hook's list (below).

**The changed-file list.** The `gate_paths` check reads one source, the
`changed-files` hook, and only that source. Its list holds every file
the PR changes, and a rename or move counts as **both** its old path and
its new one: a gate-path file moved to an ungated path is a change to a
gate path. With no hook the default in the table above applies: the
REST file list, whose length is checked against the PR's `changed_files`
count. A list that reports only a rename's destination, a list whose
length differs from that count (the endpoint stops at 3000 files and
flags no truncation), a list the source capped or paged short, a list
read in part, an empty list for a PR that changes files, and a source
that failed or is unavailable all fail closed: the PR needs a human
merge. Read it at the recorded head: the REST list is the PR's current
files, so read the PR's head again after it, and a head that differs
fails closed too. Never fill a gap in the list
from the PR body, its title, or the author's account of what changed.

A merge the session's runtime denies is not retried by any route for
the rest of the session. Comment the derived verdict line (step 5) on the PR and report it as
awaiting a human merge.

## Phase 3: Merge train

Enqueued PRs merge as their checks go green. This phase first checks
the head of every enqueued PR, then unsticks the ones that fell behind
`main` after a sibling merged:

1. For every enqueued PR, up to date with `main` or not, compare its
   current head (`gh pr view <N> --json headRefOid`; REST `gh api
   repos/{owner}/{repo}/pulls/<N> --jq .head.sha`) with its gated head.
   The gated head is the recorded head of gate step 1 in the session
   that ran the gate. In a later session it is the `Head:` line of the
   PR's latest verdict comment, read only from comments authored by the
   queue's own account (`gh api user --jq .login`; the REST comment's
   `user.login`) whose first line is a `reviewer-verdict:` line;
   otherwise the PR has no gated head. A PR with no gated head, or a
   head that differs, is a mismatch: run `gh pr merge <N> --disable-auto`,
   send the PR back through the gate, and take no further step here for
   it. The REST and MCP merges are never enqueued, so they have nothing
   to disable (no MCP tool for disabling auto-merge is confirmed): their
   protection is the pin at merge time.
2. Take the `lock` hook's lock for the PR's zone before touching its
   branch. If another session holds it, leave that zone alone this
   iteration and report it.
3. Read the PR's head, then run the `update-branch` hook. Where the
   repo's lockfile can drift on a server-side update, the hook says how
   to rebase and regenerate it instead. The hook's own commit is the one
   head change that is not a mismatch (see the exception in Rules): adopt
   the head after the hook as the gated head only when the hook exited 0
   having made a new commit with exactly two parents: the head read just
   before the hook first, and a commit already on
   `refs/remotes/origin/main` second (after `git fetch origin`; `gh api
   repos/{owner}/{repo}/commits/<head> --jq '[.parents[].sha]'` lists
   them). A branch that was already up-to-date makes no commit, and any
   other head, an author's own merge of `main` included, is a mismatch:
   handle it as step 1 does.
4. A red check after the update gets one small fix in this session, or a
   CI-fix issue and `agent-failed` on the original. It counts toward the
   circuit breaker.

Release every lock you took when the train ends, on any exit.

## Phase 4: Loop or stop

- Run the `reap` hook. A worker that committed keeps its worktree, so
  nothing else reclaims it; a reaper must refuse any worktree with an
  open PR or a live process, and needs positive evidence of a merge.
- Remove a worktree this session's dispatch cut when its worker ended
  with no commit, a clean tree and no remote branch: the `reap` hook's
  evidence of a merge can miss such a worktree, so the session does not
  rely on it. It is the
  orchestrator's own worktree only: never one it did not cut, never one
  with a PR. All four checks must hold. `git -C <path> rev-list --count
  refs/remotes/origin/main..HEAD` prints 0, after `git fetch origin`.
  `git -C <path> status --porcelain --untracked-files=all` prints
  nothing. `git ls-remote origin refs/heads/<branch>` prints nothing.
  `lsof -w +D <path>` prints nothing, so no live process holds it. On a
  pass, `git worktree remove <path>` (never `--force`), then `git
  branch -D -- <branch>`, safe because no commit is ahead of main. A
  failed check or a failed `git` call leaves the worktree and its
  branch in place and is reported with its path.
- Persist the telemetry the session appended, once per iteration, not
  per worker: an ephemeral checkout loses it, and one PR per row races
  its own auto-merge. Batch every row the iteration appended into one
  commit on one branch. Name the branch for the session as well as the
  date (`chore/queue-telemetry-<date>-<session-id>`), so two sessions
  never share one. Restore or rebase the tracked metrics file from
  `origin/main` after `git fetch origin`, never from the local `main`,
  which may be stale.
- More ready issues and budget left → Phase 0. Three consecutive failures
  (workers or train) → release locks, stop and report. The evidence
  outcome (a worker's issue left `needs-review` with its evidence
  posted) is not a failure: it leaves the count unchanged. Report it
  with its evidence.
- Report: issues claimed, PRs opened, PRs merged or awaiting merge, and
  every failure with its cause; with no `verdict` hook under `merge: auto`,
  also that every merge in the run took the fast path unreviewed.
  Under `source: work-orders`, also the
  planner's deferrals, each order's spend record, and every released
  order ([references/work-orders.md](references/work-orders.md)).

Recurring use: `/loop 30m` with this skill.
The interval is a minimum gap between iterations, not a bound on one
iteration, and an iteration that waits on CI can outlast it. A
re-invocation in the same session while an iteration is in flight
continues that iteration and never starts a second one: a loop tick
that fires then joins the one in flight and does nothing new, and the
next iteration starts only after the report. A session with no memory
of an iteration in flight cannot tell, and Phase 0 step 4 shows it the
`in-progress` issues and recently pushed PRs that iteration holds, which
it leaves alone like any other listed there.

## Labels

| Label          | Meaning                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------- |
| `ready`        | Available to claim                                                                          |
| `in-progress`  | A worker has it                                                                             |
| `has-pr`       | PR open, in the gate or the train                                                           |
| `needs-review` | Partial work, a repeat flag, or evidence that no repo change can fix it; a human looks next |
| `agent-failed` | No usable change this time                                                                  |
| `stealable`    | Failed twice; needs a different approach                                                    |

## Rules

- One queue session per repo at a time.
- One issue per PR, one PR per worker, one worktree per worker.
- Never force-push `main`; never skip CI or commit hooks.
- Absence of failures is not green. Absence of a review is not a pass.
- A gate input that cannot be proven current fails closed: more review,
  never less.
- Merge only under `merge: auto` and only through the gate. Without it,
  stop at the PR.
- A review covers one head. A push after it voids the review, whichever
  way the verdict pointed.
- The one exception is the commit the `update-branch` hook itself makes
  in the merge train, adopted only on the conditions of Phase 3 step 3.
- Discovery (audits, error triage, dependency alerts) feeds the queue;
  this skill only drains it.
