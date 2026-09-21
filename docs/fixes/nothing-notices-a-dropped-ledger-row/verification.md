---
stage: verify
run: maintenance:nothing-notices-a-dropped-ledger-row
date: 2026-09-20
assumptions: []
---

# Verification — nothing notices a dropped LEDGER.md row

Every check below was run on this branch at the commit under review.

## 1. The regression pin fails against the code as it was

`lint.py` reverted to `HEAD`, `tests/test_lint.py` kept at its new state:

```
ERROR: test_every_current_skill_stays_clean (tests.test_lint.TestLedgerNoOrphans...)
AttributeError: module 'lint' has no attribute 'check_ledger_no_orphans'
ERROR: test_missing_ledger_yields_no_problem_here (tests.test_lint.TestLedgerNoOrphans...)
AttributeError: module 'lint' has no attribute 'check_ledger_no_orphans'
ERROR: test_orphaned_row_is_reported (tests.test_lint.TestLedgerNoOrphans...)
AttributeError: module 'lint' has no attribute 'check_ledger_no_orphans'
ERROR: test_prose_mentioning_a_dropped_skill_is_not_a_row (tests.test_lint.TestLedgerNoOrphans...)
AttributeError: module 'lint' has no attribute 'check_ledger_no_orphans'
Ran 6 tests in 0.088s
FAILED (errors=5)
```

The one test that doesn't error
(`test_a_row_nested_in_a_longer_registered_slug_is_not_an_orphan`) calls
`lint.ledger_rows`, which already existed — it passes before and after,
which is expected: it is pinning a pre-existing fact (exact-slug row
extraction), not the new checker.

**Result:** PASS

## 2. The new checker fires on a planted orphan row

`TestLedgerNoOrphans.test_orphaned_row_is_reported` appends
`| retired-skill |` to the clean fixture's LEDGER.md:

```
lint.check_ledger_no_orphans(root) ==
  ["LEDGER.md has a row for skill 'retired-skill', which the taxonomy "
   "no longer registers"]
```

**Result:** PASS

## 3. The real repo's LEDGER.md stays clean

```
$ python3 -c "
from pathlib import Path
import lint
print(lint.check_ledger_no_orphans(Path('.')))
"
[]
```

Every row in the committed LEDGER.md names a currently registered skill.
Also covered by `TestCleanTree.test_every_checker_reports_zero_problems`,
which now walks `check_ledger_no_orphans` too since it is in `CHECKERS`.

**Result:** PASS

## 4. The row/prose boundary holds in reverse, mirroring #371

`test_prose_mentioning_a_dropped_skill_is_not_a_row` appends a reading
note mentioning `retired-skill` in prose, not a table row:

```
lint.check_ledger_no_orphans(root) == []
```

A dropped skill can still be discussed in the reading notes below the
table (an explicit "this was retired" line) without a stale row silently
implying it still has a maturity. This is the same row-vs-prose boundary
#371 pinned for the forward direction, held in reverse.

**Result:** PASS

## 5. Nested slugs don't produce false positives

`test_a_row_nested_in_a_longer_registered_slug_is_not_an_orphan`: the
clean tree carries both `review` and `address-pr-review` rows (`review`
is a substring of the other, registered slug). `ledger_rows` extracts
exact first-cell slugs, so neither is mistaken for an orphan of the
other:

```
lint.check_ledger_no_orphans(root) == []
'review' in lint.ledger_rows(ledger_text)  # True
```

**Result:** PASS

## 6. Missing LEDGER.md reports nothing new

`test_missing_ledger_yields_no_problem_here` deletes LEDGER.md from the
fixture tree:

```
lint.check_ledger_no_orphans(root) == []
```

`check_ledger` already reports `"missing LEDGER.md"`; a second checker
reporting the same absence would be the two-problems-one-file wart
`check_ledger_links` was written not to repeat.

**Result:** PASS

## 7. The design question for README.md is real, not assumed

The task brief asked to confirm, before implementing, whether README.md's
reverse direction is the same shape as LEDGER.md's. It is not — reversing
`check_readme_skills`'s whole-document substring search requires
inventing a "what counts as a skill mention" rule that does not exist
today, and the obvious candidate (every slug-shaped backticked token)
already misfires against the current, correct README:

```
$ python3 -c "
import re
text = open('README.md', encoding='utf-8').read()
for tok in sorted(set(re.findall(r'\`([a-z0-9][a-z0-9-]*)\`', text))):
    print(tok)
" | grep -v -f <(python3 -c "
import protocol
print('\n'.join(protocol.ALL_SKILLS))
")
claude
```

`` `claude` `` names the CLI tool ("needs the `claude` CLI"), not a
skill. This run does not implement a README.md checker on the strength of
that finding — see `defect.md`'s "Design question not resolved here."
Issue #455 is left open for this half; not claimed closed.

**Result:** PASS (as a documented, evidenced non-implementation — not a
verified fix, since none was attempted for this surface)

## 8. The battery is green

```
=== unittest ===
Ran 1623 tests in 20.413s

OK
=== lint ===
lint: 0 problem(s) across 24 skills
=== gates ===
gates: 0 problem(s)
=== selftest ===
selftest: ok
```

`one_owner.py` (advisory, not a gate) reports 7 problems, unchanged by
this diff — `check_ledger_no_orphans` reuses `ledger_rows`, `ALL_SKILLS`
and `extra_skills` rather than re-deriving any of them, so it creates no
new second owner.

**Result:** PASS

## Not verified

- **README.md's reverse direction.** Not implemented; see `defect.md`.
- **The payload's own copy.** There isn't one — `lint.py` is a root-only
  tool (confirmed: not in `factory_init.MIRRORS`), so no stamped product
  repo runs any version of these checkers.
- **`check_ledger_links`.** Untouched; it still reads the whole file for
  eval-evidence links, a different fact from row identity.
