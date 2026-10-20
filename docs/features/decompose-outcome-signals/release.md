---
stage: ship
run: feature:decompose-outcome-signals
date: 2026-10-18
outcome: released
released-at: 2026-10-20
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1040
assumptions:
  - "Release authorization is Owner decision 4 in autorun-brief.md, prepare and stop. Ship pushes the branch, opens one PR and stops. It does not merge, tag, bump the version or delete a branch."
  - "No plugin.json bump on this branch (ADR-0095 rule 1). `git diff --stat origin/main...HEAD -- skills/ .claude-plugin/ factory/` prints nothing: no skill, no payload and no manifest change. The tool is root-only (ADR-0110), so ADR-0095 rule 2's payload-only release PR does not apply either; no chore(release) PR is needed for this change."
  - "Issue #986 seeds the run and the PR closes it. No new issue was filed. No work order is mirrored (ADR-0032 mirroring is the factory's, not this run's), so the PR body carries a `No work order:` line."
  - "origin/main moved one commit past the branch point (c21828f to c2c1b78, #1037: docs/backlog.md, skills/verify/SKILL.md, tests/test_lint.py). The skill does not call for a merge of main into the branch, and the merge is clean, so the branch was not updated; the chain simulation below ran the checks on the merged trees instead."
  - "Launch brief not produced. `launch_demo.py config` prints SHIP, which per the ship skill means running the launch-demo skill and committing its output. This stage's brief commits only release.md, so Ship logs the verdict and leaves the launch brief to the Owner (on demand: /idea-to-prod:launch-demo on the PR), as pr-body-preflight's Ship did."
---

# Release: Decompose outcome signals from git history

## Pre-flight

- [x] Verification green. verification.md: 9 of 9 PRD criteria PASS
      on 4278f94. The Review re-run's test-only fix (865ed41) and its
      doc commit (ba07e7e) came after it; Ship re-ran the four CI
      checks on HEAD `ba07e7e`:
      - `python3 run_tests.py` → `tests: 3415 tests across 107 modules in 25.9s on 8 workers, 0 problem(s)`
      - `python3 lint.py` → `lint: 0 problem(s) across 34 skills`
      - `python3 kb.py drift` → `drift: 0 problem(s)`
      - `python3 gates.py && python3 gates.py --selftest` → `gates: 0 problem(s)` / `selftest: ok`
- [x] Review: no unfixed critical and no open major (review.md, re-run
      verdict "ready for Ship"). The deferred minors are listed under
      Outcome.
- [x] No secrets in the diff. 24 files: `decompose_signals.py`, its
      tests, a `factory.py` VERBS row, `eval_schema.py` and its tests,
      `tests/test_dual_membership.py`, the two dated records under
      `evals/results/`, `evals/README.md`, CLAUDE.md, CONTEXT.md, ADRs
      and their index, and run docs. A pattern scan of the added lines
      for keys and tokens matched 0. The tool reads local git refs only;
      it needs no configuration in any environment.
- [x] No migrations or data changes. The two records are new,
      append-only files.
- [x] ADR numbers: ADR-0109, ADR-0110 and ADR-0111 are free on
      origin/main `c2c1b78`, whose highest ADR is 0108. Each has its row
      in `docs/adr/README.md`. All three are `provisional`.
- [x] Pairwise hazard (docs/kb/cross-pr-merge-hazards.md). `git fetch
      origin main` moved origin/main to `c2c1b78`. Open PRs: one, #1039
      (`hourly/2026-10-19T01-kb-stamp-outside-payload`, head `3507a12`,
      one line in `docs/kb/stamp-outside-payload.md`).
      - `git merge-tree --write-tree origin/main HEAD` → `9b70e35`, exit 0.
      - Chain: that tree as commit `422b0fc`, then
        `git merge-tree --write-tree 422b0fc <#1039 head>` → `13c7f0b`,
        exit 0, as commit `afb7eed`.
      - Both commits checked out in detached scratch worktrees, the four
        checks run in each → `tests: 3416 tests across 107 modules …, 0
        problem(s)`, `lint: 0 problem(s) across 34 skills`, `drift: 0
        problem(s)`, `gates: 0 problem(s)`, `selftest: ok`, in both.
        The worktrees were removed afterwards.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert removes a new root-only read-only tool, its
