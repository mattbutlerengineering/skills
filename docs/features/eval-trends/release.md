---
stage: ship
run: feature:eval-trends
date: 2026-10-21
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1056
assumptions:
  - "Release authorization is the brief's default, prepare and stop. Ship pushed the branch and opened one PR. It did not merge, tag, bump the version or delete a branch, and ran no `claude plugin eval`, trigger_eval.py, charter_replay.py or model call."
  - "No plugin.json bump and no chore(release) PR: `git diff --stat origin/main...HEAD -- skills/ .claude-plugin/ factory/` prints nothing, and the tool is root-only (ADR-0115, ADR-0095)."
  - "Issue #1027 seeds the run and the PR closes it. No work order is mirrored, so the PR body carries a `No work order:` line."
  - "origin/main (ff3196d) equals the merge base and there are no open PRs, so the five checks ran on HEAD 6662ee1 with no merge of main into the branch."
  - "Launch brief not produced. `launch_demo.py config` prints SHIP, but this stage commits release.md only, so Ship logs the verdict and leaves the brief to the Owner (on demand: /idea-to-prod:launch-demo on the PR)."
---

# Release: A read-only eval pass-rate trend view

## Pre-flight

- [x] Verification green: 12 of 12 PRD criteria PASS (verification.md). Review fixes landed after it, so the five checks re-ran on HEAD `6662ee1`:
      - `python3 run_tests.py` -> `tests: 3778 tests across 118 modules in 25.8s on 8 workers, 0 problem(s)`
      - `python3 lint.py` -> `lint: 0 problem(s) across 34 skills`
      - `python3 kb.py drift` -> `drift: 0 problem(s)`
      - `python3 gates.py` -> `gates: 0 problem(s)`; `python3 gates.py --selftest` -> `selftest: ok`
- [x] Review: no critical finding open, confirmed against review.md (4 majors and 3 minors fixed; deferrals minor and reasoned).
- [x] No secrets in the diff: a local read-only tool, tests, copied eval records as a frozen fixture, a research note, ADR-0115, run docs.
- [x] No migrations or data changes.
- [x] ADR-0115 is free on origin/main (highest there is 0114), has its row in `docs/adr/README.md`, and is `provisional`.
- [x] Pairwise hazard: `git fetch origin` -> origin/main `ff3196d` equals the merge base; `gh pr list --state open` -> `[]`; `git merge-tree --write-tree origin/main HEAD` -> `9a43c36ebee48db301435a0e2cc262806dfc5fab`, clean.
- [x] Protected paths: `git diff --stat origin/main...HEAD -- skills/ .claude-plugin/ factory/` -> empty.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert removes a new root-only tool, its tests, a fixture, a research note and docs. Nothing is written at runtime.

Blast radius: this repo only. A broken tool turns `make check` red here; no installed plugin or stamped repo carries it.

```
# Before merge: close the PR; nothing reached main
gh pr close 1056

# After merge: revert the squash-merge commit
git checkout -b revert/eval-trends origin/main
git revert <merge sha of the PR>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/eval-trends
gh pr create --body-file <body>   # needs a No work order: line and a Closes #N line
```

## Release log

1. Five checks on HEAD `6662ee1` -> all clean (strings above).
2. `git fetch origin`; origin/main equals the merge base; no open PRs; merge-tree clean.
3. Protected-path diff -> empty. No version bump here.
4. `python3 launch_demo.py config` -> verdict and reason line verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   The launch-demo skill was not run (see the assumptions).
5. `git push -u origin feat/eval-trends` -> branch on origin.
6. Body judged first (`gates.pr_body_problems` -> `[]`), then `gh pr create --base main --head feat/eval-trends` -> https://github.com/mattbutlerengineering/skills/pull/1056

## Post-release checks

- Nothing is released until the Owner merges. The checks that apply are the pre-merge CI on the PR and the pre-flight above.

## Release steps for the Owner

1. Review the PR and merge it (squash). This is gate 3; Ship did not merge.
2. Confirm or amend provisional ADR-0115.
3. Decide whether to raise MIN_CASES / MIN_DAYS (one-line constants).
4. Do not delete `feat/eval-trends` until the PR shows `MERGED`.
5. Write-back: `gh pr view 1056 --json state,mergedAt`. When merged, set `outcome: released`, add `released-at: <merge date>`, keep `pending-merge:`, and commit as `docs(eval-trends): ship - <one line>`. If it closed unmerged, leave `outcome: prepared`.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names. Honest headline: on today's 50 records the tool prints an inventory and REFUSED lines and no trend or cost line, because no surface has two same-suite records on different days with matching case sets. Follow-ups for the Owner:

- Confirm or amend provisional ADR-0115.
- The research note supports MIN_CASES=30 and MIN_DAYS=2 only as a floor: no source gives 30, and one suggests about 1000 questions. Raising it is a one-line constant change.
- The Moonshot rung of this run's idea (an eval-quality dashboard that gates on a trend) is seeded to docs/backlog.md.
- Review deferrals: future-dated records accepted if their name agrees; symlinks followed and file size unbounded; an empty or wrong root prints only `0 record(s)` and REFUSED lines; first-day-against-last-day comparison has no multiple-comparison correction; the day hull is a conservative range, not a 95 percent interval.
- Verify's unverified list: claims attributed to S4 and S6 to S9 only partly refetched; the Wilson primary paper unreachable; no trend line, small refusal or cost line occurs on real records, only on synthetic fixtures; whether the Owner reads the output as proof of improvement is open.
- Launch brief not produced (`launch_demo.py config` says SHIP).
