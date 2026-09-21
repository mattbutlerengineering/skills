# The tracker-mirror grammar joins the knowledge plane

- Status: amended by ADR-0040 (roster further amended by ADR-0058; walk widened to parse_run by ADR-0067)
- Date: 2026-07-21

Amends ADR-0037. Its final carve-out read: "The ROW/TRACKER breakdown-row
regexes remain per-file (assembler.py, orientation_pack.py, validator.py)
— same grammar, but each file reads a different slice through it; fold
them into knowledge_plane only when a real divergence is observed."

Two things have overtaken that text:

- **ROW no longer lives per-file.** The round-4 architecture review moved
  the row grammar to `knowledge_plane.ROW`, with `row_work_order` and
  `breakdown_files` serving every reader — and orientation_pack now owns
  neither regex. The carve-out's rationale ("each file reads a different
  slice") was disproven in practice: a shared accessor serves callers
  that slice differently just fine. The slice logic stayed with the
  callers; only the grammar moved.
- **TRACKER was left half-folded.** `assembler.py` and `validator.py`
  still each define the byte-identical `\(tracker:\s*#(\d+)\)` regex for
  the two directions of the WO↔issue mirror (issue#→row, row→issue#),
  with no pin holding the copies equal.

## Decision

`knowledge_plane` owns the tracker-mirror grammar: a
`row_tracker_issue(line)` accessor — sibling of `row_work_order` —
returns the issue number a breakdown row mirrors to, or None. The
assembler and the validator consume it and keep their own lookup
directions and problem strings, exactly as they kept their slice logic
when ROW moved.

The divergence trigger ADR-0037 set for this fold never fired; the fold
is authorized on **completed locality** instead — one row grammar, one
home, matching the accessor pattern the plane already uses — because the
carve-out's stated rationale no longer describes the tree. The rest of
ADR-0037 (seam-module bar, problem-string convention, the
`write_outputs` wart, checkbox-regex owners) stands unchanged.

## Consequences

- The tracker regex can no longer drift between the dispatch direction
  and the lifecycle direction of the mirror.
- ADR-0037's carve-out list should be read through this amendment: ROW
  and TRACKER are knowledge-plane grammar; only the three
  checkbox-regex owners (knowledge_plane.ROW / protocol._CHECKBOX /
  gates.MERGED_ROW) remain deliberately separate.
