"""voice_grade.py — the offline house-voice reply grader.

The run is docs/features/house-voice/ (ADR-0119). Every case runs through
the public interface with inline texts or temp files, offline, with exact
strings; nothing here calls a model or the network.
"""
import io
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import voice_grade as vg

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "plugin-evals/house-voice/fixtures"
CASES = ("undo-unpushed-commit", "read-a-traceback", "pick-a-date-library")

# architecture.md's Data model table, in its order.
NAMES = (
    "praise-opener", "throat-clearing", "restated-question", "hedge",
    "closing-recap", "closing-offer", "em-dash", "business-jargon",
    "emphasis-crutch", "filler-adverb", "binary-contrast", "narration",
)
ANCHORED = {"restated-question"}

# One line per pattern that carries it, and the exact text it matches.
EXAMPLES = {
    "praise-opener": ("Great question, and the fix is small.",
                      "Great question"),
    "throat-clearing": ("Here's the thing: the cache is cold.",
                        "Here's the thing"),
    "restated-question": ("You are asking how to undo a commit.",
                          "You are asking"),
    "hedge": ("It is worth noting that the lock is held.",
              "It is worth noting"),
    "closing-recap": ("In summary, run the reset.", "In summary"),
    "closing-offer": ("Hope this helps with the deploy.",
                      "Hope this helps"),
    "em-dash": ("The test fails — the path is wrong.", "—"),
    "business-jargon": ("We can circle back on the schema.",
                        "circle back"),
    "emphasis-crutch": ("Make no mistake, the key leaked.",
                        "Make no mistake"),
    "filler-adverb": ("The bug is honestly in the parser.", "honestly"),
    "binary-contrast": ("It is not just slow but wrong.",
                        "not just slow but"),
    "narration": ("Let me start with the stack trace.", "Let me start"),
}


def scan_count(text):
    """An independent proxy count: one per run of word characters, one
    per other non-space character, by walking the string."""
    count, i = 0, 0
    while i < len(text):
        char = text[i]
        if char.isalnum() or char == "_":
            while i < len(text) and (text[i].isalnum() or text[i] == "_"):
                i += 1
            count += 1
            continue
        if not char.isspace():
            count += 1
        i += 1
    return count


class TestPatterns(unittest.TestCase):
    def test_the_twelve_names_in_order(self):
        self.assertEqual(tuple(n for n, _, _ in vg.SLOP_PATTERNS), NAMES)

    def test_every_pattern_is_case_insensitive(self):
        for name, _, flags in vg.SLOP_PATTERNS:
            self.assertIn("i", flags, name)

    def test_multiline_only_where_the_pattern_anchors_on_a_caret(self):
        for name, pattern, flags in vg.SLOP_PATTERNS:
            self.assertEqual("m" in flags, name in ANCHORED, name)
            anchored = bool(re.search(r"(?:^|\|)\^", pattern))
            self.assertEqual(anchored, name in ANCHORED, name)

    def test_each_example_is_found_with_its_exact_text(self):
        for name, (line, matched) in EXAMPLES.items():
            self.assertIn((name, matched), vg.slop(line), name)

    def test_case_does_not_matter(self):
        self.assertEqual(vg.slop("GREAT QUESTION."),
                         [("praise-opener", "GREAT QUESTION")])

    def test_the_restated_question_anchor_holds_on_any_line(self):
        text = "First line.\nyou want to know why it fails."
        self.assertEqual(vg.slop(text),
                         [("restated-question", "you want to know")])

    def test_the_anchor_does_not_match_mid_line(self):
        self.assertEqual(vg.slop("I think you are asking for less."), [])


class TestSlop(unittest.TestCase):
    def test_clean_text_is_an_empty_list(self):
        self.assertEqual(vg.slop("Run `git reset --soft HEAD~1`."), [])
        self.assertEqual(vg.slop(""), [])

    def test_pattern_order_then_text_order(self):
        text = ("Feel free to ask. Great question. Hope this helps."
                " Good question.")
        self.assertEqual(vg.slop(text), [
            ("praise-opener", "Great question"),
            ("praise-opener", "Good question"),
            ("closing-offer", "Feel free to"),
            ("closing-offer", "Hope this helps"),
        ])

    def test_inline_code_spans_are_skipped(self):
        self.assertEqual(vg.slop("Grep for `great question` in the log."),
                         [])

    def test_fenced_code_blocks_are_skipped(self):
        text = ("Run this:\n\n```\necho 'great question — honestly'\n"
                "```\n\nThen honestly check.")
        self.assertEqual(vg.slop(text), [("filler-adverb", "honestly")])

    def test_tilde_fences_are_skipped(self):
        text = "~~~\nIn summary\n~~~\n"
        self.assertEqual(vg.slop(text), [])

    def test_an_unclosed_fence_skips_to_the_end(self):
        self.assertEqual(vg.slop("Text.\n```\nIn summary\n"), [])

    def test_the_text_after_a_closed_fence_is_graded(self):
        text = "```\ncode\n```\nYou are asking for a reset."
        self.assertEqual(vg.slop(text),
                         [("restated-question", "You are asking")])


