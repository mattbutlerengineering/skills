"""The claude stream-json message reader (issue #861) — the registry's
one reading of the decoded event shape, and the charter replay's
transcript built from it.

The CLI emits two shapes for one assistant message under
--include-partial-messages: the stream_event partial frames and the
legacy full assistant message. The reader yields one normalised record
per assistant message and chooses frames over the legacy copy per
message id, never per run — choosing per run dropped every message the
CLI streamed without frames (a subagent's, say) whenever any other
message was framed, so a forbidden command in it passed the charter
replay unseen (the fail-open ADR-0053 kills).

Recorded real-CLI transcripts (tests/fixtures/transcripts/) pin both
consumers against what the CLI actually emitted.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import charter_replay  # noqa: E402
from trigger_eval import HARNESSES  # noqa: E402

RECORDINGS = Path(__file__).resolve().parent / "fixtures" / "transcripts"


def messages(events):
    return list(HARNESSES["claude"].messages(events))


def stream_event(inner, parent=None):
    return {"type": "stream_event", "event": inner,
            "parent_tool_use_id": parent}


def message_start(message_id):
    return stream_event({"type": "message_start",
                         "message": {"id": message_id}})


def block_start(content_block):
    return stream_event({"type": "content_block_start",
                         "content_block": content_block})


def block_delta(delta):
    return stream_event({"type": "content_block_delta", "delta": delta})


def block_stop():
    return stream_event({"type": "content_block_stop"})


def message_stop():
    return stream_event({"type": "message_stop"})


def legacy(content, message_id=None, parent=None):
    message = {"content": content}
    if message_id is not None:
        message["id"] = message_id
    return {"type": "assistant", "message": message,
            "parent_tool_use_id": parent}


def bash(command):
    return {"type": "tool_use", "name": "Bash", "input": {"command": command}}


def framed_text(text):
    return [block_start({"type": "text"}),
            block_delta({"type": "text_delta", "text": text}),
            block_stop()]


def replay(name):
    text = (RECORDINGS / f"{name}.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


class TestClaudeMessages(unittest.TestCase):

    def test_partial_message_frames_build_the_message(self):
        events = [
            block_start({"type": "text"}),
            block_delta({"type": "text_delta", "text": "plan"}),
            block_delta({"type": "text_delta", "text": "ning"}),
            block_stop(),
            block_start({"type": "tool_use", "name": "Bash"}),
            block_delta({"type": "input_json_delta",
                         "partial_json": '{"command": '}),
            block_delta({"type": "input_json_delta",
                         "partial_json": '"git status"}'}),
            block_stop(),
        ]
        [record] = messages(events)
        self.assertEqual(record["tool_calls"],
                         [{"name": "Bash",
                           "input": {"command": "git status"}}])
        self.assertEqual(record["texts"], ["planning"])

    def test_full_message_duplicates_of_frames_are_not_double_counted(self):
        # --include-partial-messages emits BOTH shapes for one message;
        # counting each once per shape would double every tool call.
        events = [
            block_start({"type": "tool_use", "name": "Bash"}),
            block_delta({"type": "input_json_delta",
                         "partial_json": '{"command": "git status"}'}),
            block_stop(),
            legacy([bash("git status")]),
        ]
        [record] = messages(events)
        self.assertEqual(len(record["tool_calls"]), 1)

    def test_frames_win_per_message_id_not_per_run(self):
        """A framed parent message, then a subagent's message the CLI
        sent only in the legacy shape: both are read."""
        events = [message_start("msg_parent"),
                  *framed_text("delegating"),
                  legacy([{"type": "text", "text": "delegating"}],
                         "msg_parent"),
                  message_stop(),
                  legacy([bash("git push origin main")], "msg_sub",
                         parent="toolu_task")]
        records = messages(events)
        self.assertEqual([r["id"] for r in records],
                         ["msg_parent", "msg_sub"])
        self.assertEqual(records[0]["texts"], ["delegating"])
        self.assertEqual(records[0]["tool_calls"], [])
        self.assertEqual(records[1]["tool_calls"],
                         [{"name": "Bash",
                           "input": {"command": "git push origin main"}}])
        self.assertEqual(records[1]["parent_tool_use_id"], "toolu_task")

    def test_the_legacy_only_message_reaches_the_charter_transcript(self):
        """The defect #861 names, through charter replay's public
        interface: a commands-scoped forbid on git push must see it."""
        events = [message_start("msg_parent"),
                  *framed_text("delegating"),
                  message_stop(),
                  legacy([bash("git push origin main")], "msg_sub",
                         parent="toolu_task")]
        built = charter_replay.transcript_from_events(events)
        self.assertEqual(built["tool_calls"],
                         [{"name": "Bash",
                           "input": {"command": "git push origin main"}}])
        self.assertEqual(built["text"], "delegating")

    def test_recordings_read_as_one_message_each(self):
        for name, message_id in (("skill-fires", "msg_01MQ55xaDeLv4eaBA6Ux3Z1Q"),
                                 ("no-fire", "msg_01HRU2rPWd3LY7XUuaJPcNLq")):
            with self.subTest(name):
                records = messages(replay(name))
                self.assertEqual([r["id"] for r in records], [message_id])
                self.assertIsNone(records[0]["parent_tool_use_id"])


class TestRecordedTranscriptsThroughCharterReplay(unittest.TestCase):
    """Real early-stopped recordings replayed through
    transcript_from_events: the open tool block at the cut still
    reaches the scorer, and nothing is double counted."""

    def test_skill_fires_recording(self):
        self.assertEqual(
            charter_replay.transcript_from_events(replay("skill-fires")),
            {"tool_calls": [{"name": "Skill", "input": {
                "raw": '{"skill": "prd-skill-pinned01'}}],
             "text": ""})

    def test_no_fire_recording(self):
        self.assertEqual(
            charter_replay.transcript_from_events(replay("no-fire")),
            {"tool_calls": [{"name": "Bash", "input": {}}],
             "text": "I'll start by finding where `userId` appears across"
                     " the codebase."})


if __name__ == "__main__":
    unittest.main()
