"""The queue profile's merge text is what an agent copies (#1827).

main has no branch protection (docs/kb/main-unprotected.md), so GitHub
requires no check: `gh pr merge --auto` merges at once instead of
waiting, and the REST twin merges whatever head it is given. Waiting
for a green `check` at the gated head is the merger's job, so the
profile's merge hooks must say it where the command sits. The
capability-gap message is a closed set: the skill's summary, its
cloud-sessions reference and the profile quote one exact string.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / ".claude" / "implement-queue.md"
SKILL = ROOT / "skills" / "implement-queue" / "SKILL.md"
CLOUD = (ROOT / "skills" / "implement-queue" / "references"
         / "cloud-sessions.md")
KB = "docs/kb/main-unprotected.md"
GAP_MESSAGE = "GitHub GraphQL not available from Claude Code sessions"


def flat(text):
    return " ".join(text.split())


def hook(name):
    """One `## <name>` section of the profile, prose unwrapped."""
    profile = PROFILE.read_text(encoding="utf-8")
    body = profile.split(f"\n## {name}\n", 1)[1]
    return flat(body.split("\n## ", 1)[0])


class TestMergeWaitsForAGreenCheck(unittest.TestCase):
    def test_the_rest_twin_runs_only_once_ci_status_is_green(self):
        text = hook("merge-command")
        rest = text.index("gh api -X PUT")
        sentence = text[text.rfind(". ", 0, rest):text.find(". ", rest)]
        self.assertIn("once `ci-status` is green at the gated head",
                      sentence)

    def test_the_merge_command_says_auto_does_not_wait_here(self):
        text = hook("merge-command")
        for token in ("`--auto` does not wait", KB,
                      "`completed` with conclusion `success`",
                      "on that exact head"):
            self.assertIn(token, text)

    def test_update_branch_waits_for_check_on_the_new_head(self):
        text = hook("update-branch")
        for token in ("`completed` with conclusion `success`",
                      "the new head", KB, "`--auto` does not wait"):
            self.assertIn(token, text)


class TestCapabilityGapMessageIsQuotedExactly(unittest.TestCase):
    def test_skill_reference_and_profile_quote_one_message(self):
        for path in (SKILL, CLOUD, PROFILE):
            with self.subTest(path=path.name):
                self.assertIn(GAP_MESSAGE,
                              flat(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
