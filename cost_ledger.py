#!/usr/bin/env python3
"""cost_ledger: the one home of the append-only cost ledger's shape
(ADR-0034, ADR-0037) — docs/factory/costs.jsonl's path, field set, line
grammar, and the append/read operations over it.

Before this seam the shape lived in three places: budget_guard.py wrote
lines, detector G (gates.py) validated them in full, and
cost_report.read_ledger hand-rolled a partial re-validation that its own
docstring admitted could diverge from G. Now G and the report read the
same grammar: parse/line_problems are the single rule, G layers its
breakdown cross-checks on top, and read() is the report's reader whose
excluded-line problems ARE the CI rule's field checks.

Conventions match gates.py: read() returns ledger:-prefixed problem
strings; parse/line_problems return unlocated suffixes for callers that
prefix their own label and location (detector G keeps its G: strings
byte-for-byte).
"""
import json
import re
from pathlib import Path

from knowledge_plane import WO_TOKEN

# The append-only cost ledger (ADR-0034). The outcome vocabulary is
# deliberately open — ADR-0034 fixes the field set, not its values.
COST_LEDGER = "docs/factory/costs.jsonl"
LEDGER_FIELDS = ("wo", "run_id", "model", "tokens", "cost", "outcome")
LEDGER_TEXT_FIELDS = ("run_id", "model", "outcome")

# Gate-latency observations (ADR-0041): a $0, zero-token row recording how
# long a work order waited at one of the three human gates, written by the
# daily gate digest inside ADR-0034's open outcome vocabulary.
GATE_OUTCOME = re.compile(r"gate_wait:([a-z]+):(\d+)s")


def entry(wo, run_id, model, tokens, cost, outcome):
    """A well-formed ledger record, built from LEDGER_FIELDS so the field
    set cannot drift from what detector G checks — the single place a
    caller assembles one."""
    return dict(zip(LEDGER_FIELDS, (wo, run_id, model, tokens, cost, outcome)))


def gate_entry(wo, gate, waited_seconds, passed_at):
    """A gate-latency observation as a well-formed ledger record
    (ADR-0041): the work order waited `waited_seconds` at `gate` and
    passed it at `passed_at` (ISO timestamp, which keys the run_id so a
    re-observed passage dedups instead of double-recording)."""
    return entry(wo, f"gate-{gate}-{passed_at}", "none", 0, 0.0,
                 f"gate_wait:{gate}:{int(waited_seconds)}s")


def gate_wait(entry):
    """The record's (gate, waited_seconds) when it is a gate-latency row,
    else None — the one predicate for callers that treat gate rows apart
    from dispatched runs (the digest dedups on them; the weekly report
    keeps them out of its run counts)."""
    value = entry.get("outcome") if isinstance(entry, dict) else None
    match = GATE_OUTCOME.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        return None
    return match.group(1), int(match.group(2))


def append(root, entry):
    """Append one line to docs/factory/costs.jsonl. APPEND ONLY: opens in
    "a" mode and never reads or rewrites existing lines — the ledger is the
    factory's measurement substrate and gets the same append-only
    discipline as evals/results/ (CLAUDE.md eval honesty)."""
    ledger = Path(root) / COST_LEDGER
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def wo_token(entry):
    """The record's valid WO-#### token, or None. The shape complaint for
    an invalid one is line_problems' job; this is for callers (detector G)
    that cross-check a VALID token against the knowledge plane."""
    value = entry.get("wo") if isinstance(entry, dict) else None
    if isinstance(value, str) and WO_TOKEN.fullmatch(value):
        return value
    return None


def line_problems(entry):
    """Unlocated shape problems for one parsed ledger record (ADR-0034):
    missing/unknown fields, then per-field rules in LEDGER_FIELDS order.
    Callers prefix their own label and location — this is the single rule
    detector G and read() both apply."""
    problems = []
    missing = sorted(set(LEDGER_FIELDS) - set(entry))
    if missing:
        problems.append(
            f"ledger line is missing field(s): {', '.join(missing)}")
    unknown = sorted(set(entry) - set(LEDGER_FIELDS))
    if unknown:
        problems.append(
            f"ledger line has unknown field(s): {', '.join(unknown)}")
    for field in LEDGER_FIELDS:
        if field not in entry:
            continue
        value = entry[field]
        if field == "wo":
            if not (isinstance(value, str) and WO_TOKEN.fullmatch(value)):
                problems.append(f"wo {value!r} is not a WO-#### token")
        elif field in LEDGER_TEXT_FIELDS:
            if not isinstance(value, str) or not value.strip():
                problems.append(f"{field} must be a non-empty string")
        elif field == "tokens":
            if isinstance(value, bool) or not isinstance(value, int) \
                    or value < 0:
                problems.append("tokens must be a non-negative integer")
        elif field == "cost":
            if isinstance(value, bool) or not isinstance(value, (int, float)) \
                    or value < 0:
                problems.append("cost must be a non-negative number")
    return problems


def parse(text):
    """[(lineno, entry, problems)] for every non-blank ledger line: entry
    is the parsed record (None when the line is not a JSON object) and
    problems are its unlocated parse + shape complaints. The one walk both
    detector G and read() are built on."""
    parsed = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as err:
            parsed.append((lineno, None, [f"is not valid JSON: {err}"]))
            continue
        if not isinstance(record, dict):
            parsed.append((lineno, None, ["is not a JSON object"]))
            continue
        parsed.append((lineno, record, line_problems(record)))
    return parsed


def read(root, ledger_path=None):
    """(entries, problems): every ledger line that satisfies the full
    ADR-0034 shape; anything else is excluded from entries and reported as
    a ledger:-prefixed problem, never silently dropped — an unaccountable
    line must not silently undercount spend (fail closed). An absent
    ledger is silent (no runs yet): the ledger is created by the first run
    that records into it, matching detector G's own convention."""
    path = Path(ledger_path) if ledger_path else Path(root) / COST_LEDGER
    if not path.is_file():
        return [], []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as err:
        return [], [f"ledger: cannot read {COST_LEDGER}: {err}"]
    entries, problems = [], []
    for lineno, record, suffixes in parse(text):
        problems.extend(f"ledger: {COST_LEDGER}:{lineno} {suffix}"
                        for suffix in suffixes)
        if record is not None and not suffixes:
            entries.append(record)
    return entries, problems
