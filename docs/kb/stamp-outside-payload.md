---
summary: factory-init stamps CODEOWNERS, the Makefile, factory.json, labels.json, seeded ADRs and design docs outside FACTORY_OWNED; update never refreshes them, and only doctor checks most.
sources: factory_init.py, factory_config.py, gates.py, skills/doctor/SKILL.md
verified: d178879624f898e06a6a052471e2f7fb33a366f0
related: manifest-regen
---

# What the stamp leaves outside the gated payload

`factory_init.FACTORY_OWNED` is `tools/factory/`, `.github/workflows/`
and `factory/`: the executable payload and the pristine mirror. Everything
else the stamp lands belongs to the product repo:

- `.github/CODEOWNERS`, written through `product_codeowners`
- the `Makefile`, written through `product_makefile`
- `.github/factory.json` (`INSTALL_MAP`, derived from
  `factory_config.ARTIFACT_HOMES`) and `.github/labels.json`
- seeded ADRs and design docs

A tools-only stamp (`stamp --tools-only`, ADR-0099) lands
`factory_init.TOOLS_ONLY_DESTINATIONS` — `tools/factory/` and
`.github/factory.json` — so of this set it writes `factory.json` alone:
no CODEOWNERS, Makefile, `labels.json` or seeds, and its manifest
carries `"install": "tools-only"`.

Consequences an agent gets wrong:

- **`factory_init.py update` never writes over these files**, whichever
  stamp kind: it refreshes `FACTORY_OWNED` destinations and anything
  absent, and keeps an existing file outside that set that differs from
  the payload (reported as `kept`). A fix to their templates does not
  reach an already-stamped repo, so `update` succeeding does not mean
  the Makefile or CODEOWNERS is current. On a tools-only target `update`
  refreshes only what its manifest lists and skips the make-target
  report below.
- **Few offline gates check them.** Detector F checks `factory.json`'s
  shape. Detector J (`gates.check_label_wiring`) checks `labels.json`:
  every label the tools and the Makefile name must still be in it, and
  an unreadable file is reported. Nothing offline checks the rest of
  this set. `doctor` is the reporter: its checks cover the Makefile's
  full target set and an unsubstituted CODEOWNERS (`@<owner>` still
  present), and on a tools-only target it declares those steps not
  applicable rather than reporting the files missing. `update` on a
  full stamp also reports make targets the stamped workflows call that
  the Makefile lacks (`factory_init.missing_make_targets`). Re-read
  doctor's steps rather than citing step numbers, because they move.

## Superseded

- 2026-10-11: "Detector F checks `factory.json`'s shape, and nothing
  else covers this set." Wrong when written: detector J also checks
  `labels.json`. Replaced by the "Few offline gates" claim above.
