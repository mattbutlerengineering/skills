# Worker brief

Moved verbatim from [SKILL.md](../SKILL.md), which links here from the step
that needs it. A phrase such as "this file", "above", "below" or
"the Rules" can name SKILL.md or a part of it.

Every worker prompt carries:

1. The issue number, title and full body.
2. First steps: the base-freshness check and the repo's dependency
   install (worktrees have none).
3. TDD per vertical slice: a failing test first, then the minimal code.
4. The repo's gates on the affected code before declaring done, typecheck
   included where the language has one.
5. Push the branch and open a PR with `Closes #<N>`; confirm its base is
   `main`. End the PR body with the line `Driver: implement-queue`, which
   marks the PR as queue-driven; Phase 0 step 3 reads the `Driver:` line
   to tell this queue's PRs from another driver's. Never merge.
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
   outcome. When the issue is already fixed on `main`, post the merged
   PR or a measurement anyone can repeat on the issue, open no PR and
   report the already-resolved outcome. Never invent a change to have
   something to push.
10. Say in the result which checks were not verified locally: list under
   `not verified locally` every CI check the PR will face that you did
   not or could not run, each with the reason. `has-pr` then means local
   gates green, so the orchestrator knows which checks to watch first.
   A profile may name checks that commonly fail only in CI (a secret
   scan, bundle size, generated-artifact drift) in its own prose, as a
   hint; when it does, the orchestrator repeats it in the brief.
11. Finish or hand off within 45 minutes from dispatch, and answer the
   orchestrator's check-in at once.
12. Before opening the PR, check your diff against the four catch classes
   of [the reviewer contract](reviewer-contract.md) (what the
   review catches): hallucination, regression, gate bypass and criteria
   gap. That path is relative to this skill, so the orchestrator writes
   the contract's catch-class list, or its absolute path, into this item
   of the brief. Check the diff against each acceptance criterion too,
   and list in the result each criterion with how you verified it. Apart
   from an existing vulnerability (item 6), change nothing the issue does
   not ask for: a case you find outside its ask is named in the PR body,
   not implemented.
