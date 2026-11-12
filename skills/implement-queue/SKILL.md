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
3. List open PRs. Unfinished PRs come before new issues: green ones go
   to the Phase 2 gate, pending ones wait, failed ones get fixed or
   their issue labelled `agent-failed`. Claim nothing new while an open
   PR is failed. This is the protocol's "Open pull requests first"
   pre-flight (`../../docs/pipeline-protocol.md`) with this skill's
   mechanics; merges still follow the Merge policy below.

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

## Phase 2: Implement, then gate

**Before dispatching**, run the `base-freshness` hook. Worktrees are cut
from this checkout's object store, so a stale or unrelated base is
inherited by every worker. Fail closed: an undeterminable base is never
usable.

Dispatch one worker per issue, **all in one message**, each with its own
worktree (`isolation: "worktree"`) and the model the `model` hook
resolves. Dispatch is never held by the merge-train lock: capacity
(`max_workers`) is the only limit on starting work.

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

When a worker finishes, label its issue with the `transition` hook:

| Outcome                          | State          |
| -------------------------------- | -------------- |
| PR open, gates green             | `has-pr`       |
| Partial work (draft PR)          | `needs-review` |
| No usable change                 | `agent-failed` |
| Second failure on the same issue | `stealable`    |

Then run the `telemetry` hook, if any, with the worker's real usage.
Leave cost empty when the usage carries none; never estimate it.

**Reconcile before Phase 4.** A worker's `transition` can fail without
a trace, so the orchestrator checks it instead of trusting it. Skip
any issue a live worker still holds. For every other issue claimed this
session that still carries `in-progress` or no state label, read the
PRs that close it (`Closes #<N>` on the PR list) and run the
`transition` hook where the label disagrees with the table: an open PR
with green or pending gates → `has-pr` (the gate still runs); a draft
PR → `needs-review`; an open PR with red gates, a PR closed unmerged,
or no PR at all → `agent-failed`. An issue whose PR merged is
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
   did not run, or exit 2 on a usable score, such as a wrong argument
   count or a crash) gets no re-dispatch, because a second review
   cannot change it: hold the PR for a human at once. Under
   `merge: auto` an `error` never merges.
   Post a verdict comment on the PR whose first line is the line the
   hook printed, verbatim, so every comment carries the score, and whose
   second line is `Head: <sha>`, the recorded head, so the comment says
   which head it covers. When the hook printed no `reviewer-verdict:`
   line, the first line is `reviewer-verdict: error (<reason>)`, with
   `<reason>` one of `no verdict hook`, `hook did not run`, `hook exit
   2` (an exit 2 that printed no such line), `reviewer timed out` or
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
- Persist the telemetry the session appended, once per iteration, not
  per worker: an ephemeral checkout loses it, and one PR per row races
  its own auto-merge. Batch every row the iteration appended into one
  commit on one branch. Name the branch for the session as well as the
  date (`chore/queue-telemetry-<date>-<session-id>`), so two sessions
  never share one. Restore or rebase the tracked metrics file from
  `origin/main` after `git fetch origin`, never from the local `main`,
  which may be stale.
- More ready issues and budget left → Phase 0. Three consecutive failures
  (workers or train) → release locks, stop and report.
- Report: issues claimed, PRs opened, PRs merged or awaiting merge, and
  every failure with its cause; with no `verdict` hook under `merge: auto`,
  also that every merge in the run took the fast path unreviewed.
  Under `source: work-orders`, also the
  planner's deferrals, each order's spend record, and every released
  order ([references/work-orders.md](references/work-orders.md)).

Recurring use: `/loop 30m` with this skill.

## Labels

| Label          | Meaning                                           |
| -------------- | ------------------------------------------------- |
| `ready`        | Available to claim                                |
| `in-progress`  | A worker has it                                   |
| `has-pr`       | PR open, in the gate or the train                 |
| `needs-review` | Partial work or a repeat flag; a human looks next |
| `agent-failed` | No usable change this time                        |
| `stealable`    | Failed twice; needs a different approach          |

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
