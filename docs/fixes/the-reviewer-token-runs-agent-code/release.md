---
stage: ship
run: maintenance:the-reviewer-token-runs-agent-code
date: 2026-10-16
outcome: released
released-at: 2026-10-15
assumptions:
  - "Written after the fact. The release itself happened on 2026-10-15, when the Owner merged PR #923; no release.md was written then, so `next` routed this run to Ship on 2026-10-16. The release log records what the merge did, read back from the forge, and the post-release checks read real validator runs from the day after. Nothing here was re-released."
  - "The release mechanism for this change is the merge to main: validator.yml runs from the default branch's copy on every pull request. Stamped repos receive the payload mirror through the plugin release that carries it, 0.20.0 (#976), and only when they run factory-init update."
  - "ADR-0098 stays provisional. Its acceptance is the Owner's call and not a Ship step."
---

# Release: the reviewer's credential never meets the pull request's code

## Pre-flight

- [x] Verification green (no unresolved failures). verification.md
  records 7 criteria, 7 PASS, 0 FAIL. Its Not verified list holds the
  runner-only proofs; the post-release checks below discharge most of
  them from real runs.
- [x] No secrets in diff; target config present. The diff names the
  secret `FACTORY_REVIEW_TOKEN` only by reference, and that secret
  already exists on the repo: the reviewer account posted from the base
  job after the merge (below).
- [x] Migrations/data changes have a tested forward path. None: the
  change is a workflow, one tool and its tests. No data moves.
- [x] ADR numbering. The run's ADR was numbered 0078 on its branch,
  collided with the knowledge-base ADR on main, and landed as ADR-0098,
  with every reference renumbered (PR #923, "How this landed"). Row
  present in `docs/adr/README.md` at line 121, `provisional`.
- [x] Rollback plan concrete (commands/steps below), dry-run on
  origin/main 0dc827f.

## Rollback plan

Door: two-way. A revert undoes it. The only thing that leaves the repo
is the payload mirror in plugin 0.20.0, and a stamped repo only takes
that when it runs factory-init update, so a later plugin release
carries the rollback the same way.

Blast radius: every pull request's `validator` run in this repo, the
day the call goes wrong. A broken split would show as a red or missing
review comment, or a `needs-review-label` that stops flipping. Every
stamped repo that updates from 0.20.0 onward gets the same behaviour.
Rolling back reopens the defect: the PR's code runs beside the
reviewer's credential again.

A full `git revert 2a5541a` conflicts on `docs/adr/README.md` and would
delete this run's record. The tested rollback reverts the code and
keeps `docs/` as it is. On a scratch worktree of origin/main 0dc827f it
left no conflicts, and the tree passed all three checks:
`tests: 3197 tests across 104 modules in 19.1s on 8 workers,
0 problem(s)`, `lint: 0 problem(s) across 34 skills`,
`gates: 0 problem(s)`.

```
git switch -c revert/reviewer-token-boundary origin/main
git revert --no-commit 2a5541a
git checkout HEAD -- docs/            # keep ADR-0098, its index row and this run
python3 factory_init.py update-manifest
python3 run_tests.py && python3 lint.py && python3 gates.py
git commit -m "revert: the validator trust split (ADR-0098)"
# Then: mark ADR-0098 superseded by a new ADR, open the PR (gate path,
# Owner merge), and ship a chore(release) PR so stamped repos can update.
```

The revert touches `validator.yml` and its payload mirror, `validator.py`
and its mirror, the manifest, and four test modules. One of them,
`tests/test_gates.py`, has changed since #923, and its hunk still
reverted cleanly.

## Release log

1. 2026-10-15 21:38 UTC: the Owner merged PR #923 (squash,
   `2a5541a`, merged by `mattbutlerengineering`). This was a human
   merge on a gate path (`.github/workflows/**`). → The trust split is on
   main. Closes #922.
