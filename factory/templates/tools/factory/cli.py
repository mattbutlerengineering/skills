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
gates.py and assembler.py both make — ADR-0042).

gh_runner, the stdout port over runner("gh"), lives beside runner for the
same reason write_outputs moved here (ADR-0040): it had grown four real
callers (label_sync, validator, gate_digest, sweeps), three of them
importing it tool-to-tool from label_sync.
"""
import json
import os
import subprocess
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
