"""The fixture recorders stay importable callers of the cli seam.

The record.py scripts under tests/fixtures/ run rarely (only when a
pinned transcript is re-recorded) and CI never executes them, so a seam
move can strand them silently — round 5's cli_version extraction did
exactly that. This pin imports each script as a module (its __main__
guard keeps it inert), so the suite fails the day a recorder's imports
drift behind the seams they call.

Which recorders those are is the filesystem's fact, globbed rather than
listed: a hand-typed tuple is a second statement of it, and the copy
that falls behind strands the recorder it forgot — the precise failure
this file exists to prevent, reintroduced by the shape of its own
enumeration.

The second pin is on what a recorder may commit. A transcript is eval
evidence (CLAUDE.md: never fabricate run or eval evidence), and the
recorders send the CLI's stderr to /dev/null, so a CLI that dies
instantly is silent — its empty stream reaches the detector, decides
nothing, and would be written out as a `fired: null` no-fire stamped
with a real cli_version. `recording_problems` is the refusal, and it is
identical in both recorders on purpose: they are standalone hand-run
scripts with no shared import between them, so the twin-ness is
asserted here rather than assumed.
"""
import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"


def recorders():
    """Every fixture recorder on disk, the enumeration this file pins."""
    return sorted(FIXTURES.glob("*/record.py"))


def load(path):
    """The recorder as a module. Executing it IS the import pin — the
    __main__ guard keeps it inert."""
    name = f"recorder_{path.parent.name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestRecordersImport(unittest.TestCase):
    def test_the_glob_finds_the_recorders_that_exist(self):
        # A glob that matched nothing would make every test below pass
        # vacuously — the failure mode of deriving an enumeration.
        found = {path.parent.name for path in recorders()}
        self.assertLessEqual({"transcripts", "omp-transcripts"}, found)

    def test_each_recorder_imports_clean(self):
        for path in recorders():
            with self.subTest(recorder=str(path.relative_to(REPO))):
                load(path)


class TestARecordingThatNeverRanIsNotANoFire(unittest.TestCase):
    """An empty stream is not evidence of anything, least of all of a
    skill declining to fire."""

    def test_every_recorder_refuses_to_commit_an_empty_stream(self):
        for path in recorders():
            with self.subTest(recorder=str(path.relative_to(REPO))):
                problems = load(path).recording_problems([])
                self.assertEqual(len(problems), 1)
                self.assertTrue(problems[0].startswith("record: "))

    def test_a_stream_with_output_is_recordable(self):
        for path in recorders():
            with self.subTest(recorder=str(path.relative_to(REPO))):
                self.assertEqual(load(path).recording_problems(["{}"]), [])

    def test_the_recorders_refuse_identically(self):
        # No shared import binds these scripts, so the one place the two
        # copies can be held together is here.
        refusals = {load(path).recording_problems([])[0]
                    for path in recorders()}
        self.assertEqual(len(refusals), 1, refusals)


if __name__ == "__main__":
    unittest.main()
