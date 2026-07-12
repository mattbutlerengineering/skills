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
  I STALENESS      — no knowledge-plane doc links to a path that no longer
                     exists on disk

`--selftest` runs the checkers against fixture trees and exits nonzero
on a failing assertion. Both run in CI (validator.yml, via `make check`)
on every push/PR.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from protocol import read_frontmatter

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

# The append-only cost ledger (ADR-0034). The outcome vocabulary is
# deliberately open — ADR-0034 fixes the field set, not its values.
COST_LEDGER = "docs/factory/costs.jsonl"
LEDGER_FIELDS = ("wo", "run_id", "model", "tokens", "cost", "outcome")
LEDGER_TEXT_FIELDS = ("run_id", "model", "outcome")
# A merged work order is a checked breakdown row (ADR-0004: the artifact,
# not the tracker, is the state).
MERGED_ROW = re.compile(r"^\s*-\s*\[x\]", re.IGNORECASE)

# Markdown links to repo paths; URLs, autolinks and bare anchors are not.
MD_LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)>\s]+)>?")
URL_TARGET = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")

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


def run_dirs(root):
    """Candidate run directories per the pipeline protocol."""
    dirs = [root / "docs"]
    for parent in ("features", "fixes"):
        base = root / "docs" / parent
        if base.is_dir():
            dirs.extend(p for p in sorted(base.iterdir()) if p.is_dir())
    return [d for d in dirs if d.is_dir()]


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
    for run in run_dirs(root):
        breakdown = run / "breakdown.md"
        if not breakdown.is_file():
            continue
        for lineno, line in enumerate(
                breakdown.read_text(encoding="utf-8").splitlines(), 1):
            wo = WO_TOKEN.search(line)
            if wo and not PRD_TOKEN.search(line):
                rel = breakdown.relative_to(root)
                problems.append(
                    f"A: {rel}:{lineno} work-order row {wo.group(0)}"
                    " cites no PRD id")
    return problems


def pr_event(env):
    """(the pull_request payload, error): the PR this CI run is about, read
    from the event file. (None, None) outside a PR run — every caller SKIPs
    silently there. Callers label the error string themselves, so this stays
    detector-agnostic (validator.py is the second caller)."""
    event_path = env.get("GITHUB_EVENT_PATH")
    if not event_path:
        return None, None
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        return None, f"cannot read GITHUB_EVENT_PATH {event_path}: {err}"
    pr = event.get("pull_request") if isinstance(event, dict) else None
    return (pr if isinstance(pr, dict) else None), None


