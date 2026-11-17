"""EventStream's timeout runs on the monotonic clock.

A wall-clock step (an NTP correction, a manual change) between the reader's
start and a later poll must neither abandon a healthy run nor stretch the
budget of a hung one. tests/test_cli.py already sizes its reap grace on
time.monotonic() for the same reason; the reader itself read time.time().
"""
import os
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import cli  # noqa: E402


class SteppedWallClock:
    """cli's `time` stand-in whose wall clock jumps an hour after its
    first read; monotonic stays real, as the OS keeps it."""

    def __init__(self):
        self.wall_reads = 0

    def time(self):
        self.wall_reads += 1
        return 1_000_000.0 + (3600 if self.wall_reads > 1 else 0)

    def monotonic(self):
        return time.monotonic()


class TestStreamTimeoutIgnoresWallClockSteps(unittest.TestCase):
    def test_a_forward_wall_clock_step_does_not_abandon_the_run(self):
        read_fd, write_fd = os.pipe()
        os.write(write_fd, b'{"type": "a"}\n{"type": "b"}\n')
        os.close(write_fd)
        with os.fdopen(read_fd, "rb") as stdout:
            process = SimpleNamespace(stdout=stdout, poll=lambda: 0)
            with mock.patch.object(cli, "time", SteppedWallClock()):
                stream = cli.EventStream(process, timeout=60)
                events = list(stream)
        self.assertEqual(events, [{"type": "a"}, {"type": "b"}])
        self.assertFalse(stream.timed_out)


if __name__ == "__main__":
    unittest.main()
