#!/usr/bin/env python3
"""Factory gate detectors (PRD-0001; ADR-0032, ADR-0033, ADR-0034).

Offline, gating checks over the knowledge plane, following the same
conventions as lint.py: every checker takes the repo root and returns
label-prefixed problem strings; the CLI prints them and exits nonzero.
Lettered detectors (audit-evals.py style, letters shared with the
ai-tooling suite where the rule is the same idea):

  A WO-CITATION    — every breakdown work-order row cites a PRD id
  B PR-TRACEABILITY — PR body carries a WO id and a closing keyword
                     (event-payload; SKIP locally)
  C LINK-INTEGRITY — every PRD-####/ADR-####/WO-#### token resolves;
                     duplicate PRD ids fail
  D BLUEPRINT-DRIFT — the approved blueprint (docs/adr) is self-consistent:
                     every ADR declares a known status and is indexed with
                     that status in docs/adr/README.md, and no artifact
                     outside docs/adr builds on a superseded decision
  E SCAFFOLD-SYNC  — factory/manifest.json checksums match the template
                     payload (no hand-edited mirrors)
  F CONFIG-SHAPE   — factory config parses and every field is a valid
                     token (budgets, routing, caps)
  G COST-LEDGER    — docs/factory/costs.jsonl lines carry the ADR-0034
                     fields and every merged (checked) work-order row has
                     one; an absent ledger is silent (no runs recorded yet)
  H EVIDENCE-HONESTY — every verification.md section that asserts a LABELLED
                     verdict (Result/Verdict/Outcome/Status) shows literal
                     fenced output or discloses NOT RUN, in its OWN section
                     scope (an appendix fence vouches for nothing; a scoped
                     hedge is not a disclaimer; there is no roll-up excuse);
                     and an artifact with neither output nor a written
                     NOT-RUN disclaimer anywhere fails outright
  I STALENESS      — no knowledge-plane doc links to a path that no longer
                     exists on disk

The letter namespace does not end at I. Detector L (LABEL-SYNC) is
network-side and lives in label_sync.py, driven by scheduled sweeps —
network calls stay out of this offline gate — and J/K are unclaimed.
DETECTORS (beside CHECKERS below) is the full roster.

`--selftest` runs the checkers against fixture trees and exits nonzero
on a failing assertion. Both run in CI (validator.yml, via `make check`)
on every push/PR.

The knowledge plane's shared grammar (typed-ID tokens, run_dirs,
repo_root) lives in knowledge_plane.py, and the cost ledger's shape in
cost_ledger.py (ADR-0037) — this module keeps only the detectors.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import cost_ledger
import factory_config
from cli import read_event
from cost_ledger import COST_LEDGER
from knowledge_plane import (ADR_TOKEN, CLOSES_TOKEN, PRD_TOKEN, WO_TOKEN,
                             breakdown_files, repo_root, run_dirs)
from protocol import read_frontmatter
# Not every factory PR implements a work order: a governance or chore PR
# (the merge-auth removal in #139, a docs fix) closes an issue but maps to no
# `WO-####`. Such a PR declares that EXPLICITLY — the same "declared, never
# assumed" rule the architecture tree-claims and the review-token provenance
# follow — and the declaration owes a reason, so a bare marker waives nothing.
# A work-order PR that simply omits its WO still fails: only an explicit,
# reasoned "no work order" claim exempts, and claiming it falsely is a
# deliberate lie the same as any other gamed gate. The Closes-#N audit link is
# still required in both cases. (ADR-0033, amended: merge stays gated, but the
# gate no longer assumes every PR is a work order.)
NO_WO_DECLARATION = re.compile(r"\bno[\s-]+work[\s-]+order\b[ \t]*:[ \t]*\S",
                               re.IGNORECASE)

CONFIG_ROUTES = ("mechanical", "implementation", "architecture_review")

# ADR status vocabulary (docs/adr/README.md), as a status head plus an
# optional free-text annotation: "accepted (shipped by ...)" is accepted.
# Only full supersession retires a decision — "superseded in part by" and
# "amended by" leave the ADR live, so citing it is not drift.
ADR_STATUS = re.compile(
    r"^(accepted|provisional"
    r"|(?P<retired>superseded by ADR-(?P<by>\d{4}))"
    r"|superseded in part by ADR-\d{4}"
    r"|amended by ADR-\d{4})"
    r"(\s*\(.*\))?$")
ADR_STATUS_LINE = re.compile(r"^-\s*Status:\s*(.+?)\s*$")
# An index row: | [0032](0032-slug.md) | Decision | status |
ADR_INDEX_ROW = re.compile(
    r"^\|\s*\[(?P<num>\d{4})\]\((?P<file>[^)]+)\)\s*\|[^|]*\|"
    r"\s*(?P<status>[^|]*?)\s*\|")

# A merged work order is a checked breakdown row (ADR-0004: the artifact,
# not the tracker, is the state). Bullet-and-whitespace shape aligned with
# knowledge_plane.ROW; separate owner because only the checked form counts.
MERGED_ROW = re.compile(r"^\s*[-*+]\s+\[x\]", re.IGNORECASE)

# A row merged before the cost ledger was born carries this annotation
# (ADR-0043); G's merged-row-must-be-recorded check skips it. The
# exemption lives on the row it describes — a repo-specific list in this
# mirrored module would leak one repo's WO ids into every stamped repo.
PRE_LEDGER_MARK = "(pre-ledger)"

# Markdown links to repo paths; URLs, autolinks and bare anchors are not.
MD_LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)>\s]+)>?")
URL_TARGET = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")

# H reads verification.md the way the verify skill writes it: markdown
# headings delimit criteria, a LABELLED line asserts the verdict, fenced
# blocks carry the literal output, and prose may disclose a check as NOT RUN.
# Every one of those signals is read IN THE SECTION THAT CARRIES IT — the
# rule H enforces is per-criterion, so its evidence test must be too.
HEADING_LINE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
# CommonMark's other heading syntax: a title underlined with === or ---.
# GitHub renders it identically to ATX, so a splitter that reads only ATX is
# blind to sections a human reviewer plainly sees (the #147 bypass). The `---`
# underline is ambiguous — it also writes a thematic break and closes the
# frontmatter fence — so a title must be a non-blank line that is not itself a
# list item, block quote, or underline.
SETEXT_UNDERLINE = re.compile(r"^\s{0,3}(?:=+|-+)\s*$")
NOT_A_SETEXT_TITLE = re.compile(r"^\s{0,3}(?:[-*+>]|\d+[.)])\s")
# Only a LABELLED verdict line asserts a verdict. The label is not just
# "Result": a criterion is just as asserted under "Verdict:", "Outcome:",
# "Conclusion:", "Assessment:", "Finding:" — so the rule engages on the whole
# verdict-noun vocabulary (case-insensitive, with an optional list bullet and
# bold markers, and a non-empty value). A four-label whitelist was itself the
# gate's escape hatch: a lying section only had to relabel its verdict line to
# become invisible, which is the same "rename it and the gate goes quiet" move
# the roll-up excuse allowed. The vocabulary below is the closed set of words
# that ASSERT A JUDGEMENT. Words that introduce an INPUT or an aside —
# "Check:", "Command:", "Note:", "Caveat:", "Evidence:" — are deliberately NOT
# verdicts: they carry no claim, and reading them as claims false-positives on
# every honest artifact that documents what it ran.
#
# Nothing else asserts anything. Unlabelled prose and heading text are read
# as prose: an author may open a note with "Done.", title a section "all
# checks pass", and — decisively — write TEMPLATE.md's `## Summary` as the
# narrative roll-up it is meant to be, all without owing output. Reading
# prose and headings as verdicts is what forced the previous roll-up EXCUSE
# ("a section named Summary/Results/… need not evidence itself, provided
# some other section does"), and that excuse was the gate's own escape
# hatch: rename the lying section, or park one throwaway evidenced leaf
# beside it, and the gate went quiet. With only labelled lines asserting, no
# excuse is needed and none exists — every labelled verdict is backed IN ITS
# OWN SECTION, wherever it is written.
# The leading-marker class is deliberately wide. A verdict is just as asserted
# under a blockquote (`> Result: PASS`) or an ordered-list item (`1. Result:
# PASS`) as under a `-` bullet, and GitHub renders all three as visible verdict
# text — so a marker-only whitelist was itself an escape hatch (an independent
# review smuggled a fake PASS past the `-*+`-only form under `>` and `1.`).
# Any run of list/quote markers may lead the line; the verdict noun is what
# makes it a verdict, not the marker. Two more wrappers GitHub renders as a
# visible verdict join the leading class (#151): a table cell's leading pipe
# (`| Result: PASS |`, a row a human reads as PASS) and an inline `<summary>`
# open tag (`<summary>Result: PASS</summary>`, an always-visible clickable
# verdict). Both close with a trailing delimiter — ` |` / `</summary>` — that
# the value capture drops OUTSIDE the group, so `_is_disclosure` still reads
# the verdict's true head (a table-cell `NOT VERIFIED` still discloses).
RESULT_LINE = re.compile(
    r"^\s*(?:(?:[-*+>]|\d+[.)]|\||<summary[^>]*>)\s*)*"
    r"\**\s*(?:result|verdict|outcome|status"
    r"|conclusion|assessment|finding|determination|evaluation|judge?ment"
    r"|disposition|decision|ruling|appraisal)\**"
    r"\s*:\s*(\S.*?)\s*(?:\|\s*|</summary>\s*)?$",
    re.IGNORECASE)
# YAML frontmatter is METADATA, not the author's assertion. `status: draft` is
# a stage field, and reading it as a labelled verdict both false-positived on
# an honest artifact ("(untitled)" asserts draft) and — worse — parked a
# `results` entry in the artifact, which switched the artifact-wide backstop
# off entirely. The frontmatter block is skipped, not scanned.
FRONTMATTER_FENCE = re.compile(r"^---\s*$")
# CommonMark fences, tracked as a stack of one — NOT a parity toggle. An
# opening fence records its marker character and length; only a fence of the
# SAME character, AT LEAST as long, and carrying NO info string closes it. So
# evidence that quotes markdown (a ```bash block inside a ~~~ block, a ```
# inside a ````) stays content instead of desyncing the scanner and silently
# swallowing every criterion below it, and an unclosed fence is reported.
# Deliberate deviation from CommonMark: the indent is unbounded, because
# verification evidence is nested under `- Evidence:` list items, where the
# fence is indented to the item's content column. We do not track containers,
# and false-positiving on honest nested evidence is the worse error.
FENCE_OPEN = re.compile(r"^\s*(?P<marker>`{3,}|~{3,})(?P<info>.*)$")
FENCE_CLOSE = re.compile(r"^\s*(?P<marker>`{3,}|~{3,})[ \t]*$")
# The disclaimer must be explicit, and it must be WRITTEN: read from body
# text, never from a heading. TEMPLATE.md ships a `## Not verified` slot in
# EVERY artifact, so a heading that counted as a disclosure would let the
# template alone excuse a wholly fabricated, zero-output artifact. What
# discloses a gap is what the author writes under the slot, not the slot.
# A scoped hedge ("not tested on Windows", "not verified in Safari") admits
# the check DID run, just not everywhere — the negative lookahead drops it so
# it cannot disarm the rule the way an unqualified "NOT RUN" legitimately does.
NOT_RUN_TOKEN = re.compile(
    r"\bnot[\s-]+(?:run|ran|verified|executed|checked|tested|attempted)\b"
    r"(?!\s+(?:on|in|for|under|with|against|across|when|beyond|outside)\b)",
    re.IGNORECASE)
# A verdict that claims nothing IS the disclosure and owes no output. Every
# other verdict is a CLAIM and owes literal evidence in its own section — and
# a disclosure sitting NEXT TO a claim buys it nothing. That distinction is
# what stops "(the retry path was not run)" from being a two-word licence to
# fabricate any verdict: a section's prose "not run" disarms nothing it does
# not itself claim. (Body prose still counts for the artifact-wide backstop:
# an artifact that ran nothing and says so is honest.)
#
# The test is ANCHORED at the head of the verdict, never a substring search.
# Searching the whole value let a claim disarm ITSELF by appending a hedge —
# "PASS - every criterion met, full suite green (soak test not run)" asserted
# PASS, showed nothing, and passed in silence. What a verdict asserts is its
# HEAD: lead with a disclosure and you have disclosed; lead with PASS and you
# have claimed, whatever you append. A trailing reason is welcome — an honest
# "NOT RUN — the CI runner was offline" is still a disclosure — and a scoped
# hedge ("not tested on Windows") is still not one, because it concedes the
# check DID run: the preposition lookahead drops it here exactly as it does in
# the body scan.
DISCLOSURE_VERDICT = re.compile(
    r"^(?:n/?a|skip(?:ped)?|defer(?:red)?|untested|unverified|pending|todo|tbd"
    r"|not[\s-]+(?:run|ran|verified|executed|checked|tested|attempted)"
    r"(?!\s+(?:on|in|for|under|with|against|across|when|beyond|outside)\b))"
    r"(?![\w/-])",
    re.IGNORECASE)
# Emphasis and brackets are formatting, not claim: `**NOT RUN**` and `(N/A)`
# are the disclosures they look like, so the head is read past them.
VERDICT_LEAD = re.compile(r"^[\s*_`\"'“‘([]+")
# Unfilled TEMPLATE filler is not output — matched by its filler TEXT, not by
# the shape `<...>`. That shape is also real evidence (a DOM dump's `<html>`,
# a Python repr like `<class 'app.models.User'>`), and discarding it
# false-positived on authors who had pasted exactly what H asks for.
PLACEHOLDER_TEXT = (r"paste|actual\s+output|fill[\s-]*in|to[\s-]?do|tbd|xxx"
                    r"|insert|example\s+output|output\s+here|your\s")
PLACEHOLDER_LINE = re.compile(
    r"^\s*<\s*(?:" + PLACEHOLDER_TEXT + r")[^>]*>\s*$", re.IGNORECASE)
# architecture.md is a blueprint too (#142). D stayed green while a PR added a
# root Makefile and deleted checks.yml, leaving architecture.md asserting the
# opposite of the tree it describes. A doc that describes the tree is
# checkable against the tree, and a doc that has stopped describing it is
# stale — the finding is the drift, not the file.
#
# The hard part is that architecture.md describes TWO trees: this repo, and
# the repo the payload stamps. It also names files that are PLANNED and do not
# exist yet (a roadmap line naming `validator.yml` before WO-0004 lands). So
# "every path it mentions must exist" is not the rule — it would false-positive
# on an honest doc, which is the failure that killed two attempts at detector
# H. Only two things are read as claims about the CURRENT tree:
#
#   1. PROSE, on a CLOSED keyword vocabulary, anchored so that the code span
#      ends a clause. "there is no `Makefile`," asserts absence; "no `gates.py`
#      change is needed" modifies a NOUN and asserts nothing. "`X` exists here"
#      asserts presence, and "here" is the doc's OWN word for "in this repo"
#      (it writes "no `Makefile` ... here", "`.github/CODEOWNERS` exists here")
#      — which is exactly what separates a claim about this tree from a claim
#      about a stamped one. Missing a hedged claim is the safe error; firing on
#      an honest sentence is not.
#   2. A DECLARED claim block, which is the only way to pin a presence claim
#      that prose states behaviourally ("`checks.yml` runs lint..." asserts the
#      file exists, but no keyword says so). Declaring it follows the same rule
#      the review token's provenance does: what is not declared is not assumed.
ARCH_ABSENT_PROSE = re.compile(
    r"\bno\s+`(?P<path>[^`\n]+)`(?:\s+here)?\s*(?=[,.;:)]|$)")
ARCH_EXISTS_PROSE = re.compile(r"`(?P<path>[^`\n]+)`\s+exists\s+here\b")
ARCH_CLAIMS_FENCE = re.compile(r"^\s*```\s*tree-claims\s*$")
ARCH_FENCE = re.compile(r"^\s*(?:```|~~~)")
ARCH_CLAIM = re.compile(
    r"^\s*(?P<verb>exists|absent)\s*:\s*(?P<path>\S+)\s*$", re.IGNORECASE)
# A claim must name a plain repo path. A glob or a `..` is not resolvable
# against the tree, and quietly resolving it anyway is how a detector starts
# reporting things it did not check.
ARCH_PLAIN_PATH = re.compile(r"^[\w.@/-]+$")


def _scannable_files(root):
    docs = root / "docs"
    files = sorted(docs.rglob("*.md")) if docs.is_dir() else []
    context = root / "CONTEXT.md"
    if context.is_file():
        files.append(context)
    return files


def check_wo_citation(root):
    """A: a work-order row that cites no PRD section is untraceable scope."""
    problems = []
    for breakdown, lines in breakdown_files(root):
        for lineno, line in enumerate(lines, 1):
            wo = WO_TOKEN.search(line)
            if wo and not PRD_TOKEN.search(line):
                rel = breakdown.relative_to(root)
                problems.append(
                    f"A: {rel}:{lineno} work-order row {wo.group(0)}"
                    " cites no PRD id")
    return problems


def pr_event(env):
    """(the pull_request payload, error): the PR this CI run is about, read
    from the event file (cli.read_event, ADR-0042). (None, None) outside a
    PR run — every caller SKIPs silently there. Callers label the error
    string themselves, so this stays detector-agnostic (validator.py is the
    second caller)."""
    event, error = read_event(env)
    if event is None:
        return None, error
    pr = event.get("pull_request")
    return (pr if isinstance(pr, dict) else None), None


def check_pr_traceability(root, env=None):
    """B: a PR whose body cites no work order and closes no issue breaks
    the audit trail from code back to scope. Reads the CI event payload;
    SKIPs silently outside a PR run. A PR that implements no work order may
    say so explicitly (`No work order: <reason>`) to waive the WO-id
    requirement; the Closes-#N link is required regardless."""
    if env is None:
        env = os.environ
    pr, error = pr_event(env)
    if error:
        return [f"B: {error}"]
    if pr is None:
        return []
    body = pr.get("body") or ""
    problems = []
    if not WO_TOKEN.search(body) and not NO_WO_DECLARATION.search(body):
        problems.append("B: PR body cites no work-order id")
    if not CLOSES_TOKEN.search(body):
        problems.append("B: PR body has no Closes #N link")
    return problems


