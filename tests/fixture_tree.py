"""The shared fixture tree the factory-tool suites build on.

One primitive — write a relative file, creating parents — kept in one
place instead of a copy per suite. A suite that wants a pre-populated
tree (a factory.json, a breakdown, an orientation pack) subclasses this
and adds builder methods next to the module-local constants they write;
the divergence lives in the subclass, never in this core.
"""
from pathlib import Path


class FixtureTree:
    def __init__(self, root):
        self.root = Path(root)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path
