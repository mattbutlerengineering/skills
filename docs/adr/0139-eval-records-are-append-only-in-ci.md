# Eval records are append-only, enforced in CI

- Status: accepted
- Date: 2026-11-24

Decided by the Owner on issue #2272, taking its recommended option 1.

## Context

CLAUDE.md's Eval honesty section and evals/README.md say
`evals/results/` and `plugin-evals/records/` are append-only: dated
snapshots, never rewritten (ADR-0012, ADR-0019). Nothing enforced it.
The 2026-11-20 offline eval audit rewrote every result in one trigger
record to pass, edited its summary, deleted another record and committed
the lot. `lint`, `gates` and `eval-trends` all reported 0 problems.

Every gates detector checked tree state. A tree-state check cannot tell
an edited record from a new one, so the rule needed a check that reads a
diff. The options were a diff-based detector, a checksum manifest of the
records that only ever gains entries (a manifest edit on every recorded
run), or convention only.

## Decision

**Detector P (EVAL-APPEND-ONLY) reads the PR's diff.** On a
pull_request event, `gates.check_eval_append_only` runs
`git diff -z --name-status -M --diff-filter=MDR <base>...HEAD` over
`evals/results/` and `plugin-evals/records/`, with the base sha taken
from the event payload the way detector B reads the PR body. Each
modified, deleted or renamed record is one problem string:

- `P: <path> is rewritten; an eval record is append-only`
- `P: <path> is deleted; an eval record is append-only`
- `P: <old> is renamed to <new>; an eval record is append-only`

Adding a record is silent. Outside a PR run (no event, or a push event)
P skips, as B does.

**A missing base is a red check, never a pass.** An event with no base
sha reports `P: PR event carries no base sha`, and a base the clone does
not hold reports `P: cannot diff eval records against base <sha>: ...`.
validator.yml's check job fetches full history (`fetch-depth: 0`) so the
base is there. The workflow is mirrored verbatim, so a stamped repo gets
the same fetch.

**P is an offline detector.** It reads the local clone's history and no
network, so it sits in ROSTER with the `env` input and runs in every
`make check`.

## Consequences

- Recording a run adds no bookkeeping: a new dated file is the whole
  change.
- A rewrite is caught at the PR that makes it. A commit pushed straight
  to main has no PR event, so P does not see it; main is unprotected
  (docs/kb/main-unprotected.md) and that gap is the same one B has.
- Correcting a record that is genuinely wrong now means a new dated
  record that supersedes it, never an edit. A PR that has to touch an
  old record (a repo-wide rename, say) fails P and needs the Owner to
  merge it over the red check, knowing why.
- The check job's clone is now full depth, which costs a little checkout
  time on every PR.
