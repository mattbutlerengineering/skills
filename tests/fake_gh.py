"""The one fake gh at cli.gh_runner's seam.

cli.gh_runner promises "tests inject a fake runner so they never touch
the network"; this is that fake, and every suite at the seam injects it.
A suite declares WHAT gh says — canned stdout keyed by argv prefix —
never HOW a fake behaves.

Which suites those are is not written down here. It was, as a list of
four, and it was wrong twice over — seven suites imported it, and
test_work_queue kept two private runners the settlement below never
reached, one of them recording and raising without computing. The list
is derived instead, by tests/test_fake_gh.py, which reads every module
under tests/ for a `__call__(self, args)` and fails when there is more
than one.

Four suites' private fakes had diverged on three behaviors; these are
the declared choices:

- Record, then compute, then raise. Every call lands in `calls` first,
  its canned answer is computed, and only then does a failing prefix
  raise — a failed call is visible with exactly the shape a successful
  one would have, which preserves the most information for assertions.
  (validator/gate_digest ordered it this way; sweeps recorded before
  delegating, label_sync re-implemented its parent's body.)
- One default error: subprocess.CalledProcessError(1, "gh",
  stderr="boom\\n") — the shape a real failed gh has, exercising
  cli.detail's stderr path. A suite exercising a different cli.detail
  path (OSError for a missing binary, a CalledProcessError with no
  stderr) passes `error=` explicitly — the divergence is now a choice
  each test states, not an accident of which suite it lives in.
- --body-file is resolved to the file's content in the recorded call:
  the real gh reads the temp file before the caller deletes it, so
  assertions see the body, not a dead path. (Knowledge that lived only
  in test_validator's fake.)

`answers` maps an argv-prefix tuple to canned stdout — a str, or a
callable(args) -> str for answers that depend on the full argv (e.g.
per-issue timelines). The longest matching prefix wins; no match
answers "".
"""
import subprocess
from pathlib import Path


def default_error():
    """What subprocess.run(check=True) raises for a gh that ran and
    failed — command exit, stderr and all."""
    return subprocess.CalledProcessError(1, "gh", stderr="boom\n")


class FakeGh:
    """Injected gh runner: records every call, answers by argv prefix,
    and raises `error` on the `failing` prefix — never the network."""

    def __init__(self, answers=None, failing=None, error=None):
        self.answers = dict(answers or {})
        self.failing = None if failing is None else list(failing)
        self.error = error if error is not None else default_error()
        self.calls = []

    def __call__(self, args):
        call = list(args)
        if "--body-file" in call:
            index = call.index("--body-file") + 1
            call[index] = Path(call[index]).read_text(encoding="utf-8")
        self.calls.append(call)
        answer = self.answer(list(args))
        if (self.failing is not None
                and list(args[:len(self.failing)]) == self.failing):
            raise self.error
        return answer

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
