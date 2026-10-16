---
name: implement-queue
description: Use when a repo's backlog of ready GitHub issues should be drained without the Owner answering each step — "work the queue", "drain the backlog", "implement the ready issues", "run the queue on a loop", a scheduled routine, or a direct invocation. Claims a batch of independent ready issues, implements each in its own worktree with a TDD worker agent, gates every PR through CI and a review by a distinct agent, then runs a serial merge train. It stops at reviewed, green PRs unless the repo's queue profile opts in to auto-merge (ADR-0087). Everything repo-specific — label transitions, gate commands, the required check, specialist reviewers, locks — comes from the repo's queue profile, never improvised. Not work-queue (factory work orders, never merges) and not conduct (the Owner answers every ask in session).
---

# Implement Queue

Drain a repo's `ready` issues: parallel implementation, serial merging.
This skill is the loop; the repo's **queue profile** supplies every
fact about that repo.

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
| `merge`          | `off`                                                          | `off`: stop at reviewed, green PRs. `auto`: enqueue them for merge (see Merge policy). |
| `max_workers`    | `3`                                                            | Workers in flight at once.                                                             |
| `required_check` | none                                                           | The check name that must be present and green (e.g. a CI gate job).                    |
| `hold_labels`    | `[needs-review]`                                               | A PR or issue carrying one is never merged by this skill.                              |
| `priority`       | `[security, ci-fix, feature, audit]`                           | Label order for claiming; oldest first within a tier.                                  |
| `gate_paths`     | `[docs/adr/**, docs/design/**, **/prd.md, **/architecture.md]` | A PR changing a match always needs a human merge (ADR-0036).                           |

Hooks (each a `## <name>` section with the exact command or rule):

| Hook             | Default when absent                                                                                   |
| ---------------- | ----------------------------------------------------------------------------------------------------- |
| `preflight`      | `gh run list --branch main --limit 5` — any failure means main is red                                 |
| `transition`     | `gh issue edit` swapping the state labels in the Labels table                                         |
| `compose`        | take candidates in priority order, skipping any that names the same files as one already taken        |
| `base-freshness` | `git fetch origin` and confirm this checkout shares history with `origin/main`                        |
| `worker`         | a general worker agent given the Worker brief below                                                   |
| `model`          | the worker's default model                                                                            |
| `ci-status`      | `gh pr checks <N>` plus the presence check below                                                      |
| `fast-path`      | none: every PR is reviewed                                                                            |
| `reviewers`      | one universal reviewer using [the reviewer contract](references/reviewer-contract.md); no specialists |
| `merge-command`  | `gh pr merge <N> --auto --squash --delete-branch`                                                     |
| `update-branch`  | `gh pr update-branch <N>`                                                                             |
| `lock`           | none: one session at a time is the only lock                                                          |
| `reap`           | none: report worker worktrees left behind                                                             |
| `telemetry`      | none                                                                                                  |

**Cloud sessions.** Each `gh` command in this file states an intent;
the environment may offer only the GitHub MCP tools or the REST API
through `gh api`, and either carries it out. In Claude Code Remote the
GraphQL-backed `gh issue|pr` subcommands (`list`, `view`, `edit`,
`checks`, `merge`, `update-branch`) return HTTP 403 while `gh api`
REST calls succeed, so a profile written for a cloud session names the
REST twin of each default above (`preflight`'s `gh run list` is REST
already):

- `transition`: `gh api -X POST repos/{owner}/{repo}/issues/<N>/labels -f 'labels[]=<to>'`
  then `gh api -X DELETE repos/{owner}/{repo}/issues/<N>/labels/<from>`,
  one pair per swap in the Labels table.
- `ci-status`: `gh api repos/{owner}/{repo}/commits/<head-sha>/check-runs`,
  with `<head-sha>` from `gh api repos/{owner}/{repo}/pulls/<N> --jq .head.sha`.
- `merge-command`: `gh api -X PUT repos/{owner}/{repo}/pulls/<N>/merge -f merge_method=squash`
  once `ci-status` is green, then
  `gh api -X DELETE repos/{owner}/{repo}/git/refs/heads/<branch>`.
  REST has no `--auto`: the train merges a green PR itself instead of
  enqueuing it.
- `update-branch`: `gh api -X PUT repos/{owner}/{repo}/pulls/<N>/update-branch`.

A hook can tighten a default rule; it can never loosen a rule in this
file's Rules section.

## Phase 0: Pre-flight

1. Run the `preflight` hook. If main is red, fixing it **is** this
   iteration: claim or file the CI-fix issue, work it through Phase 2,
   and skip to Phase 3.
