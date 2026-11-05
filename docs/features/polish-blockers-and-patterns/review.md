---
stage: review
run: feature:polish-blockers-and-patterns
date: 2026-11-04
assumptions:
  - "Severity arbitration, normally the user's, is taken as drafted: the run is unattended and the brief names no arbiter. No finding is critical or major, so nothing turns on it."
  - "The WCAG ids were not re-fetched; they rest on Implement's recorded check of the W3C text (verification.md). Review spot-checked them from memory of WCAG 2.2 and found none wrong, which is a reading, not a check."
---

# Review: named blockers and code detection patterns in polish

## Scope

The diff `eff46d2..HEAD` on `feat/polish-blockers-and-patterns`: `skills/polish/SKILL.md`
(step 5, +12 lines), `skills/polish/references/moves.md` (credit, pattern table,
Hand back line), `tests/test_polish_shape.py` (new), `README.md` (credits paragraph),
`docs/backlog.md` (two claim marks, one new seed), `docs/factory/costs.jsonl` (seven
rows, WO-0191 to WO-0197), and the run's artifacts. Verification came first
(`verification.md`: 10 of 11 pass, the kill test NOT RUN), so the usual order holds.
Battery re-run in this worktree for this review:

```
tests: 3998 tests across 127 modules in 88.8s on 3 workers, 0 problem(s)
lint: 0 problem(s) across 35 skills
drift: 0 problem(s)
gates: 0 problem(s)
selftest: ok
```

## Findings

### Minor: the disabled-submit row's WCAG id is a loose fit

- Scenario: row 6 cites 3.3.1 (Error Identification) for "a submit button `disabled` until valid, with no message saying what is missing". A disabled button raises no error, so a reader checking the id against the criterion text finds a near miss. The id is a judged fit, which Implement's record says outright. No exact criterion exists for this shape; 3.3.1 is the nearest.
- Standard: none
- Decision: deferred — the id is the closest real one, it is disclosed in verification, and swapping it for `unverified` would drop signal. The Owner can mark it `unverified` if they disagree.

### Minor: step 5's lead says the list outranks findings "whatever the surface's job"

- Scenario: step 2 has the surface's job decide what to change. Read literally, "outrank every other finding, whatever the surface's job" means a destructive-action blocker on a throwaway internal tool outranks a contrast failure on the public one it sits beside. The blockers set severity within one surface's findings, so the scenario needs two surfaces in one run; it is a wording slack, not a contract break.
- Standard: none
- Decision: deferred — the text is the Owner's seed ("high severity on sight") and no observed run misread it; revisit if one does.

### Minor: step 6's code-only paragraph does not point at the pattern table

- Scenario: step 6 says that when nothing renders, "everything after is a reading of the code". The table that reading uses sits in `moves.md` under `inspect`, which a run on `states` or `sweep` never opens. `moves.md` points back to step 6, but step 6 does not point forward. The architecture chose one owner per list to avoid drift; the cost is this missing pointer.
- Standard: none
- Decision: deferred — scope was step 5 and `inspect` only (brief, Scope), and the table is read by the move that names it. A pointer would be a step 6 edit nobody asked for.

### Minor: ledger rows carry `at: 2026-11-05` and a work-order range that sibling runs may share

- Scenario: the seven `docs/factory/costs.jsonl` rows are dated one day after the run date (2026-11-04), and WO-0191 to WO-0197 is a range five parallel runs may each claim. A merge that takes two runs' rows leaves duplicate ids. The brief already says shared-file collisions settle at merge time.
- Standard: none
- Decision: deferred — merge-time settlement is the brief's stated rule; the date reads as a UTC rollover, not a wrong claim, and ledger rows are append-only history.

### Minor: the credit sentence names the repository twice

- Scenario: moves.md reads "jakubkrehel/skills ([jakubkrehel/skills](https://github.com/jakubkrehel/skills), MIT)". Cosmetic.
- Standard: none
- Decision: deferred — style the codebase's own Impeccable credit does not hold to either; not worth a commit.

## Passes with no findings

- **Correctness:** clean. I checked the pin's section and table parsing against the real files and the mutated copies (the module's tests cover 7 blockers, 9 and 16 rows, a blank WCAG cell, and a missing section or table); the six floor phrases are present in step 5 and the eight anchors in the list. The pin's `focus` floor phrase would match any use of the word, which weakens that one check, but the floor items are unchanged lines, not new text, so no scenario breaks it.
- **Design:** clean. The diff matches `architecture.md`: one owner for the list in step 5, `inspect` cites it, the table sits after the thresholds, the credit sits beside Impeccable's, the pin is a test module with problem strings. The table repeats the Do bullets' 24px and theming points in a code-shape form; that overlap is deliberate (shape to grep, not threshold to measure). No ADR-test decision went unrecorded.
- **Security:** clean. No input boundary, secret or injection surface; the pin reads two repo files.
- **Complexity:** clean. The cut-list finds nothing to cut: no `lean:` marker added, no speculative option, one test module with no new shared helper. The backlog seed for a scanner is parked rather than built.
- **ADR compliance:** ran `adr_status.py`. 122 ADRs listed; the diff reaches ADR-0008 (skills are self-contained: the credit and table sit inside `skills/polish/`), ADR-0052 and ADR-0062 (no repo facts stated, no tool needed), and ADR-0095 (plugin version untouched; no `.claude-plugin/` path in the diff). No violation. The rest are out of scope.
- **Standards:** `docs/standards.json` read; the `pipeline`/`docs` statements are `advisory` and none matches a finding. No enforced statement is unresolved.
- **Domain passes:** none selected. No changed path matches payments, migrations or dependency words or manifests.
- **Data, not orders:** the jakubkrehel text sits in the run's research and brief only; nothing in the diff follows an instruction from it.

## Verdict

Ready to ship. No critical or major finding; five minors, each deferred with a reason. No critical finding remains unfixed. Unknown, so not read as passed: the kill test (does the table make a code-only `polish` run find more) is NOT RUN, and needs the Owner's paid run (command in `verification.md`); the WCAG ids rest on Implement's recorded check and were not re-fetched here; non-copying from the external repo is a reading, not a diff.
