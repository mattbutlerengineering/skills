#!/usr/bin/env python3
"""kb_drift: instruction-file drift (issue #682). The claims a repo's
always-loaded instruction files make — CLAUDE.md, AGENTS.md,
.claude/CLAUDE.md and .claude/rules/**/*.md — checked against what is
on disk, as label-prefixed problem strings. Read-only: the
knowledge-base skill turns each into a proposed fix a human promotes.

Four checks, each kept conservative so a finding is a claim that is
false, never a matter of style:

- **dangling paths** — a backticked path, a markdown link target, or
  the script after an interpreter (`python3 x.py`, `bash x.sh`, in
  spans and fenced blocks alike) that does not exist. A token counts
  as a path only when it ends in a known file extension or, holding a
  slash, ends in `/`; placeholders, globs, URLs, `~` and absolute paths
  are skipped, a bare filename resolves anywhere in the repo, and a
  path the root .gitignore covers is generated output, not drift.
- **table drift** — a markdown table whose first header cell says
  "skill" or "agent": a listed name not on disk, and, once such a table
  exists, an on-disk entry no table of that kind lists. Agents are
  named by their frontmatter `name:` — the harness registry's key.
- **slash commands** — a backticked `/name` or `/plugin:name` that no
  in-repo skill or command, no Claude Code built-in, and (for a
  plugin-qualified one) no plugin enabled in .claude/settings.json
  resolves. A user-level install does not count: a checked-in file is
  read by cloud sessions and worktree agents that do not have it.
- **undocumented surfaces** — .claude/agents, .claude/commands,
  .claude/skills, .claude/hooks or plugins holding two or more entries
  while no instruction file names the directory or any entry in it.

A file excuses a token it means to name with `<!-- drift-ignore: a b -->`
(the token as written, whitespace separated).

  python3 kb.py drift [root]
"""
import fnmatch
import os
import re
from pathlib import Path

import cli
from knowledge_plane import fenced, local_link_targets, resolve_link
from protocol import read_frontmatter

LABEL = "drift"
INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md", ".claude/CLAUDE.md")
RULES_DIR = Path(".claude") / "rules"
SURFACES = (".claude/agents", ".claude/commands", ".claude/skills",
            ".claude/hooks", "plugins")
SURFACE_MIN = 2
EXTENSIONS = frozenset((
    "md", "mdx", "py", "js", "mjs", "cjs", "ts", "tsx", "jsx", "json",
    "jsonl", "sh", "bash", "zsh", "yml", "yaml", "toml", "txt", "html",
    "css", "scss", "sql", "go", "rs", "rb", "java", "kt", "swift", "lock",
    "cfg", "ini", "csv", "xml", "svg", "png", "prisma", "graphql", "tf"))
BUILTINS = frozenset((
    "add-dir", "agents", "bug", "clear", "compact", "config", "context",
    "cost", "doctor", "exit", "export", "help", "hooks", "ide", "init",
    "install-github-app", "login", "logout", "mcp", "memory", "model",
    "output-style", "permissions", "plugin", "plugins", "pr-comments",
    "privacy-settings", "release-notes", "resume", "review", "rewind",
    "security-review", "skills", "status", "statusline", "tasks",
    "terminal-setup", "todos", "upgrade", "usage", "vim"))
SKIP_DIRS = frozenset((".git", "node_modules", ".venv", "venv",
                       "__pycache__", "dist", "build"))
KEPT_HIDDEN = frozenset((".claude", ".github", ".claude-plugin"))
SPAN = re.compile(r"`([^`\n]+)`")
COMMAND = re.compile(r"(?:^|\s)(?:python3?|node|bash|sh|zsh|bun|deno|"
                     r"ruby|tsx)\s+(\S+)")
SLASH = re.compile(r"^/([a-z][a-z0-9_-]*)(?::([a-z][a-z0-9_-]*))?(?:\s|$)")
IGNORE = re.compile(r"<!--\s*drift-ignore:\s*(.*?)\s*-->")
LINE_SUFFIX = re.compile(r":\d+(?::\d+)?$")
NOT_PATH = re.compile(r"[<>*{}$?\[\]|\"'=,()@\\]|://|^[~/-]")
TABLE_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
SEPARATOR = re.compile(r"^\|?[\s:|-]+\|?$")


