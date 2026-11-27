"""Audit defect #1854: EventStream decodes incrementally, so a multi-byte
character split across an 8 KiB read is not turned into U+FFFD."""
import select
import subprocess
import sys
import unittest

import cli


class TestChunkBoundary(unittest.TestCase):
    def test_split_multibyte_character_survives(self):
        prefix = '{"t": "'
        line = prefix + "a" * (8191 - len(prefix)) + "é" + '"}\n'
        code = ("import sys,time; sys.stdout.buffer.write("
                f"{line.encode()!r}); sys.stdout.flush(); time.sleep(0.2)")
        process = subprocess.Popen([sys.executable, "-c", code],
                                   stdout=subprocess.PIPE)
        try:
            # The budget starts once the child has written: counted from
            # the spawn, a cold start under load outlasts it and the
            # stream reads empty (the #446 rule ReadinessGatedClock keeps).
            ready, _, _ = select.select([process.stdout], [], [], 120)
            self.assertTrue(ready, "the child never wrote")
            events = list(cli.EventStream(process, timeout=10))
        finally:
            process.kill()
            process.wait()
            process.stdout.close()
        self.assertEqual(events[0]["t"][-3:], "aaé")


if __name__ == "__main__":
    unittest.main()
