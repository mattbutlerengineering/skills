---
stage: ship
run: maintenance:a-crashed-run-is-recorded-as-a-no-fire
date: 2026-08-27
assumptions: ["the brief carries no release authorization, so ship
  prepares and stops: the branch is pushed and CI-verified, but no PR is
  opened and nothing is merged"]
---

# Release: a crashed run is an error, not a no-fire

**Prepared, not released.** The brief authorizes no release action, so
this stage stops at a pushed, CI-green branch. No PR was opened: the
review queue stands at 17 and this branch does not add an 18th. Nothing
was merged, closed, retargeted, or labelled.

## Pre-flight

- [x] **Verification green.** `verification.md` records five criteria,
      five PASS, no unresolved failures.
- [x] **No secrets in diff.** The diff touches `trigger_eval.py` and
      three test files. No credential, token, or URL is added; the only
      new string interpolations are integer counts the process computed
      itself. `git diff origin/main...HEAD` reviewed by eye for this.
- [x] **Migrations / forward path.** One data-shape change: results
      records gain an `errors` field. It is additive, and every reader
      of it uses `.get(...)` with a default, so the dated snapshots
      already in `evals/results/` stay loadable unchanged — which the
      repo's append-only rule requires. No snapshot was rewritten; none
      was created, because no real eval was run.
- [x] **Rollback plan concrete.** Below.

## Rollback plan

The branch is unmerged, so rollback today is deleting it:

```
git push origin --delete agent/a-crashed-run-is-recorded-as-a-no-fire
git branch -D agent/a-crashed-run-is-recorded-as-a-no-fire
```

If it has been merged by then, revert both commits — they are
contiguous and touch nothing else:

```
git revert --no-edit 098518d 612942b
python3 -m unittest discover tests && python3 lint.py && python3 gates.py
```

Reverting restores `TestWorkerExceptionBucketsAsNone` and the old
bucketing together, which is the correct pairing: the test and the
behaviour it pinned live or die as one. No manifest regeneration is
needed either way — `trigger_eval.py` is not in `factory_init.MIRRORS`,
which is why this run could touch it without contending with the nine
open PRs that claim `factory/manifest.json`.

## Release log

1. `git commit` — 612942b, the fix and its contract tests → clean.
2. `git commit` — 098518d, the review-driven report fix plus
   `verification.md` and `review.md` → clean.
3. `git push -u origin agent/a-crashed-run-is-recorded-as-a-no-fire` →
   `* [new branch]`, tracking set.
4. **Stop.** No PR opened, per the brief's absent release
   authorization.

## Post-release checks

Not a deployed surface, so the check that matters is the battery on a
machine that is not mine. GitHub Actions run
[#33108235229](https://github.com/mattbutlerengineering/skills/actions/runs/33108235229),
workflow `validator`, conclusion **success**:

```
check: success
review: skipped
merged-label: skipped
needs-review-label: skipped
```

```
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
Ran 1350 tests in 14.371s
OK
```

1350 tests on Linux against 1350 locally — exact parity, so nothing in
this change is platform-dependent. The three skipped jobs are expected:
`review`, `needs-review-label` and `merged-label` fire only on
`pull_request` events, and this was a bare branch push.

## Outcome

Prepared cleanly, released nothing. Two decisions are queued for a human
and both are in `review.md`: whether `main` should exit nonzero when an
eval loses runs (finding 1, deferred with the one-line change written
out), and whether deleting `TestWorkerExceptionBucketsAsNone` is
accepted. ADR-0036 clause 2 independently blocks self-merge here — a
non-authoring reviewer must re-execute verification and record it on the
PR, whenever one is opened.
