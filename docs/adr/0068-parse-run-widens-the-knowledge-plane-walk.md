# parse_run widens the knowledge-plane walk (expand phase)

- Status: accepted
- Date: 2026-09-21

Amends ADR-0039's carve-out, restated from ADR-0037: `knowledge_plane`
concentrates LAYOUT knowledge — which directories are runs, where
breakdown.md lives — never general artifact parsing; "row and slice
grammar stay with each caller."

That carve-out held because nothing had observed a caller re-reading the
SAME artifact more than once. It no longer does. Every one of `gates.py`'s
ten `CHECKERS` is impure over the live filesystem, and two shapes of
duplication are real and measured, not anticipated:

- `knowledge_plane.breakdown_files` is walked independently by detector A
  (`check_wo_citation`), by `collect_wo_rows` (called separately from
  detector C's `check_link_integrity` and detector G's
  `check_cost_ledger`), and again by `merged_wo_rows` (also called from
  G). One `run_all` pass re-globs and re-reads every `breakdown.md` up to
  four times.
- `gates._scannable_files` — the shared markdown-tree walk C, D and I
  each check cross-links and tokens against — is re-globbed and every
  file's content re-read three times, once per detector.

This is the first of a three-step sequence (issue #441 expand, #442
migrate, #443 contract — #442 and #443 are separate, filed, currently
blocked issues; neither is touched here). Expand adds a read-once seam
ALONGSIDE the existing detectors, changing nothing about how any detector
reads the filesystem today; migrate later moves detectors onto it one at
a time; contract removes what migrate leaves unused. Doing this in one
step would touch ten detectors' behavior and their fixture-backed tests
in a single commit — the opposite of the surgical, verifiable-in-isolation
change this codebase's own review discipline asks for.

## Decision

`knowledge_plane.parse_run(root)` reads the run-level artifacts several
detectors duplicate, once, into a plain dict (no class: neither
`knowledge_plane.py` nor `gates.py` has a dataclass/NamedTuple precedent,
and every other accessor here already returns dicts and tuples). For each
`run_dirs(root)` entry it captures `breakdown.md`'s lines, `prd.md`'s
frontmatter `id`, `architecture.md`'s lines, and `verification.md`'s text
(or a decode error, mirroring `check_evidence_honesty`'s own
unreadable-file case) when each file is present; separately it captures
`docs/adr/NNNN-*.md`'s content and `docs/adr/README.md`'s lines, the
other walk C and D's blueprint checks share.

`parse_run` is additive and currently unused: no detector reads it, and
no detector's behavior, signature, or call path changes as part of this
decision. #442 wires detectors onto it.

**Deliberately left out of this first cut.** Detector E (the template
payload's byte hashes), F (`factory.json`, via `factory_config.py`), G's
ledger (`docs/factory/costs.jsonl`, via `cost_ledger.py`), J
(`.github/labels.json` + the Makefile, via `label_sync.py`) and B (the CI
event payload, via `cli.read_event`) each already read their own artifact
exactly once, through their own dedicated seam or single-pass function —
there is no cross-detector re-read to remove there, and folding them in
would be scope this issue's acceptance criteria do not ask for.
`gates._scannable_files` IS a real, observed duplication of the same
shape as `breakdown_files`', but it is `gates.py`-private policy (which
directories count as "scannable" is C/D/I's own shared choice, not run
layout) — folding it into `knowledge_plane` now would mean editing C/D/I's
own call sites, which the expand step keeps additive-only. #442 decides
then whether `_scannable_files` becomes knowledge-plane grammar too, or
`parse_run` takes an already-selected file list as a parameter.

## Consequences

- `knowledge_plane.py` is a `factory_init.MIRRORS` identity entry;
  `factory/manifest.json` and the payload copy under
  `factory/templates/tools/factory/knowledge_plane.py` are regenerated in
  this same commit (`python3 factory_init.py update-manifest`), matching
  the discipline detector E already pins.
- `parse_run` is tested through the SAME planted-defect fixture builders
  `gates.py` already has (`_wo_citation_defect_fixture`,
  `_link_integrity_defect_fixture`, `_evidence_honesty_defect_fixture`,
  `_clean_repo_fixture`, …) — issue #440's consolidated fixture surface —
  never a second, hand-typed tree.
- ADR-0039's own Status line and `docs/adr/README.md`'s index row for it
  now read "amended by ADR-0040 (roster further amended by ADR-0058; walk
  widened to `parse_run` by ADR-0068)".
- `#442` (migrate detectors onto `parse_run`, retiring the duplicated
  reads) and `#443` (contract: drop what migrate leaves unused) remain
  separately filed and blocked; nothing here unblocks or advances either.
