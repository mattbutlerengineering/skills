"""decompose_lessons.py — the Decompose lessons file (issue #988).

The run is docs/features/decompose-lessons/ (ADR-0113). Every case runs
through the public interface with a fixture record list, a temp dir and
an injected git runner; no lesson is hand-written in the repo, so every
lesson here is a fixture built by the helpers below.
"""
import copy
import unittest

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


if __name__ == "__main__":
    unittest.main()
