"""The canonical factory-config test fixture: one CONFIG, one writer.

Four suites (assembler, budget_guard, cost_report, factory_config) each
carried a byte-identical copy of this dict; a budgets_usd or routing
change was four edits or silent drift. CONFIG is loaded from
factory/templates/factory.json itself, so the fixture cannot drift from
the shipped config — a cap or routing change lands in every suite by
editing the one real file.
"""
import json
from pathlib import Path

from fixture_tree import FixtureTree as BaseFixtureTree

CONFIG = json.loads(
    (Path(__file__).resolve().parents[1] / "factory" / "templates"
     / "factory.json").read_text(encoding="utf-8"))


class FixtureTree(BaseFixtureTree):
    def factory(self):
        """The canonical factory.json in the template payload."""
        self.write("factory/templates/factory.json", json.dumps(CONFIG))
        return self
