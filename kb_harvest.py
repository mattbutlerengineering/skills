#!/usr/bin/env python3
"""kb_harvest: mine Claude Code session transcripts for knowledge-base
candidates (issue #681). The deterministic half of the knowledge-base
skill's transcript-harvest ingest; the judgement half — which candidate
is a non-inferable fact, and where it goes — stays in the skill.

Three shapes are mined:

- **arcs**: a check (a Bash command) fails, files are edited, and the
  same check later passes in the same session. A failure followed by a
  pass with no edit between is a flake or a retry, never an arc.
- **recurring errors**: the same tool error, digits and shas
  normalized, seen two or more times across the scanned transcripts.
- **human turns**: in a top-level transcript, a human turn that
  corrects the agent turn before it (its opening words), or answers an
  agent question (a text turn ending in `?`, or the question tool),
  under its own `human_turns` key. Approvals, plain instructions,
  harness-injected turns and subagent transcripts yield none.

On `--memory` it also lists the harness's auto-memory entries for the
repo (`memory/` beside the main checkout's transcripts), each paired by
file-name tokens with the page it may duplicate. An entry typed `user`
is counted and nothing else about it is kept; an entry whose type
cannot be read is counted as skipped, never listed. The two new sources
adapt practices from anthropics/knowledge-work-plugins (Apache-2.0).

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
                        [--projects-dir DIR] [--memory]

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
QUESTION_TOOL = "AskUserQuestion"
# A human turn whose opening words push back on what the agent just did.
CORRECTION = re.compile(
    r"^(no|nope|don'?t|do not|stop|wait|actually|wrong|that'?s (not|wrong)"
    r"|not that|instead|undo|revert|why did you"
    r"|you (should|shouldn'?t|didn'?t|forgot)|never|double[- ]check)\b")
# Replies that only say "carry on": an answer to nothing worth keeping.
APPROVALS = frozenset((
    "yes", "y", "ok", "okay", "go ahead", "sure", "do it", "continue",
    "proceed", "lgtm", "sounds good", "yep", "please do"))
PUNCT = re.compile(r"[^\w\s']")
MEMORY_DIR = "memory"
MEMORY_INDEX = "MEMORY.md"
LISTED_TYPES = ("feedback", "project", "reference")
TYPE_LINE = re.compile(r"^\s*type:\s*(.*?)\s*$")
FIELD_LINE = re.compile(r"^(name|description):\s*(.*?)\s*$")
# A memory file pairs with a page sharing at least this many file-name
# tokens; a miss is cheap, since ingest's dedupe step still greps.
PAIR_MIN = 2
STOPWORDS = frozenset(("a", "an", "and", "the", "of", "to", "in", "on",
                       "for", "is", "by", "with", "no", "not", "only"))
TOKEN_SPLIT = re.compile(r"[^A-Za-z0-9]+")
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


def _line(text):
    """text's last non-empty line, whitespace collapsed."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines[-1].split()) if lines else ""


def _clip(text):
    return " ".join(text.split())[:EXCERPT]


def _action(item, cwd):
    """`<tool>: <what it acted on>` for an agent tool_use."""
    name, inputs = item.get("name"), item.get("input") or {}
    if name == "Bash" and inputs.get("command"):
        what = check_key(inputs["command"])
    elif inputs.get("file_path") or inputs.get("notebook_path"):
        what = _relative(inputs.get("file_path")
                         or inputs.get("notebook_path"), cwd)
    else:
        questions = inputs.get("questions")
        first = questions[0] if isinstance(questions, list) and questions \
            else {}
        what = first.get("question", "") if isinstance(first, dict) else ""
    return _clip(f"{name}: {what}" if what else str(name))


def _human_kind(text, agent):
    """(kind, signal) for a human text turn after the agent turn, or
    None when it is neither a correction nor an answer."""
    lowered = text.strip().lower()
    if CORRECTION.match(lowered):
        return "correction", "correction-wording"
    reply = " ".join(PUNCT.sub("", lowered).split())
    if agent["question"] and reply not in APPROVALS:
        return "answer", "after-agent-question"
    return None


