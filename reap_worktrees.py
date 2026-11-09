"""reap_worktrees.py — remove merged, idle agent worktrees under
`<repo>/.claude/worktrees/`.

`python3 reap_worktrees.py` is a dry run; `--apply` removes. The rule is
`## reap` in .claude/implement-queue.md (four tests: clean, idle, no open
PR, this tip merged); this module implements it and the profile points at
it. Every command goes through one injected runner, so a failed command is
a failure, never a pass. Root-only: no payload tool imports it.
"""
import json
import os
import shutil
import subprocess
import sys

import cli

LABEL = "reap"
SCOPE = os.path.join(".claude", "worktrees")
USAGE = "usage: python3 reap_worktrees.py [--apply]"
TIMEOUT = 120


def run(args, cwd=None):
    """The command port: `args` is the full argv; returns the
    CompletedProcess whatever the exit status (lsof exits 1 for both
    idle and broken, so callers read output). A missing binary or a
    timeout raises cli.CLI_FAILURES."""
    return subprocess.run(args, capture_output=True, text=True,
                          timeout=TIMEOUT, cwd=cwd)


def parse_worktrees(text):
    """`git worktree list --porcelain` -> [{path, head, branch}], the
    branch without its refs/heads/ prefix, None when detached or bare."""
    out, cur = [], None
    for line in text.splitlines() + [""]:
        if not line:
            if cur and "path" in cur:
                out.append(cur)
            cur = None
            continue
        if cur is None:
            cur = {"path": None, "head": None, "branch": None}
        key, _, val = line.partition(" ")
        if key == "worktree":
            cur["path"] = val
        elif key == "HEAD":
            cur["head"] = val
        elif key == "branch":
            cur["branch"] = val.removeprefix("refs/heads/")
    return out


def dir_size(path):
    """Bytes under `path`, symlinks counted as links, never followed."""
    total = 0
    for root, dirs, files in os.walk(path):
        for name in dirs + files:
            try:
                total += os.lstat(os.path.join(root, name)).st_size
            except OSError:
                pass
    return total


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n} B" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def _try(runner, args, cwd=None):
    """(CompletedProcess, None) or (None, why) for a command that
    could not run at all."""
    try:
        return runner(args, cwd=cwd), None
    except cli.CLI_FAILURES as e:
        return None, f"{args[0]} could not run: {e}"


def _failed(args, proc):
    err = (proc.stderr or "").strip().splitlines()
    return f"`{' '.join(args)}` exited {proc.returncode}" + (
        f": {err[-1]}" if err else "")


def test_clean(runner, path):
    args = ["git", "-C", path, "status", "--porcelain"]
    proc, why = _try(runner, args)
    if why:
        return False, why, True
    if proc.returncode != 0:
        return False, _failed(args, proc), True
    if proc.stdout.strip():
        return False, "dirty: uncommitted changes", False
    return True, "", False


def test_idle(runner, path, which=shutil.which):
    if not which("lsof"):
        return False, "lsof not on PATH", True
    if not os.path.exists(path):
        return False, "path does not exist", True
    proc, why = _try(runner, ["lsof", "-w", "+D", path])
    if why:
        return False, why, True
    if (proc.stderr or "").strip():
        return False, "lsof wrote to stderr: " + proc.stderr.strip().splitlines()[-1], True
    if (proc.stdout or "").strip():
        return False, "busy: open files under the path", False
    return True, "", False


def test_no_open_pr(runner, repo, branch):
    if branch is None:
        return True, "", False
    args = ["gh", "pr", "list", "--head", branch, "--state", "open"]
    proc, why = _try(runner, args, cwd=repo)
    if why:
        return False, why, True
    if proc.returncode != 0:
        return False, _failed(args, proc), True
    if proc.stdout.strip():
        return False, "open PR for branch", False
    return True, "", False


def test_tip_merged(runner, repo, branch, tip):
    if not tip:
        return False, "no HEAD commit", True
    if branch is not None:
        args = ["gh", "pr", "list", "--head", branch, "--base", "main",
                "--state", "merged", "--json", "headRefOid"]
        proc, why = _try(runner, args, cwd=repo)
        if why:
            return False, why, True
        if proc.returncode != 0:
            return False, _failed(args, proc), True
        try:
            oids = {p["headRefOid"] for p in json.loads(proc.stdout)}
        except (ValueError, TypeError, KeyError):
            return False, "gh merged-PR list was not the expected JSON", True
        if tip in oids:
            return True, "", False
    args = ["git", "merge-base", "--is-ancestor", tip, "origin/main"]
    proc, why = _try(runner, args, cwd=repo)
    if why:
        return False, why, True
    if proc.returncode == 0:
        return True, "", False
    if proc.returncode == 1:
        return False, "tip not merged: no merged PR carries it and it is not on origin/main", False
    return False, _failed(args, proc), True


