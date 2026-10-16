# Autorun brief: the-reviewer-token-runs-agent-code

Collected 2026-10-10 from the owner, one question at a time. This brief
is not an artifact.

## Defect

`.github/workflows/validator.yml`'s `review` job checks out the pull
request's head (`refs/pull/<N>/head`, the dispatched agent's branch) and
its "Post findings" step runs `make review` with
`GH_TOKEN: ${{ secrets.FACTORY_REVIEW_TOKEN || secrets.GITHUB_TOKEN }}`
beside a `pull-requests: write` job grant. `make review` is the PR's own
`Makefile` invoking the PR's own `validator.py`, so an agent PR that
edits either runs arbitrary code holding the reviewer PAT: it can post
any comment or an approving review as the reviewer account (role read
live 2026-10-02: `write`), or print the PAT into posted findings. The job
fires automatically from the assembler's hand-off and on `pull_request`
for every same-repo branch, with no owner step before the token reaches
PR-controlled code.

Source: first-live-dispatch review, finding 4 (2026-10-02), re-scoped as
R3 in the 2026-10-10 re-review (`docs/features/first-live-dispatch/
review.md` on branch `fix/fld-allowlist-boundary`, PR #629). #629's ADR (number 0077)
(on that branch) closed the same class for the assembler and names this
path as not closed.

- **Observed:** the code path predates the factory's first live
  dispatch (WO-0030); the first real post on it was the review comment
  on #579. No exploitation observed — this is a reproduced-by-reading
  structural defect; Implement must reproduce it mechanically
  (a test/replay showing PR-controlled code reaching the token), not
  assert it.
- **Expected:** no step that executes code from the PR's head holds the
  reviewer PAT or any write-scoped token. PR code may run only in a job
  whose token is read-only; the job that posts as the reviewer reads that
  job's output as data and runs only base-ref (trusted) code.
- **Severity / PAT scopes:** the owner has NOT stated the reviewer PAT's
  scopes. Do not guess them. Major if the PAT is limited to review/comment;
  critical if it is classic `repo` or fine-grained `contents: write`. The
  fix must be safe under the worst case, so scopes do not change the
  design. Record scopes as an open question for the owner.

## Owner decision already taken (2026-10-10)

Fix shape: split validator.yml's `review` job #629's ADR (number 0077)-style — a
read-only job runs the PR's code (`make check`-style findings) and hands
over a result artifact; a separate job holding the PAT checks out the
BASE ref, consumes only that result as data, and runs no PR code. The
review's other candidate ("drop the reviewer account to `triage`") is
not chosen. Whether this needs its own ADR or amends #629's ADR (number 0077) is the
architect's call under CLAUDE.md's ADR bar — note #629's ADR (number 0077) is not yet on
main (PR #629 open), so do not edit it; cite it by number only if the
architect concludes a new ADR is needed.

## Scale

Maintenance (fix) run, slug `the-reviewer-token-runs-agent-code`,
artifacts under `docs/fixes/the-reviewer-token-runs-agent-code/`. Branch
`fix/reviewer-token-boundary` off `origin/main` (ca57e5c), worktree
`.claude/worktrees/reviewer-token`. Independent of PR #629: it changes
`validator.yml` (and its mirror under `factory/templates/`) and related
validator/Makefile/tests, not `assembler.yml`; the interface #629's
deliver job uses (dispatching the validator with a PR number) must stay
unchanged.

## Scope

IN: `validator.yml` + its identity mirror, the Makefile targets / tools
the review path uses, tests pinning the new boundary (mirroring
`TestAgentCredentialBoundary`'s approach on #629's branch, which you may
read via `git show fix/fld-allowlist-boundary:tests/test_assembler.py`),
`tests/test_workflow_permissions.py` recorded grants, manifest regen.

OUT: `assembler.yml`; the reviewer account's role or PAT itself (owner
actions, not code); `pull_request_target` adoption unless the architect
shows it's required and safe; Majors 2 and 3 of the first-live-dispatch
review; the fork guard's other paths beyond what the split needs.

## Tracker

No tracker seeding. Ship creates one plain anchor issue (see release).

## User-facing surface

None (CI workflow). `ux: not-applicable` where the stage asks.

## Release authorization

Push `fix/reviewer-token-boundary` by name, create ONE plain anchor issue
(never #178/#181; follow #628/#606 precedent), open ONE non-draft PR to
`main` with body per the protocol's "Pull request body" section
(`Closes #N`, a `No work order:` line, no bare work-order ids in unquoted
prose, smallest visual, before/after evidence, `## Merge danger`), then
STOP: no merge, no label, no workflow dispatch. The new workflow can only
be proven on a runner; its live proof folds into the owner's combined
post-merge live dispatch (recorded in #629's release.md). Say so in the
PR and release.md.

## Standing instructions for every stage

Answer interview questions from this brief. Where it is silent and the
stage skill offers a recommended default, take it and log it under the
artifact's `assumptions:` frontmatter; where there is no default —
including every evidentiary question — stop and surface. Never fabricate
verification evidence: run the real commands (`python3 -m unittest
discover tests`, `python3 lint.py`, `python3 gates.py && python3 gates.py
--selftest`, `actionlint` if installed). Work only inside
`.claude/worktrees/reviewer-token`. After editing any file in
`factory_init.MIRRORS` or under `factory/templates/**`, run
`python3 factory_init.py update-manifest` and commit the manifest. Commit
each stage's artifact on the branch (Conventional Commits, ending with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`). Work-order
ids continue from the highest across all local branches (row 0132 is
used on `fix/fld-allowlist-boundary`). Shell is zsh — never name a
variable `status`.
