---
stage: ship
run: feature:seed-backlog
date: 2026-07-06
---

# Release: seed backlog

## Pre-flight

- Verification green: `verification.md` 4/4 PRD criteria PASS, no
  unresolved failures.
- Review clean: `review.md` — no critical/major findings; two minors
  deferred with logged reasons.
- Secrets: diff scanned (`git diff origin/main...HEAD` grepped for
  key/token/password/private-key patterns) — nothing found. Docs +
  stdlib-Python change; no configuration needed anywhere.
- Migrations/data: none — the only "data" is the new `docs/backlog.md`,
  additive and advisory.
- Rollback plan: `git revert 605ecb8` on main undoes the entire release
  (single squash commit); `docs/backlog.md` and the ADR-0029 status flip
  revert with it. No external state to unwind.

## Release log

1. Final branch state gated: 146 tests OK, `lint: 0 problem(s) across 15
   skills`.
2. Ship commit: ADR-0029 flipped provisional → accepted (+ index row).
3. `git push -u origin feat/seed-backlog` — pushed clean.
4. PR #102 opened (10 commits, artifacts + implementation + real backlog).
5. Merge explicitly authorized by the maintainer (agent-authored PRs
   require human approval; asked and granted, option "merge + close out").
6. `gh pr merge 102 --squash --delete-branch` → merged as `605ecb8` on
   main; branch deleted.

Hiccup, recorded honestly: `verification.md` was written during Verify but
never committed on the branch — discovered untracked during the
post-release check. Committed to main in the close-out commit alongside
this artifact; content unchanged from the Verify stage.

## Post-release evidence

On merged main (`605ecb8`):

```
Ran 146 tests ... OK
lint: 0 problem(s) across 15 skills
backlog on main: 7 entries, 1 claimed, problems: 0
```

The shipped surface (skills vended from main + the live `docs/backlog.md`)
parses and lints clean through the new public grammar.

## Next

Operate — retro, and the first real use of the new convention: operate
appends this run's seeds to `docs/backlog.md`.