def judge(runner, repo, wt, which=shutil.which):
    """Apply the four tests in order; (passed, reason, is_problem) of
    the first failure."""
    for result in (
        test_clean(runner, wt["path"]),
        test_idle(runner, wt["path"], which),
        test_no_open_pr(runner, repo, wt["branch"]),
        test_tip_merged(runner, repo, wt["branch"], wt["head"]),
    ):
        if not result[0]:
            return result
    return True, "", False


def _within(path, parent):
    return os.path.commonpath([path, parent]) == parent


def reap(apply, runner=run, cwd=None, size=dir_size, which=shutil.which,
         out=print):
    """Returns (problems, freed_bytes, candidates, kept). Prints one line
    per worktree through `out`."""
    cwd = os.path.realpath(cwd or os.getcwd())
    problems = []
    proc, why = _try(runner, ["git", "-C", cwd, "fetch", "origin", "--prune"])
    if why or proc.returncode != 0:
        return [f"{LABEL}: git fetch origin --prune failed, nothing removed: "
                + (why or _failed(["git", "fetch"], proc))], 0, 0, 0
    args = ["git", "-C", cwd, "worktree", "list", "--porcelain"]
    proc, why = _try(runner, args)
    if why or proc.returncode != 0:
        return [f"{LABEL}: cannot list worktrees: "
                + (why or _failed(args, proc))], 0, 0, 0
    trees = parse_worktrees(proc.stdout)
    if not trees:
        return [f"{LABEL}: no worktrees listed"], 0, 0, 0
    repo = trees[0]["path"]
    scope = os.path.join(os.path.realpath(repo), SCOPE)
    freed = candidates = kept = 0
    for wt in trees[1:]:
        path = wt["path"]
        real = os.path.realpath(path)
        if not _within(real, scope) or real == scope:
            out(f"{LABEL}: skip {path} (outside {SCOPE}, "
                f"{human(size(path)) if os.path.isdir(path) else 'missing'})")
            continue
        if _within(cwd, real):
            kept += 1
            out(f"{LABEL}: keep {path} (the checkout this run is in)")
            continue
        ok, reason, is_problem = judge(runner, repo, wt, which)
        if not ok:
            kept += 1
            out(f"{LABEL}: keep {path} ({reason})")
            if is_problem:
                problems.append(f"{LABEL}: {path}: {reason}")
            continue
        nbytes = size(path)
        candidates += 1
        if not apply:
            freed += nbytes
            out(f"{LABEL}: would-remove {path} ({human(nbytes)})")
            continue
        args = ["git", "worktree", "remove", path]
        proc, why = _try(runner, args, cwd=repo)
        if why or proc.returncode != 0:
            kept += 1
            candidates -= 1
            reason = why or _failed(args, proc)
            out(f"{LABEL}: keep {path} (remove failed: {reason})")
            problems.append(f"{LABEL}: {path}: remove failed: {reason}")
            continue
        freed += nbytes
        note = human(nbytes)
        branch = wt["branch"]
        if branch is not None and branch != "main":
            args = ["git", "branch", "-D", branch]
            proc, why = _try(runner, args, cwd=repo)
            if why or proc.returncode != 0:
                reason = why or _failed(args, proc)
                problems.append(
                    f"{LABEL}: {path}: branch {branch} not deleted: {reason}")
                note += f", branch {branch} not deleted"
            else:
                note += f", branch {branch} deleted"
        out(f"{LABEL}: removed {path} ({note})")
    return problems, freed, candidates, kept


def main(argv, runner=run, cwd=None, size=dir_size, which=shutil.which):
    """`python3 reap_worktrees.py [--apply]` — exit 0 clean, 1 with
    problems, 2 on usage."""
    if argv not in ([], ["--apply"]):
        print(USAGE)
        return 2
    apply = bool(argv)
    problems, freed, candidates, kept = reap(apply, runner, cwd, size, which)
    verb = "freed" if apply else "would free"
    noun = "removed" if apply else "would remove"
    print(f"{LABEL}: {noun} {candidates}, kept {kept}, {verb} "
          f"{human(freed)} ({freed} bytes)" + ("" if apply else
          "; dry run, pass --apply to remove"))
    return cli.report(LABEL, problems)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
