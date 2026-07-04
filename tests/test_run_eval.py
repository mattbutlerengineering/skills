"""run_eval fan-out seam: cases x runs_per_query over a process pool,
per-case Counter folding, exception-to-'none' bucketing, and scored
assembly — tested end-to-end through the public interface with a fake
`claude` executable on PATH (no real CLI, no API calls).

The fake lists the isolated project's .claude/commands/ dir (run_single_query
sets it as cwd) and echoes back the command stem matching the slug named in
the query, driving the real detection state machine.
"""
import os
import shutil
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
# Backslashes in printf FORMAT strings get escape-processed by /bin/sh's
# printf (eating the \" needed inside partial_json), so pass the JSON
# pieces as %s arguments, which are emitted verbatim.
prefix='{"type": "stream_event", "event": {"type": "content_block_delta", "delta": {"type": "input_json_delta", "partial_json": "{\"skill\": \"'
suffix='\"}"}}}'
printf '%s%s%s\n' "$prefix" "$name" "$suffix"
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
    """Workers can't find any `claude` executable: every run raises
    FileNotFoundError; run_eval must warn and count the run as 'none',
    never crash."""

    def setUp(self):
        # Replace (not prepend) PATH with a fresh empty temp dir so a real
        # `claude` on the developer's PATH can never be invoked.
        self.dir = Path(tempfile.mkdtemp(prefix="run-eval-nopath-"))
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = str(self.dir)
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        os.environ["PATH"] = self.old_path
        shutil.rmtree(self.dir, ignore_errors=True)

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
