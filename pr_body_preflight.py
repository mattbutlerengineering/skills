#!/usr/bin/env python3
"""pr-body-preflight: refuse a `gh pr create` whose body would fail detector B.

A Claude Code PreToolUse hook on Bash, registered in this repo's checked-in
.claude/settings.json and run by filename with the hook payload (JSON) on
stdin. Detector B (gates.check_pr_traceability) reads the PR body from the
CI event, so locally it skips and only fails once the PR is open
(docs/kb/pr-body-contract.md). This applies the same rule, through B's one
owner gates.pr_body_problems, before the PR exists.

A `--body-file F` is read from disk when `gh pr create` is the compound's
first command. A same-call heredoc is also a readable shape: a not-first
reader whose file an earlier `cat > F <<D` writes is judged on that
heredoc's text, with no disk read, when the writer surely ran (its
execution is implied by the reader's), F is spelled identically in both,
and no command between them may have changed F (a write redirect, a
process substitution, a hostile joiner or any command off the inert
list) and nothing before the writer opens a descriptor onto F or
redefines the commands that run. Any binding the hook cannot establish is
a "not checked" note.

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
import collections
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
# A file-descriptor prefix (`2` in `2>&1`): a digit word touching its
# redirect operator in the unquoted source, which the tokenizer cannot tell
# from a command word once a space separates the two. _Unrun marks it.
FD_PREFIX = "__pr_body_preflight_fd_{}__"
FD_WORD = re.compile(r"__pr_body_preflight_fd_(\d+)__")
# A `{NAME}` word that touches its redirect operator (`{fd}> out`), the one
# spelling that opens a named descriptor; a `{NAME}` elsewhere is a plain word.
FD_NAME_PREFIX = "__pr_body_preflight_fdname_{}__"
FD_NAME_WORD = re.compile(r"__pr_body_preflight_fdname_([A-Za-z0-9_]+)__")
FD_NAME_SOURCE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}(?=[<>])")
DIGITS = "0123456789"
# One statement-level heredoc: the bytes a shell writes, whether the shell
# would expand nothing in them, and whether the delimiter line closed it.
Heredoc = collections.namedtuple("Heredoc", "text literal terminated")
# One simple command: its words, its redirections as (operator, target) in
# written order, and the punctuation that joined it to the previous one.
Simple = collections.namedtuple("Simple", "words redirects joiner")
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
    """(masked command, [heredoc bodies], [(placeholder, original span)]):
    each heredoc substitution is cut from the raw string and replaced by a
    placeholder word before shlex sees it, because shlex does not know
    $( ) opens a new quoting context and would strip the body's inner
    quotes. The pairs let _Unrun restore a span that sits inside a
    statement-level heredoc body."""
    pieces, bodies, originals, start = [], [], [], 0
    for match in HEREDOC_OPEN.finditer(command):
        if match.start() < start:
            continue
        found = _heredoc_at(command, match)
        if found is None:
            continue
        body, end = found
        placeholder = PLACEHOLDER.format(len(bodies))
        pieces += [command[start:match.start()], placeholder]
        bodies.append(body)
        originals.append((placeholder, command[match.start():end]))
        start = end
    pieces.append(command[start:])
    return "".join(pieces), bodies, originals


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
    last fails open. Each statement-level heredoc is recorded in
    `heredocs` (a Heredoc, in queue order) and its operator and delimiter
    are rewritten to `<<` plus a numbered placeholder word; originals are
    the (placeholder, span) pairs _mask_heredocs cut, restored in a body
    before `literal` is decided. A digit word that touches its `<` or `>`
    (a descriptor prefix) is replaced by a marker word, and `ansi_c` is
    set when an unquoted `$'...'` string was cut."""

    def __init__(self, text, originals=()):
        self.text, self.pos, self.out = text, 0, []
        self.pending, self.boundary, self.braces = [], True, 0
        self.originals, self.heredocs = originals, []
        self.ansi_c = False  # an unquoted `$'...'` string was cut

    def run(self):
        self._normal(nested=False)
        if self.pending:  # a heredoc operator on the last line: no body
            self._bodies()
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
            if self._fd_prefix(ch):
                continue
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

    def _fd_prefix(self, ch):
        """True after replacing a digit word that touches a `<` or `>` (at
        a word boundary, outside `${ }`) with its marker word."""
        text, end = self.text, self.pos
        named = FD_NAME_SOURCE.match(text, end) if (
            ch == "{" and self.boundary and not self.braces) else None
        if named:
            self.out.append(FD_NAME_PREFIX.format(named[1]))
            self.pos, self.boundary = named.end(), False
            return True
        if not (self.boundary and not self.braces and ch in DIGITS
                and not "".join(self.out[-2:]).endswith((">&", "<&"))):
            return False
        while end < len(text) and text[end] in DIGITS:
            end += 1
        if end >= len(text) or text[end] not in "<>":
            return False
        self.out.append(FD_PREFIX.format(text[self.pos:end]))
        self.pos, self.boundary = end, False
        return True

    def _special(self, ch):
        """Consume one construct starting at pos; False when ch is plain."""
        text, pos = self.text, self.pos
        if text.startswith("\\\n", pos):  # the shell removes it
            self.pos += 2
        elif ch == "\\":
            self._take(pos + 2)
        elif ch == "'" or text.startswith("$'", pos):
            self.ansi_c = self.ansi_c or ch == "$"
            self._quoted(pos + (2 if ch == "$" else 1), "'", ch == "$")
        elif ch == '"':
            self._double()
        elif ch == "`":
            self._quoted(pos + 1, "`", True)
        elif text.startswith("$((", pos):
            self._arithmetic(pos + 1)
        elif text.startswith("((", pos) and self.boundary:
            self._arithmetic(pos)
        elif text.startswith("${", pos) or (ch == "}" and self.braces):
            self.braces += 1 if ch == "$" else -1
            self._take(pos + (2 if ch == "$" else 1))
        elif text.startswith("$(", pos):
            self._take(pos + 2, boundary=True)
            self._normal(nested=True)
        elif self.braces and (text.startswith("<<", pos)
                              or (ch == "#" and self.boundary)):
            raise ValueError("a ${ } holding # or << the hook cannot read")
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
            if text.startswith("\\\n", self.pos):  # removed, as unquoted
                self.pos += 2
            elif ch == "\\":
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
        delim, quoted = [], False
        while index < len(text) and text[index] not in WORD_BREAK:
            ch = text[index]
            if ch in "$`":
                raise ValueError("a heredoc delimiter the hook cannot read")
            quoted = quoted or ch in "'\"\\"
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
        self.out.append(
            "<<" + PLACEHOLDER.format(len(self.heredocs)))
        self.pos, self.boundary = index, False
        self.pending.append(
            (len(self.heredocs), "".join(delim), dash, quoted))
        self.heredocs.append(None)

    def _bodies(self):
        """Capture each queued heredoc's body and delimiter line, and cut
        them from the output. A body whose delimiter line never comes runs
        to the end, as in bash."""
        text = self.text
        for number, delim, dash, quoted in self.pending:
            lines, terminated = [], False
            while self.pos < len(text):
                end = text.find("\n", self.pos)
                end = len(text) if end < 0 else end
                line = text[self.pos:end]
                self.pos = min(end + 1, len(text))
                if dash:
                    line = line.lstrip("\t")
                if line == delim:
                    terminated = True
                    break
                lines.append(line)
            body = "".join(line + "\n" for line in lines)
            for placeholder, original in self.originals:
                body = body.replace(placeholder, original)
            literal = quoted or not any(ch in body for ch in "$`\\")
            # a restored span with a line of its own equal to this
            # delimiter ends the heredoc early in the shell
            terminated = terminated and not any(
                (line.lstrip("\t") if dash else line) == delim
                for line in body.split("\n"))
            self.heredocs[number] = Heredoc(body, literal, terminated)
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
    """One Simple per command between control operators, including a
    redirect-only command. A redirection is a punctuation run holding `<`
    or `>`, split off from any separator before it (a lone `&` directly
    before `>` stays in the operator: `&>`, `&>>`) and paired with the
    word that follows (a `<(` or `>(` is kind `procsub` and takes none);
    the joiner is every separator run since the previous record. A digit
    word _Unrun marked as touching its operator is that redirect's
    descriptor prefix and is written into the operator (`2>&`), not left
    as a word."""
    records, joiner = [], ""
    words, redirects, operator = [], [], None
    for token in tokens:
        if operator:
            redirects.append((operator, token))
            operator = None
        elif _is_punctuation(token):
            cut = next((i for i, ch in enumerate(token) if ch in "<>"), None)
            head = token if cut is None else token[:cut]
            if cut is not None and head.endswith("&") and token[cut] == ">" \
                    and not head.endswith("&&"):
                head, cut = head[:-1], cut - 1
            if head:
                if words or redirects:
                    records.append(Simple(words, redirects, joiner))
                    words, redirects, joiner = [], [], ""
                joiner += head
            if cut is not None:
                fd = FD_WORD.fullmatch(words[-1]) if words and not head else None
                if fd:  # `2>&1`: the digits belong to the operator
                    words.pop()
                if token[cut:] in ("<(", ">("):  # opens a command, no target
                    redirects.append(("procsub", token[cut:]))
                else:
                    operator = (fd[1] if fd else "") + token[cut:]
        else:
            words.append(token)
    if words or redirects:
        records.append(Simple(words, redirects, joiner))
    return records


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


