---
stage: capture
run: maintenance:a-nested-slug-hides-a-dropped-row
date: 2026-08-28
re-entry: implement
assumptions:
  - The LEDGER row test reads the markdown table, because the problem string
    it already emits names a row and nothing else in the file is one.
  - The README test stays a prose test, because its own docstring says the
    README is prose and only asks that the skill be named.
---

# Defect: a nested slug hides a dropped row

## What is wrong

`lint.check_ledger` and `lint.check_readme_skills` each end with the same
line:

    for slug in ALL_SKILLS + extra_skills(root) if slug not in text

`slug not in text` is a substring test over the whole file. Two things
follow from it, and both are reachable in this repo today.

**A slug nested inside a longer slug can never be missing.** Four
containment pairs exist among the 24 registered skills:

    architect            in architecture-diagram
    architect            in interactive-architecture-diagram
    review               in address-pr-review
    architecture-diagram in interactive-architecture-diagram

So `architect`, `review` and `architecture-diagram` are each held up by a
longer sibling. Deleting any of their rows from LEDGER.md, or every mention
of them from README.md, leaves both checkers silent.

**A name in prose satisfies a claim about a row.** `check_ledger` reports
`LEDGER.md has no row for skill ...`, but the file it reads is a table
followed by several paragraphs of reading notes that name skills by slug.
A row deleted from the table while the reading below still mentions the
skill passes the check that says it did not.

## Why it matters

These two checkers exist because the failure they guard against already
happened: `check_readme_skills`'s docstring records that
`interactive-architecture-diagram` shipped undocumented, and the checker was
written so it could not happen again. The substring test means the guard is
blind for the shorter sibling of that very name — `architecture-diagram`
can be dropped from the README with no signal, which is the same class of
escape the checker was added to close.

LEDGER.md is also the maturity record the repo treats as load-bearing: a
skill graduates only via a real run, and the ledger is where that is
written down. A row that can vanish without a signal is a maturity claim
that can vanish without a signal.

## Reproduction

Against a copy of the tree holding only `LEDGER.md`, `README.md` and empty
`skills/*` directories, so nothing but the checker under test is involved.

```
=== leg 1: whole rows dropped from LEDGER.md ===
  drop row 'architect'                removed=1  -> SILENT
  drop row 'review'                   removed=1  -> SILENT
  drop row 'architecture-diagram'     removed=1  -> SILENT
  drop row 'audit'                    removed=1  -> ["LEDGER.md has no row for skill 'audit'"]

=== leg 2: names dropped from README.md ===
  drop name 'architect'                -> SILENT
  drop name 'review'                   -> SILENT
  drop name 'architecture-diagram'     -> SILENT
  drop name 'audit'                    -> ["README.md never names skill 'audit'"]

=== leg 3: LEDGER row deleted, name left only in the reading prose ===
  'autorun' still in prose: True
  check_ledger -> SILENT
```

`audit` is the control: a slug no other slug contains is caught in both
legs, so the checkers are not broken outright — they are blind exactly
where slugs nest.

## Breakdown

- [x] **1. Pin the three legs as failing tests.** A test per leg, asserting
      the exact problem string that should be produced and is not.
      *Acceptance*: three new tests fail against today's `lint.py` for the
      stated reason, not by error.
- [x] **2. Give the two checkers one owner for "does this text name this
      slug".** A whole-slug test, so a longer slug never satisfies a
      shorter one. *Acceptance*: legs 1 and 2 pass; `check_readme_skills`
      still reports on prose, unchanged in domain.
- [x] **3. Make `check_ledger` read the table it claims to read.**
      *Acceptance*: leg 3 passes; a row present in the table still passes
      whatever prose sits below it.
- [x] **4. Close the class in both directions for all 24 slugs.** A test
      that drops each registered skill in turn and asserts the checker
      names it. *Acceptance*: 24 slugs, 24 problem strings, no exceptions
      carved out.
- [x] **5. Battery green.** *Acceptance*: unittest OK, `lint: 0`,
      `gates: 0`, `selftest: ok`, `one-owner` no worse than 9.
