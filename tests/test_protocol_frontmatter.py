"""Frontmatter seam: protocol.read_frontmatter is the one parser
(ADR-0021) behind lint, orientation, and the trigger-eval runner.

Pins the documented contract (None for no block, {} for an empty block,
key: value pairs) plus the two well-formed inputs the line-splitting
parser used to get wrong: `|` literal block scalars and CRLF line endings.
Also pins the skill-file contract (ADR-0052): skill_path is the one
place the skills/<slug>/SKILL.md shape lives, and
skill_frontmatter_problems is the single frontmatter error contract
behind lint's skill checker and the trigger-eval loader — exact strings,
since lint prints them verbatim.
"""
import ast
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT / "tests"))

from frontmatter_shapes import SHAPES  # noqa: E402
from protocol import (SKILL_DESCRIPTION_LIMIT, frontmatter_end,  # noqa: E402
                      parse_frontmatter, read_frontmatter,
                      skill_frontmatter_problems,
                      skill_path)


def write(text):
    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8", newline="")
    handle.write(text)
    handle.close()
    return Path(handle.name)


class TestExistingContract(unittest.TestCase):
    def test_simple_key_values(self):
        path = write("---\nname: idea\ndescription: d\n---\n\nbody\n")
        self.assertEqual(read_frontmatter(path),
                         {"name": "idea", "description": "d"})

    def test_no_block_returns_none(self):
        self.assertIsNone(read_frontmatter(write("body only\n")))

    def test_fieldless_block_returns_empty_dict(self):
        self.assertEqual(read_frontmatter(write("---\n\n---\n\nbody\n")), {})


class TestBlockScalars(unittest.TestCase):
    def test_literal_block_scalar_joins_indented_lines(self):
        path = write("---\n"
                     "name: idea\n"
                     "description: |\n"
                     "  first line\n"
                     "  second line\n"
                     "---\n\nbody\n")
        self.assertEqual(read_frontmatter(path)["description"],
                         "first line\nsecond line")

    def test_key_after_block_scalar_still_parses(self):
        path = write("---\n"
                     "description: |\n"
                     "  multi\n"
                     "name: idea\n"
                     "---\n\nbody\n")
        self.assertEqual(read_frontmatter(path),
                         {"description": "multi", "name": "idea"})


class TestLineEndings(unittest.TestCase):
    def test_crlf_file_parses_like_lf(self):
        path = write("---\r\nname: idea\r\ndescription: d\r\n---\r\n\r\nbody\r\n")
        self.assertEqual(read_frontmatter(path),
                         {"name": "idea", "description": "d"})


class TestFrontmatterEnd(unittest.TestCase):
    """The one answer to where frontmatter ends (ADR-0118), over the
    shared shape table, from lines split with or without their ends."""

    def test_every_shape_from_bare_and_kept_line_ends(self):
        for name, text, end in SHAPES:
            with self.subTest(shape=name):
                self.assertEqual(frontmatter_end(text.splitlines()), end)
                self.assertEqual(
                    frontmatter_end(text.splitlines(keepends=True)), end)


class TestParseFrontmatterAgreesWithTheOwner(unittest.TestCase):
    """parse_frontmatter reads the block frontmatter_end bounds, so it is
    None exactly when there is no end, and otherwise parses lines[1:end]
    (ADR-0118)."""

    def test_every_shape(self):
        for name, text, end in SHAPES:
            with self.subTest(shape=name):
                if end is None:
                    self.assertIsNone(parse_frontmatter(text))
                    continue
                block = text.splitlines()[1:end]
                expected = ({"status": "ok"} if "status: ok" in block
                            else {})
                self.assertEqual(parse_frontmatter(text), expected)


class TestSkillPath(unittest.TestCase):
    """The one place the skills/<slug>/SKILL.md shape lives (ADR-0052)."""

    def test_shape_under_a_plugin_root(self):
        self.assertEqual(skill_path(Path("/repo"), "idea"),
                         Path("/repo/skills/idea/SKILL.md"))

    def test_accepts_a_string_root(self):
        self.assertEqual(skill_path("/repo", "next"),
                         Path("/repo/skills/next/SKILL.md"))


