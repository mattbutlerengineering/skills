---
stage: architect
run: feature:lean-and-polish
date: 2026-10-10
ux: skipped — the deliverable is two skill instruction files; no flow or screen is designed
assumptions:
  - "No live trade-off read-out; the one decision that could have gone another way (which figure card) is recorded below with the option that lost. Taken without user input."
---

# Architecture: lean and polish

## Approach

Nothing new is designed. The two skills are utility skills (ADR-0023),
each a `skills/<slug>/SKILL.md` plus a `references/` directory read at the
step that needs it. They join the plugin the way every utility skill does:
one entry in `protocol.py` `UTILITY_SKILLS` (the living roster, ADR-0021)
and its payload mirror `factory/templates/tools/factory/protocol.py`
(checksum-pinned; `factory/manifest.json` regenerated), one LEDGER row at
draft, routing-eval cases, the plugin manifest's utility list, and the
two README surfaces `lint.py` pins — the utility table
(`check_readme_skills`) and the skill-map figure (`check_readme_figure`,
which reads only the figure's visible `<text>`).

## Decisions & alternatives

- **Card: "Reshaping what's built".** Both skills act on something that
  already exists — `lean` cuts a diff or tree, `polish` takes a built
  interface the last step — beside `deepen`, which asks the same kind of
  question about module shape. The readme-skill-map run's backlog seed
  named this card for both. Lost: "Before a run exists" (`lean`'s ladder
  also runs before building, but its cut-list and debt modes do not),
  and a new seventh card (one more box for two rows; the figure's grid
  has no free slot on the left column).
- **Figure geometry.** The card grows from 48 to 80 units tall, two
  16-unit rows, keeping its last baseline 10 units above the card edge as
  the other cards do; the "Around a pull request" card below starts at
  380, so 28 units of gap remain. No other element moves.
- **Version 0.5.0.** `skills/` changes, so the installed plugin cache
  needs a new version to refresh (a stale cache is silent).

## Interfaces touched

`protocol.py` (and mirror), `.claude-plugin/plugin.json`,
`factory/manifest.json`, `README.md`, `docs/assets/skill-map.svg`,
`LEDGER.md`, `evals/routing.json`, `docs/backlog.md` (seed claim), and
`skills/lean/**`, `skills/polish/**`.
