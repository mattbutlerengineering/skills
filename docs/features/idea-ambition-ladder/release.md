---
stage: ship
run: feature:idea-ambition-ladder
date: 2026-10-20
outcome: released
released-at: 2026-10-21
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1052
assumptions:
  - "Release authorization is the brief's default, prepare and stop. Ship pushes the branch, opens one PR and stops. It does not merge, tag, bump the version or delete a branch, and ran no `claude plugin eval` or model call."
  - "This branch changes skills/idea and skills/prd, so by ADR-0095 a wave chore(release) PR must bump plugin.json once after the wave lands. Ship neither wrote nor opened it. The wave also covers the earlier merged Decompose skill change (the lessons run, PR 1050), which is not yet released; the held local write-back commit for that run is separate."
  - "Issue 994 seeds the run and the PR closes it. No work order is mirrored, so the PR body carries a No work order line. The issue's cited-run acceptance box is left unchecked in the PR body."
  - "origin/main (c0035bf) equals the merge base and there are no open PRs, so the five checks ran on HEAD 6bf2737 with no merge of main into the branch."
  - "Launch brief not produced. launch_demo.py config prints SHIP, but this stage commits release.md only, so Ship logs the verdict and leaves the brief to the Owner (on demand)."
---

# Release: An ambition ladder for the Idea stage

## Pre-flight

- [x] Verification green. verification.md: 12 of 12 PRD criteria PASS, no failures. Review fixes landed after it, so Ship re-ran the five checks on HEAD `6bf2737`:
      - `python3 run_tests.py` -> `tests: 3679 tests across 113 modules in 25.5s on 8 workers, 0 problem(s)`
      - `python3 lint.py` -> `lint: 0 problem(s) across 34 skills`
      - `python3 kb.py drift` -> `drift: 0 problem(s)`
      - `python3 gates.py` -> `gates: 0 problem(s)`; `python3 gates.py --selftest` -> `selftest: ok`
- [x] Review: no critical finding open, confirmed against review.md (two majors fixed in 87d1f3a, minors fixed, four deferred).
- [x] No secrets in the diff: skill text, a template, a protocol sentence, two test modules, a plugin-evals case with graders, run docs.
- [x] No migrations or data changes.
- [x] No ADR added by this run (highest on origin/main is 0114), so no number or index row to check.
- [x] Pairwise hazard (docs/kb/cross-pr-merge-hazards.md). `git fetch origin` -> origin/main `c0035bf` equals the merge base; `gh pr list --state open` -> no overlapping PR; `git merge-tree --write-tree origin/main HEAD` -> `6a04fd78dd79bb9e2f3938c005a729a7ca80cc21`, clean.
- [x] Protected paths: `git diff --stat origin/main...HEAD -- skills/ .claude-plugin/ factory/` -> `skills/idea/SKILL.md`, `skills/idea/TEMPLATE.md`, `skills/prd/SKILL.md` only (88 insertions, 1 deletion); `.claude-plugin/` and `factory/` untouched.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert restores the previous Idea and PRD skill text; nothing is written at runtime and no migration is involved.

Blast radius: users of the plugin's Idea stage see the new ladder question and brief sections once the plugin version moves; until then nobody does. Old idea.md files still validate.

```
# Before merge: close the PR; nothing reached main
gh pr close 1052

# After merge: revert the squash-merge commit
git checkout -b revert/idea-ambition-ladder origin/main
git revert <merge sha of the PR>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/idea-ambition-ladder
gh pr create --body-file <body>   # needs a No work order: line and a Closes line
```

## Release log

1. Five checks on HEAD `6bf2737` -> all clean (strings above).
2. `git fetch origin`; origin/main equals the merge base; no overlapping open PRs; merge-tree clean.
3. Protected-path diff -> the three skill files above. No version bump here (ADR-0095).
4. `python3 launch_demo.py config` -> verdict and reason line verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   The launch-demo skill was not run (see the assumptions).
5. `git push -u origin feat/idea-ambition-ladder` -> new branch on origin.
6. Body judged first (`gates.pr_body_problems` -> `[]`), then `gh pr create --base main --head feat/idea-ambition-ladder` -> https://github.com/mattbutlerengineering/skills/pull/1052

## Post-release checks

- Nothing is released until the Owner merges. The checks that apply are the pre-merge CI on the PR and the pre-flight above.

## Release steps for the Owner

1. Review the PR and merge it (squash). This is gate 3; Ship did not merge.
2. After the wave lands, open the wave `chore(release)` PR that bumps `.claude-plugin/plugin.json` once (ADR-0095). It also covers the merged Decompose skill change from the lessons run (PR 1050), unreleased so far. The held local write-back commit for that run is separate.
3. Decide whether to authorize the paid run `claude plugin eval . --tag idea` (cap 15 dollars) so a cited record can land under `plugin-evals/records/`; the issue's cited-run box stays unchecked until then. LEDGER unchanged.
4. Do not delete `feat/idea-ambition-ladder` until the PR shows `MERGED`.
5. Write-back: `gh pr view 1052 --json state,mergedAt`. When merged, set `outcome: released`, add `released-at: <merge date>`, keep `pending-merge:`, and commit as `docs(idea-ambition-ladder): ship - <one line>`. If it closed unmerged, leave `outcome: prepared`.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names. Follow-ups for the Owner:

- Not verified: the suite has never run; harness acceptance of the ladder-brief case is unknown; whether the ladder improves briefs is unmeasured; the llm graders are unexercised.
- Review deferrals: the unconditional "Showstopper (recommended)" string pushes tiny features; a Solid pick or declined ladder leaves the four test lines and spike section unspecified, and re-running Idea on the same run appends duplicate seeds; naming the riskiest technical piece sits next to "No solution design here"; phrase pins cannot catch contradictory prose.
- Wave release PR for plugin.json (above).
- Launch brief not produced (`launch_demo.py config` says SHIP).
