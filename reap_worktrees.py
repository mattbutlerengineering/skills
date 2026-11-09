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
USAGE = "usage: python3 reap_worktrees.py [--apply | --no-fetch]"
# The full ref: a bare `origin/main` resolves refs/tags/origin/main and
# refs/heads/origin/main before refs/remotes/origin/main, so a stray local
# branch or tag of that name would stand in for the remote.
REMOTE_MAIN = "refs/remotes/origin/main"
TIMEOUT = 120


def run(args, cwd=None):
    """The command port: `args` is the full argv; returns the
    CompletedProcess whatever the exit status (lsof exits 1 for both
    idle and broken, so callers read output). A missing binary or a
    timeout raises cli.CLI_FAILURES."""
    return subprocess.run(args, capture_output=True, text=True,
                          timeout=TIMEOUT, cwd=cwd)


def parse_worktrees(text):
    """`git worktree list --porcelain -z` -> [{path, head, branch}], the
    branch without its refs/heads/ prefix, None when detached or bare.
    NUL separates fields and an empty field ends a record, so a path
    holding a newline survives intact."""
    out, cur = [], None
    for field in text.split("\0"):
        if not field:
            if cur and cur["path"] is not None:
                out.append(cur)
            cur = None
            continue
        if cur is None:
            cur = {"path": None, "head": None, "branch": None,
                   "locked": False}
        key, _, val = field.partition(" ")
        if key == "worktree":
            cur["path"] = val
        elif key == "HEAD":
            cur["head"] = val
        elif key == "branch":
            cur["branch"] = val.removeprefix("refs/heads/")
        elif key == "locked":
            cur["locked"] = True
    if cur and cur["path"] is not None:
        out.append(cur)
    return out


def shown(path):
    """A path for one output line: a newline never splits the line."""
    return path.replace("\n", "\\n").replace("\r", "\\r")


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
    return f"`{shown(' '.join(args))}` exited {proc.returncode}" + (
        f": {err[-1]}" if err else "")


def test_clean(runner, path):
    # --untracked-files=all and --ignore-submodules=none override a repo's
    # status.showUntrackedFiles / diff.ignoreSubmodules, which would hide
    # untracked files or dirty submodules from a plain `status --porcelain`.
    args = ["git", "-C", path, "status", "--porcelain",
            "--untracked-files=all", "--ignore-submodules=none"]
    proc, why = _try(runner, args)
    if why:
        return False, why, True
    if proc.returncode != 0:
        return False, _failed(args, proc), True
    if proc.stdout.strip():
        return False, "dirty: uncommitted changes", False
    # assume-unchanged (lowercase tag) and skip-worktree (S) files hide
    # their edits from status, so read the index flags too. A skip-worktree
    # entry whose file is absent is no edit (`git sparse-checkout` marks
    # every file outside its cone so), so only a file that exists counts.
    args = ["git", "-C", path, "ls-files", "-v", "-z"]
    proc, why = _try(runner, args)
    if why:
        return False, why, True
    if proc.returncode != 0:
        return False, _failed(args, proc), True
    for entry in proc.stdout.split("\0"):
        if (entry[:1].islower() or entry[:1] == "S") and os.path.lexists(
                os.path.join(path, entry[2:])):
            return False, "dirty (hidden index flags)", False
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
    args = ["git", "merge-base", "--is-ancestor", tip, REMOTE_MAIN]
    proc, why = _try(runner, args, cwd=repo)
    if why:
        return False, why, True
    if proc.returncode == 0:
        return True, "", False
    if proc.returncode == 1:
        return False, f"tip not merged: no merged PR carries it and it is not on {REMOTE_MAIN}", False
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


def _nested_in(inner, outer):
    """True if `outer` is a parent directory of `inner`, by file identity:
    a string compare misses a case-variant spelling on a case-insensitive
    filesystem (`OUTER` vs `outer`)."""
    try:
        target = os.stat(outer)
    except OSError:
        return False
    parent = os.path.dirname(inner)
    while True:
        try:
            st = os.stat(parent)
            if (st.st_dev, st.st_ino) == (target.st_dev, target.st_ino):
                return True
        except OSError:
            pass
        up = os.path.dirname(parent)
        if up == parent:
            return False
        parent = up


