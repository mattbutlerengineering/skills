---
merge: auto
required_check: check
hold_labels: [needs-review]
gate_paths:
  - "docs/adr/**"
  - "docs/design/**"
  - "**/prd.md"
  - "**/architecture.md"
  - "factory/templates/**"
  - ".github/**"
  - ".claude-plugin/plugin.json"
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
  workflow changes and the stamped payload keep a human merge.

## fast-path

    python3 fast_path.py origin/main HEAD

Run in the PR's checkout after `git fetch origin`. Exit 0 prints
`fast-path: low-risk`: every changed path is under `docs/` and none is
a gate path, and the classification is the review for a PR no
specialist matches (ADR-0088). Exit 1 prints `fast-path: review
(<path>)`: review the PR. Exit 2 prints a `fast-path:` problem string
(git failed, a ref did not resolve): fail closed, review the PR and
dispatch every specialist.

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
