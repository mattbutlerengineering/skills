"""Stdlib-only Makefile text extraction shared by the lockstep tests.

test_factory_gates and test_design_pipeline both assert Makefile <-> CI
lockstep and had byte-identical copies of this extractor; helpers a
single suite uses (product_form, on_block) stay in their suites.
"""


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
