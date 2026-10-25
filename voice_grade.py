#!/usr/bin/env python3
"""voice-grade: count a reply's proxy tokens and name its slop patterns.

The offline half of the house-voice measurement (the run is
docs/features/house-voice/; ADR-0119). For one or more reply files it
prints a proxy token count and one problem string per slop pattern found
outside code, the patterns the house-voice skill's rules ban.

OFFLINE AND NOT A GATE. No network, no model, no write, outside `make
check`. The count is not Claude's tokenizer: it is one unit per run of
word characters and one per other non-space character, valid only for
comparing two replies to the same prompt in the same language. The
harness suite under plugin-evals/house-voice/ carries the same patterns as
regex graders, pinned to SLOP_PATTERNS by a test (ADR-0114's shape).
"""
import re
import sys

LABEL = "voice-grade"
USAGE = (f"{LABEL}: usage: python3 voice_grade.py <reply.md>"
         " [<reply.md> ...]")

# (name, pattern, flags). The flags are the harness regex grader's letters,
# so a grader file can carry them unchanged; every pattern runs in both
# Python's re and JavaScript.
SLOP_PATTERNS = (
    ("praise-opener",
     r"\b(?:great|good|excellent|fantastic) question\b", "i"),
    ("throat-clearing",
     r"\b(?:here['’]s the thing|let me be clear|the truth is|it turns out"
     r"|let me walk you through)\b", "i"),
    ("restated-question",
     r"^(?:so,? )?you(?:['’]re| are) asking\b|^you want to know\b", "im"),
    ("hedge",
     r"\bit(?:['’]s| is) (?:worth noting|important to note)\b"
     r"|\bgenerally speaking\b", "i"),
    ("closing-recap",
     r"\b(?:in summary|in conclusion|to summari[sz]e|to sum up)\b", "i"),
    ("closing-offer",
     r"\b(?:let me know if|hope this helps|feel free to|happy to help)\b",
     "i"),
    ("em-dash", r"—", "i"),
    ("business-jargon",
     r"\b(?:deep dive|circle back|game[- ]changer|lean into|double down"
     r"|moving forward)\b", "i"),
    ("emphasis-crutch",
     r"\b(?:full stop\.|let that sink in|make no mistake)", "i"),
    ("filler-adverb",
     r"\b(?:literally|genuinely|honestly|truly|fundamentally|inherently)\b",
     "i"),
    ("binary-contrast",
     r"\bnot just\b[^.]*\bbut\b|\bisn['’]t (?:just )?[^.]{1,40}\. it['’]s\b",
     "i"),
    ("narration",
     r"\blet me (?:start|begin|take a look|check|explain)\b"
     r"|\bi['’]ll (?:now|start by|begin by)\b", "i"),
)
_FLAGS = {"i": re.IGNORECASE, "m": re.MULTILINE}
_COMPILED = tuple(
    (name, re.compile(pattern, sum(_FLAGS[f] for f in flags)))
    for name, pattern, flags in SLOP_PATTERNS)
_TOKEN = re.compile(r"\w+|[^\w\s]")
_FENCE = re.compile(r"^[ \t]*(?:```|~~~)")
# lean: a single-backtick span only; a double-backtick span holding a
# backtick is graded as prose. Upgrade if a fixture ever needs one.
_INLINE = re.compile(r"`[^`\n]*`")


def count_tokens(text):
    """The proxy unit count of text, 0 for an empty string."""
    return len(_TOKEN.findall(text))


def _blank(text):
    """text with the same length and line breaks, every other character a
    space, so a match position in the mask is a position in the text."""
    return re.sub(r"[^\n]", " ", text)


def _mask_code(text):
    """text with fenced code blocks and inline code spans blanked. An
    unclosed fence blanks to the end, as a renderer shows it."""
    lines, inside = [], False
    for line in text.splitlines(keepends=True):
        if _FENCE.match(line):
            inside = not inside
            lines.append(_blank(line))
        elif inside:
            lines.append(_blank(line))
        else:
            lines.append(_INLINE.sub(lambda m: _blank(m.group(0)), line))
    return "".join(lines)


def slop(text):
    """[(name, matched_text)], one per match outside code, in pattern
    order then text order; [] when clean."""
    masked = _mask_code(text)
    return [(name, text[match.start():match.end()])
            for name, regex in _COMPILED
            for match in regex.finditer(masked)]


def _read_all(paths):
    """([(path, text)], problem): each path read through cli.read_file; the
    first failure wins and nothing is graded."""
    from cli import read_file
    texts = []
    for path in paths:
        text, problem = read_file(path, path, str)
        if problem is None and text is None:
            problem = f"cannot read {path}: no such file"
        if problem:
            return None, f"{LABEL}: {problem}"
        texts.append((path, text))
    return texts, None


def main(argv):
    """`python3 voice_grade.py <reply.md> [<reply.md> ...]` — print each
    file's count, then one line per slop match and the summary. Exit 0
    clean, 1 on any slop, 2 on usage or an unreadable input. Writes
    nothing."""
    from cli import report
    if not argv:
        print(USAGE)
        return 2
    texts, problem = _read_all(argv)
    if problem:
        print(problem)
        return 2
    problems = []
    for path, text in texts:
        print(f"{LABEL}: {path}: {count_tokens(text)} tokens")
        problems += [f'{LABEL}: {path}: {name}: "{matched}"'
                     for name, matched in slop(text)]
    return report(LABEL, problems)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