class TestCountTokens(unittest.TestCase):
    SAMPLES = (
        "Run the reset, then push again.",
        "def f(x):\n    return x[0] + 1  # first\n",
        "?!... --> ;; ''' — (([]))",
        "snake_case and CamelCase2 words_3",
    )

    def test_empty_is_zero(self):
        self.assertEqual(vg.count_tokens(""), 0)

    def test_a_hand_counted_example(self):
        # Run, the, reset, ",", then, push, again, "."
        self.assertEqual(vg.count_tokens("Run the reset, then push again."),
                         8)

    def test_an_independent_scan_agrees(self):
        for text in self.SAMPLES:
            self.assertEqual(vg.count_tokens(text), scan_count(text), text)


def fixture(*parts):
    return FIXTURES.joinpath(*parts).read_text(encoding="utf-8")


class TestFixtures(unittest.TestCase):
    """The authored replies both scorers rest on, and the PRD's demo,
    offline half: each after reply is shorter and clean."""

    def test_the_readme_says_every_file_is_authored(self):
        text = fixture("README.md")
        self.assertIn("authored", text)
        self.assertIn("not recorded model output", text)

    def test_each_slop_file_names_exactly_its_own_pattern(self):
        for name in NAMES:
            found = {n for n, _ in vg.slop(fixture("slop", f"{name}.md"))}
            self.assertEqual(found, {name}, name)

    def test_the_slop_directory_holds_one_file_per_pattern_and_clean(self):
        held = sorted(p.name for p in (FIXTURES / "slop").iterdir())
        self.assertEqual(held, sorted([f"{n}.md" for n in NAMES]
                                      + ["clean.md"]))

    def test_the_clean_file_is_clean(self):
        self.assertEqual(vg.slop(fixture("slop", "clean.md")), [])

    def test_each_after_reply_is_shorter_than_its_before(self):
        for case in CASES:
            before = vg.count_tokens(fixture(case, "before.md"))
            after = vg.count_tokens(fixture(case, "after.md"))
            self.assertLess(after, before, case)

    def test_each_after_reply_is_clean(self):
        for case in CASES:
            self.assertEqual(vg.slop(fixture(case, "after.md")), [], case)

    def test_each_before_reply_names_a_pattern(self):
        for case in CASES:
            self.assertTrue(vg.slop(fixture(case, "before.md")), case)

    def test_no_fixture_is_named_like_a_harness_case(self):
        names = {p.name for p in FIXTURES.rglob("*")}
        self.assertTrue(names)
        self.assertEqual(names & {"prompt.md", "case.yaml"}, set())


USAGE = "voice-grade: usage: python3 voice_grade.py <reply.md> [<reply.md> ...]"


class TestFrontDoor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def write(self, name, data):
        path = self.dir / name
        if isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_text(data, encoding="utf-8")
        return str(path)

    def run_main(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = vg.main(list(argv))
        return code, out.getvalue().splitlines()

    def test_no_argument_prints_usage_and_exits_two(self):
        self.assertEqual(self.run_main(), (2, [USAGE]))

    def test_a_clean_file_prints_its_count_and_exits_zero(self):
        path = self.write("clean.md", "Run the reset, then push again.")
        self.assertEqual(self.run_main(path), (0, [
            f"voice-grade: {path}: 8 tokens",
            "voice-grade: 0 problem(s)",
        ]))

    def test_slop_prints_each_match_and_exits_one(self):
        clean = self.write("clean.md", "Done.")
        dirty = self.write("dirty.md", "Great question. Hope this helps.")
        self.assertEqual(self.run_main(clean, dirty), (1, [
            f"voice-grade: {clean}: 2 tokens",
            f"voice-grade: {dirty}: 7 tokens",
            f'voice-grade: {dirty}: praise-opener: "Great question"',
            f'voice-grade: {dirty}: closing-offer: "Hope this helps"',
            "voice-grade: 2 problem(s)",
        ]))

    def test_a_match_across_a_line_break_prints_on_one_line(self):
        path = self.write("wrapped.md", "It is not just\nslow but wrong.")
        self.assertEqual(self.run_main(path), (1, [
            f"voice-grade: {path}: 8 tokens",
            f'voice-grade: {path}: binary-contrast: "not just slow but"',
            "voice-grade: 1 problem(s)",
        ]))

    def test_a_missing_file_exits_two_before_any_count(self):
        clean = self.write("clean.md", "Done.")
        missing = str(self.dir / "absent.md")
        self.assertEqual(self.run_main(clean, missing), (2, [
            f"voice-grade: cannot read {missing}: no such file",
        ]))

    def test_a_non_utf8_file_exits_two(self):
        path = self.write("bad.md", b"\xff\xfe")
        self.assertEqual(self.run_main(path), (2, [
            f"voice-grade: cannot read {path}: 'utf-8' codec can't decode"
            " byte 0xff in position 0: invalid start byte",
        ]))


if __name__ == "__main__":
    unittest.main()
