"""Trigger-eval detection seam: the fired-slug state machine — decoded
stream-json events in, fired slug (or None) out (issue #22).

detect_fired is pure (no process, pipe, or clock), so synthetic event
dicts drive every branch the state machine distinguishes: early detection
via input_json_delta, the content_block_stop/message_stop fallbacks, the
legacy full assistant message shape, a different tool firing first, and
the result event. The live-pipe adapter (cli.EventStream, ADR-0053)
gets one real-subprocess test proving the feed, plus the exit-order seam:
buffered output must survive a process that exits before the reader's
first poll, without an orphan-held pipe stalling the run. Recorded
real-CLI transcripts are the seam's second adapter (issue #24): replaying
them pins the CLI's actual output shape, so drift breaks CI instead of
silently corrupting eval results.
"""
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import cli  # noqa: E402
from protocol import ALL_SKILLS  # noqa: E402
from trigger_eval import detect_fired  # noqa: E402

NAMES = {"prd-skill-abc123": "prd", "idea-skill-abc123": "idea"}


def block_start(tool_name):
    return {"type": "stream_event",
            "event": {"type": "content_block_start",
                      "content_block": {"type": "tool_use",
                                        "name": tool_name}}}


def delta(partial_json):
    return {"type": "stream_event",
            "event": {"type": "content_block_delta",
                      "delta": {"type": "input_json_delta",
                                "partial_json": partial_json}}}


def stop(stop_type="content_block_stop"):
    return {"type": "stream_event", "event": {"type": stop_type}}


def assistant(tool_name, tool_input):
    return {"type": "assistant",
            "message": {"content": [{"type": "tool_use", "name": tool_name,
                                     "input": tool_input}]}}


def exploding_events(events):
    """Yield the given events, then fail the test if pulled further —
    proves the state machine returned early, mid-stream."""
    yield from events
    raise AssertionError("detection kept consuming after it should "
                         "have decided")


class TestEarlyDetection(unittest.TestCase):
    def test_slug_returned_mid_stream_from_accumulated_deltas(self):
        events = exploding_events([
            block_start("Skill"),
            delta('{"skill": "prd-sk'),
            delta('ill-abc123"}'),
        ])
        self.assertEqual(detect_fired(events, NAMES), "prd")

    def test_other_tool_first_returns_none_without_reading_on(self):
        events = exploding_events([block_start("Bash")])
        self.assertIsNone(detect_fired(events, NAMES))

    def test_text_blocks_are_ignored_before_the_tool_use(self):
        text_block = {"type": "stream_event",
                      "event": {"type": "content_block_start",
                                "content_block": {"type": "text"}}}
        events = [text_block, block_start("Skill"),
                  delta('{"skill": "idea-skill-abc123"}')]
        self.assertEqual(detect_fired(iter(events), NAMES), "idea")

    def test_read_tool_is_watched_like_skill(self):
        events = [block_start("Read"),
                  delta('{"file_path": "prd-skill-abc123.md"}')]
        self.assertEqual(detect_fired(iter(events), NAMES), "prd")


class TestSubstringShadowing(unittest.TestCase):
    """review-skill-<id> is a substring of address-pr-review-skill-<id>,
    and ALL_SKILLS lists review first — so first-substring-match
    misattributes every address-pr-review fire to review (observed in
    the 2026-07-03 recorded runs). The longer command name must win."""

    SHADOWED = {"review-skill-abc123": "review",
                "address-pr-review-skill-abc123": "address-pr-review"}

    def test_longer_command_name_wins_over_its_substring(self):
        events = [block_start("Skill"),
                  delta('{"skill": "address-pr-review-skill-abc123"}')]
        self.assertEqual(detect_fired(iter(events), self.SHADOWED),
                         "address-pr-review")

    def test_shorter_name_still_matches_when_actually_fired(self):
        events = [block_start("Skill"),
                  delta('{"skill": "review-skill-abc123"}')]
        self.assertEqual(detect_fired(iter(events), self.SHADOWED),
                         "review")


class TestStopFallbacks(unittest.TestCase):
    def test_content_block_stop_with_no_match_returns_none(self):
        events = exploding_events([
            block_start("Skill"),
            delta('{"skill": "unrelated"}'),
            stop(),
        ])
        self.assertIsNone(detect_fired(events, NAMES))

    def test_content_block_stop_without_pending_tool_keeps_watching(self):
        events = [stop(), block_start("Skill"),
                  delta('{"skill": "prd-skill-abc123"}')]
        self.assertEqual(detect_fired(iter(events), NAMES), "prd")

    def test_message_stop_without_pending_tool_returns_none(self):
        events = exploding_events([stop("message_stop")])
        self.assertIsNone(detect_fired(events, NAMES))


