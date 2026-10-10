---
stage: ship
run: feature:launch-demo
date: 2026-10-10
assumptions:
  - "The brief's Release authorization was read as: push the branch by name, create one plain tracking issue as the pull request's Closes anchor (never #178 or #181), confirm the plugin version is 0.4.0 on the branch, open the pull request non-draft against main, then stop. No merge, no tag, no label, nothing else on GitHub. The merge is ADR-0033 gate 3 and, because the pull request carries prd.md and architecture.md, a human code-owner merge under ADR-0036."
  - "The version bump to 0.4.0 already sat on the branch from the roster commit (Implement); this stage confirmed it rather than making it. No open pull request claims 0.4.0: #618, #620 and #621 each read 0.3.0 in .claude-plugin/plugin.json at their heads."
  - "Review's narration-quoting fix changed how the terminal tape writes screen text after the committed pipeline-board launch.mp4 and demo.tape were recorded, so the orchestrating session required a real re-render at the tip before shipping. It produced; the re-rendered mp4 and tape were committed (60d7cea) so the published brief matches the shipped tool. launch.md was not rewritten by the render (its video: line already read launch.mp4) and is unchanged."
  - "One more frame of the re-rendered mp4 is committed beside this artifact (narration-apostrophe.png, 44 KB, at 9 s): the scene whose narration holds the apostrophe the old encoding re-quoted. Verify's title-card.png is left as it was, a frame of the earlier render."
  - "The branch's own Ship hook (step 4 of skills/ship/SKILL.md on this branch) would fire here, since this repo's docs/launch-demo.json says when: ship. It was not run for this run: the Ship skill driving this stage is the installed 0.3.0 copy, which has no hook, and the orchestrating session scoped the launch-demo work of this stage to the pipeline-board re-render. A launch brief for launch-demo itself is listed as an owner action."
  - "The pull request body and this file cite the run's rows by bare number (0097 to 0113, 0125 to 0127) and carry no work-order id token, so the lifecycle legs read the body as a waived one (ADR-0057, ADR-0064), as #615 did."
  - "The pairwise test ran against all three open pull requests. #621's base is feat/grok-harness, not main; it was tested against this branch directly, as the merge order is not known."
---

# Release: Launch demo (PRD-0009), plugin 0.4.0 — pushed, anchored, pull request open; merge left to the owner

Production for this repository is `main` and the installable plugin cut
from it. This release adds the `launch-demo` utility skill and its tool
`launch_demo.py` (a launch brief — what shipped, what it does, how it
helps — plus a narrated mp4 from a vhs or Playwright recording, muxed by
ffmpeg), a per-repo config `docs/launch-demo.json`, a Ship hook that
fires the skill when that config says `when: ship`, a `timeout`/`stdin`
extension to the mirrored `cli.py` seam, and the plugin version
`0.3.0` → `0.4.0` so installed caches pick up the new skill.

Branch `feat/launch-demo`, cut from `origin/main` `736f54b`, which has
not moved.

## Pre-flight

- [x] Verification green — `verification.md`, re-verified at `6d550c7`:
  10 PASS, 0 FAIL across PRD-0009's ten success criteria; both breakdown
  acceptances outside the PRD pass. One gap was handed to Review (an
  untested fallback), which Review closed in `3d8c821`.
- [x] Review: no unfixed critical — `review.md` verdict "Ready to ship";
  no critical raised; three majors fixed with red-first tests in
  `4c53fa7` (narration could run as shell in the terminal recording),
  `22bc61d` (assemble crashed across filesystems) and `3d8c821` (the
  fallback test); seven minors deferred with reasons, three marked for
  seeding at Operate.
