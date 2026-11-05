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
import re
import sys
from collections import Counter
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


SVG_NS = "http://www.w3.org/2000/svg"
URL_RE = re.compile(r"""url\(\s*(?:"([^"]*)"|'([^']*)'|([^)\s]*))\s*\)""")
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
CLOCK = r"(?:\d+:\d\d(?::\d\d)?(?:\.\d+)?|\d+(?:\.\d+)?(?:h|min|s|ms)?)"
# One SMIL begin/end item naming an element: `<id>.<event>` and an optional
# offset. A bare clock value such as `1.6s` or `-1.6s` has no event name,
# so it never matches and is never read as an id.
TIMING_REF_RE = re.compile(
    r"(\S+?)\.([A-Za-z]\w*(?:\([^)]*\))?)(?:\s*[+-]\s*" + CLOCK + r")?$")
FONT_SIZE_RE = re.compile(r"(?:^|[;{\s])font-size\s*:\s*([^;}]+)")
SELECTOR_RE = re.compile(r"([A-Za-z][\w-]*)?(?:\.([\w-]+))?$")
PX_RE = re.compile(r"\s*(\d+(?:\.\d+)?|\.\d+)\s*(?:px)?\s*$")


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
        root = ET.fromstring(data)
    except ET.ParseError as e:
        report.refusal = f"not well-formed: {e}"
        return report
    _defects(root, report.problems)
    if root.tag == f"{{{SVG_NS}}}svg":
        _reading(root, report)
    else:
        report.note = "the root is not svg"
    return report


def _local(name):
    """The name without its `{namespace}` prefix."""
    return name.rpartition("}")[2]


def _px(value):
    """A positive px or unitless length as a float, else None."""
    m = PX_RE.match(value or "")
    return float(m.group(1)) if m and float(m.group(1)) > 0 else None


def _urls(text):
    """Every url() target in a CSS or attribute value."""
    return [next(g for g in m.groups() if g is not None).strip()
            for m in URL_RE.finditer(text)]


def _defects(root, problems):
    """Append one problem string per defect found in the parsed tree."""
    if root.tag != f"{{{SVG_NS}}}svg":
        problems.append(f"root element is {root.tag}, not svg")
        return
    for dim in ("width", "height"):
        value = root.get(dim)
        if value is None:
            problems.append(f"root {dim} missing")
        elif _px(value) is None:
            problems.append(f'root {dim} "{value}" is not a px length')
    elements = list(root.iter())
    counts = Counter(e.get("id") for e in elements if e.get("id") is not None)
    ids = set(counts)
    for name, n in counts.items():
        if n > 1:
            problems.append(f'duplicate id "{name}" on {n} elements')
    for e in elements:
        tag = _local(e.tag)
        for attr, value in e.attrib.items():
            attr = _local(attr)
            if attr == "href":
                _href(problems, ids, tag, value.strip())
            elif attr in ("begin", "end"):
                _timing(problems, ids, tag, attr, value)
            _css_urls(problems, ids, value, f"{tag} {attr}")
        if tag == "style":
            css = CSS_COMMENT_RE.sub("", "".join(e.itertext()))
            _css_urls(problems, ids, css, "<style>")


def _timing(problems, ids, tag, attr, value):
    for item in value.split(";"):
        m = TIMING_REF_RE.match(item.strip())
        if m and m.group(1) not in ids:
            problems.append(f'dangling timing reference "{m.group(1)}" '
                            f"in {tag} {attr}")


def _scale(root, embed):
    """(content scale, None), or (None, why it cannot be computed). An
    <img> is scaled down to the column and never up, so the rendered width
    is min(root width, embed); the smaller axis scale is the `meet` fit."""
    w, h = _px(root.get("width")), _px(root.get("height"))
    if w is None or h is None:
        return None, "root width and height are needed to scale text"
    box = root.get("viewBox")
    if box is None:
        vb_w, vb_h = w, h  # no viewBox: user units are px
    else:
        try:
            nums = [float(n) for n in re.split(r"[\s,]+", box.strip())]
        except ValueError:
            nums = []
        if (len(nums) != 4 or not all(map(math.isfinite, nums))
                or nums[2] <= 0 or nums[3] <= 0):
            return None, ("viewBox is not four numbers with a positive"
                          " width and height")
        vb_w, vb_h = nums[2], nums[3]
    rendered = min(w, embed)
    return min(rendered / vb_w, rendered * (h / w) / vb_h), None


