---
stage: ship
run: feature:house-voice
date: 2026-10-25
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1094
assumptions:
  - "Release authorization is NONE (autorun brief): prepare and stop. Ship pushed the branch and opened one PR. It did not merge, tag, bump the version, delete a branch or file an issue, and ran no `claude plugin eval`, trigger_eval.py, charter_replay.py, `claude -p` or other model call."
  - "Issue #1076 seeds the run and the PR closes it. The breakdown rows were never mirrored as work-order issues, so the PR body carries a `No work order:` line and names no work-order token, per Decompose's note (the validator would otherwise demand a close per work order)."
  - "origin/main (446fcc2) has moved past the merge base (d178879). Ship did not merge main into the branch: `git merge-tree --write-tree HEAD origin/main` is clean, and the five checks were re-run on a simulated merge commit (commit-tree of that tree, detached worktree in the scratchpad, removed after). Both runs are quoted."
  - "`skills/` changed (a new skill), so installed plugin caches refresh only when the version moves. Ship did not touch `version` (ADR-0095). The wave's chore(release) PR must bump it after this merges; the Owner steps say so."
  - "Launch brief not produced. `launch_demo.py config` prints SHIP, but this unattended pass commits release.md only and runs no recorder or voice, so Ship logs the verdict and leaves the brief to the Owner (on demand: /idea-to-prod:launch-demo on PR 1094), as the eval-trends release did. A launch brief before criteria 11 and 12 run would also describe an unmeasured claim."
  - "Review has no critical finding (review.md Verdict: 'No critical finding was raised'); the one major is fixed in 3104407. The five deferred minors are carried below, three of them as Owner steps before the first paid run."
---

# Release: A house voice for agent replies, set once instead of corrected every session

## Pre-flight

- [x] Verification green: 10 PASS, 0 FAIL, 3 NOT RUN (criteria 11, 12, 13, all Owner-run) of the PRD's 13 criteria (verification.md). Review commits landed after it, so the checks re-ran on HEAD `15e96a7`:
      - `python3 run_tests.py` -> `tests: 3892 tests across 121 modules in 51.4s on 8 workers, 0 problem(s)`
      - `python3 lint.py` -> `lint: 0 problem(s) across 35 skills`
      - `python3 kb.py drift` -> `drift: 0 problem(s)`
      - `python3 gates.py` -> `gates: 0 problem(s)`; `python3 gates.py --selftest` -> `selftest: ok`
      - `cmp protocol.py factory/templates/tools/factory/protocol.py` -> identical (no output, exit 0)
      - `git status --porcelain` -> empty
- [x] Review: no critical finding open. One major and three minors fixed; five minors deferred with reasons.
- [x] No secrets in the diff: a skill, an output style, a stdlib offline tool, tests, an unrun eval suite with hand-written fixtures, a research note, ADR-0119, registration edits, eight zero-cost ledger rows and run docs. A grep of the added lines for key, secret, token or password assignments finds nothing.
- [x] No migrations or data changes. No target configuration is required: the style is opt-in.
- [x] ADR-0119 is free on origin/main (highest there is 0118), has its row in `docs/adr/README.md`, and is `provisional`.
- [x] Pairwise hazard: `git fetch origin` -> origin/main `446fcc2`; `gh pr list --state open` -> `[]` before this PR; `git merge-tree --write-tree HEAD origin/main` -> `b5017a6588db21a55232c344cddee70c07621c40`, exit 0, no conflict. Simulated merge `8aa823f` (that tree, parents HEAD and origin/main), in a detached worktree:
      - `tests: 3892 tests across 121 modules in 26.8s on 8 workers, 0 problem(s)`
      - `lint: 0 problem(s) across 35 skills`, `drift: 0 problem(s)`, `gates: 0 problem(s)`, `selftest: ok`
- [x] Protected paths: `.claude-plugin/plugin.json` changes the `description` string only (adds `house-voice`); `version` is untouched (ADR-0095). `skills/` gains `skills/house-voice/SKILL.md`, so a release PR is required.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert removes a new skill, an opt-in output style, an offline tool, its tests, an unrun eval suite and docs. Nothing is written at runtime and nothing migrates.

Blast radius: every plugin user, but only after the wave's chore(release) bump refreshes installed caches. The skill fires only when invoked and the style only when a user selects it. A wrong call shows up as a misrouted prompt or a selected style that does not change replies. Before the bump, this repo only.

(The same call the PR body makes under `## Merge danger`.)

```
# Before merge: close the PR; nothing reached main
gh pr close 1094

# After merge, before the release bump: revert the squash-merge commit
git checkout -b revert/house-voice origin/main
git revert <merge sha of PR 1094>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/house-voice
gh pr create --base main --body-file <body>   # needs a "No work order:" line and a Closes #N line

# After the release bump: the same revert, then a new chore(release) PR so
# installed caches drop the skill (ADR-0095). A user who selected the style
# falls back to Default once it is gone; tell them to clear "outputStyle".
```