- [x] Real re-render at the tip with the committed config, because the
  narration fix changed the tape after the committed mp4 was recorded:
  ```
  $ python3 launch_demo.py render pipeline-board
  launch-demo: wrote docs/launches/pipeline-board/demo.tape
  launch-demo: wrote docs/launches/pipeline-board/launch.mp4
  ... codec_name=h264 / codec_name=aac / duration=32.233333
  PRODUCED
  launch-demo: 0 problem(s)          (exit=0, 1:21 wall)
  $ ffprobe -v error -show_entries stream=codec_name,codec_type,width,height:format=duration,size -of compact launch.mp4
  stream|codec_name=h264|codec_type=video|width=1280|height=720
  stream|codec_name=aac|codec_type=audio
  format|duration=32.233333|size=429720
  ```
  Frames extracted with ffmpeg at 0.5, 9, 13, 16, 25 and 30 s and looked
  at: the title card reads "The pipeline board" / "Every run, on its
  step, at a glance"; at 9 s the narration reads "...reads every run's
  notes..." with a plain apostrophe (`narration-apostrophe.png`); at
  25 s the jq command and the launch-demo ladder print as JSON rows
  (ship `current`); the outro line is clean. No visible escape sequence,
  octal code or stray quote in any frame. The tape's screen lines now
  use `printf %b` with octal escapes (`run\0047s` where the old tape had
  `run'"'"'s`). 429,720 bytes against the previous 432,885: within the
  ~0.5 MB budget. Committed as `60d7cea`.
- [x] Battery at `60d7cea`, Python 3.14.6:
  ```
  $ python3 -m unittest discover tests      -> exit=0; Ran 2039 tests in 24.468s; OK
  $ python3 lint.py                         -> lint: 0 problem(s) across 26 skills
  $ python3 gates.py && python3 gates.py --selftest
                                            -> gates: 0 problem(s) / selftest: ok
  ```
- [x] Base current: `git fetch origin`; `origin/main` = `736f54b` =
  `git merge-base HEAD origin/main`; `git log HEAD..origin/main` empty,
  so the merge is a fast-forward of `main`'s tree.
