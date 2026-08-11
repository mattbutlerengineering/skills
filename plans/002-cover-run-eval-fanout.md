# Plan 002: Cover `run_eval`'s fan-out and counter assembly with an end-to-end fake-CLI test

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 79b08fc..HEAD -- trigger_eval.py tests/test_trigger_eval_run_eval.py`
> If `trigger_eval.py`'s `run_eval` changed since this plan was written,
> compare the "Current state" excerpt against the live code before
> proceeding; on a mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (composes with plan 001; see Maintenance notes)
- **Category**: tests
- **Planned at**: commit `79b08fc`, 2026-07-03 (refreshed from the 8399f85 original by a /improve re-audit; `run_eval` excerpt re-verified unchanged at HEAD)

## Why this matters

`run_eval` is the glue between the well-tested pieces: it fans cases ×
`runs_per_query` out over a `ProcessPoolExecutor`, folds each run's fired
slug (or a worker exception) into per-case `Counter`s, and assembles the
scored results. `score_case`/`summarize` are covered
(`tests/test_trigger_eval_scoring.py`) and detection is covered
(`tests/test_trigger_eval_detection.py`), but the fan-out itself has zero
coverage. A defect here (miscounted runs, a case silently dropped, an
exception mishandled) makes the measurement tool lie — and LEDGER evidence
is built from this tool's output, so a silent miscount poisons the repo's
honesty policy at the source.

## Current state

- `trigger_eval.py:253-286` at commit `79b08fc` (unchanged since `8399f85`) — the function under test:

```python
def run_eval(cases, descriptions, workers, runs_per_query, timeout,
             threshold, model, isolate):
    """Fan out cases x runs_per_query; return per-case results + summary."""
    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_case = {
            executor.submit(run_single_query, case["query"], descriptions,
                            timeout, model, isolate): case["id"]
            for case in cases
            for _ in range(runs_per_query)
        }
        fired_by_case = {}
        done = 0
        for future in as_completed(future_to_case):
            case_id = future_to_case[future]
            try:
                fired = future.result()
            except Exception as err:
                print(f"warning: run for {case_id!r} failed: {err}",
                      file=sys.stderr)
                fired = None
            counts = fired_by_case.setdefault(case_id, Counter())
            counts[fired or "none"] += 1
            done += 1
            print(f"progress: {done}/{len(future_to_case)} runs",
                  file=sys.stderr, end="\r")
    print(file=sys.stderr)

    results = [
        score_case(case, fired_by_case.get(case["id"], Counter()),
                   sum(fired_by_case.get(case["id"], Counter()).values()),
                   threshold)
        for case in cases
    ]
    return {"results": results, **summarize(results)}
```

- `run_single_query` (same file, lines 169–204) runs `["claude", "-p",
  query, ...]` with `cwd=project_dir`. `build_project_dir` (lines 53–69)
  writes one command file per skill into
  `<project_dir>/.claude/commands/<slug>-skill-<run_id>.md`, where
  `run_id` is random per query. Detection matches when the command file's
  stem appears in the streamed tool-use JSON.
- **Test strategy — no refactor needed**: a fake `claude` executable on
  `PATH` makes `run_eval` testable end-to-end through its public
  interface (the repo's stated testing convention). The fake can't know
  the random `run_id`, but it runs with the project dir as its cwd, so it
  can *list* `.claude/commands/` and echo back the filename matching the
  slug the query asks for. This drives real detection, real subprocess
  fan-out, and real counter folding without the real CLI or any API call.
- Key seam facts the fake relies on (verified at `79b08fc`):
  - `run_single_query` passes `env` = parent env minus `CLAUDECODE` — so
    env vars set by the test (like a modified `PATH`) reach the fake.
  - Detection (`detect_fired`) fires on a `stream_event` /
    `content_block_start` with tool `Skill` followed by a
    `content_block_delta` whose `partial_json` contains the command stem —
    see `tests/test_trigger_eval_detection.py` helpers `block_start`/`delta`
    for the exact JSON shapes.
- Repo conventions: stdlib-only, plain `unittest`, module docstring
  explaining the seam, tests through public interfaces. Exemplars:
  `tests/test_trigger_eval_scoring.py` (case-dict helper), 
  `tests/test_trigger_eval_detection.py` (subprocess + stream-json shapes).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests   | `python3 -m unittest discover tests` | `OK`, exit 0 |
| One test module | `python3 -m unittest tests.test_trigger_eval_run_eval -v` | all pass |
| Lint    | `python3 lint.py` | `lint: 0 problem(s) across 13 skills`, exit 0 |

## Scope

**In scope**:
- `tests/test_trigger_eval_run_eval.py` (create) — the only file this plan adds.
- `trigger_eval.py` — **read-only**. This plan must not modify it.

**Out of scope** (do NOT touch):
- Any production file. If `run_eval` turns out to need a change to be
  testable, that's a STOP condition, not a refactor license.
- `tests/test_trigger_eval_scoring.py`, `tests/test_trigger_eval_detection.py` —
  reuse their *patterns*, don't edit them.

## Git workflow

- Branch: `test/run-eval-fanout` off `main`.
- Conventional Commits, e.g. `test: cover run_eval fan-out and counter assembly via fake CLI`.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Write the fake-CLI test module

Create `tests/test_trigger_eval_run_eval.py`:

```python
"""run_eval fan-out seam: cases x runs_per_query over a process pool,
per-case Counter folding, exception-to-'none' bucketing, and scored
assembly — tested end-to-end through the public interface with a fake
`claude` executable on PATH (no real CLI, no API calls).

The fake lists the isolated project's .claude/commands/ dir (run_single_query
sets it as cwd) and echoes back the command stem matching the slug named in
the query, driving the real detection state machine.
"""
import os
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from trigger_eval import run_eval  # noqa: E402

