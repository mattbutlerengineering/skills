"""conductor_flow.changed_files / gate_blobs and conductor_plan.ids_on_main
against a real scratch repo (#1871, #1880): git quotes non-ASCII names and
a plain split breaks a name with spaces, a deleted gate file has no blob
on the branch, and each of them must still be read."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import conductor_flow as flow  # noqa: E402
import git_repo  # noqa: E402
import conductor_plan as plan  # noqa: E402

ZERO = "0" * 40
BRANCH = "conductor/b1-12"


class RepoCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        git_repo.init(self.dir, "-b", "main")
        self.run_git("config", "user.email", "t@example.com")
        self.run_git("config", "user.name", "t")

    def run_git(self, *args):
        return subprocess.run(["git", "-C", str(self.dir), *args], text=True,
                              capture_output=True, check=True)

    def git(self, args):
        return self.run_git(*args)

    def commit(self, files, message="c"):
        for name, text in files.items():
            path = self.dir / name
            if text is None:
                path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.run_git("add", "-A")
        self.run_git("commit", "-q", "-m", message)

    def publish_main(self):
        self.run_git("update-ref", "refs/remotes/origin/main", "HEAD")

    def branch(self, files):
        self.run_git("checkout", "-q", "-b", BRANCH)
        self.commit(files)

    def blob(self, path):
        return self.run_git("rev-parse", f"{BRANCH}:{path}").stdout.strip()


class TestBranchPaths(RepoCase):
    def test_a_deleted_gate_file_is_read_with_the_zero_blob(self):
        self.commit({"docs/adr/0001-x.md": "x\n", "keep.txt": "k\n"})
        self.publish_main()
        self.branch({"docs/adr/0001-x.md": None})
        self.assertEqual(flow.changed_files(self.git, BRANCH),
                         (["docs/adr/0001-x.md"], []))
        self.assertEqual(flow.gate_blobs(self.git, BRANCH),
                         ({"docs/adr/0001-x.md": ZERO}, []))

    def test_non_ascii_and_spaced_gate_files_are_read_whole(self):
        self.commit({"keep.txt": "k\n"})
        self.publish_main()
        accented, spaced = ("docs/adr/0002-décision.md",
                            "docs/adr/0003 two words.md")
        self.branch({accented: "d\n", spaced: "w\n"})
        self.assertEqual(sorted(flow.changed_files(self.git, BRANCH)[0]),
                         [accented, spaced])
        self.assertEqual(flow.gate_blobs(self.git, BRANCH), (
            {accented: self.blob(accented), spaced: self.blob(spaced)}, []))

    def test_the_old_side_of_a_rename_is_a_deletion(self):
        self.commit({"docs/adr/0001-x.md": "x\n"})
        self.publish_main()
        self.branch({"docs/adr/0001-x.md": None, "docs/adr/0001-y.md": "x\n"})
        blobs, problems = flow.gate_blobs(self.git, BRANCH)
        self.assertEqual((problems, blobs["docs/adr/0001-x.md"]), ([], ZERO))
        self.assertEqual(blobs["docs/adr/0001-y.md"],
                         self.blob("docs/adr/0001-y.md"))


class TestIdsOnMain(RepoCase):
    def test_a_non_ascii_adr_filename_still_holds_its_number(self):
        self.commit({"docs/adr/0001-x.md": "x\n",
                     "docs/adr/0002-décision.md": "d\n"})
        self.publish_main()
        found, problems = plan.ids_on_main(self.git)
        self.assertEqual((problems, found["adr"]), ([], {1, 2}))


if __name__ == "__main__":
    unittest.main()
