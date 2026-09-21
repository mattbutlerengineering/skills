---
stage: review
run: maintenance:nothing-notices-a-dropped-readme-mention
date: 2026-09-20
assumptions: []
---

# Review — nothing notices a dropped README.md mention

Scope: the diff this run produced — `lint.py` (two new module-level
constants, one helper, one checker) and `tests/test_lint.py` (a fixture
change plus eight new tests). Nothing else was touched. The battery was
re-run after the change.

## Correctness

**1. (verified) Section-scoped, not whole-document.**
`readme_stage_mentions` searches only from `## Stages` to the next `## `
heading. `test_a_backtick_token_outside_the_section_is_not_scanned`
plants a `` `claude` ``-shaped mention outside that boundary and confirms
it is not reported — reproducing, inside the test suite, the exact false
positive the whole-document candidate has against the real file today.

**2. (verified) Exact tokens, not substrings.**
`SLUG_TOKEN` matches a full backtick-delimited span; a filename
(`` `idea.md` ``) or doc path (`` `docs/pipeline-protocol.md` ``) has a
dot or slash and never matches the `[a-z0-9][a-z0-9-]*` class, so those
are excluded without a separate rule.
`test_a_mention_nested_in_a_longer_registered_slug_is_not_an_orphan`
confirms `architect` and `architecture-diagram` — one a substring of the
other, both registered — are each read as their own token.

**3. (verified) `extra_skills` is in the trusted set, not just
`ALL_SKILLS`.** `known = set(ALL_SKILLS) | set(extra_skills(root))`
matches the set `check_ledger_no_orphans` and `check_readme_skills`
already use, so a legitimately new, not-yet-registered skill's mention
does not read as an orphan the moment someone documents it ahead of
`protocol.py`.

**4. (verified) No double-reporting on a missing file.**
`check_readme_skills` already returns `["missing README.md"]` when the
file is absent; `check_readme_no_orphans` returns `[]` in that case
(`test_missing_readme_yields_no_problem_here`), matching the precedent
`check_ledger_links` and `check_ledger_no_orphans` set for their file.

**5. (verified) A missing anchor fails loud, not silent.**
`check_readme_skills`'s forward direction doesn't depend on the
`## Stages` heading existing, so nothing else would notice it being
renamed or deleted out from under this checker.
`test_missing_stages_heading_is_reported` confirms that case produces its
own problem string rather than a false-clean `[]`.

## Design

**6. (accepted) A separate checker, not folded into
`check_readme_skills`.** Mirrors `check_ledger_no_orphans` beside
`check_ledger`: same file, different fact (mention vs. orphan), independent
problem strings, independent `CHECKERS` entry. `check_readme_skills`'s
own docstring and behavior (forward direction, whole document) are
unchanged.

**7. (accepted, the actual design call this run makes) Section-scoped,
not table-only or whole-document.** Issue #502 laid out three paths:
invent a new authoring convention, accept reduced recall by reading only
the structural table, or find another structural marker. This run found
one already implicit in README.md's own `## Stages` section — the table
and the utility-skill prose immediately below it are both part of the one
section whose entire job is enumerating what the plugin ships, introduced
by the same lead-in sentence. Reading that whole section (not just its
table) closes the prose-only utility-skill gap a table-only reading would
leave open, without re-introducing the whole-document false positive
(`` `claude` ``) — verified against the real file in `defect.md`, not
assumed.

**8. (flagged, accepted cost — documented per the brief's "make the
limitation loud" instruction) Reading prose, not just a table row, is a
real and different risk shape than `check_ledger_no_orphans`.** That
checker never leaves a table row; this one also reads free prose inside
its section boundary. A future edit that adds an unrelated slug-shaped
backtick token inside `## Stages` — one that doesn't name a skill — would
misfire as a false orphan. Named explicitly in `check_readme_no_orphans`'s
own docstring and in `defect.md`'s "What this still does not catch, on
purpose," not left implicit. Judged acceptable because: (a) the false
positive would surface on the very PR that introduces it, with a
one-line fix (reword, or drop the backticks); (b) the section's whole
purpose is naming skills, so the odds of an unrelated slug-shaped term
landing there are low; (c) the alternative (table-only) silently drops
exactly the coverage issue #502 was raised to get — a retired utility
skill's stale mention.

## Security

Nothing here reads untrusted input, writes outside the repo, spawns a
process, or touches a credential. The checker reads one file already in
the tree (`README.md`) and returns strings built from its own token
extraction and the trusted taxonomy — no external data reaches a regex or
a shell.

## Verdict

No criticals, no majors. One design call made and argued explicitly
(observation 7), with its accepted residual risk named rather than
buried (observation 8). Nothing here blocks shipping.
