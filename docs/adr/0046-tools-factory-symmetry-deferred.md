# The tools/factory root symmetry is deferred — the flat root is load-bearing

- Status: accepted
- Date: 2026-08-05

## Context

The 2026-08-05 architecture review confirmed the desirable end state for
the repo root: the 14 mirrored factory tools living at `tools/factory/`
so the root layout equals the payload layout, `factory_init.MIRRORS`
collapsing to an identity map, and the Lockstep suite's `product_form`
string-rewriting adapter (which exists solely to translate root commands
into payload commands) getting deleted.

The move is blocked by one file. `protocol.py` belongs to both root
families at once: it is a `MIRRORS` entry consumed by the mirrored
factory tools (gates.py imports `read_frontmatter`), and it is the
ADR-0021 pipeline seam imported by three unmirrored pipeline tools
(lint.py, orientation.py, trigger_eval.py). Every cross-module import at
the root is a bare sibling import — there is no package, and standalone
stdlib execution (`python3 gates.py`) is a hard convention. Moving
`protocol.py` into `tools/factory/` breaks the pipeline tools' imports;
leaving it at the root breaks the identity map; a `sys.path` shim
forfeits stdlib-only standalone execution.

## Decision

Keep the flat root. Do not attempt the `tools/factory/` restructure
until a design resolves `protocol.py`'s dual membership (for example, by
splitting the frontmatter reader the factory tools need from the
pipeline taxonomy the plugin tools need — a split that must itself clear
the shared-module bar of multiple callers plus observed divergence).

## Consequences

- Future architecture reviews cite this ADR instead of re-deriving the
  dead end. The blocker is `protocol.py`'s dual membership, not the
  manifest, the Makefiles, or CI — those all migrate mechanically.
- Until then, the root↔payload path difference remains a real seam, and
  the Lockstep suite's `product_form` transform remains its adapter.
- The two root families stay interleaved; the mitigations are indexing
  and naming (the detector roster, the charters rename), not file moves.