- [x] Pairwise against open pull requests (`git merge-tree --write-tree`
  against each head; clean ones then built as a merge commit in a
  detached scratch worktree and the battery run there):
  - #620 `fix/reaping-test-flake` → clean; merged tree: Ran 2040 tests
    OK, lint 0, gates 0, selftest ok.
  - #618 `feat/grok-harness` → clean; merged tree: Ran 2053 tests OK,
    lint 0 across 26 skills, gates 0, selftest ok.
  - #621 `docs/docs-audit` (base `feat/grok-harness`) → **conflict in
    `docs/factory/costs.jsonl` only**: both branches append rows at the
    end of the append-only ledger (#621 adds 11, this branch 20).
    Resolution for whichever merges second: keep both sides' rows, no
    row edited. `README.md` auto-merges.
  - Plugin version on each head: 0.3.0 (#618, #620, #621). None claims
    0.4.0.
- [x] No secrets in diff — `git diff origin/main...HEAD` (39 files,
  +5350/−38) added lines grepped for `sk-ant-`, `ghp_`, `github_pat_`,
  `AKIA` + 16, `-----BEGIN`, Slack and Stripe live-key shapes: 0. The
  feature needs no secret: narration defaults to the local `say`, and a
  hosted voice is the consuming repo's own config with its own key.
  Target config: this repo's `docs/launch-demo.json` is committed.
- [x] Migrations/data changes — none (`migrat|\.sql$|alembic` over the
  changed names: 0). The mirrored `cli.py` change is additive (two
  keyword arguments defaulting to `None`; every earlier caller is
  unchanged) and the manifest was regenerated in the run
  (`factory/manifest.json` in the diff; detector E is green).
- [x] Rollback plan concrete (below).

## Rollback plan

Door: one-way for the published version, two-way for the code. A
`git revert` of the squash removes the skill, the tool, the Ship hook,
the config and the `cli.py` extension in one step, but `0.4.0` is a
published plugin version once merged: installed copies that updated
have it in their cache, and a revert only reaches them through a
further bump (0.4.1). The mp4 (430 KB) and the five PNGs stay in
`main`'s history after a revert. Squash only: the branch history also
holds the earlier 432,885-byte render, which a merge commit or rebase
would carry into `main`.

Blast radius: every installed copy of the plugin on its next update
(a new utility skill, and a Ship stage with one more step that does
nothing unless a repo has `docs/launch-demo.json`); this repository's
own Ship stage, which will fire the hook because the committed config
says `when: ship` (the hook never blocks a release; a missing tool is
one log line); stamped repos only on their next factory update, through
the additive `cli.py` seam change. If the call is wrong the first to
notice is the owner's next Ship run here.

(the same call the pull request body makes under the protocol's Pull
request body section)

```
# Pull request open, unmerged: nothing is published.
gh pr close 623 --delete-branch
gh issue close 622 --comment "PR closed without merge; run parked at docs/features/launch-demo/"

# After the squash merge: revert on a branch, bump past the published
# version so installed caches re-copy, re-check, merge at gate 3.
git fetch origin main && git switch -c revert/launch-demo origin/main
git revert --no-edit <squash-sha>
# set .claude-plugin/plugin.json "version" to "0.4.1" (the revert alone
# would restore 0.3.0, which caches already past 0.4.0 never re-copy)
python3 factory_init.py update-manifest      # the revert touches mirrored cli.py and protocol.py
make check
git push -u origin revert/launch-demo
gh pr create --base main --title "revert: back out launch-demo" --body-file <body>   # fresh plain anchor; No work order: a revert
gh issue reopen 622
```

## Release log

Steps run on 2026-10-10 under the brief's Release authorization; step 5
is the operator's.

1. Re-render, battery, pairwise, secret scan — above; re-render committed
   as `60d7cea`; this file and the frame committed before any outward
   action.
2. `git push -u origin feat/launch-demo` → `* [new branch] feat/launch-demo -> feat/launch-demo`;
   `git ls-remote --heads origin feat/launch-demo` → `be13efd`.
3. `gh issue create --title "Ship launch-demo (PRD-0009): a narrated launch brief for any shipped feature" --body "Audit anchor for the run's PR, closed by that PR's merge (detector B's Closes link; the run's rows have no tracker mirror, ADR-0026). Run: docs/features/launch-demo/."`
   → https://github.com/mattbutlerengineering/skills/issues/622 , no label.
   Not #178, not #181.
4. Body written to the session scratchpad (`Closes #622` first; the
   `No work order:` line; `## What changed` with the render pipeline as
   pseudocode and a file tree; `## Before and after` with the re-render
   output, the mp4/copy/frame blob links, and the real bash run of the
   old and new screen-line encodings; pairwise results; `## Merge
   danger`; the attribution line last), checked for work-order id
   tokens (0), then
   `gh pr create --base main --head feat/launch-demo --title "feat(launch-demo): a narrated launch brief for any shipped feature (PRD-0009)" --body-file pr-body.md`
   → https://github.com/mattbutlerengineering/skills/pull/623 ;
   `gh pr view 623` → `OPEN draft=false base=main head=be13efd`; body
   as landed holds 0 work-order id tokens. `gh pr checks 623` on the
   pull-request event (run `38077618954`, `pull_request success
   be13efd`):
   ```
   check               pass      34s
   review              pass      27s
   needs-review-label  pass       6s
   merged-label        skipping   0s   (fires on merge)
   ```
   The check job's log: `lint: 0 problem(s) across 26 skills`,
   `gates: 0 problem(s)`, `selftest: ok`, `Ran 2039 tests`, and no `B:`
   line. The push event's own run (`38077579366`): `check` pass.
5. **Operator — the merge, ADR-0033 gate 3.** Watch
   `docs/launches/pipeline-board/launch.mp4` on the branch, then
   squash-merge and delete the branch. Squash only.

## Post-release checks

For the operator, after the squash merge; none has run yet.

- `claude plugin update idea-to-prod@skills` → the cache at
  `~/.claude/plugins/cache/skills/idea-to-prod/0.4.0/` exists and holds
  `skills/launch-demo/SKILL.md` and `launch_demo.py`.
- On `main`: `python3 lint.py` → `lint: 0 problem(s) across 26 skills`;
  `python3 gates.py && python3 gates.py --selftest` → `gates: 0
  problem(s)`, `selftest: ok`.
- The anchor issue closes on the merge.
- The next Ship run in this repo shows one Release-log entry from the
  launch-demo hook with its verdict.
- Whichever of this pull request and #621 merges second resolves the
  `docs/factory/costs.jsonl` append conflict by keeping both sides.

## Outcome

Shipped to the gate, cleanly: the re-render at the tip produced
(h264+aac 1280x720, 32.23 s, 429,720 bytes; frames read correctly) and
was committed; the battery is green; #618 and #620 merge clean and stay
green merged; #621 conflicts only on the ledger append. The branch is
pushed, the anchor is #622, the pull request is #623 — non-draft, base
`main`, CI green at `be13efd`. The commit adding these lines re-runs the
pull-request event; this file cannot quote its own commit's result. The
merge is the owner's at ADR-0033 gate 3, squash only. Next stage after
the merge and the post-release checks: Operate (`retro.md`), where the
drift-band, render-slug and config-grammar minors should be seeded, and
the owner may run `launch-demo` for this run itself.
