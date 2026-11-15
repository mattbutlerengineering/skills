---
name: implement-queue
description: Use when a repo's backlog of ready GitHub issues, or of factory work orders, should be drained without the Owner answering each step — "work the queue", "drain the backlog", "implement the ready issues", "run the queue on a loop", a scheduled routine, or a direct invocation. Claims a batch of independent ready issues, implements each in its own worktree with a TDD worker agent, gates every PR through CI and a review by a distinct agent (held unreviewed when the profile has no `verdict` hook), then runs a serial merge train. It stops at reviewed, green PRs unless the repo's queue profile opts in to auto-merge (ADR-0087). Everything repo-specific — label transitions, gate commands, the required check, specialist reviewers, locks — comes from the repo's queue profile, never improvised. Work orders never merge here (ADR-0033 gate 3). Many items, nobody present — not conduct (the Owner present, answering every ask in session) and not autorun (one run through every stage).
metadata:
  author: Matt Butler
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

| Key | Default | Meaning |
| --- | --- | --- |
| `source` | `issues` | `issues`: plain `ready` issues. `work-orders`: factory work orders, per [references/work-orders.md](references/work-orders.md). An invocation that asks for work orders overrides it for that run. |
| `merge` | `off` | `off`: stop at reviewed, green PRs. `auto`: enqueue them for merge (see Merge policy). |
| `max_workers` | `3` | Workers in flight at once. |
| `required_check` | none | The check name that must be present and green (e.g. a CI gate job). |
| `hold_labels` | `[needs-review]` | A PR or issue carrying one is never merged by this skill. |
| `priority` | `[security, ci-fix, feature, audit]` | Label order for claiming; oldest first within a tier. |
| `gate_paths` | `[docs/adr/**, docs/design/**, **/prd.md, **/architecture.md]` | A PR changing a match, old path of a rename included, always needs a human merge (ADR-0036). |

Hooks (each a `## <name>` section with the exact command or rule):

