"""decompose_lessons.py — the Decompose lessons file (issue #988).

The run is docs/features/decompose-lessons/ (ADR-0113). Every case runs
through the public interface with a fixture record list, a temp dir and
an injected git runner; no lesson is hand-written in the repo, so every
lesson here is a fixture built by the helpers below.
"""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import decompose_lessons as dl

SRC_A = "feature:alpha"
SRC_B = "feature:beta"


def lesson(lid="replan/feature/added", importance=2, sources=(SRC_A,),
           voted=(), text="a fixture lesson"):
    return {"id": lid, "importance": importance, "text": text,
            "sources": list(sources), "voted": list(voted)}


class TestLessonOperations(unittest.TestCase):
    def test_add_with_no_source_run_is_refused_and_returns_the_original(self):
        original = [lesson("x/feature/a")]
        frozen = copy.deepcopy(original)
        result, problems = dl.add(original, "x/feature/b", "t", [])
        self.assertIs(result, original)
        self.assertEqual(
            problems,
            ["decompose-lessons: add refused: x/feature/b cites no source"
             " run"])
        self.assertEqual(original, frozen)

    def test_add_returns_a_new_list_at_importance_two(self):
        original = [lesson("x/feature/a")]
        frozen = copy.deepcopy(original)
        result, problems = dl.add(original, "x/feature/b", "why",
                                  [SRC_A, SRC_B])
        self.assertEqual(problems, [])
        self.assertEqual(original, frozen)
        self.assertEqual(result, original + [
            {"id": "x/feature/b", "importance": 2, "text": "why",
             "sources": [SRC_A, SRC_B], "voted": []}])

    def test_add_of_an_existing_id_is_refused(self):
        original = [lesson("x/feature/a")]
        result, problems = dl.add(original, "x/feature/a", "t", [SRC_B])
        self.assertIs(result, original)
        self.assertEqual(
            problems,
            ["decompose-lessons: add refused: x/feature/a already exists"])

    def test_upvote_takes_two_to_three_and_keeps_the_sources(self):
        original = [lesson(sources=(SRC_A, SRC_B))]
        frozen = copy.deepcopy(original)
        result, problems = dl.upvote(original, "replan/feature/added",
                                     "feature:gamma")
        self.assertEqual(problems, [])
        self.assertEqual(original, frozen)
        self.assertEqual(result[0]["importance"], 3)
        self.assertEqual(result[0]["sources"], [SRC_A, SRC_B])
        self.assertEqual(result[0]["voted"], ["feature:gamma"])

    def test_downvote_takes_two_to_one_and_keeps_the_sources(self):
        original = [lesson()]
        result, problems = dl.downvote(original, "replan/feature/added",
                                       "feature:gamma")
        self.assertEqual(problems, [])
        self.assertEqual(result[0]["importance"], 1)
        self.assertEqual(result[0]["sources"], [SRC_A])
        self.assertEqual(result[0]["voted"], ["feature:gamma"])

    def test_downvote_from_one_removes_the_lesson(self):
        original = [lesson("a/feature/x"), lesson("b/feature/y", 1)]
        frozen = copy.deepcopy(original)
        result, problems = dl.downvote(original, "b/feature/y", "feature:g")
        self.assertEqual(problems, [])
        self.assertEqual(original, frozen)
        self.assertEqual([entry["id"] for entry in result], ["a/feature/x"])

    def test_a_lesson_at_one_left_alone_remains(self):
        original = [lesson(importance=1)]
        result, _ = dl.upvote(original, "replan/feature/added", "feature:g")
        self.assertEqual(result[0]["importance"], 2)
        self.assertTrue(all(entry["importance"] >= 1 for entry in result))

    def test_a_vote_or_edit_on_an_unknown_id_creates_nothing(self):
        original = [lesson()]
        for op, call in (("upvote", lambda: dl.upvote(original, "no/id",
                                                       "feature:g")),
                         ("downvote", lambda: dl.downvote(original, "no/id",
                                                           "feature:g")),
                         ("edit", lambda: dl.edit(original, "no/id", "t"))):
            with self.subTest(op=op):
                result, problems = call()
                self.assertIs(result, original)
                self.assertEqual(
                    problems,
                    [f"decompose-lessons: {op} refused: no lesson no/id"])

    def test_edit_changes_text_and_keeps_importance_sources_and_voted(self):
        original = [lesson(importance=3, sources=(SRC_A, SRC_B),
                           voted=("feature:g",))]
        frozen = copy.deepcopy(original)
        result, problems = dl.edit(original, "replan/feature/added", "new")
        self.assertEqual(problems, [])
        self.assertEqual(original, frozen)
        self.assertEqual(result, [lesson(
            importance=3, sources=(SRC_A, SRC_B), voted=("feature:g",),
            text="new")])

    def test_edit_may_replace_the_sources(self):
        result, problems = dl.edit([lesson()], "replan/feature/added", "t",
                                   [SRC_A, SRC_B])
        self.assertEqual(problems, [])
        self.assertEqual(result[0]["sources"], [SRC_A, SRC_B])

    def test_an_edit_that_leaves_no_source_run_is_refused(self):
        original = [lesson()]
        result, problems = dl.edit(original, "replan/feature/added", "t", [])
        self.assertIs(result, original)
        self.assertEqual(
            problems,
            ["decompose-lessons: edit refused: replan/feature/added cites"
             " no source run"])


