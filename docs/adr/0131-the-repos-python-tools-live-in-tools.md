# The repo's Python tools live in tools/, not at the root

- Status: provisional
- Date: 2026-11-17

Recorded from the Owner's request to reorganize the repo root to match
common conventions. It is provisional until the Owner confirms it. It
moves files and the paths that name them; it changes no tool's
behavior and no rule in an earlier ADR.

## Context

The repo root held 65 Python tools, two HTML templates and a stray
browser capture beside README.md, CLAUDE.md, CONTEXT.md, LEDGER.md and
the Makefile. 94 root entries made the project's own documents hard to
find. Every tool is a stdlib script that imports its siblings by bare
module name, and 32 of them import `cli.py`.

## Decision

1. **One directory.** All 65 `*.py` tools and the two HTML templates
   `assembly_line.py` and `dashboard.py` load (`assembly_line.html`,
   `dashboard.html`) move to `tools/`. Nothing else moves. The root
   keeps the documents, the Makefile, `package.json` and the existing
   directories.
2. **Flat imports stay.** A script's own directory leads its import
   path, so the bare-name imports resolve unchanged. Tests get the same
   path from `tests/__init__.py`, which `python3 -m unittest
   tests.<module>` (what `run_tests.py` spawns) runs first.
3. **The payload layout is untouched.** `factory_init.MIRRORS` keeps its
   destinations under `tools/factory/`; only its source names gain the
   `tools/` prefix. A stamped repo sees no change, and `product_form`
   still respells a root command into its payload twin.
4. **Tools that find the repo root** (`lint.py`, `factory_init.py`,
   `run_tests.py`, `trigger_eval.py`, `eval_trends.py`, `npx_bundle.py`)
   step up one directory. The factory-source probe in
   `conductor_merge.factory_source` looks for `tools/factory_init.py`.
5. **The vocabulary is kept.** Earlier ADRs, run artifacts and the
   dual-membership pin say "root-only" for a tool that `MIRRORS` does
   not ship. That still means not mirrored into the payload. Their
   wording is a record and is not rewritten.

## Alternatives considered

- **Family subdirectories** (`conductor/`, `kb/`, and so on). They would
  need a `sys.path` bootstrap in each moved file, and that boilerplate
  would ship byte-identical into the stamped payload. Rejected.
- **Leave the tools at the root and move only the stray files.** It does
  not reduce the 65-file clutter. Rejected.

## Consequences

- Every live invocation reads `python3 tools/<name>.py`: the Makefile,
  workflows, `.claude/` hooks and profile, skills and live docs.
  `docs/adr/**`, `docs/fixes/**`, `docs/features/**`, `docs/research/**`
  and `docs/launches/**` keep the root paths they were written with,
  except the lines detectors D and I check mechanically, which name the
  new path.
- Open branches cut before this change need a rebase that follows the
  renames (`git` tracks them as renames, so it usually applies cleanly).
