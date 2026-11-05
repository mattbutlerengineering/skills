"""The review skill's domain-pass table: rows, links, and Interface selection."""
import fnmatch
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

REFS = ROOT / "skills" / "review" / "references"
TABLE = REFS / "domain-reviewers.md"
INTERFACE = REFS / "interface.md"

PASSES = ["Payments", "Migrations", "Dependencies", "Interface"]
PRD_EXTENSIONS = ["*.tsx", "*.jsx", "*.vue", "*.svelte", "*.css", "*.scss"]
SIGNALS = [
    "aria-label",
    "alt=",
    ":focus-visible",
    "outline",
    "tabindex",
    "prefers-reduced-motion",
    "logical properties",
    "lang=",
    "dir=",
    "token",
]
UI_PATHS = ["src/App.tsx", "styles/main.scss", "views/show.html.erb",
            "a/Button.vue"]
NON_UI_PATHS = ["README.md", "skills/x/templates/TEMPLATE.md", "src/api.ts",
                "package.json", "migrations/001.sql"]


def rows():
    """Table rows as (pass name, selection cell, read cell)."""
    out = []
    for line in TABLE.read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) == 3 and cells[0] not in (
                "Pass", "---"):
            out.append(tuple(cells))
    return out


def interface_row():
    for row in rows():
        if row[0] == "Interface":
            return row
    return None


class DomainTableTest(unittest.TestCase):
    def test_pass_names(self):
        self.assertEqual([r[0] for r in rows()], PASSES)

    def test_read_links_resolve(self):
        for name, _, read in rows():
            with self.subTest(row=name):
                m = re.search(r"\]\(([^)]+)\)", read)
                self.assertIsNotNone(m, f"{name} row has no Read link")
                self.assertTrue((REFS / m.group(1)).is_file(),
                                f"{name} row links {m.group(1)}, not a file")

    def test_interface_row_extensions(self):
        row = interface_row()
        self.assertIsNotNone(row, "missing the Interface row")
        tokens = re.findall(r"`(\*\.[A-Za-z0-9]+)`", row[1])
        for ext in PRD_EXTENSIONS:
            self.assertIn(ext, tokens, f"Interface row lacks {ext}")

    def test_interface_reference_names_signals(self):
        self.assertTrue(INTERFACE.is_file(), "missing interface.md")
        text = INTERFACE.read_text()
        for signal in SIGNALS:
            self.assertIn(signal, text, f"interface.md lacks {signal}")

    def test_selection_by_path(self):
        row = interface_row()
        self.assertIsNotNone(row, "missing the Interface row")
        tokens = re.findall(r"`(\*\.[A-Za-z0-9]+)`", row[1])

        def selected(path):
            return any(fnmatch.fnmatch(path.lower(), "*" + t[1:])
                       for t in tokens)
        for path in UI_PATHS:
            with self.subTest(path=path):
                self.assertTrue(selected(path))
        for path in NON_UI_PATHS:
            with self.subTest(path=path):
                self.assertFalse(selected(path))


if __name__ == "__main__":
    unittest.main()
