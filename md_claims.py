#!/usr/bin/env python3
"""md-claims: the claims a human-facing doc makes that a lookup can settle.

The audit skill's markdown-claims mode ships this as its deterministic
half (ADR-0062, issue #685); the judgement half — does the behaviour the
prose describes still hold — is the skill's headless pass, which runs
after this one and never re-reports what it found.

Three claim kinds, each checked against the tree and never executed:

  link     a markdown link outside code: the target exists, relative to
           the linking doc (or the root, for a leading /)
  path     an inline-code path (`src/app.py`, `docs/`, `tool.py:12`): it
           exists at the root, beside the doc, or as the tail of a real
           path; a bare filename may exist anywhere in the tree
  command  a line in a sh/bash/shell/zsh/console fence: the script it runs
           exists, every --flag it passes appears in that script's
           source, a make target is defined, an npm/pnpm/yarn `run`
           script is in package.json. Other programs are not judged.

A line carrying `<!-- md-claims: ignore -->`, and the line after it, are
skipped; on the line before a fence it skips the whole block.

  python3 md_claims.py check [root] [path ...]    problem strings
  python3 md_claims.py extract [root] [path ...]  every claim, as JSON

Root defaults to the working directory. Paths (docs or directories,
relative to root) replace the default set: README and the other root
*.md except the agent-instruction files, plus docs/**/*.md, minus
date-prefixed snapshots, which record what was true on their date.
"""
import json
import os
import re
import shlex
import sys
from pathlib import Path

import cli
from gates import MD_LINK, URL_TARGET
from knowledge_plane import FENCE_OPEN, fence_closes, fence_open

LABEL = "md-claims"
USAGE = "usage: md_claims.py check|extract [root] [path ...]"
IGNORE = "<!-- md-claims: ignore -->"
AGENT_FILES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md")
SNAPSHOT = re.compile(r"^\d{4}-\d{2}-\d{2}-")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
SHELL_LANGS = {"sh", "bash", "shell", "zsh"}
PROMPT_LANGS = {"console", "shell-session"}
INTERPRETERS = {"python", "python3", "node", "bash", "sh", "zsh", "ruby",
                "perl"}
NO_SCRIPT = {"-m", "-c", "-e"}
PACKAGE_RUNNERS = {"npm", "pnpm", "yarn"}
MAKEFILES = ("GNUmakefile", "makefile", "Makefile")
SEPARATORS = {"&&", "||", ";", "|", "&"}
REDIRECTS = {">", ">>", "<", "<<", "<<<", ">&", "<&", "&>"}
INLINE_CODE = re.compile(r"(`+)([^`\n]+?)\1")
PLACEHOLDER = re.compile(r"[<>{}$*?\[\]~|\s]|\.\.\.")
FILE_EXT = re.compile(
    r"\.(md|py|json|ya?ml|toml|sh|js|mjs|cjs|ts|tsx|txt|cfg|ini|lock)$")
PATH_CHARS = re.compile(r"^[\w.@/-]+$")
LINE_SUFFIX = re.compile(r":\d+(-\d+)?$")
TEMPLATE = re.compile(r"<[A-Za-z][^<>]*>")
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")
MAKE_RULE = re.compile(r"^([^\s:=#][^:=#]*?)\s*::?(?!=)")


def doc_set(root, paths=None):
    """(docs as root-relative posix strings, problems) — the default set
    when paths is empty, else every named doc and every *.md under each
    named directory."""
    root = Path(root)
    if paths:
        docs, problems = [], []
        for rel in paths:
            target = root / rel
            if target.is_dir():
                docs += _walk_md(root, target)
            elif target.is_file():
                docs.append(Path(rel).as_posix())
            else:
                problems.append(f"{LABEL}: {rel} does not exist")
        return docs, problems
    docs = [p.name for p in sorted(root.glob("*.md"))
            if p.name not in AGENT_FILES]
    if (root / "docs").is_dir():
        docs += _walk_md(root, root / "docs")
    return docs, []


def _walk_md(root, top):
    found = []
    for path in sorted(top.rglob("*.md")):
        if SKIP_DIRS & set(path.relative_to(root).parts):
            continue
        if not SNAPSHOT.match(path.name):
            found.append(path.relative_to(root).as_posix())
    return found


def claims_in(text):
    """[(line, kind, text)] for one doc's text. A command's claim text
    is the command as one line; the checker re-splits its tokens."""
    lines = text.splitlines()
    ignored = {n for n, line in enumerate(lines, 1) if IGNORE in line}
    ignored |= {n + 1 for n in ignored}
    found, fence, block = [], None, []
    for number, line in enumerate(lines, 1):
        if fence:
            if fence_closes(line, fence[0], fence[1]):
                found += _block_claims(*fence[2:], block)
                fence, block = None, []
            else:
                block.append((number, line))
            continue
        opened = fence_open(line)
        if opened:
            info = FENCE_OPEN.match(line).group("info").strip().lower()
            lang = info.split()[0] if info else ""
            fence = (*opened, lang, number in ignored)
            continue
        if number not in ignored:
            found += _prose_claims(number, line)
    return found


