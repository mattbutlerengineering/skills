#!/usr/bin/env python3
"""cli: the shared adapter over an external CLI (ADR-0037).

Two tools shell out to a binary and turn its failures into problem
strings — label_sync.py (gh) and budget_guard.py (git) — and before this
seam each carried a byte-identical copy of the failure tuple and the
one-line detail formatter. Two adapters make the seam real: the failure
vocabulary and its formatting live here once; each caller keeps its own
port (gh_runner returns stdout, git_runner the CompletedProcess) and its
own problem-string label. Tests inject a fake runner so they never touch
a real CLI.

The harness-IO conventions live here for the same reason: child_env
(nesting a harness under Claude Code), version (provenance probes),
write_outputs (the $GITHUB_OUTPUT heredoc form assembler.py and
cost_report.py both emit), and read_event (the $GITHUB_EVENT_PATH read
gates.py and assembler.py both make — ADR-0042). decode_events and
harness_run (ADR-0045) are the streaming half: the one JSON-lines
decode every harness stream shares, and the spawn-watch-reap lifecycle
of a `-p` harness child (own process group, drain-after-exit reader,
unconditional group kill) that trigger_eval.py and charter_replay.py
both run. harness_run is POSIX-only (select on pipes, os.killpg), the
stance trigger_eval.py has always documented.

gh_runner, the stdout port over runner("gh"), lives beside runner for the
same reason write_outputs moved here (ADR-0040): it had grown four real
callers (label_sync, validator, gate_digest, sweeps), three of them
importing it tool-to-tool from label_sync.
"""
import contextlib
import json
import os
import select
import signal
import subprocess
import time
from pathlib import Path

# A failed or missing binary raises one of these; callers turn that into
# a label-prefixed problem string instead of a traceback.
CLI_FAILURES = (subprocess.CalledProcessError, OSError)


def child_env():
    """The environment for a harness child process: the caller's environ
    minus CLAUDECODE, so an eval run or charter replay can nest
    `claude -p` inside a Claude Code session — the guard exists for
    interactive terminal conflicts, not child runs. Returns a copy;
    mutating it never touches os.environ."""
    return {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}


def detail(err):
    """One-line detail for a failed CLI call's problem string: the
    command's own stderr when it ran, else the OS error (e.g. the binary
    not installed)."""
    stderr = (getattr(err, "stderr", None) or "").strip()
    return stderr.splitlines()[-1] if stderr else str(err)


def version(binary):
    """The binary's --version line, or None when the probe fails.

    Provenance metadata for results snapshots, not a dependency check —
    a missing or hanging binary must never turn the probe into a crash,
    so failure is None rather than a CLI_FAILURES raise.
    """
    try:
        proc = subprocess.run([binary, "--version"], capture_output=True,
                              text=True, timeout=15)
        return proc.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def decode_events(lines):
    """Decode an iterable of JSON-lines into event dicts. Blank and
    undecodable lines are skipped — harness streams interleave noise
    with events, and a half-written trailing line must not abort the
    run. The one decode every harness stream shares (ADR-0045); the
    per-harness registry (trigger_eval.HARNESSES) names it so recorders
    and runners cannot fork their own copies."""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


class EventStream:
    """Decoded JSON-lines events from a live harness pipe, until the
    process exits AND its buffered output is drained, the stream closes,
    or timeout elapses. `timed_out` flips True when the reader abandoned
    the run on the clock — how a consumer that read the stream to its
    end tells a completed run from a truncated one.

    The drain-after-exit order is load-bearing: a harness that writes its
    whole stream and exits within milliseconds is often dead before the
    reader's first poll, and breaking on exit alone silently drops
    whatever is still in the pipe — a fired run scores 'none' (observed
    as a CI-only flake in the fake-harness suite). After exit the reader
    stops the first time the pipe reads empty, so an orphaned child
    holding the write end open but idle costs nothing; one that keeps
    writing is bounded by the overall timeout. A trailing line with no
    newline is dropped — harness streams are newline-terminated."""

    def __init__(self, process, timeout):
        self.timed_out = False
        self._iter = decode_events(self._lines(process, timeout))

    def __iter__(self):
        return self._iter

    def _lines(self, process, timeout):
        start_time = time.time()
        buffer = ""
        while True:
            if time.time() - start_time >= timeout:
                self.timed_out = True
                return
            exited = process.poll() is not None
            ready, _, _ = select.select([process.stdout], [], [],
                                        0 if exited else 1.0)
            if not ready:
                if exited:
                    return
                continue

            chunk = os.read(process.stdout.fileno(), 8192)
            if not chunk:
                return
            buffer += chunk.decode("utf-8", errors="replace")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                yield line


