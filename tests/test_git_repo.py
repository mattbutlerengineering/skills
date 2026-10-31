"""tests/git_repo.py — the one way a suite makes a real temp git repo.

#874 (siblings #761, #803): a commit in a fixture repo may start git's
auto housekeeping (`gc --auto`, `maintenance run --auto`), which can
detach and go on writing .git/objects/pack after the commit returns. A
TemporaryDirectory cleanup that races it fails with ENOTEMPTY. The race
itself is timing; what is pinned here is its writer: a git whose global
config asks for gc on every commit packs a raw repo's objects on
commit, and packs nothing in a repo git_repo made.

The last class pins that every suite makes its repos through git_repo,
derived from the syntax so the roll-call cannot go stale.
"""
import ast
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import git_repo  # noqa: E402

TESTS = Path(__file__).resolve().parent

# Synchronous gc on every commit: what a CI runner's git may do in the
# background, done in the foreground so the test is deterministic.
EAGER_GC = ("[gc]\n\tauto = 1\n\tautoDetach = false\n"
            "[maintenance]\n\tautoDetach = false\n"
            "[user]\n\tname = t\n\temail = t@t\n")


def packs(repo):
    return sorted(p.name for p in (repo / ".git/objects/pack").iterdir())


def bucket_17(count):
    """`count` file contents whose blob ids start 17: `gc --auto` judges
    the loose-object count by sampling objects/17 alone, so these are
    what makes gc.auto=1 fire on the commit that adds them."""
    found, n = [], 0
    while len(found) < count:
        text = f"{n}\n".encode()
        blob = hashlib.sha1(b"blob %d\0" % len(text) + text).hexdigest()
        if blob.startswith("17"):
            found.append(text)
        n += 1
    return found


def commit_gc_bait(repo):
    for i, text in enumerate(bucket_17(4)):
        name = f"f{i}"
        (repo / name).write_bytes(text)
        subprocess.run(["git", "-C", str(repo), "add", name], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", name],
                       check=True, capture_output=True)


class EagerGcCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        config = self.tmp / "gitconfig"
        config.write_text(EAGER_GC)
        env = mock.patch.dict(os.environ, {
            "HOME": str(self.tmp), "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(config)})
        env.start()
        self.addCleanup(env.stop)


class TestHousekeepingIsOff(EagerGcCase):
    def test_a_raw_repo_packs_on_commit(self):
        # The defect's writer: plain `git init` leaves auto-gc on.
        repo = self.tmp / "raw"
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        # Auto-gc detaches by default and can outlive the commit; run it
        # in the foreground so the pack exists when we look (#1132).
        subprocess.run(["git", "-C", str(repo), "config", "gc.autoDetach",
                        "false"], check=True)
        commit_gc_bait(repo)
        self.assertTrue(packs(repo))

    def test_an_init_repo_never_packs(self):
        repo = git_repo.init(self.tmp / "repo")
        commit_gc_bait(repo)
        self.assertEqual(packs(repo), [])

    def test_a_bare_init_and_its_clone_never_pack(self):
        origin = git_repo.init(self.tmp / "origin.git", "--bare")
        work = git_repo.clone(origin, self.tmp / "work")
        commit_gc_bait(work)
        subprocess.run(["git", "-C", str(work), "push", "-q", "origin",
                        "HEAD:refs/heads/main"], check=True,
                       capture_output=True)
        self.assertEqual(packs(work), [])
        self.assertEqual(sorted(p.name for p in
                                (origin / "objects/pack").iterdir()), [])

    def test_both_switches_are_in_the_repo_config(self):
        repo = git_repo.init(self.tmp / "repo")
        for key, value in (("gc.auto", "0"), ("maintenance.auto", "false")):
            got = subprocess.run(
                ["git", "-C", str(repo), "config", "--local", key],
                check=True, capture_output=True, text=True).stdout.strip()
            self.assertEqual(got, value, key)


def raw_repo_makers(directory=TESTS):
    """(file, line) of every git `init` or `clone` a suite under
    `directory` runs itself: a call passing the bare word "init" or
    "clone" as a positional argument, or a ["git", ..., "init"] argv
    whose first non-flag word is one. Recorded failures
    (CalledProcessError) build an argv without running it."""
    found = []
    for path in sorted(directory.glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call) or _records(node):
                continue
            if any(_makes(arg) for arg in node.args):
                found.append((path.name, node.lineno))
    return found


def _records(call):
    name = getattr(call.func, "attr", getattr(call.func, "id", ""))
    return name == "CalledProcessError"


def _makes(arg):
    if isinstance(arg, ast.Constant):
        return arg.value in ("init", "clone")
    if not isinstance(arg, ast.List) or not arg.elts:
        return False
    words = [e.value for e in arg.elts
             if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    if words[:1] != ["git"]:
        return False
    verbs = [w for w in words[1:] if not w.startswith("-")
             and "=" not in w]
    return verbs[:1] in (["init"], ["clone"])


class TestEverySuiteUsesGitRepo(unittest.TestCase):
    def test_no_suite_makes_a_raw_repo(self):
        self.assertEqual(raw_repo_makers(), [])

    def test_the_roll_call_sees_a_planted_maker(self):
        with tempfile.TemporaryDirectory() as tmp:
            planted = Path(tmp)
            (planted / "test_planted.py").write_text(
                "import subprocess\n"
                "subprocess.run(['git', 'init', '-q', 'r'])\n"
                "sh(tmp, 'clone', 'a', 'b')\n"
                "subprocess.CalledProcessError(128, ['git', 'init'])\n"
                "subprocess.run(['git', '-C', 'r', 'status'])\n")
            self.assertEqual(raw_repo_makers(planted),
                             [("test_planted.py", 2),
                              ("test_planted.py", 3)])


if __name__ == "__main__":
    unittest.main()
