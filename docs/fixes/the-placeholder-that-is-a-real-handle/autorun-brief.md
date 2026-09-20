---
run: maintenance:the-placeholder-that-is-a-real-handle
date: 2026-08-28
---

# Autorun brief

Maintenance run, autorun-driven, re-entry at Implement.

**Scale.** Maintenance (`docs/fixes/<slug>/`), scoped fix.

**Finding.** `factory_init.MIRRORS` mirrors `.github/CODEOWNERS` into the
template payload with the `identity` transform, so `factory-init stamp`
lands this repo's real code-owner handle in the target repo. Three
surfaces in the same repo — the seeded blueprint ADR, `gates.py`'s
`PRISTINE_PREFIXES` comment, and `factory_init.py`'s own `update` and
`FACTORY_OWNED` comments — all state that the stamp ships a *placeholder*
the product repo substitutes. Nothing in the stamped file is a
placeholder.

**Scope in.** The CODEOWNERS MIRRORS transform, its payload twin, the
manifest checksum it moves, and the tests that pin the mirror.

**Scope out.** The root `.github/CODEOWNERS` itself (correct for this
repo). `gates.py` and the seeded ADR text (both already state the
intended rule; they are the evidence, not the bug). No detector is added
— that is `gates.py`, contended by open PRs #320/#328.

**Release authorization.** None. Ship prepares and stops.

**Battery.** `python3 -m unittest discover tests`, `python3 lint.py`,
`python3 gates.py`, `python3 gates.py --selftest`, plus the free
`python3 one_owner.py` pre-pass.
