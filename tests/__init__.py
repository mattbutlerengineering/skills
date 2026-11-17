"""Put tools/ on sys.path before any test module imports a tool.

The tools are flat modules that import each other by bare name, so the
suite needs tools/ itself on the path, exactly as running a tool as a
script puts its own directory there. Loading the suite as the `tests`
package (`python3 -m unittest tests.<module>`, which run_tests.py spawns
per module, or `python3 -m unittest discover -s tests -t .`) runs this
first; a test that is run another way still carries its own insert.
"""
import sys
from pathlib import Path

_TOOLS = str(Path(__file__).resolve().parent.parent / "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
