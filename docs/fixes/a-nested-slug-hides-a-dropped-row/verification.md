---
stage: verify
run: maintenance:a-nested-slug-hides-a-dropped-row
date: 2026-08-28
assumptions: []
---

# Verification — a nested slug hides a dropped row

Every check below was run on this branch at the commit under review. The
regression pin is the centre of the run: six new tests in
`tests/test_lint.py`, each of which fails against `lint.py` as it was.

## 1. The defect reproduces against the code as it was

`lint.py` stashed, the new tests run against the old checkers.

```
FAIL: test_a_slug_nested_in_a_longer_one_still_needs_its_own_row TestLedger...
FAIL: test_every_registered_skill_can_be_reported_missing TestLedger... (slug='architect')
FAIL: test_every_registered_skill_can_be_reported_missing TestLedger... (slug='review')
FAIL: test_every_registered_skill_can_be_reported_missing TestLedger... (slug='architecture-diagram')
FAIL: test_prose_under_the_table_is_not_a_row TestLedger...
FAIL: test_a_slug_nested_in_a_longer_one_is_still_required TestReadmeSkills...
FAIL: test_every_registered_skill_can_be_reported_missing TestReadmeSkills... (slug='architect')
FAIL: test_every_registered_skill_can_be_reported_missing TestReadmeSkills... (slug='review')
FAIL: test_every_registered_skill_can_be_reported_missing TestReadmeSkills... (slug='architecture-diagram')
Ran 10 tests in 0.576s
FAILED (failures=9)
```

Nine failures, and the three slugs named are exactly the three the defect
brief predicted: the ones contained in a longer registered slug. They fail
by assertion, not by error.

**Result:** PASS

## 2. Every registered skill's ledger row is reportable

`TestLedger.test_every_registered_skill_can_be_reported_missing` drops each
slug's row in turn and asserts the checker names that slug. Twenty-four
subtests, no carve-outs.

```
Ran 10 tests in 0.326s

OK
```

Before the change three of those subtests failed; after it, none do. The
closure is what makes the pin non-vacuous — the two hand-picked tests could
each be satisfied by a checker that special-cases one slug, and this one
cannot.

**Result:** PASS

## 3. Every registered skill's README mention is reportable

`TestReadmeSkills.test_every_registered_skill_can_be_reported_missing`, the
same shape on the prose side. The whole-slug boundary is what carries it:

```
  names_slug('interactive-architecture-diagram'  , 'architecture-diagram') -> False
  names_slug('interactive-architecture-diagram'  , 'architect'           ) -> False
  names_slug('address-pr-review'                 , 'review'              ) -> False
  names_slug('- `architect`'                     , 'architect'           ) -> True
  names_slug('the architect stage'               , 'architect'           ) -> True
```

The last two rows are the half that matters as much as the first three: the
boundary must not turn the checker into one that only accepts backticked
names, because the README is prose and names skills both ways.

**Result:** PASS

## 4. Prose below the table is not a row

`TestLedger.test_prose_under_the_table_is_not_a_row` deletes `operate`'s
row and leaves a reading line naming the skill. The real LEDGER.md carries
several such paragraphs, so this is the file's actual shape, not a
contrivance.

```
FAIL: test_prose_under_the_table_is_not_a_row  (before)
OK                                             (after)
```

The row cell is now the only thing that counts, which is what the problem
string has always said.

**Result:** PASS

## 5. The pin is not vacuous on the real tree

A checker made stricter can pass its tests by reporting everything. Both
checkers still return nothing against this repo's own files:

```
check_ledger        -> []
check_readme_skills -> []
ledger_rows found   -> 24 rows
skills required     -> 24
```

Twenty-four rows for twenty-four registered skills — the table is complete
today, and the change reports no false problem against it.

**Result:** PASS

## 6. A row and a mention agree about what a slug is

`extra_skills` accepts any directory name under `skills/`, so the two
halves of the change have to accept the same names or a present row reads
as missing. Review caught them disagreeing about a leading digit; the
character classes now match, and a test holds them together.

```
  '| 3d-diagram |' -> NO ROWS          (before)
  '| 3d-diagram |' -> ['3d-diagram']   (after)
  names_slug('- `3d-diagram`', '3d-diagram') -> True   (both)
```

**Result:** PASS

## 7. The battery is green

```
=== unittest ===
Ran 1350 tests in 23.432s

OK
=== lint ===
lint: 0 problem(s) across 24 skills
=== gates ===
gates: 0 problem(s)
=== selftest ===
selftest: ok
=== one_owner ===
one-owner: 9 problem(s)
```

1344 on the base commit, 1350 here: the six new tests and nothing else.
`one_owner` is unchanged at 9, so the change created no second owner it can
see. `lint.py` is not in the payload mirror table, so no manifest
regeneration is owed and detector E agrees.

**Result:** PASS

## Not verified

- **The reverse direction.** Nothing checks that LEDGER.md lacks a row for
  a skill that no longer exists. That gap predates this run and is left
  open; the closure test's docstring says so rather than implying cover.
- **The payload's own copy.** There isn't one — `lint.py` is a root-only
  tool, so a stamped product repo runs no version of these checkers and
  there is nothing there to verify.
- **`check_ledger_links`.** Untouched, and it still reads the whole file
  on purpose: eval-evidence links live in row cells and in the reading
  below alike.