`factory.py` verb, its tests and docs. The two records are append-only
evidence files; a revert removes them along with the tool, and nothing
else reads them yet (#987 is not built).

Blast radius: this repo only. Nothing ships in the plugin payload or to
stamped repos. A wrong call shows up as wrong numbers in
`python3 decompose_signals.py` output, which only the Owner and #987
read; the full suite, lint and gates include its tests, so a broken
tool turns `make check` red here and nowhere else.

(The same call the PR body makes under its `## Merge danger` heading.)

```
# Before merge: close the PR; nothing reached main
gh pr close 1040

# After merge: revert the squash-merge commit
git checkout -b revert/decompose-outcome-signals origin/main
git revert <merge sha of #1040>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/decompose-outcome-signals
gh pr create --body-file <body>   # needs a No work order: line and a Closes #N line
```

The ADR index rows and the partial-supersession lines on ADR-0091,
ADR-0106 and ADR-0109 revert with the same commit.

## Release log

1. The four CI checks on HEAD `ba07e7e` → all clean (strings above).
2. `git fetch origin main` → `c21828f..c2c1b78`. `gh pr list --state
   open` → #1039 only. Merge-tree and chain simulation → clean, checks
   green on both links (above).
3. `git diff --stat origin/main...HEAD -- skills/ .claude-plugin/ factory/`
   → empty. No version bump, no release PR needed.
4. `python3 launch_demo.py config` → verdict and reason lines verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   The launch-demo skill was not run (see the assumptions).
5. `python3 decompose_signals.py` on HEAD → `decompose-signals: 36
   run(s), 0 problem(s)`. Its aggregate lines today (not a record; the
   records are the committed files):
   ```
   decompose-signals: aggregate re-plan — observed 2/42 over 4 run(s); inferred 10/208 over 25 run(s); combined 12/250 over 29 run(s); unmeasurable 7 run(s)
   decompose-signals: aggregate design gaps — observed 2/4 over 4 run(s); inferred 0/18 over 18 run(s); combined 2/22 over 22 run(s); unmeasurable 14 run(s)
   decompose-signals: aggregate review-traced — observed 34/194 over 35 run(s); inferred 0/0 over 0 run(s); combined 34/194 over 35 run(s); unmeasurable 1 run(s)
   ```
   review-traced moved from the second record's 33/193 because this
   run's own review.md gained a finding naming an item after that record
   was taken: its row read `1 of 9` in the record and reads `2 of 10`
   now. The records are not edited.
6. `git push -u origin feat/decompose-outcome-signals` → new branch on
   origin, at `0c05aeb`.
7. Body judged first (`gates.pr_body_problems` on the body file → `[]`),
   then `gh pr create --base main --head feat/decompose-outcome-signals
   --body-file …` in a call of its own →
   https://github.com/mattbutlerengineering/skills/pull/1040

## Post-release checks

- Nothing is released until the Owner merges. The checks that apply are
  the pre-merge CI on the PR and the pre-flight above.

## Release steps for the Owner

1. Review the PR, then merge it (squash, as usual). This is gate 3. Ship
   did not merge.
2. Confirm or amend the provisional ADRs: ADR-0109 (an observed boundary
   names its stage and writes its artifact), ADR-0110 (decompose_signals
   joins the root-only importers of cli.py, knowledge_plane.py and
   protocol.py) and ADR-0111 (the inferred implement boundary is the
   commit that checks the last row). The records cite ADR-0109 and
   ADR-0111 in their `rule` field, so they should not be cited as a
   baseline until those two are confirmed.
3. Version: none. No `skills/`, `.claude-plugin/` or `factory/` file
   changed, so ADR-0095 needs neither a bump nor a `chore(release)` PR
   for this change.
4. Do not delete `feat/decompose-outcome-signals` until the PR shows
   `MERGED`. Main is squash-merged, so the branch's boundary commits are
   what this tool measures for this run; keep the branch (or its
   `refs/pull/1040/head`) reachable.
5. Write-back, per the protocol's "The Ship outcome":
   `gh pr view 1040 --json state,mergedAt` (in a cloud session:
   `gh api repos/mattbutlerengineering/skills/pulls/1040 --jq '{merged,merged_at}'`).
   When it merged, set `outcome: released` and add
   `released-at: <merge date>` here, keep `pending-merge:`, and commit as
   `docs(decompose-outcome-signals): ship — <one line>`. If it closed
   unmerged, leave `outcome: prepared`.

## Outcome

Prepared and stopped — waiting on the pull request `pending-merge:`
names. Flags that stand:

- ADR-0109, ADR-0110 and ADR-0111 are provisional.
- Deferred review minors: an empty "Design gaps found" section reads as
  a missing one (reason string only, no number changes); no
  `tests/timings.json` entry for the new module; the first record
  measured this run mid-flight (partly addressed by the second record;
  compare the records run by run, never as one series, per ADR-0111).
- The Implement-stage suite flake did not recur in Verify's five runs
  or in Ship's; its cause is still unknown (verification.md, Not
  verified).
- Launch brief not produced: `launch_demo.py config` says SHIP, but this
  stage's brief commits release.md only.
