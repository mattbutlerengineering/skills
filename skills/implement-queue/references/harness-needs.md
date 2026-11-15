# Harness needs and their fallbacks

Moved verbatim from [SKILL.md](../SKILL.md), which links here from the step
that needs it. A phrase such as "this file", "above", "below" or
"the Rules" can name SKILL.md or a part of it.

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
[references/work-orders.md](work-orders.md), not the
orchestrator-cut worktree.
