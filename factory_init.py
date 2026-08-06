#!/usr/bin/env python3
"""factory-init: stamp the factory template payload into a product repo,
and regenerate the checksum manifest that pins it (PRD-0001; ADR-0032).

Conventions match lint.py/gates.py: functions return label-prefixed
problem strings; the CLI prints them and exits nonzero.

  update-manifest   refresh the mirrors (root tools, workflows,
                    CODEOWNERS, and the Makefile — see MIRRORS) from the
                    repo root into factory/templates/, writing each file
                    through its MIRRORS transform, then rewrite
                    factory/manifest.json (plugin name + version from
                    .claude-plugin/plugin.json, sha256 per template file —
                    hashed over the TRANSFORMED bytes that land in the
                    payload). Detector E pins the result: templates are
                    never hand-edited without re-running this.
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

import factory_config
import gates
from cli import report


def identity(text):
    """The verbatim MIRRORS transform: the payload twin is the root file,
    byte for byte."""
    return text


# The command spellings that differ between this repo and a stamped
# product repo: its factory tools live under tools/factory/, and its
# stamped test run is quiet.
_PRODUCT_TOOLS = ("gates.py", "validator.py", "assembler.py",
                  "cost_report.py", "gate_digest.py")


def product_form(command):
    """A root command as its product-repo twin spells it. The one
    production statement of the root<->payload command respelling:
    product_makefile generates the payload Makefile through it, and
    TestLockstep (tests/test_factory_gates.py) asserts both Makefiles'
    command sets against it — never a test-private copy."""
    for tool in _PRODUCT_TOOLS:
        command = command.replace(f"python3 {tool}",
                                  f"python3 tools/factory/{tool}")
    return command.replace("unittest discover tests",
                           "unittest discover -q tests")


# The product-repo Makefile's header comment, authored here because the
# two repos genuinely say different things about themselves; everything
# below it is generated from the root Makefile by product_makefile.
PRODUCT_MAKEFILE_HEADER = (
    "# Factory product-repo Makefile — stamped by factory-init"
    " (ADR-0032).\n"
    "#\n"
    "# `make check` is the canonical local gate and exactly what CI runs:"
    " the\n"
    "# stamped .github/workflows/validator.yml names no commands of its"
    " own, it\n"
    "# calls these targets. Same targets as the factory repo's own root"
    " Makefile\n"
    "# (its tools sit at the root, these under tools/factory/, and the"
    " plugin's\n"
    "# structural lint has no product-repo counterpart).\n")


def product_makefile(text):
    """The Makefile's MIRRORS transform: the root Makefile as its
    product-repo twin. Swap the root header comment for the product one,
    drop the plugin-only lint line (lint.py has no product-repo
    counterpart), and respell every command via product_form. Leans on
    the root Makefile's shape — an opening comment block ending at the
    first blank line — which the real-tree mirror test pins."""
    body = text.partition("\n\n")[2]
    body = body.replace("\tpython3 lint.py\n", "")
    return PRODUCT_MAKEFILE_HEADER + "\n" + product_form(body)


# Root files mirrored into the payload as (repo-root path, path under
# factory/templates/, transform) triples, so a stamped product repo runs
# the same tools and the same CI as this one — one source of truth, never
# a hand-maintained second copy. The transform is identity for every
# byte-for-byte mirror; the Makefile is the one twin that genuinely
# differs per repo, and product_makefile above is the whole translation —
# a new make target is a root-Makefile edit plus update-manifest, never a
# hand-sync. gates.py imports its sibling protocol; label_sync.py is the
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
# byte-for-byte instead of forked per repo. .github/CODEOWNERS is the
# human-gate surface (ADR-0033), identical in both repos, so it mirrors
# verbatim like the workflows.
MIRRORS = (
    ("gates.py", "tools/factory/gates.py", identity),
    ("protocol.py", "tools/factory/protocol.py", identity),
    ("knowledge_plane.py", "tools/factory/knowledge_plane.py", identity),
    ("cli.py", "tools/factory/cli.py", identity),
    ("factory_config.py", "tools/factory/factory_config.py", identity),
    ("cost_ledger.py", "tools/factory/cost_ledger.py", identity),
    ("label_sync.py", "tools/factory/label_sync.py", identity),
    ("validator.py", "tools/factory/validator.py", identity),
    ("assembler.py", "tools/factory/assembler.py", identity),
    ("budget_guard.py", "tools/factory/budget_guard.py", identity),
    ("handoff.py", "tools/factory/handoff.py", identity),
    ("orientation_pack.py", "tools/factory/orientation_pack.py", identity),
    ("cost_report.py", "tools/factory/cost_report.py", identity),
    ("gate_digest.py", "tools/factory/gate_digest.py", identity),
    (".github/workflows/validator.yml",
     ".github/workflows/validator.yml", identity),
    (".github/workflows/assembler.yml",
     ".github/workflows/assembler.yml", identity),
    (".github/workflows/design.yml",
     ".github/workflows/design.yml", identity),
    (".github/workflows/cost-report.yml",
     ".github/workflows/cost-report.yml", identity),
    (".github/workflows/gate-digest.yml",
     ".github/workflows/gate-digest.yml", identity),
    (".github/CODEOWNERS", ".github/CODEOWNERS", identity),
    ("Makefile", "Makefile", product_makefile),
)

# Manifest rel -> install destination; anything unmapped strips "templates/".
# Derived from the seam's installed-vs-payload grammar (ADR-0048), never a
# second spelling of it: an artifact whose payload home already mirrors its
# installed home (labels.json under templates/.github/) needs no entry —
# the strip rule below installs it — so only factory.json, at the payload
# root, maps.
INSTALL_MAP = {payload: installed for installed, payload
               in factory_config.ARTIFACT_HOMES.values()
               if payload != f"templates/{installed}"}


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
                 for name, _, _ in MIRRORS if not (root / name).is_file()]
    if problems:
        return problems
    meta = json.loads(plugin_meta.read_text(encoding="utf-8"))
    templates = root / "factory" / "templates"
    for name, rel, transform in MIRRORS:
        mirror = templates / rel
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_bytes(transform(
            (root / name).read_text(encoding="utf-8")).encode("utf-8"))
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
    return report("factory-init", problems)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
