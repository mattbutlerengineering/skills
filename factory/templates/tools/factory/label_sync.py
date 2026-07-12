#!/usr/bin/env python3
"""label-sync: detector L (LABEL-SYNC) — the GitHub label taxonomy must
match .github/labels.json (PRD-0001; ADR-0033 lifecycle labels).

A NETWORK detector: it reads the live label set through the gh CLI, so it
runs in scheduled sweeps only and is NEVER wired into gates.py CHECKERS
(those stay offline). Conventions match gates.py/lint.py: functions return
L:-prefixed problem strings; the CLI prints them and exits nonzero.

  python3 label_sync.py           report drift (gh label list)
  python3 label_sync.py --apply   also create/update each drifted label
                                  (gh label create --force)

Drift is one-way: labels outside the taxonomy are ignored (GitHub's
default labels are not drift), so --apply never deletes anything.
"""
import json
import subprocess
import sys
from pathlib import Path

LABEL_FIELDS = ("name", "color", "description")


def load_labels(root):
    """Desired taxonomy for a repo: the installed .github/labels.json when
    stamped, else the template payload copy. Returns (labels, problems);
    malformed entries are excluded from labels and reported."""
    root = Path(root)
    candidates = (root / ".github" / "labels.json",
                  root / "factory" / "templates" / ".github" / "labels.json")
    path = next((p for p in candidates if p.is_file()), None)
    if path is None:
        return [], ["L: missing labels.json (.github/labels.json or"
                    " factory/templates/.github/labels.json)"]
    rel = path.relative_to(root).as_posix()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return [], [f"L: {rel} is not valid JSON: {err}"]
    if not isinstance(data, list) or not data:
        return [], [f"L: {rel} must be a non-empty JSON array"
                    " of label entries"]
    labels, problems = [], []
    for index, entry in enumerate(data):
        fields = entry if isinstance(entry, dict) else {}
        lacking = [field for field in LABEL_FIELDS
                   if not isinstance(fields.get(field), str)
                   or not fields.get(field)]
        if lacking:
            problems.append(
                f"L: {rel}[{index}] entry lacks {', '.join(lacking)}")
        else:
            labels.append({field: fields[field] for field in LABEL_FIELDS})
    return labels, problems


def plan(current, desired):
    """PURE drift computation: the L: problems that make current match
    desired. Labels outside the taxonomy are ignored (GitHub defaults are
    not drift), so an empty desired plans nothing."""
    have = {label.get("name"): label for label in current}
    problems = []
    for want in desired:
        got = have.get(want["name"])
        if got is None:
            problems.append(f"L: missing label {want['name']}")
            continue
        if got.get("color") != want["color"]:
            problems.append(f"L: label {want['name']} color"
                            f" {got.get('color')}, want {want['color']}")
        if got.get("description") != want["description"]:
            problems.append(
                f"L: label {want['name']} description"
                f" {got.get('description')!r}, want {want['description']!r}")
    return problems


def gh_runner(args):
    """Default runner: shell out to gh, return stdout. Tests inject a fake
    so they never touch the network."""
    return subprocess.run(["gh", *args], check=True, capture_output=True,
                          text=True).stdout


def sync(root, apply=False, run=gh_runner):
    """Report drift between the live label set and the taxonomy; with
    apply=True, force-create each drifted label (gh treats create --force
    on an existing name as an update). A broken labels.json short-circuits
    before any network call."""
    desired, problems = load_labels(root)
    if problems:
        return problems
    current = json.loads(run(["label", "list", "--json",
                              "name,color,description", "--limit", "1000"]))
    problems = []
    for want in desired:
        drift = plan(current, [want])
        problems.extend(drift)
        if apply and drift:
            run(["label", "create", want["name"], "--force",
                 "--color", want["color"],
                 "--description", want["description"]])
    return problems


def repo_root():
    """Nearest ancestor containing .git (dir or worktree file): correct at
    the factory repo root and stamped at tools/factory/ in a product repo."""
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    return here


def main(argv, run=gh_runner):
    apply = "--apply" in argv
    if [arg for arg in argv if arg != "--apply"]:
        print(__doc__.strip())
        return 2
    problems = sync(repo_root(), apply=apply, run=run)
    for problem in problems:
        print(problem)
    print(f"label-sync: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
