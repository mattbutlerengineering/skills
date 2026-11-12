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
quoted argument and only once it reads as a bare finite number from 0
to 10: the score is
the reviewer's text, never a shell fragment. The reviewer is
told no pass line and the threshold lives only in this tool. Exit 0
prints `reviewer-verdict: pass (score N/10)`, exit 1 prints
`reviewer-verdict: flag (score N/10)`, exit 2 prints
`reviewer-verdict: error (<reason>)` (no usable score, or a wrong
argument count). Act on the exit code only; post the printed line
verbatim as the first line of the PR's verdict comment. A hook-side
`error` (a missing hook, a hook that did not run, or any exit code
other than 0 or 1 on a usable score: a wrong argument count gives 2, a
killed process 137) is held for a human at once,
with no re-dispatch. A reviewer-side `error` (a timeout, or a `score`
that is not a bare finite number from 0 to 10, which the orchestrator
checks before running the hook) is re-dispatched once, then held.
Under `merge: auto` an `error` never merges. A `verdict` the reviewer
returns itself is ignored.

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

    gh pr merge <N> --auto --squash --delete-branch --match-head-commit <sha>

The skill's default, stated because it needs a session permission the
Owner grants outside this repo. `<sha>` is the gated head (the skill's
gate step 1), so an `--auto` merge is enabled only at the head the
review saw. A merge the runtime denies is reported
as awaiting a human merge and never retried by another route
(ADR-0087).

`--delete-branch` has left the remote branch behind in this repo (#1636),
so delete it yourself once `gh pr view <N> --json
state,headRefName,headRefOid,isCrossRepository` reports `MERGED`. If the
PR is not yet `MERGED` (an `--auto` merge waiting on checks), do nothing
now and repeat this step when it is. Delete only when all of these hold,
and otherwise leave the branch alone and report it by name. Each command
must exit 0: a failed `gh` or `git` call is a failure, never an empty
result.

1. `isCrossRepository` is `false`.
2. `<headRefName>` is not the default branch (`main`).
3. `gh pr list --base <headRefName> --state open --json number` exits 0
   and prints `[]`, so no open PR is stacked on it.
4. `git ls-remote origin refs/heads/<headRefName>` exits 0 and prints
   exactly one line, and its commit equals `headRefOid`. The full ref is
   required: `--heads <name>` also matches any branch whose name ends in
   it. A different commit means the branch carries later commits. No
   line at all means the branch is already gone: nothing to do, and
   nothing to report.

Then pin the delete to that commit, so a push that lands after the check
is refused instead of deleted:

    git push --force-with-lease=refs/heads/<headRefName>:<headRefOid> origin --delete refs/heads/<headRefName>

A refused push leaves the branch: report it by name, and never retry the
delete without the lease or by another route (the lease is the race
protection).

## update-branch

    gh pr update-branch <N>

The skill's default, stated because the merge train depends on it: one
PR at a time, `update-branch`, then a green `check` against the main of
that moment before the next PR starts (`docs/kb/cross-pr-merge-hazards.md`).

## reap

The hook is `python3 reap_worktrees.py --apply` (no flag: a dry run that
removes no worktree or branch; `--no-fetch` makes the dry run offline);
that tool implements this section, and the rules below are its
definition. It runs `git fetch origin --prune` first, which prunes
remote-tracking refs, and removes nothing if the fetch fails. For each worktree that
`git worktree list --porcelain` lists under `.claude/worktrees/`,
apply all four tests; any failure leaves the worktree and its branch
alone and reports the path with the failed test. `<branch>` below is
the porcelain `branch` line without its `refs/heads/` prefix, and
`<tip>` is the worktree's `HEAD` commit:

1. **Clean.** `git -C <path> status --porcelain --untracked-files=all
   --ignore-submodules=none` exits 0 and prints nothing on stdout (the
   two flags override a repo's `status.showUntrackedFiles` and
   `diff.ignoreSubmodules`, which would hide untracked files or a dirty
   submodule). `git -C <path> ls-files -v` also exits 0, and any line
   whose tag is lowercase (assume-unchanged) or `S` (skip-worktree) is
   dirty when its file exists in the worktree, because those flags hide
   edits from `status`; a flagged file that is absent is no edit (`git
   sparse-checkout` flags every file outside its cone), so a sparse
   worktree is not dirty for that. A failed `git`
   call is a failure, not a clean tree. "Clean" means exactly that:
   gitignored files (for example `.env`, `plugin-evals/results/`,
   `__pycache__`) are not checked and are deleted with the worktree, on
   purpose.
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
   refs/remotes/origin/main` exits 0 (the full ref: a bare `origin/main`
   resolves a local branch or tag of that name first, and an unmerged
   branch so named would pass). A merged PR for the branch *name* is not
   evidence: a branch that gained commits after its PR merged, or
   reused the name, fails here. A tip no merged PR carries, on a branch
   with no PR, is unmerged work, never reaped.

On a pass, `git worktree remove <path>` (never `--force`), then, if it
had a branch other than `main`, `git branch -D -- <branch>` (the `--` keeps a branch named `-x` from
parsing as an option): the squash merge leaves the
branch off `refs/remotes/origin/main`'s history, so `-d` would refuse a branch that
test 4 already proved merged. A locked worktree (`git worktree lock`) is kept, never
reaped, and so is a worktree that is a parent directory of another
listed worktree, decided by file identity (`os.path.samefile`), not path
text, so a case-variant spelling on a case-insensitive filesystem still
counts (`.git/info/exclude` hides the nested one from the outer's
`status` and from `git worktree remove`'s own check, so reaping the outer
would delete the inner's work). Never touch a worktree outside
`.claude/worktrees/`, and never the checkout the session runs in.
