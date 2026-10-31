#!/usr/bin/env python3
"""kb_harvest: mine Claude Code session transcripts for knowledge-base
candidates (issue #681). The deterministic half of the knowledge-base
skill's transcript-harvest ingest; the judgement half — which candidate
is a non-inferable fact, and where it goes — stays in the skill.

Two shapes are mined:

- **arcs**: a check (a Bash command) fails, files are edited, and the
  same check later passes in the same session. A failure followed by a
  pass with no edit between is a flake or a retry, never an arc.
- **recurring errors**: the same tool error, digits and shas
  normalized, seen two or more times across the scanned transcripts.

The tool only reads. It prints candidates as JSON for the skill to turn
into proposals a human promotes; nothing is written anywhere. Transcript
text is untrusted data, and the excerpts it prints are capped.

Transcripts live in `<projects dir>/<slug>/`, where the projects dir is
`$CLAUDE_CONFIG_DIR/projects` or `~/.claude/projects`, and the slug is
the repo's absolute path with every non-alphanumeric character turned
into `-` (older harnesses kept dots; paths past 200 characters are cut
and given a hash suffix). Claude Code worktrees of the repo
(`.claude/worktrees/*`) get their own slug beside it and are scanned too.
Run from a linked worktree, the root resolves to the main checkout (the
parent of git's common dir) first, so the same transcripts are found.

  python3 kb.py harvest [root] [--days N] [--session ID]
                        [--projects-dir DIR]

No flag scans the newest top-level session; --days N scans every
transcript, subagents included, modified in the last N days.
"""
import json
import os
import re
import time
from pathlib import Path

import cli

LABEL = "harvest"
SLUG_LIMIT = 200
EXCERPT = 160
RECURRING = 2
EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
EXIT_LINE = re.compile(r"^Exit code (\d+)$")
FAIL_LINE = re.compile(r"error|fail|traceback|problem\(s\)|not found|"
                       r"denied|refus|stale|drift|out of sync", re.I)
NOT_ERRORS = ("The user doesn't want to proceed", "[Request interrupted")
SEGMENT = re.compile(r"&&|\|\||;|\|")
ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=\S*$")
SHA = re.compile(r"\b[0-9a-f]{7,40}\b")
DIGITS = re.compile(r"\d+")


