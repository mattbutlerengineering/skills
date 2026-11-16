"""Every product adapter that shells out reads the child's output as UTF-8.

`text=True` alone decodes with the locale's codec, so under an ASCII locale
a gh or git line holding an em dash (issue titles, commit subjects, paths)
raised a UnicodeDecodeError that CLI_FAILURES does not name, and under a
Latin-1 locale it read as mojibake. The repo's other I/O passes
encoding="utf-8" everywhere; these adapters are the subprocess half of the
same convention. The probe runs in a child interpreter with UTF-8 mode and
locale coercion switched off, because the test runner's own locale is the
one thing the assertion must not depend on.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DASH = "—"

# Run in the child: each entry maps an adapter to the text it returned for
# a program that wrote an em dash as UTF-8 bytes.
PROBE = r"""
import json, os, stat, sys, tempfile
sys.path.insert(0, sys.argv[1])
import cli, conductor_merge, reap_worktrees

EMIT = "import sys; sys.stdout.buffer.write('—'.encode('utf-8'))"
ECHO = ("import sys; sys.stdout.buffer.write("
        "sys.stdin.buffer.read())")
argv = [sys.executable, "-c", EMIT]
script = os.path.join(tempfile.mkdtemp(), "fakebin")
with open(script, "w", encoding="utf-8") as handle:
    handle.write("#!/bin/sh\nprintf '\\342\\200\\224'\n")
os.chmod(script, os.stat(script).st_mode | stat.S_IXUSR)
out = {
    "cli.runner stdout": cli.runner(sys.executable)(["-c", EMIT]).stdout,
    "cli.runner stdin": cli.runner(sys.executable)(
        ["-c", ECHO], input="—").stdout,
    "cli.version": cli.version(script),
    "conductor_merge.run_tool": conductor_merge.run_tool(argv).stdout,
    "reap_worktrees.run": reap_worktrees.run(argv).stdout,
}
print(json.dumps(out))
"""


class TestAdaptersReadUtf8UnderAnAsciiLocale(unittest.TestCase):
    def test_every_adapter_returns_the_em_dash_intact(self):
        env = {**os.environ, "PYTHONUTF8": "0",
               "PYTHONCOERCECLOCALE": "0", "LC_ALL": "C", "LANG": "C"}
        env.pop("PYTHONIOENCODING", None)
        run = subprocess.run([sys.executable, "-c", PROBE, str(ROOT)],
                             capture_output=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr.decode("utf-8", "replace"))
        got = json.loads(run.stdout.decode("ascii"))
        self.assertEqual(len(got), 5)
        self.assertEqual(got, {name: DASH for name in got})


if __name__ == "__main__":
    unittest.main()
