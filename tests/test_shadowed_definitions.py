"""No module may rebind a name it already defined at the same scope.

Python rebinds silently, so the second definition simply replaces the
first and nothing reports it. In a test module that means the shadowed
class's tests stop running and **the suite still says OK** — the only
signal is a test count nobody checks. This run was written after
exactly that happened here: a second `class TestScaffoldSync` in
`tests/test_gates.py` deleted three tests, and `unittest` reported
success (`docs/fixes/json-that-is-not-utf8/verification.md` §5).

The grammar is pure over one file's source, in the shape every checker
in this repo uses (twin of `gates.evidence_problems`): it takes text and
returns label-prefixed problem strings. The repo-wide walk below is the
thin caller.

Only the SAME scope counts. Two classes may each define `setUp`; a
module and a class may each define `check`. A conditional definition
(`if X: def f() else: def f()`) is nested inside the `if`, never a
sibling in `body`, so it is naturally out of scope rather than
special-cased. Property accessors are the one real same-scope
repetition Python intends, and they are excused by their decorator.
"""
import ast
import subprocess
import unittest
from pathlib import Path

# Definitions Python intends to repeat at one scope: the property
# protocol rebinds the name on purpose, and typing.overload declares
# several signatures for one implementation.
_INTENDED = ("setter", "getter", "deleter")
_OVERLOAD = {"overload", "typing.overload"}

_DEFINITION = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _intended(node):
    decorators = {ast.unparse(d) for d in node.decorator_list}
    return (any(d.rsplit(".", 1)[-1] in _INTENDED for d in decorators)
            or bool(decorators & _OVERLOAD))


def _rebindings(body):
    """(name, first line, rebinding line) for every name defined twice as
    a direct child of one body, in the order the rebindings appear."""
    seen, found = {}, []
    for node in body:
        if not isinstance(node, _DEFINITION) or _intended(node):
            continue
        if node.name in seen:
            found.append((node.name, seen[node.name], node.lineno))
        seen[node.name] = node.lineno
    return found


def shadow_problems(rel, source):
    """Problem strings for every definition `source` rebinds, module
    scope and class scope, prefixed `shadow:` and located at the
    rebinding — the line to delete, not the line that is lost.

    A syntax error is a problem, not a traceback: this walk parses every
    Python file in the repo, and one unparsable file must not take the
    check down with it."""
    try:
        tree = ast.parse(source)
    except SyntaxError as err:
        return [f"shadow: {rel} cannot be parsed: {err}"]
    problems = [f"shadow: {rel}:{line} redefines {name}, shadowing the"
                f" definition at line {first}"
                for name, first, line in _rebindings(tree.body)]
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            problems += [
                f"shadow: {rel}:{line} redefines {node.name}.{name},"
                f" shadowing the definition at line {first}"
                for name, first, line in _rebindings(node.body)]
    return problems


def tracked_python(root):
    """(rel, source) for every Python file git tracks, and the problems
    reading them.

    git, never rglob, and for the reason one_owner.source_files states:
    rglob finds 250 Python files here where git tracks 98, and the
    difference is stale `.claude/worktrees/agent-*` checkouts hidden by
    a LOCAL, uncommitted `.git/info/exclude`. A walking check would
    report a shadowed definition in a months-old copy of a file the
    tracked tree has since fixed.

    Unlike one_owner this keeps `tests/`, which is the scope that needs
    the check most: a shadowed test class is the case that fails
    silently."""
    listed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "*.py"],
        capture_output=True, text=True, check=True).stdout
    files, problems = [], []
    for rel in sorted(r for r in listed.split("\0") if r):
        try:
            files.append((rel, (Path(root) / rel).read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError) as err:
            problems.append(f"shadow: {rel} cannot be read: {err}")
    return files, problems


class TestShadowProblems(unittest.TestCase):
    def test_a_rebound_module_level_class_is_a_problem(self):
        source = ("class A:\n    pass\n\n\nclass B:\n    pass\n\n\n"
                  "class A:\n    pass\n")
        self.assertEqual(shadow_problems("m.py", source), [
            "shadow: m.py:9 redefines A, shadowing the definition at line 1"])

    def test_a_rebound_method_is_a_problem(self):
        source = ("class A:\n    def go(self):\n        pass\n\n"
                  "    def go(self):\n        pass\n")
        self.assertEqual(shadow_problems("m.py", source), [
            "shadow: m.py:5 redefines A.go, shadowing the definition"
            " at line 2"])

    def test_the_same_name_at_two_scopes_is_not_a_problem(self):
        """Two classes may each define setUp, and a module-level helper
        may share a name with a method. Only one body is one scope."""
        source = ("def go():\n    pass\n\n\nclass A:\n    def go(self):\n"
                  "        pass\n\n\nclass B:\n    def go(self):\n"
                  "        pass\n")
        self.assertEqual(shadow_problems("m.py", source), [])

    def test_a_conditional_definition_is_not_a_problem(self):
        """Nested in the `if`, never a sibling in the module body — out
        of scope by construction rather than by a special case."""
        source = ("import sys\n\nif sys.version_info >= (3, 12):\n"
                  "    def go():\n        pass\n"
                  "else:\n    def go():\n        pass\n")
        self.assertEqual(shadow_problems("m.py", source), [])

    def test_property_accessors_are_not_a_problem(self):
        source = ("class A:\n    @property\n    def v(self):\n"
                  "        return 1\n\n    @v.setter\n"
                  "    def v(self, value):\n        pass\n")
        self.assertEqual(shadow_problems("m.py", source), [])

    def test_every_rebinding_is_reported_not_just_the_first(self):
        source = "def go():\n    pass\n\n\ndef go():\n    pass\n\n\ndef go():\n    pass\n"
        self.assertEqual(shadow_problems("m.py", source), [
            "shadow: m.py:5 redefines go, shadowing the definition at line 1",
            "shadow: m.py:9 redefines go, shadowing the definition at line 5"])

    def test_an_unparsable_file_is_a_problem_not_a_traceback(self):
        problems = shadow_problems("m.py", "def (\n")
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("shadow: m.py cannot be"
                                               " parsed:"), problems)


class TestTheRepoItself(unittest.TestCase):
    def test_no_tracked_module_shadows_a_definition(self):
        root = Path(__file__).resolve().parents[1]
        files, problems = tracked_python(root)
        # an empty universe is never a clean one — the same posture
        # one_owner.source_files takes about a broken environment
        self.assertTrue(files, "git tracked no Python files — the walk"
                               " itself is broken, not the repo clean")
        for rel, source in files:
            problems += shadow_problems(rel, source)
        self.assertEqual(problems, [])
