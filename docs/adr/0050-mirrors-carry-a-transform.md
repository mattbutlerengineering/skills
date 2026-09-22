# MIRRORS carries a transform: one authority per payload file

- Status: amended by ADR-0067
- Date: 2026-08-05

## Context

- `factory_init.MIRRORS` mirrored 19 root files verbatim into the
  template payload, sha256-pinned in `factory/manifest.json`; detector E
  gates manifest↔payload and the real-tree mirror test pins
  payload↔root. That half of the seam earns its keep — all 19 diffed
  with zero divergence.
- Two payload files were hand-authored twins outside it.
  `factory/templates/.github/CODEOWNERS` is a byte-identical copy of the
  root `.github/CODEOWNERS` pinned to it by nothing — edit the root and
  the payload stales silently. `factory/templates/Makefile` is a
  *translated* twin of the root `Makefile`, and the translation rule
  lived only in a test (TestLockstep's private `product_form`, six
  str.replace calls) — unavailable to production and to any stamped
  repo. A new make target meant edits in roughly five places.

## Decision

- MIRRORS entries are `(root path, template path, transform)` triples —
  plain data plus functions, no registry. The transform is `identity`
  for the 19 verbatim mirrors and for `.github/CODEOWNERS`, which joins
  the table; `product_makefile` — built on the production `product_form`
  command respeller — generates `factory/templates/Makefile` from the
  root Makefile (swap the header comment, drop the plugin-only lint
  line, respell tool paths and the quiet test run).
- `update-manifest` writes the TRANSFORMED content into the payload and
  hashes what it wrote, so manifest↔payload↔root stay consistent through
  one code path. Detector E's comparison is unchanged; what changed is
  that every twin it pins now has a generator.
- TestLockstep asserts against `factory_init.product_form`; the
  test-resident copy is deleted. The real-tree mirror test pins
  `payload == transform(root)` for every entry.
- The repo root stays flat and `product_form` stays the adapter at the
  root↔payload seam — this ADR gives that adapter a production home; it
  moves no files.

## Consequences

- Every payload file has exactly one authority: mirrored entries are
  generated from the root through their transform, and the remaining
  payload-only files (`factory.json`, `labels.json`, the design-doc
  templates) are authored in place — nothing is a hand-maintained twin.
- A new make target is a root-Makefile edit plus
  `python3 factory_init.py update-manifest`; a root CODEOWNERS edit can
  no longer stale the payload silently (the mirror pin fails CI).
- A transform must stay deterministic and total over its root file. The
  Makefile transform leans on the root Makefile opening with a comment
  block that ends at the first blank line; the real-tree pin is what
  catches that shape breaking.
