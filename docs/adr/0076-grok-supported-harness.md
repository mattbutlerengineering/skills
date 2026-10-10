# Grok is a supported harness; Claude Code stays primary

- Status: accepted
- Date: 2026-10-08
- Amends: ADR-0027

ADR-0027 made the skills dual-target: Claude Code primary, oh-my-pi (omp)
a supported second harness, each with its own packaging. Grok reads
`.claude-plugin/` natively — `plugin.json`, `marketplace.json`, and a
`skills/` directory — so this port adds no third manifest. `grok plugin
validate` on this repo (2026-10-08) reports the existing manifest valid
and finds the `skills/` directory.

## Decision

- **Three harnesses, Claude Code primary.** Claude keeps the marketplace
  plugin, the `claude`-CLI evals, and the LEDGER as its maturity system
  of record. omp stays the supported second harness (ADR-0027), including
  its `package.json` `pi.skills` packaging and `lint.check_pi_package`.
  Grok is a supported harness on the same neutral skill bodies
  (ADR-0008).
- **Grok installs from the existing `.claude-plugin/` manifests.** A
  parallel `.grok-plugin/` tree was considered and left out: Grok reads
  `.claude-plugin/`, and a second file would be a second owner of the
  same install fact. `lint.check_grok_marketplace` pins the part
  `check_manifest` does not see: `marketplace.json` lists the plugin
  named in `plugin.json`, and that entry's source is a relative path
  inside the repo whose tree contains `skills/`. A plain string and
  `{"type": "local", "path": "..."}` both count, because Grok accepts
  both.
- **Invocation.** `/next` and the stage skills, the same names as Claude
  Code. When a name collides with a Grok built-in, the qualified form is
  `/idea-to-prod:<skill>`.

## Deferred

- **A Grok eval driver.** `trigger_eval.py` stays on claude and omp
  (`eval_schema.HARNESSES`). Triggering under Grok is the install plus
  `grok plugin validate` for now. LEDGER evidence remains Claude evals.
  An adapter that runs the routing eval-set through `grok -p` is a
  future ADR — the same deferral ADR-0027 made for omp, which ADR-0031
  later resolved.
