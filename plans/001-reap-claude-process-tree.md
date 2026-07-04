# Plan 001: Reap the whole claude process tree and close the stdout pipe in `run_single_query`

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 79b08fc..HEAD -- trigger_eval.py tests/test_process_reaping.py`
> If `trigger_eval.py` changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `79b08fc`, 2026-07-03 (refreshed from the 8399f85 original by a /improve re-audit; `run_single_query` excerpt re-verified unchanged at HEAD)

## Why this matters

`run_single_query` in `trigger_eval.py` launches `claude -p` and, in the
common early-detection path, returns *before* the process finishes. The
`finally` block kills only the direct child. The `claude` CLI spawns its own
children; those grandchildren are orphaned and keep running (and burning
tokens/API budget) after the eval moves on. Additionally, `process.stdout`
is never closed, so each query leaks one pipe file descriptor inside the
reused `ProcessPoolExecutor` worker. A 47-case eval at 3 runs per query is
141 leaked pipes and up to 141 orphaned process trees per eval run.

## Current state

- `trigger_eval.py` — the trigger/routing eval runner. Stdlib-only Python 3,
  POSIX-only by design (the module docstring already says "POSIX-only (uses
  select.select on pipes)"), so `os.killpg` is acceptable.
- The relevant function, `trigger_eval.py:169-204` at commit `79b08fc` (unchanged since `8399f85`):

```python
def run_single_query(query, descriptions, timeout, model, isolate):
    """Run one query in a fresh isolated project; return fired slug or None."""
    run_id = uuid.uuid4().hex[:8]
    name_to_slug = {f"{slug}-skill-{run_id}": slug for slug in descriptions}
    project_dir = build_project_dir(descriptions, run_id)

    cmd = [
        "claude", "-p", query,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    if isolate:
        cmd.extend(["--setting-sources", "project"])
    if model:
        cmd.extend(["--model", model])

    # Remove CLAUDECODE env var to allow nesting claude -p inside a
    # Claude Code session; the guard is for interactive terminal conflicts.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    process = None
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=project_dir,
            env=env,
        )
        return _watch_stream(process, name_to_slug, timeout)
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        shutil.rmtree(project_dir, ignore_errors=True)
```

- `trigger_eval.py` already imports `os`, `subprocess`, `shutil`. It does
  NOT import `signal` yet — you will add that import.
- Repo conventions: stdlib only, no third-party deps. Tests live in
  `tests/`, run with `python3 -m unittest discover tests`, and test through
  public interfaces. Subprocess-style integration tests already exist —
  see `tests/test_eval_schema.py` (class `TestRunnerRefusesMalformedSet`)
  and `tests/test_trigger_detection.py` (class `TestLivePipeAdapter`, which
  uses `subprocess.Popen` + `finally: process.kill(); process.wait();
  process.stdout.close()`). Match their style: module docstring explaining
  the seam, plain `unittest`, `tempfile` + `addCleanup`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests   | `python3 -m unittest discover tests` | `OK`, exit 0 (86 tests before this plan; more after) |
| One test module | `python3 -m unittest tests.test_process_reaping -v` | all pass |
| Lint    | `python3 lint.py` | `lint: 0 problem(s) across 13 skills`, exit 0 |

## Scope

**In scope** (the only files you should modify):
- `trigger_eval.py` (the `run_single_query` function and the import block only)
- `tests/test_process_reaping.py` (create)

**Out of scope** (do NOT touch, even though they look related):
- `_stream_events` / `detect_fired` / `_watch_stream` — the detection seam
  is covered by issue #22's tests; nothing there changes.
- `run_eval` — covered separately by plan 002.
- `eval_schema.py`, `protocol.py`, anything under `skills/` or `evals/`.

## Git workflow

- Branch: `fix/reap-claude-process-tree` off `main`.
- Conventional Commits, e.g. `fix: reap claude process tree and close stdout pipe in run_single_query`.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Write the failing test (RED)

Create `tests/test_process_reaping.py`. The test installs a **fake `claude`
executable** on `PATH` (so no real CLI or API is needed): a shell script
that spawns a grandchild `sleep`, writes the grandchild's PID to a file,
and then sleeps itself. `run_single_query` with a short timeout returns
`None`; the test then asserts BOTH processes are dead and the pipe was
closed.

```python
"""run_single_query must reap the entire claude process tree and close
its stdout pipe — early detection returns before the CLI exits, so
without process-group kill the CLI's own children are orphaned.

A fake `claude` on PATH (shell script spawning a grandchild sleep) stands
in for the real CLI; no API calls are made.
"""
import os
import stat
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from trigger_eval import run_single_query  # noqa: E402

FAKE_CLAUDE = """#!/bin/sh
# Spawn a grandchild that outlives us unless the caller kills our group.
sleep 300 &
echo $! > "$PID_FILE"
sleep 300
"""


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


