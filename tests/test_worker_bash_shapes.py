"""Worker Bash shapes (#2319) — one owner, the dispatchers recite.

skills/implement-queue/references/worker-bash-shapes.md is the one owner
of the Bash shapes a worktree-isolated worker may use. implement-queue's
worker brief and work-order brief, and autorun's dispatch step, carry
one identical sentence that names the owner and cite its path; none
restates the block, so the shapes are counted across the owner and the
reciters: exactly once, and that once in the owner. conduct's Workers
are headless runs bounded by --allowedTools rather than worktree
isolation, so conduct cites the owner's variant and its brief, written
by conductor_run.compose_brief, carries that variant's section.

Also pins the merge shape the same issue fixed: no prescribed
`gh pr merge` carries `--delete-branch`, which fails from a worktree.
Whether a worker actually followed the shapes is not a thing a test can
know; these pin what the prose promises.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import conductor_run  # noqa: E402

OWNER = "skills/implement-queue/references/worker-bash-shapes.md"
# The one sentence each reciter carries, verbatim, beside its citation.
RECITAL = ("Copy the worker Bash shapes block verbatim into the prompt of"
           " every worktree-isolated worker; one file owns it:")
RECITERS = {
    "skills/implement-queue/references/worker-brief.md":
        "(worker-bash-shapes.md)",
    "skills/implement-queue/references/work-orders.md":
        "(worker-bash-shapes.md)",
    # A sibling skill's file is named in backticks, never linked
    # (ADR-0008; lint's SIBLING_ASSET).
    "skills/autorun/SKILL.md":
        "`../implement-queue/references/worker-bash-shapes.md`",
}
CONDUCT = "skills/conduct/SKILL.md"
CONDUCT_CITE = "`../implement-queue/references/worker-bash-shapes.md`"
# The block's distinctive lines: in the owner once, in no reciter.
SHAPES = (
    "One plain command per call: no heredoc, no `&&`, `||`, `;` or `|`"
    " compound",
    "Never `cd`. Name every file by its absolute path.",
    "Write file content through the Write or Edit tool, never through"
    " the shell",
    "Run git as `git -C <absolute worktree path> <subcommand>`.",
    "Run gh with `--repo <owner>/<repo>` on every call.",
    "goes in a script written to the scratchpad directory and run as one"
    " plain command",
)
# What conductor_run's brief must say in its own section.
CONDUCT_SHAPES = ("One plain command per call", "no heredoc", "never `cd`",
                  "Write or Edit", "never `git -C`",
                  "one `python3 <absolute script path>` call")
# Files that prescribe a merge command an agent copies.
MERGE_PROSE = ("skills/implement-queue/SKILL.md",
               "skills/implement-queue/references/profile-migration.md",
               "skills/implement-queue/references/merge-train.md",
               "skills/implement-queue/references/cloud-sessions.md",
               "skills/conduct/SKILL.md", ".claude/implement-queue.md",
               "docs/factory/merge-train-routine.md")


def flat(rel):
    """Lower-cased, whitespace-collapsed text with blockquote markers
    gone, so a line wrapped or quoted differently still matches."""
    text = (ROOT / rel).read_text(encoding="utf-8")
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
    return " ".join(text.split()).lower()


def norm(sentence):
    return " ".join(sentence.split()).lower()


class TheOwnerStatesTheShapes(unittest.TestCase):
    def test_each_shape_occurs_once_and_in_the_owner(self):
        files = [OWNER, *RECITERS, CONDUCT]
        for shape in SHAPES:
            counts = {rel: flat(rel).count(norm(shape)) for rel in files}
            with self.subTest(shape=shape):
                self.assertEqual((sum(counts.values()), counts[OWNER]),
                                 (1, 1), counts)

    def test_the_owner_names_conducts_variant(self):
        text = flat(OWNER)
        for needle in ("conductor_run.compose_brief", "`## bash shapes`",
                       "never `git -c`", "--allowedtools"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)


class TheDispatchersRecite(unittest.TestCase):
    def test_each_reciter_carries_the_sentence_once_and_cites_the_owner(self):
        for rel, cited in RECITERS.items():
            with self.subTest(file=rel):
                text = flat(rel)
                self.assertEqual(text.count(norm(RECITAL)), 1)
                self.assertIn(cited, text)

    def test_conduct_cites_the_owner(self):
        self.assertIn(CONDUCT_CITE, flat(CONDUCT))

    def test_the_cited_owner_ships(self):
        self.assertTrue((ROOT / OWNER).is_file())


class TheConductBriefCarriesTheVariant(unittest.TestCase):
    def test_the_brief_has_a_bash_shapes_section(self):
        brief = conductor_run.compose_brief(
            step="build", item="#12", item_type="feature", worktree="/w",
            branch="conductor/b1-12", block={}, wo="WO-0170", context="",
            issue_body=None, ceiling=3.0)
        section = brief.split("## Bash shapes", 1)[1].split("\n## ", 1)[0]
        for needle in CONDUCT_SHAPES:
            with self.subTest(needle=needle):
                self.assertIn(needle, section)
        self.assertIn("/w", section)


class NoPrescribedMergeDeletesTheBranch(unittest.TestCase):
    def test_no_gh_pr_merge_line_carries_delete_branch(self):
        for rel in MERGE_PROSE:
            for line in (ROOT / rel).read_text(encoding="utf-8").splitlines():
                with self.subTest(file=rel, line=line):
                    self.assertFalse("gh pr merge" in line
                                     and "--delete-branch" in line, line)

    def test_the_default_deletes_the_remote_branch_once_merged(self):
        text = flat("skills/implement-queue/SKILL.md")
        self.assertIn("gh api -x delete repos/<owner>/<repo>/git/refs/heads/"
                      "<branch>", text)
        self.assertIn("reports `merged`", text)


if __name__ == "__main__":
    unittest.main()
