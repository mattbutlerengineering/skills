# CODEOWNERS mirrors through product_codeowners, not identity

- Status: accepted
- Date: 2026-09-21

Amends ADR-0050. Its Decision said "The transform is identity for the 19
verbatim mirrors and for `.github/CODEOWNERS`, which joins the table." PR
#354 (merged 2026-09-20) made that false: `.github/CODEOWNERS` now mirrors
through `product_codeowners`, not `identity`.

## Context

- Under `identity`, the stamped payload's `.github/CODEOWNERS` carried the
  literal `@mattbutlerengineering` handle as a target repo's code owner.
  GitHub silently ignores a CODEOWNERS entry naming a non-collaborator, so
  a stamped repo's merge gate was inert while its blueprint, `make check`,
  and `/doctor` all reported health.
- Six surfaces already promised a real placeholder before any transform
  delivered one: `factory/templates/docs/adr/0005-three-human-gates.md`,
  `gates.PRISTINE_PREFIXES`'s comment, `factory_init.py`'s `update`
  docstring and `FACTORY_OWNED` comment, `docs/setup.md`'s verify
  checklist, and `skills/doctor/SKILL.md` step 8.
- PR #354 added `product_codeowners` (`factory_init.py`): it swaps the
  header for `PRODUCT_CODEOWNERS_HEADER` and replaces every owner token
  with `OWNER_PLACEHOLDER` (`@<owner>`), then moved the
  `.github/CODEOWNERS` `MIRRORS` entry onto it. ADR-0050's Decision text
  was never updated to match.

## Decision

- ADR-0050's Decision is corrected by this amendment, not rewritten:
  `.github/CODEOWNERS` mirrors through `product_codeowners`, not
  `identity`. The 19 verbatim mirrors ADR-0050 also names are unaffected.

## Consequences

- No code changes: detector E and the real-tree mirror test already
  enforce `payload == transform(root)` for every `MIRRORS` entry,
  `.github/CODEOWNERS` included, and have done so since PR #354. This
  amendment brings ADR-0050's prose back in agreement with code that was
  already correct.
- Closes the blueprint-drift ADR-0050's prose carried (issue #450).
