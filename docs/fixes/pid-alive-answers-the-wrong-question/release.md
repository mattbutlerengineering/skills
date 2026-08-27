---
stage: ship
run: maintenance:pid-alive-answers-the-wrong-question
date: 2026-08-27
---

# Release — prepared, not executed

The brief grants no release authorization, so this stage prepares and
stops. No merge, tag, publish or deploy was performed.

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, no unresolved failures |
| Full suite | `Ran 1346 tests ... OK` |
| lint | `lint: 0 problem(s) across 24 skills` |
| gates + selftest | `gates: 0 problem(s)` / `selftest: ok` |
| Unfixed critical review findings | None — three minor, all with a recorded decision |
| Secrets in the diff | None. Test code only; no credential, token or URL |
| Configuration required in target | None |
| Migrations / data changes | None |
| Mirrored files touched | None. No `factory/templates/**`, no `factory_init.MIRRORS` entry, so no `update-manifest` and no manifest conflict |
| Rollback plan | Below, concrete |

## Blockers on merge

1. **ADR-0036 clause 2 is unmet.** Every commit here is agent-authored
   and the review pass was written by the same author. A non-authoring
   reviewer must re-execute verification and record it on the PR before
   merge. This is the same gate that holds the other 17 open PRs.
2. **The queue is saturated and the standing instruction is to hold.**
   The user's decision was to add nothing to the queue until it drains.
   This run was undertaken because its two files — `tests/test_cli_process_reaping.py`
   and `tests/test_charter_replay.py` — are claimed by none of the 17
   open PRs, so it merges cleanly whenever it is wanted. That makes it
   safe to hold indefinitely, not urgent to land.

## The change

Branch `agent/pid-alive-answers-the-wrong-question`, off `main` at
`622e7c0`.

```
10e684d docs(capture): pid_alive answers the wrong question
33910b4 fix(tests): pid_alive reports a terminated process as dead
```

Four files: the run's own artifacts under
`docs/fixes/pid-alive-answers-the-wrong-question/`, plus the two test
modules.

## Release steps — NOT executed

Whoever lands this runs, in order:

```sh
git push -u origin agent/pid-alive-answers-the-wrong-question
gh pr create --fill --base main            # gh pr edit is broken on this
                                           # repo; use --body-file if the
                                           # body needs changing later
# then: a non-authoring reviewer re-runs the battery and records it,
# satisfying ADR-0036 clause 2
gh pr merge --squash
```

There is no version bump, tag or publish: this repo releases by merging
to `main`, and the change ships no user-facing surface.

## Rollback

```sh
git revert 33910b4 10e684d      # newest first
python3 -m unittest discover tests
```

No manifest regeneration is needed on the way out, for the same reason
none was needed on the way in: no mirrored file is touched. Reverting
restores the original predicate, which means restoring the latent
defect — acceptable, since the suite was green with it for months.

## Hiccups, recorded

- The charter-replay copy was fixed before its regression test existed,
  so the RED could not be observed in the normal order. Rather than
  assert a failure that was never seen, the naive predicate was restored
  in that file alone, the test run to a genuine FAILED, and the fix put
  back. Both states are quoted in `verification.md`.
- A 6x suite-timing discrepancy was noticed mid-run (16 s here versus
  ~103 s in two other worktrees earlier today) and chased rather than
  waved through. The first measurement attempt returned nothing — the
  redirection swallowed `time`'s own output — and the corrected run
  showed the unmodified baseline is also ~16 s. The difference was
  contention from concurrent background jobs, not this change. No
  speedup is claimed.
