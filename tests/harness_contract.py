"""Shared scaffold for run_eval's per-harness e2e twins.

Every harness adapter in trigger_eval.HARNESSES must meet the same
fan-out contract: count every run, score per case, feed wrong slugs
into the confusion matrix, preserve case order. This mixin holds that
contract once — a twin (test_run_eval.py, test_run_eval_omp.py) sets
FAKE and HARNESS, and supplies only what genuinely differs: the fake
executable's event shapes and any harness-specific seam tests. The
executable name the fake shadows comes from the registry's own binary
field (ADR-0045), so the contract exercises the same name the runner
invokes.
"""
import os
import shutil
import stat
import sys
import tempfile
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from trigger_eval import HARNESSES, run_eval  # noqa: E402


def case(case_id, expected, query, kind="direct"):
    return {"id": case_id, "kind": kind, "expected": expected, "query": query}


class RunEvalContract:
    """Mixin for a unittest.TestCase twin: installs the fake harness
    binary at the front of PATH, then asserts the shared contract
    through run_eval's public interface (no real CLI, no API calls)."""

    FAKE = None     # shell script body emitting harness-shaped events
    HARNESS = None  # run_eval harness key; the binary comes from the registry

    def setUp(self):
        binary = HARNESSES[self.HARNESS].binary
        self.dir = Path(tempfile.mkdtemp(prefix=f"run-eval-{binary}-"))
        fake = self.dir / binary
        fake.write_text(self.FAKE, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = f"{self.dir}:{self.old_path}"
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        os.environ["PATH"] = self.old_path
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_quiet(self, cases, descriptions, **kwargs):
        with redirect_stderr(StringIO()) as err:
            output = run_eval(cases, descriptions, harness=self.HARNESS,
                              **kwargs)
        return output, err.getvalue()

    def test_counts_every_run_and_scores_per_case(self):
        cases = [case("a", "idea", "fire:idea"),
                 case("b", None, "fire:none", kind="distractor")]
        output, err = self.run_quiet(
            cases, {"idea": "d", "prd": "d"}, workers=2, runs_per_query=2,
            timeout=10, threshold=0.5, model=None, isolate=False)
        # A crashed worker buckets its run as 'none' and warns — without
        # this check it would masquerade as a routing miss below.
        self.assertNotIn("warning:", err)
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
