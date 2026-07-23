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
(nesting a harness under Claude Code), version (provenance probes), and
write_outputs (the $GITHUB_OUTPUT heredoc form assembler.py and
cost_report.py both emit).
"""
import os
import subprocess

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


def runner(binary):
    """A run(args) callable shelling out to `binary`, returning the
    CompletedProcess. A failed or missing binary raises CLI_FAILURES —
    the caller's concern, not this adapter's."""
    def run(args):
        return subprocess.run([binary, *args], check=True,
                              capture_output=True, text=True)
    return run
