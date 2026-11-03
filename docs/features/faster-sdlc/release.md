---
stage: ship
run: feature:faster-sdlc
date: 2026-11-03
outcome: released
released-at: 2026-11-03
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1144
assumptions:
  - "Release authorization is NONE (autorun brief): prepare and stop. Ship pushed the branch and opened one PR. It did not merge, enable auto-merge, tag, bump the version, edit `.claude-plugin/plugin.json` or create an issue."
  - "Owner decision (2026-11-03, relayed by the orchestrator, not an assumption Ship made): the PR body's `Closes #912`. The contract (`docs/kb/pr-body-contract.md`) requires a closing keyword, no open issue fits the run (its tracker rows #902-#912 and #916 are all closed), and the brief allows no new tracker interaction. The Owner chose #912, the run's closed Merge-wait record tracker; the line is a tracker no-op."
  - "No work order ids: the rows were mirrored as #902-#912 and closed earlier, so the PR body carries a `No work order:` line and no four-digit work-order token."
  - "Launch brief not produced here: see Release log step 3."
  - "origin/main is still `36bbab1` (the merge base), so no simulated merge was needed; the five checks ran on the branch HEAD."
---

# Release: faster-sdlc — fast-path rename and instruction-docs gates, with the run's review artifacts

## Pre-flight

- [x] Verification green: no unresolved failure. `verification.md` (second re-verify, HEAD `9de3057`) records two FAIL-on-the-original-bar rows (CI before/after, Merge-wait), both checked on recorded Owner decisions, and five NOT RUN parts; none routes back to Implement. Checks re-ran on HEAD `21ed673`:
      - `python3 run_tests.py` -> `tests: 3971 tests across 126 modules in 99.5s on 8 workers, 0 problem(s)`
      - `python3 lint.py` -> `lint: 0 problem(s) across 35 skills`
      - `python3 kb.py drift` -> `drift: 0 problem(s)`
      - `python3 gates.py` -> `gates: 0 problem(s)`; `python3 gates.py --selftest` -> `selftest: ok`
      - `git status --porcelain` -> empty
- [x] Review: the Critical (rename bypass) is fixed in `9670deb`; the Major (instruction docs) is fixed in `63e7732` (ADR-0121); verdict "Ready for Ship ... No Critical is unfixed, no Major is open". Seven Minors are deferred or resolved with reasons (see Flagged for human review).
- [x] No secrets in the diff: `fast_path.py`, its tests, a queue profile, ADR-0121 and run docs. A grep of the added lines for key, secret, token or password assignments finds nothing.
- [x] No migrations or data changes; no target configuration is required.
- [x] ADR-0121 is free on origin/main (highest there is 0120), has its row in `docs/adr/README.md`, and is `provisional`. ADR-0096's status line now reads "amended by ADR-0121".
- [x] Pairwise hazard (`docs/kb/cross-pr-merge-hazards.md`): `git fetch origin` -> origin/main `36bbab1`, unmoved; `gh pr list --state open` -> no open PR before this one. Nothing to pair against.
- [x] Protected paths: `git diff origin/main...HEAD -- .claude-plugin/plugin.json` -> empty (0 lines). `skills/` is untouched by the branch, so no version bump is owed by this PR.
- [x] PR body judged first: `gates.pr_body_problems(body)` -> `[]`.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert restores the previous classifier, profile `gate_paths` and ADR text; nothing migrates, nothing is published and the plugin version is untouched.

Blast radius: the merge train and the implement queue's fast-path hook, nobody else. After merge, a rename of a gate-path file, or a docs-only change to `docs/factory/**`, `docs/pipeline-protocol.md` or `docs/standards.json`, routes to review instead of the fast path. A wrong call costs extra human review on docs PRs; a dropped list would let such a PR auto-merge unreviewed (the pin test guards the profile's spelling).

(The same call the PR body makes under `## Merge danger`.)

```
# Before merge: close the PR; nothing reached main
gh pr close 1144

# After merge: revert the squash-merge commit
git fetch origin && git checkout -b revert/faster-sdlc origin/main
git revert <merge sha of PR 1144>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/faster-sdlc
gh pr create --base main --body-file <body>   # needs a "No work order:" line and a Closes #N line
# The revert reopens the rename hole and the instruction-docs hole (review's Critical and Major),
# so also set `merge:` in .claude/implement-queue.md away from auto until the fix is re-landed.
```

## Release log

1. Soft gate: `review.md` Verdict -> "Ready for Ship on this review's findings. No Critical is unfixed, no Major is open" -> pass.
2. `git fetch origin` -> origin/main `36bbab196292869bfc887c9e6cfbf344513924e5`; HEAD `21ed67346f410f3df911dab0b6ba1c2b383ccb66`; 11 commits ahead.
3. `python3 launch_demo.py config` -> exit 0, verdict and reason line verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   The launch-demo skill was not run: this unattended pass commits `release.md` only and runs no recorder or voice, and the run has no user-facing surface (brief: `None`). Left for the Owner (on demand: /idea-to-prod:launch-demo on PR 1144).
4. Pre-flight checks on HEAD `21ed673` -> all clean (strings above); `git diff origin/main...HEAD -- .claude-plugin/plugin.json` -> empty.
5. `git push -u origin feat/faster-sdlc-merge-wait` -> new branch on origin, tracking set.
6. `gh pr create --base main --head feat/faster-sdlc-merge-wait --body-file /tmp/faster-sdlc-pr-body.md` -> https://github.com/mattbutlerengineering/skills/pull/1144 (the body carries the `No work order:` line, `Closes #912`, the visual, before/after evidence and `## Merge danger`).