def _prose_claims(number, line):
    found = [(number, "path", span)
             for _, span in INLINE_CODE.findall(line) if _is_path(span)]
    bare = INLINE_CODE.sub(lambda m: " " * len(m.group(0)), line)
    links = [(number, "link", target) for target in MD_LINK.findall(bare)
             if not URL_TARGET.match(target) and not target.startswith("#")]
    return links + found


def _is_path(span):
    """Does an inline-code span name a repo path? It must be path-shaped
    (no placeholder, glob, whitespace or URL), not absolute or a flag, and
    either be a directory below the top level (`src/lib/`) or a file with
    a named stem and a known extension — `owner/repo`, `x.y`, `.py` and a
    bare `routine/` prefix are not paths."""
    span = LINE_SUFFIX.sub("", span.strip())
    if not PATH_CHARS.match(span) or span.startswith(("-", "/")):
        return False
    if span.endswith("/"):
        return "/" in span[:-1]
    ext = FILE_EXT.search(span.rsplit("/", 1)[-1])
    return bool(ext) and ext.start() > 0


def _block_claims(lang, skipped, block):
    """Commands in one fenced block: `$ ` prompts stripped (and required,
    in a console block), backslash continuations and open quotes joined
    onto the line that started them, comments and heredoc bodies
    skipped."""
    if skipped or lang not in SHELL_LANGS | PROMPT_LANGS:
        return []
    found, pending, heredoc = [], None, None
    for number, raw in block:
        line = raw.strip()
        if heredoc:
            heredoc = None if line == heredoc else heredoc
            continue
        if pending:
            number, head, joint = pending
            line, pending = f"{head}{joint}{line}", None
        elif lang in PROMPT_LANGS:
            if not line.startswith("$ "):
                continue
            line = line[2:].strip()
        elif line.startswith("$ "):
            line = line[2:].strip()
        if line.endswith("\\"):
            pending = (number, line[:-1].strip(), " ")
            continue
        if not line or line.startswith("#"):
            continue
        if _open_quote(line):
            pending = (number, line, "\n")
            continue
        marker = HEREDOC.search(line)
        heredoc = marker.group(1) if marker else None
        found.append((number, "command", line))
    return found


def _open_quote(line):
    try:
        shlex.split(line, comments=True)
    except ValueError:
        return True
    return False


def extract(root, paths=None):
    """Every claim in the doc set, as {file, line, kind, text} records."""
    root = Path(root)
    docs, _ = doc_set(root, paths)
    return [{"file": doc, "line": line, "kind": kind, "text": text}
            for doc in docs
            for line, kind, text in claims_in(_read(root, doc)[0] or "")]


def _read(root, doc):
    text, problem = cli.read_file(root / doc, doc, str)
    return text, problem and f"{LABEL}: {problem}"


def check(root, paths=None):
    """Every claim in the doc set that the tree contradicts, as problem
    strings."""
    root = Path(root)
    docs, problems = doc_set(root, paths)
    index = _tree_index(root)
    for doc in docs:
        text, unreadable = _read(root, doc)
        if unreadable:
            problems.append(unreadable)
            continue
        for line, kind, claim in claims_in(text or ""):
            problems += [f"{LABEL}: {doc}:{line}: {found}"
                         for found in _verify(root, index, doc, kind, claim)]
    return problems


def _tree_index(root):
    """(every root-relative path, every basename) in the tree — files and
    directories, minus SKIP_DIRS."""
    rels, names = set(), set()
    for top, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        base = Path(top).relative_to(root)
        for name in dirs + files:
            rels.add((base / name).as_posix())
            names.add(name)
    return rels, names


def _verify(root, index, doc, kind, text):
    doc_dir = (root / doc).parent
    if kind == "link":
        target = text.split("#", 1)[0].split("?", 1)[0]
        base = root if target.startswith("/") else doc_dir
        if target and not (base / target.lstrip("/")).exists():
            return [f"link target {text.split('#', 1)[0]!r} does not exist"]
        return []
    if kind == "path":
        return [] if _path_exists(root, index, doc_dir, text) else [
            f"path {LINE_SUFFIX.sub('', text.strip())!r} does not exist"]
    return _verify_command(root, doc_dir, text)


def _path_exists(root, index, doc_dir, span):
    span = LINE_SUFFIX.sub("", span.strip()).rstrip("/")
    rels, names = index
    if (root / span).exists() or (doc_dir / span).exists():
        return True
    if "/" not in span:
        return span in names
    tail = re.sub(r"^(\.\.?/)+", "", span)
    return any(rel == tail or rel.endswith("/" + tail) for rel in rels)


