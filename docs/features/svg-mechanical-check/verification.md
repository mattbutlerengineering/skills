---
stage: verify
run: feature:svg-mechanical-check
date: 2026-11-04
---

# Verification: A mechanical SVG check for the diagram skills

## Summary

16 of 16 PRD success criteria pass; 0 fail. Every criterion was run from
this worktree with a real command and its output is quoted below. No
criterion was skipped, deferred or left unknown, and no paid run (routing
eval, `claude plugin eval`, `trigger_eval.py`, `charter_replay.py`,
`claude -p`) was made or is owed, because no skill `description` changed.
The battery is green: `tests: 4026 tests across 127 modules ... 0
problem(s)`, lint, kb drift, gates and selftest all 0 problems. Two
observations are recorded under Not verified (they are not failures).

## Criteria & evidence

### PRD 1: all four defects named, one per line

- Check: `python3 -I svg_check.py tests/fixtures/svg-check/all-four.svg`
- Evidence:
  ```
  svg-check: all-four.svg: root width missing
  svg-check: all-four.svg: duplicate id "a" on 2 elements
  svg-check: all-four.svg: dangling url(#nope) in rect fill
  svg-check: all-four.svg: external href "https://example.com/x.png" on image
  svg-check: all-four.svg: no text
  exit=1
  ```
- Result: PASS

### PRD 2: four single-defect fixtures name only their defect

- Check: ran `no-size.svg`, `dup-id.svg`, `dangling-url.svg`, `external-href.svg`.
- Evidence:
  ```
  svg-check: no-size.svg: root width missing                      exit=1
  svg-check: dup-id.svg: duplicate id "a" on 2 elements           exit=1
  svg-check: dangling-url.svg: dangling url(#nope) in rect fill   exit=1
  svg-check: external-href.svg: external href "https://example.com/x.png" on image   exit=1
  ```
  Each also prints a second `...: no text` line, the report note that the
  fixture has no text; it is not a defect line (see Not verified).
- Result: PASS

### PRD 3: clean fixture passes and states smallest text and embed width

- Check: `clean.svg` default and `--embed-width 440`.
- Evidence:
  ```
  svg-check: clean.svg: pass — smallest text 8.3px at 830px embed width   exit=0
  svg-check: clean.svg: pass — smallest text 4.4px at 440px embed width
  ```
- Result: PASS

### PRD 4: DTD and entity payloads refused, not expanded

- Check: both refusal fixtures from the CLI; `python3 -m unittest tests.test_svg_check` (37 tests) creates a sentinel file named by `external-entity.svg` and asserts its contents never appear in the output.
- Evidence:
  ```
  svg-check: entity-expansion.svg: refused: the file declares a DTD or an entity (remove the <!DOCTYPE>; the check does not expand either)
  exit=2
  svg-check: external-entity.svg: refused: the file declares a DTD or an entity (remove the <!DOCTYPE>; the check does not expand either)
  exit=2
  Ran 37 tests in 0.022s
  OK
  ```
- Result: PASS

### PRD 5: animated SMIL and CSS fixtures

- Check: the four animated fixtures.
- Evidence:
  ```
  svg-check: smil-clean.svg: pass — no text                                              exit=0
  svg-check: css-clean.svg: pass — no text                                               exit=0
  svg-check: smil-dangling.svg: dangling timing reference "first" in animateMotion begin  exit=1
  svg-check: css-dangling.svg: dangling url(#g) in <style>                               exit=1
  ```
- Result: PASS

### PRD 6: external href fails, same-document fragments pass

- Check: `external-href.svg` and `same-doc-href.svg`.
- Evidence:
  ```
  svg-check: external-href.svg: external href "https://example.com/x.png" on image   exit=1
  svg-check: same-doc-href.svg: pass — no text                                       exit=0
  ```
- Result: PASS

### PRD 7: stdlib only, invoked under `python3 -I`

- Check: listed every import in `svg_check.py`; every command above ran as `python3 -I`; both skills' step 7 give the command with `-I`.
- Evidence:
  ```
  13:import math
  14:import re
  15:import sys
  16:from collections import Counter
  17:import xml.etree.ElementTree as ET
  18:from dataclasses import dataclass, field
  19:from xml.parsers import expat
  skills/architecture-diagram/SKILL.md:115:    python3 -I <this skill's directory>/../../svg_check.py <file.svg>
  skills/animated-diagram/SKILL.md:152:    python3 -I <this skill's directory>/../../svg_check.py <file.svg>
  ```
- Result: PASS

### PRD 8: tests offline, fixtures committed, picked up by `run_tests.py`

- Check: `python3 run_tests.py -j 3`; fixtures live in `tests/fixtures/svg-check/` (14 files); the test module only reads files and runs the CLI in a temp directory, with no model or network call (the import list above has no network module).
- Evidence:
  ```
  tests: 4026 tests across 127 modules in 50.7s on 3 workers, 0 problem(s)
  ```
- Result: PASS

### PRD 9: both skills' step 7 instruct the check and say what failure means

