---
stage: ship
run: maintenance:a-reap-the-test-checks-too-soon
date: 2026-10-10
assumptions: ["release authorization is push plus one non-draft PR to main, per autorun-brief.md; the merge is the human's (ADR-0033 gate 3) and is not performed here", "anchor issue #619 created for the PR's Closes line because the defect had no GitHub issue (it is tracked in beads wo-0wu)"]
---

# Release — PR opened, merge left to a human

This repo releases by merging to `main`. The brief authorizes push and PR
only, so this stage stops at an open PR.

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, no unresolved failures |
| Full suite | `Ran 1945 tests in 34.787s` / `OK` |
| lint | `lint: 0 problem(s) across 25 skills` |
| gates + selftest | `gates: 0 problem(s)` / `selftest: ok` (re-run after every artifact) |
| Unfixed critical review findings | None. Three minors deferred with reasons, one design call accepted |
| Secrets in the diff | None. Test code and run docs only |
| Configuration / migrations | None |
| Mirrored files touched | None. `cli.py` was mutated for one verification run and restored (`git diff --stat cli.py` empty); nothing under `factory/templates/**`. No `update-manifest` needed |
| Rollback plan | Below |

## Blocker on merge

**ADR-0036 clause 2 is unmet.** Every commit is agent-authored and the
review was written by the same author. A non-authoring reviewer has to
re-run verification and record it on the PR before merge.

## The change

Branch `fix/reaping-test-flake`, off `origin/main` at `736f54b`:

```
48c4193 docs(capture): a reap the test checks too soon
b7ff056 fix(tests): size the harness_run reap window to the survival it detects
f731700 fix(tests): the sibling reap windows import REAP_GRACE
4d1f790 docs(verify): a reap the test checks too soon
cced19d docs(review): a reap the test checks too soon
```

plus this artifact's own commit.

## Release steps (executed)

1. `gh issue create` made the anchor issue #619. The defect had no
   GitHub issue, and #178 and #181 are permanent state that must never be
   closed.
2. `git push -u origin fix/reaping-test-flake`.
3. `gh pr create --base main --head fix/reaping-test-flake --body-file ...`,
   non-draft. The body carries `Closes #619`, a `No work order:` line, the
   diff as its visual, before/after output, and `## Merge danger`.

Not executed: merge, tag, publish. There is no version bump — the change
is test-only and ships no user-facing surface.

## Post-release

There is nothing to smoke-check until merge. The PR's CI run is the first
execution on Linux (the `/proc` branch of `pid_alive`), and the reviewer
should read it as such.

## Rollback

Door: two-way. A revert restores the 2 s `time.time()` window exactly.
Blast radius: this repo's own test suite. If the call is wrong, the
reaping tests either flake again (window too small) or report a real
regression ~30 s slower (window larger). No stamped repo, consumer or
payload file is affected.

```sh
git revert <merge-commit>          # squash merge: one commit
python3 -m unittest discover tests
```

## Hiccups, recorded

- The first `gates.py` run after writing `defect.md` failed with
  `M: ... missing required section 'Defect (or Condition)'`. The
  precedent run's `## Defect` heading predates detector M's adoption date,
  so copying its format was wrong. The heading was renamed before the
  capture commit.
- CPU load did not reproduce the flake (0/50 at load 74.86), so the
  before/after loop is evidence of no regression, not of the fix. The fix
  is proven by the injected late death.