def _writer_of(record, spelling):
    """The statement heredoc's index when record is exactly
    `cat > SPELLING <<D` (the two redirects in either order), else None."""
    if record.words != ["cat"] or len(record.redirects) != 2:
        return None
    by_operator = dict(record.redirects)
    if len(by_operator) != 2 or by_operator.get(">") != spelling:
        return None
    placeholder = PLACEHOLDER_WORD.fullmatch(by_operator.get("<<", ""))
    return int(placeholder[1]) if placeholder else None


# Names a shell changes without an assignment, so two spellings of one are
# not one file.
SHELL_MAINTAINED = frozenset({
    "RANDOM", "SRANDOM", "SECONDS", "EPOCHSECONDS", "EPOCHREALTIME", "LINENO",
    "BASHPID", "PIPESTATUS", "HISTCMD", "DIRSTACK", "status", "pipestatus",
    "PWD", "OLDPWD", "_"})
NAME_FORM = re.compile(
    r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")
# An argument that runs a command or assigns: a substitution (the tokenizer
# splits `$(` after its `$`), a backtick, `$[`, or `${NAME=` / `${NAME:=`.
UNSAFE_ARGUMENT = re.compile(r"`|\$\(|\$\[|\$$|\$\{[^}]*=")
# A joiner the chain rule reads: one `;`, `&&` or newline, then newlines.
# Anything else (`||`, `|`, `&`, a paren, `;;`, `&& ;`) is hostile.
SEQUENTIAL = re.compile(r"(?:;|&&|\n)\n*")
START_OR_SEMICOLON = re.compile(r"(?:[;\n]\n*)?")
ONLY_AND = re.compile(r"&&\n*")
SHELL_KEYWORDS = frozenset({
    "if", "then", "else", "elif", "fi", "for", "while", "until", "do",
    "done", "case", "esac", "function", "{", "}", "!"})


def _surely_ran(records, index, at):
    """True when the writer at records[index] runs whenever the reader at
    records[at] does: the writer's own joiner is the start, `;` or a
    newline, or every joiner from the writer through the reader is a run
    whose only operator is && (newlines allowed); in both cases no joiner
    after the writer is hostile and no record starts a shell construct."""
    after = records[index + 1:at + 1]
    if any(not SEQUENTIAL.fullmatch(record.joiner)
           or (record.words and record.words[0] in SHELL_KEYWORDS)
           for record in after):
        return False
    if START_OR_SEMICOLON.fullmatch(records[index].joiner):
        return True
    return all(ONLY_AND.fullmatch(record.joiner)
               for record in [records[index]] + after)


def _names(spelling):
    """The variable names a spelling expands."""
    return [m[1] or m[2] for m in NAME_FORM.finditer(spelling)]


def _comparable(spelling):
    """True when SPELLING names a file the hook can compare by identity:
    no backtick, `$(`, glob, brace outside `${NAME}` or leading `~`, and
    every `$` begins `$NAME` or `${NAME}` of a name the shell leaves to
    assignments."""
    names = _names(spelling)
    return not (spelling.startswith("~")
                or re.search(r"[`$*?\[\]{}]", NAME_FORM.sub("", spelling))
                or any(name in SHELL_MAINTAINED or name.startswith("BASH")
                       for name in names))


def _runs(word):
    """True when WORD may run a command or assign: an unsafe argument, or
    a placeholder for a masked `$(cat <<'D' ...)` substitution."""
    return bool(UNSAFE_ARGUMENT.search(word) or PLACEHOLDER_WORD.search(word))


def _directory_change(record):
    """True when record is a bare cd, pushd or popd whose arguments run
    nothing and assign nothing."""
    return bool(record.words and record.words[0] in DIRECTORY_CHANGERS
                and not record.redirects
                and not any(_runs(word) for word in record.words))


# Commands that leave every file alone when their arguments do not run
# anything: builtins, then read-only verbs (architecture.md's inert list).
INERT_VERBS = frozenset({
    "echo", "printf", "true", ":", "sleep",
    "cat", "grep", "egrep", "fgrep", "head", "tail", "wc", "ls", "test", "[",
    "diff", "cmp", "stat"})
# Names whose value steers a later command (git, gh, a pager, the search
# path, word splitting, a startup file, the loader): an assignment or export
# of one before the writer is a note when a command sits between writer and reader.
STEERING_NAME = re.compile(
    r"GIT_.*|GH_.*|.*PAGER|PATH|IFS|BASH_ENV|ENV|LD_.*|DYLD_.*|HOME|XDG_.*"
    r"|BROWSER")
# Redirections that only read, so they never unbind.
READ_OPERATORS = frozenset({"<", "<<", "<<<", "<&"})
BLOCK_CLOSERS = ("}", "done", "fi", "esac")
_REWRITTEN = ("{} may be rewritten or removed by {} between the heredoc and "
              "gh pr create")


def _verb(record):
    """The command word of record, or None for a redirect-only command."""
    return record.words[0] if record.words else None


# Words that open a command without being it.
LEADERS = SHELL_KEYWORDS | {"time", "command", "builtin"}
NULL_TARGETS = ("/dev/null", "/dev/stderr")
# Names that can change the writer `cat` itself, so they unbind wherever
# they are set; every other steering name matters only to a command that
# runs between writer and reader.
WRITER_STEERING = re.compile(r"PATH|LD_.*|DYLD_.*|BASH_ENV|ENV")
# Signals whose trap cannot run a command mid-script before the writer.
TRAP_SAFE = frozenset({"EXIT", "0", "INT", "TERM", "HUP"})
_BEFORE = "{} may be rewritten or removed by {} before the heredoc"


def _unmark(text):
    """text with a descriptor-prefix marker word written back as it was
    written and a heredoc placeholder rendered as `a heredoc`."""
    text = FD_NAME_WORD.sub(r"{\1}", FD_WORD.sub(r"\1", text))
    return PLACEHOLDER_WORD.sub("a heredoc", text)


def _opens_descriptor(record):
    """True when record, before the writer, keeps a descriptor open onto
    a file for the rest of the shell: an `exec`, or a `{NAME}` word, that
    carries a write redirect."""
    return ("exec" in record.words
            or any(FD_NAME_WORD.fullmatch(word) for word in record.words)
            ) and bool(_write_redirect(record))


def _shadows(record, between):
    """What in record, a command before the writer, may change how a later
    command behaves, else None: a function definition (`name()` leaves `()`
    in the joiner of the record after it, or the `function` keyword as the
    command word), an alias, a trap, or a standalone
    assignment or `export` of a name that can change the writer itself
    (WRITER_STEERING) or, when a command sits between writer and reader
    (`between`), of any steering name. Leading `NAME=value` assignments
    are stripped when a command follows. A trap is admitted only as a
    reset (`trap - SIG`), a print or list (`trap -p`, `trap -l`) or an
    action whose every signal is EXIT, 0, INT, TERM or HUP (TRAP_SAFE),
    each print/list signal held to the same set; DEBUG, ERR, RETURN and
    every other signal stay notes. `eval`, `source`, `declare -x`,
    `export NAME other`, `for NAME in` and `NAME+=` are accepted limits."""
    if "()" in record.joiner:
        return "a function definition"
    words = list(record.words)
    while words and words[0] in LEADERS:
        if words.pop(0) == "function":
            return "a function definition"
    lead = 0
    while lead < len(words) and ASSIGNMENT.match(words[lead]):
        lead += 1
    if lead < len(words):  # a command follows: its assignments are its own
        words = words[lead:]
        while words and words[0] in LEADERS:
            if words.pop(0) == "function":
                return "a function definition"
    if not words:
        return None
    if words[0] == "alias":
        return "alias"
    if words[0] == "trap":
        args = words[1:]
        if args[:1] in (["-p"], ["-l"]):  # print or list: safe signals only
            return None if all(s in TRAP_SAFE for s in args[1:]) else "trap"
        if args[:1] == ["--"]:  # after `--`, `-p` and `-l` are the action
            args = args[1:]
        if args[:1] == ["-"]:  # reset
            return None
        if len(args) < 2 or any(s not in TRAP_SAFE for s in args[1:]):
            return "trap"
        return None
    exported = words[0] == "export"
    assignments = words[1:] if exported else words
    if assignments and all(ASSIGNMENT.match(w) for w in assignments):
        for word in assignments:
            name = word.split("=", 1)[0]
            if WRITER_STEERING.fullmatch(name) or (
                    between and STEERING_NAME.fullmatch(name)):
                return "export" if exported else name + "="
    return None


def _running_redirect(record, statements):
    """The text of the first redirection of record whose target can run a
    command: a word holding a substitution, a masked substitution's
    placeholder, or a statement heredoc that is not literal (an unquoted
    body expands) or never closes."""
    for operator, target in record.redirects:
        if operator == "procsub":
            continue
        found = PLACEHOLDER_WORD.fullmatch(target)
        if operator == "<<" and found:
            number = int(found[1])
            if (number >= len(statements) or not statements[number].literal
                    or not statements[number].terminated):
                return "<< an unquoted heredoc"
        elif _runs(target):
            return _unmark(f"{operator} {target}")
    return None


def _write_redirect(record):
    """The text of the first redirection of record that may write a file,
    else None: any operator but the read ones, and a `<(` or `>(`, unless
    its target is /dev/null or /dev/stderr or, for `>&`, a descriptor
    number or `-` (a duplication or a close). Never compares F."""
    for operator, target in record.redirects:
        if operator == "procsub":
            return target
        bare = operator.lstrip(DIGITS)
        if bare == operator:
            if operator in READ_OPERATORS or target in NULL_TARGETS:
                continue
        elif bare in ("<", "<&") or (bare in (">", ">>", ">|")
                                      and target in NULL_TARGETS):
            continue  # a prefixed read, or a prefixed write to /dev/null
        if bare == ">&" and (target.isdigit() or target == "-"):
            continue  # a duplication or a close, with or without a prefix
        return _unmark(f"{operator} {target}")
    return None


def _removed_by(record):
    """What a note names: the name of an assignment (its value may be
    long), `git` or `gh` with the word that picks the command, else the
    verb."""
    verb, words = _verb(record), record.words
    if ASSIGNMENT.match(verb):
        return verb.split("=", 1)[0] + "="
    if verb == "git":
        return " ".join(words[:2])
    if verb == "gh":
        two = len(words) < 3 or words[1] == "api" or words[1].startswith("-")
        return " ".join(words[:2 if two else 3])
    return _unmark(verb)


def _inert(record):
    """True when record, a command between writer and reader, leaves the
    body file alone: a bare cd, or an inert verb with no argument that
    runs or assigns and, for printf, no `-v`. Write redirects are judged
    before this."""
    words = record.words
    if _directory_change(record):
        return True
    if any(_runs(word) for word in words):
        return False
    if words[0] == "printf" and any(w.startswith("-v") for w in words[1:]):
        return False
    return words[0] in INERT_VERBS


def _bound_body(spelling, context):
    """The text `cat > SPELLING <<D` leaves at SPELLING when it surely ran
    before this gh pr create. Raises _Unreadable: today's note when no such
    writer wrote that spelling, else the reason the heredoc cannot be
    trusted."""
    not_first = _Unreadable("a body file is read only from the first command")
    records, at = context["records"], context["record"]
    if not _comparable(spelling):
        if spelling.endswith("$"):  # the tokenizer cut `$(` after its `$`
            raise _Unreadable("a command substitution names the body file, "
                              "which the hook cannot compare")
        raise _Unreadable(f"{spelling} names a file through an expansion "
                          "the hook cannot compare")
    for index in range(at - 1, -1, -1):
        number = _writer_of(records[index], spelling)
        if number is not None:
            break
    else:
        raise not_first
    heredoc = context["statements"][number]
    if not heredoc.terminated:
        raise _Unreadable(
            f"the heredoc that writes {spelling} has no closing delimiter")
    if not heredoc.literal:
        raise _Unreadable(
            "an unquoted heredoc body holds $, a backtick or a backslash")
    if not _surely_ran(records, index, at):
        raise _Unreadable(f"the heredoc that writes {spelling} is not "
                          "certain to run before gh pr create")
    if context["ansi_c"] and index + 1 < at:  # `$'\\''` hides what follows
        raise _Unreadable(_REWRITTEN.format(spelling, "$'...'"))
    anything_between = index + 1 < at
    for earlier in records[:index]:
        if _opens_descriptor(earlier):
            raise _Unreadable(_BEFORE.format(spelling, "an open descriptor"))
        shadow = _shadows(earlier, anything_between)
        if shadow:
            raise _Unreadable(_BEFORE.format(spelling, shadow))
    for between in records[index + 1:at + 1]:
        redirect = (_write_redirect(between)
                    or _running_redirect(between, context["statements"]))
        if redirect:
            raise _Unreadable(_REWRITTEN.format(spelling, redirect))
    for later in records[at + 1:]:
        if (later.words and later.words[0] in BLOCK_CLOSERS
                or ")" in later.joiner):
            redirect = _write_redirect(later)
            if redirect:
                raise _Unreadable(_REWRITTEN.format(spelling, redirect))
    for between in records[index + 1:at]:
        verb = _verb(between)
        if verb and not _inert(between):
            raise _Unreadable(_REWRITTEN.format(spelling, _removed_by(between)))
        if verb in DIRECTORY_CHANGERS and not spelling.startswith("/"):
            raise _Unreadable("a cd between the heredoc and gh pr create "
                              f"may change what {spelling} names")
    return heredoc.text


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
    if any(kind == "procsub" for kind, _ in
           context["records"][context["record"]].redirects):
        raise _Unreadable(
            "a process substitution in gh pr create hides the body file")
    sources, repos = _body_sources(args)
    if not sources:
        raise _Unreadable("no --body or --body-file")
    if len(sources) > 1:
        raise _Unreadable("more than one body source")
    kind, value = sources[0]
    if kind == "file":
        if value != "-" and not context["first"]:
            return _bound_body(value, context), repos
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
    masked, heredocs, originals = _mask_heredocs(command)
    unrun = _Unrun(masked, originals)
    try:
        source = unrun.run()
        tokens = _tokens(source)
    except ValueError as exc:
        return False, [NOTE.format(f"cannot parse the command: {exc}")]
    records = _simple_commands(tokens)
    commands = [record.words for record in records if record.words]
    with_words = [at for at, record in enumerate(records) if record.words]
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
                   "records": records, "record": with_words[position],
                   "statements": unrun.heredocs, "ansi_c": unrun.ansi_c,
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
