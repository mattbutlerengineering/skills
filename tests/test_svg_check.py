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

    def test_unknown_encoding_declaration_is_not_well_formed(self):
        # expat raises LookupError, not ExpatError, for an encoding it has
        # no codec for; the contract is that content never raises
        data = (b'<?xml version="1.0" encoding="bogus"?>'
                b'<svg xmlns="http://www.w3.org/2000/svg" width="1" '
                b'height="1"/>')
        r = svg_check.check(data)
        self.assertTrue(r.refusal.startswith("not well-formed: "), r.refusal)
        self.assertEqual(r.problems, [])

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


class TestAnimatedReferences(unittest.TestCase):
    def test_animated_clean_fixtures_pass(self):
        for name in ("smil-clean.svg", "css-clean.svg"):
            self.assertEqual(problems(fixture(name)), [], name)
            self.assertEqual(run_main(str(FIX / name))[0], 0, name)

    def test_dangling_variants_name_their_defect(self):
        path = str(FIX / "smil-dangling.svg")
        code, lines = run_main(path)
        self.assertEqual(code, 1)
        self.assertEqual(
            [ln for ln in lines if "smallest" not in ln and "no text" not in ln],
            [f'svg-check: {path}: dangling timing reference "first" in '
             "animateMotion begin"])
        self.assertEqual(problems(fixture("css-dangling.svg")),
                         ["dangling url(#g) in <style>"])

    def test_timing_items_that_are_not_ids_are_not_read_as_ids(self):
        for begin in ("1.6s; 0s; indefinite", "-1.6s", "0.5s", "2",
                      "00:01.5", "click", "indefinite", "+3s",
                      "accessKey(a)", "10ms", "1.5min"):
            body = f'<circle r="1"><animate begin="{begin}"/></circle>'
            self.assertEqual(problems(wrap(body)), [], begin)

    def test_timing_items_that_are_ids_are_checked(self):
        cases = {
            "gone.end": "gone",
            "gone.begin+1s": "gone",
            "gone.end - 0.5s": "gone",
            "gone.repeat(2)": "gone",
            "gone.click": "gone",
            "1.6s; gone.end": "gone",
            "my-id.end": "my-id",
        }
        for begin, name in cases.items():
            body = f'<circle r="1"><animate end="{begin}"/></circle>'
            self.assertEqual(
                problems(wrap(body)),
                [f'dangling timing reference "{name}" in animate end'],
                begin)
        ok = ('<circle id="d.o-t" r="1"/><circle r="1">'
              '<animate begin="d.o-t.end+1s; x_y"/></circle>')
        self.assertEqual(problems(wrap(ok)), [])
        body = ('<circle id="a" r="1"><animate begin="a.end"/>'
                '<animate begin="a.repeat(3)"/></circle>')
        self.assertEqual(problems(wrap(body)), [])

    def test_mpath_and_use_hrefs_are_checked(self):
        self.assertEqual(problems(wrap(
            '<circle r="1"><animateMotion><mpath href="#gone"/>'
            '</animateMotion></circle>')),
            ['dangling href "#gone" on mpath'])
        self.assertEqual(problems(wrap('<use href="#gone"/>')),
                         ['dangling href "#gone" on use'])

    def test_css_animation_and_keyframe_names_are_not_ids(self):
        css = ('<style>@keyframes spin { from { opacity: 0 } to '
               '{ opacity: 1 } } .a { animation: spin 2s infinite; }'
               '</style><circle class="a" r="1"/>')
        self.assertEqual(problems(wrap(css)), [])


def reading(body, root='width="400" height="200" viewBox="0 0 400 200"',
            embed=830.0):
    return svg_check.check(wrap(body, root), embed)


