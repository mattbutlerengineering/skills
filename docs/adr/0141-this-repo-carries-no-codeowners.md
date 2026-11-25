# This repo carries no CODEOWNERS; the stamped one is authored

- Status: accepted
- Date: 2026-11-25

Supersedes ADR-0067 in part: the stamped file still names only the
placeholder owner, but it is no longer generated from a root twin.
Amends ADR-0050's MIRRORS table: `.github/CODEOWNERS` leaves it.

## Context

- ADR-0033's code-owner gate takes effect only when branch protection
  requires code-owner review. This repo's main has no branch protection
  and no ruleset (`docs/kb/main-unprotected.md`), so the root
  `.github/CODEOWNERS` enforced nothing. `docs/process-register.md`
  found no PR with a changes-requested review: no real catch.
- ADR-0135's sunset rule removes a process that protects nothing, and
  the Owner chose this one for the first wave on 2026-11-25 (#2361).
- The stamped copy is different. A product repo that turns on branch
  protection gets a working gate from it. ADR-0067 generated that copy
  from the root file through `product_codeowners`, so deleting the root
  would have deleted the consumer's gate too.

## Decision

- Delete the root `.github/CODEOWNERS`.
- `factory/templates/.github/CODEOWNERS` stays, byte for byte, as an
  authored payload file with no root twin. It leaves `factory_init.MIRRORS`,
  and `product_codeowners` and its header constant go with it.
  `update-manifest` still checksum-pins the file, and
  `tests/test_factory_init.py` pins that it names only the placeholder
  owner.
- Stamped repos are unchanged: the same file lands, with the same
  placeholder to substitute.

## Consequences

- This repo's merge gate is what it already was in practice: the
  independent review (ADR-0036) and the queue profile's `gate_paths`.
- Editing the stamped CODEOWNERS is a direct edit under
  `factory/templates/**` followed by `update-manifest`, not a root edit.
