#!/usr/bin/env python3
"""pr-body-preflight: refuse a `gh pr create` whose body would fail detector B.

A Claude Code PreToolUse hook on Bash, registered in this repo's checked-in
.claude/settings.json and run by filename with the hook payload (JSON) on
stdin. Detector B (gates.check_pr_traceability) reads the PR body from the
CI event, so locally it skips and only fails once the PR is open
(docs/kb/pr-body-contract.md). This applies the same rule, through B's one
owner gates.pr_body_problems, before the PR exists.

  exit 2   a body the hook read exactly and B judged failing: B's strings
           on stderr, one per line, then a pointer at the kb page
  exit 0   everything else: silent, or one `pr-body-preflight: not checked
           — <reason>` note per `gh pr create` whose body it cannot read

It fails open: an unreadable body, an unparsable command, a PR aimed at
another repository or any exception is exit 0, and CI's B still judges
that PR. Heredoc bodies and comments are never read as commands.
Root-only (not mirrored).

  python3 pr_body_preflight.py < payload.json
"""
import json
import os
import re
import shlex
import sys
from pathlib import Path

NOTE = "pr-body-preflight: not checked — {}"
POINTER = ("pr-body-preflight: the body contract is "
           "docs/kb/pr-body-contract.md")
NOT_SEEN = 'saw "gh pr create" but found no such command'

PUNCTUATION = ";&|()<>\n"
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
# gh pr create flags whose next argument is their value, so that value is
# never mistaken for a flag of its own.
VALUE_FLAGS = frozenset({
    "-t", "--title", "-B", "--base", "-H", "--head", "-a", "--assignee",
    "-l", "--label", "-m", "--milestone", "-p", "--project",
    "-r", "--reviewer", "-R", "--repo"})
# Flags that leave the body to gh (commits, a browser, an editor, a
# template or a saved draft), so the hook cannot know it. -f is --fill's
# shorthand.
DEFERRING_FLAGS = frozenset({
    "--fill", "--fill-first", "--fill-verbose", "-f", "--web", "-w",
    "--editor", "-e", "--template", "-T", "--recover"})
# Commands that move the shell before a later gh pr create runs.
DIRECTORY_CHANGERS = frozenset({"cd", "pushd", "popd"})
REMOTE_URL = re.compile(r"(?:push)?url\s*=\s*(?P<url>\S+)$")
# The opening of a heredoc command substitution, `$(cat <<'D'` and kin.
HEREDOC_OPEN = re.compile(
    r"\$\(\s*cat\s+<<(?P<dash>-?)[ \t]*(?P<quote>['\"]?)"
    r"(?P<delim>[A-Za-z_][A-Za-z0-9_]*)(?P=quote)[ \t]*\n")
HEREDOC_CLOSE = re.compile(r"\s*\)")
PLACEHOLDER = "__pr_body_preflight_heredoc_{}__"
PLACEHOLDER_WORD = re.compile(r"__pr_body_preflight_heredoc_(\d+)__")
# `$(cat PATH)` or `$(< PATH)` with a plain path: read as a body file.
CAT_FILE = re.compile(
    r"\$\(\s*(?:cat\s+|<\s*)(?P<path>[^\s$`'\"()<>|;&\\]+)\s*\)")


def _heredoc_at(command, match):
    """(body, end) for the heredoc substitution whose opening is match,
    or None when its delimiter line or closing paren is missing. body is
    (text, literal): $() drops trailing newlines, <<- drops leading tabs,
    and an unquoted delimiter's body is literal only with no $,
    backtick or backslash, since the shell would expand or join it."""
    delim, dash = match["delim"], bool(match["dash"])
    lines, offset = [], match.end()
    while True:
        newline = command.find("\n", offset)
        if newline < 0:
            return None
        line = command[offset:newline]
        if dash:
            line = line.lstrip("\t")
        offset = newline + 1
        if line == delim:
            break
        lines.append(line)
    close = HEREDOC_CLOSE.match(command, offset)
    if close is None:
        return None
    text = "\n".join(lines).rstrip("\n")
    literal = bool(match["quote"]) or not any(ch in text for ch in "$`\\")
    return (text, literal), close.end()


