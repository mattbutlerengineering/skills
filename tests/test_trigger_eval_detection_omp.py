"""omp trigger-eval detection seam: the fired-slug state machine —
decoded omp --mode json events in, fired slug (or None) out (issue #88).

detect_omp_fired is pure (no process, pipe, or clock), detect_fired's
twin for the second harness (ADR-0031). In omp a skill loads through the
built-in read tool with a skill://<name> URI, so synthetic event dicts
drive every branch: decision at toolcall_end (before the tool executes),
the tool_execution_start fallback, non-read tools and non-skill reads
meaning no fire, and agent_end without a tool call. The live-pipe
adapter gets one real-subprocess test proving the feed. Recorded real
omp transcripts are the seam's second adapter: replaying them pins omp's
actual output shape, so drift breaks CI instead of silently corrupting
eval results.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from protocol import ALL_SKILLS  # noqa: E402
import cli  # noqa: E402
from trigger_eval import detect_omp_fired  # noqa: E402

NAMES = {"prd-skill-abc123": "prd", "idea-skill-abc123": "idea"}


def toolcall_end(tool_name, arguments):
    return {"type": "message_update",
            "assistantMessageEvent": {"type": "toolcall_end",
                                      "contentIndex": 1,
                                      "toolCall": {"type": "toolCall",
                                                   "id": "toolu_x",
                                                   "name": tool_name,
                                                   "arguments": arguments}}}


def message_update(event_type, **fields):
    return {"type": "message_update",
            "assistantMessageEvent": {"type": event_type, **fields}}


def execution_start(tool_name, args):
    return {"type": "tool_execution_start", "toolCallId": "toolu_x",
            "toolName": tool_name, "args": args}


def agent_end():
    return {"type": "agent_end", "messages": []}


def exploding_events(events):
    """Yield the given events, then fail the test if pulled further —
    proves the state machine returned early, mid-stream."""
    yield from events
    raise AssertionError("detection kept consuming after it should "
                         "have decided")


class TestToolcallEndDecides(unittest.TestCase):
    def test_skill_uri_read_returns_slug_before_execution(self):
        events = exploding_events([
            toolcall_end("read", {"path": "skill://prd-skill-abc123",
                                  "i": "load the prd skill"}),
        ])
        self.assertEqual(detect_omp_fired(events, NAMES), "prd")

    def test_direct_skill_md_path_read_matches_too(self):
        events = [toolcall_end(
            "read", {"path": ".claude/skills/idea-skill-abc123/SKILL.md"})]
        self.assertEqual(detect_omp_fired(iter(events), NAMES), "idea")

    def test_non_skill_read_returns_none_without_reading_on(self):
        events = exploding_events([
            toolcall_end("read", {"path": "package.json"}),
        ])
        self.assertIsNone(detect_omp_fired(events, NAMES))

    def test_other_tool_first_returns_none_without_reading_on(self):
        events = exploding_events([
            toolcall_end("bash", {"cmd": "ls"}),
        ])
        self.assertIsNone(detect_omp_fired(events, NAMES))

    def test_text_and_partial_toolcall_events_are_ignored_before_it(self):
        events = [message_update("text_delta", delta="Let me load"),
                  message_update("toolcall_start"),
                  message_update("toolcall_delta", delta='{"pa'),
                  toolcall_end("read", {"path": "skill://prd-skill-abc123"})]
        self.assertEqual(detect_omp_fired(iter(events), NAMES), "prd")


class TestExecutionStartFallback(unittest.TestCase):
    def test_skill_uri_execution_returns_slug(self):
        events = exploding_events([
            execution_start("read", {"path": "skill://idea-skill-abc123"}),
        ])
        self.assertEqual(detect_omp_fired(events, NAMES), "idea")

    def test_other_tool_execution_returns_none(self):
        events = exploding_events([execution_start("bash", {"cmd": "ls"})])
        self.assertIsNone(detect_omp_fired(events, NAMES))


class TestTerminalEvents(unittest.TestCase):
    def test_agent_end_without_tool_call_returns_none(self):
        events = exploding_events([
            message_update("text_delta", delta="Here is a plan instead."),
            agent_end(),
        ])
        self.assertIsNone(detect_omp_fired(events, NAMES))

    def test_exhausted_stream_returns_none(self):
        self.assertIsNone(detect_omp_fired(iter([]), NAMES))


class TestLivePipeAdapter(unittest.TestCase):
    """cli.EventStream feeds a real pipe through the omp state machine:
    one subprocess emitting omp-shaped JSON lines, non-JSON noise
    skipped."""

    def test_detects_through_a_real_subprocess_pipe(self):
        lines = ["not json",
                 json.dumps({"type": "agent_start"}),
                 json.dumps(toolcall_end(
                     "read", {"path": "skill://prd-skill-abc123"}))]
        script = ("import sys, time\n"
                  "for line in " + repr(lines) + ":\n"
                  "    print(line)\n"
                  "    sys.stdout.flush()\n"
                  "    time.sleep(0.05)\n"
                  "time.sleep(5)\n")
        process = subprocess.Popen([sys.executable, "-c", script],
                                   stdout=subprocess.PIPE)
        try:
            self.assertEqual(
                detect_omp_fired(cli.EventStream(process, timeout=10),
                                 NAMES),
                "prd")
        finally:
            process.kill()
            process.wait()
            process.stdout.close()


class TestRecordedTranscripts(unittest.TestCase):
    """Replay committed real omp -p transcripts through detect_omp_fired
    and assert the outcome recorded in provenance.json — the detection
    seam's second adapter. Re-recording is documented in the fixtures'
    README; transcripts are never edited by hand."""

    DIR = Path(__file__).resolve().parent / "fixtures" / "omp-transcripts"

    @classmethod
    def setUpClass(cls):
        cls.provenance = json.loads(
            (cls.DIR / "provenance.json").read_text(encoding="utf-8"))
        run_id = cls.provenance["run_id"]
        cls.names = {f"{slug}-skill-{run_id}": slug for slug in ALL_SKILLS}

    def replay(self, name):
        # strict, unlike cli.decode_events' junk tolerance: a committed
        # transcript must decode fully or the pinning is compromised
        text = (self.DIR / f"{name}.jsonl").read_text(encoding="utf-8")
        events = [json.loads(line) for line in text.splitlines()
                  if line.strip()]
        self.assertTrue(events, f"{name}.jsonl replayed to zero events")
        return detect_omp_fired(iter(events), self.names)

    def test_skill_fires_transcript_replays_to_recorded_slug(self):
        recorded = self.provenance["transcripts"]["skill-fires"]["fired"]
        self.assertIsNotNone(recorded)
        self.assertEqual(self.replay("skill-fires"), recorded)

    def test_no_fire_transcript_replays_to_none(self):
        self.assertIsNone(
            self.provenance["transcripts"]["no-fire"]["fired"])
        self.assertIsNone(self.replay("no-fire"))


if __name__ == "__main__":
    unittest.main()
