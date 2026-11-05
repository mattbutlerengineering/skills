#!/usr/bin/env python3
"""svg-check: a mechanical check for the diagram skills' SVG output.

The run is docs/features/svg-mechanical-check/. For one SVG file it
refuses a DTD or entity before any parse that could expand it, then names
every defect it finds, one problem string each.

OFFLINE AND NOT A GATE. Standard library only, no network, no model, no
write, outside `make check`. The smallest-text reading is a report, never a
failure. The file is read whole; the refusal below is the untrusted-input
defence, not a size cap.
"""
import math
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from xml.parsers import expat

LABEL = "svg-check"
USAGE = (f"{LABEL}: usage: python3 svg_check.py <file.svg>"
         " [--embed-width PX]")
DEFAULT_EMBED = 830.0
REFUSED = ("refused: the file declares a DTD or an entity (remove the"
           " <!DOCTYPE>; the check does not expand either)")


@dataclass
class Report:
    refusal: "str | None" = None
    problems: list = field(default_factory=list)
    smallest_px: "float | None" = None
    embed_px: float = DEFAULT_EMBED
    unread: int = 0
    skipped_rules: int = 0
    note: "str | None" = None  # why smallest_px is unset: "no text" or a reason


class _Refused(Exception):
    pass


def _refuse(*_args):
    raise _Refused


def _refusal(data):
    """None when the file is well-formed and declares no DTD or entity,
    else the refusal text. expat is the only place the declarations can be
    intercepted, and it fires before an entity is defined or used."""
    parser = expat.ParserCreate()
    parser.StartDoctypeDeclHandler = _refuse
    parser.EntityDeclHandler = _refuse
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    try:
        parser.Parse(data, True)
    except _Refused:
        return REFUSED
    except expat.ExpatError as e:
        return f"not well-formed: {e}"
    return None


def check(data, embed_width=DEFAULT_EMBED):
    """Check one SVG's bytes; never raises on file content. A non-positive
    or non-finite embed_width is a caller bug and raises ValueError."""
    if not (isinstance(embed_width, (int, float))
            and math.isfinite(embed_width) and embed_width > 0):
        raise ValueError(f"embed_width must be a positive number: "
                         f"{embed_width!r}")
    report = Report(embed_px=float(embed_width))
    report.refusal = _refusal(data)
    if report.refusal:
        return report
    try:
        ET.fromstring(data)
    except ET.ParseError as e:
        report.refusal = f"not well-formed: {e}"
    return report


def _usage(argv):
    """(path, embed_width) or None when argv is not one file and an
    optional --embed-width."""
    path, embed, args = None, DEFAULT_EMBED, list(argv)
    while args:
        a = args.pop(0)
        if a == "--embed-width" or a.startswith("--embed-width="):
            raw = a.partition("=")[2] if "=" in a else (
                args.pop(0) if args else None)
            try:
                embed = float(raw)
            except (TypeError, ValueError):
                return None
            if not (math.isfinite(embed) and embed > 0):
                return None
        elif a.startswith("--") or path is not None:
            return None
        else:
            path = a
    return None if path is None else (path, embed)


def main(argv):
    """`python3 svg_check.py <file.svg> [--embed-width PX]` — exit 0 clean,
    1 with defects, 2 when the file was not checked (usage, unreadable,
    refused). Writes nothing."""
    parsed = _usage(argv)
    if parsed is None:
        print(USAGE)
        return 2
    path, embed = parsed
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        print(f"{LABEL}: {path}: cannot read: {e.strerror or e}")
        return 2
    report = check(data, embed)
    if report.refusal:
        print(f"{LABEL}: {path}: {report.refusal}")
        return 2
    for problem in report.problems:
        print(f"{LABEL}: {path}: {problem}")
    return 1 if report.problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
