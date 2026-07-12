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
# Maintenance runs enter at a capture step (ADR-0025). Capture is a
# stage skill — it owns defect.md and the router routes to it — but it
# sits outside the product/feature spine, so it is listed separately.
MAINTENANCE_STAGES = ["capture"]
# implement's artifact is code itself; every other stage ships a template
TEMPLATED_STAGES = [s for s in STAGES + MAINTENANCE_STAGES
                    if s != "implement"]
# Utility skills act on work surrounding the pipeline (ADR-0023); they
# have no stage artifact and the router never routes to them, but they are
# full skills for install, lint, and trigger-eval purposes.
UTILITY_SKILLS = ["address-pr-review", "autorun", "factory-init", "mermaid"]
ALL_SKILLS = ["next"] + STAGES + MAINTENANCE_STAGES + UTILITY_SKILLS

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
    what a missing block means for them. Values may be `|` literal block
    scalars (following indented lines joined with newlines); CRLF files
    are normalized before matching.
    """
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = _FRONTMATTER.match(text)
    if not match:
        return None
    fields = {}
    key = None
    block_lines = None
    for line in match.group(1).splitlines():
        if block_lines is not None and (line.startswith("  ") or not line.strip()):
            block_lines.append(line[2:])
            continue
        if key is not None and block_lines is not None:
            fields[key] = "\n".join(block_lines).rstrip("\n")
        key = None
        block_lines = None
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if value == "|":
            block_lines = []
        else:
            fields[key] = value
    if key is not None and block_lines is not None:
        fields[key] = "\n".join(block_lines).rstrip("\n")
    return fields


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


# The seed-backlog entry grammar (ADR-0029): docs/backlog.md is an
# advisory bullet list, one seed per line, each carrying its origin
# run-ref and optionally the run that claimed it. Only `- ` bullets are
# held to the grammar; the run-ref forms mirror the protocol doc's
# "Seed backlog (optional)" section.
_BACKLOG_RUN_REF = re.compile(
    r"product|feature:[a-z0-9-]+|maintenance:[a-z0-9-]+"
    r"|session:\d{4}-\d{2}-\d{2}")
_BACKLOG_ENTRY = re.compile(
    r"- (?P<text>.+?) \(from: (?P<origin>[^()]+)\)"
    r"(?: \(claimed: (?P<claimed>[^()]+)\))?")


def _backlog_refs(match):
    """The (marker, run-ref) pairs a matched entry carries; claimed may
    be absent."""
    return [(marker, match.group(marker))
            for marker in ("origin", "claimed")
            if match.group(marker) is not None]


def parse_backlog(text):
    """Parse backlog text into entries {text, origin, claimed} (claimed
    is None on unclaimed seeds). Never raises: malformed bullets and
    non-bullet lines are skipped — check_backlog is where they become
    problems."""
    entries = []
    for line in text.splitlines():
        match = _BACKLOG_ENTRY.fullmatch(line)
        if not match or not all(_BACKLOG_RUN_REF.fullmatch(ref)
                                for _, ref in _backlog_refs(match)):
            continue
        entries.append({"text": match.group("text"),
                        "origin": match.group("origin"),
                        "claimed": match.group("claimed")})
    return entries


def check_backlog(text):
    """Problem strings (`backlog: line N: ...`) for every bullet line
    that breaks the entry grammar; [] when conformant. Non-bullet lines
    (header, blanks, prose) are ignored, and malformed input yields
    problem strings, never exceptions."""
    problems = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.startswith("- "):
            continue
        match = _BACKLOG_ENTRY.fullmatch(line)
        if not match:
            problems.append(f"backlog: line {number}: entry does not "
                            "match '- <seed text> (from: <run-ref>)'")
            continue
        problems.extend(
            f"backlog: line {number}: invalid run-ref {ref!r}"
            for _, ref in _backlog_refs(match)
            if not _BACKLOG_RUN_REF.fullmatch(ref))
    return problems