- Check: read `skills/architecture-diagram/SKILL.md` step 7 (quoted in full above the by-eye text) and the `animated-diagram` step 7 line 152 region.
- Evidence (architecture-diagram step 7):
  ```
  Exit 0 means no defect: ... Exit 1 names each defect, one per line: fix every one
  in the file and rerun until exit 0. Exit 2 means the file was not
  checked: remove the `<!DOCTYPE>` or entity it names, or repair the XML,
  and rerun. If Python 3 is not available, say that the check did not run;
  never skip it silently. It does not see themes, contrast or layout, so
  the by-eye checks below still apply.
  ```
  `animated-diagram/SKILL.md` carries the same command at line 152 (26-line
  diff, scoped to the `.svg` target per the breakdown).
- Result: PASS

### PRD 10: architecture-diagram scaffold has root width/height and passes unmodified

- Check: from `skills/architecture-diagram`, `python3 -I ../../svg_check.py assets/boilerplate.svg`; `git diff origin/main --stat` shows the scaffold as a one-line change.
- Evidence:
  ```
  svg-check: assets/boilerplate.svg: pass — smallest text 7.5px at 830px embed width
  exit=0
   skills/architecture-diagram/assets/boilerplate.svg | 2 +-
  ```
- Result: PASS

### PRD 11: animated-diagram scaffold passes

- Check: from `skills/animated-diagram`, same command.
- Evidence:
  ```
  svg-check: assets/boilerplate.svg: pass — smallest text 8.5px at 830px embed width
  exit=0
   skills/animated-diagram/assets/boilerplate.svg     | 2 +-
  ```
- Result: PASS

### PRD 12: backlog line 91 claimed

- Check: `sed -n 91p docs/backlog.md | grep -o 'claimed[^.]*'`; the text-floor half is appended as an open seed at line 162.
- Evidence:
  ```
  claimed: feature:svg-mechanical-check)
  162:- The text-floor half of the architecture-diagram scaffold seed above is still open: ...
  ```
- Result: PASS

### PRD 13: packaging, lint and manifest leave no finding or drift

- Check: `python3 lint.py`; `python3 factory_init.py update-manifest` then `git status --porcelain`. `svg_check.py` is root-only, with a `svg-check` verb in `factory.py`.
- Evidence:
  ```
  lint: 0 problem(s) across 35 skills
  factory-init: 0 problem(s)
  (git status --porcelain: empty)
  ```
- Result: PASS

### PRD 14: the full battery

- Check: from the worktree, `python3 run_tests.py -j 3`, `python3 lint.py`, `python3 kb.py drift`, `python3 gates.py`, `python3 gates.py --selftest`.
- Evidence:
  ```
  tests: 4026 tests across 127 modules in 50.7s on 3 workers, 0 problem(s)
  lint: 0 problem(s) across 35 skills
  drift: 0 problem(s)
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

### PRD 15: no frontmatter `description` changed

- Check: `git diff -U0 origin/main -- 'skills/*/SKILL.md' | grep -E '^[-+]description'`; `git diff origin/main -- .claude-plugin | wc -l` for the plugin manifest.
- Evidence:
  ```
  (grep printed nothing)
  0
  ```
  Only the two diagram `SKILL.md` files changed among skills. No routing
  eval is owed, and none was run.
- Result: PASS

### PRD 16: README skill map read, file unchanged

- Check: `python3 -I svg_check.py docs/assets/skill-map.svg`; `git diff --stat origin/main -- docs/assets`.
- Evidence:
  ```
  svg-check: docs/assets/skill-map.svg: pass — smallest text 9.4px at 830px embed width
  exit=0
  (git diff --stat: empty)
  ```
  No defect line, so no seed is owed.
- Result: PASS

### Breakdown acceptance not covered by a PRD criterion

- Check: refusal and CLI paths from the first item: truncated file, missing path, bad usage.
- Evidence:
  ```
  svg-check: truncated.svg: not well-formed: no element found: line 3, column 0   exit=2
  svg-check: nonexist.svg: cannot read: No such file or directory                  exit=2
  ```
  The remaining item-level checks (a root `width="100%"`, a root `<html>`,
  the `unread` and `skipped_rules` suffixes, `check(b"<svg/>", 0)` raising
  `ValueError`) are asserted by `tests/test_svg_check.py`, which passed
  (37 tests, OK; also inside the 4026 above).
- Result: PASS

## Failures

none.

## Not verified

- `python3 -I` hardening against a hostile real-world SVG beyond the two committed payloads (billion-laughs and external entity): only those fixtures were run. A DTD of any kind is refused before parsing, so no other payload shape was tried.
- Fixtures with no text print an extra `...: no text` line beside the defect line. The PRD says the check "names only that defect"; the note is a report line, not a defect, and this reading is the verifier's, not an Owner decision. Flagged for Review.
- The smallest-text figures are the tool's own computation. The test hand-works them for `clean.svg`; the skill-map 9.4px and scaffold 7.5px/8.5px figures were not independently re-derived here.
- Rendering in a browser (the Moonshot, backlog line 161) is out of scope by the PRD.
