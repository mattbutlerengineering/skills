---
stage: verify
run: maintenance:one-owner-for-copied-skill-text
date: 2026-10-25
---

# Verification: copied skill text with no owner

## Summary

6 PASS, 0 FAIL, 1 NOT RUN. Every work item's acceptance criterion holds
on HEAD: the regression test was red on origin/main's skill text (18
failures across 5 tests), is green on the fixed text, and catches a copy
pasted back; all four repo checks are clean. The one NOT RUN is live
agent behaviour reading the moved text (no paid model run); the moves
are text-ownership only, so this verdict is about the text, not about a
model's reading of it.

## Criteria & evidence

### Regression test fails on the current text before any move

- Check: `skills/` from `origin/main` (f905d53) extracted with
  `git archive origin/main skills` into a scratch tree, the new
  `tests/test_skill_shared_references.py` copied beside it, and the test
  module run there (the test resolves files from its own location).
- Evidence:
  ```
  FAIL: test_each_cited_owner_ships (passage='recon')
  FAIL: test_each_cited_owner_ships (passage='routing ladder')
  FAIL: test_each_consumer_cites_its_owner (passage='recon', consumer='skills/audit/SKILL.md')
  FAIL: test_each_consumer_cites_its_owner (passage='recon', consumer='skills/automate/SKILL.md')
  FAIL: test_each_consumer_cites_its_owner (passage='routing ladder', consumer='skills/audit/SKILL.md')
  FAIL: test_each_consumer_cites_its_owner (passage='routing ladder', consumer='skills/automate/SKILL.md')
  FAIL: test_each_consumer_cites_its_owner (passage='dark diagram palette', consumer='skills/interactive-architecture-diagram/references/design-system.md')
  FAIL: test_each_sentence_occurs_once_and_in_its_owner (passage='recon', sentence='dropping every entry that carries a `pull_request` key')
  FAIL: test_each_sentence_occurs_once_and_in_its_owner (passage='recon', sentence='is a duplicate of work in flight')
  FAIL: test_each_sentence_occurs_once_and_in_its_owner (passage='recon', sentence='gh issue list --state open --limit 50')
  FAIL: test_each_sentence_occurs_once_and_in_its_owner (passage='routing ladder', sentence='the default for anything worth remembering and not worth a run today')
  FAIL: test_each_sentence_occurs_once_and_in_its_owner (passage='routing ladder', sentence='the dedupe happens before the write, not after')
  FAIL: test_each_sentence_occurs_once_and_in_its_owner (passage='dark diagram palette', sentence='| storage | cache / object / block store | `#39c5cf` | `rgba(57,197,207,0.10)` |')
  FAIL: test_each_sentence_occurs_once_and_in_its_owner (passage='dark diagram palette', sentence='| node surface (mask) | `#161b22` |')
  FAIL: test_each_sentence_occurs_once_and_in_its_owner (passage='dark diagram palette', sentence='the fill is a hint')
  FAIL: test_no_keep_in_step_instruction_survives (file='skills/animated-diagram/references/design-system.md')
  FAIL: test_no_keep_in_step_instruction_survives (file='skills/interactive-architecture-diagram/references/design-system.md')
  FAIL: test_step_four_items_number_one_to_n
  Ran 5 tests in 0.010s
  FAILED (failures=18)
  ```
  The same 18 failures were seen in this worktree before the moves, at
  commit 4d9f2ec.
- Result: PASS

### The test catches a copy pasted back

- Check: HEAD's `skills/` extracted into a second scratch tree, and the
  REST fallback's last clause appended to `skills/automate/SKILL.md`,
  wrapped at a different column from the owner's copy; test run there.
- Evidence:
  ```
  FAIL: test_each_sentence_occurs_once_and_in_its_owner (passage='recon', sentence='dropping every entry that carries a `pull_request` key')
   : recon: 'dropping every entry that carries a `pull_request` key' counted {'skills/audit/references/recon.md': 1, 'skills/audit/SKILL.md': 0, 'skills/automate/SKILL.md': 1}
  Ran 5 tests in 0.005s
  FAILED (failures=1)
  ```
- Result: PASS

### audit/automate recon and routing have one owner each

- Check: the recon and routing cases of the regression test on HEAD,
  run as part of the full suite below; `python3 lint.py` resolves
  automate's backticked `../audit/references/*.md` sibling references
  (`lint.SIBLING_ASSET`) and audit's markdown links.
- Evidence:
  ```
  $ python3 -m unittest tests.test_skill_shared_references
  Ran 5 tests in 0.004s

  OK
  $ python3 lint.py
  lint: 0 problem(s) across 35 skills
  ```
- Result: PASS

### Diagram dark palette has one owner and no keep-in-step instruction

- Check: the palette and keep-in-step cases of the test (green above),
  plus a direct search of both dark design-system files.
- Evidence:
  ```
  $ grep -rn "match it in the other" skills/animated-diagram/references/design-system.md skills/interactive-architecture-diagram/references/design-system.md
  grep exit=1
  ```
- Result: PASS

### work-queue step 4 numbers 1–9 and nothing cites an old number

- Check: `test_step_four_items_number_one_to_n` (green above); search
  the skill and the protocol for item or step-4 citations.
- Evidence:
  ```
  $ grep -rnE "item [0-9]+|step 4\.[0-9]|step-4" skills/work-queue/ docs/pipeline-protocol.md
  skills/work-queue/SKILL.md:91:   (`../../docs/pipeline-protocol.md`), with item 2's `Closes #N` line
  ```
  Item 2 is unchanged by the renumbering.
- Result: PASS

### All four repo checks are clean

- Check: the four CI verify commands from `CLAUDE.md`, on HEAD.
- Evidence:
  ```
  $ python3 run_tests.py
  tests: 3912 tests across 123 modules in 33.2s on 8 workers, 0 problem(s)
  run_tests exit=0
  $ python3 lint.py
  lint: 0 problem(s) across 35 skills
  $ python3 kb.py drift
  drift: 0 problem(s)
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  gates exit=0
  ```
  No file under `factory/templates/` or in `factory_init.MIRRORS` was
  touched, so no manifest regeneration was needed; no skill
  `description:` line and no `.claude-plugin/plugin.json` changed.
- Result: PASS

### An agent running audit or automate follows the moved text

- Check: none — it needs a live model run.
- Result: NOT RUN

## Failures

none.

## Not verified

- Live agent behaviour: no paid `trigger_eval.py`, `charter_replay.py`
  or `claude plugin eval` run was made. Descriptions are unchanged, so
  routing is unaffected; whether an agent reads the cited reference at
  the step that names it is not demonstrated here.
- Anchor `#palette--owned-by-animated-diagram` in the interactive
  design system's contents list was written to the repo's existing
  anchor convention (`#text--three-tiers`) and not rendered on GitHub.
