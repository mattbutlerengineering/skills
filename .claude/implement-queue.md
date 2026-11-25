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

    python3 tools/fast_path.py origin/main <sha>

`<sha>` is the recorded head (gate step 1), never the checkout's
`HEAD`, which can lag the pushed head. Get it locally first: `git fetch
origin` and `git fetch origin pull/<N>/head`, then compare `git
rev-parse FETCH_HEAD` with the recorded head. If they differ, the head
moved: return to gate step 1 on the new head (at most once per run, as
gate step 1 bounds it), and nothing recorded for the old one counts,
this classification included. If they are equal, confirm `git cat-file
-e <sha>^{commit}` exits 0. A fetch that fails, or a recorded
head that does not resolve to a commit, means the classifier cannot
prove its input: fail closed, review the PR and dispatch every
specialist. Exit 0 prints
`fast-path: low-risk`: every changed path is under `docs/` and none is
a gate path, and the classification is the review for a PR no
specialist matches (ADR-0088). Exit 1 prints `fast-path: review
(<path>)`: review the PR. Exit 2 prints a `fast-path:` problem string
(git failed, a ref did not resolve): fail closed, review the PR and
dispatch every specialist.

## verdict

    python3 tools/reviewer_verdict.py <score>

Run on the universal reviewer's `score` (ADR-0123), passed as one
quoted argument and only once it reads as a bare finite number from 0
to 10: the score is
the reviewer's text, never a shell fragment. The reviewer is
told no pass line and the threshold lives only in this tool. Exit 0
prints `reviewer-verdict: pass (score N/10)`, exit 1 prints
`reviewer-verdict: flag (score N/10)`, exit 2 prints
`reviewer-verdict: error (<reason>)` (no usable score); a wrong
argument count prints usage and exits 2, so post
`reviewer-verdict: error (hook exit 2)` per gate step 5. Act on the
exit code only; post the printed `reviewer-verdict:` line verbatim as
the first line of the PR's verdict comment. A hook-side
`error` (a missing hook, a hook that did not run, or any exit code
other than 0 or 1 on a usable score: a wrong argument count gives 2, a
killed process 137) is held for a human at once,
with no re-dispatch. A reviewer-side `error` (a timeout, or a `score`
that is not a bare finite number from 0 to 10, which the orchestrator
checks before running the hook) is re-dispatched once, then held.
Under `merge: auto` an `error` never merges. A `verdict` the reviewer
returns itself is ignored.

## changed-files

    python3 tools/fast_path.py gate origin/main <sha>

