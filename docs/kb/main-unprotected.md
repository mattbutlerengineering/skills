---
summary: main has no branch protection or rulesets — ADR-0036's required checks are convention, and the ADR-0070 merge queue is off.
sources: docs/adr/0036-agent-merge-under-independent-review.md, docs/adr/0070-github-merge-queue-composes-with-agent-merge.md
verified: f2ba566331b8ff91d0113fdf97833e91edb43ca8
related: pr-body-contract, cross-pr-merge-hazards
checked-against: the GitHub API (main's branch protection and the repo's rulesets); not GitHub's merge-queue docs, and nothing in this repo records the setting
checked: 2026-11-08
max-age: 30d
---

# main is unprotected

Re-check with these two commands against the GitHub API (the
results shown are what they returned on the `checked:` date):

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
