"""Put tools/ on sys.path before any test module imports a tool.

The tools are flat modules that import each other by bare name, so the
suite needs tools/ itself on the path, exactly as running a tool as a
script puts its own directory there. Loading the suite as the `tests`
package (`python3 -m unittest tests.<module>`, which run_tests.py spawns
per module, or `python3 -m unittest discover -s tests -t .`) runs this
first; a test that is run another way still carries its own insert.
"""
import os
import sys
from pathlib import Path

_TOOLS = str(Path(__file__).resolve().parent.parent / "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

# The suite is hermetic about the CI event. In a PR run the job's
# GITHUB_EVENT_PATH names the real PR (FACTORY_EVENT_PATH on a validator
# dispatch, which cli.read_event prefers), and tests that run gates
# inside a temp repo would otherwise judge that PR against a tree it
# never saw: detector P diffs from the PR's base sha, which a temp repo
# does not hold. Every test of an event-reading detector passes its own
# env; tests/test_suite_hermetic.py derives the names from cli.py.
for _name in ("GITHUB_EVENT_PATH", "GITHUB_EVENT_NAME",
              "FACTORY_EVENT_PATH"):
    os.environ.pop(_name, None)
