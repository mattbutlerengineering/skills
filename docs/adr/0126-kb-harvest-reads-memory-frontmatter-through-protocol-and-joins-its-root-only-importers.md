# kb_harvest reads a memory file's frontmatter through protocol.frontmatter_end and joins the root-only importers of protocol.py

- Status: provisional
- Date: 2026-11-08

Recorded by the `kb-from-knowledge-work-plugins` feature run
(`docs/features/kb-from-knowledge-work-plugins/architecture.md`, issue
#1274), unattended, so it is provisional. Architect wrote it on a re-run
that resolved a design gap Implement stopped on. It follows ADR-0118 (one
owner of where frontmatter ends) and ADR-0110, ADR-0118 and ADR-0124 for
the `protocol.py` row of the dual-membership set ADR-0091 pinned.

## Context

The run's harvest reads auto-memory entries on `--memory`
(`kb_harvest.memory_type` and `memory_candidates`), and each entry's
`type`, `name` and `description` sit in a leading `---` frontmatter block.
Finding that block needs the fence rule. ADR-0118 gives the rule one owner,
`protocol.frontmatter_end`, and `tests/test_protocol_frontmatter.py`
(`TestOneFenceDefinition.test_the_exact_count_map`) fails on any second
definition in tracked Python. The run's first implementation defined the
fence again in a `_block` helper, because the architecture said
`kb_harvest.py` would import nothing beyond `cli`. Calling the owner means
importing `protocol`, which adds a root-only to mirrored pair that
`tests/test_dual_membership.py` pins.

Three ways out were on the table:

- **`kb_harvest` imports `protocol` and calls `frontmatter_end`.** One
  fence owner, one new pinned pair. `launch_demo` (ADR-0118) and
  `assembly_line` (ADR-0124) took this path.
- **`kb.py`, which already imports `protocol`, parses each memory file and
  passes the result in.** No new pair, but the page-contract module would
  read harness memory files, `memory_type(text)` and `memory_candidates`
  would change shape, and `protocol.parse_frontmatter` returns one value
  per key with the last one winning, so a file carrying both `type: user`
  and a nested `type: project` would read as `project`. The architecture's
  fail-safe rule (more than one distinct `type` value is skipped, so a
  user-scoped entry is never listed) needs every `type:` line in the
  block, so `kb_harvest` would still scan the block's lines itself.
- **Keep the copy and disguise the literal** (`"-" * 3`). It hides the
  second rule from the detector without removing it, which games the
  ADR-0118 gate.

## Decision

`kb_harvest` imports `protocol` and finds a memory file's frontmatter
block with `protocol.frontmatter_end(text.splitlines())`: the block is the
lines between the opener and the index it returns, and None means no
block, which `memory_type` and `memory_candidates` already treat as a skip.
`kb_harvest.py` defines no fence of its own. The architecture's
`memory_type(text)` and `memory_candidates` interfaces are unchanged.

The dual-membership set gains the pair `kb_harvest` to `protocol`, so
`tests/test_dual_membership.py`'s pin carries `kb_harvest` in its
`protocol.py` row. `kb_harvest` is root-only (not in
`factory_init.MIRRORS`), and `protocol` imports none of its callers, so the
edge adds no cycle and no payload or manifest change.

## Consequences

- A memory file now has frontmatter exactly when a run artifact does under
  ADR-0118: an opener indented by whitespace is no block, so that entry is
  skipped and counted rather than listed. The skip fails safe.
- `protocol.py` gains a tenth root-only importer. A future attempt at the
  tools/factory restructure (ADR-0091) has one more pair to account for.
- A change to the fence rule now also changes which memory entries harvest
  lists. That rule already needs a new ADR to change (ADR-0118).
