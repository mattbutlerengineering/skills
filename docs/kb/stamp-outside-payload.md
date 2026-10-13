---
summary: factory-init stamps CODEOWNERS, the Makefile, factory.json, labels.json, seeded ADRs and design docs outside FACTORY_OWNED; update never refreshes them, and only doctor checks most.
sources: factory_init.py, factory_config.py, gates.py, skills/doctor/SKILL.md
verified: 97507559df22791a05186404e7453a281b164bae
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

Consequences an agent gets wrong:

- **`factory_init.py update` never writes over these files.** A fix to
  their templates does not reach an already-stamped repo, so `update`
  succeeding does not mean the Makefile or CODEOWNERS is current.
- **Few offline gates check them.** Detector F checks `factory.json`'s
  shape. Detector J (`gates.check_label_wiring`) checks `labels.json`:
  every label the tools and the Makefile name must still be in it, and
  an unreadable file is reported. Nothing offline checks the rest of
  this set. `doctor` is the reporter: its checks cover the Makefile's
  full target set and an unsubstituted CODEOWNERS (`@<owner>` still
  present). Re-read doctor's steps rather than citing step numbers,
  because they move.

## Superseded

- 2026-10-11: "Detector F checks `factory.json`'s shape, and nothing
  else covers this set." Wrong when written: detector J also checks
  `labels.json`. Replaced by the "Few offline gates" claim above.
