"""ADR-0096's fast-path classifier: is a PR's diff docs-only and clear of
every gate path? (faster-sdlc #909)

`python3 fast_path.py <base> <head>` reads `git diff --name-only
<base>...<head>` and prints one line:

- `fast-path: low-risk`, exit 0 — every changed path is under `docs/`
  and none is a gate path. Under `merge: auto` that classification is
  the review for a PR no specialist reviewer matches (ADR-0088).
- `fast-path: review (<first non-matching path>)`, exit 1 — anything
  else, and an empty diff.
- `fast-path: git diff ... failed: <reason>`, exit 2 — git failed or a
  ref did not resolve. The queue profile's hook reads this as ADR-0088's
  fail-closed case: review the PR, dispatch every specialist.

The gate paths are ADR-0087's defaults plus the three ADR-0096 adds for
this repo. Root-only (ADR-0060's rule), stdlib only; the git port is
cli.runner("git"), injected for tests.
"""
import subprocess
import sys

import cli

# ADR-0087's default gate paths (as directory prefixes and basenames) and
# the three ADR-0096 adds: release PRs, workflows and the stamped payload
# keep a human merge.
GATE_PREFIXES = ("docs/adr/", "docs/design/", "factory/templates/",
                 ".github/")
GATE_NAMES = ("prd.md", "architecture.md")
GATE_FILES = (".claude-plugin/plugin.json",)
LOW_RISK_PREFIX = "docs/"
USAGE = ("usage: python3 fast_path.py <base> <head>\n"
         "  classifies `git diff --name-only <base>...<head>`: exit 0"
         " low-risk, 1 review, 2 git failed")


def is_gate_path(path):
    return (path in GATE_FILES
            or path.startswith(GATE_PREFIXES)
            or path.rsplit("/", 1)[-1] in GATE_NAMES)


def classify(paths):
    """"low-risk" or ("review", reason): the first path that is not a
    docs path clear of the gate paths, or "empty diff" when there is
    none to judge."""
    if not paths:
        return "review", "empty diff"
    for path in paths:
        if not path.startswith(LOW_RISK_PREFIX) or is_gate_path(path):
            return "review", path
    return "low-risk"


def changed_paths(git, base, head):
    """(paths, None) from the three-dot diff, or (None, problem) when git
    failed — a problem string, never a traceback (ADR-0021)."""
    args = ["diff", "--name-only", f"{base}...{head}"]
    try:
        out = git(args).stdout
    except cli.CLI_FAILURES as err:
        return None, (f"fast-path: git {' '.join(args)} failed:"
                      f" {cli.detail(err)}")
    return [line for line in out.splitlines() if line], None


def main(argv, git=cli.runner("git")):
    if len(argv) != 2:
        print(USAGE)
        return 2
    paths, problem = changed_paths(git, *argv)
    if problem:
        print(problem)
        return 2
    verdict = classify(paths)
    if verdict == "low-risk":
        print("fast-path: low-risk")
        return 0
    print(f"fast-path: review ({verdict[1]})")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
