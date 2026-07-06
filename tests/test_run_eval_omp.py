"""run_eval's omp harness path (issue #88), tested end-to-end through
the public interface with a fake `omp` executable on PATH (no real CLI,
no API calls) — test_run_eval.py's twin for the second harness.

The fake lists the isolated project's .claude/skills/ dir
(run_single_query sets it as cwd, build_omp_project_dir populates it)
and emits an omp-shaped toolcall_end event reading the skill named in
the query via its skill:// URI, driving the real omp detection state
machine.
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

# Query protocol: "fire:<slug>" -> emit a read of that slug's skill://
# URI; "fire:none" -> emit a tool-free agent_end. The query is the last
# argument of the omp invocation.
FAKE_OMP = r"""#!/bin/sh
for arg; do query="$arg"; done
slug="${query#fire:}"
if [ "$slug" = "none" ]; then
  echo '{"type": "agent_end", "messages": []}'
  exit 0
fi
name=$(ls .claude/skills/ | grep "^${slug}-skill-" | head -1)
# Backslashes in printf FORMAT strings get escape-processed by /bin/sh's
# printf, so pass the JSON pieces as %s arguments, emitted verbatim.
prefix='{"type": "message_update", "assistantMessageEvent": {"type": "toolcall_end", "toolCall": {"type": "toolCall", "id": "toolu_1", "name": "read", "arguments": {"path": "skill://'
suffix='"}}}}'
printf '%s%s%s\n' "$prefix" "$name" "$suffix"
"""


def case(case_id, expected, query, kind="direct"):
    return {"id": case_id, "kind": kind, "expected": expected, "query": query}


class FakeOmpTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="run-eval-omp-"))
        fake = self.dir / "omp"
        fake.write_text(FAKE_OMP, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = f"{self.dir}:{self.old_path}"
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        os.environ["PATH"] = self.old_path
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_quiet(self, cases, descriptions, **kwargs):
        with redirect_stderr(StringIO()) as err:
            output = run_eval(cases, descriptions, harness="omp", **kwargs)
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


if __name__ == "__main__":
    unittest.main()
