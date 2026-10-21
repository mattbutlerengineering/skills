# The Decompose lessons file is a JSONL ledger of voted, sourced lessons, and decompose_lessons joins the root-only importers

- Status: provisional
- Date: 2026-10-20

Recorded by the `decompose-lessons` feature run
(`docs/features/decompose-lessons/`), unattended, so it is provisional.
It follows ADR-0110 and ADR-0112 for the dual-membership pin.

## Context

Step 3 of the Decompose learning loop (#988) keeps an ExpeL-style list of
lessons that the Decompose skill reads at draft time. Two things outlive
the commit that adds them: the file's on-disk shape, which every later
update and every skill read depends on, and the root-only to mirrored
import edges the tool adds. After ADR-0112 the pinned set is 50 pairs over
nine mirrored modules. `decompose_lessons.py` imports two mirrored
modules, `cli` (report, runner, guarded read) and `factory_config` (the
calibrate floor), and one root-only module, `decompose_signals`.

## Decision

- The file is `docs/factory/decompose-lessons.jsonl`, beside `costs.jsonl`.
  It is not markdown, so gates detectors C and I (which scan every repo
  markdown) never see it. Line 1 is `{"seen": [<run refs>]}`; every
  other line is one lesson `{"id", "importance", "text", "sources",
  "voted"}`, sorted by id.
- Lessons are derived only. The tool's single writer is `update`; there is
  no command that takes lesson text from a person.
- `decompose_lessons` is root-only (no payload tool imports it; a stamped
  repo has no learning loop). The set becomes 52 pairs: the `cli.py` row
  reads 22 root-only importers and the `factory_config.py` row gains
  `decompose_lessons`. `tests/test_dual_membership.py`'s pin carries the
  two new pairs. `factory.py`'s `VERBS` gains a `decompose-lessons` row.

## Rejected alternatives

- **A markdown lessons file**, which a human can read in the diff but which
  detectors C and I scan, fences included, so a quoted id in a lesson
  could fail the gates.
- **Free lesson text from a person or a model**, which is the shape ExpeL
  showed degrading on raw reflections, and which lets an unsourced lesson in.
- **Mirror into the payload.** No payload tool needs it.

## Consequences

- A format change means rewriting every line of an existing file, so it
  needs a new ADR that supersedes this one.
- The `seen` header is what stops a lesson dropped at 0 from being
  re-derived from the same runs; deleting it resurrects dropped lessons.
