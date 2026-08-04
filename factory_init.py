#!/usr/bin/env python3
"""factory-init: stamp the factory template payload into a product repo,
and regenerate the checksum manifest that pins it (PRD-0001; ADR-0032).

Conventions match lint.py/gates.py: functions return label-prefixed
problem strings; the CLI prints them and exits nonzero.

  update-manifest   refresh the mirrors (the factory tools and the
                    validator workflow — see MIRRORS) from the repo root
                    into factory/templates/, then rewrite factory/manifest.json
                    (plugin name + version from .claude-plugin/plugin.json,
                    sha256 per template file). Detector E pins the result:
                    templates are never hand-edited without re-running this.
  stamp <target>    copy the payload into <target>: a pristine mirror
                    under factory/ (manifest + templates, what detector E
                    checks there) plus installed copies (Makefile at the
                    root, .github/factory.json, tools/factory/*). Refuses
                    a drifted source payload, a malformed manifest key, a
                    destination resolving outside the target, and any
                    existing destination file — no partial stamps, no
                    overwrites, no writes outside the target tree.
"""
import json
import shutil
import sys
from pathlib import Path

import gates

# Root files mirrored verbatim into the payload (repo-root path -> path
# under factory/templates/), so a stamped product repo runs the same tools
# and the same CI as this one — one source of truth, never a hand-maintained
# second copy. gates.py imports its sibling protocol; label_sync.py is the
# sweeps-only network detector L; validator.py is the validator workflow's
# brain; budget_guard.py/handoff.py are the ADR-0034 dollar-budget stop and
# its hard-stop handoff, run ad hoc by a dispatched agent, not by a workflow
# step of their own. orientation_pack.py is assembler.py's sibling import
# (WO-0015 — the orientation pack folded into the dispatched prompt),
# mirrored alongside it for the same reason. cost_report.py is the ADR-0034
# weekly rollup and monthly circuit breaker (WO-0009): unlike budget_guard,
# it IS driven by its own scheduled workflow step (`make cost-report` in
# cost-report.yml), but the same compute/mutate split holds — it computes
# only, the workflow is the one that mutates (gh issue create, gh variable
# set). knowledge_plane.py, cli.py, factory_config.py, and cost_ledger.py
# are the ADR-0037 seam modules the tools above import as siblings —
# mirrored for the same reason protocol.py is. validator.yml is
# path-agnostic (it runs `make` targets), which is what lets it be mirrored
# byte-for-byte instead of forked per repo.
MIRRORS = {
    "gates.py": "tools/factory/gates.py",
    "protocol.py": "tools/factory/protocol.py",
    "knowledge_plane.py": "tools/factory/knowledge_plane.py",
    "cli.py": "tools/factory/cli.py",
    "factory_config.py": "tools/factory/factory_config.py",
    "cost_ledger.py": "tools/factory/cost_ledger.py",
    "label_sync.py": "tools/factory/label_sync.py",
    "validator.py": "tools/factory/validator.py",
    "assembler.py": "tools/factory/assembler.py",
    "budget_guard.py": "tools/factory/budget_guard.py",
    "handoff.py": "tools/factory/handoff.py",
    "orientation_pack.py": "tools/factory/orientation_pack.py",
    "cost_report.py": "tools/factory/cost_report.py",
    "gate_digest.py": "tools/factory/gate_digest.py",
    ".github/workflows/validator.yml": ".github/workflows/validator.yml",
    ".github/workflows/assembler.yml": ".github/workflows/assembler.yml",
    ".github/workflows/design.yml": ".github/workflows/design.yml",
    ".github/workflows/cost-report.yml": ".github/workflows/cost-report.yml",
    ".github/workflows/gate-digest.yml": ".github/workflows/gate-digest.yml",
}

# Manifest rel -> install destination; anything unmapped strips "templates/".
INSTALL_MAP = {"templates/factory.json": ".github/factory.json"}


def install_path(rel):
    """(destination in a product repo, problem). A manifest key must be
    a plain relative path under templates/ — anything else is refused,
    never sliced into something that happens to join cleanly. The
    checksum gate upstream makes a malformed key unlikely; this makes
    the write path safe by construction, not by upstream luck. The one
    exception: an INSTALL_MAP hit returns its repo-controlled value
    verbatim, unvalidated — stamp's containment pass is what bounds
    those destinations."""
    if rel in INSTALL_MAP:
        return INSTALL_MAP[rel], None
    if not rel.startswith("templates/"):
        return None, (f"factory-init: manifest key {rel!r} is not under"
                      " templates/")
    dest = rel[len("templates/"):]
    parts = dest.split("/")
    # "" in parts covers the empty, leading-slash, and doubled-slash
    # shapes in one clause.
    if "\x00" in dest or ".." in parts or "." in parts or "" in parts:
        return None, (f"factory-init: manifest key {rel!r} does not"
                      " resolve to a plain relative path")
    return dest, None


def update_manifest(root):
    """Refresh the payload mirrors and rewrite the checksum manifest."""
    root = Path(root)
    problems = []
    plugin_meta = root / ".claude-plugin" / "plugin.json"
    if not plugin_meta.is_file():
        problems.append("factory-init: missing .claude-plugin/plugin.json")
    problems += [f"factory-init: missing {name} at repo root"
                 for name in MIRRORS if not (root / name).is_file()]
    if problems:
        return problems
    meta = json.loads(plugin_meta.read_text(encoding="utf-8"))
    templates = root / "factory" / "templates"
    for name, rel in MIRRORS.items():
        mirror = templates / rel
        mirror.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, mirror)
    # the walk-hash-key grammar is gates.manifest_files — the same map
    # detector E diffs against, so writer and verifier cannot diverge
    manifest = {"plugin": meta.get("name"), "version": meta.get("version"),
                "files": gates.manifest_files(root)}
    (root / "factory" / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return []


def stamp(source, target):
    """Stamp the source payload into target; refuse drift and overwrites."""
    source, target = Path(source), Path(target)
    problems = gates.check_scaffold_sync(source)
    if problems:
        return problems
    manifest_src = source / "factory" / "manifest.json"
    files = json.loads(manifest_src.read_text(encoding="utf-8"))["files"]
    copies = [(manifest_src, Path("factory/manifest.json"))]
    problems = []
    for rel in sorted(files):
        copies.append((source / "factory" / rel, Path("factory") / rel))
        dest, problem = install_path(rel)
        if problem:
            problems.append(problem)
            continue
        copies.append((source / "factory" / rel, Path(dest)))
    if problems:
        return problems
    # Every resolved destination — INSTALL_MAP's entries included — must
    # stay inside the resolved target tree, checked before any write.
    target_root = target.resolve()
    escapes = [f"factory-init: destination {dest.as_posix()} escapes"
               " the stamp target" for _, dest in copies
               if not (target / dest).resolve().is_relative_to(target_root)]
    if escapes:
        return escapes
    clashes = [f"factory-init: target already has {dest.as_posix()}"
               for _, dest in copies if (target / dest).exists()]
    if clashes:
        return clashes
    for src, dest in copies:
        (target / dest).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target / dest)
    return []


def main(argv):
    root = Path(__file__).resolve().parent
    if argv == ["update-manifest"]:
        problems = update_manifest(root)
    elif len(argv) == 2 and argv[0] == "stamp":
        problems = stamp(root, Path(argv[1]))
    else:
        print(__doc__.strip())
        return 2
    for problem in problems:
        print(problem)
    print(f"factory-init: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
