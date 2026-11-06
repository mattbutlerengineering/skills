---
stage: ship
run: feature:assembly-line
date: 2026-11-06
outcome: released
released-at: 2026-11-06
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1168
assumptions:
  - "The Owner's brief authorizes push, PR and squash-merge once CI is green, and forbids any plugin.json version bump or chore(release) PR (ADR-0095); the diff changes plugin.json's description only, version stays 0.26.0."
  - "The PR needs a Closes line (the waiver does not excuse it) and the breakdown created no mirror issues, so Ship opened issue #1167 as the closing target; flagged for the Owner."
  - "The launch brief ran because docs/launch-demo.json says when: ship; the storyboard's happy path is the shipped `python3 assembly_line.py --out` command, and it shows the page being written, not the animated page itself (a terminal recorder cannot)."
---

# Release: assembly-line — an animated isometric page of every run, with history replay

## Pre-flight

- [x] Verification green (no unresolved failures): `verification.md` has 8 PASS, 0 FAIL, 4 NOT RUN (human judgement, carried by the Owner's decision; not failures). `review.md` reports no CRITICAL; its two fixed findings are in `47dba2d`.
- [x] No secrets in diff; target config present: grep of the added lines for key/secret/token/password hit only the `"tokens": 0` cost-ledger fields. No environment config is involved.
- [x] Migrations/data changes: none. Only new files plus small seams in `board.py`, `protocol.py` (and its factory mirror), `factory.py`, `npx_bundle.py`, `factory/manifest.json` (hash refreshed).
- [x] ADR-0124 free on `origin/main` (`git ls-tree origin/main docs/adr | grep -c 0124` → 0), indexed in `docs/adr/README.md`. No file for WO-0198..WO-0214 or PRD-0021 exists on `origin/main`. `origin/main` had not moved past the branch base (`git log HEAD..origin/main` empty), so no rebase was needed.
- [x] Rollback plan concrete (below).
- [x] Cross-PR hazard: open PRs on 2026-11-06 were #1166 (README only, the Development CI roster line) and this one. `git merge-tree --write-tree HEAD pr1166` printed a tree id with no conflict markers, so the pair merges clean. This branch's README change is one table row in a different section.
- [x] Version: not bumped (ADR-0095). The `chore(release)` PR is the Owner's next step.

Checks re-run on the head to be shipped:

```
python3 run_tests.py   → tests: 4080 tests across 131 modules in 25.3s on 8 workers, 0 problem(s)
python3 lint.py        → lint: 0 problem(s) across 36 skills
python3 kb.py drift    → drift: 0 problem(s)
python3 gates.py       → gates: 0 problem(s)
python3 gates.py --selftest → selftest: ok
```

## Open quality bar (NOT RUN, human criteria)

PRD-0021's four human-judgement criteria were not run, by the Owner's decision to continue through Ship. None is marked passed; they stay open after the merge:

1. **Style match** against the Owner's three reference images.
2. **Cold-viewer test**: 2 of 3 viewers name the steps and the busiest station within 30 seconds.
3. **The Owner would show it** in a real presentation.
4. **The demo runs as written** (the demo script, run start to end).

## Rollback plan

Door: two-way. Everything is additive files plus small seams, and no data or published version moves; a revert of the squash commit undoes it.

Blast radius: the `assembly-line` skill and its page, plus the `board.py`/`protocol.py`/`factory.py`/`npx_bundle.py` seams that skill reads. A wrong call is noticed by the repo's own CI (tests, lint, gates) and by anyone invoking the skill. Stamped repos only see the `protocol.py` mirror change when they next re-stamp. Nobody outside the repo is touched until the Owner cuts the next release.

```
git revert -m1 <squash-commit-sha>   # or: git revert <sha> for a squash commit
git push origin <revert-branch> && gh pr create && gh pr merge --squash
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py
```

## Release log

1. `git fetch origin; git log HEAD..origin/main` → empty; no rebase.
2. Pre-flight checks above → all green.
3. Launch brief: `python3 launch_demo.py config` → verdict `SHIP`, `launch-demo: 0 problem(s)`. Ran the launch-demo skill: `probe` → `READY`; `render assembly-line` → `PRODUCED`, 0 problem(s), launch.mp4 21.3 s (h264 + aac). Wrote `docs/launches/assembly-line/` (launch.md, storyboard.json, demo.tape, launch.mp4), committed on the branch.
4. `gh issue create` → https://github.com/mattbutlerengineering/skills/issues/1167 (the closing target).
5. Push `feat/assembly-line`, open the PR → https://github.com/mattbutlerengineering/skills/pull/1168 (squash-merge authorized once CI is green).

## Post-release checks

- `gh pr view 1168 --json state,mergedAt,mergeCommit` → `MERGED` at 2026-11-06T17:08:06Z as `9804284`. PR CI: `check` pass (both runs), `review` pass. Issue #1167 closes with the merge.
- Still open: the four NOT RUN human criteria above, and the `chore(release)` version bump (ADR-0095), the Owner's next step.

## Outcome

Shipped cleanly. The squash-merge of #1168 (authorized, CI green) reached main; this write-back follows the protocol's Ship outcome rule. No version bump was made (ADR-0095).
