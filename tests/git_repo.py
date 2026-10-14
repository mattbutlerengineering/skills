"""tests/git_repo.py — a real temp git repo with git's housekeeping off.

A commit (or a push into a bare repo) can start `gc --auto` or `git
maintenance run --auto`, which may detach and keep writing
.git/objects/pack after the command returns; a TemporaryDirectory
cleanup racing it fails with ENOTEMPTY (#874, siblings #761, #803).
Every repo a suite makes is made here, so the switches are in the
repo's own config and hold for every git that touches it — the suite's
and the code under test's alike.
"""
import subprocess

QUIET = (("gc.auto", "0"), ("maintenance.auto", "false"))


def quiet(repo, env=None):
    """Turn auto-gc and auto-maintenance off in `repo`; return it."""
    for key, value in QUIET:
        subprocess.run(["git", "-C", str(repo), "config", key, value],
                       check=True, capture_output=True, env=env)
    return repo


def init(path, *flags, env=None):
    """`git init -q <flags> <path>`, made quiet; return `path`."""
    subprocess.run(["git", "init", "-q", *flags, str(path)], check=True,
                   capture_output=True, env=env)
    return quiet(path, env)


def clone(source, path, *flags, env=None):
    """`git clone -q <flags> <source> <path>`, made quiet; return `path`."""
    subprocess.run(["git", "clone", "-q", *flags, str(source), str(path)],
                   check=True, capture_output=True, env=env)
    return quiet(path, env)
