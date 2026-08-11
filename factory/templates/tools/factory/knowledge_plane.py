#!/usr/bin/env python3
"""knowledge_plane: the shared grammar and layout of the knowledge plane
(ADR-0004, ADR-0037) — the typed-ID token grammar, the run-directory
layout, and where a factory tool finds the repo root.

These primitives grew up inside gates.py because its detectors needed
them first, but every dispatch-plane tool reads the same plane:
assembler.py resolves breakdown rows, validator.py maps work orders to
tracker issues, orientation_pack.py bundles cited ADRs, budget_guard.py
and cost_report.py locate the repo — and each imported gates for the
privilege, while label_sync.py carried its own repo_root copy. ADR-0037
gives the plane's grammar one home; gates.py keeps only the detectors.
"""
import re
from pathlib import Path

PRD_TOKEN = re.compile(r"\bPRD-\d{4}\b")
ADR_TOKEN = re.compile(r"\bADR-(\d{4})\b")
WO_TOKEN = re.compile(r"\bWO-\d{4}\b")
# GitHub's issue-closing keywords, with the optional colon form
# ("Closes: #12") and any run of whitespace before the issue number. The
# number is captured: detector B only asks whether a link exists, but
# validator.py asks WHICH issues a PR closes (it is how a merged PR names
# the one work order it implements), and the closing grammar lives here.
CLOSES_TOKEN = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b:?\s+#(\d+)\b",
    re.IGNORECASE)

# A breakdown row is a checkbox bullet line; its work order is its FIRST
# WO token (later tokens are blocking edges). Notes and Accept: sub-bullets
# are prose, never rows. One grammar for the whole dispatch plane:
# validator (row -> tracker issue), assembler (row -> dispatch), and
# orientation_pack (row -> owned block) all read it from here.
# protocol._CHECKBOX (stage completion) and gates.MERGED_ROW (merged-row
# detection) stay separate owners — protocol must not depend on this
# factory seam, and each captures something this one doesn't — but their
# bullet-and-whitespace shape is aligned with this regex; change them
# together or completion counting and dispatch will disagree about the
# same line.
ROW = re.compile(r"^\s*[-*+]\s+\[[ xX]\]\s")


def row_work_order(line):
    """The work order a breakdown row carries: its first WO token, or None
    when the line is not a checkbox row or names no work order."""
    if not ROW.match(line):
        return None
    tokens = WO_TOKEN.findall(line)
    return tokens[0] if tokens else None


# The dispatch mirror's marker on a breakdown row (ADR-0032: the row,
# never the issue, is authoritative). One grammar for both mirror
# directions (ADR-0039): the assembler resolves issue# -> row, the
# validator row -> issue#, each through the accessor below.
TRACKER = re.compile(r"\(tracker:\s*#(\d+)\)")


def row_tracker_issue(line):
    """The issue number a breakdown row mirrors to — its `(tracker: #N)`
    marker — or None when the line is not a checkbox row or carries no
    marker. Sibling of row_work_order: the mirror grammar lives here,
    each caller keeps its own lookup direction."""
    if not ROW.match(line):
        return None
    match = TRACKER.search(line)
    return int(match.group(1)) if match else None


# A row merged before the cost ledger was born carries this trailing
# annotation (ADR-0043): the exemption is a fact about a work order, so
# it lives on the row it describes, never as a repo-specific list in a
# mirrored module. The grammar lives here with its row siblings; the
# skip policy (detector G exempts annotated rows from its
# merged-row-must-be-recorded check) stays with gates.py.
PRE_LEDGER_MARK = "(pre-ledger)"
_PRE_LEDGER = re.compile(re.escape(PRE_LEDGER_MARK) + r"\s*$")


def row_pre_ledger(line):
    """Does this breakdown row carry the (pre-ledger) annotation
    (ADR-0043)? The annotation is written TRAILING — the mark ends the
    row, after the tracker mirror — so only a checkbox row ending with
    it is annotated. The mark as mid-row prose (a row about the
    annotation) marks nothing, and a non-row line never does."""
    return bool(ROW.match(line)) and bool(_PRE_LEDGER.search(line))


# A row's own declared metadata. `size:` is the cost band (factory_config
# resolves it to a dollar budget) and `blocked by:` is the dependency edge
# the ROW comment above refers to as "later tokens". Both are clause-scoped
# so the trailing `(PRD-...)` and `(tracker: #N)` markers can never be read
# as part of them.
DONE_ROW = re.compile(r"^\s*[-*+]\s+\[x\]", re.IGNORECASE)
SIZE = re.compile(r"\bsize:\s*([SML])\b")
BLOCKED_BY = re.compile(r"\bblocked by:\s*([^(]*)")


def row_size(line):
    """The row's declared size band ("S"/"M"/"L"), or None.

    factory_config.resolve_budget turns it into the dollar budget, so a
    caller planning a batch can price the batch before running it rather
    than discovering the cost afterwards (ADR-0034).
    """
    if not ROW.match(line):
        return None
    match = SIZE.search(line)
    return match.group(1) if match else None


def row_blockers(line):
    """The work orders this row declares it is blocked by.

    Read from the `blocked by:` clause only — NOT "every WO token after
    the first", which would swallow a work order merely mentioned in the
    row's prose and park the row forever. An em-dash (the written form of
    "nothing") yields an empty list, same as an absent clause.
    """
    if not ROW.match(line):
        return []
    match = BLOCKED_BY.search(line)
    return WO_TOKEN.findall(match.group(1)) if match else []


def row_done(line):
    """Whether a breakdown row is checked off.

    gates.MERGED_ROW is a separate, older owner of the same bullet shape
    and stays that way: it additionally excludes ADR-0043 pre-ledger rows,
    which is detector G's rule and not the row grammar's. Same alignment
    caveat as protocol._CHECKBOX — change the bullet shape in one and the
    others must move with it.
    """
    return bool(DONE_ROW.match(line))


def run_dirs(root):
    """Candidate run directories per the pipeline protocol."""
    dirs = [root / "docs"]
    for parent in ("features", "fixes"):
        base = root / "docs" / parent
        if base.is_dir():
            dirs.extend(p for p in sorted(base.iterdir()) if p.is_dir())
    return [d for d in dirs if d.is_dir()]


def breakdown_files(root):
    """(breakdown path, its lines) per run that has a breakdown.md.

    The layout walk in one place: every dispatch-plane reader of
    work-order rows — the assembler, the validator, orientation_pack,
    and gates' detectors — opens the same files in the same run order.
    Row and slice grammar stay with each caller (ADR-0037: this
    concentrates layout knowledge, not row-reading policy).
    """
    for run in run_dirs(root):
        breakdown = run / "breakdown.md"
        if breakdown.is_file():
            yield breakdown, breakdown.read_text(
                encoding="utf-8").splitlines()


def repo_root():
    """Nearest ancestor containing .git (dir or worktree file): correct at
    the factory repo root and stamped at tools/factory/ in a product repo."""
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    return here