class TestProcessTreeReaping(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="reap-"))
        self.addCleanup(self._cleanup)
        fake = self.dir / "claude"
        fake.write_text(FAKE_CLAUDE, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.pid_file = self.dir / "grandchild.pid"
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = f"{self.dir}:{self.old_path}"
        os.environ["PID_FILE"] = str(self.pid_file)

    def _cleanup(self):
        os.environ["PATH"] = self.old_path
        os.environ.pop("PID_FILE", None)
        if self.pid_file.is_file():
            pid = int(self.pid_file.read_text())
            if pid_alive(pid):
                os.kill(pid, 9)
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_grandchild_is_dead_after_timeout_return(self):
        fired = run_single_query("q", {"idea": "d"}, timeout=2,
                                 model=None, isolate=False)
        self.assertIsNone(fired)
        deadline = time.time() + 2
        while time.time() < deadline and not self.pid_file.is_file():
            time.sleep(0.05)
        self.assertTrue(self.pid_file.is_file(),
                        "fake claude never started")
        pid = int(self.pid_file.read_text())
        # brief grace for the kill to land
        deadline = time.time() + 2
        while time.time() < deadline and pid_alive(pid):
            time.sleep(0.05)
        self.assertFalse(pid_alive(pid),
                         "grandchild survived run_single_query")


if __name__ == "__main__":
    unittest.main()
```

**Verify**: `python3 -m unittest tests.test_process_reaping -v` →
`test_grandchild_is_dead_after_timeout_return` **FAILS** with
"grandchild survived run_single_query". (If it errors because the fake
`claude` was not found, fix the PATH setup before proceeding — the RED
must be the assertion, not a setup error.)

### Step 2: Implement the fix (GREEN)

In `trigger_eval.py`:

1. Add `import signal` to the import block (alphabetical order:
   between `select` and `shutil`).
2. In `run_single_query`, add `start_new_session=True` to the
   `subprocess.Popen(...)` call so the CLI gets its own process group.
3. Replace the `finally` block with:

```python
    finally:
        if process is not None:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    process.kill()
                process.wait()
            process.stdout.close()
        shutil.rmtree(project_dir, ignore_errors=True)
```

Notes: with `start_new_session=True`, `process.pid` IS the process-group
id. `ProcessLookupError` covers the group already being gone;
`PermissionError` is the paranoid fallback. `process.stdout.close()` runs
whether or not the process was already dead — that is the fd-leak half of
this fix.

**Verify**: `python3 -m unittest tests.test_process_reaping -v` → PASS.

### Step 3: Full gates

**Verify**: `python3 -m unittest discover tests` → all pass (previous count
plus the new test), and `python3 lint.py` → `lint: 0 problem(s) across 11
skills`.

### Step 4: Commit

```bash
git add trigger_eval.py tests/test_process_reaping.py
git commit -m "fix: reap claude process tree and close stdout pipe in run_single_query"
```

## Test plan

- New: `tests/test_process_reaping.py::test_grandchild_is_dead_after_timeout_return`
  (the regression this plan fixes). Model structure after
  `tests/test_trigger_detection.py`'s `TestLivePipeAdapter`.
- Existing detection tests must stay green — the fix must not change what
  `run_single_query` returns, only how it cleans up.
- Verification: `python3 -m unittest discover tests` → all pass.

## Done criteria

- [ ] `python3 -m unittest discover tests` exits 0, includes the new test
- [ ] `python3 lint.py` exits 0
- [ ] `grep -n "start_new_session=True" trigger_eval.py` → one match inside `run_single_query`
- [ ] `grep -n "killpg" trigger_eval.py` → one match in the `finally` block
- [ ] `grep -n "stdout.close()" trigger_eval.py` → one match in the `finally` block
- [ ] `git status --short` shows only the two in-scope files changed
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `run_single_query` in the live `trigger_eval.py` no longer matches the
  excerpt above (drift — e.g. plan 002 or an issue landed first and moved
  the code).
- The RED test in Step 1 *passes* before any fix — that means reaping was
  already added elsewhere; report instead of rewriting.
- The test is flaky across 3 consecutive runs after the fix (timing on a
  loaded machine) — report with the failure output rather than padding
  sleeps past 5 seconds.
- The fix appears to require touching `_stream_events` or `run_eval`.

## Maintenance notes

- If Windows support is ever added, `os.killpg`/`start_new_session` must be
  replaced (e.g. `CREATE_NEW_PROCESS_GROUP` + `taskkill /T`); the module is
  documented POSIX-only today, so this is deliberately not handled.
- Plan 002 (run_eval coverage) uses the same fake-`claude`-on-PATH
  technique; if both land, a reviewer may suggest extracting a shared shim
  helper — fine, but not required by either plan.
- Reviewer should scrutinize: the `finally` still runs `shutil.rmtree` even
  when kill raises, and `process.stdout.close()` is unconditional for a
  started process.