@contextlib.contextmanager
def harness_run(cmd, cwd, timeout, env=None, spawn=None):
    """Run a harness command in its own process group and yield its
    EventStream; on the way out, SIGKILL the whole group unconditionally
    — early detection returns before the CLI exits, and a dead leader's
    grandchildren keep the group alive and would otherwise outlive the
    run (burning API budget). start_new_session makes the leader's pid
    the pgid, and the kernel keeps that pgid alive while any grandchild
    survives, so the group is signalled whether the leader is running,
    exited with survivors, or setpgid itself away (the leader-only kill
    covers the last; an empty group's lookup failure is swallowed). The
    pipe is closed after the wait, so no fd leaks per run.

    env defaults to child_env(); spawn is the injectable substitute
    (tests pass a fake instead of monkeypatching subprocess). A spawn
    that never starts raises straight into the caller's catch — there
    is nothing to clean up."""
    process = (spawn or subprocess.Popen)(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=cwd,
        env=child_env() if env is None else env,
        start_new_session=True,
    )
    try:
        yield EventStream(process, timeout)
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            # Group empty (then Popen.kill is a no-op — poll already
            # recorded the exit) or a leader that setpgid itself out
            # of the group; the leader-only kill covers the latter.
            process.kill()
        process.wait()
        process.stdout.close()


def write_outputs(env, outputs):
    """Append outputs to $GITHUB_OUTPUT for the workflow's downstream steps.
    Multiline values (e.g. the assembler's prompt) use GitHub's heredoc
    form. No GITHUB_OUTPUT (a hand or local run) is a silent no-op."""
    path = env.get("GITHUB_OUTPUT")
    if not path:
        return
    chunks = []
    for key, value in outputs.items():
        text = str(value)
        if "\n" in text:
            delim = f"__{key.upper()}_EOF__"
            chunks.append(f"{key}<<{delim}\n{text}\n{delim}")
        else:
            chunks.append(f"{key}={text}")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(chunks) + "\n")


def read_event(env):
    """(the CI event payload, error) from $GITHUB_EVENT_PATH. (None, None)
    when the environment carries no event path — absence is a fact, not an
    error, and each caller judges it (detector B skips silently outside a
    PR run; the assembler calls it a problem). An unreadable, unparsable,
    or non-object payload is an error string the caller labels."""
    path = env.get("GITHUB_EVENT_PATH")
    if not path:
        return None, None
    try:
        event = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        return None, f"cannot read GITHUB_EVENT_PATH {path}: {err}"
    if not isinstance(event, dict):
        return None, f"GITHUB_EVENT_PATH {path} is not a JSON object"
    return event, None


def runner(binary):
    """A run(args) callable shelling out to `binary`, returning the
    CompletedProcess. A failed or missing binary raises CLI_FAILURES —
    the caller's concern, not this adapter's."""
    def run(args):
        return subprocess.run([binary, *args], check=True,
                              capture_output=True, text=True)
    return run


_gh = runner("gh")


def gh_runner(args):
    """The gh port: shell out to gh (runner), return stdout. A missing
    (OSError), unauthenticated, or rate-limited (CalledProcessError) gh
    raises CLI_FAILURES — each caller turns that into its own
    label-prefixed problem string, never a traceback. Tests inject a fake
    runner so they never touch the network."""
    return _gh(args).stdout


def gh_json(args, run=gh_runner, expect=None):
    """(parsed value, problem-suffix): run gh and parse its stdout as
    JSON. The third failure vocabulary entry — ran, exited 0, said
    something unreadable — becomes a suffix here instead of a traceback
    in a scheduled job; `expect` (list or dict) adds the wrong-shape
    case. The suffix is a verb phrase with no label and no operation:
    the caller prefixes both ("gd: gh issue list " + suffix), exactly
    the cost_ledger.line_problems convention, so identical failures at
    different call sites stay tellable apart. (None, suffix) on any
    failure; a failed/missing gh still raises CLI_FAILURES — that
    vocabulary entry stays the caller's catch."""
    out = run(args)
    try:
        value = json.loads(out)
    except json.JSONDecodeError as err:
        return None, f"returned unparseable JSON: {err}"
    if expect is not None and not isinstance(value, expect):
        return None, (f"returned {type(value).__name__} where"
                      f" {expect.__name__} was expected")
    return value, None


def full_window(entries, limit):
    """Problem-suffix when a windowed gh listing came back full — gh
    truncates silently, so a full window means entries past it are
    invisible and must be reported, never trusted (the sweeps
    known_keys rule, made shared). A verb phrase like gh_json's: the
    caller names the operation and its own label."""
    if len(entries) >= limit:
        return (f"returned a full {limit}-entry window — older entries"
                " are invisible; raise the window or narrow the query")
    return None