def _verify_command(root, doc_dir, line):
    if TEMPLATE.search(line):
        return []
    try:
        lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []
    problems, cwd = [], root
    for segment in _segments(tokens):
        if cwd is None:
            break
        if segment[0] == "cd":
            cwd = _cd(cwd, segment)
            continue
        problems += _verify_segment(root, cwd, doc_dir, segment)
    return problems


def _segments(tokens):
    segment, skip = [], False
    for token in tokens:
        if skip:
            skip = False
        elif token in SEPARATORS:
            if segment:
                yield segment
            segment = []
        elif token in REDIRECTS or token.endswith((">", "<")):
            skip = True
        elif segment or not re.match(r"^\w+=", token):
            segment.append(token)
    if segment:
        yield segment


def _cd(cwd, segment):
    if len(segment) != 2 or PLACEHOLDER.search(segment[1]):
        return None
    return cwd / segment[1]


def _verify_segment(root, cwd, doc_dir, segment):
    program, args = segment[0], segment[1:]
    if PLACEHOLDER.search(program):
        return []
    if program == "make":
        return _verify_make(root, cwd, args)
    if program in PACKAGE_RUNNERS:
        return _verify_package(root, cwd, args)
    if program in INTERPRETERS:
        for at, arg in enumerate(args):
            if arg in NO_SCRIPT:
                return []
            if not arg.startswith("-"):
                return _verify_script(root, cwd, doc_dir, arg, args[at + 1:])
        return []
    if "/" in program:
        return _verify_script(root, cwd, doc_dir, program, args)
    return []


def _verify_script(root, cwd, doc_dir, script, args):
    if PLACEHOLDER.search(script) or script.startswith("/"):
        return []
    found = next((base / script for base in (cwd, doc_dir)
                  if (base / script).is_file()), None)
    if found is None:
        return [f"command runs {script.removeprefix('./')!r}, which does"
                " not exist"]
    source, _ = cli.read_file(found, script, str)
    if source is None:
        return []
    shown = found.relative_to(root).as_posix()
    return [f"flag {flag!r} does not appear in {shown}"
            for flag in _long_flags(args)
            if not re.search(rf"(?<![\w-]){re.escape(flag)}(?![\w-])",
                             source)]


def _long_flags(args):
    return [arg.split("=", 1)[0] for arg in args
            if arg.startswith("--") and len(arg) > 2
            and not PLACEHOLDER.search(arg.split("=", 1)[0])]


def _verify_make(root, cwd, args):
    targets, at = [], 0
    while at < len(args):
        arg = args[at]
        if arg == "-C" and at + 1 < len(args):
            cwd, at = cwd / args[at + 1], at + 2
            continue
        if not arg.startswith("-") and "=" not in arg:
            targets.append(arg)
        at += 1
    where = cwd.relative_to(root).as_posix() if cwd.is_relative_to(root) \
        else str(cwd)
    # Listed, not probed: a case-insensitive filesystem answers is_file()
    # for every spelling, and the message names the one on disk.
    present = set(os.listdir(cwd)) if cwd.is_dir() else set()
    makefile = next((cwd / n for n in MAKEFILES if n in present), None)
    if makefile is None:
        return [f"command runs make, but no Makefile exists in {where}"]
    text, _ = cli.read_file(makefile, where, str)
    rules = {name for line in (text or "").splitlines()
             for match in [MAKE_RULE.match(line)] if match
             for name in match.group(1).split()}
    shown = makefile.relative_to(root).as_posix()
    return [f"make target {target!r} is not defined in {shown}"
            for target in targets
            if target not in rules and not PLACEHOLDER.search(target)]


def _verify_package(root, cwd, args):
    if len(args) < 2 or args[0] not in ("run", "run-script"):
        return []
    name = args[1]
    if PLACEHOLDER.search(name):
        return []
    package = cwd / "package.json"
    shown = package.relative_to(root).as_posix()
    data, problem = cli.read_file(package, shown, dict)
    if data is None and problem is None:
        where = cwd.relative_to(root).as_posix()
        return [f"command runs {args[0]} {name}, but no package.json exists"
                f" in {where}"]
    if problem:
        return [problem]
    scripts = data.get("scripts")
    if not isinstance(scripts, dict) or name not in scripts:
        return [f"script {name!r} is not defined in {shown}"]
    return []


def main(argv):
    """`python3 md_claims.py <check|extract> [root] [path ...]`."""
    if not argv or argv[0] not in ("check", "extract"):
        print(USAGE)
        return 2
    root = argv[1] if len(argv) > 1 else "."
    paths = argv[2:] or None
    if argv[0] == "extract":
        print(json.dumps(extract(root, paths), indent=2))
        return 0
    docs, _ = doc_set(root, paths)
    return cli.report(LABEL, check(root, paths),
                      suffix=f" across {len(docs)} doc(s)")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