def _mask_heredocs(command):
    """(masked command, [heredoc bodies]): each heredoc substitution is
    cut from the raw string and replaced by a placeholder word before
    shlex sees it, because shlex does not know $( ) opens a new quoting
    context and would strip the body's inner quotes."""
    pieces, bodies, start = [], [], 0
    for match in HEREDOC_OPEN.finditer(command):
        if match.start() < start:
            continue
        found = _heredoc_at(command, match)
        if found is None:
            continue
        body, end = found
        pieces += [command[start:match.start()],
                   PLACEHOLDER.format(len(bodies))]
        bodies.append(body)
        start = end
    pieces.append(command[start:])
    return "".join(pieces), bodies


# Characters after which an unquoted `#` starts a comment: whitespace and
# the control and redirection operators, as in the shell's own grammar.
WORD_BREAK = " \t\n;&|()<>"


class _Unrun:
    """Cut the text the shell never runs out of a command: every heredoc
    body (with its delimiter line) and every comment, so neither is
    tokenized as a command. Quote-aware: `<<` and `#` inside quotes, a
    `#` mid-word and a `<<<` here-string are kept. Raises ValueError on a
    shape it cannot classify (an unclosed quote, substitution or
    backtick, or a heredoc delimiter it cannot read), which the caller
    turns into a note: the shell would reject the first kinds, and the
    last fails open."""

    def __init__(self, text):
        self.text, self.pos, self.out = text, 0, []
        self.pending, self.boundary = [], True

    def run(self):
        self._normal(nested=False)
        return "".join(self.out)

    def _take(self, end, boundary=False):
        self.out.append(self.text[self.pos:end])
        self.pos, self.boundary = end, boundary

    def _normal(self, nested):
        """Unquoted text, to the end or (nested) to the `)` closing a
        `$(`. The quoting and substitution openers hand off."""
        depth, text = 0, self.text
        while self.pos < len(text):
            ch = text[self.pos]
            if ch == ")" and nested and depth == 0:
                return self._take(self.pos + 1)
            if ch in "()" and nested:
                depth += 1 if ch == "(" else -1
            if not self._special(ch):
                self._take(self.pos + 1, boundary=ch in WORD_BREAK)
                if ch == "\n" and self.pending:
                    self._bodies()
        if nested:
            raise ValueError("an unclosed command substitution")

    def _special(self, ch):
        """Consume one construct starting at pos; False when ch is plain."""
        text, pos = self.text, self.pos
        if ch == "\\":  # a removed backslash-newline keeps the boundary
            joined = text[pos + 1:pos + 2] == "\n"
            self._take(pos + 2, self.boundary and joined)
        elif ch == "'" or text.startswith("$'", pos):
            self._quoted(pos + (2 if ch == "$" else 1), "'", ch == "$")
        elif ch == '"':
            self._double()
        elif ch == "`":
            self._quoted(pos + 1, "`", True)
        elif text.startswith("$((", pos):
            self._arithmetic(pos + 1)
        elif text.startswith("((", pos) and self.boundary:
            self._arithmetic(pos)
        elif text.startswith("${", pos) and re.search(
                r"\s#|<<", text[pos:text.find("}", pos)]):
            raise ValueError("a ${ } holding # or << the hook cannot read")
        elif text.startswith("$(", pos):
            self._take(pos + 2, boundary=True)
            self._normal(nested=True)
        elif ch == "#" and self.boundary:
            end = text.find("\n", pos)
            self.pos = len(text) if end < 0 else end
        elif text.startswith("<<<", pos):
            self._take(pos + 3, boundary=True)
        elif text.startswith("<<", pos):
            self._heredoc_operator()
        else:
            return False
        return True

    def _quoted(self, start, close, escapes):
        """A span to the next close (single quotes take no escapes)."""
        index = start
        while index < len(self.text) and self.text[index] != close:
            index += 2 if escapes and self.text[index] == "\\" else 1
        if index >= len(self.text):
            raise ValueError("No closing quotation")
        if close == "`" and "<<" in self.text[start:index]:
            raise ValueError("a heredoc inside backticks")
        self._take(index + 1)

    def _double(self):
        """A double-quoted span; a `$(` inside it is unquoted again."""
        self._take(self.pos + 1)
        text = self.text
        while self.pos < len(text):
            ch = text[self.pos]
            if ch == '"':
                return self._take(self.pos + 1)
            if ch == "\\":
                self._take(self.pos + 2)
            elif ch == "`":
                self._quoted(self.pos + 1, "`", True)
            elif text.startswith("$((", self.pos):
                self._arithmetic(self.pos + 1)
            elif text.startswith("$(", self.pos):
                self._take(self.pos + 2, boundary=True)
                self._normal(nested=True)
            else:
                self._take(self.pos + 1)
        raise ValueError("No closing quotation")

    def _arithmetic(self, start):
        """`$(( … ))` or a `(( … ))` command (start at its first paren),
        kept whole: its `<<` is a shift, not a heredoc."""
        depth, index = 0, start
        while index < len(self.text):
            depth += {"(": 1, ")": -1}.get(self.text[index], 0)
            index += 1
            if depth == 0:
                return self._take(index)
        raise ValueError("an unclosed command substitution")

    def _heredoc_operator(self):
        """`<<D`, `<<-D`, `<< 'D'`, `<<\\D`, `<<E'O'F`: keep the operator
        and its word, and queue the body for the end of the line."""
        text, index = self.text, self.pos + 2
        dash = text.startswith("-", index)
        index += dash
        while index < len(text) and text[index] in " \t":
            index += 1
        delim = []
        while index < len(text) and text[index] not in WORD_BREAK:
            ch = text[index]
            if ch in "$`":
                raise ValueError("a heredoc delimiter the hook cannot read")
            if ch in "'\"":
                close = text.find(ch, index + 1)
                if close < 0:
                    raise ValueError("No closing quotation")
                delim.append(text[index + 1:close])
                index = close + 1
            else:
                step = 2 if ch == "\\" else 1
                delim.append(text[index + step - 1:index + step])
                index += step
        if not "".join(delim):
            raise ValueError("a heredoc with no delimiter")
        self.pending.append(("".join(delim), dash))
        self._take(index)

    def _bodies(self):
        """Drop each queued heredoc's body and delimiter line. A body
        whose delimiter line never comes runs to the end, as in bash."""
        text = self.text
        for delim, dash in self.pending:
            while self.pos < len(text):
                end = text.find("\n", self.pos)
                end = len(text) if end < 0 else end
                line = text[self.pos:end]
                self.pos = min(end + 1, len(text))
                if (line.lstrip("\t") if dash else line) == delim:
                    break
        self.pending = []


