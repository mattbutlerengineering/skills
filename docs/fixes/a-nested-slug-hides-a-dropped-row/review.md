---
stage: review
run: maintenance:a-nested-slug-hides-a-dropped-row
date: 2026-08-28
assumptions: []
---

# Review — a nested slug hides a dropped row

Scope: the diff this run produced — `lint.py` (two checkers, one new
helper, one new pattern) and `tests/test_lint.py` (six tests). Nothing
else was touched. The battery was re-run after every finding that changed
code.

## Correctness

**1. (major, fixed) The two halves disagreed about what a slug is.**
`LEDGER_ROW` opened `[a-z]`; `names_slug` accepts anything not adjacent to
`[a-z0-9-]`. `extra_skills` imposes no shape on a directory name, so a
skill directory named `3d-diagram` would have its LEDGER row read as no
row at all and be reported missing while sitting in the table. Verified:
`ledger_rows("| 3d-diagram |")` returned the empty set while
`names_slug("- \`3d-diagram\`", "3d-diagram")` returned True. Fixed by
matching the character classes, and pinned by
`test_a_row_and_a_mention_agree_about_what_a_slug_is`.

**2. (minor, deferred) `LEDGER_ROW` anchors at column zero.** A table
indented up to three spaces is still a table in CommonMark, and would read
as zero rows: `ledger_rows("  | next |\n")` returns the empty set.
Deferred because the failure is loud — every skill reported missing at
once, which nobody ships past — and because widening the anchor invites
the opposite error, reading an indented code block's pipe table as ledger
rows. The real file has no indented rows; verified 24 of 24 match
`^\| [a-z]`.

**3. (minor, deferred) `names_slug` is case-sensitive.** A README naming a
skill only as "Architect" reports it missing. This is unchanged from the
substring test it replaces, so it is not a regression, and it is arguably
right: the taxonomy's slugs are lowercase and the checker asks for the
slug. Verified the current README names all 24 in lowercase, so nothing is
affected today.

## Design

**4. (minor, accepted) `names_slug` has one caller.** Ordinarily that
argues for inlining. It is kept as a named function because the fact it
owns — what counts as naming a skill — is the fact this defect was about,
and a second checker that needs exactly this test is already written on
another branch. Until that lands, it is a one-caller helper with its
reasoning attached, which is the cheaper of the two mistakes.

**5. (observation) The module now holds two slug shapes.**
`HANDOFF_LINE` matches `[a-z][a-z-]*` and the new `LEDGER_ROW` matches
`[a-z0-9][a-z0-9-]*`; they disagree about digits. They are local patterns
for different grammars rather than two copies of one fact, and
`one_owner.py` is unchanged at 9, so this is logged rather than fixed —
unifying them would change `check_router`'s behaviour, which this run has
no business touching.

**6. (observation, follow-up) The whole-slug hazard has a second author.**
A checker on another branch introduces its own slug-token regex for this
exact hazard, and names it in its docstring. When that lands, adopting
`names_slug` there is a one-line change and the alternative is two owners
of the same rule. Recorded as a backlog seed rather than done here, since
the code it would edit does not exist on this branch.

**7. (observation, follow-up) The reverse direction has no checker at
all.** Nothing reports a LEDGER row, or a README mention, for a skill that
no longer exists. That gap predates this run, and this run does not close
it — the closure test's docstring says so explicitly rather than letting
the reader assume cover.

## Security

Nothing here reads untrusted input, writes outside the repo, spawns a
process, or touches a credential. Both checkers read two files that are
already in the tree and return strings. `re.escape` is applied to the slug
before it enters the pattern in `names_slug`, so a directory name cannot
inject pattern syntax — the one place in this diff where external data
reaches a regex.

## Verdict

One major, fixed and pinned in the same change. Two minors and three
observations deferred with reasons above. No critical findings; nothing
blocks Ship.
