---
stage: ship
run: feature:pr-body-preflight
date: 2026-10-16
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/991
assumptions:
  - "Release authorization is Owner decision 4 in autorun-brief.md, prepare and stop. Ship pushed the branch, filed one type:feature issue (#990), opened one PR (#991) and stopped. It did not merge, tag, bump the version or delete a branch."
  - "No plugin.json bump on this branch. ADR-0095 rule 1 forbids one, and there is no skills/ change. The branch does change the payload (factory/templates/tools/factory/gates.py, a behaviour-identical extraction of pr_body_problems, with factory/manifest.json). ADR-0095 rule 2 says a payload-only wave still gets a chore(release) PR. The orchestrator's brief said no release PR was needed, so whether to cut one is flagged for the Owner and not decided here."
  - "verification.md (6706914) predates the re-review's three fix commits (0715189, b745415, b276426). It was not re-run as a stage. Ship re-ran the four CI checks, a smoke of the registered hook and the merged-PR false-block replay on HEAD 4ab722f instead. The fix commits were reviewed only by the reviewer who wrote them."
  - "The cloud routines' CLAUDE_PROJECT_DIR is assumed, not observed. If it is unset there, the [ ! -f ... ] guard makes the hook a no-op (fail open), not a block."
  - "Launch brief not produced. launch_demo.py config printed the verdict SHIP (docs/launch-demo.json exists), which per the ship skill means running the launch-demo skill and committing its output. The orchestrator's stage brief allows committing only release.md, so Ship followed the brief, logged the verdict, and flagged the launch brief for the Owner. It can be run on demand (/idea-to-prod:launch-demo on #991)."
---

# Release: PR-body preflight hook

## Pre-flight

- [x] Verification green. verification.md has no unresolved failures.
      The re-review re-ran the suite and the replays after its fix
      commits, and Ship re-ran them on HEAD `4ab722f`:
      - `python3 run_tests.py` → `tests: 3289 tests across 106 modules in 23.8s on 8 workers, 0 problem(s)`
      - `python3 lint.py` → `lint: 0 problem(s) across 34 skills`
      - `python3 kb.py drift` → `drift: 0 problem(s)`
      - `python3 gates.py && python3 gates.py --selftest` → `gates: 0 problem(s)` / `selftest: ok`
- [x] Review: no unfixed critical (review.md, re-review verdict). The
      deferred findings are listed under Outcome.
- [x] No secrets in the diff. 20 files: the hook, its tests, the gates
      extraction and its payload copy, the manifest, settings.json, a
      factory.py VERBS row, ADRs, the backlog claim and run docs. The
      target config is the checked-in `.claude/settings.json`, which is
      in the diff.
- [x] No migrations or data changes.
- [x] ADR numbers: ADR-0106 is free on origin/main `7376d94`, where the
      highest ADR is 0105, and no other PR is open. Its index row is in
      `docs/adr/README.md`. It is still `provisional`.
- [x] Pairwise hazard: `git fetch origin main`, then
      `git merge-tree --write-tree origin/main HEAD` → `1c3bd0d36adb816c7ca6cce8541ec3f3e648b69f`,
      exit 0, no conflicts. origin/main has not moved since the branch
      point (the merge base is `7376d94`), so the manifest still matches.
      `gh pr list --state open` was `[]` before #991.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert removes the hook. Short of a revert, deleting
the one `PreToolUse` entry in `.claude/settings.json` (or
`pr_body_preflight.py`, which the guard turns into a pass) disables it.
The `gates.py` change is a behaviour-identical extraction.

Blast radius: every Claude Code session in this repo runs the hook on
every Bash call, including the cloud routines (merge train, hourly
improvement). A wrong call is a false block on a legitimate
`gh pr create`, which stalls an unattended routine. The fail-open rules
cap that risk to a body the hook read and B rejects. Each call also
pays about 34 ms of Python start-up.

(The same call the PR body makes under its `## Merge danger` heading.)

```
# Fastest: disable the hook without touching the extraction
#   edit .claude/settings.json back to {}  (or git rm pr_body_preflight.py;
#   the [ ! -f ... ] guard then exits 0)
git checkout -b fix/disable-pr-body-preflight origin/main
printf '{}\n' > .claude/settings.json
git commit -am "fix: disable the pr-body-preflight hook"   # PR, Closes #<issue>, No work order: line

# Full undo: revert the squash-merge commit
git checkout -b revert/pr-body-preflight origin/main
git revert <merge sha of #991>
python3 factory_init.py update-manifest   # only if the revert conflicts on factory/manifest.json
python3 run_tests.py && python3 lint.py && python3 gates.py
# open the revert PR with a No work order: line and a Closes #N line
```

A session that already loaded the hook and is stuck can still run
commands, because the hook blocks only a judged `gh pr create`. Pass
the body by any unread shape (for example `--web`) or fix the body.

## Release log