def _tokens(command):
    """shlex configured per the architecture: a newline is an operator,
    and `#` is ordinary text. Raises ValueError on an unclosed quote."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=PUNCTUATION)
    lexer.whitespace_split = True
    lexer.whitespace = " \t"
    lexer.commenters = ""
    return list(lexer)


def _is_punctuation(token):
    return bool(token) and all(ch in PUNCTUATION for ch in token)


def _simple_commands(tokens):
    """Word lists between control operators. A redirection (a punctuation
    token starting with < or >) drops itself and its target word."""
    commands, words, skip = [], [], False
    for token in tokens:
        if skip:
            skip = False
        elif _is_punctuation(token) and token[0] in "<>":
            skip = True
        elif _is_punctuation(token):
            commands.append(words)
            words = []
        else:
            words.append(token)
    commands.append(words)
    return [words for words in commands if words]


def _create_args(words):
    """The args after `gh pr create`, or None when this simple command is
    not one. Leading NAME=value assignments are skipped; prefixes such as
    bash -c, env, xargs or command are not looked through."""
    index = 0
    while index < len(words) and ASSIGNMENT.match(words[index]):
        index += 1
    head = words[index:index + 3]
    if len(head) < 3 or head[1:] != ["pr", "create"]:
        return None
    if head[0] != "gh" and not head[0].endswith("/gh"):
        return None
    return words[index + 3:]


def _flag_value(args, index, long_flag, short_flag):
    """(value, next_index) when args[index] spells long_flag or
    short_flag with a value, else None. Raises _Unreadable when the flag
    has no value."""
    arg = args[index]
    if arg in (long_flag, short_flag):
        if index + 1 >= len(args):
            raise _Unreadable(f"{arg} has no value")
        return args[index + 1], index + 2
    if arg.startswith(long_flag + "="):
        return arg[len(long_flag) + 1:], index + 1
    if arg.startswith(short_flag) and len(arg) > 2:
        value = arg[2:]
        return (value[1:] if value.startswith("=") else value), index + 1
    return None


class _Unreadable(Exception):
    """A gh pr create whose body the hook cannot read; the message is
    the note's reason."""


