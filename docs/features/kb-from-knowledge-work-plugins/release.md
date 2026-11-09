---
stage: ship
run: feature:kb-from-knowledge-work-plugins
date: 2026-11-08
outcome: released
released-at: 2026-11-09
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1609
assumptions:
  - "Release authorization is none (autorun-brief.md, Release authorization), so this pass prepares and stops: push, one pull request, no merge, tag, version bump, branch deletion or issue close."
  - "origin/main had moved one commit (7623a0a, #1606) since the branch was cut. git merge-tree showed a clean merge, so origin/main was merged into the branch (no rebase, no force-push) and the full battery rerun. That merge brought in the ship skill's rollback-trigger rule, and this artifact follows the merged skill and template (a Trigger line in the rollback plan)."
  - "The pairwise check the brief asked for against #1606 was run as a chain anyway, although #1606 had already merged as 7623a0a: origin/main + #1606's head merges to origin/main's own tree, and chaining this branch on top gives the same tree as the branch's merge commit. The one open pull request, #1608, was chained on top as well, unasked, because it is the remaining cross-PR hazard."
  - "Launch brief happy path: the skill's source 2, the commands verification ran (the kb and kb_harvest test modules and the page's declared fields). The demo never runs harvest against the real memory directory, which the run's standing instructions put off limits; the memory step is shown through its fixture tests."
  - "Rollback trigger chosen by this stage, since nothing in the brief names one: a traceback from kb.py lint or kb.py harvest, harvest output carrying a user-scoped memory entry or memory text outside a description excerpt, or main's battery going red after the merge."
  - "The pull request title is this stage's wording; the brief names none."
---

# Release: Teach the knowledge base what it cannot see yet

## Pre-flight

- [x] Verification green (no unresolved failures): verification.md records
  31 of 33 PRD criteria PASS, 0 FAIL, and 2 NOT RUN for the Owner (PRD 13,
  human-turn precision on real transcripts; PRD 32, demo steps 3 and 4 on
  the real memory directory). Review: ready to ship, no unfixed critical.
  The NOT RUN items are not counted as passed.
- [x] No secrets in diff; target config present: `git diff
  origin/main...HEAD` (mp4 excluded) grepped for key, secret, token,
  password, private-key and token-prefix shapes; every hit is the word
  "token" in prose or in the pairing code. No configuration is needed in
  any target environment; every new page field and `--memory` are
  optional.
- [x] Migrations/data changes have a tested forward path: none. The only
  data change is `docs/kb/main-unprotected.md` gaining three optional
  fields, which `kb.py lint` passes (`kb: 0 problem(s)`).
- [x] ADR numbers: ADR-0125 and ADR-0126 are free on origin/main (highest
  there is 0124) and on every other remote branch, and both have rows in
  `docs/adr/README.md`. Both are provisional. No renumbering.
- [x] Mirrored files: no path under `factory/templates/`, no
  `factory/manifest.json` and no `.claude-plugin/plugin.json` in the
  diff, so no manifest regeneration and no version bump (ADR-0095).
- [x] Rollback plan concrete (commands/steps and trigger below)

## Rollback plan

Trigger: any one of: `kb.py lint` or `kb.py harvest` exits with a
traceback instead of problem strings in any repo; harvest output carries a
user-scoped memory entry, or memory text outside a description excerpt; or
main's battery (`python3 run_tests.py`, `python3 lint.py`, `python3 kb.py
drift`, `python3 gates.py`) goes red after this merge.

Door: two-way — a revert of the merge commit undoes it whole. There is no
migration, nothing is published by this pull request (the plugin version
moves only in a later release PR), and every new page field and the
`--memory` flag are optional.

Blast radius: this repo's own `make check` and docs/kb until the next
release PR; after that, every repo that installs the plugin and runs
`kb.py lint` or `kb.py harvest`. The worst case is harvest listing memory
text it should not; the user-scope, symlink and injected-text exclusions
are pinned by fixture tests.

(the same call the PR body makes under the protocol's Pull request body
section)

```
# Before merge: close the pull request; nothing reached main.
gh pr close 1609

# After merge (squash or merge commit), from an up-to-date main:
git switch main && git pull --ff-only
git switch -c revert/kb-from-knowledge-work-plugins
git revert --no-edit <merge-sha>          # add -m 1 if it is a merge commit
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py
git push -u origin revert/kb-from-knowledge-work-plugins
gh pr create --base main --title "revert: kb-from-knowledge-work-plugins" --body-file <body with a No work order: line>