def instruction_files(root):
    """The instruction files present, a symlinked twin once."""
    rules = sorted((root / RULES_DIR).rglob("*.md")) if (
        root / RULES_DIR).is_dir() else []
    seen, found = set(), []
    for path in [root / name for name in INSTRUCTION_FILES] + rules:
        if path.is_file() and path.resolve() not in seen:
            seen.add(path.resolve())
            found.append(path)
    return found


def path_token(token):
    """The repo path a token names, or None when it is not one."""
    token = LINE_SUFFIX.sub("", token.split("#")[0])
    if token.startswith("./"):
        token = token[2:]
    if not token or NOT_PATH.search(token) or any(c.isspace() for c in token):
        return None
    if token.endswith("/") and len(token) > 1:
        return token
    name = token.rsplit("/", 1)[-1]
    if name.startswith(".") and name[1:].lower() in EXTENSIONS:
        return None
    if "." in name and name.rsplit(".", 1)[1].lower() in EXTENSIONS:
        return token
    return None


def _basenames(root):
    """Every file and directory name in the repo, pruning vendored,
    build and hidden trees (.claude and .github excepted) and Claude
    Code worktrees, which are whole second checkouts."""
    names = set()
    for current, dirs, files in os.walk(root):
        here = Path(current)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS
                   and (not d.startswith(".") or d in KEPT_HIDDEN)
                   and (here / d).relative_to(root).as_posix()
                   != ".claude/worktrees"]
        names.update(dirs)
        names.update(files)
    return names


def _ignore_rules(text):
    """(negated, anchored, pattern) per rule line of a .gitignore."""
    rules = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        pattern = line.lstrip("!")
        rules.append((negated, "/" in pattern.rstrip("/"),
                      pattern.strip("/")))
    return rules


def gitignored(rules, token):
    """Whether the root .gitignore covers a token: generated output an
    instruction file rightly names, never drift. The last matching rule
    wins, as in git; a slashless rule matches any path component."""
    parts = token.strip("/").split("/")
    prefixes = ["/".join(parts[:n]) for n in range(1, len(parts) + 1)]
    verdict = False
    for negated, anchored, pattern in rules:
        hit = (any(fnmatch.fnmatchcase(p, pattern) for p in prefixes)
               if anchored else
               any(fnmatch.fnmatchcase(p, pattern) for p in parts))
        if hit:
            verdict = not negated
    return verdict


class Disk:
    """What is on disk that instruction files make claims about."""

    def __init__(self, root):
        self.root = root
        self._names = None
        text, problem = cli.read_file(root / ".gitignore", ".gitignore", str)
        self.problems = [f"{LABEL}: {problem}"] if problem else []
        self.ignore = _ignore_rules(text or "")
        self.skills = self._skills()
        self.agents = self._agents()
        self.plugins = self._plugins()

    def names(self):
        if self._names is None:
            self._names = _basenames(self.root)
        return self._names

    def exists(self, token, base):
        if gitignored(self.ignore, token):
            return True
        if "/" not in token.rstrip("/"):
            return (self.root / token).exists() or token.rstrip(
                "/") in self.names()
        return (self.root / token).exists() or (base / token).exists()

    def _manifest_name(self, plugin_root):
        data, _ = cli.read_file(plugin_root / ".claude-plugin" /
                                "plugin.json", "plugin.json", dict)
        return (data or {}).get("name")

    def _plugin_roots(self):
        roots = []
        if (self.root / ".claude-plugin" / "plugin.json").is_file():
            roots.append(self.root)
        plugins = self.root / "plugins"
        if plugins.is_dir():
            roots += sorted(p for p in plugins.iterdir() if p.is_dir())
        return roots

    def _skills(self):
        found = {}
        for base in [self.root / ".claude"] + self._plugin_roots():
            for skill in sorted(base.glob("skills/*/SKILL.md")):
                found.setdefault(skill.parent.name, skill.parent.relative_to(
                    self.root).as_posix() + "/")
        return found

    def _agents(self):
        found = {}
        for base in [self.root / ".claude"] + self._plugin_roots():
            for path in sorted(base.glob("agents/**/*.md")):
                fields = read_frontmatter(path) or {}
                found.setdefault(fields.get("name") or path.stem,
                                 path.relative_to(self.root).as_posix())
        return found

    def _plugins(self):
        """{plugin name: set of its skill and command names}."""
        found = {}
        for plugin in self._plugin_roots():
            name = self._manifest_name(plugin) or plugin.name
            found[name] = ({p.parent.name for p in
                            plugin.glob("skills/*/SKILL.md")}
                           | {p.stem for p in plugin.glob("commands/**/*.md")})
        return found

    def commands(self):
        return {p.stem for p in (self.root / ".claude").glob(
            "commands/**/*.md")}


