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


def problems(data):
    return svg_check.check(data).problems


def wrap(body, root='width="400" height="200" viewBox="0 0 400 200"'):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" {root}>{body}</svg>'
            ).encode()


class TestDefects(unittest.TestCase):
    SINGLE = {
        "no-size.svg": "root width missing",
        "dup-id.svg": 'duplicate id "a" on 2 elements',
        "dangling-url.svg": "dangling url(#nope) in rect fill",
        "external-href.svg":
            'external href "https://example.com/x.png" on image',
    }

    def test_each_single_defect_fixture_prints_exactly_its_defect(self):
        for name, line in self.SINGLE.items():
            path = str(FIX / name)
            code, lines = run_main(path)
            self.assertEqual(code, 1, name)
            defects = [ln for ln in lines if "smallest text" not in ln
                       and "no text" not in ln]
            self.assertEqual(defects, [f"svg-check: {path}: {line}"], name)

    def test_all_four_names_every_defect(self):
        path = str(FIX / "all-four.svg")
        code, lines = run_main(path)
        self.assertEqual(code, 1)
        defects = {ln for ln in lines if "smallest text" not in ln
                   and "no text" not in ln}
        self.assertEqual(defects, {
            f"svg-check: {path}: root width missing",
            f'svg-check: {path}: duplicate id "a" on 2 elements',
            f"svg-check: {path}: dangling url(#nope) in rect fill",
            f'svg-check: {path}: external href '
            f'"https://example.com/x.png" on image',
        })
        self.assertEqual(len(defects), 4)

    def test_same_document_hrefs_pass(self):
        self.assertEqual(problems(fixture("same-doc-href.svg")), [])
        self.assertEqual(run_main(str(FIX / "same-doc-href.svg"))[0], 0)

    def test_clean_fixture_exits_0(self):
        self.assertEqual(problems(fixture("clean.svg")), [])
        self.assertEqual(run_main(str(FIX / "clean.svg"))[0], 0)

    def test_root_size_must_be_a_px_length(self):
        for value in ("100%", "10em", "0", "-5", "abc"):
            p = problems(wrap("", f'width="{value}" height="200"'))
            self.assertEqual(p, [f'root width "{value}" is not a px length'],
                             value)
        p = problems(wrap("", 'width="400" height="50%"'))
        self.assertEqual(p, ['root height "50%" is not a px length'])
        self.assertEqual(problems(wrap("", 'width="400px" height="2.5"')), [])
        self.assertEqual(problems(wrap("", 'viewBox="0 0 1 1"')),
                         ["root width missing", "root height missing"])

    def test_root_must_be_svg(self):
        r = svg_check.check(b"<html><body/></html>")
        self.assertEqual(r.problems, ["root element is html, not svg"])
        wrong_ns = b'<svg xmlns="http://example.com/x" width="1" height="1"/>'
        (only,) = problems(wrong_ns)
        self.assertTrue(only.startswith("root element is "), only)
        self.assertTrue(only.endswith(", not svg"), only)

    def test_xlink_href_and_other_reference_places(self):
        xl = 'xmlns:xlink="http://www.w3.org/1999/xlink"'
        self.assertEqual(problems(wrap(
            f'<use {xl} xlink:href="#gone"/>')),
            ['dangling href "#gone" on use'])
        self.assertEqual(problems(wrap(
            '<a href="https://example.com"><text>x</text></a>')),
            ['external href "https://example.com" on a'])
        self.assertEqual(problems(wrap(
            '<image href="data:image/png;base64,AAAA"/>')),
            ['external href "data:image/png;base64,AAAA" on image'])
        self.assertEqual(problems(wrap(
            '<rect style="fill:url(#gone)"/>')),
            ["dangling url(#gone) in rect style"])
        self.assertEqual(problems(wrap(
            '<rect fill="url(https://example.com/p.svg#x)"/>')),
            ["external url(https://example.com/p.svg#x) in rect fill"])
        self.assertEqual(problems(wrap(
            '<style>@import url(https://example.com/a.css);</style>')),
            ["external url(https://example.com/a.css) in <style>"])
        self.assertEqual(problems(wrap(
            '<style>/* url(#gone) */ .a { fill: url(#gone); }</style>')),
            ["dangling url(#gone) in <style>"])
        self.assertEqual(problems(wrap(
            '<rect id="p"/><rect fill="url( &quot;#p&quot; )"/>')), [])


if __name__ == "__main__":
    unittest.main()