# If a release PR has already bumped .claude-plugin/plugin.json past this
# merge, the revert ships in the next release PR's bump, so installed
# caches refresh (ADR-0095).
```

## Release log

1. `git status --porcelain` → empty; HEAD 5127bd6 on
   `feat/kb-from-knowledge-work-plugins`.
2. `git fetch origin` → origin/main at 7623a0a ("feat(ship): name the
   rollback trigger before release (#1606)"), one commit past the merge
   base 6f921cb, touching `docs/research/anthropic-engineering-plugin-2026-11-08.md`,
   `skills/ship/SKILL.md` and `skills/ship/TEMPLATE.md`.
3. `gh pr view 1606 --json state,headRefName,headRefOid,mergedAt` →
   `MERGED` at 2026-11-08T23:03:35Z, head cfd3c21 on
   `docs/research-engineering-plugin`. `gh pr list --state open` → one
   open pull request, #1608 (`fix/factory-current-model-ids`).
4. `git merge-tree --write-tree origin/main HEAD` → exit 0, tree
   b8ac9f6 (clean).
5. ADR check: `git ls-tree --name-only origin/main docs/adr/` → highest
   0124; no remote branch other than this one holds a 0125 or 0126 file;
   `docs/adr/README.md` rows 148 and 149 present.
6. `git merge --no-edit origin/main` → merge commit 9874b09, no conflict.
7. Battery after the merge, each on its own exit code:
   - `python3 run_tests.py` → `tests: 4147 tests across 132 modules in
     27.0s on 8 workers, 0 problem(s)`, exit 0
   - `python3 lint.py` → `lint: 0 problem(s) across 36 skills`, exit 0
   - `python3 kb.py drift` → `drift: 0 problem(s)`, exit 0
   - `python3 kb.py lint` → `kb: 0 problem(s)`, exit 0
   - `python3 gates.py` → `gates: 0 problem(s)`, exit 0
   - `python3 gates.py --selftest` → `selftest: ok`, exit 0
8. Pairwise chain (docs/kb/cross-pr-merge-hazards.md): `git fetch origin
   '+refs/pull/1606/head:refs/remotes/pr/1606'
   '+refs/pull/1608/head:refs/remotes/pr/1608'` → pr/1606 cfd3c21, pr/1608
   d7799b8. `git merge-tree --write-tree origin/main pr/1606` → exit 0,
   tree aba9f13, identical to origin/main's tree. Wrapped with `git
   commit-tree`, then `git merge-tree --write-tree <that> HEAD` → exit 0,
   tree b8ac9f6, identical to this branch's merge commit tree; wrapped as
   b8edff8. `git merge-tree --write-tree b8edff8 pr/1608` → exit 0, tree
   3cf7990, wrapped as aff05a1.
9. `git worktree add --detach <scratchpad>/pairwise b8edff8`, battery
   there: `run_tests.py` → `tests: 4147 tests across 132 modules in 27.5s
   on 8 workers, 0 problem(s)` exit 0; `lint.py` → `lint: 0 problem(s)
   across 36 skills` exit 0; `kb.py drift` → `drift: 0 problem(s)` exit 0;
   `kb.py lint` → `kb: 0 problem(s)` exit 0; `gates.py` → `gates: 0
   problem(s)` exit 0; `gates.py --selftest` → `selftest: ok` exit 0.
10. Same worktree at aff05a1 (chain plus #1608): `run_tests.py` → `tests:
    4147 tests across 132 modules in 27.1s on 8 workers, 0 problem(s)`
    exit 0; `lint.py`, `kb.py drift`, `kb.py lint`, `gates.py` each `0
    problem(s)` exit 0; `gates.py --selftest` → `selftest: ok` exit 0.
11. `git worktree remove <scratchpad>/pairwise` → exit 0; `git worktree
    list` shows no pairwise entry.
12. Launch brief: `python3 launch_demo.py config` → exit 0, verdict
    quoted verbatim:
    ```
    SHIP
    launch-demo: 0 problem(s)
    ```
    The tool printed no reason line beyond the verdict. Loaded the
    launch-demo skill. `python3 launch_demo.py probe` → `READY`,
    `launch-demo: 0 problem(s)`, exit 0. Wrote
    `docs/launches/kb-from-knowledge-work-plugins/launch.md` (sources
    prd.md and verification.md) and `storyboard.json` (happy path:
    source 2, verification's commands). `python3 launch_demo.py render
    kb-from-knowledge-work-plugins` → wrote `demo.tape` and
    `launch.mp4`, streams h264 video and aac audio, duration 46.166667,
    verdict `PRODUCED`, `launch-demo: 0 problem(s)`, exit 0. A frame at
    40 s shows the harvest tests typed and `Ran 34 tests ... OK`.
    `video:` set to `launch.mp4`. `python3 gates.py` → `gates: 0
    problem(s)`, then committed as b4b16d4.
13. Secrets scan over `git diff origin/main...HEAD` (mp4 excluded) → no
    secret; hits are the word "token" only.
14. `git push -u origin feat/kb-from-knowledge-work-plugins` → new branch
    on origin; `git ls-remote origin feat/kb-from-knowledge-work-plugins`
    → b4b16d4, matching local HEAD.
15. `gh pr create --base main --head feat/kb-from-knowledge-work-plugins
    --title "feat(knowledge-base): outside-fact age, memory and human-turn
    harvest, and five page practices" --body-file <scratchpad>/pr-body.md`
    → https://github.com/mattbutlerengineering/skills/pull/1609, exit 0.
    The body carries the `No work order:` line and `Closes #1274` as its
    only closing keyword; the PreToolUse body hook did not refuse it.
16. Stopped here: no merge, tag, version bump, branch deletion or issue
    close (release authorization none).

## Post-release checks

Possible before the merge:

- The branch on origin matches the tested commit: `git ls-remote` →
  b4b16d4 = local HEAD after the launch commit.
- The pull request exists against main with the traceability lines:
  #1609, body with `No work order:` and `Closes #1274`.
- The merged result is green locally, including against the one open
  pull request (#1608), per release-log entries 7, 9 and 10.
- CI on #1609: recorded in the stage report; this artifact does not
  claim a CI result it did not see.

Waiting on the merge (for the write-back pass): `gh pr view 1609 --json
state,mergedAt`; main's battery green at the merge commit; `python3 kb.py
lint` on main prints `kb: 0 problem(s)` (main-unprotected.md is not due
until 2026-12-08); issue #1274 closed by the merge; and, once a release PR
bumps the plugin version, the usage text `python3 kb.py` prints in an
installed copy shows `[--memory]`. Operate starts no earlier than five
days after the merge (autorun-brief.md, Operate).

- Fix runs: not a fix run.

## Outcome

Prepared and stopped — waiting on the pull request `pending-merge:` names
(#1609). Hiccups: none in the release mechanism; origin/main had moved
one commit, merged cleanly, and the battery was rerun green.
