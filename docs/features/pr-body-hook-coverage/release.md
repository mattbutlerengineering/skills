---
stage: ship
run: feature:pr-body-hook-coverage
date: 2026-11-09
outcome: released
released-at: 2026-11-09
---

# Release: pr-body-hook-coverage (same-call heredoc body judged by `pr_body_preflight.py`)

"Production" for this run is `main` of this repo: the hook is a root tool
registered in `.claude/settings.json`, so it reached its users, the Owner's
agent sessions in this repo, when each milestone pull request squash-merged.
The merges happened before this stage (`merge: auto`, each milestone passing
its gate); this record is the write-back.

## Pre-flight

- [x] Verification green (no unresolved failures). `verification.md`: all
  8 PRD criteria PASS, 0 FAIL. Its qualifications stand and are carried, not
  closed: the 24-command margin over the 25% bar moves with the disk, and
  the between-commands rule beyond 8 corpus cases is unverified.
- [x] No secrets in diff; target config present. The diff
  `a4b32bf..origin/main` over `pr_body_preflight.py`,
  `tests/test_pr_body_preflight.py` and `docs/kb/pr-body-contract.md` was
  scanned for key, token and password shapes: the only matches are the word
  "token" in the tokenizer's comments and code. The hook registration in
  `.claude/settings.json` is unchanged and present.
- [x] Migrations/data changes have a tested forward path. None: no data or
  schema; the hook reads a payload and writes nothing.
- [x] No ADR added by this run (`docs/adr/` last touched by an unrelated
  commit), so no numbering or index row is owed. `review.md` checked the
  three-leg test and found none owed.
- [x] Review has no unfixed critical finding: `review.md` found none; one
  major and six minors are deferred by the Owner on 2026-11-09 to #1677,
  #1678 and #1679.
- [x] Rollback plan concrete (commands/steps and trigger below).

## Rollback plan

Trigger: any of these, observed on main: (a) a real `gh pr create` in an
agent session is refused by `pr_body_preflight.py` with a body that detector
B would pass (a false block, the run's named biggest risk); (b) the hook
exits 2 for a command whose body it read from a file a same-call writer
wrote, and a person finds the file the shell wrote differs from what the
hook judged; (c) `python3 -m unittest tests.test_pr_body_preflight` or
`python3 run_tests.py` goes red on main because of the hook.

Door: two-way. The change is one root module, its test file and one kb page;
reverting restores the pre-feature hook, which judged only a body-file that
already existed on disk, with no data to migrate and no published artifact.

Blast radius: this repo's agent sessions only. A wrong call blocks a PR
creation (the agent rewrites the command, or a person disables the hook for
that call) or lets a bad body through to detector B in CI, which still
refuses it. Nothing ships to a consumer repo: `pr_body_preflight.py` is not
part of the plugin payload.

```
# fastest, without a revert: stop the hook for a session
#   remove the PreToolUse entry that runs pr_body_preflight.py from
#   .claude/settings.json (the hook is a no-op when the file is absent)
# full rollback to the pre-feature hook (a4b32bf), newest first:
git revert --no-edit 3931922 f5e3f7b ccface0 2c8b88a
python3 -m unittest tests.test_pr_body_preflight
python3 gates.py && python3 lint.py
```

## Release log

1. Milestone 1, #1660, squash `2c8b88a`, merged 2026-11-09 → the same-call
   `cat > F <<D` writer binds to a later `--body-file F`.
2. Milestone 2, #1663, squash `ccface0`, merged 2026-11-09 → chain rule and
   spelling rule.
3. Milestone 3, #1666, squash `f5e3f7b`, merged 2026-11-09 → a changed file
   is never judged from a stale heredoc.
4. Milestone 4, #1669, squash `3931922`, merged 2026-11-09 → docs, fixtures,
   fail-open gates and the Verify hand-off.
5. `docs/kb/pr-body-contract.md` re-stamped to `3931922` in #1672 → merged.
6. Verify, #1674 → merged; Review, #1676 → merged.
7. Launch brief: `python3 launch_demo.py config` printed `SHIP` and
   `launch-demo: 0 problem(s)`; the launch-demo skill ran for this run, and
   `render` printed `PRODUCED` and `launch-demo: 0 problem(s)`
   (`docs/launches/pr-body-hook-coverage/`: `launch.md`, `storyboard.json`,
   `demo.tape`, `launch.mp4`, 39.8 s, h264 + aac).

## Post-release checks

- The registered hook command, run exactly as `.claude/settings.json`
  registers it (`CLAUDE_PROJECT_DIR` set, through `sh -c`), on a payload
  whose command writes a body lacking both required lines and opens the pull
  request from it in the same call → stderr `B: PR body cites no work-order
  id`, `B: PR body has no Closes #N link`, the pointer line, exit 2. The
  passing twin (both lines present) → no output, exit 0. A malformed payload
  (`{not json`) → exit 0.
- `python3 -m unittest tests.test_pr_body_preflight` on `origin/main` →
  `Ran 166 tests`, `OK`.
- Main's `validator` and `pages` runs after the last merge → `completed
  success`.
- Judged share on the frozen snapshot, from `verification.md`: 229 of 1817
  (12.60%) before, 479 of 1817 (26.36%) after, 0 false blocks over 250
  oracle pairs.
- Fix runs: not a maintenance run.

## Outcome

Shipped cleanly. The one hiccup of record: the Verify snapshot was frozen
twice because the first extraction preferred transcript lines with no cwd;
the first file was discarded before any measurement (`verification.md`).
Carried risks, none blocking: the 24-command margin depends on the disk
(`verification.md`, #1633), the deferred lean cut (#1677) needs a fresh
Verify replay before it lands, and the Architect amendments are open at
#1679.
