"""The pipeline protocol's executable knowledge, in one place.

docs/pipeline-protocol.md is the spec; this module is its one
implementation. It owns the stage/skill taxonomy, the artifact tables
(product/feature and maintenance, ADR-0025), artifact-frontmatter
reading, the UX conditional, the re-entry conditional, the checkbox
rule, the retro short-circuit, and next-stage derivation (ADR-0021).
Tools — the orientation CLI, the structural lint, the trigger-eval
runner — are thin callers.
"""
import re
from pathlib import Path

STAGES = ["idea", "prd", "ux-design", "architect", "decompose",
          "implement", "verify", "review", "ship", "operate"]
# implement's artifact is code itself; every other stage ships a template
TEMPLATED_STAGES = [s for s in STAGES if s != "implement"]
# Utility skills act on work surrounding the pipeline (ADR-0023); they
# have no stage artifact and the router never routes to them, but they are
# full skills for install, lint, and trigger-eval purposes.
UTILITY_SKILLS = ["address-pr-review", "autorun"]
ALL_SKILLS = ["next"] + STAGES + UTILITY_SKILLS

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

# (stage, artifact) rows for a maintenance run (ADR-0025), in pipeline
# order. Capture replaces the idea-through-decompose front; re-entry
# depth recorded in defect.md decides whether the architect and decompose
# rows participate; implement's checkboxes live where the
# breakdown-placement rule puts them (see _maintenance_breakdown).
# Verify onward matches the main table — verify is never skippable.
MAINTENANCE_STAGE_ARTIFACTS = [
    ("capture", "defect.md"),
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


def _all_boxes_checked(path):
    """Every checkbox in the file is checked. Zero checkboxes counts as
    incomplete — no checkboxes is no evidence of implementation, and the
    breakdown (wherever the run keeps it) always emits them."""
    if not path.is_file():
        return False
    boxes = _CHECKBOX.findall(path.read_text(encoding="utf-8"))
    return bool(boxes) and all(box in "xX" for box in boxes)


def is_maintenance_run(run_dir):
    """A maintenance run is recognized without a manifest: it lives under
    docs/fixes/<slug>/ (the run-discovery rule) or already holds the
    capture seed defect.md. Either signal suffices, so an empty fixes
    directory orients to capture before any artifact exists."""
    run_dir = Path(run_dir)
    return (run_dir.parent.name == "fixes"
            or (run_dir / "defect.md").is_file())


def _re_entry_architect(run_dir):
    """Re-entry depth is decided at capture time and recorded in
    defect.md frontmatter (re-entry: implement | architect). Only an
    explicit architect re-entry brings the architecture.md +
    breakdown.md chain into the run; otherwise those stages are
    skipped."""
    defect = run_dir / "defect.md"
    if not defect.is_file():
        return False
    return (read_frontmatter(defect) or {}).get("re-entry") == "architect"


def _maintenance_breakdown(run_dir):
    """The breakdown-placement rule: checkboxes live inline in defect.md
    with re-entry: implement, and in breakdown.md with re-entry:
    architect. There is no third option."""
    name = "breakdown.md" if _re_entry_architect(run_dir) else "defect.md"
    return run_dir / name


def _stage_complete(stage, artifact, run_dir):
    if stage == "implement":
        return _all_boxes_checked(run_dir / "breakdown.md")
    if stage == "ux-design":
        return (run_dir / artifact).is_file() or _ux_skipped(run_dir)
    return (run_dir / artifact).is_file()


def _maintenance_stage_complete(stage, artifact, run_dir):
    if stage == "implement":
        return _all_boxes_checked(_maintenance_breakdown(run_dir))
    if stage in ("architect", "decompose"):
        return ((run_dir / artifact).is_file()
                or not _re_entry_architect(run_dir))
    return (run_dir / artifact).is_file()


def next_stage(run_dir):
    """First stage in pipeline order that is not complete. retro.md marks
    the whole run complete regardless of earlier gaps (the protocol's
    run-discovery rule and the router's step 6 both key on it alone).
    Maintenance runs walk their own rows (ADR-0025); every other run
    walks the product/feature table."""
    run_dir = Path(run_dir)
    if (run_dir / "retro.md").is_file():
        return "complete"
    if is_maintenance_run(run_dir):
        rows = MAINTENANCE_STAGE_ARTIFACTS
        complete = _maintenance_stage_complete
    else:
        rows = STAGE_ARTIFACTS
        complete = _stage_complete
    for stage, artifact in rows:
        if not complete(stage, artifact, run_dir):
            return stage
    return "complete"