# Query protocol: "fire:<slug>" -> emit that slug's command stem;
# "fire:none" -> emit nothing tool-related.
FAKE_CLAUDE = r"""#!/bin/sh
query="$2"
slug="${query#fire:}"
if [ "$slug" = "none" ]; then
  echo '{"type": "result"}'
  exit 0
fi
name=$(ls .claude/commands/ | grep "^${slug}-skill-" | head -1)
name="${name%.md}"
printf '%s\n' '{"type": "stream_event", "event": {"type": "content_block_start", "content_block": {"type": "tool_use", "name": "Skill"}}}'
printf '{"type": "stream_event", "event": {"type": "content_block_delta", "delta": {"type": "input_json_delta", "partial_json": "{\"skill\": \"%s\"}"}}}\n' "$name"
"""


def case(case_id, expected, query, kind="direct"):
    return {"id": case_id, "kind": kind, "expected": expected, "query": query}


class FakeClaudeTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="run-eval-"))
        fake = self.dir / "claude"
        fake.write_text(FAKE_CLAUDE, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = f"{self.dir}:{self.old_path}"
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        os.environ["PATH"] = self.old_path
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_quiet(self, *args, **kwargs):
        with redirect_stderr(StringIO()) as err:
            output = run_eval(*args, **kwargs)
        return output, err.getvalue()

    def test_counts_every_run_and_scores_per_case(self):
        cases = [case("a", "idea", "fire:idea"),
                 case("b", None, "fire:none", kind="distractor")]
        output, _ = self.run_quiet(
            cases, {"idea": "d", "prd": "d"}, workers=2, runs_per_query=2,
            timeout=10, threshold=0.5, model=None, isolate=False)
        by_id = {r["id"]: r for r in output["results"]}
        self.assertEqual(by_id["a"]["fired"], {"idea": 2})
        self.assertEqual(by_id["a"]["runs"], 2)
        self.assertTrue(by_id["a"]["pass"])
        self.assertEqual(by_id["b"]["fired"], {"none": 2})
        self.assertTrue(by_id["b"]["pass"])
        self.assertEqual(output["summary"]["total"], 2)
        self.assertEqual(output["summary"]["passed"], 2)

    def test_wrong_slug_fires_into_confusion_not_pass(self):
        cases = [case("a", "prd", "fire:idea")]
        output, _ = self.run_quiet(
            cases, {"idea": "d", "prd": "d"}, workers=1, runs_per_query=3,
            timeout=10, threshold=0.5, model=None, isolate=False)
        result = output["results"][0]
        self.assertEqual(result["fired"], {"idea": 3})
        self.assertFalse(result["pass"])
        self.assertEqual(output["confusion"]["prd"], {"idea": 3})

    def test_case_order_is_preserved_in_results(self):
        cases = [case(f"c{n}", "idea", "fire:idea") for n in range(5)]
        output, _ = self.run_quiet(
            cases, {"idea": "d"}, workers=3, runs_per_query=1,
            timeout=10, threshold=0.5, model=None, isolate=False)
        self.assertEqual([r["id"] for r in output["results"]],
                         [c["id"] for c in cases])


class TestWorkerExceptionBucketsAsNone(unittest.TestCase):
    """No fake claude on PATH at all: every worker raises FileNotFoundError;
    run_eval must warn and count the run as 'none', never crash."""

    def test_missing_cli_counts_none_and_warns(self):
        cases = [case("a", "idea", "fire:idea")]
        with redirect_stderr(StringIO()) as err:
            output = run_eval(cases, {"idea": "d"}, workers=1,
                              runs_per_query=2, timeout=5, threshold=0.5,
                              model=None, isolate=False)
        result = output["results"][0]
        self.assertEqual(result["fired"], {"none": 2})
        self.assertEqual(result["runs"], 2)
        self.assertFalse(result["pass"])
        self.assertIn("warning: run for 'a' failed", err.getvalue())


if __name__ == "__main__":
    unittest.main()
```

**Caveat for `TestWorkerExceptionBucketsAsNone`**: a real `claude` may be
on the developer's PATH. To force the exception deterministically, in that
test set `PATH` to a fresh empty temp dir for the duration of the test
(same setUp/cleanup pattern as `FakeClaudeTest`, but *without* writing the
fake executable, and *replacing* PATH instead of prepending). If
`ProcessPoolExecutor` fails to spawn workers with an empty PATH on your
platform, keep the system dirs but not the claude dir — e.g.
`os.environ["PATH"] = "/usr/bin:/bin"` — and add a comment saying why.

**Verify**: `python3 -m unittest tests.test_trigger_eval_run_eval -v` → all 4 tests pass
in under ~30 seconds. (These are characterization tests of existing
behavior — they should pass immediately; a failure means either the fake's
JSON shapes are wrong or you found a real fan-out bug. If the latter,
that's a STOP condition — report it, don't fix production code here.)

### Step 2: Full gates

**Verify**: `python3 -m unittest discover tests` → all pass;
`python3 lint.py` → `lint: 0 problem(s) across 13 skills`.

### Step 3: Commit

```bash
git add tests/test_trigger_eval_run_eval.py
git commit -m "test: cover run_eval fan-out and counter assembly via fake CLI"
```

## Test plan

This plan IS the test plan. Cases covered: happy-path counting across
workers and repeat runs; wrong-slug firing feeding the confusion matrix;
result order preserved relative to input cases; worker exception bucketed
as `"none"` with a warning (the silent-failure path). Structural pattern:
`tests/test_trigger_eval_detection.py` (stream-json shapes) and
`tests/test_trigger_eval_scoring.py` (case helper).

## Done criteria

- [ ] `python3 -m unittest tests.test_trigger_eval_run_eval -v` → 4 tests, all pass
- [ ] `python3 -m unittest discover tests` exits 0
- [ ] `python3 lint.py` exits 0
- [ ] `git status --short` shows only `tests/test_trigger_eval_run_eval.py` added; `trigger_eval.py` unmodified
- [ ] No test makes a network/API call (fake CLI only)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `run_eval`'s live code no longer matches the excerpt (drift).
- A test failure implicates production code (a real fan-out bug) — report
  the failing assertion and observed output; do not patch `trigger_eval.py`.
- The fake-CLI tests are flaky across 3 consecutive full-suite runs.
- Making the tests pass seems to require modifying any production file.

## Maintenance notes

- Plan 001 changes `run_single_query`'s cleanup (`start_new_session`,
  `killpg`, `stdout.close()`). These tests exercise `run_single_query`
  end-to-end, so they double as regression cover for that change — run
  both plans' suites together if both land.
- Issue #24 (transcript-level pinning of detection) may later want the
  fake-CLI shim extracted into a shared helper; fine, but out of scope here.
- Reviewer should scrutinize: PATH restoration in cleanup (a leaked PATH
  breaks every later test in the process), and that the exception test
  can't accidentally invoke a real `claude`.
