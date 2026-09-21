---
stage: review
run: maintenance:nothing-notices-a-dropped-ledger-row
date: 2026-09-20
assumptions: []
---

# Review — nothing notices a dropped LEDGER.md row

Scope: the diff this run produced — `lint.py` (one new checker) and
`tests/test_lint.py` (six new tests). Nothing else was touched. The
battery was re-run after the change.

## Correctness

**1. (verified) Set difference, not substring.** `check_ledger_no_orphans`
computes `rows - known` over exact slugs from `ledger_rows`, the same
extraction `check_ledger` and #371 already established. Confirmed no
nested-slug false positive:
`test_a_row_nested_in_a_longer_registered_slug_is_not_an_orphan` carries
both `review` and `address-pr-review` rows in the clean tree and reports
neither.

**2. (verified) `extra_skills` is included in the trusted set, not just
`ALL_SKILLS`.** A skill directory added to `skills/` but not yet
registered in `protocol.py` is still "a skill" per `check_ledger`'s own
forward direction (`test_discovered_skill_needs_a_row_too`), so the
reverse direction has to accept the same set or a legitimately-new,
not-yet-registered skill's row would read as an orphan the moment it was
added — the opposite of what #371 fixed for the row/mention agreement.
`known = set(ALL_SKILLS) | set(extra_skills(root))` matches `check_ledger`
exactly.

**3. (verified) No double-reporting on a missing file.** `check_ledger`
already returns `["missing LEDGER.md"]` when the file is absent;
`check_ledger_no_orphans` returns `[]` in that case
(`test_missing_ledger_yields_no_problem_here`), matching the precedent
`check_ledger_links` set for the same file.

## Design

**4. (accepted) A separate checker, not folded into `check_ledger`.**
Mirrors `check_ledger_links` beside `check_ledger`: same file, different
fact, independent problem strings, independent CHECKERS entry. Keeps
`check_ledger`'s own docstring and behavior (forward direction only)
unchanged, so nothing about the existing, well-covered function had to be
touched or re-verified.

**5. (accepted) Row-scoped, not whole-file.** Deliberately mirrors
`check_ledger`'s own boundary rather than trying to also catch a retired
skill discussed in the reading notes below the table. That prose is where
a human explains *why* a row was dropped — flagging it as if it were a
live claim would be wrong, not thorough.

**6. (observation, follow-up) README.md's reverse direction is still
open.** Investigated and found to be a genuinely different shape — see
`defect.md`'s "Design question not resolved here" — rather than force a
heuristic (e.g. "every slug-shaped backtick token is a skill mention")
that already misfires on the real file (`` `claude` ``, the CLI tool,
under the on-demand commands section). Left for a human design call;
issue #455 stays open for this half and this run does not claim to close
it.

## Security

Nothing here reads untrusted input, writes outside the repo, spawns a
process, or touches a credential. The checker reads one file already in
the tree (`LEDGER.md`) and returns strings built from its own row
extraction and the trusted taxonomy — no external data reaches a regex or
a shell.

## Verdict

No criticals, no majors. One design question surfaced and deliberately
left unresolved (observation 6), documented rather than silently dropped.
Nothing here blocks shipping the LEDGER.md half.