def _font_rules(root):
    """(rules, skipped). A rule is (specificity, order, tag, class, value)
    for a `tag`, `.class`, `tag.class` or comma-list selector. A <style>
    rule carrying font-size under any other selector, or inside an at-rule,
    is counted in skipped, never silently ignored."""
    css = CSS_COMMENT_RE.sub("", "\n".join(
        "".join(e.itertext()) for e in root.iter()
        if _local(e.tag) == "style"))
    rules, skipped, i = [], 0, 0
    while True:
        brace = css.find("{", i)
        if brace < 0:
            return rules, skipped
        prelude, depth, j = css[i:brace].strip(), 1, brace + 1
        while j < len(css) and depth:
            depth += (css[j] == "{") - (css[j] == "}")
            j += 1
        body, i = css[brace + 1:j - 1], j
        while prelude.startswith("@") and ";" in prelude:
            prelude = prelude.partition(";")[2].strip()  # @import and kin
        if "font-size" not in body:
            continue
        decls = FONT_SIZE_RE.findall(body)
        if prelude.startswith("@") or not decls:
            skipped += 1
            continue
        value = decls[-1].replace("!important", "").strip()
        readable = True
        for sel in prelude.split(","):
            m = SELECTOR_RE.match(sel.strip())
            if not m or not sel.strip():
                readable = False
                continue
            tag, cls = m.groups()
            rules.append(((cls is not None) * 10 + (tag is not None),
                          len(rules), tag, cls, value))
        skipped += not readable


def _declared(node, rules):
    """The font-size declaration that applies to this element itself, in
    precedence inline style, <style> rule, attribute; None if it has none."""
    found = FONT_SIZE_RE.findall(node.get("style", ""))
    if found:
        return found[-1].replace("!important", "").strip()
    classes = (node.get("class") or "").split()
    tag = _local(node.tag)
    hits = [r for r in rules if r[2] in (None, tag)
            and r[3] in (None, *classes)]
    if hits:
        return max(hits)[4]
    value = node.get("font-size")
    return value.strip() if value is not None else None


def _font_size(node, parents, rules):
    """The px size from the nearest declaration walking up the ancestors,
    or None when that declaration is not px or unitless (em, %, var())
    or there is none."""
    while node is not None:
        value = _declared(node, rules)
        if value is not None:
            return _px(value)
        node = parents.get(node)
    return None


def _has_text(e):
    return bool((e.text or "").strip()
                or any((c.tail or "").strip() for c in e))


def _reading(root, report):
    """Fill the text fields of report: the smallest text size at the embed
    width, or the reason it was not read."""
    rules, report.skipped_rules = _font_rules(root)
    parents = {c: p for p in root.iter() for c in p}
    texts = [e for e in root.iter()
             if _local(e.tag) in ("text", "tspan") and _has_text(e)]
    sizes = [_font_size(e, parents, rules) for e in texts]
    report.unread = sizes.count(None)
    scale, why = _scale(root, report.embed_px)
    if not texts:
        report.note = "no text"
    elif why:
        report.note = why
    elif len(sizes) == report.unread:
        report.note = "no text size resolved"
    else:
        report.smallest_px = min(s for s in sizes if s is not None) * scale


def _text_line(report):
    if report.smallest_px is not None:
        line = (f"smallest text {round(report.smallest_px, 1):g}px at "
                f"{report.embed_px:g}px embed width")
    elif report.note == "no text":
        line = "no text"
    else:
        line = f"smallest text not read: {report.note}"
    counts = [f"{n} {what}" for n, what in (
        (report.unread, "text elements unread"),
        (report.skipped_rules, "style rules skipped")) if n]
    return f"{line} ({', '.join(counts)})" if counts else line


def _href(problems, ids, tag, value):
    if not value.startswith("#"):
        problems.append(f'external href "{value}" on {tag}')
    elif value[1:] not in ids:
        problems.append(f'dangling href "{value}" on {tag}')


def _css_urls(problems, ids, text, where):
    for target in _urls(text):
        if not target.startswith("#"):
            problems.append(f"external url({target}) in {where}")
        elif target[1:] not in ids:
            problems.append(f"dangling url({target}) in {where}")


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
    line = _text_line(report)
    print(f"{LABEL}: {path}: {line}" if report.problems
          else f"{LABEL}: {path}: pass — {line}")
    return 1 if report.problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
