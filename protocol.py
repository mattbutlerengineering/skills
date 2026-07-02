"""The pipeline protocol's executable knowledge, in one place.

docs/pipeline-protocol.md is the spec; this module is its one
implementation. It owns the stage/skill taxonomy, the artifact table,
artifact-frontmatter reading, the UX conditional, the checkbox rule, the
retro short-circuit, and next-stage derivation (ADR-0021). Tools — the
orientation CLI, the structural lint, the trigger-eval runner — are thin
callers.
"""
import re
from pathlib import Path

STAGES = ["idea", "prd", "ux-design", "architect", "decompose",
          "implement", "verify", "review", "ship", "operate"]
# implement's artifact is code itself; every other stage ships a template
TEMPLATED_STAGES = [s for s in STAGES if s != "implement"]
ALL_SKILLS = ["next"] + STAGES

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

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_CHECKBOX = re.compile(r"^\s*[-*+] \[([ xX])\]", re.MULTILINE)


def read_frontmatter(path):
    """Parse a `key: value` frontmatter block into a dict.

    Single error contract: returns None when the file has no frontmatter
    block; a present-but-fieldless block is an empty dict. Callers decide
    what a missing block means for them.
    """
    match = _FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        return None
    return dict(
        (line.split(":", 1)[0].strip(), line.split(":", 1)[1].strip())
        for line in match.group(1).splitlines()
        if ":" in line
    )


def _ux_skipped(run_dir):
    """UX Design is skipped only when prd.md records ux: not-applicable.
    A missing prd.md or missing ux: field means the decision hasn't been
    made, so the stage still counts as pending."""
    prd = run_dir / "prd.md"
    if not prd.is_file():
        return False
    return (read_frontmatter(prd) or {}).get("ux") == "not-applicable"


def _implement_complete(run_dir):
    """Every checkbox in breakdown.md is checked. Zero checkboxes counts
    as incomplete — no checkboxes is no evidence of implementation, and
    the decompose template always emits them."""
    breakdown = run_dir / "breakdown.md"
    if not breakdown.is_file():
        return False
    boxes = _CHECKBOX.findall(breakdown.read_text(encoding="utf-8"))
    return bool(boxes) and all(box in "xX" for box in boxes)


def _stage_complete(stage, artifact, run_dir):
    if stage == "implement":
        return _implement_complete(run_dir)
    if stage == "ux-design":
        return (run_dir / artifact).is_file() or _ux_skipped(run_dir)
    return (run_dir / artifact).is_file()


def next_stage(run_dir):
    """First stage in pipeline order that is not complete. retro.md marks
    the whole run complete regardless of earlier gaps (the protocol's
    run-discovery rule and the router's step 6 both key on it alone)."""
    run_dir = Path(run_dir)
    if (run_dir / "retro.md").is_file():
        return "complete"
    for stage, artifact in STAGE_ARTIFACTS:
        if not _stage_complete(stage, artifact, run_dir):
            return stage
    return "complete"
