# Merge-train routine

The protocol for a scheduled `implement-queue` pass that only clears
open pull requests: Phase 0 (pre-flight) and Phase 3 (merge train) of
the [implement-queue skill](../../skills/implement-queue/SKILL.md),
under this repo's [queue profile](../../.claude/implement-queue.md)
and ADR-0096, which is the Owner's standing consent for the merges it
performs. It claims no issue and implements nothing: a PR that is not
yet green and reviewed is reported, not worked. Built on the mechanism
ADR-0044 decided for the daily routine and the shape the
[queue groomer](queue-groomer-routine.md) pilots; no new ADR.

Two facts frame every run:

- **The profile is the policy; this file is the schedule's shape.**
  Which PR may merge, what counts as the required check, which paths
  need a human, how a fast-path PR is reviewed — all of it is the
  queue profile's and ADR-0087's, read at run time, never restated or
  loosened here. Where this file and the profile disagree, the profile
  wins.
- **This file is not the routine's to edit.** Amendments are proposed
  in the run's journal comment (§7) and applied by the human.

## Markers on GitHub

Every marker this file names obeys the rules in
`docs/factory/routine-markers.md` (the MCP-only environment; find by
both forms, write raw then verify, never create on doubt); read it
before the first GitHub read or write. This file's own: the journal's
`<!-- factory-merge-train-journal -->` and the state line's
`<!-- merge-train-state last-run=... -->`. It opens no PR, so it has no
PR-body marker; its only writes are PR comments, `update-branch`
merges onto PR branches, merges into `main`, and the journal comment.

## 1 Preconditions and degrade ladder

Check in order; the first hit sets the run mode.

1. GitHub is unreachable — `gh auth status` fails and no GitHub MCP
   tool answers → record the failure in the session log and stop.
2. `FACTORY_PAUSED` is `true` (`gh variable list`) → **report-only
   mode**: survey and journal; no `update-branch`, no merge.
3. The queue profile is missing, or its `merge` key is not `auto` →
   **report-only mode**: the Owner's consent is the profile, and
   without it this routine merges nothing (ADR-0087).
4. `main` is red — the `preflight` hook (`gh run list --branch main
   --limit 5` by default) shows a failed `check` → **report-only
   mode**, naming the run. Fixing `main` is a human's or the daily
   routine's work, never this routine's.
5. Otherwise → **normal mode**.

## 2 Orient (read-only)

1. The queue profile, in full: `merge`, `required_check`,
   `hold_labels`, `gate_paths`, and the `fast-path`, `merge-command`
   and `update-branch` hooks.
2. This routine's journal (§6): its latest comment's
   `<!-- merge-train-state last-run=... -->` marker. First run → no
   prior state.
3. Every open PR (`gh pr list --state open`), with its checks rollup,
   labels, changed paths against `main`, review state, and whether its
   branch is behind `main`.
4. `docs/kb/cross-pr-merge-hazards.md`, so the train's one-at-a-time
   rule is read as the hazard it answers, not as caution.

## 3 Phase 0: verdict per PR

Implement-queue's pre-flight, run with nothing claimed. One line per
open PR, with its number, title, and exactly one verdict:

- **merge** — `required_check` present and green on the PR's current
  head; a review pass from a reviewer distinct from the author, or a
  `fast-path: low-risk` classification with no specialist matched
  (ADR-0088); no `gate_paths` file; no `hold_labels` label on the PR
  or its issue.
- **review first** — green, no gate path, no hold label, but no review
  pass yet and the fast path says `review (<path>)` or fails closed.
  The reviewer dispatch is implement-queue's Phase 2 gate, which this
  routine runs for such a PR; a `flag` or `block` ends in
  `needs-review` and no merge, per the reviewer contract.
- **human gate** — changes a `gate_paths` file, or carries a hold
  label. Reported with the path or label; never merged here.
- **wait** — checks pending, or a draft. Reported with what it waits
  on.
- **failed** — the required check failed. Reported with the failing
  job; implement-queue's "fix or label `agent-failed`" step is not run
  here, because this routine claims no work.

Each line names its reason. The whole list is the run's survey and
goes in the journal whatever the mode.

## 4 Phase 3: the train

In normal mode only, over the PRs whose verdict is **merge**, oldest
first, one at a time:

1. If the PR's branch is behind `main`, run the `update-branch` hook
   and wait for `required_check` to finish on the new head. Red →
   comment the failing job on the PR, report it as **failed after
   update**, and go to the next PR. The consent never covers a head
   that has not passed on the `main` it will land on
   (`docs/kb/cross-pr-merge-hazards.md`).
2. Re-check the four conditions on the current head: a label or a
   review can change while the train waits.
