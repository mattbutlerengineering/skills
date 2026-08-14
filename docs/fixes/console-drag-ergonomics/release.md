---
stage: ship
run: maintenance:console-drag-ergonomics
date: 2026-08-14
assumptions:
  - "'Production' is main plus the operator's running server (the
    process-dashboard release's precedent): dashboard.html is re-read
    per request, so the merge WAS the deploy — the operator's next
    refresh served the new controls, no restart."
---

# Release: console-drag-ergonomics

## Pre-flight

- [x] Verification green — `verification.md` 5/5 PASS; `review.md`
      ready-to-ship with two minors deferred into the retro seed.
- [x] No secrets in diff — one page, one test file, run docs.
- [x] Migrations/data changes — none; the save contract and backlog
      grammar are untouched.
- [x] Rollback plan concrete — below.

## Rollback plan

Two commits on `main` plus one squash merge, all additive to the page
and tests (`dashboard.html` is deliberately outside
`factory_init.MIRRORS`, so no manifest step):

```
git revert --no-commit fc30389 1730609
python3 -m unittest discover tests && python3 lint.py && python3 gates.py
git commit && git push origin main
gh issue reopen 277
```

The operator's backlog reorder (data, not code) survives a rollback —
`reorder_backlog` shipped in the previous run and stays.

## Release log

1. Capture: `defect.md` + seed claim at 1730609, direct to main
   (stage-artifact precedent), push CI green.
2. Implement item 1: PR #278 squash-merged as fc30389 after
   `check`/`review`/`needs-review-label` all passed (this session's
   standing green-merge authorization); mirror #277 closed by the
   `Closes` link. Push CI on main: success.
3. Implement item 2: the operator's browser reorder landed the same
   day — the fix's acceptance was a human save, so shipping and final
   verification happened in the same act. Verification and this note
   committed direct to main behind it.

## Post-release

The verified state IS the post-release check: the running server (port
7700, never restarted) served the new controls to the operator, who
completed a reorder that `docs/backlog.md` now records — the exact flow
the process-dashboard retro shipped rough. Operator's verdict: "good
enough for now."