def _deferring(arg):
    """The flag name when arg leaves the body to gh, else None."""
    name = arg.split("=", 1)[0] if arg.startswith("--") else arg
    return name if name in DEFERRING_FLAGS else None


def _hidden_in_cluster(arg):
    """True for a single-dash cluster holding b or F past second place
    (`-db`): a body flag the hook will not unpick. A value flag's joined
    value (`-Bfix/b`) is not a cluster."""
    return (len(arg) > 2 and arg[0] == "-" and arg[1] not in "-bF"
            and arg[:2] not in VALUE_FLAGS
            and ("b" in arg[2:] or "F" in arg[2:]))


def _body_sources(args):
    """([(kind, value)] for every body source among args, kind "body" or
    "file"; [every -R/--repo value]). Raises _Unreadable for a flag or
    cluster that hides the body."""
    sources, repos, index = [], [], 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            break
        if _deferring(arg):
            raise _Unreadable(f"{_deferring(arg)} leaves the body to gh")
        if _hidden_in_cluster(arg):
            raise _Unreadable(f"{arg} hides a body flag in a cluster")
        body = _flag_value(args, index, "--body", "-b")
        path = None if body else _flag_value(args, index, "--body-file", "-F")
        repo = (None if body or path
                else _flag_value(args, index, "--repo", "-R"))
        if body or path:
            sources.append(("body", body[0]) if body else ("file", path[0]))
            index = (body or path)[1]
        elif repo:
            repos.append(repo[0])
            index = repo[1]
        elif arg in VALUE_FLAGS:
            index += 2
        else:
            index += 1
    return sources, repos


def _read_body_file(path, context):
    """The text of one body file. Read only from the compound's first
    simple command: an earlier segment could write the file or change
    directory, so the file on disk is not known to be the body."""
    import cli  # lazy, like gates: only a candidate pays for it
    if path == "-":
        raise _Unreadable("--body-file - reads the body from stdin")
    if not context["first"]:
        raise _Unreadable("a body file is read only from the first command")
    target = Path(path)
    if not target.is_absolute():
        if not isinstance(context["cwd"], str):
            raise _Unreadable("a relative body file with no cwd in the payload")
        target = Path(context["cwd"]) / target
    text, problem = cli.read_file(target, path, str)
    if problem:
        raise _Unreadable(problem)
    if text is None:
        raise _Unreadable(f"no body file at {path}")
    return text


