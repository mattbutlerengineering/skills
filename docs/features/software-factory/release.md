---
stage: ship
run: feature:software-factory
date: 2026-08-17
---

# Release: software factory v1 (self-host)

"Production" for this run is `main`: the factory's code shipped
incrementally across the run through 29 reviewed, merged PRs
(#106–#293, WO-0001..WO-0035), and its planes are already live there —
this morning's weekly report (#296) was posted by the shipped
cost-report workflow before this release commit existed. What ships
today is the close-out: the post-Milestone-E verification and review
plus this artifact, landing as one docs-only commit.

## Pre-flight

- [x] Verification green in the shipping sense: the battery is clean
  (`Ran 1234 tests … OK`, `lint: 0 problem(s)`, `gates: 0 problem(s)`,
  `selftest: ok`), and verification.md's three remaining FAILs (no
  live gate traversal / unattended dispatch; the first report's
  historical miss) carry the operator's recorded adjudication — the
  2026-08-15 /goal directed close-out with the supervised traversal
  reseeded in `docs/backlog.md`. Shipping past those FAILs is that
  decision, logged here per the ship contract.
- [x] No secrets in diff: the shipping diff is three docs; grepped for
  key/token/password/private-key — hits are only prose quoting
  workflow *syntax* (`${{ secrets.GITHUB_TOKEN }}` references).
  Target config recorded honestly: `gh secret list` and
  `gh variable list` are both EMPTY — no ANTHROPIC_API_KEY (dispatch
  stays key-gated off, by design and per ADR-0055's posture), no
  FACTORY_PAUSE_TOKEN / FACTORY_REVIEW_TOKEN (the review job falls
  back to GITHUB_TOKEN; the pause step would fail if a cap breach
  ever fired — dormant at $0.00 spend, but a known gap the operate
  stage should carry).
- [x] Migrations/data: none — docs only. The cost ledger is
  append-only data already on main; nothing rewrites it.
- [x] Rollback plan concrete (below). No tag: the repo has no tag
  convention (`git tag` is empty); a release is a merged main state.

## Rollback plan

```
# The release is one docs-only commit on main; undoing it is one revert:
git revert <close-out-sha> && git push origin main
# Factory kill switch, independent of this release (halts all dispatch):
gh variable set FACTORY_PAUSED --body true
```

## Release log

1. Pre-flight battery (2026-08-17) → `Ran 1234 tests … OK`,
   `lint: 0 problem(s) across 23 skills`, `gates: 0 problem(s)`,
   `selftest: ok`.
2. Hiccup, recorded honestly: the FIRST pre-flight run failed — 2 test
   failures, 5 gate problems, all one root cause: detector H rejected
   verification.md's own first draft (criteria 3–7 asserted verdicts
   without fenced evidence). The factory's evidence-honesty gate fired
   on the factory's own verification artifact — criterion 6, live.
   Fixed by fencing real command output into those sections (and
   folding in report #296, which posted mid-ship); battery re-run
   clean. No detector was weakened; the artifact was raised to the
   gate's bar, never the reverse.
3. Release authorization: the operator chose "commit to main + push"
   over a PR (asked and granted, this session).
4. Ship commit: `docs/features/software-factory/{verification,review,release}.md`
   committed to main as the close-out (this artifact rides the
   release commit; the code it closes out was already on main).
5. `git push origin main` → recorded in Post-release checks below.

## Post-release checks

- The shipped planes work where users get them, observed today
  without this commit's help: weekly report #296 posted at
  2026-08-17T08:01Z, recomputed from 18 real ledger rows — the first
  report ever to post with rows (issue #222's fix demonstrated live).
- Push verified: `git log origin/main -1` shows the close-out commit;
  the battery that gates main ran clean on the identical tree
  immediately before the push (log entry 1).
- Run completeness: all 24 breakdown rows checked; verification.md,
  review.md, release.md present; the run's only open thread — the
  supervised end-to-end gate traversal — lives as a named seed in
  `docs/backlog.md`, not as silence.

## Outcome

Shipped with one hiccup, listed above (the gate that caught its own
paperwork — arguably the run's best evidence). v1 of the factory is
live on main: gates that draw blood, planes that post unprompted, a
ledger that survives its runners, and a dispatch path built, fixed
per review, and waiting on the key + label gates it was designed to
wait on. Next stage is Operate — the retro should weigh the three
adjudicated FAILs as graduation gates for v2.