def collect_prd_ids(root):
    """Map PRD id -> list of prd.md paths declaring it in frontmatter."""
    ids = {}
    for run in run_dirs(root):
        prd = run / "prd.md"
        if not prd.is_file():
            continue
        fields = read_frontmatter(prd) or {}
        prd_id = fields.get("id")
        if prd_id:
            ids.setdefault(prd_id, []).append(prd.relative_to(root))
    return ids


def collect_wo_rows(root):
    """Set of WO tokens that appear in any breakdown.md row."""
    rows = set()
    for _, lines in breakdown_files(root):
        for line in lines:
            rows.update(WO_TOKEN.findall(line))
    return rows


def check_link_integrity(root):
    """C: typed cross-link tokens must resolve; duplicate PRD ids fail."""
    problems = []
    prd_ids = collect_prd_ids(root)
    for prd_id, paths in sorted(prd_ids.items()):
        if len(paths) > 1:
            listed = ", ".join(str(p) for p in paths)
            problems.append(f"C: duplicate PRD id {prd_id} in {listed}")
    adr_dir = root / "docs" / "adr"
    adr_numbers = set()
    if adr_dir.is_dir():
        for path in adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md"):
            adr_numbers.add(path.name[:4])
    wo_rows = collect_wo_rows(root)
    for path in _scannable_files(root):
        rel = path.relative_to(root)
        in_breakdown = path.name == "breakdown.md"
        for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            for token in PRD_TOKEN.findall(line):
                if token not in prd_ids:
                    problems.append(
                        f"C: {rel}:{lineno} dangling {token}"
                        " (no prd.md declares this id)")
            for number in ADR_TOKEN.findall(line):
                if number not in adr_numbers:
                    problems.append(
                        f"C: {rel}:{lineno} dangling ADR-{number}"
                        " (no docs/adr file)")
            if not in_breakdown:
                for token in WO_TOKEN.findall(line):
                    if token not in wo_rows:
                        problems.append(
                            f"C: {rel}:{lineno} dangling {token}"
                            " (no breakdown row)")
    return problems


