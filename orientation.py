#!/usr/bin/env python3
"""Reference implementation of the orientation decision table in
docs/pipeline-protocol.md: given a run directory, which stage is next?

The router skill follows the table as prose; this module makes the same
rules executable so the table is verifiable against fixture docs trees
(and usable ad hoc: `python3 orientation.py docs/`).
"""
import re
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
CHECKBOX = re.compile(r"^\s*[-*+] \[([ xX])\]", re.MULTILINE)

# (stage, artifact) rows in pipeline order; implement and the UX
# conditional are handled specially below.
STAGE_ARTIFACTS = [
    ("idea", "idea.md"),
    ("prd", "prd.md"),
    ("ux-design", "ux.md"),
    ("architect", "architecture.md"),
    ("decompose", "breakdown.md"),
    ("implement", "breakdown.md"),
    ("verify", "verification.md"),
    ("review", "review.md"),
    ("ship", "release.md"),
    ("operate", "retro.md"),
]


def read_frontmatter(path):
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        return {}
    return dict(
        (line.split(":", 1)[0].strip(), line.split(":", 1)[1].strip())
        for line in match.group(1).splitlines()
        if ":" in line
    )


def ux_skipped(run_dir):
    """UX Design is skipped only when prd.md records ux: not-applicable.
    A missing prd.md or missing ux: field means the decision hasn't been
    made, so the stage still counts as pending."""
    prd = run_dir / "prd.md"
    if not prd.is_file():
        return False
    return read_frontmatter(prd).get("ux") == "not-applicable"


def implement_complete(run_dir):
    """Every checkbox in breakdown.md is checked. Zero checkboxes counts
    as incomplete — no checkboxes is no evidence of implementation, and
    the decompose template always emits them."""
    breakdown = run_dir / "breakdown.md"
    if not breakdown.is_file():
        return False
    boxes = CHECKBOX.findall(breakdown.read_text(encoding="utf-8"))
    return bool(boxes) and all(box in "xX" for box in boxes)


def stage_complete(stage, artifact, run_dir):
    if stage == "implement":
        return implement_complete(run_dir)
    if stage == "ux-design":
        return (run_dir / artifact).is_file() or ux_skipped(run_dir)
    return (run_dir / artifact).is_file()


def next_stage(run_dir):
    """First stage in pipeline order that is not complete. retro.md marks
    the whole run complete regardless of earlier gaps (the protocol's
    run-discovery rule and the router's step 6 both key on it alone)."""
    run_dir = Path(run_dir)
    if (run_dir / "retro.md").is_file():
        return "complete"
    for stage, artifact in STAGE_ARTIFACTS:
        if not stage_complete(stage, artifact, run_dir):
            return stage
    return "complete"


def main(argv):
    if len(argv) != 2:
        print("usage: orientation.py <run-directory>", file=sys.stderr)
        return 2
    run_dir = Path(argv[1])
    if not run_dir.is_dir():
        print(f"orientation: not a directory: {run_dir}", file=sys.stderr)
        return 2
    print(next_stage(run_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
