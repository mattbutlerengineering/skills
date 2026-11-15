# Phase 4: worktree cleanup, telemetry persistence, recurring use

Moved verbatim from [SKILL.md](../SKILL.md), which links here from the step
that needs it. A phrase such as "this file", "above", "below" or
"the Rules" can name SKILL.md or a part of it.

## Empty worktrees

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

## Telemetry persistence

- Persist the telemetry the session appended, once per iteration, not
  per worker: an ephemeral checkout loses it, and one PR per row races
  its own auto-merge. Batch every row the iteration appended into one
  commit on one branch. Name the branch for the session as well as the
  date (`chore/queue-telemetry-<date>-<session-id>`), so two sessions
  never share one. Restore or rebase the tracked metrics file from
  `origin/main` after `git fetch origin`, never from the local `main`,
  which may be stale.

## Recurring use

The interval is a minimum gap between iterations, not a bound on one
iteration, and an iteration that waits on CI can outlast it. A
re-invocation in the same session while an iteration is in flight
continues that iteration and never starts a second one: a loop tick
that fires then joins the one in flight and does nothing new, and the
next iteration starts only after the report. A session with no memory
of an iteration in flight cannot tell, and Phase 0 step 4 shows it the
`in-progress` issues and recently pushed PRs that iteration holds, which
it leaves alone like any other listed there.
