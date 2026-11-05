"""svg_check.py — the offline mechanical SVG check.

The run is docs/features/svg-mechanical-check/. Every case runs through
`check` or `main` over committed fixture SVGs under tests/fixtures/svg-check/
or inline bytes, offline, with exact strings; nothing here calls a model or
the network.
"""
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import svg_check

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/svg-check"
SENTINEL_TEXT = "SENTINEL-CONTENTS-MUST-NEVER-APPEAR"


def fixture(name):
    return (FIX / name).read_bytes()


def run_main(*argv):
    """(exit code, printed lines) for main(argv)."""
    out = io.StringIO()
    with redirect_stdout(out):
        code = svg_check.main(list(argv))
    return code, out.getvalue().splitlines()


class TestRefusal(unittest.TestCase):
    REFUSED = ("refused: the file declares a DTD or an entity",)

    def test_entity_expansion_is_refused(self):
        r = svg_check.check(fixture("entity-expansion.svg"))
        self.assertTrue(r.refusal.startswith(self.REFUSED[0]), r.refusal)
        self.assertEqual(r.problems, [])

    def test_external_entity_is_refused_and_never_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            sentinel = Path(tmp) / "sentinel.txt"
            sentinel.write_text(SENTINEL_TEXT)
            raw = fixture("external-entity.svg")
            self.assertIn(b"SENTINEL_PATH", raw)
            svg = Path(tmp) / "external-entity.svg"
            svg.write_bytes(raw.replace(b"SENTINEL_PATH",
                                        str(sentinel).encode()))
            r = svg_check.check(svg.read_bytes())
            self.assertTrue(r.refusal.startswith(self.REFUSED[0]))
            code, lines = run_main(str(svg))
        self.assertEqual(code, 2)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith(f"svg-check: {svg}: refused: "))
        self.assertNotIn(SENTINEL_TEXT, "\n".join(lines))
        self.assertNotIn(SENTINEL_TEXT, r.refusal)

    def test_a_benign_doctype_is_refused_too(self):
        data = (b'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "x.dtd">'
                b'<svg xmlns="http://www.w3.org/2000/svg" width="1" '
                b'height="1"/>')
        self.assertTrue(svg_check.check(data).refusal.startswith(
            self.REFUSED[0]))

    def test_truncated_file_is_not_well_formed(self):
        r = svg_check.check(fixture("truncated.svg"))
        self.assertTrue(r.refusal.startswith("not well-formed: "), r.refusal)
        code, lines = run_main(str(FIX / "truncated.svg"))
        self.assertEqual(code, 2)
        self.assertEqual(len(lines), 1)
        self.assertIn(": not well-formed: ", lines[0])

    def test_missing_path_cannot_read(self):
        missing = str(FIX / "no-such-file.svg")
        code, lines = run_main(missing)
        self.assertEqual(code, 2)
        self.assertEqual(len(lines), 1)
        self.assertTrue(
            lines[0].startswith(f"svg-check: {missing}: cannot read: "))

    def test_bad_usage_exits_2_with_one_line(self):
        for argv in ([], ["a.svg", "b.svg"], ["a.svg", "--embed-width"],
                     ["a.svg", "--embed-width", "wide"],
                     ["a.svg", "--embed-width", "0"], ["a.svg", "--nope"]):
            code, lines = run_main(*argv)
            self.assertEqual(code, 2, argv)
            self.assertEqual(len(lines), 1, argv)
            self.assertTrue(lines[0].startswith("svg-check: usage: "), argv)

    def test_invalid_embed_width_is_a_caller_bug(self):
        for bad in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                svg_check.check(b"<svg/>", bad)


if __name__ == "__main__":
    unittest.main()
