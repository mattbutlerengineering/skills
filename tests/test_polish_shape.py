"""Pin the countable shape of polish's named blockers and code patterns.

SKILL.md step 5 names eight blockers beside the six-item accessibility
floor; moves.md's inspect move carries a table of 10 to 15 code patterns
whose accessibility rows each carry a WCAG 2.2 id. The pin checks
presence and form. It cannot check that an id is true: that is the
reading of the WCAG 2.2 text recorded in the run's evidence.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills/polish/SKILL.md"
MOVES = ROOT / "skills/polish/references/moves.md"

LEAD = "high severity on sight"
FLOOR = ["contrast", "focus", "keyboard", "labelled", "reduced-motion",
         "targets big enough"]
# one distinct anchor phrase per added blocker, in the file's spelling
ANCHORS = [("320", "200%"), ("colour alone",), ("confirm or undo",),
           ("truncat",), ("scroll edge",), ("recovery",),
           ("semantic colour",), ("motion alone",)]
ID = re.compile(r"^\d\.\d\.\d+(?:[;,] ?\d\.\d\.\d+)*$")


def _section(text, start_re, end_re):
    """The text from the heading matching start_re to the next end_re."""
    m = re.search(start_re, text, re.M)
    if not m:
        return None
    rest = text[m.end():]
    n = re.search(end_re, rest, re.M)
    return rest[:n.start()] if n else rest


def polish_shape_problems(skill_text, moves_text):
    problems = []
    step5 = _section(skill_text, r"^### 5\..*$", r"^### ")
    if step5 is None:
        problems.append("polish: SKILL.md has no '### 5.' section")
    else:
        for phrase in FLOOR:
            if phrase not in step5:
                problems.append(
                    f"polish: SKILL.md step 5 does not name '{phrase}'")
        lines = step5.splitlines()
        lead = next((i for i, ln in enumerate(lines) if LEAD in ln), None)
        if lead is None:
            problems.append(
                f"polish: SKILL.md step 5 has no lead line saying '{LEAD}'")
        else:
            items = []
            for ln in lines[lead + 1:]:
                if re.match(r"^\s+- ", ln):
                    items.append(ln)
                elif ln.strip() and not items:
                    continue
                elif ln.strip() and not re.match(r"^\s+\S", ln):
                    break
            if len(items) != 8:
                problems.append(f"polish: SKILL.md step 5 names {len(items)} "
                                "added blockers, expected 8")
            joined = "\n".join(items).lower()
            for anchor in ANCHORS:
                if not all(a in joined for a in anchor):
                    problems.append("polish: SKILL.md step 5 blocker list "
                                    f"lacks '{' and '.join(anchor)}'")

    inspect = _section(moves_text, r"^## inspect\b.*$", r"^## ")
    if inspect is None:
        problems.append("polish: moves.md has no '## inspect' section")
        return problems
    rows = []
    in_table = False
    for ln in inspect.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if not ln.lstrip().startswith("|"):
            if in_table:
                break
            continue
        if not in_table:
            in_table = cells[0] == "Pattern"
            continue
        if set(ln) <= set("|- :"):
            continue
        rows.append(cells)
    if not in_table:
        problems.append("polish: moves.md inspect has no pattern table")
        return problems
    if not 10 <= len(rows) <= 15:
        problems.append(f"polish: moves.md inspect pattern table has "
                        f"{len(rows)} rows, expected 10 to 15")
    for cells in rows:
        wcag = cells[2] if len(cells) > 2 else ""
        if not (wcag in ("—", "unverified") or ID.match(wcag)):
            problems.append(f"polish: moves.md pattern row '{cells[0]}' "
                            "has no WCAG id")
    return problems


def _mutate(text, old, new):
    assert old in text, old
    return text.replace(old, new, 1)


class PolishShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.moves = MOVES.read_text(encoding="utf-8")

    def problems(self, skill=None, moves=None):
        return polish_shape_problems(skill or self.skill, moves or self.moves)

    def test_real_files_hold_the_shape(self):
        self.assertEqual(self.problems(), [])

    def test_seven_added_blockers(self):
        lines = self.skill.splitlines(keepends=True)
        i = next(i for i, ln in enumerate(lines) if "motion alone" in ln)
        skill = "".join(lines[:i] + lines[i + 1:])
        self.assertEqual(self.problems(skill=skill), [
            "polish: SKILL.md step 5 names 7 added blockers, expected 8",
            "polish: SKILL.md step 5 blocker list lacks 'motion alone'"])

    def test_floor_phrase_missing(self):
        skill = _mutate(self.skill, "a\n  reduced-motion path", "a\n  calm path")
        self.assertEqual(self.problems(skill=skill), [
            "polish: SKILL.md step 5 does not name 'reduced-motion'"])

    def test_missing_step_five(self):
        skill = _mutate(self.skill, "### 5.", "### Five.")
        self.assertEqual(self.problems(skill=skill),
                         ["polish: SKILL.md has no '### 5.' section"])

    def test_missing_inspect_section(self):
        moves = _mutate(self.moves, "## inspect", "## examine")
        self.assertEqual(self.problems(moves=moves),
                         ["polish: moves.md has no '## inspect' section"])

    def test_missing_table(self):
        moves = _mutate(self.moves, "| Pattern |", "| Shape |")
        self.assertEqual(self.problems(moves=moves),
                         ["polish: moves.md inspect has no pattern table"])

    def _table_rows(self):
        return [ln for ln in self.moves.splitlines()
                if ln.startswith("|") and not ln.startswith("| Pattern")
                and not set(ln) <= set("|- :")
                and ln in _section(self.moves, r"^## inspect\b.*$",
                                   r"^## ")]

    def test_nine_rows(self):
        rows = self._table_rows()
        moves = self.moves
        for ln in rows[:len(rows) - 9]:
            moves = moves.replace(ln + "\n", "", 1)
        self.assertEqual(self.problems(moves=moves), [
            "polish: moves.md inspect pattern table has 9 rows, "
            "expected 10 to 15"])

    def test_sixteen_rows(self):
        rows = self._table_rows()
        moves = self.moves.replace(
            rows[-1] + "\n", "".join(rows[-1] + "\n" for _ in range(
                16 - len(rows) + 1)), 1)
        self.assertEqual(self.problems(moves=moves), [
            "polish: moves.md inspect pattern table has 16 rows, "
            "expected 10 to 15"])

    def test_blank_wcag_cell(self):
        row = next(r for r in self._table_rows()
                   if re.search(r"\| \d\.\d\.\d+", r))
        cells = row.strip().strip("|").split("|")
        cells[2] = " "
        moves = self.moves.replace(row, "|" + "|".join(cells) + "|", 1)
        self.assertEqual(self.problems(moves=moves), [
            f"polish: moves.md pattern row '{cells[0].strip()}' "
            "has no WCAG id"])


if __name__ == "__main__":
    unittest.main()
