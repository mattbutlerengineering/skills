"""implement-queue's two claim sources (ADR-0127).

work-queue folded into implement-queue as `source: work-orders`. Three
promises keep the fold from loosening a gate, and each is pinned here
against the real files:

- the profile table names the `source` key and its `issues` default;
- issues mode never claims an issue carrying a `wo:*` label, so the two
  sources cannot race for one issue;
- work-orders mode never merges, whatever `merge:` says (ADR-0033 gate 3).
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "implement-queue" / "SKILL.md"
WORK_ORDERS = ROOT / "skills" / "implement-queue" / "references" / "work-orders.md"


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def section(path, heading):
    text = path.read_text(encoding="utf-8")
    body = text.split(f"\n{heading}\n", 1)[1].split("\n## ", 1)[0]
    return " ".join(body.split())


class TestTheSourceKey(unittest.TestCase):
    def test_the_profile_table_names_source_and_its_default(self):
        self.assertIn("| `source` | `issues` |",
                      flat(SKILL).replace("  ", " "))

    def test_the_skill_points_work_orders_at_the_reference(self):
        self.assertIn("references/work-orders.md", flat(SKILL))


class TestTheSourcesNeverRace(unittest.TestCase):
    def test_issues_mode_drops_work_order_issues(self):
        claim = section(SKILL, "## Phase 1: Claim a batch")
        self.assertIn("carries a `wo:*` label", claim)


class TestWorkOrdersNeverMerge(unittest.TestCase):
    def test_the_reference_forces_merge_off(self):
        text = flat(WORK_ORDERS)
        self.assertIn("forces `merge: off`", text)
        self.assertIn("gate 3", text)

    def test_the_merge_policy_names_the_exception(self):
        policy = section(SKILL, "## Merge policy")
        self.assertIn("`source: work-orders`", policy)


if __name__ == "__main__":
    unittest.main()
