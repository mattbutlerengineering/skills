"""Stdlib-only workflow text extraction shared by the run-step tests.

Sibling of make_parse: test_factory_gates' run-step invariant needs every
`run:` command in a workflow file without a YAML parser (stdlib only,
like every script here). Handles the two forms this repo's workflows
use — inline (`run: make check`) and block scalar (`run: |` followed by
deeper-indented lines).
"""


def run_steps(text):
    """Every `run:` command in a workflow file, one string per step
    (single-line and block-scalar forms both — any `|`/`>` indicator
    starts a block, chomping and folding markers included, since the
    guard classifies commands and folding semantics don't matter). A
    block step is its lines stripped and joined with newlines — comment
    lines kept (they carry the step's justification), blank lines
    dropped; the block ends at the first non-blank line indented at or
    left of the `run:` key (for a `- run:` sequence item, the key
    column, so a sibling key like `env:` ends the block)."""
    steps = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        dashed = stripped.startswith("- ")
        if dashed:
            stripped = stripped[2:].lstrip()
        if not stripped.startswith("run:"):
            index += 1
            continue
        indent = len(line) - len(line.lstrip())
        if dashed:
            indent += 2
        rest = stripped[len("run:"):].strip()
        if rest and rest[0] in "|>":
            block = []
            index += 1
            while index < len(lines):
                nxt = lines[index]
                if nxt.strip() and len(nxt) - len(nxt.lstrip()) <= indent:
                    break
                if nxt.strip():
                    block.append(nxt.strip())
                index += 1
            steps.append("\n".join(block))
            continue
        steps.append(rest)
        index += 1
    return steps
