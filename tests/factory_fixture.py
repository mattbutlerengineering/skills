"""The canonical factory-config test fixture: one CONFIG, one writer.

Four suites (assembler, budget_guard, cost_report, factory_config) each
carried a byte-identical copy of this dict; a budgets_usd or routing
change was four edits or silent drift. It mirrors
factory/templates/factory.json — change them together.
"""
import json

from fixture_tree import FixtureTree as BaseFixtureTree

CONFIG = {
    "budgets_usd": {"S": 5, "M": 15, "L": 40},
    "routing": {"mechanical": "claude-haiku-4-5",
                "implementation": "claude-sonnet-5",
                "architecture_review": "claude-fable-5"},
    "wip_cap": 3,
    "monthly_cap_usd": 300,
}


class FixtureTree(BaseFixtureTree):
    def factory(self):
        """The canonical factory.json in the template payload."""
        self.write("factory/templates/factory.json", json.dumps(CONFIG))
        return self