def _adr_status(path):
    """(lineno, status text) of an ADR's Status line; (0, None) if absent."""
    for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1):
        match = ADR_STATUS_LINE.match(line)
        if match:
            return lineno, match.group(1)
    return 0, None


def _status_head(text):
    """The decision state alone, annotation stripped; None if unknown."""
    match = ADR_STATUS.match(text or "")
    return match.group(1) if match else None


def _claim_path(root, raw):
    """(resolved path, problem-suffix). A claim must name a plain repo path;
    anything else is refused rather than resolved."""
    cleaned = raw.strip().rstrip("/")
    if not cleaned or ".." in cleaned.split("/") \
            or not ARCH_PLAIN_PATH.match(cleaned):
        return None, (f"tree claim '{raw}' is not a plain repo path"
                      " (no globs, no '..')")
    return root / cleaned, None


def _declared_claims(root, rel, lineno, line):
    """Problems for one line inside a ```tree-claims block."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return []
    claim = ARCH_CLAIM.match(line)
    if not claim:
        return [f"D: {rel}:{lineno} unreadable tree claim '{stripped}'"
                " (expected 'exists: <path>' or 'absent: <path>')"]
    raw = claim.group("path")
    path, refused = _claim_path(root, raw)
    if refused:
        return [f"D: {rel}:{lineno} {refused}"]
    name = raw.strip().rstrip("/")
    exists = path.exists()
    if claim.group("verb").lower() == "exists" and not exists:
        return [f"D: {rel}:{lineno} claims {name} exists, but it does not"
                " (architecture.md is stale)"]
    if claim.group("verb").lower() == "absent" and exists:
        return [f"D: {rel}:{lineno} claims {name} is absent, but it exists"
                " (architecture.md is stale)"]
    return []


def _prose_claims(root, rel, lineno, line):
    """Problems for the existence claims a prose line makes about this tree.
    An unresolvable path (a glob, a `make check` command span) is not a claim
    and is skipped — in prose, silence is the safe reading."""
    problems = []
    for match in ARCH_ABSENT_PROSE.finditer(line):
        raw = match.group("path")
        path, refused = _claim_path(root, raw)
        if path is not None and path.exists():
            problems.append(
                f"D: {rel}:{lineno} says there is no {raw.rstrip('/')}, but"
                " it exists (architecture.md is stale)")
    for match in ARCH_EXISTS_PROSE.finditer(line):
        raw = match.group("path")
        path, refused = _claim_path(root, raw)
        if path is not None and not path.exists():
            problems.append(
                f"D: {rel}:{lineno} says {raw.rstrip('/')} exists, but it"
                " does not (architecture.md is stale)")
    return problems


def _architecture_drift(root):
    """D: every file architecture.md names as present or absent in THIS repo
    must agree with the tree. Fenced examples are inert — a doc quoting a
    claim is not making it — except for the ```tree-claims block, which is
    where a claim prose can only state behaviourally gets declared."""
    problems = []
    for run in run_dirs(root):
        arch = run / "architecture.md"
        if not arch.is_file():
            continue
        rel = arch.relative_to(root)
        fence = None  # None | "tree-claims" | "other"
        for lineno, line in enumerate(
                arch.read_text(encoding="utf-8").splitlines(), 1):
            if fence is not None:
                if ARCH_FENCE.match(line):
                    fence = None
                elif fence == "tree-claims":
                    problems.extend(
                        _declared_claims(root, rel, lineno, line))
                continue
            if ARCH_CLAIMS_FENCE.match(line):
                fence = "tree-claims"
                continue
            if ARCH_FENCE.match(line):
                fence = "other"
                continue
            problems.extend(_prose_claims(root, rel, lineno, line))
    return problems


def check_blueprint_drift(root):
    """D: docs/adr is the approved blueprint (ADR-0033's second gate). It
    must describe itself consistently — every ADR carries a known status
    and is indexed with that status — and no artifact outside docs/adr may
    build on a decision the blueprint has retired (ADR-0032: disagreement
    resolves in the knowledge plane's favour).

    A run's architecture.md is a blueprint too, and it drifts the same way:
    it goes on describing a tree that has moved out from under it (#142). So
    a file it names as present or absent in this repo must agree with the
    tree, on the same principle — the doc does not get to disagree with what
    is there."""
    problems = _architecture_drift(root)
    adr_dir = root / "docs" / "adr"
    if not adr_dir.is_dir():
        return problems
    statuses = {}  # ADR number -> status text (None when unusable)
    retired = {}   # ADR number -> the ADR number that superseded it
    for path in sorted(adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md")):
        rel = path.relative_to(root)
        number = path.name[:4]
        lineno, text = _adr_status(path)
        statuses[number] = None
        if text is None:
            problems.append(f"D: {rel} declares no Status line")
            continue
        match = ADR_STATUS.match(text)
        if not match:
            problems.append(f"D: {rel}:{lineno} unknown ADR status {text!r}")
            continue
        statuses[number] = text
        if match.group("retired"):
            retired[number] = match.group("by")

    index = adr_dir / "README.md"
    if statuses and not index.is_file():
        problems.append("D: docs/adr/README.md is missing"
                        " (ADR files present, no blueprint index)")
    elif index.is_file():
        rows = {}
        for lineno, line in enumerate(
                index.read_text(encoding="utf-8").splitlines(), 1):
            match = ADR_INDEX_ROW.match(line)
            if not match:
                continue
            number, filename = match.group("num"), match.group("file")
            rows[number] = (lineno, match.group("status"))
            if not (adr_dir / filename).is_file():
                problems.append(
                    f"D: docs/adr/README.md:{lineno} index row ADR-{number}"
                    f" links to missing file {filename}")
        for number, text in sorted(statuses.items()):
            if number not in rows:
                problems.append(
                    f"D: docs/adr/README.md has no index row for"
                    f" ADR-{number}")
                continue
            lineno, indexed = rows[number]
            if text is None:  # already flagged; nothing to compare against
                continue
            if _status_head(indexed) != _status_head(text):
                problems.append(
                    f"D: docs/adr/README.md:{lineno} ADR-{number} index"
                    f" status {indexed!r} does not match the file's {text!r}")

    for path in _scannable_files(root):
        if adr_dir in path.parents:
            continue
        rel = path.relative_to(root)
        for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            for number in ADR_TOKEN.findall(line):
                if number in retired:
                    problems.append(
                        f"D: {rel}:{lineno} cites ADR-{number}, superseded"
                        f" by ADR-{retired[number]} (blueprint drift)")
    return problems


def merged_wo_rows(root):
    """(breakdown path, lineno, WO token) for every checked breakdown row —
    the artifact-side record that a work order merged (ADR-0004). Rows
    annotated (pre-ledger) are excluded: they merged before the ledger
    existed and G owes them no ledger line (ADR-0043)."""
    rows = []
    for breakdown, lines in breakdown_files(root):
        rel = breakdown.relative_to(root)
        for lineno, line in enumerate(lines, 1):
            wo = WO_TOKEN.search(line)
            if (MERGED_ROW.match(line) and wo
                    and PRE_LEDGER_MARK not in line):
                rows.append((rel, lineno, wo.group(0)))
    return rows


def check_cost_ledger(root):
    """G: every run appends {wo, run_id, model, tokens, cost, outcome} to
    the append-only docs/factory/costs.jsonl, and a merged work order with
    no ledger line is a gating finding (ADR-0034). An absent ledger is
    silent, not a finding: the ledger is created by the first run that
    records into it, so a freshly stamped repo has no runs to account for
    — the rule bites once the ledger exists.

    The line grammar itself is cost_ledger.parse — the same rule the
    weekly report reads with (ADR-0037), so the two cannot diverge. What
    stays here is G's own work: the cross-checks between ledger and
    breakdown (a recorded wo must have a row; a merged row must be
    recorded)."""
    ledger = root / COST_LEDGER
    if not ledger.is_file():
        return []
    try:
        text = ledger.read_text(encoding="utf-8")
    except OSError as err:
        return [f"G: cannot read {COST_LEDGER}: {err}"]
    problems = []
    wo_rows = collect_wo_rows(root)
    recorded = set()
    for lineno, entry, suffixes in cost_ledger.parse(text):
        problems.extend(f"G: {COST_LEDGER}:{lineno} {suffix}"
                        for suffix in suffixes)
        wo = cost_ledger.wo_token(entry) if entry is not None else None
        if wo:
            recorded.add(wo)
            if wo not in wo_rows:
                problems.append(f"G: {COST_LEDGER}:{lineno} wo {wo}"
                                " has no breakdown row")
    for rel, lineno, wo in merged_wo_rows(root):
        if wo not in recorded:
            problems.append(f"G: {rel}:{lineno} merged work order {wo} has"
                            f" no line in {COST_LEDGER}")
    return problems


def check_staleness(root):
    """I: a doc that links to a path which no longer exists on disk is
    stale — the knowledge plane moved and the doc did not. Deliberately
    filesystem-shaped, not time-shaped: a detector must be deterministic
    and hermetic, which "older than the code it describes" is not."""
    problems = []
    for path in _scannable_files(root):
        rel = path.relative_to(root)
        for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            for target in MD_LINK.findall(line):
                if URL_TARGET.match(target) or target.startswith("#"):
                    continue
                cleaned = target.split("#", 1)[0]
                if not cleaned:
                    continue
                base = root if cleaned.startswith("/") else path.parent
                if not (base / cleaned.lstrip("/")).exists():
                    problems.append(
                        f"I: {rel}:{lineno} stale link {cleaned}"
                        " (no such path)")
    return problems


def manifest_files(root):
    """{rel: sha256} for every file in the template payload, keyed
    relative to factory/ in posix form — the ONE statement of the
    manifest's walk-hash-key grammar. update_manifest (factory_init.py)
    writes exactly this map and check_scaffold_sync diffs the manifest
    against it, so writer and verifier cannot diverge — the same
    discipline detector G borrows from cost_ledger.parse."""
    payload = root / "factory" / "templates"
    if not payload.is_dir():
        return {}
    return {p.relative_to(root / "factory").as_posix():
            hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(payload.rglob("*")) if p.is_file()}


def check_scaffold_sync(root):
    """E: the template payload must match its checksum manifest exactly."""
    manifest_path = root / "factory" / "manifest.json"
    if not manifest_path.is_file():
        return ["E: missing factory/manifest.json"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return [f"E: factory/manifest.json is not valid JSON: {err}"]
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        return ["E: factory/manifest.json has no files map"]
    problems = []
    actual = manifest_files(root)
    for rel, expected in sorted(files.items()):
        if rel not in actual:
            problems.append(f"E: manifest lists missing file factory/{rel}")
        elif actual[rel] != expected:
            problems.append(
                f"E: factory/{rel} does not match its manifest checksum"
                " (re-run manifest update, never hand-edit)")
    problems += [f"E: factory/{rel} is not in the manifest"
                 for rel in sorted(actual) if rel not in files]
    return problems


def check_config_shape(root):
    """F: factory config must parse and every field be a valid token."""
    candidates = [root / "factory" / "templates" / "factory.json",
                  root / ".github" / "factory.json"]
    problems = []
    for path in candidates:
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            problems.append(f"F: {rel} is not valid JSON: {err}")
            continue
        # key-set completeness is this gate's whole-shape concern; the
        # field-VALUE grammar is factory_config.config_problems — one
        # home shared with the runtime accessors, so the gate can never
        # again pass a value the dispatch path rejects
        budgets = config.get("budgets_usd")
        if not isinstance(budgets, dict) or sorted(budgets) != ["L", "M", "S"]:
            problems.append(f"F: {rel} budgets_usd must map exactly S, M, L")
        routing = config.get("routing")
        if not isinstance(routing, dict) or sorted(routing) != sorted(CONFIG_ROUTES):
            expected = ", ".join(CONFIG_ROUTES)
            problems.append(f"F: {rel} routing must map exactly {expected}")
        problems += [f"F: {rel} {problem}"
                     for problem in factory_config.config_problems(config)]
    return problems


def _is_setext_title(lines, idx):
    """True when lines[idx] is a Setext heading title — a non-blank line with a
    ===/--- underline beneath it. Callers rule out fenced content first. A list
    item or block quote is not a title: `- item` over `---` is a list followed
    by a thematic break, not a heading."""
    if idx + 1 >= len(lines) or not SETEXT_UNDERLINE.match(lines[idx + 1]):
        return False
    line = lines[idx]
    if not line.strip() or SETEXT_UNDERLINE.match(line):
        return False
    return not (HEADING_LINE.match(line) or NOT_A_SETEXT_TITLE.match(line))


def _is_disclosure(verdict):
    """Does this labelled verdict claim nothing — i.e. does it LEAD with the
    NOT-RUN disclaimer ("NOT VERIFIED", "SKIPPED", "N/A", "NOT RUN — reason")?
    Anything else is a claim, and a claim owes literal evidence. The head is
    what asserts: a hedge appended to a claim is still a claim."""
    return bool(DISCLOSURE_VERDICT.match(VERDICT_LEAD.sub("", verdict)))


def _fence_open(line):
    """(marker char, marker length) if `line` opens a fence, else None."""
    match = FENCE_OPEN.match(line)
    if not match:
        return None
    marker, info = match.group("marker"), match.group("info")
    # CommonMark: a backtick fence's info string may not contain a backtick.
    if marker[0] == "`" and "`" in info:
        return None
    return marker[0], len(marker)


def _fence_closes(line, char, length):
    """Does `line` close a fence opened with `length` copies of `char`?"""
    match = FENCE_CLOSE.match(line)
    if not match:
        return False
    marker = match.group("marker")
    return marker[0] == char and len(marker) >= length


def verification_sections(text):
    """Split a verification artifact's TEXT into heading-delimited sections,
    each recording — IN ITS OWN SCOPE — whether it shows literal output,
    discloses a check as NOT RUN, and what verdicts it asserts. Scope is the
    point: evidence parked in an appendix does not vouch for a criterion
    three headings away. Fenced content is inert: a heading, a `Result:`
    line, or a "not run" quoted inside evidence is output, not the author's
    assertion.

    A section asserts a verdict exactly one way: `results` holds its LABELLED
    verdict lines as (lineno, verdict) pairs (the verdict-noun vocabulary —
    see RESULT_LINE). Prose and heading text assert nothing. YAML frontmatter
    is metadata and is skipped outright, so a `status:` field is never
    mistaken for an author's verdict.

    Public with evidence_problems: pure text in, structure out, so the H
    grammar is exercisable without a fixture tree. Returns (sections,
    unclosed), where each section is {"title", "lineno", "evidence",
    "not_run", "results"} and `unclosed` is the line number of a fence that
    is never closed, or None."""
    sections = []

    def blank(title, lineno):
        return {"title": title, "lineno": lineno, "evidence": False,
                "not_run": False, "results": []}

    lines = text.splitlines()
    body = 0
    if lines and FRONTMATTER_FENCE.match(lines[0]):
        for index in range(1, len(lines)):
            if FRONTMATTER_FENCE.match(lines[index]):
                body = index + 1
                break
        # An unterminated opener is not frontmatter: scan the whole file.

    current = blank("(untitled)", body + 1)
    fence = None  # (marker char, marker length, opening line number)
    underlined = False
    for lineno, line in enumerate(lines[body:], body + 1):
        if fence is not None:
            if _fence_closes(line, fence[0], fence[1]):
                fence = None
            elif line.strip() and not PLACEHOLDER_LINE.match(line):
                current["evidence"] = True
            continue
        if underlined:  # the ===/--- under a Setext title, already consumed
            underlined = False
            continue
        opened = _fence_open(line)
        if opened:
            fence = (opened[0], opened[1], lineno)
            continue
        heading = HEADING_LINE.match(line)
        if heading:
            title = heading.group(2) or "(untitled)"
        elif _is_setext_title(lines, lineno - 1):
            title, underlined = line.strip(), True
        else:
            title = None
        if title is not None:
            sections.append(current)
            current = blank(title, lineno)
            continue
        if NOT_RUN_TOKEN.search(line):
            current["not_run"] = True
        result = RESULT_LINE.match(line)
        if result:
            current["results"].append((lineno, result.group(1)))
    sections.append(current)
    return sections, (fence[2] if fence else None)


def evidence_problems(text):
    """The H grammar over one verification artifact's TEXT: [(lineno,
    suffix)] for every violation, in artifact order — an unclosed fence
    first (it would otherwise swallow every criterion after it), then each
    section's unevidenced claim, then the artifact-wide backstop. Suffixes
    carry no label and no path; check_evidence_honesty prefixes
    "H: {rel}:{lineno}" (the cost_ledger.parse convention: the grammar is
    pure over text, so its rules are exercisable without a fixture tree).

    The rule is per-criterion, uniform, and UNEXCUSED: every section holding
    a labelled verdict line carries its own evidence or its own disclaimer.
    There is no roll-up exemption to buy by renaming a section, and no "some
    other section is honest" test to satisfy with one throwaway leaf.

    An artifact that asserts no labelled verdict anywhere escapes that rule
    but still owes the reader something, so the backstop demands exactly what
    the acceptance criterion demands: literal command output, or an explicit
    NOT-RUN disclaimer. Neither one present means the build fails."""
    problems = []
    sections, unclosed = verification_sections(text)
    if unclosed is not None:
        problems.append((unclosed, "unclosed code fence — every criterion"
                                   " after it is unread"))
    for section in sections:
        if section["evidence"]:
            continue
        claims = [(lineno, verdict)
                  for lineno, verdict in section["results"]
                  if not _is_disclosure(verdict)]
        if not claims:
            continue
        lineno, verdict = claims[0]
        problems.append(
            (lineno,
             f'criterion "{section["title"]}" asserts {verdict} with'
             " neither literal evidence nor a NOT-RUN disclaimer (evidence"
             " must be a fenced code block in this section)"))
    # An artifact that asserts no verdict at all escapes the per-criterion
    # rule; it still owes the reader output or a disclosure.
    if not any(s["results"] for s in sections) and not any(
            s["evidence"] or s["not_run"] for s in sections):
        problems.append(
            (1, "verification artifact shows neither literal evidence nor"
                " a NOT-RUN disclaimer (evidence must be a fenced code"
                " block)"))
    return problems


def check_evidence_honesty(root):
    """H: a criterion that asserts a verdict must show literal output or
    disclose that the check was NOT RUN. Prose confidence is not evidence
    (PRD-0001: a change whose verification is asserted but not evidenced
    fails the build).

    The grammar — what asserts, what evidences, what discloses — is
    evidence_problems, pure over the artifact's text. What stays here is
    the detector's own job: find each run's verification.md, read it (an
    unreadable artifact is a problem, never a traceback), and prefix each
    (lineno, suffix) the grammar returns."""
    problems = []
    for run in run_dirs(root):
        artifact = run / "verification.md"
        if not artifact.is_file():
            continue
        rel = artifact.relative_to(root)
        try:
            text = artifact.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as err:
            problems.append(f"H: {rel} cannot be read: {err}")
            continue
        problems.extend(f"H: {rel}:{lineno} {suffix}"
                        for lineno, suffix in evidence_problems(text))
    return problems


# The detector letter namespace, indexed in ONE place: letter -> (name,
# home module, plane). A letter's plane decides where its code goes.
# Offline detectors live in this module and gate every push/PR through
# CHECKERS — hermetic and deterministic, no network (B reads a local event
# file, so it is offline too; it just SKIPs outside a PR run). Network
# detectors read live services, so they live beside the scheduled sweeps
# that drive them and are NEVER wired into CHECKERS: L reads the repo's
# live label set through gh, which is why it lives in label_sync.py and
# not here (the same posture that keeps every ADR-0037 seam offline).
# J and K are unclaimed — the shared ai-tooling letter namespace assigns
# nothing to them, so a new detector takes the next free letter and adds
# its row here.
DETECTORS = {
    "A": ("WO-CITATION", "gates.py", "offline"),
    "B": ("PR-TRACEABILITY", "gates.py", "offline"),
    "C": ("LINK-INTEGRITY", "gates.py", "offline"),
    "D": ("BLUEPRINT-DRIFT", "gates.py", "offline"),
    "E": ("SCAFFOLD-SYNC", "gates.py", "offline"),
    "F": ("CONFIG-SHAPE", "gates.py", "offline"),
    "G": ("COST-LEDGER", "gates.py", "offline"),
    "H": ("EVIDENCE-HONESTY", "gates.py", "offline"),
    "I": ("STALENESS", "gates.py", "offline"),
    "J": (None, None, "unused"),
    "K": (None, None, "unused"),
    "L": ("LABEL-SYNC", "label_sync.py", "network"),
}

CHECKERS = (check_wo_citation, check_pr_traceability, check_link_integrity,
            check_blueprint_drift, check_scaffold_sync, check_config_shape,
            check_cost_ledger, check_evidence_honesty, check_staleness)


def run_all(root, env=None):
    """Run every detector. `env` (default os.environ) is threaded to the
    checkers that read the process environment, so callers can stay
    hermetic without mutating global state."""
    if env is None:
        env = os.environ
    problems = []
    for checker in CHECKERS:
        if checker is check_pr_traceability:
            problems.extend(checker(root, env))
        else:
            problems.extend(checker(root))
    return problems


def selftest():
    """Fixture trees: each detector must catch its planted defect and stay
    silent on the clean tree."""
    failures = []

    def expect(label, problems, *substrings):
        for fragment in substrings:
            if not any(fragment in p for p in problems):
                failures.append(f"{label}: expected a problem containing"
                                f" {fragment!r}, got {problems}")

    def expect_clean(label, problems):
        if problems:
            failures.append(f"{label}: expected no problems, got {problems}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run = root / "docs" / "features" / "demo"
        run.mkdir(parents=True)
        (run / "prd.md").write_text(
            "---\nstage: prd\nid: PRD-0001\n---\n# PRD\n", encoding="utf-8")
        (run / "breakdown.md").write_text(
            "- [x] WO-0001 do the thing (PRD-0001 §Solution)\n"
            "- [ ] WO-0002 uncited row\n", encoding="utf-8")
        (root / "CONTEXT.md").write_text(
            "See PRD-0001, PRD-0099, ADR-0001 and WO-0003.\n"
            "The [handbook](docs/handbook.md) moved away.\n",
            encoding="utf-8")
        (root / "docs" / "adr").mkdir()
        (root / "docs" / "adr" / "0001-real.md").write_text(
            "# Real\n\n- Status: superseded by ADR-0002\n", encoding="utf-8")
        (root / "docs" / "adr" / "0002-new.md").write_text(
            "# New\n\n- Status: accepted\n", encoding="utf-8")
        (root / "docs" / "adr" / "README.md").write_text(
            "| ADR | Decision | Status |\n|-----|----------|--------|\n"
            "| [0001](0001-real.md) | Real | superseded by ADR-0002 |\n"
            "| [0002](0002-new.md) | New | provisional |\n", encoding="utf-8")
        expect("A", check_wo_citation(root), "WO-0002")
        problems = check_link_integrity(root)
        expect("C", problems, "PRD-0099", "WO-0003")
        if any("PRD-0001 " in p and "dangling" in p for p in problems):
            failures.append(f"C: PRD-0001 should resolve, got {problems}")

        # D: the index disagrees with ADR-0002's file, and CONTEXT.md still
        # builds on ADR-0001, which ADR-0002 superseded.
        expect("D", check_blueprint_drift(root),
               "ADR-0002 index status 'provisional'",
               "cites ADR-0001, superseded by ADR-0002")

        # G: the ledger accounts for an unmerged order and misses a merged
        # one, and one line is not JSON at all.
        (root / "docs" / "factory").mkdir()
        (root / "docs" / "factory" / "costs.jsonl").write_text(
            json.dumps({"wo": "WO-0002", "run_id": "r1", "model": "m",
                        "tokens": 900, "cost": 0.3, "outcome": "failed"})
            + "\n{\"wo\": \"WO-0001\"\n", encoding="utf-8")
        expect("G", check_cost_ledger(root),
               "merged work order WO-0001 has no line", "is not valid JSON")

        # I: CONTEXT.md links a doc that is not on disk.
        expect("I", check_staleness(root), "stale link docs/handbook.md")

        factory = root / "factory" / "templates"
        factory.mkdir(parents=True)
        (factory / "Makefile").write_text("check:\n", encoding="utf-8")
        digest = hashlib.sha256((factory / "Makefile").read_bytes()).hexdigest()
        (root / "factory" / "manifest.json").write_text(json.dumps(
            {"files": {"templates/Makefile": digest}}), encoding="utf-8")
        expect_clean("E clean", check_scaffold_sync(root))
        (factory / "Makefile").write_text("check: tampered\n", encoding="utf-8")
        expect("E", check_scaffold_sync(root), "manifest checksum")

        (factory / "factory.json").write_text(json.dumps(
            {"budgets_usd": {"S": 5, "M": 15},
             "routing": {"mechanical": "m"},
             "wip_cap": 0, "monthly_cap_usd": -1}), encoding="utf-8")
        problems = check_config_shape(root)
        expect("F", problems, "budgets_usd", "routing", "wip_cap",
               "monthly_cap_usd")

        event = root / "event.json"
        env = {"GITHUB_EVENT_PATH": str(event)}
        event.write_text(json.dumps({"pull_request": {
            "title": "fix: something", "body": "no tokens here"}}),
            encoding="utf-8")
        expect("B", check_pr_traceability(root, env),
               "cites no work-order id", "no Closes #N link")
        expect("B unreadable", check_pr_traceability(
            root, {"GITHUB_EVENT_PATH": str(root / "missing.json")}),
            "cannot read GITHUB_EVENT_PATH")
        event.write_text(json.dumps({"ref": "refs/heads/main"}),
                         encoding="utf-8")
        expect_clean("B non-PR", check_pr_traceability(root, env))
        event.write_text(json.dumps({"pull_request": {
            "title": "WO-0003: detector B",
            "body": "WO-0003 (PRD-0001) Fixes: #108"}}), encoding="utf-8")
        expect_clean("B clean", check_pr_traceability(root, env))

        (run / "verification.md").write_text(
            "---\nstage: verify\n---\n# Verification\n\n"
            "### Suite is green\n\n- Check: ran it, all good.\n"
            "- Result: PASS\n", encoding="utf-8")
        # A wholly fabricated, TEMPLATE-shaped artifact with ZERO command
        # output. The `## Not verified` slot ships in every artifact, so its
        # LABEL cannot be the disclosure — only what the author writes is.
        fabricated = root / "docs" / "features" / "fabricated"
        fabricated.mkdir()
        (fabricated / "verification.md").write_text(
            "---\nstage: verify\n---\n# Verification\n\n"
            "## Summary\n\n6/6 criteria pass. Verdict: ship it.\n\n"
            "## Criteria & evidence\n\n### Test suite\n\n"
            "- Check: ran the full suite; everything passed.\n\n"
            "## Failures\n\nNone.\n\n"
            "## Not verified\n\nNothing; everything was checked.\n",
            encoding="utf-8")
        # The gaming shapes H exists to stop: a lying roll-up RENAMED to dodge
        # the (now deleted) roll-up excuse, one throwaway evidenced leaf trying
        # to launder it, a relabelled verdict dodging the "Result:" token, a
        # scoped hedge posing as a NOT-RUN disclaimer, and an unrelated
        # appendix fence standing in for per-criterion evidence. Each fires in
        # its own section's scope.
        gamed = root / "docs" / "features" / "gamed"
        gamed.mkdir()
        (gamed / "verification.md").write_text(
            "---\nstage: verify\n---\n# Verification\n\n"
            "### Grammar parses\n\n- Evidence:\n  ```\n  .\n  ```\n"
            "- Result: PASS\n\n"
            "## Results\n\n- Result: all 6 criteria PASS\n\n"
            "### Budget guard holds\n\n- Verdict: PASS\n\n"
            "### Router picks the model\n\n- Result: PASS\n"
            "Note: not tested on Windows.\n\n"
            "### Retry path\n\n- Result: PASS\n"
            "- (the retry path itself was not run)\n\n"
            "## Appendix\n\n```\ngit log --oneline -3\n```\n",
            encoding="utf-8")
        # An unclosed fence must be reported, never silently absorb the tail.
        unclosed = root / "docs" / "features" / "unclosed"
        unclosed.mkdir()
        (unclosed / "verification.md").write_text(
            "---\nstage: verify\n---\n# Verification\n\n"
            "### Report renders\n\n- Evidence:\n  ```\n  3 orders merged\n"
            "- Result: PASS\n", encoding="utf-8")
        expect("H", check_evidence_honesty(root),
               'criterion "Suite is green" asserts PASS with neither',
               "artifact shows neither literal evidence",
               'criterion "Results" asserts all 6 criteria PASS with neither',
               'criterion "Budget guard holds" asserts PASS with neither',
               'criterion "Router picks the model" asserts PASS with neither',
               'criterion "Retry path" asserts PASS with neither',
               "unclosed code fence")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run = root / "docs" / "features" / "demo"
        run.mkdir(parents=True)
        (run / "prd.md").write_text(
            "---\nstage: prd\nid: PRD-0001\n---\n# PRD\n", encoding="utf-8")
        (run / "breakdown.md").write_text(
            "- [x] WO-0001 shipped slice (PRD-0001 §Solution), per"
            " [ADR-0001](../../adr/0001-spine.md)\n", encoding="utf-8")
        (root / "docs" / "adr").mkdir()
        (root / "docs" / "adr" / "0001-spine.md").write_text(
            "# Spine\n\n- Status: accepted (shipped 2026-07-06)\n",
            encoding="utf-8")
        (root / "docs" / "adr" / "README.md").write_text(
            "| ADR | Decision | Status |\n|-----|----------|--------|\n"
            "| [0001](0001-spine.md) | Spine | accepted |\n",
            encoding="utf-8")
        (root / "docs" / "factory").mkdir()
        (root / "docs" / "factory" / "costs.jsonl").write_text(
            json.dumps({"wo": "WO-0001", "run_id": "r1", "model": "m",
                        "tokens": 1200, "cost": 0.42, "outcome": "merged"})
            + "\n", encoding="utf-8")
        evidenced = root / "docs" / "features" / "evidenced"
        evidenced.mkdir(parents=True)
        (evidenced / "verification.md").write_text(
            "---\nstage: verify\n---\n# Verification\n\n"
            "### Suite is green\n\n- Evidence:\n  ```\n  Ran 212 tests\n"
            "\n  OK\n  ```\n- Result: PASS\n", encoding="utf-8")
        disclosed = root / "docs" / "features" / "disclosed"
        disclosed.mkdir()
        (disclosed / "verification.md").write_text(
            "---\nstage: verify\n---\n# Verification\n\n"
            "### Non-owner dispatch does not fire\n\n"
            "- Check: NOT RUN — needs a second GitHub account.\n"
            "- Result: NOT VERIFIED\n", encoding="utf-8")
        # A roll-up summary narrates the verdicts the criteria below evidence.
        # It is not itself a criterion, and H must not read it as one.
        rollup = root / "docs" / "features" / "rollup"
        rollup.mkdir()
        (rollup / "verification.md").write_text(
            "---\nstage: verify\n---\n# Verification\n\n"
            "## Summary\n\n4/4 criteria pass; suite and lint green on the\n"
            "branch. Verdict: the feature demonstrably works.\n\n"
            "## Criteria & evidence\n\n### Suite is green\n\n- Evidence:\n"
            "  ```\n  Ran 222 tests\n\n  OK\n  ```\n- Result: PASS\n",
            encoding="utf-8")
        expect_clean("H honest", check_evidence_honesty(root))
        payload = root / "factory" / "templates"
        payload.mkdir(parents=True)
        (payload / "factory.json").write_text(json.dumps(
            {"budgets_usd": {"S": 5, "M": 15, "L": 40},
             "routing": {"mechanical": "m", "implementation": "i",
                         "architecture_review": "a"},
             "wip_cap": 3, "monthly_cap_usd": 300}), encoding="utf-8")
        digest = hashlib.sha256(
            (payload / "factory.json").read_bytes()).hexdigest()
        (root / "factory" / "manifest.json").write_text(json.dumps(
            {"files": {"templates/factory.json": digest}}), encoding="utf-8")
        expect_clean("clean tree", run_all(root, env={}))

    for failure in failures:
        print(failure)
    print(f"selftest: {'FAIL' if failures else 'ok'}")
    return 1 if failures else 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    root = repo_root()
    problems = run_all(root)
    for problem in problems:
        print(problem)
    print(f"gates: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
