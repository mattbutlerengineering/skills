# Autorun brief: lean-and-polish

Collected 2026-10-10 from the owner's dispatch instructions. This brief is
not an artifact.

## Feature

Land two utility skills that were authored in this worktree around
2026-09-29 and left uncommitted: `lean` (the smallest thing that fully
works; cut-lists over a diff or a tree; a ledger of deliberate shortcuts)
and `polish` (take a built interface from working to considered; one named
move per pass; look at the rendered result). The owner preserved them
verbatim as WIP commit 18b5e10 on `feat/lean-and-polish-skills`:
`skills/lean/**`, `skills/polish/**`, the roster edits to `protocol.py`
and its payload mirror, `README.md`, `LEDGER.md`, `evals/routing.json`,
`.claude-plugin/plugin.json` and `factory/manifest.json`.

## Scale

Feature run, slug `lean-and-polish`, artifacts under
`docs/features/lean-and-polish/`. Why a feature run and not a maintenance
run: the protocol's tracker-intake rule says a missing capability is a
feature and routes it to `idea`, not `capture`; the two skills add
capability the plugin does not ship today, and every earlier new skill
(`launch-demo`, `pipeline-board`) landed as a feature run. The code
already exists, so the run is proportionate: short idea and PRD, a
paragraph-scale architecture, a three-row breakdown.

## Decided by the owner (2026-10-10)

- Land these two skills first, as one pull request, and stop there: no
  merge. They are the base for later runs on issues #624, #626 and #627;
  this run neither closes nor reference-closes any of them. A later gap
  analysis decides what those issues still need.
- Merge `origin/main` into the branch (it is 19 commits behind) and
  resolve the roster conflicts keeping both sides: `UTILITY_SKILLS` (and
  its payload mirror), the README utility table and the skill-map figure
  (`lean` and `polish` as literal `<text>` rows in the right card), the
  LEDGER rows (draft, no evidence), the routing-eval cases (never edit an
  existing case), the plugin version (0.4.0 on main, bump to 0.5.0), and
  the manifest via `python3 factory_init.py update-manifest`.
- Review both `SKILL.md` files against the conventions as they stand on
  main now (strict-YAML descriptions, Pi's 1024-character limit, harness
  neutrality, ADR-0023's utility-skill rules, references loaded at the
  step that needs them). Fix lint or gate failures; improve only what a
  convention requires.
- Battery: unit tests, `lint.py`, `gates.py` and its selftest. The paid
  routing eval (`trigger_eval.py`) is not run; it is owed.
- Ship: push the branch, open one plain anchor issue for the pull
  request's `Closes #N` (never #178, #181 or #624-#627), open one
  non-draft pull request to main, poll the checks, and stop.

## Tracker

One anchor issue, created at Ship. No work-order issues (no tracker
mirror, ADR-0026).

## Release authorization

None. Ship prepares the release (the pull request) and stops; the merge
is the owner's.