def _candidates(line, in_fence):
    """Every path-like token on a line, as written: spans and commands in
    line order. Links are _link_problems' to read."""
    found = [(m.start(1), m.group(1)) for m in COMMAND.finditer(line)] \
        if in_fence else []
    if not in_fence:
        for span in SPAN.finditer(line):
            text = span.group(1).strip()
            if path_token(text):
                found.append((span.start(1), text))
            found += [(span.start(1) + m.start(1), m.group(1))
                      for m in COMMAND.finditer(text)]
    return [token for _, token in sorted(found)]


def _link_problems(disk, rel, number, line, doc, ignored):
    """A line's local links, resolved by knowledge_plane.resolve_link
    (issue #773) — so a fragment, query or leading slash is read the way
    every other caller reads it — then judged, and reported, as the
    repo-root path they name."""
    problems = []
    for written in local_link_targets(line):
        named = resolve_link(disk.root, doc, written)
        token = named and path_token(named.relative_to(disk.root).as_posix())
        if token and written not in ignored and token not in ignored \
                and not disk.exists(token, disk.root):
            problems.append(f"{LABEL}: {rel}:{number} names path {token!r},"
                            " which does not exist")
    return problems


def _path_problems(disk, rel, number, line, in_fence, doc, ignored):
    problems = []
    for written in _candidates(line, in_fence):
        token = path_token(written)
        if token and written not in ignored and token not in ignored \
                and not disk.exists(token, doc.parent):
            problems.append(f"{LABEL}: {rel}:{number} names path {token!r},"
                            " which does not exist")
    return problems + ([] if in_fence else _link_problems(
        disk, rel, number, line, doc, ignored))


def _slash_problems(disk, settings, rel, number, line, ignored):
    problems = []
    for span in SPAN.finditer(line):
        match = SLASH.match(span.group(1).strip())
        if not match or span.group(1).strip().split()[0] in ignored:
            continue
        plugin, name = match.groups() if match.group(2) else (None,
                                                              match.group(1))
        ref = f"/{plugin}:{name}" if plugin else f"/{name}"
        if plugin is None:
            every = set(disk.skills) | disk.commands() | BUILTINS
            if not any(name in names for names in disk.plugins.values()) \
                    and name not in every:
                problems.append(f"{LABEL}: {rel}:{number} references {ref},"
                                " which resolves to no skill or command in"
                                " this repo")
        elif plugin in disk.plugins:
            if name not in disk.plugins[plugin]:
                problems.append(f"{LABEL}: {rel}:{number} references {ref},"
                                f" but plugin {plugin!r} has no skill or"
                                f" command {name!r}")
        elif plugin not in settings:
            problems.append(f"{LABEL}: {rel}:{number} references {ref}, but"
                            f" plugin {plugin!r} is neither in this repo nor"
                            " enabled in .claude/settings.json")
    return problems


