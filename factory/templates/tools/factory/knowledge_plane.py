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
