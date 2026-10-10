---
stage: review
run: maintenance:a-reap-the-test-checks-too-soon
date: 2026-10-10
assumptions: ["minor findings deferred with a logged reason, per the review skill's default that minors may be deferred freely", "no docs/standards.json statement applies: the diff is tests/** and this run's own docs/fixes/** artifacts only"]
---

# Review

Scope: `git diff origin/main` on this branch — `tests/test_cli.py`,
`tests/test_cli_process_reaping.py`, `tests/test_charter_replay.py`, and
the run's artifacts. Scaled to the blast radius in `defect.md`: test-only,
no shipped module, no mirrored file.

Reviewed by the run's own author. ADR-0036 clause 2 wants a
non-authoring reader before merge; that is unmet here and is carried into
`release.md`.

## Correctness

### 1. Can the wider window hide a real escape? — checked, no

The risk worth the most attention: a 15x larger window could let a
grandchild that `harness_run` failed to signal pass anyway. It cannot,
because the fakes' grandchild is `sleep 300`: unsignalled, it is alive at
30 s, and the final `pid_alive` fails. Not reasoned only — the mutation in
`verification.md` §2 removed the group kill and both reaping tests failed
with `grandchild survived harness_run`. The window must stay well under
300 s for that to keep holding; the `REAP_GRACE` comment says so.

### 2. Does the regression test leave anything behind? — checked, no

The victim is the test's own child. Cleanups run last-in first-out:
cancel the timer, kill the victim (a no-op once dead — `Popen.kill`
checks `returncode` first), collect it, then `setUp`'s `_cleanup`, which
finds the PID gone. A failing run still ends clean: the timer or the
cleanup kill fires, and `wait()` collects. Because the victim is collected
only at cleanup, it sits as a zombie during the assertion. The post-#571
`pid_alive` reads that as dead, which is exactly the state this test
needs.

### 3. A regressed group kill now costs ~30 s per reaping test — minor, deferred

**Failure scenario:** someone breaks the group kill in `harness_run` or
`run_single_query`. Each reaping test now takes ~30 s to report it
instead of ~2 s (63.4 s for the two `test_cli` tests in the mutation
run), so a CI run that fails this way is a couple of minutes slower.
**Deferred:** this cost falls only on a real regression, never on a
passing run. Paying it there is the trade the fix exists to make.

### 4. The watcher threads still budget on `time.time()` — minor, deferred

`watch_for_grandchild` in both sibling files waits up to 70 s on
`time.time()`. **Failure scenario:** a large forward step during that
wait ends it before the PID file appears, giving
`fake claude never started`. **Deferred:** that is a different assertion,
70 s is wide, and nothing has observed it failing. Changing it would
widen the diff past the defect. Logged so it is not re-derived.

## Design

### 5. A test module importing a constant from another — accepted

`tests/test_cli_process_reaping.py` now imports `REAP_GRACE` from
`test_cli`, the pattern `test_charter_replay.py` already used for
`ReadinessGatedClock`. A second `sys.path` insert of `tests/` is the cost,
and it copies the sibling's lines. This is the "one fact, one owner"
direction the repo wants. The three restated `2`s are what made this
defect a three-file fix.

### 6. The three grace-loop helpers are still verbatim copies — minor, deferred

Same smell as the `pid_alive` run, and this is the second defect to be
fixed in three places. **Deferred:** extracting a shared helper is a
design change outside `re-entry: implement`. The constant now has one
owner, so at least the number cannot drift. Recorded in `defect.md`
Notes.

## Security

Nothing to examine: no input boundary, secret, network or shell
interpolation. The regression test runs a fixed `["sleep", "300"]` argv.

## Not reviewed

- Which of the two hypothesised delays fired on the runner (see
  `verification.md`, Not verified). The fix does not depend on knowing.
- The Linux `/proc` branch; the PR's CI run exercises it.
