"""The fixture recorders stay importable callers of the cli seam.

The two record.py scripts under tests/fixtures/ run rarely (only when a
pinned transcript is re-recorded) and CI never executes them, so a seam
move can strand them silently — round 5's cli_version extraction did
exactly that. This pin imports each script as a module (its __main__
guard keeps it inert), so the suite fails the day a recorder's imports
drift behind the seams they call.
"""
import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RECORDERS = (
    REPO / "tests" / "fixtures" / "transcripts" / "record.py",
    REPO / "tests" / "fixtures" / "omp-transcripts" / "record.py",
)


class TestRecordersImport(unittest.TestCase):
    def test_each_recorder_imports_clean(self):
        for path in RECORDERS:
            with self.subTest(recorder=str(path.relative_to(REPO))):
                name = f"recorder_{path.parent.name.replace('-', '_')}"
                spec = importlib.util.spec_from_file_location(name, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)


if __name__ == "__main__":
    unittest.main()