def human_turns(records):
    """Corrections and answered questions in one top-level transcript.
    A human turn counts only after an agent turn, which it consumes, so
    two human turns in a row yield at most one candidate."""
    found, agent, asked = [], None, {}

    def turn(kind, signal, human, said, record):
        found.append({"kind": kind, "signal": signal, "human": _clip(human),
                      "agent": said, "session": record.get("sessionId", ""),
                      "at": record.get("timestamp", "")})

    for record in records:
        message = record.get("message")
        if record.get("isSidechain") or record.get("isMeta") \
                or not isinstance(message, dict):
            continue
        content = message.get("content")
        items = content if isinstance(content, list) else [
            {"type": "text", "text": content}] if isinstance(
                content, str) else []
        items = [item for item in items if isinstance(item, dict)]
        if record.get("type") == "assistant":
            for item in items:
                if item.get("type") == "text" and _line(item.get("text", "")):
                    said = _line(item["text"])
                    agent = {"excerpt": said[:EXCERPT],
                             "question": said.endswith("?")}
                elif item.get("type") == "tool_use":
                    said = _action(item, record.get("cwd", ""))
                    agent = {"excerpt": said, "question": False}
                    if item.get("name") == QUESTION_TOOL:
                        asked[item.get("id")] = said
            continue
        if record.get("type") != "user":
            continue
        results = [item for item in items
                   if item.get("type") == "tool_result"]
        for item in results:
            said = asked.pop(item.get("tool_use_id"), None)
            text = _text(item.get("content"))
            if said is not None and not _failed(item, text) \
                    and not text.startswith(NOT_ERRORS):
                turn("answer", "question-tool", text, said, record)
        if results:
            continue
        text = _text(items).strip()
        if not text or text.startswith("<") or text.startswith(NOT_ERRORS):
            continue
        if agent is not None:
            kind = _human_kind(text, agent)
            if kind:
                turn(*kind, text, agent["excerpt"], record)
        agent = None
    return found


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
    found, errors, problems, skipped, turns = [], [], [], 0, []
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
        if not Path(path).name.startswith("agent-"):
            turns += human_turns(records)
    return {"scanned": {"transcripts": len(paths) - len(problems),
                        "skipped_lines": skipped},
            "arcs": found, "recurring_errors": recurring(errors),
            "human_turns": turns}, problems