class TestSkillFrontmatterProblems(unittest.TestCase):
    """One frontmatter error contract for lint and the trigger-eval
    loader (ADR-0052). Before it, trigger-eval skipped the Pi
    description limit lint enforces — an overlong description passed
    eval but failed lint."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="skill-fm-"))
        self.addCleanup(shutil.rmtree, self.root)

    def seed(self, slug, text):
        skill_dir = self.root / "skills" / slug
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")

    def test_conformant_skill_yields_no_problems(self):
        self.seed("idea", "---\nname: idea\ndescription: d\n---\n\nbody\n")
        self.assertEqual(skill_frontmatter_problems(self.root, "idea"), [])

    def test_missing_file(self):
        self.assertEqual(skill_frontmatter_problems(self.root, "idea"),
                         ["missing skills/idea/SKILL.md"])

    def test_no_frontmatter_block(self):
        self.seed("idea", "body only\n")
        self.assertEqual(skill_frontmatter_problems(self.root, "idea"),
                         ["skills/idea/SKILL.md has no frontmatter block"])

    def test_name_mismatch_and_missing_description_both_surface(self):
        self.seed("idea", "---\nname: notidea\n---\n\nbody\n")
        self.assertEqual(
            skill_frontmatter_problems(self.root, "idea"),
            ["skills/idea/SKILL.md frontmatter name is 'notidea', "
             "expected 'idea'",
             "skills/idea/SKILL.md frontmatter has no description"])

    def test_description_over_the_pi_limit(self):
        self.assertEqual(SKILL_DESCRIPTION_LIMIT, 1024)
        overlong = "x" * (SKILL_DESCRIPTION_LIMIT + 1)
        self.seed("idea",
                  f"---\nname: idea\ndescription: {overlong}\n---\n\nbody\n")
        self.assertEqual(
            skill_frontmatter_problems(self.root, "idea"),
            ["skills/idea/SKILL.md description exceeds Pi's "
             "1024-char limit"])

    # Bare-scalar rule (PRD-0007): the value read_frontmatter's plain
    # `key: value` split hands back must be the value a strict YAML
    # loader would read. Three shapes, one exact string each, in the
    # fixed order contains-': ', contains-' #', starts-with. Pocock's
    # v1.3.1 lost six skills to the first shape; this repo had six too.

    def test_description_containing_colon_space(self):
        self.seed("idea", "---\nname: idea\n"
                  "description: Read-only: it proposes and hands off\n"
                  "---\n\nbody\n")
        self.assertEqual(
            skill_frontmatter_problems(self.root, "idea"),
            ["skills/idea/SKILL.md description is not a bare YAML scalar:"
             " contains ': '"])

    def test_description_containing_space_hash(self):
        self.seed("idea", "---\nname: idea\n"
                  "description: Use when closing #12 or #34\n"
                  "---\n\nbody\n")
        self.assertEqual(
            skill_frontmatter_problems(self.root, "idea"),
            ["skills/idea/SKILL.md description is not a bare YAML scalar:"
             " contains ' #'"])

    def test_description_with_both_substrings_yields_both_in_order(self):
        self.seed("idea", "---\nname: idea\n"
                  "description: Read-only: it never closes #12\n"
                  "---\n\nbody\n")
        self.assertEqual(
            skill_frontmatter_problems(self.root, "idea"),
            ["skills/idea/SKILL.md description is not a bare YAML scalar:"
             " contains ': '",
             "skills/idea/SKILL.md description is not a bare YAML scalar:"
             " contains ' #'"])

    def test_double_quoted_description_is_rejected(self):
        # Quoting is not the fix: read_frontmatter is a plain splitter
        # and does not strip quotes, so the quotes would ship to the
        # harness as part of the description. The first character is
        # rendered with !r, so '"' here.
        self.seed("idea", "---\nname: idea\n"
                  'description: "Use when the ask is quoted"\n'
                  "---\n\nbody\n")
        self.assertEqual(
            skill_frontmatter_problems(self.root, "idea"),
            ["skills/idea/SKILL.md description is not a bare YAML scalar:"
             " starts with '\"'"])

    def test_description_starting_with_other_yaml_indicators(self):
        cases = (("brack", "[flow] sequence start", "'['"),
                 ("pipe", "|not a block scalar", "'|'"),
                 ("squote", "'single quoted'", "\"'\""))
        for slug, description, rendered in cases:
            with self.subTest(indicator=description[0]):
                self.seed(slug, f"---\nname: {slug}\n"
                          f"description: {description}\n---\n\nbody\n")
                self.assertEqual(
                    skill_frontmatter_problems(self.root, slug),
                    [f"skills/{slug}/SKILL.md description is not a bare"
                     f" YAML scalar: starts with {rendered}"])

    def test_clean_description_with_bare_colon_and_hash_passes(self):
        # A colon not followed by a space and a hash not preceded by one
        # are fine YAML plain scalars; only the two-char forms end one.
        self.seed("idea", "---\nname: idea\n"
                  "description: Use on wo:ready-for-agent rows (ADR-0033);"
                  " see docs/pipeline-protocol.md#gates.\n---\n\nbody\n")
        self.assertEqual(skill_frontmatter_problems(self.root, "idea"), [])

    def test_missing_description_skips_the_scalar_checks(self):
        self.seed("idea", "---\nname: idea\n---\n\nbody\n")
        self.assertEqual(
            skill_frontmatter_problems(self.root, "idea"),
            ["skills/idea/SKILL.md frontmatter has no description"])


# The fence-definition detector (ADR-0118). A string constant counts as a
# frontmatter fence definition when it is
#   - the pattern of an re.* call that finds "---" but not "--" (so a
#     dash-run rule such as gates.SETEXT_UNDERLINE, which takes "--" too,
#     is not a fence), or
#   - a constant that strips to "---" handed to a method call (the
#     startswith("---\n") / find("\n---\n") form) or standing on either
#     side of ==, !=, in or not in (the strip() == "---" form), alone or
#     inside a tuple, list or set literal there.
# String bodies that merely contain a fence (writers, fixtures, the
# charter_replay "--- YOUR CHARTER ---" delimiters) are none of these.
_REGEX_CALLS = frozenset({"compile", "match", "fullmatch", "search", "sub",
                          "subn", "split", "findall", "finditer"})
_COMPARISONS = (ast.Eq, ast.NotEq, ast.In, ast.NotIn)
# A fence line alone, inside text, and as a whole block (the old
# protocol._FRONTMATTER shape, a block regex that needs both fences).
_FENCE_PROBES = ("---", "\n---\n", "---\nx\n---\n")


def _is_fence_regex(pattern):
    try:
        compiled = re.compile(pattern)
    except re.error:
        return False
    finds = any(compiled.search(s) for s in _FENCE_PROBES)
    return finds and not any(compiled.search(s.replace("---", "--"))
                             for s in _FENCE_PROBES)


def _fence_literals(nodes):
    for node in nodes:
        elements = (node.elts if isinstance(node, (ast.Tuple, ast.List,
                                                   ast.Set)) else [node])
        for element in elements:
            if (isinstance(element, ast.Constant)
                    and isinstance(element.value, str)
                    and element.value.strip() == "---"):
                yield element.value


def fence_definitions(source):
    """Every fence-defining string constant in SOURCE, in walk order."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func,
                                                     ast.Attribute):
            func = node.func
            if (isinstance(func.value, ast.Name) and func.value.id == "re"
                    and func.attr in _REGEX_CALLS):
                first = node.args[:1]
                if (first and isinstance(first[0], ast.Constant)
                        and isinstance(first[0].value, str)
                        and _is_fence_regex(first[0].value)):
                    found.append(first[0].value)
                continue
            found.extend(_fence_literals(node.args))
        elif isinstance(node, ast.Compare) and any(
                isinstance(op, _COMPARISONS) for op in node.ops):
            found.extend(_fence_literals([node.left, *node.comparators]))
    return found