def _resolve(value, context):
    """The body a --body value stands for. A placeholder alone is its
    heredoc; `$(cat PATH)` / `$(< PATH)` is that file; any other $ or
    backtick is a shell expansion the hook cannot do."""
    placeholder = PLACEHOLDER_WORD.fullmatch(value)
    if placeholder:
        text, literal = context["heredocs"][int(placeholder[1])]
        if not literal:
            raise _Unreadable(
                "an unquoted heredoc body holds $, a backtick or a backslash")
        return text
    cat = CAT_FILE.fullmatch(value)
    if cat:
        return _read_body_file(cat["path"], context)
    if PLACEHOLDER_WORD.search(value) or any(ch in value for ch in "$`"):
        raise _Unreadable(
            "the body holds $ or a backtick the hook cannot expand")
    return value


def _body(args, context):
    """(body text, [-R/--repo values]) for one gh pr create. Raises
    _Unreadable."""
    sources, repos = _body_sources(args)
    if not sources:
        raise _Unreadable("no --body or --body-file")
    if len(sources) > 1:
        raise _Unreadable("more than one body source")
    kind, value = sources[0]
    if kind == "file":
        return _read_body_file(value, context), repos
    return _resolve(value, context), repos


def _git_config(start):
    """The resolved path of the git config that owns directory start, or
    None outside a checkout. A worktree's `.git` file is followed to its
    common directory, so every worktree of one clone shares one config."""
    import cli
    start = start.resolve()
    for directory in (start, *start.parents):
        dot = directory / ".git"
        if dot.is_dir():
            return (dot / "config").resolve()
        if not dot.is_file():
            continue
        text, _ = cli.read_file(dot, ".git", str)
        if not text or not text.startswith("gitdir:"):
            return None
        gitdir = directory / text[len("gitdir:"):].strip()
        common, _ = cli.read_file(gitdir / "commondir", "commondir", str)
        base = gitdir / common.strip() if common else gitdir
        return (base / "config").resolve()
    return None


def _slug(value):
    """`host/owner/name`, lowercased, for a gh `[HOST/]OWNER/REPO` value
    or a git remote URL (scp-like, https or ssh), else None."""
    text = re.sub(r"^[a-z][a-z0-9+.-]*://", "", value.strip().lower())
    text = re.sub(r"^[^@/]*@", "", text).replace(":", "/", 1)
    parts = text.removesuffix("/").removesuffix(".git").split("/")
    if len(parts) == 2:
        parts = ["github.com", *parts]
    return "/".join(parts) if len(parts) == 3 and all(parts) else None


def _remote_slugs(cwd):
    """The slugs of every remote URL in the cwd checkout's git config,
    read from the file (no git, no network), or None when unknown."""
    import cli
    if not isinstance(cwd, str):
        return None
    config = _git_config(Path(cwd))
    text = cli.read_file(config, "git config", str)[0] if config else None
    slugs, in_remote = set(), False
    for line in (text or "").splitlines():
        line = line.strip()
        if line.startswith("["):
            in_remote = line.startswith("[remote ")
        elif in_remote and REMOTE_URL.match(line):
            slugs.add(_slug(REMOTE_URL.match(line)["url"]))
    slugs.discard(None)
    return frozenset(slugs) or None


def _gh_repo(earlier, prefix, environ):
    """GH_REPO as gh will see it: the environment, then each earlier
    `GH_REPO=` word in the compound, then the command's own prefix; the
    last one wins and an empty value means unset."""
    value = environ.get("GH_REPO", "")
    for word in [word for words in earlier for word in words] + prefix:
        if word.startswith("GH_REPO="):
            value = word[len("GH_REPO="):]
    return [value] if value else []


def _working_directory(earlier, cwd):
    """The directory gh pr create runs in after the compound's earlier
    cd/pushd/popd, or None when one of them cannot be placed."""
    here = Path(cwd) if isinstance(cwd, str) else None
    for words in earlier:
        if words[0] not in DIRECTORY_CHANGERS:
            continue
        args = words[1:]
        if words[0] == "popd" or len(args) != 1 or here is None:
            return None
        if args[0].startswith(("-", "~")) or any(
                ch in args[0] for ch in "$`"):
            return None
        here = here / args[0]
        if not here.is_dir():
            return None
    return here


