"""The eval-quality research note keeps its required structure.

docs/research/eval-quality-metrics-2026-10-21.md is the dated, sourced
metric set behind eval_trends.py (docs/features/eval-trends/, S16 to
S19). This pins its shape, not its claims: the headings, a failure mode
per metric, and that every metric either cites a source listed under
## Sources with a fetch date or says it is unverified and appears under
## Not verified. What the sources say is the note's to defend.
"""
import re
import unittest
from pathlib import Path

import eval_trends

REPO = Path(__file__).resolve().parent.parent
NOTE = REPO / eval_trends.NOTE
METRICS = ("Pass rate with a confidence interval", "Flake rate",
           "Saturation", "Judge agreement and drift", "Contamination",
           "Cost per point")
HEADINGS = ("## Metrics and failure modes",
            "## What n justifies a trend claim", "## Sources",
            "## Not verified")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
TAG = re.compile(r"\[(S\d+)\]")


def sections(text, level):
    """{heading: body} for the headings of exactly `level` hashes."""
    pattern = re.compile(rf"^{'#' * level} (.+)$", re.M)
    found = list(pattern.finditer(text))
    out = {}
    for i, match in enumerate(found):
        end = found[i + 1].start() if i + 1 < len(found) else len(text)
        out[match[1].strip()] = text[match.end():end]
    return out


def read():
    return NOTE.read_text(encoding="utf-8") if NOTE.is_file() else ""


class TestNoteStructure(unittest.TestCase):
    def test_the_note_exists_at_the_path_the_tool_names(self):
        self.assertTrue(NOTE.is_file(), f"{NOTE} is missing")

    def test_the_first_paragraph_is_dated(self):
        text = read()
        paragraphs = [p for p in text.split("\n\n")
                      if p.strip() and not p.lstrip().startswith("#")]
        self.assertTrue(paragraphs and DATE.search(paragraphs[0]),
                        "the first paragraph carries no date")

    def test_the_required_headings_are_present(self):
        text = read()
        for heading in HEADINGS:
            with self.subTest(heading=heading):
                self.assertRegex(text, rf"(?m)^{re.escape(heading)}\s*$")

    def test_a_metric_subsection_names_its_failure_mode(self):
        top = sections(read(), 2).get("Metrics and failure modes", "")
        subs = sections(top, 3)
        for metric in METRICS:
            with self.subTest(metric=metric):
                body = next((b for h, b in subs.items()
                             if h.lower().startswith(metric.lower())), None)
                self.assertIsNotNone(body, f"no subsection for {metric}")
                self.assertIn("failure mode", body.lower())

    def test_every_metric_cites_a_dated_source_or_is_marked_unverified(self):
        text = read()
        top = sections(text, 2)
        subs = sections(top.get("Metrics and failure modes", ""), 3)
        sources = top.get("Sources", "")
        listed = {}
        for item in re.split(r"(?m)^- (?=\[S\d+\])", sources)[1:]:
            tag = TAG.search(item)  # an item may wrap over several lines
            listed[tag[1]] = " ".join(item.split())
        for tag, line in listed.items():
            with self.subTest(source=tag):
                self.assertRegex(line, r"fetched \d{4}-\d{2}-\d{2}")
        unverified = top.get("Not verified", "").lower()
        for heading, body in subs.items():
            with self.subTest(metric=heading):
                cited = set(TAG.findall(body)) & set(listed)
                if cited:
                    continue
                self.assertIn("not verified", body.lower(),
                              "cites no listed source and is not marked")
                self.assertIn(heading.lower()[:20], unverified)

    def test_the_note_says_fetched_material_was_treated_as_data(self):
        self.assertRegex(read().lower(), r"untrusted data")


if __name__ == "__main__":
    unittest.main()