2. 2026-10-15: no plugin version bump on the branch (ADR-0095), because
   #923 changed no `skills/` file. → The payload mirror went out in plugin
   0.20.0 (#976, `5a58fe4`), and `git merge-base --is-ancestor 2a5541a
   5a58fe4` holds.
3. 2026-10-16: `release.md` written after the fact (see assumptions), on
   branch `docs/ship-reviewer-token`. → This artifact.
4. 2026-10-16: the launch-demo hook. `python3 launch_demo.py config`
   printed the verdict verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   No reason line was printed. `probe` returned `READY`, and `render
   the-reviewer-token-runs-agent-code` returned `PRODUCED`, a 41.6s
   h264 and AAC video. → `docs/launches/the-reviewer-token-runs-agent-code/`
   holds launch.md, storyboard.json, demo.tape and launch.mp4.

## Post-release checks

All runs are `validator.yml` on GitHub Actions after the merge.

- **The trust split runs on real PRs.** 67 `pull_request` runs and 1
  `workflow_dispatch` run since 21:38 UTC on 2026-10-15. All succeeded
  except one, run 38853488318, whose `check` failed on
  the branch's own `make check`. → The jobs `check`,
  `review` and `needs-review-label` appear in every run. The first PR
  after the merge, #927 in run 38813227956, shows all three as success.
- **The base checkout works on `pull_request`.** In run 38853488318
  (PR #954), `check` checked out `refs/remotes/pull/954/merge`. Both
  `review` and `needs-review-label` checked out
  `7e3045c030bcf1c0d73caebc6f36756b0ab6edda`, the base SHA. → The
  PR's code ran only in the job with no secret.
- **The review's Critical holds on a live `--ref <pr-branch>`
  dispatch.** Run 38854152670 was dispatched on `fix/conflict-avoidance`
  for PR #954. `check` checked out `refs/remotes/pull/954/head`
  (`134163f`). `review` and `needs-review-label` both ran
  `git checkout --progress --force -B main refs/remotes/origin/main`.
  → The dispatch ref did not reach the jobs that hold the credential.
  This was review.md's one Critical and the owner's combined
  post-merge live dispatch.
- **Findings reach `review` when `check` fails, under `always()`, and
  the verdict comes from the result.** In run 38853488318, `review`'s
  "Write the handed-over findings" step logged the check's own failure
  line, `make: *** [Makefile:43: check] Error 1`. The reviewer comment
  on PR #954 (id 6208447633) first read `**Detectors and tests: FAIL**`
  at 05:00:24 UTC. The passing dispatch at 05:08:05 UTC edited it to
  `PASS`. → The hand-off round-trips on a real runner, and the verdict
  tracks the check's result in both directions.
- **The reviewer posts as the reviewer, from the base job.** The
  comments on #927 and #954 are by `mattbutlerengineeringreviewer`, not
  the author `mattbutlerengineering`. → The reviewer identity check
  resolves, and the comment lands under the separate actor.
- **`needs-review-label` from the base checkout.** The job succeeded on
  both triggers in the runs above. → The label flip was not read
  separately. The job's success is the evidence.

Still not shown by a live run, carried from verification.md:

- Linux E2BIG on a hand-off over about 128 KiB. No real PR produced
  findings that large.
- The premise that a `GITHUB_TOKEN` push touching
  `.github/workflows/**` is refused. No agent branch has tried it.

Open Owner question, carried and not guessed: what are
`FACTORY_REVIEW_TOKEN`'s scopes? The answer settles the defect's
severity as major or critical. The design holds under the worst case,
a classic `repo` scope.

## Outcome

Shipped cleanly on 2026-10-15 by the Owner's merge of PR #923, and the
release was recorded after the fact on 2026-10-16. Real runs since the
merge show the base checkout on both triggers, the dispatch-ref pin,
and the findings hand-off when the check fails. They also show the
verdict following the result, and the reviewer identity posting from
the base job. Two runner-only proofs and the token-scope question stay
open. Next stage: Operate.
