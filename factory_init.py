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

import factory_config
import gates
from cli import report


def identity(text):
    """The verbatim MIRRORS transform: the payload twin is the root file,
    byte for byte."""
    return text


def product_form(command):
    """A root command as its product-repo twin spells it. The one
    production statement of the root<->payload command respelling:
    product_makefile generates the payload Makefile through it, and
    TestLockstep (tests/test_gates.py) asserts both Makefiles'
    command sets against it — never a test-private copy.

    Which files move is MIRRORS' fact, read here rather than restated: a
    hand-kept list of tools is a second copy of it, and the copy that
    falls behind emits a command naming a root-level file the stamped
    repo does not have. `"/" not in name` skips the workflows and
    CODEOWNERS, whose root spelling already carries their path; `rel !=
    name` skips the Makefile, whose payload home IS its root home. The
    replacement uses MIRRORS' own destination, so a tool mirrored
    somewhere other than tools/factory/ would follow it there. The
    remaining respelling is the stamped test run, which is quiet."""
    for name, rel, _ in MIRRORS:
        if "/" not in name and rel != name:
            command = command.replace(f"python3 {name}", f"python3 {rel}")
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
    "# stamped .github/workflows/validator.yml names no repo tool of its"
    " own, it\n"
    "# calls these targets (the gh and git plumbing around them stays in"
    " the\n"
    "# workflow). Same targets as the factory repo's own root Makefile"
    " — its\n"
    "# tools sit at the root, these under tools/factory/, and the"
    " plugin's\n"
    "# structural lint has no product-repo counterpart.\n")


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


# The stamped repo's code owner, as the payload spells it before anyone
# has substituted a real one. Deliberately not a legal GitHub login —
# angle brackets cannot appear in one — so the token can never resolve to
# an account someone registered, and GitHub reports it as a CODEOWNERS
# syntax error rather than ignoring one more unknown name in silence.
OWNER_PLACEHOLDER = "@<owner>"


# The product-repo CODEOWNERS header, authored here for the same reason
# PRODUCT_MAKEFILE_HEADER is: the root file's comment is true about this
# repo, and the stamped twin has to say something else. It names the
# three-human-gates decision instead of citing a number — the seed files
# that decision under its own numbering, and a bare token would point a
# stamped repo at an ADR it does not have.
PRODUCT_CODEOWNERS_HEADER = (
    "# Code owners — stamped by factory-init. SUBSTITUTE THE"
    " PLACEHOLDER:\n"
    f"# replace every `{OWNER_PLACEHOLDER}` below with a GitHub handle or"
    " team that is a\n"
    "# collaborator on THIS repo.\n"
    "#\n"
    "# Until you do, the merge gate is inert. Required code-owner"
    " review is what\n"
    "# makes the merged PR the approval record (the three-human-gates"
    " decision,\n"
    "# in docs/adr/). GitHub ignores a CODEOWNERS entry naming someone"
    " who is\n"
    "# not a collaborator here, and it does not tell you that it did.\n"
    "#\n"
    "# The explicit doc paths are the first two gates' surfaces; the"
    " fallback\n"
    "# keeps every merge owner-reviewed.\n")


# A CODEOWNERS owner: a whitespace-delimited token that STARTS with @.
# An email address is also a legal owner, and its local part must survive.
_OWNER_TOKEN = re.compile(r"(^|\s)@\S+", re.MULTILINE)


def product_codeowners(text):
    """CODEOWNERS' MIRRORS transform: the root file as its product-repo
    twin. Swap the root header comment for the product one, and rewrite
    every owner to OWNER_PLACEHOLDER.

    The root names THIS repo's owner. A stamped repo that inherits it has
    a merge gate GitHub silently ignores — the failure the seeded
    blueprint, docs/setup.md and doctor's step 8 all warn about, and the
    reason detector E leaves this file out of the pristine set. They all
    say the stamp ships a placeholder; this is what makes that true.

    Only the LEADING comment block is dropped — the root's header, the
    one part that is prose about this repo. A comment further down
    annotates a rule, and dropping it would lose the payload something
    the root said, silently. The block is found by walking comment lines
    from the top rather than partitioning on the first blank line the way
    product_makefile does, so a root file with no header, or one whose
    header stops using a blank line, still lands complete — ADR-0050
    names that dependence as the fragile part.
    """
    lines = text.splitlines()
    start = 0
    while start < len(lines) and lines[start].lstrip().startswith("#"):
        start += 1
    rules = _OWNER_TOKEN.sub(rf"\1{OWNER_PLACEHOLDER}",
                             "\n".join(lines[start:]))
    return PRODUCT_CODEOWNERS_HEADER + rules.strip("\n") + "\n"


# Root files mirrored into the payload as (repo-root path, path under
# factory/templates/, transform) triples, so a stamped product repo runs
# the same tools and the same CI as this one — one source of truth, never
# a hand-maintained second copy. The transform is identity for every
# byte-for-byte mirror; the Makefile and .github/CODEOWNERS are the two
# twins that genuinely differ per repo, and product_makefile and
# product_codeowners above are the whole translation — a new make target
# is a root-Makefile edit plus update-manifest, never a hand-sync.
# gates.py imports its sibling protocol; label_sync.py is the
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
# mirrored for the same reason protocol.py is. standards_index.py is the
# ADR-0073 seam gates.py's detector K imports (the normative-statement
# index's shape/parsing/regen), mirrored for the identical reason: the
# detector ships to every stamped repo, so its import must resolve
# there too. human_gates.py is the gate
# vocabulary and the stay partition (ADR-0056), and it ships for that same
# reason and not optionally: gate_digest.py and rejection_mining.py both
# ship and both import it as a bare sibling, so a stamped repo without it
# is a broken stamp. No Makefile target invokes it,
# so product_form never has occasion to respell it — but it would, since
# that respelling is derived from this table rather than from a second
# list that could fall behind it. validator.yml is
# path-agnostic (it runs `make` targets), which is what lets it be mirrored
# byte-for-byte instead of forked per repo. .github/CODEOWNERS is the
# human-gate surface (ADR-0033) and the one other twin that genuinely
# differs per repo: the root file names this repo's code owner, so it
# mirrors through product_codeowners, which swaps the header and blanks
# the owner to a placeholder the stamped repo substitutes.
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
    ("human_gates.py", "tools/factory/human_gates.py", identity),
    ("gate_digest.py", "tools/factory/gate_digest.py", identity),
    ("rejection_mining.py", "tools/factory/rejection_mining.py", identity),
    ("work_queue.py", "tools/factory/work_queue.py", identity),
    ("standards_index.py", "tools/factory/standards_index.py", identity),
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
    (".github/workflows/toolsmith-mine.yml",
     ".github/workflows/toolsmith-mine.yml", identity),
    (".github/CODEOWNERS",
     ".github/CODEOWNERS", product_codeowners),
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

    update overwrites the workflows, and they name no repo tool of their
    own — every tool invocation goes through make. So a factory change
    that adds a target
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
    return report("factory-init", problems)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
