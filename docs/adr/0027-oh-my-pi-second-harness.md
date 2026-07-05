# oh-my-pi (omp) is a supported second harness; Claude Code stays primary

- Status: accepted
- Date: 2026-07-04
- Amends: ADR-0007

ADR-0007 confined Claude-Code-isms to the packaging layer so a future port to
opencode/pi would be cheap. That port is now realised for **oh-my-pi (omp)** —
the Pi-based terminal agent (`@oh-my-pi/pi-coding-agent`, `omp.sh`). The port
was as cheap as ADR-0007 promised:

- **Skill content is unchanged.** Bodies were already harness-neutral (ADR-0008)
  and lint-enforced; frontmatter (`name` ≤ 64 lowercase/hyphens, `description`
  ≤ 1024) already satisfies Pi's rules. omp's `task`/`todo`/`bash` tools cover
  the two neutral touchpoints (autorun's subagent dispatch, address-pr-review's
  PR tooling), and omp inherits `.claude` skills on first run.

## Decision

- **Dual-target, Claude Code primary.** Claude keeps the marketplace plugin, the
  `claude`-CLI evals, and the LEDGER as its maturity system of record. omp is a
  supported second harness, not a replacement.
- **Pi packaging = a root `package.json`.** omp discovers the skills through a
  `pi.skills` entry (`{ "pi": { "skills": ["./skills"] } }`, `private: true`,
  keyword `pi-package`). It carries no dependencies and no Node toolchain — a
  static discovery manifest in the packaging layer, so the stdlib-only rule for
  the Python scripts still holds. The `.claude-plugin/` manifests are untouched.
- **`lint.check_pi_package` guards it** the way `check_manifest` guards the Claude
  manifest, so the two packaging layers can't drift; lint also flags any
  description over Pi's 1024-char limit.

## Deferred

- **An omp eval driver.** `trigger_eval.py` stays Claude-only (it drives the
  `claude` CLI and parses its event stream). Triggering under omp is verified by
  a manual smoke test for now; LEDGER evidence remains Claude evals. A second
  adapter that runs the routing eval-set through the omp CLI is a future ADR.