## Post-release checks

- Nothing is released until the Owner merges PR 1144. The checks that apply now are the PR's CI and the pre-flight above.
- After merge, in a fresh session: `python3 fast_path.py origin/main <a branch that renames .github/workflows/validator.yml into docs/>` should print `fast-path: review (.github/workflows/validator.yml)` and exit 1.
- Fix runs: producing boundary `fast_path.changed_paths`/`GATE_*`; consumers inspected: the queue profile's `fast-path` hook, the merge-train and hourly routines (review, second re-review). Related cleanup remaining: the deferred Minors below, and the `autorun-brief.md` exclusion if the Owner ranks it Major.

## Release steps for the Owner

1. Accept or amend provisional ADR-0121 (`docs/adr/0121-the-fast-path-gates-the-docs-agents-obey.md`, and its row in `docs/adr/README.md`).
2. Review PR 1144 and squash-merge it. This is gate 3; Ship did not merge. Re-run `git merge-tree --write-tree origin/main feat/faster-sdlc-merge-wait` first if main has moved, and recheck that ADR-0121 is still free.
3. Do not delete `feat/faster-sdlc-merge-wait` until the PR shows `MERGED`.
4. The wave's `chore(release)` PR that bumps `.claude-plugin/plugin.json`'s `version` is separate (ADR-0095) and not on this branch. This PR changes no `skills/` file, so it does not require one by itself; include it if the wave's other changes do.
5. Write-back: `gh pr view 1144 --json state,mergedAt` (in a cloud session, `gh api repos/mattbutlerengineering/skills/pulls/1144 --jq '{merged,merged_at}'`). When merged, set `outcome: released`, add `released-at: <merge date>`, keep `pending-merge:`, and commit as `docs(faster-sdlc): ship — <one line>`. If it closed unmerged, leave `outcome: prepared`.
6. Out-of-repo Owner steps still NOT RUN (verification): the memory note on the version rule, the session permission, and the `factory-merge-train` trigger.

## Flagged for human review

- Two rows checked on Owner decisions despite missing their bars as written: CI before/after (median 62.0s to 79.5s; `check` job 48.0s to 23.0s) and Merge-wait (p90 7.5h vs under 4h; p90 down from 13.5h). Two more had timing bars moved to #916 (under 8s `test_conductor_merge`, under 25s `make check`), NOT RUN under load 191-207.
- Provisional ADR-0121 awaits acceptance.
- Review Minor, deferred, Owner arbitrates severity: `docs/features/<slug>/autorun-brief.md` is an instruction source not on the gate list (fix: `**/autorun-brief.md` in the profile and `GATE_NAMES`). If ranked Major, it blocks a fix-or-defer.
- Other deferred Minors: the "no automated flow loses the fast path" claim audited for `costs.jsonl` only; exit-2 reason shows git's usage line; `run_tests.py` exits 0 with zero modules; the Notes' test counts are wrong in two places; the real-git tests assume no `commit.gpgsign`.
- Not examined: the GitHub-side `gate_paths` matcher's rename handling, and `fast_path.py`'s agreement with the skill's glob matcher.
- `Closes #912` is the Owner's no-op choice (see assumptions).

## Operate

Per the brief's `operate:` block: minimum signal is the merge-wait read (median, p90 and the >4h open-hours share against the 2026-10-14 baseline) recorded in `breakdown.md`'s Notes, and Ship written back as `released`. `users-observed:` is counted from the signal Operate finds, never from the brief.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names. The offline checks are green on HEAD `21ed673`; the Critical and Major review findings are fixed; the run stays at Ship until PR 1144 is merged and written back.

## Write-back: released 2026-11-03

`gh pr view 1144 --json state,mergedAt,mergeCommit` ->
`{"mergeCommit":{"oid":"b04fb8cae3cf70c3f8ce5b3f82e8418b5d1dfbc4"},"mergedAt":"2026-11-03T16:30:25Z","state":"MERGED"}`.
PR 1144 squash-merged as `b04fb8c` at 2026-11-03T16:30:25Z. The Owner answered the merge in session ("Merge #1144 now", 2026-11-03) and the orchestrator performed it. `pending-merge:` is kept as the record of what was waited on. The sections above describe the state at preparation time.

Outstanding, an Owner step (ADR-0095): the separate `chore(release)` PR that bumps `.claude-plugin/plugin.json`'s `version`. Not done here. PR 1144 changed no `skills/` file, so it needs one only if the wave's other changes do.
