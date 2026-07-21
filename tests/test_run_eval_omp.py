"""run_eval's omp harness path (issue #88): the shared contract lives in
harness_contract.RunEvalContract; this twin supplies the fake `omp`
executable and the omp-only invocation seam tests.

The fake lists the isolated project's .claude/skills/ dir
(run_single_query sets it as cwd, build_omp_project_dir populates it)
and emits an omp-shaped toolcall_end event reading the skill named in
the query via its skill:// URI, driving the real omp detection state
machine.
"""
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling harness_contract import
sys.path.insert(0, str(ROOT / "tests"))

from harness_contract import RunEvalContract  # noqa: E402
from trigger_eval import _omp_invocation  # noqa: E402

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


class FakeOmpTest(RunEvalContract, unittest.TestCase):
    BINARY = "omp"
    FAKE = FAKE_OMP
    HARNESS = "omp"


class TestOmpInvocation(unittest.TestCase):
    """The isolation-critical flags of the omp invocation, pinned.

    omp has no --setting-sources equivalent, so its isolation is ALWAYS
    on: --no-session/--no-extensions/--no-rules keep the user's omp
    environment out, and the --skills glob restricts discovery to this
    run's own candidates. The e2e fake above ignores every flag, so an
    accidental deletion would pass every other test — this is the
    internal seam test that would catch it."""

    def invoke(self, isolate):
        project_dir, cmd = _omp_invocation(
            "a query", {"idea": "d"}, "run1234", None, isolate)
        self.addCleanup(shutil.rmtree, project_dir, ignore_errors=True)
        return cmd

    def test_isolation_flags_are_always_on(self):
        for isolate in (True, False):
            cmd = self.invoke(isolate)
            for flag in ("--no-session", "--no-extensions", "--no-rules"):
                self.assertIn(flag, cmd, isolate)

    def test_the_skills_glob_names_this_runs_suffix(self):
        cmd = self.invoke(isolate=True)
        index = cmd.index("--skills")
        self.assertEqual(cmd[index + 1], "*-skill-run1234")

    def test_the_query_is_the_last_argument(self):
        # The fake omp reads the query as the LAST argument; pin that
        # contract so a flag appended after the query cannot silently
        # swallow it.
        self.assertEqual(self.invoke(isolate=True)[-1], "a query")


if __name__ == "__main__":
    unittest.main()
