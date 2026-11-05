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

## update-branch

    gh pr update-branch <N>

The skill's default, stated because the merge train depends on it: one
PR at a time, `update-branch`, then a green `check` against the main of
that moment before the next PR starts (`docs/kb/cross-pr-merge-hazards.md`).
