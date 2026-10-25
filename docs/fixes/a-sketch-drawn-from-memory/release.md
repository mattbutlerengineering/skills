---
stage: ship
run: maintenance:a-sketch-drawn-from-memory
date: 2026-10-25
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1100
---

# Release: ux-design grounds sketches in code, walks scenarios first, reviews independently

## Pre-flight

- [x] Verification green: 7 PASS, 0 FAIL, 1 NOT RUN (criterion 8, a live
      designer run) in verification.md. Review's fixes (`0ddb8c1`) landed
      after it, so the checks re-ran there:
      - `python3 run_tests.py` -> `tests: 3907 tests across 122 modules in 27.1s on 8 workers, 0 problem(s)`
      - `python3 lint.py` -> `lint: 0 problem(s) across 35 skills`
      - `python3 kb.py drift` -> `drift: 0 problem(s)`
      - `python3 gates.py` -> `gates: 0 problem(s)`; `--selftest` -> `selftest: ok`
      - regression module on HEAD -> `Ran 13 tests ... OK`; against
        origin/main's `skills/ux-design/` -> `FAILED (failures=10, errors=3)`
- [x] Review: no critical finding. Two majors and three minors fixed in
      `0ddb8c1`; two minors deferred with reasons.
- [x] No secrets in diff: skill prose, a template, a read-only stdlib test,
      run docs. No target configuration is required.
- [x] No migrations or data changes.
- [x] No ADR added (review: a prose change fails the protocol's
      hard-to-reverse leg).
- [x] Base: `git fetch origin` -> origin/main `98b220e`, the branch's base.
      `git merge-tree --write-tree HEAD origin/main` -> exit 0, clean.
      `gh pr list --state open` -> 0 before this PR.
- [x] Protected paths: `.claude-plugin/plugin.json` untouched (ADR-0095).
      `skills/` changed, so a release bump is needed before installed
      caches see the fix.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert restores the old skill prose, template and test.
Nothing is written at runtime and nothing migrates.

Blast radius: every plugin user who runs ux-design (`ux: required` runs),
but only after a release bump refreshes installed caches. A wrong call shows
up as a longer stage: more questions, a code read, and a reviewer dispatch.
Before the bump, this repo only.

(The same call the PR body makes under `## Merge danger`.)

```
# Before merge: close the PR; nothing reached main
gh pr close 1100

# After merge: revert the squash-merge commit
git checkout -b revert/a-sketch-drawn-from-memory origin/main
git revert <merge sha of PR 1100>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/a-sketch-drawn-from-memory
gh pr create --base main --body-file <body>   # needs a "No work order:" line and a Closes #N line

# After the release bump: the same revert, then a new chore(release) PR so
# installed caches drop the change (ADR-0095).
```

## Release log

1. Soft gate: review.md Verdict, "No critical finding was raised" -> pass.
2. `python3 launch_demo.py config` -> exit 0, verdict and reason line verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   Not run: the Owner answered "Skip, log the verdict" in session. The change
   is skill prose, with nothing on screen to record.
3. Regression evidence re-captured with the final 13-test module: red
   against origin/main's skill text in a detached scratchpad worktree
   (removed after), green on HEAD.
4. PR body judged first: `gates.pr_body_problems(body)` -> `[]`; four-digit
   typed-id tokens in the body -> 0.
5. `git push -u origin fix/a-sketch-drawn-from-memory` -> new branch on
   origin.
6. `gh pr create --base main --body-file <scratchpad>/fix-body.md` ->
   https://github.com/mattbutlerengineering/skills/pull/1100

## Post-release checks

- Nothing is released until the PR merges and a release PR bumps the
  version. Until then, the checks that apply are the PR's CI and the
  pre-flight above.
- Intake #1093 closes through the PR's `Closes #1093` line when it merges,
  not before ("closed" means fixed in a release).
- First live observation, after the bump: the next `ux: required` run's
  `ux.md` should carry Scenario walkthroughs, Code facts and a Review
  section that names its review kind.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names.
The skill text and template are pinned green. Whether a designer following
them catches #1093's defects is unknown until a live run (verification.md
criterion 8, NOT RUN). Follow-ups:

- A chore(release) bump after the merge (`skills/` changed).
- Review's deferred minors: Architect does not yet read the Dependencies
  section, and the tests pin sentences, not behaviour.
