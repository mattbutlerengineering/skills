---
stage: verify
run: maintenance:nothing-notices-a-dropped-readme-mention
date: 2026-09-20
assumptions: []
---

# Verification — nothing notices a dropped README.md mention

Every check below was run on this branch at the commit under review.

## 1. The regression pin fails against the code as it was

`lint.py` reverted to the branch point, `tests/test_lint.py` kept at its
new state (`TestReadmeNoOrphans`, plus the `## Stages` heading added to
`make_clean_tree`'s README fixture):

```
ERROR: test_a_backtick_token_outside_the_section_is_not_scanned (tests.test_lint.TestReadmeNoOrphans...)
AttributeError: module 'lint' has no attribute 'check_readme_no_orphans'
ERROR: test_a_mention_nested_in_a_longer_registered_slug_is_not_an_orphan (tests.test_lint.TestReadmeNoOrphans...)
AttributeError: module 'lint' has no attribute 'check_readme_no_orphans'
ERROR: test_a_prose_only_utility_mention_is_reported (tests.test_lint.TestReadmeNoOrphans...)
AttributeError: module 'lint' has no attribute 'check_readme_no_orphans'
ERROR: test_an_orphaned_table_mention_is_reported (tests.test_lint.TestReadmeNoOrphans...)
AttributeError: module 'lint' has no attribute 'check_readme_no_orphans'
ERROR: test_every_current_mention_stays_clean (tests.test_lint.TestReadmeNoOrphans...)
AttributeError: module 'lint' has no attribute 'check_readme_no_orphans'
ERROR: test_missing_readme_yields_no_problem_here (tests.test_lint.TestReadmeNoOrphans...)
AttributeError: module 'lint' has no attribute 'check_readme_no_orphans'
ERROR: test_missing_stages_heading_is_reported (tests.test_lint.TestReadmeNoOrphans...)
AttributeError: module 'lint' has no attribute 'check_readme_no_orphans'
Ran 8 tests in 0.082s
FAILED (errors=7)
```

The one test that doesn't error
(`test_bytes_that_are_not_utf8_are_a_problem_not_a_crash`, inherited from
`CheckerTreeTest`) exercises `check_manifest`, not the new checker — it
passes before and after, as expected.

**Result:** PASS

## 2. The new checker fires on a planted orphan — table row and prose

`test_an_orphaned_table_mention_is_reported` appends a `- \`retired-skill\``
bullet to the clean fixture's README:

```
lint.check_readme_no_orphans(root) ==
  ["README.md's '## Stages' section names 'retired-skill', which the "
   "taxonomy no longer registers"]
```

`test_a_prose_only_utility_mention_is_reported` plants the harder case
instead — a sentence with no table row at all, the shape a retired
*utility* skill's stale mention would actually take (ADR-0023: utility
skills are documented only in this section's prose):

```
lint.check_readme_no_orphans(root) ==
  ["README.md's '## Stages' section names 'retired-utility', which the "
   "taxonomy no longer registers"]
```

**Result:** PASS

## 3. The real repo's README.md stays clean

```
$ python3 -c "
from pathlib import Path
import lint
print(lint.check_readme_no_orphans(Path('.')))
"
[]
```

Every slug-shaped backtick token inside the real README's `## Stages`
section names a currently registered skill. Also covered by
`TestCleanTree.test_every_checker_reports_zero_problems`, which now walks
`check_readme_no_orphans` too since it is in `CHECKERS`.

**Result:** PASS

## 4. The section boundary excludes the known false positive

`test_a_backtick_token_outside_the_section_is_not_scanned` plants a
`` `claude` `` mention — the real, current false positive
`nothing-notices-a-dropped-ledger-row/defect.md` found for the rejected
whole-document candidate — inside a planted `## Development` heading,
outside `## Stages`:

```
lint.check_readme_no_orphans(root) == []
```

Confirmed directly against the real file too (see `defect.md`): scoping
the same slug-shaped-backtick-token scan to `## Stages` alone produces
zero exceptions against the real, correct README, where scanning the
whole document produces one (`claude`).

**Result:** PASS

## 5. Nested slugs don't produce false positives

`test_a_mention_nested_in_a_longer_registered_slug_is_not_an_orphan`: the
clean tree's README carries both `architect` and `architecture-diagram`
mentions (`architect` is a substring of the other, registered slug).
`readme_stage_mentions` reads exact backtick tokens (`SLUG_TOKEN`), not
substrings, so neither is mistaken for an orphan of the other:

```
lint.check_readme_no_orphans(root) == []
'architect' in lint.readme_stage_mentions(readme_text)  # True
```

**Result:** PASS

## 6. A missing or renamed heading is reported, not silently skipped

`test_missing_stages_heading_is_reported` deletes the `## Stages` line
from the fixture README:

```
lint.check_readme_no_orphans(root) ==
  ["README.md has no '## Stages' section — it is where "
   "check_readme_no_orphans reads which skills are currently claimed"]
```

`check_readme_skills`'s forward direction never depended on this heading
(it searches the whole document), so without this problem string a
renamed or deleted heading would silently stop the reverse check from
reading anything, with nothing else noticing.

**Result:** PASS

## 7. Missing README.md reports nothing new here

`test_missing_readme_yields_no_problem_here` deletes README.md from the
fixture tree:

```
lint.check_readme_no_orphans(root) == []
```

`check_readme_skills` already reports `"missing README.md"`; a second
checker reporting the same absence would be the two-problems-one-file
wart `check_ledger_links` was written not to repeat, mirrored here for
README.md.

**Result:** PASS

## 8. The battery is green

```
=== unittest ===
Ran 1625 tests in 20.237s

OK
=== lint ===
lint: 0 problem(s) across 24 skills
=== gates ===
gates: 0 problem(s)
=== selftest ===
selftest: ok
```

`one_owner.py` (advisory, not a gate) reports 7 problems, none touching
`lint.py`, `readme_stage_mentions`, or `check_readme_no_orphans` —
unchanged by this diff. The new checker reuses `ALL_SKILLS`,
`extra_skills` and the same `[a-z0-9][a-z0-9-]*` slug character class
`names_slug` already owns, rather than re-deriving any of them, so it
creates no new second owner.

**Result:** PASS

## Not verified

- **Mentions outside `## Stages`.** Not this checker's scope, by design
  — see `defect.md`'s "What this still does not catch, on purpose."
- **The payload's own copy.** There isn't one — `lint.py` is a root-only
  tool (confirmed: not in `factory_init.MIRRORS`), so no stamped product
  repo runs any version of these checkers.
- **A future non-skill, slug-shaped backtick token added inside
  `## Stages`.** Would read as a false orphan; accepted, documented risk,
  not something this run can verify against a case that doesn't exist
  yet.