The source of the `gate_paths` check. `<sha>` is the recorded head
(gate step 1), never the checkout's `HEAD`. Get it locally first: `git
fetch origin` and `git fetch origin pull/<N>/head`, then compare `git
rev-parse FETCH_HEAD` with the recorded head. If they differ, the head
moved: return to gate step 1 on the new head (at most once per run, as
gate step 1 bounds it), and nothing recorded for the old one counts,
this list included. If they are equal, confirm `git cat-file -e
<sha>^{commit}` exits 0. A fetch that fails, or a recorded head that
does not resolve to a commit, means the list cannot be proven current:
fail closed, a human merge. It reads `git diff --name-only -z --no-renames
origin/main...<sha>`, so a rename lists its old path and its new one
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
closed. The number of file ENTRIES (one per file, a rename one entry —
`--jq '.[].filename' | wc -l`, never `--jq length`, which prints one
count per page) must equal the PR's `changed_files`, which counts a
rename once:

    gh api repos/{owner}/{repo}/pulls/<N> --jq .changed_files

A different length (the endpoint stops at 3000 files and flags no
truncation) fails closed. A GitHub MCP file-list tool is
not a source until a run records that it reports `previous_filename`.

## merge-command

    gh pr merge <N> --repo mattbutlerengineering/skills --auto --squash --match-head-commit <sha>

The skill's default, stated because it needs a session permission the
Owner grants outside this repo. `<sha>` is the gated head (the skill's
gate step 1), so an `--auto` merge is enabled only at the head the
review saw. `--auto` does not wait here: `main` has no branch
protection, so no check is required and GitHub merges at once
(`docs/kb/main-unprotected.md`; #1840 and #1841 merged before `check`
finished on their updated heads). So after an `update-branch`, or
whenever the head changed, wait until the `check` run is `completed`
with conclusion `success` on that exact head before running this
command. A merge the runtime or the Owner refuses (a permission
refusal) is reported as awaiting a human merge and never retried by
another route: no REST call, no MCP tool (ADR-0087).

An HTTP 403 (`GitHub GraphQL not available from Claude Code
sessions`) or `spawn gh ENOENT` is a capability gap, not a refusal
(the skill's `references/cloud-sessions.md`). On the 403, and only
once `ci-status` is green at the gated head, merge with the REST twin,
`gh api -X PUT repos/{owner}/{repo}/pulls/<N>/merge -f
merge_method=squash -f sha=<sha>`, which merges a red head as readily
as a green one (`docs/kb/main-unprotected.md`); with no `gh`, with the MCP
`merge_pull_request` (`merge_method: squash`, `expectedHeadSha: <sha>`).
A twin merge still owes both obligations below:

- **The branch delete.** Run the delete steps below with REST reads in
  place of the GraphQL ones: `gh api repos/{owner}/{repo}/pulls/<N>`
  gives `merged` (true is `MERGED`), `.head.ref`, `.head.sha`, and
  `isCrossRepository` as `.head.repo.full_name != .base.repo.full_name`;
  step 3 reads `gh api 'repos/{owner}/{repo}/pulls?base=<headRefName>&state=open'
  --jq length` and needs `0`. With no `gh` (the MCP twin) no delete can
  run: report the branch by name.
- **The post-merge check read.** Before the train starts its next PR,
  wait for the merge to land on `main` and for `main`'s `check` to
  finish, as for any merge (`docs/factory/merge-train-routine.md` §4
  step 5), read through the `preflight` twin. Red `main` stops the
  train.

The command carries no `--delete-branch`: run from a worktree it fails
deleting the local branch that worktree holds (#2319), and it has left
the remote branch behind in this repo (#1636). So delete the remote
branch yourself once `gh pr view <N> --json
state,headRefName,headRefOid,isCrossRepository` reports `MERGED`. If the
PR is not yet `MERGED` (the merge has not landed yet), do nothing
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
The update moves the head, and `--auto` does not wait for checks here
(`docs/kb/main-unprotected.md`), so run the `merge-command` only once
the `check` run on the new head is `completed` with conclusion
`success`.

## reap

The hook is `python3 tools/reap_worktrees.py --apply` (no flag: a dry run that
removes no worktree or branch; `--no-fetch` makes the dry run offline);
that tool implements this section, and the rules below are its
definition. It runs `git fetch origin --prune` first, which prunes
remote-tracking refs, and removes nothing if the fetch fails. For each worktree that
`git worktree list --porcelain` lists under `.claude/worktrees/`,
apply all four tests; any failure leaves the worktree and its branch
alone and reports the path with the failed test. `<branch>` below is
the porcelain `branch` line without its `refs/heads/` prefix, and
`<tip>` is the worktree's `HEAD` commit:

1. **Clean.** No git operation is in flight: `git -C <path> rev-parse
   --absolute-git-dir` exits 0, and that directory holds none of
   `rebase-merge`, `rebase-apply`, `MERGE_HEAD`, `CHERRY_PICK_HEAD`,
   `REVERT_HEAD`, `BISECT_LOG` or `sequencer` (a rebase can leave a
   clean tree detached on `main`'s tip, which passes every other test).
   Then `git -C <path> status --porcelain --untracked-files=all
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
4. **Positive evidence that this tip merged.** The evidence is that
   `<tip>` is preserved: on `refs/remotes/origin/main`, or under a
   merged same-repo PR's pull ref (`refs/pull/<number>/head`); it does
   not claim the tip's content reached main. One of: `<tip>` is a
   `headRefOid` in `gh pr list --head <branch> --base main --state
   merged --json number,headRefOid,isCrossRepository`; `git merge-base
   --is-ancestor <tip> refs/remotes/origin/main` exits 0 (the full ref:
   a bare `origin/main` resolves a local branch or tag of that name
   first, and an unmerged branch so named would pass); or `git
   merge-base --is-ancestor <tip> <headRefOid>` exits 0 for one of
   those merged PRs, because Phase 3's `update-branch` merge commit or a
   retry worker's later commits make the final head a descendant of the
   worker's tip and the squash merge puts neither on main. A retry
   worker works on a differently named local branch (`retry-<pr>`) with
   no PRs of its own, so when those fail the same ancestry check runs
   on each PR that `gh pr list --search <tip> --base main --state
   merged --json number,headRefOid,isCrossRepository` returns (a PR
   already checked is skipped); a detached worktree searches neither
   list. A PR whose `isCrossRepository` is `true` is never evidence, in
   either list. A head not already local (`git cat-file -e
   <oid>^{commit}`) is fetched first with `git fetch --no-tags origin
   pull/<number>/head`; under `--no-fetch` it is not fetched and the
   worktree is kept. A failed fetch, `gh` or `git` call, or a `number`
   that is not a positive integer, a `headRefOid` that is not a full
   object name, or an `isCrossRepository` that is not a boolean, is a
   failure. A merged PR for the branch *name* is not evidence: a branch
   that gained commits after its PR merged, or reused the name, fails
   here. A tip that no merged same-repo PR's head contains and that is
   not on main is unmerged work, never reaped.

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