## Release log

1. Soft gate: review.md Verdict, "No critical finding was raised"; the major is fixed in 3104407 -> pass.
2. `git fetch origin` -> origin/main `446fcc2`, merge base `d178879`. `git merge-tree --write-tree HEAD origin/main` -> `b5017a6588db21a55232c344cddee70c07621c40`, exit 0, clean.
3. Checks on HEAD `15e96a7` -> all clean (strings above). `cmp` of the protocol twin -> identical. Working tree clean.
4. Simulated merge `8aa823f` in a detached scratchpad worktree -> the same checks clean; worktree removed (`git worktree list` shows none).
5. Protected-path diff -> `plugin.json` description only; no version bump here.
6. `python3 launch_demo.py config` -> exit 0, verdict and reason line verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   The launch-demo skill was not run (see the assumptions).
7. PR body judged first: `gates.pr_body_problems(body)` -> `[]`; four-digit work-order tokens in the body -> 0.
8. `git push -u origin feat/house-voice` -> new branch on origin, tracking set.
9. `gh pr create --base main --head feat/house-voice --body-file <scratchpad>/pr-body.md` -> https://github.com/mattbutlerengineering/skills/pull/1094

## Post-release checks

- Nothing is released until the Owner merges and the release PR bumps the version. The checks that apply now are the PR's CI and the pre-flight above.
- Smoke check after the bump, for the Owner: reinstall or update the plugin, run `/output-style`, and confirm the menu lists `idea-to-prod:house-voice`. That is criterion 12's first half, and no live session has shown it yet.

## Release steps for the Owner

1. Accept or amend provisional ADR-0119 (`docs/adr/0119-a-reply-voice-ships-as-a-utility-skill-with-an-opt-in-output-style.md`, and its row in `docs/adr/README.md`).
2. Review PR 1094 and squash-merge it. This is gate 3; Ship did not merge. Re-run `git merge-tree --write-tree origin/main feat/house-voice` first if main has moved again, and recheck the ADR number.
3. Do not delete `feat/house-voice` until the PR shows `MERGED`.
4. Open the wave's chore(release) PR that bumps `.claude-plugin/plugin.json`'s `version` (ADR-0095). It is required: `skills/` changed, and installed caches refresh only when the version moves.
5. Write-back: `gh pr view 1094 --json state,mergedAt` (in a cloud session, `gh api repos/mattbutlerengineering/skills/pulls/1094 --jq '{merged,merged_at}'`). When merged, set `outcome: released`, add `released-at: <merge date>`, keep `pending-merge:`, and commit as `docs(house-voice): ship — <one line>`. If it closed unmerged, leave `outcome: prepared`.
6. Before the first paid run, settle review's deferred minors:
   - The clarity grader's weight: `carries-the-answer.md` scores at weight 1 beside twelve slop graders, so an empty or wrong reply passes 12 of 13. Decide whether to give it a `weight` (for example 12).
   - Quoted prose is not masked by `voice_grade` or the harness regexes, though the rules exempt it. Known divergence.
   - "Keeps Claude Code's coding instructions" holds on the full system prompt only; on the shorter one `keep-coding-instructions` does nothing.
7. Select the style with `/output-style idea-to-prod:house-voice` (or `"outputStyle": "idea-to-prod:house-voice"` in settings) and run the paid live run, per architecture.md's "The Owner's live run (documented, not run)": `claude plugin eval . --tag house-voice --no-publish --max-cost-usd <cap>`, `claude -p --output-format json` per question and arm for the real output-token count, a blind clarity read of each pair, and a hand session past the first turn. That settles criteria 11 and 12. Copy any cited `aggregate-result.json` unedited to `plugin-evals/records/`; it moves no LEDGER maturity.

## Operate

Per the brief's `operate:` block: wait 7 days after this artifact is written back as `released`. Minimum signal: the Owner's verdict on a week of use (criterion 13, keep or drop). `users-observed:` is counted from the signal Operate finds, never from the brief.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names. Honest headline: the offline half is green, but the core claim, that a live reply is shorter, clean and at least as clear, is unknown. Criteria 11 to 13 are NOT RUN, and the style's menu name `idea-to-prod:house-voice` comes from the docs, not a live session. Follow-ups for the Owner:

- Accept or amend provisional ADR-0119.
- The wave's chore(release) version bump (required, `skills/` changed).
- The three before-the-first-paid-run decisions in step 6.
- Review's other deferrals: hard-wrapped phrases are missed; a fence opened with backticks and closed with tildes ends the mask early; a directory argument prints a misleading "no such file" reason; no routing near-miss for ux-writing's "voice and tone guide" (meaningful only with a live `trigger_eval.py` run).
- Launch brief not produced (`launch_demo.py config` says SHIP).
