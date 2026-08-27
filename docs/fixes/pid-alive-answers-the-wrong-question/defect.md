---
stage: capture
run: maintenance:pid-alive-answers-the-wrong-question
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance is recorded at the head of
  autorun-brief.md"]
---

# Defect: `pid_alive` answers the wrong question

## Defect

`pid_alive` is defined identically in two test files:

```python
def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
```

`os.kill(pid, 0)` asks the kernel *does a process table entry exist for
this PID, and may I signal it*. It does not ask *is that process still
running*. A **zombie** — terminated, but not yet collected by its parent
or by init — still owns its table entry, so the call succeeds and the
predicate reports a dead process as alive.

Both files consume it the same way, in a grace loop that waits for a
killed grandchild to disappear:

```python
deadline = time.time() + 2
while time.time() < deadline and pid_alive(pid):
    time.sleep(0.05)
self.assertFalse(pid_alive(pid), "grandchild survived ...")
```

So the assertion does not test *the grandchild died*. It tests *the
grandchild died **and** was collected within two seconds*. Collection is
the operating system's business and is not what these tests are about.

Expected: a terminated process reads as dead.
Observed: a terminated process reads as alive until something collects it.

## Reproduction / Evidence

Measured this session on macOS (Darwin 25.5.0), stdlib only:

```
child pid 12262: ps state = 'Z'  (Z = zombie)
pid_alive() says: True

=> a DEAD process is reported ALIVE
after wait(), pid_alive() says: False
```

The child was `subprocess.Popen([sys.executable, "-c", "pass"])`, left
uncollected. `ps -o stat=` reports `Z`; the process is definitively
terminated. `pid_alive` returns `True` for it, and returns `False` only
once `wait()` reaps it — confirming the predicate tracks collection, not
liveness.

## Root-cause hypothesis

Not a hypothesis — the mechanism above is demonstrated. The predicate
conflates *exists in the process table* with *is running*.

What remains genuinely unknown is whether this defect is what makes the
suite flake in the improvement routine's sandbox. See `Ruled out`.

## Blast radius

Test-only; no shipped module is affected, and no file in
`factory_init.MIRRORS` is touched, so no manifest regeneration.

The cost is diagnostic, not functional. The improvement-routine journal
(#181) records a `"grandchild survived"` failure on 2026-08-08, 08-13,
08-18, 08-19 and 08-25 — five runs — each time logged as a fresh "one-off
environment flake, not chased". They are not five flakes: they are one
assertion, reached through two verbatim copies of the same helper, which
is why the test *name* differs each time and the pattern stayed hidden.
Review and Ship scale down accordingly.

## Ruled out

- **Zombie-blindness explains the observed flakes — refuted.** The
  obvious next step was to blame this defect for the five journal
  entries. Driving it says otherwise. In the exited-leader path that both
  named flaky tests exercise, the orphaned grandchild is collected by
  init in **3.5 ms**, and is never even observably a zombie — against a
  2000 ms budget, a ~570x margin that load does not close. In the
  surviving-leader path, `/bin/sh` reaps its own background children, so
  no zombie persists there either. The defect is real; it is not the
  cause of these failures, and this run does not claim it is.
- **Reproducing the flake locally — did not.** 60 consecutive runs of
  `tests.test_cli_process_reaping` on an idle machine: 0 failures. That
  is the condition under which it is expected to pass, so it is not
  evidence either way, and it is recorded so nobody re-runs it expecting
  a different answer.
- **PID reuse — open, untested.** The predicate asks about a *number*,
  not about a process, so a recycled PID would also read as a survivor.
  This fits the load-correlation the zombie theory could not, but it has
  not been tested and is explicitly not claimed here.

## Work items

- [x] **Pin and fix the CLI copy** — add a regression test that a
  terminated-but-uncollected process reads as dead, then correct
  `pid_alive` in `tests/test_cli_process_reaping.py`.
  - Accept: the new test fails against the current predicate for the
    right reason, and passes after the fix; `tests.test_cli_process_reaping`
    is green.
- [x] **Pin and fix the charter-replay copy** — the same, in
  `tests/test_charter_replay.py`.
  - Accept: the new test fails first and passes after; the offline half
    of `tests.test_charter_replay` is green. The live replay is never run
    (it costs real model spend).
- [x] **Battery green** — the repo's full verification set.
  - Accept: `python3 -m unittest discover tests` OK, `python3 lint.py`
    0 problems, `python3 gates.py` 0 problems and `--selftest` ok, with
    output quoted in `verification.md`.

## Notes

- 2026-08-27: the two `pid_alive` definitions are verbatim duplicates, as
  are the two `assert_grandchild_reaped` helpers that consume them. That
  is a second-owner smell and it is why one defect presented under many
  test names. It is **logged, not fixed** — de-duplicating test helpers is
  a design change outside a `re-entry: implement` run, and `one_owner.py`
  excludes `tests/**` from its universe, so the pass would not have caught
  it. An unclaimed backlog seed already covers that exclusion.
- 2026-08-27: `os.waitpid(pid, os.WNOHANG)` is not available as a fix.
  The grandchild is not a child of the test process, so `waitpid` raises
  `ChildProcessError` for it.
