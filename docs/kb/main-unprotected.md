---
summary: main has no branch protection or rulesets — ADR-0036's required checks are convention, and the ADR-0070 merge queue is off.
sources: docs/adr/0036-agent-merge-under-independent-review.md, docs/adr/0070-github-merge-queue-composes-with-agent-merge.md
verified: 55d5eae43e2f6c27dea78200aa71f5d3966bf434
related: pr-body-contract, cross-pr-merge-hazards
---

# main is unprotected

Checked 2026-10-10 against the GitHub API, not the repo:

```
gh api repos/mattbutlerengineering/skills/branches/main/protection  -> 404 "Branch not protected"
gh api repos/mattbutlerengineering/skills/rulesets                  -> []
```

- GitHub enforces none of the "required checks" that ADR-0036 names. A
  red PR can be merged, and a direct push to `main` is accepted. Waiting
  for green is something the merger does, not something GitHub forces.
- ADR-0070's merge queue was never switched on. Merge queues may need an
  organization-owned repo, and this one is user-owned and public (not
  verified against GitHub's docs).
- Because the queue is off, PRs merge one at a time with no re-test
  against the new `main`. That is why `cross-pr-merge-hazards` exists.

Re-check with the two commands above before relying on this page. They
are the source of truth, and nothing in the repo records the setting.