def _check_target(repos, context):
    """Raise _Unreadable unless this gh pr create opens a PR on this
    repository: B is this repository's rule (review finding 3). Named
    repositories (-R/--repo, GH_REPO) are compared with the cwd
    checkout's remotes; a cd must stay inside the cwd's checkout."""
    earlier = context["commands"][:context["position"]]
    named = repos + _gh_repo(earlier, context["prefix"], context["environ"])
    if named:
        slugs = _remote_slugs(context["cwd"])
        for value in named:
            if slugs is None:
                raise _Unreadable(f"the PR targets {value} and this "
                                  "repository's remote cannot be read")
            if _slug(value) not in slugs:
                raise _Unreadable(
                    f"the PR targets {value}, not this repository")
    if not any(words[0] in DIRECTORY_CHANGERS for words in earlier):
        return
    here = _working_directory(earlier, context["cwd"])
    home = _git_config(Path(context["cwd"])) if here else None
    if home is None:
        raise _Unreadable("a cd before gh pr create the hook cannot place")
    if _git_config(here) != home:
        raise _Unreadable("a cd before gh pr create leaves this repository")


def _verdicts(command, cwd, environ):
    """(failed, notes-and-problems lines) over every gh pr create."""
    masked, heredocs = _mask_heredocs(command)
    try:
        tokens = _tokens(_Unrun(masked).run())
    except ValueError as exc:
        return False, [NOTE.format(f"cannot parse the command: {exc}")]
    commands = _simple_commands(tokens)
    candidates = [(position, args) for position, args in
                  enumerate(map(_create_args, commands)) if args is not None]
    if not candidates:
        return False, [NOTE.format(NOT_SEEN)]
    import gates  # lazy: ~60 ms, paid only by a candidate command
    failed, lines = False, []
    for position, args in candidates:
        words = commands[position]
        context = {"first": position == 0, "cwd": cwd, "heredocs": heredocs,
                   "commands": commands, "position": position,
                   "prefix": words[:len(words) - len(args) - 3],
                   "environ": environ}
        try:
            body, repos = _body(args, context)
            _check_target(repos, context)
        except _Unreadable as exc:
            lines.append(NOTE.format(exc))
            continue
        problems = gates.pr_body_problems(body)
        failed = failed or bool(problems)
        lines.extend(problems)
    return failed, lines


def preflight(payload_text, environ=None):
    """(exit_code, stderr_lines) for one PreToolUse payload. Pure: writes
    nothing, reads only body files and the cwd checkout's git config.
    environ is the environment gh would inherit (only GH_REPO is read;
    None is empty). Exit 2 only on a judged failing body; any exception
    is exit 0 with a note."""
    try:
        data = json.loads(payload_text)
    except ValueError:
        return 0, []
    tool_input = data.get("tool_input") if isinstance(data, dict) else None
    command = (tool_input.get("command")
               if isinstance(tool_input, dict) else None)
    if not isinstance(command, str):
        return 0, []
    if not all(part in command for part in ("gh", "pr", "create")):
        return 0, []
    try:
        failed, lines = _verdicts(command, data.get("cwd"), environ or {})
    except Exception as exc:  # fail open: a crash must never block Bash
        return 0, [NOTE.format(f"{type(exc).__name__}: {exc}")]
    return (2, lines + [POINTER]) if failed else (0, lines)


def main(argv, stdin=None):
    """The hook adapter. An argument (only a human passes one) prints this
    usage and exits 0, since exit 2 would mean "block" to a hook."""
    if argv:
        sys.stderr.write(__doc__.strip() + "\n")
        return 0
    try:
        text = (sys.stdin if stdin is None else stdin).read()
    except Exception as exc:  # fail open on an unreadable stdin
        print(NOTE.format(f"{type(exc).__name__}: {exc}"), file=sys.stderr)
        return 0
    code, lines = preflight(text, os.environ)
    for line in lines:
        print(line, file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