2. List open PRs. Unfinished PRs come before new issues: green ones go
   to the Phase 2 gate, pending ones wait, failed ones get fixed or
   their issue labelled `agent-failed`. Claim nothing new while an open
   PR is failed. This is the protocol's "Open pull requests first"
   pre-flight (`../../docs/pipeline-protocol.md`) with this skill's
   mechanics; merges still follow the Merge policy below.

## Phase 1: Claim a batch

    gh issue list --label ready --state open --json number,title,body,labels

In a cloud session (see Cloud sessions above):
`gh api 'repos/{owner}/{repo}/issues?labels=ready&state=open&per_page=100'`,
dropping every entry that carries a `pull_request` key — the REST
issues endpoint lists pull requests too.

Sort by the profile's `priority`, oldest first within a tier; a security
issue always gets a slot. Drop any issue that:

- names an open dependency (`Depends on: #N` with `#N` open);
- carries `in-progress`, `stealable`, or a `hold_labels` label;
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

When a worker finishes, label its issue with the `transition` hook:

| Outcome                          | State          |
| -------------------------------- | -------------- |
| PR open, gates green             | `has-pr`       |
| Partial work (draft PR)          | `needs-review` |
| No usable change                 | `agent-failed` |
| Second failure on the same issue | `stealable`    |

Then run the `telemetry` hook, if any, with the worker's real usage.
Leave cost empty when the usage carries none; never estimate it.

### The gate, per PR

This is the last check before a merge. Run it for each worker PR as soon
as that PR's CI settles; it can overlap with workers still running.

1. **CI.** Run the `ci-status` hook. With a `required_check`, green
   means that check is **present and successful**. A rollup with no
   failures and no pending checks is not green when the required check
   never ran: treat a missing check as its own state, re-trigger CI once
   if the repo's hook says how, and never enqueue on it.
2. **Holds.** A `hold_labels` label on the PR or its issue ends the gate
   here: no review, no merge.
3. **Fast path.** If the `fast-path` hook says the diff is low-risk
   **and** no specialist reviewer matches it, skip step 4. That
   classification counts as the review for the Merge policy (ADR-0088). If the hook
   cannot prove its own inputs are current (a stale build, an unreadable
   classifier), fail closed: review the PR and dispatch every specialist.
4. **Review.** Dispatch the universal reviewer, plus each specialist
   the `reviewers` hook matches to the changed files, with the input
   [the reviewer contract](references/reviewer-contract.md) defines. A
   reviewer is never the PR's author.
   - Snapshot `git status --porcelain` before each reviewer dispatch and
     compare it afterwards. A reviewer that changed the checkout has
     produced an invalid verdict: inspect, restore, re-dispatch.
   - A review that timed out or errored is recorded as `error`, never as
     `pass`.
5. **Verdict.** All pass → the Merge policy. A `flag` or a specialist
   `block` → the contract's retry policy (one retry on the same branch,
   then `needs-review` and no merge).

## Merge policy

Under `merge: off` (the default) a PR that passes the gate is labelled
for the human merge, ADR-0033's gate 3, and the report lists it as
**reviewed, green, awaiting merge**. This skill merges nothing.

Under `merge: auto` (ADR-0087) the profile is the Owner's standing
consent, and a PR that passes every gate step is enqueued with the
`merge-command` hook. The consent never covers a PR that:

- lacks a pass from a reviewer distinct from its author, unless it took
  the fast path (step 3): the `fast-path` hook's low-risk
  classification is the Owner's written review for it (ADR-0088);
- lacks the `required_check` present and green;
- carries a `hold_labels` label.
- changes a file `gate_paths` matches.

A merge the session's runtime denies is not retried by any route for
the rest of the session. Comment the verdict on the PR and report it as
awaiting a human merge.

## Phase 3: Merge train

Enqueued PRs merge as their checks go green. This phase unsticks the
ones that fell behind `main` after a sibling merged:

1. Take the `lock` hook's lock for the PR's zone before touching its
   branch. If another session holds it, leave that zone alone this
   iteration and report it.
2. Run the `update-branch` hook. Where the repo's lockfile can drift on
   a server-side update, the hook says how to rebase and regenerate it
   instead.
3. A red check after the update gets one small fix in this session, or a
   CI-fix issue and `agent-failed` on the original. It counts toward the
   circuit breaker.

Release every lock you took when the train ends, on any exit.

## Phase 4: Loop or stop

- Run the `reap` hook. A worker that committed keeps its worktree, so
  nothing else reclaims it; a reaper must refuse any worktree with an
  open PR or a live process, and needs positive evidence of a merge.
- Persist telemetry the session appended: an ephemeral checkout loses it.
- More ready issues and budget left → Phase 0. Three consecutive failures
  (workers or train) → release locks, stop and report.
- Report: issues claimed, PRs opened, PRs merged or awaiting merge, and
  every failure with its cause.

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
- Discovery (audits, error triage, dependency alerts) feeds the queue;
  this skill only drains it.