def jsonl(seen, *lessons):
    """The file text the module writes: header, then one line per lesson."""
    lines = [json.dumps({"seen": seen}, ensure_ascii=False)]
    lines += [json.dumps(entry, ensure_ascii=False) for entry in lessons]
    return "\n".join(lines) + "\n"


class TempFile(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        self.path = self.dir / "lessons.jsonl"


class TestFile(TempFile):
    def test_a_file_round_trips_byte_identically(self):
        text = jsonl(["feature:a", "feature:b"],
                     lesson("a/feature/x", text="em dash \u2014 kept"),
                     lesson("b/feature/y", 3, (SRC_A, SRC_B), ("feature:c",)))
        self.path.write_text(text, encoding="utf-8")
        lessons, seen, problems = dl.load(self.path)
        self.assertEqual(problems, [])
        self.assertEqual(seen, ["feature:a", "feature:b"])
        self.assertEqual([entry["id"] for entry in lessons],
                         ["a/feature/x", "b/feature/y"])
        self.assertEqual(dl.dump(self.path, lessons, seen), [])
        self.assertEqual(self.path.read_text(encoding="utf-8"), text)

    def test_dump_sorts_lessons_by_id_and_seen(self):
        problems = dl.dump(self.path, [lesson("b/feature/y"),
                                       lesson("a/feature/x")],
                           ["feature:b", "feature:a"])
        self.assertEqual(problems, [])
        self.assertEqual(
            self.path.read_text(encoding="utf-8"),
            jsonl(["feature:a", "feature:b"], lesson("a/feature/x"),
                  lesson("b/feature/y")))

    def test_a_missing_file_loads_as_nothing(self):
        self.assertEqual(dl.load(self.path), ([], [], []))

    def test_each_malformed_shape_names_its_line_and_loads_nothing(self):
        header = json.dumps({"seen": []})
        good = json.dumps(lesson("a/feature/x"))
        cases = {
            "not json": ([header, "{oops"],
                         "lessons.jsonl line 2: not valid JSON"),
            "not an object": ([header, "[1]"],
                              "lessons.jsonl line 2: not a JSON object"),
            "no sources": ([header, json.dumps(lesson(sources=()))],
                           "lessons.jsonl line 2: cites no source run"),
            "duplicate id": ([header, good, good],
                             "lessons.jsonl line 3: duplicate id"
                             " a/feature/x"),
            "importance": ([header, json.dumps(lesson("a/feature/x", 0))],
                           "lessons.jsonl line 2: importance 0 is below 1"),
            "no header": ([good],
                          "lessons.jsonl line 1: expected the seen header"),
            "missing field": ([header, json.dumps({"id": "a/feature/x"})],
                              "lessons.jsonl line 2: missing or malformed"
                              " field importance"),
        }
        for name, (lines, expected) in cases.items():
            with self.subTest(name):
                self.path.write_text("\n".join(lines) + "\n")
                self.assertEqual(
                    dl.load(self.path),
                    ([], [], [f"decompose-lessons: {expected}"]))

    def test_dump_refuses_an_invalid_lesson_and_writes_nothing(self):
        problems = dl.dump(self.path, [lesson(sources=())], [])
        self.assertEqual(
            problems,
            ["decompose-lessons: lessons.jsonl line 2: cites no source run"])
        self.assertFalse(self.path.exists())

    def test_a_failing_replace_leaves_the_original_byte_identical(self):
        text = jsonl(["feature:a"], lesson())
        self.path.write_text(text, encoding="utf-8")
        with mock.patch.object(dl.os, "replace",
                               side_effect=OSError("disk full")):
            problems = dl.dump(self.path, [lesson("b/feature/y")], [])
        self.assertEqual(
            problems,
            ["decompose-lessons: cannot write lessons.jsonl: disk full"])
        self.assertEqual(self.path.read_text(encoding="utf-8"), text)
        self.assertEqual(os.listdir(self.dir), ["lessons.jsonl"])

    def test_an_empty_write_creates_no_file(self):
        self.assertEqual(dl.dump(self.path, [], []), [])
        self.assertEqual(os.listdir(self.dir), [])


UNMEASURABLE = {"unmeasurable": "fixture"}


def replan(count, items, label, added=0, dropped=0, split=0, merged=0):
    return {"label": label, "count": count, "items_at_d": items,
            "added": added, "dropped": dropped, "split": split,
            "merged": merged, "renamed": 0}


def record(run, rp=UNMEASURABLE, gaps=UNMEASURABLE, review=UNMEASURABLE,
           decompose="observed", **extra):
    return {"run": run, "path": f"docs/{run}",
            "decompose": {"sha": "d" * 40, "label": decompose},
            "implement": {"sha": "i" * 40, "label": decompose},
            "replan": rp, "design_gaps": gaps, "review": review, **extra}


NO_HEADING = {"findings": 0, "reason": "no finding heading"}
# Worked by hand: kind and label decide who may be a clean run; the first
# clean run in list order is the exemplar.
HISTORY = [
    record("feature:0"),
    record("feature:a", replan(2, 10, "observed", added=2),
           {"label": "observed", "routes": 1, "source": "subjects"},
           {"label": "observed", "findings": 4, "named": 3},
           band_miss="S took M", retro="we should plan better"),
    record("feature:b", replan(0, 8, "observed"),
           {"label": "observed", "routes": 0, "source": "subjects"},
           NO_HEADING),
    record("feature:c", replan(4, 8, "inferred", added=1, dropped=3)),
    record("feature:d", replan(0, 14, "inferred")),
    record("feature:e", replan(1, 6, "observed", added=1)),
    record("maintenance:m", replan(6, 7, "inferred", dropped=6)),
    record("maintenance:n", replan(0, 5, "inferred")),
    record("maintenance:z", replan(4, 9, "observed", dropped=2, split=2)),
]


def pair(signal, kind, detail, hit, clean, text):
    return {"signal": signal, "kind": kind, "detail": detail, "hit": hit,
            "clean": clean, "text": text}


HAND_PAIRS = [
    pair("replan", "feature", "added", "feature:a", "feature:b",
         "feature runs that re-planned mostly by adding rows: a 2 of 10"
         " items (observed), b 0 of 8 items (observed)"),
    pair("replan", "feature", "dropped", "feature:c", "feature:d",
         "feature runs that re-planned mostly by dropping rows: c 4 of 8"
         " items (inferred), d 0 of 14 items (inferred)"),
    pair("replan", "feature", "added", "feature:e", "feature:b",
         "feature runs that re-planned mostly by adding rows: e 1 of 6"
         " items (observed), b 0 of 8 items (observed)"),
    pair("replan", "maintenance", "dropped", "maintenance:m",
         "maintenance:n",
         "maintenance runs that re-planned mostly by dropping rows: m 6 of"
         " 7 items (inferred), n 0 of 5 items (inferred)"),
    pair("design_gaps", "feature", "routed", "feature:a", "feature:b",
         "feature runs routed back to Architect: a 1 route(s) (observed),"
         " b 0 route(s) (observed)"),
    pair("review", "feature", "named", "feature:a", "feature:b",
         "feature runs whose review findings name an item: a 3 of 4"
         " findings (observed), b 0 of 0 findings (observed)"),
]


class TestPairs(unittest.TestCase):
    def test_pairs_match_the_hand_worked_history(self):
        self.assertEqual(dl.pairs(HISTORY), HAND_PAIRS)

    def test_a_hit_run_with_no_clean_run_of_its_kind_and_label_has_no_pair(
            self):
        hits = {p["hit"] for p in dl.pairs(HISTORY)}
        self.assertNotIn("maintenance:z", hits)

    def test_an_unmeasurable_run_is_never_hit_or_clean(self):
        used = {p["hit"] for p in dl.pairs(HISTORY)} | {
            p["clean"] for p in dl.pairs(HISTORY)}
        self.assertNotIn("feature:0", used)

    def test_band_misses_and_retro_notes_reach_no_pair_or_lesson(self):
        text = repr(dl.pairs(HISTORY)) + repr(dl.candidates(
            dl.pairs(HISTORY)))
        self.assertNotIn("S took M", text)
        self.assertNotIn("plan better", text)

    def test_the_detail_ties_break_in_added_dropped_split_merged_order(self):
        tie = [record("feature:x", replan(4, 9, "observed", dropped=2,
                                          split=2)),
               record("feature:y", replan(0, 9, "observed"))]
        self.assertEqual(dl.pairs(tie)[0]["detail"], "dropped")
        tie = [record("feature:x", replan(4, 9, "observed", split=2,
                                          merged=2)),
               record("feature:y", replan(0, 9, "observed"))]
        self.assertEqual(dl.pairs(tie)[0]["detail"], "split")

    def test_skipped_hit_runs_make_no_pair_but_may_still_be_clean(self):
        got = dl.pairs(HISTORY, skip={"feature:a", "feature:c"})
        self.assertEqual([p["hit"] for p in got],
                         ["feature:e", "maintenance:m"])

    def test_two_pairs_with_one_id_collapse_to_one_lesson_with_both_sources(
            self):
        self.assertEqual(dl.candidates(dl.pairs(HISTORY)), [
            {"id": "design_gaps/feature/routed",
             "text": HAND_PAIRS[4]["text"],
             "sources": ["feature:a", "feature:b"]},
            {"id": "replan/feature/added", "text": HAND_PAIRS[0]["text"],
             "sources": ["feature:a", "feature:b", "feature:e"]},
            {"id": "replan/feature/dropped", "text": HAND_PAIRS[1]["text"],
             "sources": ["feature:c", "feature:d"]},
            {"id": "replan/maintenance/dropped",
             "text": HAND_PAIRS[3]["text"],
             "sources": ["maintenance:m", "maintenance:n"]},
            {"id": "review/feature/named", "text": HAND_PAIRS[5]["text"],
             "sources": ["feature:a", "feature:b"]},
        ])

    def test_a_history_with_no_pair_is_empty_and_has_the_string(self):
        lone = [record("feature:a", replan(2, 10, "observed", added=2))]
        self.assertEqual(dl.pairs(lone), [])
        self.assertEqual(dl.candidates([]), [])
        self.assertEqual(
            dl.NO_PAIR, "decompose-lessons: no contrast pair found \u2014 no"
            " lesson derived")


if __name__ == "__main__":
    unittest.main()
