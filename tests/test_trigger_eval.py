"""run_single_query's cleanup contract with the harness stream stubbed
out at the cli seam (ADR-0045) — no stdlib monkeypatching. The process
lifecycle (group kill, wait, pipe close) is cli.harness_run's contract,
pinned at tests/test_cli.py; the real-subprocess composition is pinned
at tests/test_process_reaping.py. What remains run_single_query's own
duty — and what this module pins — is the per-run project dir: created
once, removed whatever the stream does. A leaked dir per query times
hundreds of runs is the failure this guards. The version probe lives at
the cli seam (tests/test_cli.py) and the record()/collision pin at
tests/test_trigger_scoring.py.
"""
import contextlib
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cli
import protocol
import trigger_eval


class TestRunSingleQueryCleanup(unittest.TestCase):
    """The finally block's contract: whether the harness stream never
    spawned or ran to a verdict, the per-run project dir is removed and
    the detection result passes through untouched."""

    DESCRIPTIONS = {"next": "Route to the next stage."}

    def project_dirs(self):
        """mkdtemp wrapper recording every project dir the run makes."""
        created = []
        real = tempfile.mkdtemp

        def record(*args, **kwargs):
            path = real(*args, **kwargs)
            created.append(Path(path))
            return path
        return created, record

    def test_a_harness_that_never_spawns_still_removes_the_project_dir(self):
        created, record = self.project_dirs()

        @contextlib.contextmanager
        def no_spawn(cmd, cwd, timeout, env=None, spawn=None):
            raise OSError("no harness binary")
            yield  # pragma: no cover — the raise is the point
        with mock.patch.object(tempfile, "mkdtemp", record), \
                mock.patch.object(cli, "harness_run", no_spawn):
            with self.assertRaises(OSError):
                trigger_eval.run_single_query("q", self.DESCRIPTIONS, 5,
                                              None, True)
        self.assertEqual(len(created), 1)
        self.assertEqual([p for p in created if p.exists()], [])

    def test_the_detection_result_passes_through_and_the_dir_is_removed(self):
        created, record = self.project_dirs()
        seen = {}

        @contextlib.contextmanager
        def fake_run(cmd, cwd, timeout, env=None, spawn=None):
            seen["cmd"], seen["cwd"] = cmd, Path(cwd)
            yield iter(())

        def fake_detect(events, name_to_slug):
            return "next"
        adapter = trigger_eval.HARNESSES["claude"]._replace(
            detect=fake_detect)
        with mock.patch.object(tempfile, "mkdtemp", record), \
                mock.patch.object(cli, "harness_run", fake_run), \
                mock.patch.dict(trigger_eval.HARNESSES,
                                {"claude": adapter}):
            fired = trigger_eval.run_single_query("q", self.DESCRIPTIONS,
                                                  5, None, True)
        self.assertEqual(fired, "next")
        # the registry invocation is what ran: its project dir was the
        # cwd, its command carried the query, and the dir is gone now
        self.assertEqual(len(created), 1)
        self.assertEqual(seen["cwd"], created[0])
        self.assertIn("q", seen["cmd"])
        self.assertEqual([p for p in created if p.exists()], [])


class TestLoadDescriptions(unittest.TestCase):
    """load_descriptions shares lint's frontmatter contract
    (protocol.skill_frontmatter_problems, ADR-0052). The pinned
    divergence: an overlong description used to pass eval but fail
    lint — now both refuse it with the same string."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="eval-skills-"))
        self.addCleanup(shutil.rmtree, self.root)
        for slug in protocol.ALL_SKILLS:
            self.seed(slug, f"---\nname: {slug}\ndescription: d({slug})\n"
                            "---\n\nbody\n")

    def seed(self, slug, text):
        skill_dir = self.root / "skills" / slug
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")

    def test_conformant_tree_yields_every_description(self):
        descriptions = trigger_eval.load_descriptions(self.root)
        self.assertEqual(sorted(descriptions), sorted(protocol.ALL_SKILLS))
        self.assertEqual(descriptions["idea"], "d(idea)")

    def test_overlong_description_fails_loudly_with_lints_string(self):
        overlong = "x" * (protocol.SKILL_DESCRIPTION_LIMIT + 1)
        self.seed("idea",
                  f"---\nname: idea\ndescription: {overlong}\n---\n\nbody\n")
        with self.assertRaises(ValueError) as ctx:
            trigger_eval.load_descriptions(self.root)
        self.assertIn("skills/idea/SKILL.md description exceeds Pi's "
                      "1024-char limit", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
