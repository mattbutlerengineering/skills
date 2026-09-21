---
stage: ship
run: feature:pipeline-board
date: 2026-08-25
---

# Release: pipeline board — plugin 0.2.0, PR #351

Production for this repo is the installable plugin: work merged to
main, then the version-gated cache re-copy (`claude plugin update`)
delivers it. The operator authorized push + PR; the merge itself is
the human gate (ADR-0033) and stays with the operator.

## Pre-flight

- [x] Verification green (no unresolved failures) — verification.md:
  nine criteria pass, the one first-check failure route-backed and
  re-verified same day
- [x] No secrets in diff; target config present — secret-pattern scan
  over `main...HEAD` returned only the word "token" in design-token
  prose; the skill needs no configuration beyond the plugin itself
- [x] Migrations/data changes have a tested forward path — none: docs,
  stdlib tools, and skill assets only
- [x] Rollback plan concrete (commands/steps below)

## Rollback plan

```
# PR open, unmerged (current state): close it and delete the branch
gh pr close 351 --delete-branch
# reopen the audit anchor if the close comment closed it
gh issue reopen 350

# After merge: revert the squash commit on main, regenerate the
# mirror manifest, and keep the version at 0.2.0-reverted state
git revert <squash-sha>
find factory/templates -name __pycache__ -type d | xargs rm -rf
python3 -B factory_init.py update-manifest && git add -A && git commit
git push
# Installed caches that already picked up 0.2.0 roll back with:
claude plugin uninstall idea-to-prod@skills && claude plugin install idea-to-prod@skills
```

## Release log

1. `git push -u origin feature/pipeline-board` → new branch pushed,
   tracking set (9 commits, 4b1b72a..7ec6830)
2. `gh issue create` (run-summary audit anchor) → issue #350
3. `gh pr create` → PR #351; body cited the six order ids and closed
   #350
4. CI on the opened PR → `check` pass, `review` pass,
   `needs-review-label` FAIL: "none of the work orders this PR cites
   … is mirrored to an issue it closes" — the lifecycle flipper pairs
   cited order tokens with mirrored issues, and this run has no
   tracker mirror by Decompose's decision, so citing the ids can never
   satisfy it
5. Body rewritten to the unmirrored-work pattern (PR #318 precedent):
   order tokens dropped from prose, `No work order:` declaration
   stating the real reason, `Closes #350` kept; patched via
   `gh api repos/…/pulls/351 -X PATCH` (`gh pr edit` is unusable on
   this repo) and re-read to confirm — 0 order tokens, declaration and
   Closes line present
6. The `edited` trigger re-ran the validator → all PR checks
   pass/skip; the opened-run failure superseded in the rollup
7. `gh workflow run validator.yml -f pr=351` (belt-and-suspenders
   re-flip) → the dispatch run itself failed: "V: no pull_request in
   the CI event payload" — the dispatch path's synthesized-payload
   override never reaches the make step. Latent workflow bug,
   pre-existing and harmless here (the flip is a designed no-op for an
   uncited PR); left un-fixed per surgical scope and recorded for the
   retro's seeds
8. `release.md` (this file) committed on the branch and pushed so the
   merged PR carries the complete run

## Post-release checks

- PR #351 check rollup after the body fix → every check pass or
  skipping; no failing check attached
- The shipped surface (installed plugin cache) → cannot be checked
  until the operator merges: the marketplace sources pushed main, and
  the 0.1.0 cache predates board.py (review.md's operational finding).
  Post-merge steps, in order: merge PR #351 (auto-closes #350) →
  `claude plugin update idea-to-prod@skills` (or uninstall/install) →
  invoke `/pipeline-board` in a fresh session and confirm a board
  renders from the 0.2.0 cache. Recorded here as the remaining tail
  rather than silently claimed done.

## Outcome

Shipped to the merge gate with hiccups (release log items 4–7): the
release is staged, CI-green, and awaiting the operator's merge — the
one step the factory's own rules reserve for a human. The propagation
tail (plugin update + smoke invoke) runs after that merge and is
listed above.