def slug(path):
    """The harness's project-directory name for an absolute path."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def legacy_slug(path):
    """The name older harnesses gave it: separators only."""
    return re.sub(r"[/\\:]", "-", str(path))


def projects_dir():
    base = os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"
    return Path(base) / "projects"


def project_dirs(root, projects):
    """The repo's transcript directory, then its worktrees', sorted."""
    projects, root = Path(projects), str(Path(root).absolute())
    if not projects.is_dir():
        return []
    names = {entry.name for entry in projects.iterdir() if entry.is_dir()}
    found = []
    for name in (slug(root), legacy_slug(root)):
        if len(name) > SLUG_LIMIT:
            found += sorted(n for n in names
                            if n.startswith(name[:SLUG_LIMIT] + "-"))
        elif name in names:
            found.append(name)
            found += sorted(n for n in names
                            if n.startswith((name + "--claude-worktrees-",
                                             name + "-.claude-worktrees-")))
        if found:
            break
    return [projects / name for name in found]


def select(dirs, days, session, now):
    """The transcripts to scan: one named session, every one modified in
    the last `days`, or the newest top-level session."""
    if session is not None:
        return [path for d in dirs[:1]
                for path in [Path(session) if Path(session).is_file()
                             else d / f"{session}.jsonl"] if path.is_file()]
    if days is not None:
        cutoff = now - days * 86400
        return sorted(path for d in dirs for path in d.rglob("*.jsonl")
                      if path.stat().st_mtime >= cutoff)
    top = [path for d in dirs[:1] for path in d.glob("*.jsonl")
           if not path.name.startswith("agent-")]
    return sorted(top, key=lambda p: p.stat().st_mtime)[-1:]


def check_key(command):
    """A command's identity across retries: its first segment that is
    not a `cd`, without env assignments, cut to three words."""
    for segment in SEGMENT.split(command):
        words = [w for w in segment.split() if not ENV_ASSIGN.match(w)]
        if words and words[0] not in ("cd", "export", "set", "source"):
            return " ".join(words[:3])
    return command.strip()[:EXCERPT]


def _text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(item.get("text", "") for item in content
                         if isinstance(item, dict))
    return ""


def _failed(item, text):
    first = text.strip().splitlines()[0] if text.strip() else ""
    exit_line = EXIT_LINE.match(first)
    return (item.get("is_error") is True
            or bool(exit_line and exit_line.group(1) != "0"))


def excerpt(text):
    """The line that says what failed: the first matching FAIL_LINE,
    else the first non-empty line that is not the exit code."""
    lines = [line.strip() for line in text.splitlines()
             if line.strip() and not EXIT_LINE.match(line.strip())]
    pick = next((line for line in lines if FAIL_LINE.search(line)),
                lines[0] if lines else "")
    return pick[:EXCERPT]


def _relative(path, cwd):
    try:
        return Path(path).relative_to(cwd).as_posix()
    except ValueError:
        return str(path)


def events(records):
    """(kind, detail) per tool call in transcript order: ("bash", dict)
    with check, command, failed, failure, at, session; ("edit", path);
    ("error", dict) with tool, error, example, session."""
    uses = {}
    for record in records:
        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_use":
                uses[item.get("id")] = (item.get("name"),
                                        item.get("input") or {}, record)
                if item.get("name") in EDIT_TOOLS:
                    inputs = item.get("input") or {}
                    path = inputs.get("file_path") or inputs.get(
                        "notebook_path")
                    if path:
                        yield "edit", _relative(path, record.get("cwd", ""))
            elif item.get("type") == "tool_result":
                yield from _result(uses.get(item.get("tool_use_id")), item,
                                   record)


def _result(use, item, record):
    if use is None:
        return
    name, inputs, _ = use
    text = _text(item.get("content"))
    failed = _failed(item, text) and not text.startswith(NOT_ERRORS)
    session = record.get("sessionId", "")
    command = inputs.get("command", "") if name == "Bash" else ""
    if failed:
        yield "error", {"tool": name, "error": excerpt(text),
                        "example": check_key(command) if command else name,
                        "session": session}
    if command:
        yield "bash", {"check": check_key(command), "failed": failed,
                       "failure": excerpt(text) if failed else "",
                       "at": record.get("timestamp", ""),
                       "session": session}


def arcs(stream):
    """Failed -> edited -> passed arcs, one per check that recovered."""
    found, open_ = [], {}
    for kind, detail in stream:
        if kind == "edit":
            for pending in open_.values():
                if detail not in pending["fixed_by"]:
                    pending["fixed_by"].append(detail)
        elif kind == "bash" and detail["failed"]:
            pending = open_.setdefault(detail["check"], {
                "check": detail["check"], "failure": detail["failure"],
                "fixed_by": [], "attempts": 0,
                "session": detail["session"], "failed_at": detail["at"]})
            pending["attempts"] += 1
        elif kind == "bash" and detail["check"] in open_:
            pending = open_.pop(detail["check"])
            if pending["fixed_by"]:
                found.append({**pending, "fixed_by": sorted(
                    pending["fixed_by"]), "passed_at": detail["at"]})
    return found


def normalize(error):
    return " ".join(DIGITS.sub("N", SHA.sub("<sha>", error)).split())


def recurring(errors):
    """Error classes seen RECURRING or more times, most frequent first."""
    groups = {}
    for err in errors:
        key = (err["tool"], normalize(err["error"]))
        if not key[1]:
            continue
        group = groups.setdefault(key, {"tool": key[0], "error": key[1],
                                        "count": 0, "sessions": set(),
                                        "example": err["example"]})
        group["count"] += 1
        group["sessions"].add(err["session"])
    return sorted(({**g, "sessions": len(g["sessions"])}
                   for g in groups.values() if g["count"] >= RECURRING),
                  key=lambda g: (-g["count"], g["tool"], g["error"]))


def _records(text):
    records, skipped = [], 0
    for _, record, err in cli.json_lines(text):
        if err is not None:
            skipped += 1
            continue
        if isinstance(record, dict):
            records.append(record)
        else:
            skipped += 1
    return records, skipped


def mine(paths):
    """(result, problems) for the transcripts at paths."""
    found, errors, problems, skipped = [], [], [], 0
    for path in paths:
        text, problem = cli.read_file(path, str(path), str)
        if problem:
            problems.append(f"{LABEL}: {problem}")
            continue
        records, bad = _records(text or "")
        skipped += bad
        stream = list(events(records))
        found += arcs(stream)
        errors += [detail for kind, detail in stream if kind == "error"]
    return {"scanned": {"transcripts": len(paths) - len(problems),
                        "skipped_lines": skipped},
            "arcs": found, "recurring_errors": recurring(errors)}, problems


def main_checkout(root):
    """root's main checkout: the parent of git's common dir, so a linked
    worktree finds the transcripts filed under the main checkout's slug
    (#710). root itself when git cannot say (not a repo, no git), and
    exactly as given when it already is the main checkout."""
    root = Path(root).absolute()
    try:
        out = cli.runner("git")(["-C", str(root), "rev-parse",
                                 "--path-format=absolute",
                                 "--git-common-dir"]).stdout
    except cli.CLI_FAILURES:
        return root
    main = Path(out.strip()).parent
    return root if main == root.resolve() else main


def harvest(root, projects=None, days=None, session=None, now=None):
    """(result, problems): the candidates in root's transcripts."""
    projects = Path(projects) if projects else projects_dir()
    checkout = main_checkout(root)
    dirs = project_dirs(checkout, projects)
    if not dirs:
        return None, [f"{LABEL}: no Claude Code transcripts for {root}"
                      f" under {projects} (looked for {slug(checkout)})"]
    paths = select(dirs, days, session, time.time() if now is None else now)
    if session is not None and not paths:
        return None, [f"{LABEL}: no session transcript {session!r} in"
                      f" {dirs[0]}"]
    result, problems = mine(paths)
    result["scanned"]["dirs"] = [str(d) for d in dirs]
    return result, problems


USAGE = ("usage: kb.py harvest [root] [--days N] [--session ID]"
         " [--projects-dir DIR]")


def _options(argv):
    """(root, options, problems) from harvest's own arguments."""
    root, options, problems, rest = ".", {}, [], list(argv)
    flags = {"--days": "days", "--session": "session",
             "--projects-dir": "projects"}
    while rest:
        arg = rest.pop(0)
        if arg in flags and rest:
            options[flags[arg]] = rest.pop(0)
        elif arg.startswith("-"):
            return None, None, [USAGE]
        else:
            root = arg
    days = options.get("days")
    if days is not None:
        if not (days.isdigit() and int(days) > 0):
            problems.append(f"{LABEL}: --days must be a positive whole"
                            f" number, got {days!r}")
        else:
            options["days"] = int(days)
    return root, options, problems


def main(argv):
    """`kb.py harvest ...`: candidates as JSON, or problem strings."""
    root, options, problems = _options(argv)
    if root is None:
        print(problems[0])
        return 2
    if problems:
        return cli.report(LABEL, problems)
    result, problems = harvest(root, **options)
    if problems:
        return cli.report(LABEL, problems)
    print(json.dumps(result, indent=2))
    return 0
