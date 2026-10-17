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


def _body_sources(args):
    """[(kind, value)] for every body source among args, kind "body"."""
    sources, index = [], 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            break
        found = _flag_value(args, index, "--body", "-b")
        if found is not None:
            sources.append(("body", found[0]))
            index = found[1]
        elif arg in VALUE_FLAGS:
            index += 2
        else:
            index += 1
    return sources


def _body(args):
    """The body text for one gh pr create. Raises _Unreadable."""
    sources = _body_sources(args)
    if not sources:
        raise _Unreadable("no --body or --body-file")
    if len(sources) > 1:
        raise _Unreadable("more than one body source")
    return sources[0][1]


def _verdicts(command):
    """(problems, notes-and-problems lines) over every gh pr create."""
    try:
        tokens = _tokens(command)
    except ValueError as exc:
        return False, [NOTE.format(f"cannot parse the command: {exc}")]
    candidates = [args for args in map(_create_args,
                                       _simple_commands(tokens))
                  if args is not None]
    if not candidates:
        return False, [NOTE.format(NOT_SEEN)]
    import gates  # lazy: ~60 ms, paid only by a candidate command
    failed, lines = False, []
    for args in candidates:
        try:
            body = _body(args)
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
        failed, lines = _verdicts(command)
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