def _block(text):
    """The lines of text's leading `---` frontmatter block, or None."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = next((i for i, line in enumerate(lines[1:], 1)
                if line.strip() == "---"), None)
    return None if end is None else lines[1:end]


def memory_type(text):
    """One of LISTED_TYPES, "user", or None (skip): exactly one distinct
    `type:` value, at any indentation, inside the frontmatter block."""
    block = _block(text)
    if block is None:
        return None
    values = {match.group(1).strip("'\"") for line in block
              if (match := TYPE_LINE.match(line))}
    if len(values) != 1:
        return None
    value = values.pop()
    return value if value == "user" or value in LISTED_TYPES else None


def _tokens(name):
    words = [w.lower() for w in TOKEN_SPLIT.split(name) if w]
    # A plural's one trailing s is cut; a double ss (cross) is a stem.
    return [w[:-1] if len(w) > 3 and w.endswith("s")
            and not w.endswith("ss") else w
            for w in words if w not in STOPWORDS]


def pair(stem, slugs):
    """(slug, shared tokens in the slug's order) for the page sharing the
    most file-name tokens with stem, at least PAIR_MIN; ties go to the
    first slug in sorted order. (None, []) below that."""
    mine, best = set(_tokens(stem)), (None, [])
    for slug in sorted(slugs):
        shared = [t for t in dict.fromkeys(_tokens(slug)) if t in mine]
        if len(shared) >= PAIR_MIN and len(shared) > len(best[1]):
            best = (slug, shared)
    return best


def memory_candidates(memory_dir, pages):
    """The memory object: every *.md directly in memory_dir except the
    index, typed by memory_type and paired against pages, a mapping of
    page slug to its repo-relative path. User-scoped entries are only
    counted; unreadable or untyped ones are counted as skipped."""
    memory_dir = Path(memory_dir)
    result = {"dir": str(memory_dir), "listed": 0, "user_scoped": 0,
              "skipped": 0, "candidates": []}
    for path in sorted(memory_dir.glob("*.md")):
        if path.name == MEMORY_INDEX or not path.is_file():
            continue
        text, problem = cli.read_file(path, path.name, str)
        kind = None if problem or text is None else memory_type(text)
        if kind is None:
            result["skipped"] += 1
            continue
        if kind == "user":
            result["user_scoped"] += 1
            continue
        fields = dict(match.groups() for line in _block(text)
                      if (match := FIELD_LINE.match(line)))
        slug, shared = pair(path.stem, pages)
        result["listed"] += 1
        result["candidates"].append({
            "file": path.name, "name": fields.get("name") or path.stem,
            "type": kind,
            "description": _clip(fields.get("description", "")),
            "page": pages[slug] if slug else None, "shared": shared})
    return result


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


def _pages(root, kb_dir):
    """Page slug -> repo-relative path for the pages under kb_dir; empty
    when there is no kb_dir or no directory there."""
    if kb_dir is None:
        return {}
    folder = Path(root) / kb_dir
    return {path.stem: (Path(kb_dir) / path.name).as_posix()
            for path in sorted(folder.glob("*.md"))} if folder.is_dir() \
        else {}


def harvest(root, projects=None, days=None, session=None, now=None,
            memory=False, kb_dir=None):
    """(result, problems): the candidates in root's transcripts and, with
    memory, its auto-memory entries paired with the pages in kb_dir."""
    projects = Path(projects) if projects else projects_dir()
    checkout = main_checkout(root)
    dirs = project_dirs(checkout, projects)
    if not dirs:
        return None, [f"{LABEL}: no Claude Code transcripts for {root}"
                      f" under {projects} (looked for {slug(checkout)})"]
    memory_dir = dirs[0] / MEMORY_DIR
    if memory and not memory_dir.is_dir():
        return None, [f"{LABEL}: no memory directory at {memory_dir}"]
    paths = select(dirs, days, session, time.time() if now is None else now)
    if session is not None and not paths:
        return None, [f"{LABEL}: no session transcript {session!r} in"
                      f" {dirs[0]}"]
    result, problems = mine(paths)
    result["scanned"]["dirs"] = [str(d) for d in dirs]
    if memory:
        result["memory"] = memory_candidates(memory_dir,
                                             _pages(root, kb_dir))
    return result, problems


USAGE = ("usage: kb.py harvest [root] [--days N] [--session ID]"
         " [--projects-dir DIR] [--memory]")


def _options(argv):
    """(root, options, problems) from harvest's own arguments."""
    root, options, problems, rest = ".", {}, [], list(argv)
    flags = {"--days": "days", "--session": "session",
             "--projects-dir": "projects"}
    while rest:
        arg = rest.pop(0)
        if arg == "--memory":
            options["memory"] = True
        elif arg in flags and rest:
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


def main(argv, kb_dir=None):
    """`kb.py harvest ...`: candidates as JSON, or problem strings.
    kb_dir is the page directory kb.py owns, for memory pairing."""
    root, options, problems = _options(argv)
    if root is None:
        print(problems[0])
        return 2
    if problems:
        return cli.report(LABEL, problems)
    result, problems = harvest(root, kb_dir=kb_dir, **options)
    if problems:
        return cli.report(LABEL, problems)
    print(json.dumps(result, indent=2))
    return 0
