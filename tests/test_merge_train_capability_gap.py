"""The merge-train routine's no-retry rules carve out the capability
gap (#1827). Two runs of this routine diverged in #1803: one read a
GraphQL 403 in a cloud session as a denial, the other ran the REST twin.
A denied merge is never retried, but a capability gap is not a denial,
so §4 step 4 and §7 both point at the skill's capability-gap section,
and that link must name a real heading.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUTINE = ROOT / "docs" / "factory" / "merge-train-routine.md"
LINK = ("../../skills/implement-queue/references/cloud-sessions.md"
        "#a-capability-gap-is-not-a-permission-refusal")


def section(text, start, end):
    return " ".join(text.split(start, 1)[1].split(end, 1)[0].split())


class TestNoRetryRulesPointAtTheCapabilityGap(unittest.TestCase):
    def setUp(self):
        self.text = ROUTINE.read_text(encoding="utf-8")

    def test_the_trains_merge_step_links_the_section(self):
        step = section(self.text, "\n4. Run the `merge-command` hook",
                       "\n5. ")
        self.assertIn("capability gap", step)
        self.assertIn(f"]({LINK})", step)

    def test_the_non_negotiable_links_the_section(self):
        rules = section(self.text, "## 7 Non-negotiables", "## 8 ")
        bullet = rules.split("- Never retry a denied merge", 1)[1]
        bullet = bullet.split(" - ", 1)[0]
        self.assertIn("capability gap", bullet)
        self.assertIn(f"]({LINK})", bullet)

    def test_the_link_names_a_real_heading(self):
        target, anchor = LINK.split("#")
        headings = re.findall(r"^#{1,6} (.+)$", (ROUTINE.parent / target)
                              .resolve().read_text(encoding="utf-8"), re.M)
        slugs = {re.sub(r"[^\w\- ]", "", h.strip().lower()).replace(" ", "-")
                 for h in headings}
        self.assertIn(anchor, slugs)


if __name__ == "__main__":
    unittest.main()
