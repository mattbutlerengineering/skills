"""adr_status.py (issue #684): the review skill's ADR compliance pass
reads which of a repo's ADRs are live from this tool, never from its own
reading of status lines (ADR-0062). Status and standing come from
knowledge_plane's ADR record (issue #747), whose own tests pin the
standing of every status head.

Pinned against tempfile fixture trees, as board.py is.
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import adr_status  # noqa: E402


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# A latin-1 accent: valid text, invalid UTF-8 — a consumer repo's ADR
# written by an editor that never asked (issue #855).
UNDECODABLE = "# Caf\xe9\n\n- Status: accepted\n".encode("latin-1")


def decode_error(data):
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as err:
        return str(err)
    raise AssertionError("fixture decodes as UTF-8")


def adr(root, name, title, status_line):
    write(Path(root) / "docs" / "adr" / name,
          f"# {title}\n\n{status_line}\n- Date: 2026-01-01\n\n## Decision\n")


class TestGather(unittest.TestCase):
    def test_missing_root_is_the_one_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            model, problems = adr_status.gather(Path(tmp) / "nope")
            self.assertIsNone(model)
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith("adr-status: "))

    def test_no_adr_directory_is_an_empty_list_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(adr_status.gather(tmp), ({"adrs": []}, []))

    def test_entries_carry_id_file_title_status_standing(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr(tmp, "0002-new.md", "New way", "- Status: accepted")
            adr(tmp, "0001-old.md", "Old way",
                "- Status: superseded by ADR-0002")
            write(Path(tmp) / "docs/adr/README.md", "# Index\n")
            write(Path(tmp) / "docs/adr/TEMPLATE.md",
                  "# Title\n\n- Status: accepted\n")
            model, problems = adr_status.gather(tmp)
        self.assertEqual(problems, [])
        self.assertEqual(model["adrs"], [
            {"id": "ADR-0001", "file": "docs/adr/0001-old.md",
             "title": "Old way", "status": "superseded by ADR-0002",
             "standing": "retired", "superseded_by": "ADR-0002"},
            {"id": "ADR-0002", "file": "docs/adr/0002-new.md",
             "title": "New way", "status": "accepted",
             "standing": "active", "superseded_by": None},
        ])

    def test_an_undecodable_adr_is_a_problem_string_not_a_traceback(self):
        # Issue #855: adr_status promises problem strings, and runs
        # against arbitrary target repos.
        with tempfile.TemporaryDirectory() as tmp:
            adr(tmp, "0002-new.md", "New way", "- Status: accepted")
            path = Path(tmp) / "docs/adr/0001-cafe.md"
            path.write_bytes(UNDECODABLE)
            model, problems = adr_status.gather(tmp)
        self.assertIsNone(model)
        self.assertEqual(problems, [
            "adr-status: cannot read docs/adr/0001-cafe.md: "
            + decode_error(UNDECODABLE)])

    def test_frontmatter_status_is_read_when_no_status_line(self):
        """Repos outside this grammar keep status in frontmatter; the raw
        text still reaches the reviewer, flagged unrecognized."""
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "docs/adr/ADR-007-auth.md",
                  "---\nstatus: active\n---\n# Auth middleware\n")
            model, _ = adr_status.gather(tmp)
        [entry] = model["adrs"]
        self.assertEqual(entry["id"], "ADR-0007")
        self.assertEqual(entry["status"], "active")
        self.assertEqual(entry["standing"], "unrecognized")
        self.assertEqual(entry["title"], "Auth middleware")

    def test_no_status_anywhere_is_unrecognized_with_null_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "docs/adr/0003-bare.md", "# Bare\n")
            model, _ = adr_status.gather(tmp)
        [entry] = model["adrs"]
        self.assertIsNone(entry["status"])
        self.assertEqual(entry["standing"], "unrecognized")


class TestMain(unittest.TestCase):
    def test_prints_the_model_as_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            adr(tmp, "0001-a.md", "A", "- Status: provisional")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = adr_status.main([tmp])
        self.assertEqual(code, 0)
        [entry] = json.loads(out.getvalue())["adrs"]
        self.assertEqual(entry["standing"], "provisional")

    def test_missing_root_exits_nonzero_with_the_problem(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = adr_status.main(["/nonexistent/adr-status-root"])
        self.assertEqual(code, 1)
        self.assertIn("adr-status: 1 problem(s)", out.getvalue())


class TestThisRepo(unittest.TestCase):
    """The repo's own ADR tree reads with no unrecognized status — gates
    detector D already rejects one, so the two grammars cannot part."""

    def test_every_adr_here_has_a_recognized_standing(self):
        model, problems = adr_status.gather(ROOT)
        self.assertEqual(problems, [])
        self.assertTrue(model["adrs"])
        self.assertEqual(
            [e["id"] for e in model["adrs"]
             if e["standing"] == "unrecognized"], [])


if __name__ == "__main__":
    unittest.main()
