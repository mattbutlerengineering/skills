"""The one fake git at the conductor's git port.

The conductor's git port is cli.runner("git"): `git(args)` returns a
subprocess.CompletedProcess and raises cli.CLI_FAILURES. Ten private
fakes stood in for it across the conductor suites, each restating git's
exit codes, and they disagreed with real git (#781): the one behind
every RunCase launch answered `config --get-regexp` with exit 0, so the
branch real git takes (exit 1, no match) was never exercised. This is
FakeGh's shape (tests/fake_gh.py) at the git port, and
tests/test_fake_git.py checks that no conductor suite keeps another.

A suite declares WHAT git prints — canned stdout keyed by argv prefix,
a str or a callable(args) -> str (which may also make what the command
makes, such as a `worktree add` directory). The longest matching
prefix wins. How git fails is stated here, once:

- An unanswered (or empty) command succeeded and printed nothing — what
  push, commit, add, diff, log, worktree add and ls-tree of an absent
  path do. Never an AssertionError outside cli.CLI_FAILURES.
- Except the reads whose "nothing" real git reports as a failure:
  `config --get*` and `grep` exit 1 with no stderr; `show <rev>:<path>`
  and `rev-parse <rev>` exit 128 with git's fatal line.
- Record, then compute, then raise, as FakeGh does: every call lands in
  `calls` first, then its answer is computed, then a `failing` prefix
  raises `error` (default: a failed git, exit 128, "fatal: rejected").
- Every error names `git`, never `gh`.
"""
import subprocess

CONFIG_READS = ("--get", "--get-all", "--get-regexp")


def default_error():
    """What cli.runner("git") raises for a git that ran and failed."""
    return subprocess.CalledProcessError(128, "git",
                                         stderr="fatal: rejected\n")


def nothing_found(args):
    """The error real git exits with when this read finds nothing, or
    None when printing nothing is a success."""
    rest = list(args)
    while rest[:1] in (["-C"], ["-c"]):
        rest = rest[2:]
    command, last = (rest[:1] or [""])[0], (rest[-1:] or [""])[0]
    if (command == "config" and any(a in CONFIG_READS for a in rest)) \
            or command == "grep":
        return subprocess.CalledProcessError(1, "git", stderr="")
    if command == "show" and ":" in last:
        rev, path = last.split(":", 1)
        return subprocess.CalledProcessError(
            128, "git",
            stderr=f"fatal: path '{path}' does not exist in '{rev}'\n")
    if command == "rev-parse":
        return subprocess.CalledProcessError(
            128, "git",
            stderr=f"fatal: ambiguous argument '{last}': unknown revision"
                   " or path not in the working tree.\n"
                   "Use '--' to separate paths from revisions, like"
                   " this:\n'git <command> [<revision>...] -- [<file>...]'"
                   "\n")
    return None


class FakeGit:
    """Injected git port: records every call, answers by argv prefix,
    fails as real git fails, and raises `error` on the `failing`
    prefix."""

    def __init__(self, answers=None, failing=None, error=None):
        self.answers = dict(answers or {})
        self.failing = None if failing is None else list(failing)
        self.error = error if error is not None else default_error()
        self.calls = []

    def __call__(self, args):
        self.calls.append(list(args))
        answer = self.answer(list(args))
        if (self.failing is not None
                and list(args[:len(self.failing)]) == self.failing):
            raise self.error
        if not answer:
            failure = nothing_found(args)
            if failure is not None:
                raise failure
        return subprocess.CompletedProcess(["git", *args], 0, stdout=answer,
                                           stderr="")

    def answer(self, args):
        """The canned stdout for one argv: longest matching prefix wins,
        an unmatched argv answers ""."""
        best_prefix, best_value = None, ""
        for prefix, value in self.answers.items():
            head = list(prefix)
            if args[:len(head)] != head:
                continue
            if best_prefix is None or len(head) > len(best_prefix):
                best_prefix, best_value = head, value
        return best_value(args) if callable(best_value) else best_value

    def called(self, *prefix):
        """Every recorded call starting with `prefix`."""
        return [c for c in self.calls if c[:len(prefix)] == list(prefix)]