def _tracked_non_test_python():
    listed = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--", "*.py"],
        capture_output=True, text=True, check=True).stdout
    for rel in sorted(r for r in listed.split("\0") if r):
        parts = Path(rel).parts
        if "tests" in parts or parts[-1].startswith("test_"):
            continue
        yield rel, (ROOT / rel).read_text(encoding="utf-8")


class TestOneFenceDefinition(unittest.TestCase):
    """protocol.frontmatter_end holds the one fence rule (ADR-0118): a
    second definition anywhere in tracked Python fails this count."""

    def test_the_exact_count_map(self):
        counts = {}
        for rel, source in _tracked_non_test_python():
            found = fence_definitions(source)
            if found:
                counts[rel] = sorted(found)
        self.assertEqual(counts, {
            "protocol.py": [r"^---\s*$"],
            "factory/templates/tools/factory/protocol.py": [r"^---\s*$"],
            # Not a fence: the markdown table separator row lint skips.
            "lint.py": ["---"],
        })

    def test_the_detector_sees_each_copy_shape(self):
        copies = {
            "regex": 'FENCE = re.compile(r"^---\\s*$")\n',
            "block regex": ('BLOCK = re.compile(r"\\A---\\n(.*?)\\n---\\n", '
                            're.DOTALL)\n'),
            "string method": 'text.startswith("---\\n")\n',
            "string search": 'text.find("\\n---\\n", 4)\n',
            "comparison": 'line.strip() == "---"\n',
            "membership": 'cell in ("stage", "---")\n',
        }
        for shape, source in copies.items():
            with self.subTest(shape=shape):
                self.assertEqual(len(fence_definitions(source)), 1)

    def test_the_known_non_owners_count_zero(self):
        import gates
        non_owners = {
            "setext underline": (
                f"SETEXT_UNDERLINE = re.compile({gates.SETEXT_UNDERLINE.pattern!r})\n"),
            "charter delimiters": 'PROMPT = """--- YOUR CHARTER ---\n"""\n',
            "frontmatter writer": 'text = "---\\nname: " + name\n',
        }
        for shape, source in non_owners.items():
            with self.subTest(shape=shape):
                self.assertEqual(fence_definitions(source), [])


if __name__ == "__main__":
    unittest.main()