def reap(apply, runner=run, cwd=None, size=dir_size, which=shutil.which,
         out=print, fetch=True):
    """Returns (problems, freed_bytes, candidates, kept). Prints one line
    per worktree through `out`."""
    cwd = os.path.realpath(cwd or os.getcwd())
    problems = []
    if fetch:
        proc, why = _try(runner,
                         ["git", "-C", cwd, "fetch", "origin", "--prune"])
        if why or proc.returncode != 0:
            return [f"{LABEL}: git fetch origin --prune failed, nothing "
                    "removed: "
                    + (why or _failed(["git", "fetch"], proc))], 0, 0, 0
    args = ["git", "-C", cwd, "worktree", "list", "--porcelain", "-z"]
    proc, why = _try(runner, args)
    if why or proc.returncode != 0:
        return [f"{LABEL}: cannot list worktrees: "
                + (why or _failed(args, proc))], 0, 0, 0
    trees = parse_worktrees(proc.stdout)
    if not trees:
        return [f"{LABEL}: no worktrees listed"], 0, 0, 0
    repo = trees[0]["path"]
    scope = os.path.realpath(os.path.join(repo, SCOPE))
    seen = {os.path.realpath(repo)}
    reals = {os.path.realpath(w["path"]) for w in trees[1:]}
    freed = candidates = kept = 0
    for wt in trees[1:]:
        path = wt["path"]
        real = os.path.realpath(path)
        if real in seen:
            continue
        seen.add(real)
        if not _within(real, scope) or real == scope:
            out(f"{LABEL}: skip {shown(path)} (outside {SCOPE}, "
                f"{human(size(path)) if os.path.isdir(path) else 'missing'})")
            continue
        inner = min((r for r in reals if r != real and _nested_in(r, real)),
                    default=None)
        if inner is not None:
            kept += 1
            out(f"{LABEL}: keep {shown(path)} "
                f"(contains worktree {shown(inner)})")
            continue
        if _within(cwd, real):
            kept += 1
            out(f"{LABEL}: keep {shown(path)} (the checkout this run is in)")
            continue
        if wt["locked"]:
            kept += 1
            out(f"{LABEL}: keep {shown(path)} (locked)")
            continue
        ok, reason, is_problem = judge(runner, repo, wt, which)
        if not ok:
            kept += 1
            out(f"{LABEL}: keep {shown(path)} ({reason})")
            if is_problem:
                problems.append(f"{LABEL}: {shown(path)}: {reason}")
            continue
        nbytes = size(path)
        candidates += 1
        if not apply:
            freed += nbytes
            out(f"{LABEL}: would-remove {shown(path)} ({human(nbytes)})")
            continue
        args = ["git", "worktree", "remove", path]
        proc, why = _try(runner, args, cwd=repo)
        if why or proc.returncode != 0:
            kept += 1
            candidates -= 1
            reason = why or _failed(args, proc)
            out(f"{LABEL}: keep {shown(path)} (remove failed: {reason})")
            problems.append(f"{LABEL}: {shown(path)}: remove failed: {reason}")
            continue
        freed += nbytes
        note = human(nbytes)
        branch = wt["branch"]
        if branch is not None and branch != "main":
            args = ["git", "branch", "-D", "--", branch]
            proc, why = _try(runner, args, cwd=repo)
            if why or proc.returncode != 0:
                reason = why or _failed(args, proc)
                problems.append(
                    f"{LABEL}: {shown(path)}: branch {branch} not deleted: {reason}")
                note += f", branch {branch} not deleted"
            else:
                note += f", branch {branch} deleted"
        out(f"{LABEL}: removed {shown(path)} ({note})")
    return problems, freed, candidates, kept


def main(argv, runner=run, cwd=None, size=dir_size, which=shutil.which):
    """`python3 reap_worktrees.py [--apply | --no-fetch]` — exit 0 clean,
    1 with problems, 2 on usage. `--no-fetch` is the offline dry run;
    with `--apply` the fetch is mandatory, so the two never combine."""
    if argv not in ([], ["--apply"], ["--no-fetch"]):
        print(USAGE)
        return 2
    apply = argv == ["--apply"]
    problems, freed, candidates, kept = reap(
        apply, runner, cwd, size, which, fetch=argv != ["--no-fetch"])
    verb = "freed" if apply else "would free"
    noun = "removed" if apply else "would remove"
    print(f"{LABEL}: {noun} {candidates}, kept {kept}, {verb} "
          f"{human(freed)} ({freed} bytes)" + ("" if apply else
          "; dry run, pass --apply to remove"))
    return cli.report(LABEL, problems)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
