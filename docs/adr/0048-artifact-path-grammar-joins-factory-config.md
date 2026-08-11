# The installed-vs-payload path grammar joins factory_config

- Status: accepted
- Date: 2026-08-05

## Context

Where a dual-home factory artifact lives — installed once stamped, or in
the template payload — is repo-layout grammar, and it had four homes in
three shapes, already drifted:

- `factory_config.load` hardcoded `(.github/factory.json,
  factory/templates/factory.json)` — installed first, first hit wins.
- `label_sync.load_labels` hardcoded the same order for labels.json,
  with an extra `.github/` payload segment its own reader carried.
- `gates.check_config_shape` (detector F) hardcoded the factory.json
  pair payload FIRST and checked BOTH candidates.
- `factory_init.INSTALL_MAP` spelled the same fact a fourth way:
  `{"templates/factory.json": ".github/factory.json"}`.

Three observed divergences: (a) the `.github/` asymmetry — factory.json
at the payload root, labels.json under `templates/.github/` — restated
per reader; (b) candidate ORDER inverted between `factory_config.load`
and detector F; (c) first-hit semantics in the runtime readers against
check-both in the gate. Add a candidate home under that arrangement and
the runtime reads it while CI does not gate it, or vice versa. The
routing-band vocabulary had the same disease in miniature: the tuple
`("mechanical", "implementation", "architecture_review")` lived
literally in gates' `CONFIG_ROUTES` and test_model_routing's `ROUTES`,
while `factory_config.resolve_model` — the seam that resolves bands —
took band as an opaque string.

## Decision

`factory_config` owns both vocabularies, beside the accessors that
resolve over them (same fold pattern as ADR-0039/0040/0042):

- `ARTIFACT_HOMES` + `artifact_paths(root, name)` — each dual-home
  artifact's ordered candidates, `((installed, True), (payload,
  False))`, installed first. The `.github/` asymmetry, the payload
  prefix, and the read order are stated once. `load` and
  `label_sync.load_labels` take the first existing candidate (their
  missing-artifact messages now derive from the same candidates);
  detector F iterates every candidate, keeping its check-both
  semantics; `factory_init.INSTALL_MAP` is derived — an artifact whose
  payload home already mirrors its installed home needs no entry, so
  only factory.json maps.
- `BANDS` — the legal routing bands. Gates' `CONFIG_ROUTES` literal is
  retired in its favour, and test_model_routing's `ROUTES` reads it.
  `resolve_model` is unchanged: it already fails closed per lookup with
  a pinned problem string, so no second membership check was added.

One divergence is retained deliberately: detector F still REPORTS
payload-first — its problem output and order are pinned by tests — the
inverse of the seam's installed-first read order. The retained
difference is the order of report lines, never which files are checked,
and F's code now says so where it reverses the seam's candidates.

## Consequences

- A new candidate home lands in the runtime readers, the CI gate, and
  the stamp map together, or not at all — the drift class where the
  runtime reads a path CI does not gate is retired.
- Problem strings are byte-identical to before at every converted call
  site; the missing-artifact messages can no longer drift from the
  candidate list they enumerate.
- The stamp's strip rule stays with `factory_init.install_path`: the
  seam states where artifacts live, the stamp owns how they move.