1. `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
   `python3 gates.py && python3 gates.py --selftest` on HEAD `4ab722f`
   → all clean (the strings above).
2. Smoke of the registered hook command (read from
   `.claude/settings.json`, run under `/bin/sh` with
   `CLAUDE_PROJECT_DIR` set) on HEAD:
   ```
   passing body: exit 0; stderr: ''
   failing body: exit 2; stderr: 'B: PR body cites no work-order id\nB: PR body has no Closes #N link\npr-body-preflight: the body contract is docs/kb/pr-body-contract.md'
   --web: exit 0; stderr: 'pr-body-preflight: not checked — --web leaves the body to gh'
   non-gh command: exit 0; stderr: ''
   ```
3. Merged-PR false-block replay (the scratchpad `v2/replay.py` harness)
   on HEAD → `merged PRs fetched: 60; B accepts: 60; B rejects
   (skipped): 0` / `hook invocations: 180; refusals (exit 2): 0`. 58 of
   the single-quoted forms passed with the `$ or a backtick` note
   (finding 5).
4. `python3 <plugin>/launch_demo.py config` → verdict and reason lines
   verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   The launch-demo skill was not run. This stage's brief commits only
   release.md, so the launch brief is left for the Owner (see the
   assumptions).
5. `git fetch origin main` and `git merge-tree --write-tree origin/main HEAD`
   → clean (above).
6. `gh issue list` searches for an existing run issue found none, so
   `gh issue create --label type:feature` →
   https://github.com/mattbutlerengineering/skills/issues/990
7. `git push -u origin feat/pr-body-preflight` → new branch on origin.
8. `gh pr create --base main --head feat/pr-body-preflight --body-file …`
   → https://github.com/mattbutlerengineering/skills/pull/991. Hiccup:
   that call ran in the same Bash call as the `cat >` heredoc that wrote
   the body file, so the hook passed it unjudged (finding 4's shape),
   and the first body claimed the hook had judged it. Ship then judged
   the body file through the registered hook as a first command (exit
   0, no note; `gates.pr_body_problems` → `[]`) and corrected the line
   with `gh api -X PATCH repos/mattbutlerengineering/skills/pulls/991 -F body=@…`.
9. CI on #991: `check` passed on the `opened` validator run (17 s)
   and on the `edited` run from the PATCH (23 s). The label and review
   jobs were skipped, as expected for an Owner-gated PR.

## Post-release checks

- Nothing is released until the Owner merges. The checks that apply are
  the pre-merge CI and the smoke above.
- #991 `check` job → pass on both the opened and the edited event.
  Detector B accepted the body on CI.

## Release steps for the Owner

1. Review #991, then merge it (squash, as usual). This is gate 3. Ship
   did not merge.
2. Version: this PR does not touch `.claude-plugin/plugin.json` (ADR-0095
   rule 1). No `skills/` file changed. The payload did change
   (`factory/templates/tools/factory/gates.py` + manifest), and ADR-0095
   rule 2 gives a payload-only wave its own `chore(release)` PR so
   stamped repos receive it. The change is behaviour-identical for a
   stamped repo, so cutting that release PR now, or folding it into
   the next wave's, is the Owner's call.
3. Do not delete `feat/pr-body-preflight` until #991 shows `MERGED`.
4. Write-back, per the protocol's "The Ship outcome":
   `gh pr view 991 --json state,mergedAt` (in a cloud session:
   `gh api repos/mattbutlerengineering/skills/pulls/991 --jq '{merged,merged_at}'`).
   When it merged, set `outcome: released` and add
   `released-at: <merge date>` here, keep `pending-merge:`, and commit as
   `docs(pr-body-preflight): ship — <one line>`. If it closed unmerged,
   leave `outcome: prepared`.
5. After merge, in a fresh session (the hook config loads at session
   start), check that a `gh pr create --body 'x'` is refused with B's
   strings. A cloud routine's first PR after merge shows whether
   `$CLAUDE_PROJECT_DIR` is set there.

## Outcome

Prepared and stopped. The run is waiting on the pull request that
`pending-merge:` names (#991, which closes #990). Flagged for the Owner:

- ADR-0106 is provisional.
- Deferred review findings: 4 (major, real coverage is about 19%, 40 of
  210 historical `pr create` commands judged, and the lever is binding
  a heredoc to the `--body-file` it writes; this PR's own creation hit
  it), 5 (single-quoted `$`/backtick bodies go unchecked), 6
  (`--dry-run` refused), 7 (pathological sizes can pass the 10 s
  timeout), 8 (Python start-up on every Bash call), and re-review
  minor 7 (any remote, `upstream` included, counts as this repository).
- The routines' `$CLAUDE_PROJECT_DIR` is unverified. The guard makes it
  fail open.
- The re-review's code fixes were reviewed only by their author.
- A payload change without a version bump: the `chore(release)` PR
  under ADR-0095 rule 2 is the Owner's call.
- Launch brief not produced: `launch_demo.py config` says SHIP, but this
  stage's brief committed release.md only.
- The re-review's advisory `deepen` hand-off: the command is lexed three
  times. A single quote-aware pass would retire most accepted limits.
