"""Stdlib-only Makefile text extraction shared by the lockstep tests.

test_gates and test_design_pipeline both assert Makefile <-> CI
lockstep and had byte-identical copies of this extractor; helpers a
single suite uses (product_form, on_block) stay in their suites.
"""
import re

TARGET_HEADER = re.compile(r"^([A-Za-z_][\w-]*):(?!=)")


def make_targets(text):
    """Every recipe target this Makefile actually declares, in file
    order — a real `name:` header at column 0, never a `.PHONY:` listing
    or a `VAR ?=`/`VAR :=` assignment (the `(?!=)` guard on the colon)."""
    names = []
    for line in text.splitlines():
        if not line or line[0].isspace():
            continue
        match = TARGET_HEADER.match(line)
        if match:
            names.append(match.group(1))
    return names


def phony_targets(text):
    """The names every `.PHONY:` line lists, in file order, deduplicated —
    GNU Make lets a Makefile repeat `.PHONY:` to add more names rather
    than requiring one line."""
    names = []
    for line in text.splitlines():
        if line.startswith(".PHONY:"):
            for name in line[len(".PHONY:"):].split():
                if name not in names:
                    names.append(name)
    return names


def make_recipe(text, target):
    """The command lines of one make target (tab-indented recipe lines)."""
    lines, capturing = [], False
    for line in text.splitlines():
        if line.startswith(f"{target}:"):
            capturing = True
        elif capturing:
            if line.startswith("\t"):
                lines.append(line.strip())
            elif line.strip():
                break
    return lines