3. Run the `merge-command` hook. A merge the runtime denies is
   reported as **awaiting a human merge** with the denial, and is
   never retried by any other route in this run (ADR-0087).
4. Wait for the merge to land on `main` and for `main`'s `check` to
   finish before the next PR starts. Red `main` → stop the train,
   report it as §1's mode 4 would, and leave the remaining PRs for the
   next run.

Caps: one PR merging at a time; no `update-branch` on a PR whose
verdict is not **merge**; no retries of a denied merge; stop after
three consecutive **failed after update** verdicts.

## 5 Report lines

Every PR's verdict and reason from §3, then for each PR the train
touched: updated / merged / failed after update / awaiting a human
merge, with the run or denial it cites. PRs in **human gate** are
listed with the path or label so the Owner's next session is a list,
not a search.

## 6 Report and journal

This routine keeps its own journal issue, titled **Factory merge-train
journal**, body starting `<!-- factory-merge-train-journal -->`. Find it
by marker, in either form (§Markers on GitHub); create it only when
that search succeeded and found none. It is not pinned: GitHub allows
three pinned issues per repo and those slots are already contended.
Marker lookup never depends on the pin.

Exactly one journal comment per run:

```
<!-- merge-train-state last-run=<this run's start, ISO-8601 UTC> -->
**YYYY-MM-DD HH:MM — <normal | report-only | stopped>**: <merged N, awaiting human M, failed K>
- Verdicts: <one line per open PR: number, verdict, reason>
- Train: <per PR touched: updated / merged / failed after update / awaiting a human merge, with the citation>
- Health: <main red, profile missing, denials, marker repairs>
- Proposals: <amendments to this file or the profile, as diffs>
- Spend: <estimate for this run>
```

Spend is reported here and never appended to `docs/factory/costs.jsonl`,
exactly as ADR-0044 decided for the daily routine.

## 7 Non-negotiables

Re-read before the first `update-branch` or merge.

- Never merge a PR whose verdict is not **merge** on its current head,
  and never a PR that changes a `gate_paths` file or carries a hold
  label, whatever its author — including the Owner's own PRs.
- Never claim, create, close, label or comment on an issue; never open
  a PR; never push to a PR branch except through the `update-branch`
  hook.
- Never retry a denied merge, by any route (ADR-0087).
- Never merge two PRs at once, and never merge the next before
  `main`'s `check` has finished on the previous.
- Never edit this file, `docs/factory/routine-markers.md`, the queue
  profile, any schedule, or another routine's journal.
- Never run anything needing the `claude` CLI or an API key beyond the
  reviewer dispatch implement-queue's Phase 2 gate defines.
- Caps: one PR at a time; stop after three consecutive **failed after
  update**; one journal comment per run.

## 8 Amending this playbook

The routine proposes; the human applies. A proposed amendment is a
unified diff under Proposals with one line of rationale. Schedule
changes — cron, prompt, model — are proposed the same way and applied
by the human.

## Trigger

**Created 2026-10-15.** A scheduled trigger is recurring paid spend,
and the Owner explicitly approved this one on 2026-10-15, in session
("Create it: every 4h, Sonnet, no connectors"). Nothing in this file
authorizes creating, editing or running a trigger, and no agent or
routine does so on the strength of this file. It takes ADR-0044's
shape, as the queue groomer's does:

- **Name:** `factory-merge-train`.
- **Trigger id:** `trig_01HHqUqPCVA4ZuaaN1fHm5qH`, created 2026-10-15
  20:38 UTC. First scheduled run 2026-10-16 00:38 UTC; the two-week
  read for the merge-wait record (#912) starts there.
- **Cadence:** every 4 hours, stored as `38 */4 * * *` UTC (the
  recommendation was `0 */4 * * *`; the server set the minute), so a
  green PR waits at most one slot rather than for the next Owner
  session; the breakdown's merge-wait baseline is p90 13.5h.
- **Model:** Sonnet (`claude-sonnet-5-5`); the run reads state and
  calls hooks, and the reviewer dispatch uses the skill's model.
- **Connectors:** none — the create call attached every account
  connector despite an empty `mcp_connections`, as it did for the queue
  groomer; they were cleared at 20:38:51 UTC, before any run, and the
  read-back shows `[]`.
- **Environment:** `git`, and GitHub through the GitHub MCP tools; the
  `gh` CLI may be absent. Markers follow §Markers on GitHub. The
  `merge-command` hook needs the session permission ADR-0096 names.
- **Prompt:** a thin pointer to this file, plus duplicated hard limits
  as defense in depth: open PRs only, one merge at a time, never a
  gate path, never retry a denial, no self-edit.
- **Reporting:** the marker-found journal issue in §6.
- **Spend:** reported in the journal; excluded from the cost ledger
  exactly as ADR-0044 decided.
