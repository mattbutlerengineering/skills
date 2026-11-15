# Phase 3: Merge train

Moved verbatim from [SKILL.md](../SKILL.md), which links here from the step
that needs it. A phrase such as "this file", "above", "below" or
"the Rules" can name SKILL.md or a part of it.

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
