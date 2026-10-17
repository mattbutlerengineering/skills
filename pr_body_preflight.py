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

It fails open: an unreadable body, an unparsable command or any exception
is exit 0, and CI's B still judges that PR. Root-only (not mirrored).

  python3 pr_body_preflight.py < payload.json
"""
import json
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
    """[(kind, value)] for every body source among args, kind "body" or
    "file". Raises _Unreadable for a flag or cluster that hides it."""
    sources, index = [], 0
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
        if body or path:
            sources.append(("body", body[0]) if body else ("file", path[0]))
            index = (body or path)[1]
        elif arg in VALUE_FLAGS:
            index += 2
        else:
            index += 1
    return sources


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
    """The body text for one gh pr create. Raises _Unreadable."""
    sources = _body_sources(args)
    if not sources:
        raise _Unreadable("no --body or --body-file")
    if len(sources) > 1:
        raise _Unreadable("more than one body source")
    kind, value = sources[0]
    if kind == "file":
        return _read_body_file(value, context)
    return _resolve(value, context)


def _verdicts(command, cwd):
    """(failed, notes-and-problems lines) over every gh pr create."""
    masked, heredocs = _mask_heredocs(command)
    try:
        tokens = _tokens(masked)
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
        context = {"first": position == 0, "cwd": cwd, "heredocs": heredocs}
        try:
            body = _body(args, context)
        except _Unreadable as exc:
            lines.append(NOTE.format(exc))
            continue
        problems = gates.pr_body_problems(body)
        failed = failed or bool(problems)
        lines.extend(problems)
    return failed, lines


def preflight(payload_text):
    """(exit_code, stderr_lines) for one PreToolUse payload. Pure: writes
    nothing, reads only body files. Exit 2 only on a judged failing body;
    any exception is exit 0 with a note."""
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
        failed, lines = _verdicts(command, data.get("cwd"))
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
    code, lines = preflight(text)
    for line in lines:
        print(line, file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