class TestLegacyAssistantShape(unittest.TestCase):
    def test_skill_tool_input_matches(self):
        events = [assistant("Skill", {"skill": "prd-skill-abc123"})]
        self.assertEqual(detect_fired(iter(events), NAMES), "prd")

    def test_read_tool_file_path_matches(self):
        events = [assistant("Read",
                            {"file_path": "/tmp/idea-skill-abc123.md"})]
        self.assertEqual(detect_fired(iter(events), NAMES), "idea")

    def test_first_tool_use_being_neither_skill_nor_read_returns_none(self):
        events = exploding_events([assistant("Bash", {"command": "ls"})])
        self.assertIsNone(detect_fired(events, NAMES))


class TestTerminalEvents(unittest.TestCase):
    def test_result_event_returns_none(self):
        events = exploding_events([{"type": "result"}])
        self.assertIsNone(detect_fired(events, NAMES))

    def test_exhausted_stream_returns_none(self):
        self.assertIsNone(detect_fired(iter([]), NAMES))


class TestLivePipeAdapter(unittest.TestCase):
    """cli.EventStream feeds a real pipe through the same state machine:
    one subprocess emitting stream-json lines, non-JSON noise skipped."""

    def test_detects_through_a_real_subprocess_pipe(self):
        lines = ["not json",
                 json.dumps(block_start("Skill")),
                 json.dumps(delta('{"skill": "prd-skill-abc123"}'))]
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
                detect_fired(cli.EventStream(process, timeout=10), NAMES),
                "prd")
        finally:
            process.kill()
            process.wait()
            process.stdout.close()


class TestStreamEventsDrainsAfterExit(unittest.TestCase):
    """The reader must not lose buffered output when the process beats it
    to the exit: a fake harness writes its whole stream and exits within
    milliseconds, so on a loaded runner it is often dead before the
    reader's first poll — and a reader that breaks on exit before
    draining scores a fired run as 'none'. That race is CI-only (100
    local iterations of the fan-out contract never lose it), so these
    tests construct the post-exit states deterministically instead."""

    def test_buffered_events_survive_an_early_exit(self):
        # ~1000 lines ≈ 11 KB: spans multiple 8192-byte reads, yet stays
        # under the smallest default pipe capacity (16 KiB on macOS) so
        # the writer exits without blocking — wait() would deadlock on a
        # payload that fills the pipe, hence its own timeout.
        script = ("for n in range(1000):\n"
                  "    print('{\"n\": %d}' % n)\n")
        process = subprocess.Popen([sys.executable, "-c", script],
                                   stdout=subprocess.PIPE)
        self.addCleanup(process.stdout.close)
        process.wait(timeout=10)  # dead before the reader's first poll
        self.assertEqual(list(cli.EventStream(process, timeout=10)),
                         [{"n": n} for n in range(1000)])

    class DeadLeaderOpenPipe:
        """The exited-leader shape run_single_query can meet: the leader
        is gone (poll() says so) but an orphan still holds the write end,
        so EOF never comes. os.read needs a real fd, hence a real pipe;
        the payload is far under pipe capacity, so os.write never
        blocks."""

        def __init__(self, payload):
            read_fd, self.write_fd = os.pipe()
            os.write(self.write_fd, payload)
            self.stdout = os.fdopen(read_fd, "rb")

        def poll(self):
            return 0

        def close(self):
            self.stdout.close()
            os.close(self.write_fd)

    def test_a_dead_process_with_a_held_open_pipe_does_not_hang(self):
        # Why the reader still watches poll(): an idle orphan holding the
        # write end must not stall the run until timeout. The bound is a
        # fraction of the timeout so the test can only pass by breaking
        # early, never by riding the timeout out.
        timeout = 3
        process = self.DeadLeaderOpenPipe(b'{"n": 1}\n')
        self.addCleanup(process.close)
        start = time.time()
        events = list(cli.EventStream(process, timeout=timeout))
        self.assertEqual(events, [{"n": 1}])
        self.assertLess(time.time() - start, timeout / 3)


class TestRecordedTranscripts(unittest.TestCase):
    """Replay committed real claude -p transcripts through detect_fired
    and assert the outcome recorded in provenance.json — the detection
    seam's second adapter. Re-recording is documented in the fixtures'
    README; transcripts are never edited by hand."""

    DIR = Path(__file__).resolve().parent / "fixtures" / "transcripts"

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
        return detect_fired(iter(events), self.names)

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
