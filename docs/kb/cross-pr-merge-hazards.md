---
summary: Two PRs can each pass CI and fail together; per-PR CI cannot see it — test the pair with merge-tree before merging in sequence.
sources: .github/workflows/validator.yml, docs/adr/0082-the-pipeline-writes-adrs-at-its-stages.md
verified: 55d5eae43e2f6c27dea78200aa71f5d3966bf434
related: main-unprotected, manifest-regen
---

# Green alone, red together

Every workflow here runs per PR, against that PR's own merge with the
`main` of the moment. Once one PR lands, nothing re-tests the next one
against the new `main` (the merge queue is off, see `main-unprotected`).
On 2026-10-07, 2 of 44 green PRs were pairs that merged cleanly and then
went red. The shapes:

- **A number collision.** Two PRs each take the next ADR, PRD or
  work-order number. For ADRs, ADR-0082 confirms the number
  against the base branch at merge time, and the later ADR renumbers.
- **A check meets the data it governs.** One PR adds a detector, another
  adds files the detector would reject. Each is green against the old
  `main`.
- **Manifest drift.** Two PRs each regenerate `factory/manifest.json`.
  The text merges cleanly, but the hashes go stale.

When the merge order is known, simulate the chain without touching any
branch. For each PR in order, run
`git merge-tree --write-tree <acc> <pr-head>`, wrap the resulting tree
with `git commit-tree`, and run the suite and the gates in a detached
worktree at that commit. Merge for real only after every link is green.
