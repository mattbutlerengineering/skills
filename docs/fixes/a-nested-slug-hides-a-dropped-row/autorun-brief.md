# Autorun brief — a nested slug hides a dropped row

- **Scale**: maintenance run, slug `a-nested-slug-hides-a-dropped-row`.
- **Re-entry**: implement. The fix is two checkers in one module; no
  design question is open, so Architect has nothing to decide.
- **Problem**: `lint.check_ledger` and `lint.check_readme_skills` both ask
  `if slug not in text`. That is a substring test over the whole file, so a
  skill whose slug is contained in a longer slug can be deleted from
  LEDGER.md or README.md without either checker noticing.
- **Origin**: audit, while reading `lint.py` for the run-22 candidate. The
  hazard is named in the repo already — the `check_plugin_skills` docstring
  on `origin/agent/issue-323-plugin-description-drift` (PR #324) spells it
  out for the checker it adds, and leaves both older checkers as they were.
- **Scope in**: `lint.check_ledger`, `lint.check_readme_skills`, and their
  tests.
- **Scope out**: every other checker in `lint.py`; the LEDGER and README
  content itself, which is currently complete; `check_plugin_skills`, which
  does not exist on main.
- **Success**: dropping any single skill's LEDGER row or README mention
  produces a problem string naming that skill, for all 24 skills, and the
  battery stays green.
- **Tracker**: an intake issue is opened for the PR to close. No work order
  is minted — there is no breakdown row and this is not PRD scope.
- **Release authorization**: none. Ship prepares and stops.
