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
  update <target>   refresh an ALREADY-stamped <target>: overwrite the
                    executable payload (tools/factory/, .github/workflows/)
                    and the pristine mirror, create any payload file the
                    target lacks, and leave every other existing file
                    alone — budgets, the code-owner handle and the doc
                    seeds are the repo's. Reports each kept file that
                    differs, and any `make` target the refreshed workflows
                    call that the Makefile lacks.
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
import re
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


def payload_copies(source, target):
    """([(src, dest relative to target)], problems) for the whole payload.

    The half stamp and update share: verify the source payload, resolve
    every manifest key to its mirror path and its install destination, and
    prove each stays inside the target. The two commands differ only in
    what they do when a destination already exists.
    """
    problems = gates.check_scaffold_sync(source)
    if problems:
        return [], problems
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
        return [], problems
    # Every resolved destination — INSTALL_MAP's entries included — must
    # stay inside the resolved target tree, checked before any write.
    target_root = target.resolve()
    escapes = [f"factory-init: destination {dest.as_posix()} escapes"
               " the stamp target" for _, dest in copies
               if not (target / dest).resolve().is_relative_to(target_root)]
    return (copies, []) if not escapes else ([], escapes)


def stamp(source, target):
    """Stamp the source payload into target; refuse drift and overwrites."""
    source, target = Path(source), Path(target)
    copies, problems = payload_copies(source, target)
    if problems:
        return problems
    clashes = [f"factory-init: target already has {dest.as_posix()}"
               for _, dest in copies if (target / dest).exists()]
    if clashes:
        return clashes
    for src, dest in copies:
        (target / dest).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target / dest)
    return []


# Factory-owned destinations: the executable payload plus the pristine
# mirror it is checked against. Detector E states the same split in
# manifest-key terms (gates.PRISTINE_PREFIXES); this states it in
# destination terms, and tests/test_factory_init.py pins the two together.
# Everything else the stamp lands is the product repo's to edit — budgets,
# the code-owner handle, the doc seeds — so update never writes over it.
FACTORY_OWNED = ("tools/factory/", ".github/workflows/", "factory/")


def is_factory_owned(dest):
    return dest.as_posix().startswith(FACTORY_OWNED)


def missing_make_targets(target):
    """Targets the stamped workflows call that the repo's Makefile lacks.

    update overwrites the workflows, and they name no commands of their own
    — every step goes through make. So a factory change that adds a target
    (wo-failed, ADR-0045) leaves a repo whose refreshed assembler.yml calls
    a target its Makefile has never heard of. Nothing else reports that
    until the workflow runs in anger.
    """
    makefile = target / "Makefile"
    if not makefile.is_file():
        return ["factory-init: target has no Makefile — the refreshed"
                " workflows have nothing to call"]
    defined = set(re.findall(r"(?m)^([a-z][a-z0-9-]*):",
                             makefile.read_text(encoding="utf-8")))
    workflows = target / ".github" / "workflows"
    called = set()
    for path in sorted(workflows.glob("*.yml")) if workflows.is_dir() else []:
        # comment lines describe the convention ("every step goes through a
        # `make` target") and would otherwise read as a call
        body = "\n".join(line for line in
                         path.read_text(encoding="utf-8").splitlines()
                         if not line.lstrip().startswith("#"))
        called.update(re.findall(r"\bmake\s+([a-z][a-z0-9-]*)", body))
    return [f"factory-init: workflows call `make {name}` but the Makefile"
            f" has no {name} target (add it, or re-stamp the Makefile)"
            for name in sorted(called - defined)]


def update(source, target):
    """Refresh an already-stamped repo: (written, kept, problems).

    stamp refuses every existing destination. That is right for a first
    stamp and leaves a stamped repo unable to take a factory fix — the
    detector E fix could not reach the repos it protects (issue #212).

    update splits the payload exactly where detector E does. The executable
    payload and the mirror are overwritten: they are never meant to be
    hand-edited, detector E fails the build if they are, and restoring from
    the mirror is already the documented remedy. Everything else is created
    only when absent — a seed that does not exist yet is safe to land, one
    that does is the repo's — and any kept file that differs from the
    payload is reported so the user can reconcile it deliberately.

    Refuses a tree that was never stamped rather than silently becoming a
    first stamp, which would land a payload nobody asked for.
    """
    source, target = Path(source), Path(target)
    copies, problems = payload_copies(source, target)
    if problems:
        return [], [], problems
    if not (target / "factory" / "manifest.json").is_file():
        return [], [], ["factory-init: target has no factory/manifest.json"
                        " — it was never stamped; run stamp, not update"]
    written, kept = [], []
    for src, dest in copies:
        path = target / dest
        if path.exists() and not is_factory_owned(dest):
            if path.read_bytes() != src.read_bytes():
                kept.append(dest.as_posix())
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, path)
        written.append(dest.as_posix())
    return written, sorted(kept), missing_make_targets(target)


def main(argv):
    root = Path(__file__).resolve().parent
    if argv == ["update-manifest"]:
        problems = update_manifest(root)
    elif len(argv) == 2 and argv[0] == "stamp":
        problems = stamp(root, Path(argv[1]))
    elif len(argv) == 2 and argv[0] == "update":
        written, kept, problems = update(root, Path(argv[1]))
        for rel in kept:
            print(f"factory-init: kept {rel} (yours — differs from the"
                  " payload, reconcile by hand if you want the change)")
        print(f"factory-init: refreshed {len(written)} file(s),"
              f" kept {len(kept)}")
    else:
        print(__doc__.strip())
        return 2
    for problem in problems:
        print(problem)
    print(f"factory-init: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
