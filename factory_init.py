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
                    a drifted source payload and any existing destination
                    file — no partial stamps, no overwrites.
"""
import hashlib
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
# brain. validator.yml is path-agnostic (it runs `make` targets), which is
# what lets it be mirrored byte-for-byte instead of forked per repo.
MIRRORS = {
    "gates.py": "tools/factory/gates.py",
    "protocol.py": "tools/factory/protocol.py",
    "label_sync.py": "tools/factory/label_sync.py",
    "validator.py": "tools/factory/validator.py",
    ".github/workflows/validator.yml": ".github/workflows/validator.yml",
}

# Manifest rel -> install destination; anything unmapped strips "templates/".
INSTALL_MAP = {"templates/factory.json": ".github/factory.json"}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_path(rel):
    """Destination of a manifest entry in a product repo."""
    return INSTALL_MAP.get(rel, rel[len("templates/"):])


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
    files = {p.relative_to(root / "factory").as_posix(): _sha256(p)
             for p in sorted(templates.rglob("*")) if p.is_file()}
    manifest = {"plugin": meta.get("name"), "version": meta.get("version"),
                "files": files}
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
    for rel in sorted(files):
        copies.append((source / "factory" / rel, Path("factory") / rel))
        copies.append((source / "factory" / rel, Path(install_path(rel))))
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
