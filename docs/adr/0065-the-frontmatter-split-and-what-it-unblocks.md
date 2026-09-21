# The frontmatter split, and what it does and does not unblock

- Status: provisional
- Date: 2026-09-21

## Context

ADR-0046 (amended by ADR-0059) blocks the `tools/factory/` restructure —
moving the fourteen mirrored factory tools to the root so the layout
equals the payload layout, `factory_init.MIRRORS` collapsing to an
identity map, and the Lockstep suite's `product_form` string-rewriting
adapter going away — on `protocol.py`'s dual membership: it is a
`MIRRORS` entry the mirrored factory tools import (`gates.py` and
`assembler.py` both call `read_frontmatter`), and it is also the
ADR-0021 pipeline seam three unmirrored plugin tools import as a bare
sibling (`lint.py`, `trigger_eval.py`, and — ADR-0046's own citation is
stale here, see Consequences — not `orientation.py`, which does not
exist). Moving `protocol.py` breaks one side or the other; a `sys.path`
shim forfeits the stdlib-only standalone-execution convention every
root tool holds to.

`docs/fixes/deepening-cli-seams/architecture.md` (2026-08-13) measured
what the payload side of that dual membership actually uses:
`read_frontmatter` is 1 of `protocol.py`'s 15 exported names, called
from exactly two payload sites (`tools/factory/gates.py:73`,
`tools/factory/assembler.py:43`). The other ~250 lines — the
stage/skill taxonomy, the artifact table, the skill-file contract,
next-stage derivation — ship into every stamped repo behind that one
import and are never called there.

That is a smaller blocker than ADR-0046 names. `frontmatter.py` — one
function, one error contract (`None` for no frontmatter block; `{}` for
an empty one) — can be extracted from `protocol.py` as its own module.
`protocol.py` then imports it instead of defining it, and becomes a
consumer rather than one of the two families straddling the mirror
boundary.

**This does not unblock the restructure, and the reason is worth
recording rather than re-discovered.** The split alone keeps every
import a bare sibling in both trees: root `protocol.py` imports root
`frontmatter.py`; the mirrored tools import their mirrored
`frontmatter.py` next to them under `tools/factory/`. Nothing is shared
across the root/payload boundary yet — `factory_init.MIRRORS` pins
`templates/**`-to-root pairs (`manifest_files` walks
`factory/templates/**` only; `install_destination` requires the
`templates/` prefix), never a root-to-root pair. The restructure's
actual move — relocating the mirrored tools to `tools/factory/` at the
root, so the layouts match — is what would put root `frontmatter.py`
and payload `frontmatter.py` in the position of being the SAME file
content declared twice with no mechanical pin between them, which is
the root-to-root duplicate ADR-0046 is really asking about. That
question — may a `MIRRORS` entry pin a root↔root pair, the way
ADR-0050's transform machinery pins root↔payload pairs today — is
unanswered, and the split does not answer it. It only shrinks the
surface the eventual answer has to cover, from `protocol.py`'s 291
lines to `frontmatter.py`'s 42.

## Decision

**Amend ADR-0046: its blocker is narrowed from `protocol.py`'s dual
membership to `frontmatter.py`'s, once the split below lands — the
restructure itself stays blocked.** `MIRRORS` pins payload pairs only;
extending it to root pairs is a separate, still-open decision this ADR
does not make.

**The split itself is not performed by this ADR.** Extracting
`frontmatter.py` from `protocol.py`, updating both trees' imports, and
regenerating the mirrored payload and manifest is real implementation
work — sized, per `docs/fixes/deepening-cli-seams/architecture.md`'s
own Components section, as one module extraction plus a `MIRRORS`
identity entry — and is left for that work to actually do, not asserted
here as already done. This ADR records the decision and its
consequence so that work has a citable "why" when it happens, matching
this repo's ADR-first convention for a change that touches an accepted
decision.

## Consequences

- `docs/adr/0046-tools-factory-symmetry-deferred.md`'s Status line moves
  to record this narrowing without retiring ADR-0059's diagnosis, which
  still stands — see that file's edit in this same change.
- A future review that reaches for the `tools/factory/` restructure
  should read this ADR and find one blocker (`frontmatter.py`'s 42
  lines), not re-measure `protocol.py`'s 291 and re-derive the same
  question ADR-0046 already answered once.
- The root-to-root `MIRRORS` question stays genuinely open. Until it is
  answered, the split is worth doing on its own merits (roughly 250
  lines of unread pipeline taxonomy stop shipping into every stamped
  repo behind a single-function import) but does not, by itself, move
  the restructure forward.
- **Correction to ADR-0046's Context, recorded rather than silently
  fixed** (CLAUDE.md: never rewrite an old ADR): it names
  `orientation.py` as one of three pipeline importers of `protocol.py`.
  No such file exists in this repo; the third importer is
  `trigger_eval.py`. The reasoning and the decision both stand — only
  the citation was wrong.