| Hook | Default when absent |
| --- | --- |
| `preflight` | the gate's own green on the head SHA of `origin/main`, read from its check runs (Phase 0, step 2) |
| `transition` | `gh issue edit` swapping the state labels in the Labels table |
| `compose` | take candidates in priority order, skipping any that would change a file an issue already taken, or an open PR in the gate or the train, changes (Phase 1) |
| `promote` | none: no issue is promoted to `ready` ([lifecycle.md](references/lifecycle.md#the-promote-hook)) |
| `base-freshness` | `git fetch origin` and confirm this checkout shares history with `origin/main` |
| `worker` | a general worker agent given the Worker brief below |
| `model` | the worker's default model |
| `ci-status` | `gh pr checks <N>` plus the presence check below |
| `fast-path` | none: every PR is reviewed (with no `verdict` hook, every PR off the fast path is held unreviewed, [gate step 4](references/gate.md)) |
| `verdict` | none: a missing hook is an `error` verdict, never a pass (fail closed) |
| `reviewers` | one universal reviewer using [the reviewer contract](references/reviewer-contract.md); no specialists |
| `merge-command` | `gh pr merge <N> --auto --squash --delete-branch --match-head-commit <sha>` |
| `update-branch` | `gh pr update-branch <N>` |
| `changed-files` | `gh api repos/{owner}/{repo}/pulls/<N>/files --paginate`: every `filename` plus every `previous_filename`; its length must equal `gh api repos/{owner}/{repo}/pulls/<N> --jq .changed_files`, else fail closed |
| `lock` | none: one session at a time is the only lock |
| `reap` | none: report worker worktrees left behind |
| `telemetry` | none |

In every `merge-command`, `<sha>` is the gated head ([gate step 1](references/gate.md)), never
a head read at merge time. A merge refused because the PR's head is no
longer `<sha>` is a moved head, not a failure to retry: the PR goes back
through the gate. The pin guards the moment the merge is requested; a
push after `--auto` is enabled is Phase 3's to catch.

**Cloud sessions.** Each hook's REST and MCP twin:
[cloud-sessions.md](references/cloud-sessions.md).

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
   The default's reads, wait and re-run:
   [preflight.md](references/preflight.md#step-2-the-default-preflight-read).
3. Read every open PR (`gh pr list --state open --limit 1000 --json number,title,headRefOid,labels,body`;
   cloud twin in [the list above](references/cloud-sessions.md)). The REST twin is paged, so read every
   page of `gh api 'repos/{owner}/{repo}/pulls?state=open&per_page=100'`
   (`.head.sha` is the head). A list that may be truncated (its count
   equals the limit, or a page is missing) fails closed: claim nothing
   and report it. A PR belongs to this queue when it closes an issue
   carrying `in-progress`, `has-pr`, `needs-review`, `agent-failed` or
   `stealable` and its body has no `Driver:` line naming a driver other
   than `implement-queue`; every other PR is foreign (another agent's, a
   bot's, a routine's). A PR whose `Driver:` line names another driver
   is that driver's, which claimed its issue through
   [the claim step](references/claim.md). A PR the evidence says must
   not merge (the third cause below) is never gated, re-run toward green
   or merged by this queue
   in any CI state, a revert someone else re-ran to green included; it
   is reported. Unfinished PRs come before new issues: green ones go to
   the Phase 2 gate, pending ones wait, failed ones of this queue get
   fixed or their issue labelled `agent-failed`, which stops them blocking
   ([the `agent-failed` cause](references/preflight.md#step-3-failed-pr-causes-and-settled-green-prs)). A foreign green PR goes
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

   The causes, and when a green PR is settled:
   [preflight.md](references/preflight.md#step-3-failed-pr-causes-and-settled-green-prs).

4. Look for another queue session, and report it before claiming:
   [preflight.md](references/preflight.md#step-4-another-queue-session).
5. Count the backlog's leaks (stale `has-pr`, no state label,
   `agent-failed`, stale `in-progress`), and apply the closed-unmerged rule to each `has-pr` issue
   whose PRs all closed unmerged: [lifecycle.md](references/lifecycle.md#phase-0-step-5-count-the-leaks).

## Phase 1: Claim a batch

Under `source: work-orders`, the planner and the `wo:*` claim in
[references/work-orders.md](references/work-orders.md) replace this
phase.

    gh issue list --label ready --state open --json number,title,body,labels

In a cloud session (see [Cloud sessions](references/cloud-sessions.md) above):
`gh api 'repos/{owner}/{repo}/issues?labels=ready&state=open&per_page=100'`,
dropping every entry that carries a `pull_request` key — the REST
issues endpoint lists pull requests too.

Sort by the profile's `priority`, oldest first within a tier; a security
issue always gets a slot. Drop any issue that:

- names an open dependency (`Depends on: #N` with `#N` open);
- carries `in-progress`, `stealable`, or a `hold_labels` label;
- carries a `wo:*` label: a factory work order belongs to
  `source: work-orders`, so the two sources never race for one issue;
- would change a file that an issue already taken in this batch would
  change, or that an open PR closing an `in-progress` or `has-pr`
  issue changes (run the `compose` hook when the profile has one).
  Two workers on one file end in a merge conflict or an
  `update-branch` commit, and each costs a CI run and can void a
  review. Without a hook, an issue's files are the repo paths its
  title and body name; when it names none, the one file that defines
  the skill, tool, workflow or document it is about. An issue whose
  files cannot be told collides with nothing and is reported as
  `files unknown`. An open PR's files come from the `changed-files`
  hook, and a list that fails closed there counts as changing every
  file. A dropped issue keeps `ready`, is reported with the path and
  the issue or PR it waits for, and is claimed in a later iteration.

Fewer than `max_workers` left → run the `promote` hook, if any, once:
[lifecycle.md](references/lifecycle.md#the-promote-hook).

Take at most `max_workers`, and claim each with
[the claim step](references/claim.md), the one claim every driver of
`ready` issues in the repo runs (ADR-0130). Dispatch no worker for an
issue until that file says the claim holds; an issue it skips is not
claimed by this session and is reported.

## Phase 2: Implement, then gate

**Before dispatching**, run the `base-freshness` hook. Worktrees are cut
from this checkout's object store, so a stale or unrelated base is
inherited by every worker. Fail closed: an undeterminable base is never
usable.

Dispatch one worker per issue, **all in one message**, each with its own
worktree (`isolation: "worktree"`) and the model the `model` hook
resolves. Dispatch is never held by the merge-train lock: capacity
(`max_workers`) is the only limit on starting work.
The [wall-clock bound](references/worker-finish.md#wall-clock-bound) runs from dispatch.

**Harness needs.** The fallbacks for a harness without the Agent
tool's features: [harness-needs.md](references/harness-needs.md).

### Worker brief

Under `source: work-orders`, use the work-order brief in
[references/work-orders.md](references/work-orders.md) instead.

Every worker prompt carries the items in [worker-brief.md](references/worker-brief.md).

When a worker finishes, label its issue with the `transition` hook:

| Outcome | State |
| --- | --- |
| PR open, gates green | `has-pr` |
| Partial work (draft PR) | `needs-review` |
| Investigated: no repo change can fix it, evidence posted | `needs-review` |
| Already resolved on `main`, no change needed, evidence posted | closed ([lifecycle.md](references/lifecycle.md#already-resolved)) |
| No usable change | `agent-failed` |
| Second failure on the same issue | `stealable` |
| PR closed unmerged, the issue's first ([rule](references/lifecycle.md#a-pr-closed-unmerged)) | `ready` |
| PR closed unmerged, the issue's second or later | `needs-review` |

Then run the `telemetry` hook, if any, with the worker's real usage.
Leave cost empty when the usage carries none; never estimate it.

[Missing usage, the wall-clock bound and reconcile](references/worker-finish.md).

### The gate, per PR

This is the last check before a merge. Run it for each worker PR as soon
as its head is recorded (step 1), without waiting for its CI; it can
overlap with workers still running.

Steps 1 Head and CI, 2 Holds, 3 Fast path, 4 Review, 5 Verdict:
[gate.md](references/gate.md).

## Merge policy

Under `merge: off` (the default) a PR that passes the gate is left for
the human merge, ADR-0033's gate 3, with no label change (`has-pr`
stays), and the report lists it as
**reviewed, green, awaiting merge**. This skill merges nothing.

Under `source: work-orders` the merge is always off, whatever `merge:`
says: a work order's merge is the human's (ADR-0033 gate 3).

Under `merge: auto` (ADR-0087) the profile is the Owner's standing
consent, and a PR that passes every gate step is enqueued with the
`merge-command` hook. The consent never covers a PR that:

- lacks a pass from a reviewer distinct from its author, unless it took
  the fast path ([step 3](references/gate.md)): the `fast-path` hook's low-risk
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

A merge the session's runtime or the Owner refuses (a permission
refusal) is not retried by any route for the rest of the session. Comment the derived verdict line ([step 5](references/gate.md)) on the PR and report it as
awaiting a human merge. A GraphQL 403 or `spawn gh ENOENT` is a
capability gap, not a refusal: [run the twin](references/cloud-sessions.md#a-capability-gap-is-not-a-permission-refusal).

## Phase 3: Merge train

Its steps and lock release: [merge-train.md](references/merge-train.md).

## Phase 4: Loop or stop

[Reconcile](references/worker-finish.md#reconcile-before-phase-4) first.

- Run the `reap` hook. A worker that committed keeps its worktree, so
  nothing else reclaims it; a reaper must refuse any worktree with an
  open PR or a live process, and needs positive evidence of a merge.
- Remove empty worktrees this session's dispatch cut:
  [loop-and-cleanup.md](references/loop-and-cleanup.md#empty-worktrees).
- Persist the telemetry the session appended:
  [loop-and-cleanup.md](references/loop-and-cleanup.md#telemetry-persistence).
- More ready issues and budget left → Phase 0. Three consecutive failures
  (workers or train) → release locks, stop and report. The evidence
  outcome (a worker's issue left `needs-review` with its evidence
  posted) and the already-resolved outcome are not failures: they leave
  the count unchanged. Report each with its evidence.
- Report: issues claimed, PRs opened, PRs merged or awaiting merge, and
  every failure with its cause, and Phase 0 step 5's four counts
  ([as lifecycle.md words them](references/lifecycle.md#phase-0-step-5-count-the-leaks)) even
  with no batch; with no `verdict` hook under `merge: auto`,
  also that every merge in the run took the fast path unreviewed.
  Under `source: work-orders`, also the
  planner's deferrals, each order's spend record, and every released
  order ([references/work-orders.md](references/work-orders.md)).

Recurring use: `/loop 30m` with this skill.
An iteration in flight:
[loop-and-cleanup.md](references/loop-and-cleanup.md#recurring-use).

## Labels

| Label | Meaning |
| --- | --- |
| `ready` | Available to claim |
| `in-progress` | A worker has it |
| `has-pr` | PR open, in the gate or the train |
| `needs-review` | Partial work, a repeat flag, or evidence that no repo change can fix it; a human looks next |
| `agent-failed` | No usable change this time |
| `stealable` | Failed twice; needs a different approach |

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
  in the merge train, adopted only on the conditions of [Phase 3 step 3](references/merge-train.md).
- Discovery (audits, error triage, dependency alerts) feeds the queue;
  this skill only drains it.