def main_over(data, *flags):
    """(exit code, lines, path) for main over a temp file holding data."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "x.svg"
        path.write_bytes(data)
        code, lines = run_main(str(path), *flags)
    return code, lines, str(path)


class TestSmallestText(unittest.TestCase):
    # clean.svg: root 1000x500, viewBox 500x250, so at 830px the scale is
    # 830/500 = 1.66 on both axes; its smallest text is the 5px under
    # <g font-size="5"> (the 12px title is larger): 5 x 1.66 = 8.3.
    def test_clean_fixture_prints_the_hand_worked_figure(self):
        path = str(FIX / "clean.svg")
        code, lines = run_main(path)
        self.assertEqual(code, 0)
        self.assertEqual(lines, [
            f"svg-check: {path}: pass — smallest text 8.3px at 830px "
            "embed width"])

    def test_embed_width_option_scales_in_proportion(self):
        # 440 / 500 = 0.88; 5 x 0.88 = 4.4
        path = str(FIX / "clean.svg")
        for flags in (["--embed-width", "440"], ["--embed-width=440"]):
            code, lines = run_main(path, *flags)
            self.assertEqual(code, 0)
            self.assertEqual(lines, [
                f"svg-check: {path}: pass — smallest text 4.4px at 440px "
                "embed width"])

    def test_a_root_narrower_than_the_embed_is_not_scaled_up(self):
        # root 1000 < embed 2000: rendered 1000, scale 1000/500 = 2, 5 x 2
        r = svg_check.check(fixture("clean.svg"), 2000)
        self.assertAlmostEqual(r.smallest_px, 10.0)

    def test_scale_is_the_smaller_axis_when_aspect_ratios_differ(self):
        # root 400x100 over viewBox 400x200: x scale 1, y scale
        # 400 x (100/400) / 200 = 0.5; the smaller wins: 10 x 0.5 = 5
        r = reading('<text font-size="10">a</text>',
                    'width="400" height="100" viewBox="0 0 400 200"')
        self.assertAlmostEqual(r.smallest_px, 5.0)

    def test_no_viewbox_means_user_units_are_px(self):
        r = reading('<text font-size="10">a</text>',
                    'width="400" height="200"', embed=200)
        self.assertAlmostEqual(r.smallest_px, 5.0)

    def test_unusable_scale_leaves_the_number_unset_with_a_reason(self):
        r = reading('<text font-size="10">a</text>',
                    'viewBox="0 0 400 200"')
        self.assertIsNone(r.smallest_px)
        self.assertEqual(r.problems,
                         ["root width missing", "root height missing"])
        self.assertTrue(r.note.startswith("root width and height"))
        r = reading('<text font-size="10">a</text>',
                    'width="400" height="200" viewBox="0 0 0 200"')
        self.assertIsNone(r.smallest_px)
        self.assertTrue(r.note.startswith("viewBox"))
        code, lines, path = main_over(wrap(
            '<text font-size="10">a</text>', 'viewBox="0 0 4 2"'))
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 3)
        self.assertIn("smallest text not read: root width and height",
                      lines[-1])
        self.assertNotIn("px at", lines[-1])

    def test_defects_and_a_readable_size_print_both(self):
        code, lines, path = main_over(wrap(
            '<rect fill="url(#gone)"/><text font-size="10">a</text>'))
        self.assertEqual(code, 1)
        self.assertEqual(lines, [
            f"svg-check: {path}: dangling url(#gone) in rect fill",
            f"svg-check: {path}: smallest text 10px at 830px embed width"])

    def test_no_text(self):
        code, lines, path = main_over(wrap('<rect width="1" height="1"/>'))
        self.assertEqual(code, 0)
        self.assertEqual(lines, [f"svg-check: {path}: pass — no text"])

    def test_unresolved_sizes_are_counted_never_guessed(self):
        for size in ("1.2em", "120%", "var(--s)", "1rem"):
            r = reading(f'<text font-size="{size}">a</text>')
            self.assertIsNone(r.smallest_px, size)
            self.assertEqual(r.unread, 1, size)
        r = reading('<text>no declaration</text>')
        self.assertEqual(r.unread, 1)
        code, lines, path = main_over(wrap('<text font-size="1.2em">a</text>'))
        self.assertEqual(code, 0)
        self.assertEqual(lines, [
            f"svg-check: {path}: pass — smallest text not read: no text size"
            " resolved (1 text elements unread)"])

    def test_resolved_and_unread_text_report_both(self):
        code, lines, path = main_over(wrap(
            '<text font-size="10">a</text><text font-size="1.2em">b</text>'))
        self.assertEqual(lines, [
            f"svg-check: {path}: pass — smallest text 10px at 830px embed "
            "width (1 text elements unread)"])

    def test_complex_selector_rules_are_counted_as_skipped(self):
        code, lines, path = main_over(wrap(
            '<style>g > text { font-size: 7px }</style>'
            '<g><text font-size="10">a</text></g>'))
        self.assertEqual(code, 0)
        self.assertEqual(lines, [
            f"svg-check: {path}: pass — smallest text 10px at 830px embed "
            "width (1 style rules skipped)"])
        r = reading('<style>@media (min-width: 1px) { text '
                    '{ font-size: 3px } }</style><text font-size="10">a'
                    '</text>')
        self.assertEqual(r.skipped_rules, 1)
        self.assertAlmostEqual(r.smallest_px, 10.0)

    def test_counts_are_absent_when_zero(self):
        _, lines, _ = main_over(wrap('<text font-size="10">a</text>'))
        self.assertNotIn("(", lines[0])

    def test_precedence_inline_then_rule_then_attribute(self):
        def px(body, style=""):
            s = f"<style>{style}</style>" if style else ""
            return reading(s + body).smallest_px
        # a class rule beats a tag rule whichever is written later
        self.assertAlmostEqual(px(
            '<text class="c">a</text>',
            ".c{font-size:9px} text{font-size:8px}"), 9)
        # the later of two equal rules wins
        self.assertAlmostEqual(px(
            '<text class="c">a</text>',
            ".c{font-size:9px} .c{font-size:11px}"), 11)
        # tag.class and comma lists
        self.assertAlmostEqual(px(
            '<text class="b">a</text>', "text.b, .zz{font-size:6px}"), 6)
        # unitless CSS value
        self.assertAlmostEqual(px('<text>a</text>',
                                  "text{font-size:9}"), 9)
        # inline style beats a rule, a rule beats the attribute
        self.assertAlmostEqual(px(
            '<text style="font-size:7px;fill:red" font-size="6">a</text>',
            "text{font-size:12px}"), 7)
        self.assertAlmostEqual(px('<text font-size="6">a</text>',
                                  "text{font-size:12px}"), 12)
        self.assertAlmostEqual(px('<text font-size="6">a</text>'), 6)

    def test_ancestors_are_walked_nearest_first(self):
        r = reading('<g font-size="20"><g style="font-size:15px">'
                    '<text>a</text></g></g>')
        self.assertAlmostEqual(r.smallest_px, 15)
        r = reading('<g font-size="20"><g font-size="1.5em">'
                    '<text>a</text></g></g>')
        self.assertIsNone(r.smallest_px)
        self.assertEqual(r.unread, 1)

    def test_tspan_text_is_read_and_a_blank_text_is_not(self):
        r = reading('<text font-size="9"><tspan font-size="4">a</tspan>'
                    '</text><text font-size="1em">   </text>')
        self.assertAlmostEqual(r.smallest_px, 4)
        self.assertEqual(r.unread, 0)


class TestScaffolds(unittest.TestCase):
    """Both diagram skills' scaffolds, read in place, must pass their own
    step-7 check. A scaffold that drifts fails here."""
    SCAFFOLDS = {
        "skills/architecture-diagram/assets/boilerplate.svg": (880, 448),
        "skills/animated-diagram/assets/boilerplate.svg": (880, 392),
    }

    def test_each_scaffold_passes_and_reads_a_smallest_text(self):
        for rel, (w, h) in self.SCAFFOLDS.items():
            r = svg_check.check((ROOT / rel).read_bytes())
            self.assertIsNone(r.refusal, rel)
            self.assertEqual(r.problems, [], rel)
            self.assertIsNotNone(r.smallest_px, f"{rel}: {r.note}")
            self.assertEqual(run_main(str(ROOT / rel))[0], 0, rel)

    def test_root_size_equals_the_viewbox(self):
        import xml.etree.ElementTree as ET
        for rel, (w, h) in self.SCAFFOLDS.items():
            root = ET.parse(ROOT / rel).getroot()
            self.assertEqual(root.get("viewBox"), f"0 0 {w} {h}", rel)
            self.assertEqual((root.get("width"), root.get("height")),
                             (str(w), str(h)), rel)


if __name__ == "__main__":
    unittest.main()