def _cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _table_rows(lines):
    """(kind, line number, name) for each named row of a skill or agent
    table; kind is "skill" or "agent"."""
    rows, kind = [], None
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            kind = None
            continue
        if kind is None:
            if index + 1 < len(lines) and SEPARATOR.match(
                    lines[index + 1].strip()):
                head = _cells(line)[0].lower()
                kind = ("skill" if "skill" in head else
                        "agent" if "agent" in head else "")
            continue
        if not kind or SEPARATOR.match(line.strip()):
            continue
        name = _cells(line)[0].strip("`*_ ").lstrip("/")
        if TABLE_NAME.match(name):
            rows.append((kind, index + 1, name))
    return rows


def _table_problems(disk, tables):
    """Listed-but-absent per row, then on-disk-but-unlisted per kind."""
    on_disk = {"skill": disk.skills, "agent": disk.agents}
    problems = [f"{LABEL}: {rel}:{number} lists {kind} {name!r}, which is"
                " not on disk" for rel, kind, number, name in tables
                if name not in on_disk[kind]]
    for kind in ("skill", "agent"):
        listed = {name for _, k, _, name in tables if k == kind}
        if not listed:
            continue
        problems += [f"{LABEL}: {kind} {name!r} is on disk ({where}) but no"
                     f" {kind} table in an instruction file lists it"
                     for name, where in sorted(on_disk[kind].items())
                     if name not in listed]
    return problems


def _surface_problems(root, texts):
    corpus = "\n".join(texts)
    problems = []
    for surface in SURFACES:
        directory = root / surface
        if not directory.is_dir():
            continue
        entries = sorted(p for p in directory.iterdir()
                         if not p.name.startswith("."))
        if len(entries) < SURFACE_MIN or surface in corpus:
            continue
        named = any(re.search(rf"(?<![\w-]){re.escape(p.stem)}(?![\w-])",
                              corpus) for p in entries)
        if not named:
            problems.append(f"{LABEL}: {surface}/ holds {len(entries)}"
                            " entries but no instruction file mentions it"
                            " or any of them")
    return problems


def _enabled_plugins(root):
    data, problem = cli.read_file(root / ".claude" / "settings.json",
                                  ".claude/settings.json", dict)
    if problem:
        return set(), [f"{LABEL}: {problem}"]
    enabled = (data or {}).get("enabledPlugins") or {}
    if not isinstance(enabled, dict):
        return set(), []
    return {key.split("@")[0] for key, on in enabled.items() if on}, []


def _file_problems(disk, settings, path, text):
    rel = path.relative_to(disk.root).as_posix()
    ignored = {token for match in IGNORE.finditer(text)
               for token in match.group(1).split()}
    lines, problems = text.splitlines(), []
    for number, line, fence in fenced(lines):
        if line is None:  # the unclosed event; its lines were read above
            continue
        in_fence = fence is not None
        problems += _path_problems(disk, rel, number, line, in_fence,
                                   path, ignored)
        if not in_fence:
            problems += _slash_problems(disk, settings, rel, number, line,
                                        ignored)
    tables = [(rel, kind, number, name)
              for kind, number, name in _table_rows(lines)
              if name not in ignored]
    return problems, tables


def drift(root):
    """Every instruction-file drift problem under root."""
    root = Path(root)
    files = instruction_files(root)
    if not files:
        return [f"{LABEL}: no instruction file ({', '.join(INSTRUCTION_FILES)},"
                " .claude/rules/**/*.md) to audit"]
    settings, problems = _enabled_plugins(root)
    disk, tables, texts = Disk(root), [], []
    problems += disk.problems
    for path in files:
        text, problem = cli.read_file(path, path.relative_to(
            root).as_posix(), str)
        if problem:
            problems.append(f"{LABEL}: {problem}")
            continue
        texts.append(text)
        found, rows = _file_problems(disk, settings, path, text)
        problems += found
        tables += rows
    return (problems + _table_problems(disk, tables)
            + _surface_problems(root, texts))


def main(argv):
    """`kb.py drift [root]`."""
    if len(argv) > 1:
        print("usage: kb.py drift [root]")
        return 2
    return cli.report(LABEL, drift(argv[0] if argv else "."))
