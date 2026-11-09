---
merge: auto
required_check: check
hold_labels: [needs-review]
gate_paths:
  - "docs/adr/**"
  - "docs/design/**"
  - "**/prd.md"
  - "**/architecture.md"
  - "**/autorun-brief.md"
  - "factory/templates/**"
  - ".github/**"
  - ".claude-plugin/plugin.json"
  - "docs/factory/**"
  - "docs/pipeline-protocol.md"
  - "docs/standards.json"
---

# Queue profile: this repo

The Owner's standing configuration for the `implement-queue` skill
here, under ADR-0096 (which applies ADR-0087's opt-in auto-merge and
ADR-0088's fast path to this repo). The frontmatter is the policy; each
section below is one hook, as the skill's "The queue profile" section
defines them. Keys and hooks not stated keep the skill's defaults. This
file changes only by a PR: its commit is the consent record.

- `merge: auto` — a PR that passes every gate step is enqueued with the
  `merge-command` hook. ADR-0087's four conditions apply to every open
  PR, whatever its author or branch: `required_check` present and
  green, an independent review passed (or the fast path below), no
  `gate_paths` file, no `hold_labels` label.
- `required_check: check` — the validator workflow's gate job, which
  runs `make check`. A rollup with no `check` run is not green.
- `gate_paths` — ADR-0087's defaults plus `factory/templates/**`,
  `.github/**` and `.claude-plugin/plugin.json`: release PRs (ADR-0095),
  workflow changes and the stamped payload keep a human merge. ADR-0121
  adds the instruction docs agents obey (`docs/factory/**`,
  `docs/pipeline-protocol.md`, `docs/standards.json`): a docs-only PR
  cannot rewrite them unreviewed. ADR-0122 adds `**/autorun-brief.md`:
  a resume obeys the brief's release authorization, so a brief edit
  keeps a human merge. `tests/test_fast_path.py` pins this
  list equal to the classifier's.

## fast-path

    python3 fast_path.py origin/main HEAD

Run in the PR's checkout after `git fetch origin`. Exit 0 prints
`fast-path: low-risk`: every changed path is under `docs/` and none is
a gate path, and the classification is the review for a PR no
specialist matches (ADR-0088). Exit 1 prints `fast-path: review
(<path>)`: review the PR. Exit 2 prints a `fast-path:` problem string
(git failed, a ref did not resolve): fail closed, review the PR and
dispatch every specialist.

## verdict

    python3 reviewer_verdict.py <score>

Run on the universal reviewer's `score` (ADR-0123), passed as one
quoted argument and only once it reads as a bare number: the score is
the reviewer's text, never a shell fragment. The reviewer is
told no pass line and the threshold lives only in this tool. Exit 0
prints `reviewer-verdict: pass (score N/10)`, exit 1 prints
`reviewer-verdict: flag (score N/10)`, exit 2 prints
`reviewer-verdict: error (<reason>)` (no usable score, or a wrong
argument count). Act on the exit code only; post the printed line
verbatim as the first line of the PR's verdict comment. Exit 2, a hook
that did not run, or a missing hook is `error`: re-dispatch the
reviewer once, then hold the PR for a human. Under `merge: auto` an
`error` never merges. A `verdict` the reviewer returns itself is
ignored.

## changed-files

    python3 fast_path.py gate origin/main HEAD

The source of the `gate_paths` check, run in the PR's checkout after
`git fetch origin`. It reads `git diff --name-only -z --no-renames
origin/main...HEAD`, so a rename lists its old path and its new one
(the same list as `fast-path`, one `changed_paths` call), and `-z`
lists a non-ASCII or quote-bearing name as written, not quoted. Exit 0 prints
`gate-paths: clear`: no changed path is a gate path. Exit 1 prints
`gate-paths: human (<path>)`: a human merge, and `<path>` may be the old
path of a rename. Exit 2 prints a `fast-path:` problem string (git
failed, a ref did not resolve): fail closed, a human merge.

With no checkout, the source is the REST file list, never
`gh pr diff --name-only` or `gh pr view --json files`, which drop a
rename's old path (the second also stops at 100 files):

    gh api repos/{owner}/{repo}/pulls/<N>/files --paginate

Take every `filename` **and** every `previous_filename` and match each
against `gate_paths`. Without `--paginate`, or if the call fails, fail
closed. The list's length must equal the PR's `changed_files`:

    gh api repos/{owner}/{repo}/pulls/<N> --jq .changed_files

A different length (the endpoint stops at 3000 files and flags no
truncation) fails closed. A GitHub MCP file-list tool is
not a source until a run records that it reports `previous_filename`.

## merge-command

    gh pr merge <N> --auto --squash --delete-branch

The skill's default, stated because it needs a session permission the
Owner grants outside this repo. A merge the runtime denies is reported
as awaiting a human merge and never retried by another route
(ADR-0087).

`--delete-branch` has left the remote branch behind in this repo (#1636),
so delete it yourself once `gh pr view <N> --json
state,headRefName,headRefOid,isCrossRepository` reports `MERGED`. If the
PR is not yet `MERGED` (an `--auto` merge waiting on checks), do nothing
now and repeat this step when it is. Delete only when all of these hold,
and otherwise leave the branch alone and report it by name:

1. `isCrossRepository` is `false`.
2. `<headRefName>` is not the default branch (`main`).
3. `gh pr list --base <headRefName> --state open --json number` is
   empty, so no open PR is stacked on it.
4. `git ls-remote origin refs/heads/<headRefName>` prints exactly one
   line, and its commit equals `headRefOid`. The full ref is required:
   `--heads <name>` also matches any branch whose name ends in it.

Then pin the delete to that commit, so a push that lands after the check
is refused instead of deleted:

    git push --force-with-lease=refs/heads/<headRefName>:<headRefOid> origin --delete refs/heads/<headRefName>

A remote tip that differs from `headRefOid` carries later commits.

## update-branch

    gh pr update-branch <N>

The skill's default, stated because the merge train depends on it: one
PR at a time, `update-branch`, then a green `check` against the main of
that moment before the next PR starts (`docs/kb/cross-pr-merge-hazards.md`).

## reap

Run after `git fetch origin --prune`. For each worktree that
`git worktree list --porcelain` lists under `.claude/worktrees/agent-*`,
apply all four tests; any failure leaves the worktree and its branch
alone and reports the path with the failed test. `<branch>` below is
the porcelain `branch` line without its `refs/heads/` prefix, and
`<tip>` is the worktree's `HEAD` commit:

1. **Clean.** `git -C <path> status --porcelain` exits 0 and prints
   nothing on stdout. A failed `git` call is a failure, not a clean tree.
2. **Idle.** `lsof` is on `PATH`, `<path>` exists, and `lsof -w +D
   <path>` prints nothing on stdout or stderr. `-w` silences all of
   lsof's warnings, so one on an unreadable mount cannot block every
   reap; an error that stops the scan still reaches stderr. `lsof` exits
   1 for both an idle directory and an error, so read the output, never
   the exit status; any stderr output is a failure.
3. **No open PR.** `gh pr list --head <branch> --state open` exits 0 and
   prints nothing on stdout (`gh` writes its "no matches" notice to
   stderr on a terminal). A failed `gh` call is a failure, not an empty
   list. A detached worktree has no branch and skips this test.
4. **Positive evidence that this tip merged.** Either `<tip>` is a
   `headRefOid` in `gh pr list --head <branch> --base main --state
   merged --json headRefOid`, or `git merge-base --is-ancestor <tip>
   origin/main` exits 0. A merged PR for the branch *name* is not
   evidence: a branch that gained commits after its PR merged, or
   reused the name, fails here. A tip no merged PR carries, on a branch
   with no PR, is unmerged work, never reaped.

On a pass, `git worktree remove <path>` (never `--force`), then, if it
had a branch, `git branch -D <branch>`: the squash merge leaves the
branch off `origin/main`'s history, so `-d` would refuse a branch that
test 4 already proved merged. Never touch a worktree outside
`.claude/worktrees/`, and never the checkout the session runs in.