def check_pr_traceability(root, env=None):
    """B: a PR whose body cites no work order and closes no issue breaks
    the audit trail from code back to scope. Reads the CI event payload;
    SKIPs silently outside a PR run. No exemptions."""
    if env is None:
        env = os.environ
    pr, error = pr_event(env)
    if error:
        return [f"B: {error}"]
    if pr is None:
        return []
    body = pr.get("body") or ""
    problems = []
    if not WO_TOKEN.search(body):
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
    for run in run_dirs(root):
        breakdown = run / "breakdown.md"
        if breakdown.is_file():
            rows.update(WO_TOKEN.findall(
                breakdown.read_text(encoding="utf-8")))
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
    the artifact-side record that a work order merged (ADR-0004)."""
    rows = []
    for run in run_dirs(root):
        breakdown = run / "breakdown.md"
        if not breakdown.is_file():
            continue
        rel = breakdown.relative_to(root)
        for lineno, line in enumerate(
                breakdown.read_text(encoding="utf-8").splitlines(), 1):
            wo = WO_TOKEN.search(line)
            if MERGED_ROW.match(line) and wo:
                rows.append((rel, lineno, wo.group(0)))
    return rows


def _ledger_line(entry, lineno, wo_rows, recorded):
    """Field-level problems for one parsed ledger record (ADR-0034)."""
    problems = []
    for field in LEDGER_FIELDS:
        if field not in entry:
            continue
        value = entry[field]
        if field == "wo":
            if isinstance(value, str) and WO_TOKEN.fullmatch(value):
                recorded.add(value)
                if value not in wo_rows:
                    problems.append(f"G: {COST_LEDGER}:{lineno} wo {value}"
                                    " has no breakdown row")
            else:
                problems.append(f"G: {COST_LEDGER}:{lineno} wo {value!r}"
                                " is not a WO-#### token")
        elif field in LEDGER_TEXT_FIELDS:
            if not isinstance(value, str) or not value.strip():
                problems.append(f"G: {COST_LEDGER}:{lineno} {field} must be"
                                " a non-empty string")
        elif field == "tokens":
            if isinstance(value, bool) or not isinstance(value, int) \
                    or value < 0:
                problems.append(f"G: {COST_LEDGER}:{lineno} tokens must be"
                                " a non-negative integer")
        elif field == "cost":
            if isinstance(value, bool) or not isinstance(value, (int, float)) \
                    or value < 0:
                problems.append(f"G: {COST_LEDGER}:{lineno} cost must be"
                                " a non-negative number")
    return problems


def check_cost_ledger(root):
    """G: every run appends {wo, run_id, model, tokens, cost, outcome} to
    the append-only docs/factory/costs.jsonl, and a merged work order with
    no ledger line is a gating finding (ADR-0034). An absent ledger is
    silent, not a finding: the ledger is created by the first run that
    records into it, so a freshly stamped repo has no runs to account for
    — the rule bites once the ledger exists."""
    ledger = root / "docs" / "factory" / "costs.jsonl"
    if not ledger.is_file():
        return []
    try:
        text = ledger.read_text(encoding="utf-8")
    except OSError as err:
        return [f"G: cannot read {COST_LEDGER}: {err}"]
    problems = []
    wo_rows = collect_wo_rows(root)
    recorded = set()
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as err:
            problems.append(
                f"G: {COST_LEDGER}:{lineno} is not valid JSON: {err}")
            continue
        if not isinstance(entry, dict):
            problems.append(f"G: {COST_LEDGER}:{lineno} is not a JSON object")
            continue
        missing = sorted(set(LEDGER_FIELDS) - set(entry))
        if missing:
            problems.append(f"G: {COST_LEDGER}:{lineno} ledger line is"
                            f" missing field(s): {', '.join(missing)}")
        unknown = sorted(set(entry) - set(LEDGER_FIELDS))
        if unknown:
            problems.append(f"G: {COST_LEDGER}:{lineno} ledger line has"
                            f" unknown field(s): {', '.join(unknown)}")
        problems.extend(_ledger_line(entry, lineno, wo_rows, recorded))
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
    for rel, expected in sorted(files.items()):
        path = root / "factory" / rel
        if not path.is_file():
            problems.append(f"E: manifest lists missing file factory/{rel}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            problems.append(
                f"E: factory/{rel} does not match its manifest checksum"
                " (re-run manifest update, never hand-edit)")
    payload = root / "factory" / "templates"
    if payload.is_dir():
        for path in sorted(payload.rglob("*")):
            if path.is_file():
                rel = str(path.relative_to(root / "factory"))
                if rel not in files:
                    problems.append(f"E: factory/{rel} is not in the manifest")
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
        budgets = config.get("budgets_usd")
        if not isinstance(budgets, dict) or sorted(budgets) != ["L", "M", "S"]:
            problems.append(f"F: {rel} budgets_usd must map exactly S, M, L")
        else:
            for size, value in budgets.items():
                if not isinstance(value, (int, float)) or value <= 0:
                    problems.append(
                        f"F: {rel} budgets_usd.{size} must be a positive number")
        routing = config.get("routing")
        if not isinstance(routing, dict) or sorted(routing) != sorted(CONFIG_ROUTES):
            expected = ", ".join(CONFIG_ROUTES)
            problems.append(f"F: {rel} routing must map exactly {expected}")
        else:
            for route, model in routing.items():
                if not isinstance(model, str) or not model:
                    problems.append(
                        f"F: {rel} routing.{route} must name a model id")
        wip = config.get("wip_cap")
        if not isinstance(wip, int) or wip < 1:
            problems.append(f"F: {rel} wip_cap must be a positive integer")
        cap = config.get("monthly_cap_usd")
        if not isinstance(cap, (int, float)) or cap <= 0:
            problems.append(f"F: {rel} monthly_cap_usd must be a positive number")
    return problems


CHECKERS = (check_wo_citation, check_pr_traceability, check_link_integrity,
            check_blueprint_drift, check_scaffold_sync, check_config_shape,
            check_cost_ledger, check_staleness)


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


def repo_root():
    """Nearest ancestor containing .git (dir or worktree file): correct at
    the factory repo root and stamped at tools/factory/ in a product repo."""
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    return here


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
