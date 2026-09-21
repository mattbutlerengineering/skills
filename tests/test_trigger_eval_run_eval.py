"""run_eval fan-out seam, claude harness: the shared contract lives in
harness_contract.RunEvalContract; this twin supplies the fake `claude`
executable and the claude-only seam tests (invocation flags,
registry-vocabulary consistency). Crashed-run accounting is harness-
independent and lives in the contract.

The fake lists the isolated project's .claude/commands/ dir (run_single_query
sets it as cwd) and echoes back the command stem matching the slug named in
the query, driving the real detection state machine.
"""
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# discover puts tests/ on sys.path; selective package-style runs
# (python3 -m unittest tests.test_trigger_eval_run_eval) need it added for the
# sibling harness_contract import
sys.path.insert(0, str(ROOT / "tests"))

import eval_schema  # noqa: E402
import trigger_eval  # noqa: E402
from harness_contract import RunEvalContract, case  # noqa: E402
from trigger_eval import _claude_invocation  # noqa: E402

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


class FakeClaudeTest(RunEvalContract, unittest.TestCase):
    FAKE = FAKE_CLAUDE
    HARNESS = "claude"


class TestHarnessRegistry(unittest.TestCase):
    """trigger_eval.HARNESSES is the runner's per-harness registration
    (ADR-0038); eval_schema.HARNESSES is the vocabulary (results grammar,
    --harness choices). One drifting past the other would let the CLI
    accept a harness with no adapter, or ship an adapter no flag can
    reach — so the key sets are pinned to each other."""

    def test_registry_keys_match_the_harness_vocabulary(self):
        self.assertEqual(set(trigger_eval.HARNESSES),
                         set(eval_schema.HARNESSES))


class TestClaudeInvocation(unittest.TestCase):
    """The isolation-critical flags of the claude invocation, pinned.

    An eval run's whole validity rests on these flags: without
    --setting-sources project, the user's global skills leak into the run
    and the eval discriminates among the wrong candidates. The e2e fakes
    above never see the flags (the fake claude ignores them), so an
    accidental deletion would pass every other test — this is the internal
    seam test that would catch it."""

    def invoke(self, isolate):
        project_dir, cmd = _claude_invocation(
            "a query", {"idea": "d"}, "run1234", None, isolate)
        self.addCleanup(shutil.rmtree, project_dir, ignore_errors=True)
        return cmd

    def test_isolate_pins_setting_sources_to_project(self):
        cmd = self.invoke(isolate=True)
        index = cmd.index("--setting-sources")
        self.assertEqual(cmd[index + 1], "project")

    def test_no_isolate_omits_setting_sources(self):
        self.assertNotIn("--setting-sources", self.invoke(isolate=False))

    def test_a_model_lands_after_its_flag(self):
        project_dir, cmd = _claude_invocation(
            "a query", {"idea": "d"}, "run1234", "claude-haiku-4-5", True)
        self.addCleanup(shutil.rmtree, project_dir, ignore_errors=True)
        index = cmd.index("--model")
        self.assertEqual(cmd[index + 1], "claude-haiku-4-5")


if __name__ == "__main__":
    unittest.main()
