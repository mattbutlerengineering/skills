---
stage: ship
run: feature:lean-in-the-build
date: 2026-10-10
assumptions:
  - "Release authorization read from the brief's Amendment (which wins over its earlier Release section): PR #632 is merged, so push feat/lean-in-the-loop by name and open ONE ready, non-draft pull request to main whose body carries Closes #626 and a No work order: line, then stop. No merge, no tag, no label, no other tracker write. Taken from the brief."
  - "The push and the pull request are made by the orchestrating session, not by this stage's subagent; this artifact records the pre-flight and the exact steps, and the orchestrator's push and PR number belong in the Release log once they happen. Taken from the orchestrator's instruction."
  - "The pull request body cites this run's breakdown rows by bare number (0150 to 0152), as #632 did for its rows, so the lifecycle legs read the body as waived. Taken without user input, mirroring the lean-and-polish release."
  - "The battery ran once on the tip on Python 3.14.6; CI runs it again on the pull request. Taken without user input."
---

# Release: lean in the build (PRD-0012) — prepared; push and pull request by the orchestrator, merge left to the owner

Production for this repository is `main` and the installable plugin cut
from it. This release wires the `lean` utility skill into two stage
skills: Implement climbs lean's ladder before writing each item's
implementation (shortcuts carry a `lean:` marker), and Review gains a
fourth pass, **Complexity**, that applies lean's cut-list to the run's
diff. Plugin version 0.5.0 -> 0.5.1, carried into
`factory/manifest.json`. Seeded by #626.

## Pre-flight

- [x] Verification green — `verification.md`: 5 of 5 PRD-0012 criteria
  pass; the routing eval and charter replay are owed, not run (paid).
- [x] Review: no unfixed critical — `review.md` verdict "Ready to ship";
  one minor fixed, two minors deferred with reasons (one as a
  `docs/backlog.md` seed).
- [x] Base current. `git fetch origin` exited 0; `origin/main` is the
  merge base, so no merge was needed and the battery below is on the
  tree that ships:
  ```
  $ git rev-parse --short origin/main
  6aacc5c
  $ git merge-base HEAD origin/main | cut -c1-7
  6aacc5c
  $ git log --oneline HEAD..origin/main | wc -l
         0
  ```
- [x] Battery on tip `b0160f0`, Python 3.14.6:
  ```
  $ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
  Ran 2066 tests in 37.357s
  OK
  $ python3 lint.py
  lint: 0 problem(s) across 28 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- [x] No secrets in diff:
  ```
  $ git diff origin/main...HEAD | grep "^+" | grep -E -c "sk-ant-|ghp_|github_pat_|AKIA[0-9A-Z]{16}|-----BEGIN|xox[bp]-|sk_live_"
  0
  ```
- [x] No eval definition touched: `git diff origin/main -- evals` is
  empty.
- [x] Migrations/data changes: none. The diff is prose in two skill
  bodies, one template word, a version field in two files, three
  `docs/factory/costs.jsonl` rows, one backlog seed and this run
  directory.
- [x] Concurrent version claim checked. One other pull request is open,
  #635 (`feat/knowledge-base-skill`), and it bumps the same version
  field to 0.6.0. A pairwise merge test against it conflicts on exactly
  the two version lines:
  ```
  $ git merge-tree --write-tree --name-only HEAD origin/feat/knowledge-base-skill
  afa3592589933b3f719022f8917832380d36fb94
  .claude-plugin/plugin.json
  factory/manifest.json

  Auto-merging .claude-plugin/plugin.json
  CONFLICT (content): Merge conflict in .claude-plugin/plugin.json
  Auto-merging factory/manifest.json
  CONFLICT (content): Merge conflict in factory/manifest.json
  ```
  Whichever pull request merges second merges `main` in, keeps the
  higher version (0.6.0 if #635 lands first; a bump past 0.5.1 if this
  lands first), and runs `python3 factory_init.py update-manifest`. This
  is called out under the pull request's Merge danger.

## Release steps

1. Push `feat/lean-in-the-loop` by name (`git push -u origin
   feat/lean-in-the-loop`).
2. Open one ready, non-draft pull request to `main`, title
   `feat(skills): wire lean into Implement and Review (PRD-0012)`, body
   per the protocol's Pull request body section with `Closes #626` and a
   `No work order:` line.
3. Poll `gh pr checks` until done; record the result below.
4. Stop. The merge is the owner's (ADR-0033 gate 3; the pull request
   carries `prd.md` and `architecture.md`, so a human code-owner merge
   under ADR-0036). No tag.

## Rollback plan

Door: one-way-ish. The change reverts cleanly, but the 0.5.1 version
bump is what makes installed plugin caches refresh; a cache that already
pulled 0.5.1 keeps the new Implement and Review wording until a later
version replaces it, so a corrective release needs 0.5.2.

Blast radius: every installed copy of the plugin and every run that
reaches Implement or Review afterwards. If the call is wrong, Implement
agents under-build by over-applying the ladder (the floor bullet is the
guard), or Review files style-level cuts as findings and the fix loop
churns on them; nobody notices until a run's review.md shows it. No
stamped repo's payload changes beyond the manifest's version field, and
no routing description changed.

```
# undo after merge (owner)
git checkout main && git pull
git revert -m 1 <merge-commit-sha>
# bump .claude-plugin/plugin.json to 0.5.2, then
python3 factory_init.py update-manifest
python3 -m unittest discover tests && python3 lint.py && python3 gates.py
# commit, push a branch, open a pull request to main

# undo before merge
gh pr close <pr-number> --comment "withdrawn; see docs/features/lean-in-the-build/release.md"
```

## Release log

1. `git fetch origin` -> exit 0; `origin/main` 6aacc5c is the merge
   base; no merge needed.
2. Battery on `b0160f0` -> green (output under Pre-flight).
3. Pairwise merge test against #635 -> conflicts on the two version
   lines only (output under Pre-flight).
4. Pull request body drafted for the orchestrator.
5. Push and pull request: the orchestrating session pushed
   `feat/lean-in-the-loop` and opened PR #637 (ready, not draft)
   against `main`. Stopped there: no merge, no tag.

## Post-release checks

- `gh pr checks 637` on the first push: check pass (x2),
  needs-review-label pass, review pass; merged-label and the
  push-event duplicates skipping.
- After the owner merges: a plugin reinstall shows version 0.5.1 and
  `skills/implement/SKILL.md` names `../lean/references/ladder.md`.

## Outcome

Prepared. Pre-flight is green on the tree that ships; the push, the
pull request and its checks are the orchestrator's to record, and the
merge is the owner's.
