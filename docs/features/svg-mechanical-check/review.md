---
stage: review
run: feature:svg-mechanical-check
date: 2026-11-04
assumptions:
  - "Severity was ranked by the reviewer, not arbitrated live by the Owner (unattended autorun). Per the stage note, critical and major findings are fixed on the branch and minors deferred with reasons."
  - "Soft gate satisfied: verification.md exists (16 of 16 PRD criteria pass), so the review does not invert the usual order."
---

# Review: A mechanical SVG check for the diagram skills

## Scope

The run's diff, `eff46d2...HEAD` on `feat/svg-mechanical-check`: `svg_check.py`
(new), its verb in `factory.py`, `tests/test_svg_check.py` and
`tests/fixtures/svg-check/*.svg`, both diagram skills' step 7 and design-system
text, both `assets/boilerplate.svg` scaffolds, the AGENTS.md and CLAUDE.md tool
entries, `docs/backlog.md`, and the run's artifacts. Diff files outside this
run's directories that appear in `git diff main...HEAD` come from a stale local
`main`, not from this run, and were not reviewed.

Beyond reading the code, the reviewer ran probes against the real tool from
`/tmp` (not committed): hostile and malformed inputs, 20,000 byte-level
mutations of the committed fixtures and both scaffolds, and timing probes for
long attribute values, 20,000-deep nesting and 20,000 style rules.

## Findings

### Major: an unknown `encoding=` declaration crashes the check with a traceback

- Scenario: a file starting `<?xml version="1.0" encoding="bogus"?><svg
  xmlns="http://www.w3.org/2000/svg"/>` made `expat` raise `LookupError`,
  which `_refusal` did not catch (it caught only `ExpatError`). `check()`
  documents "never raises on file content", and the CLI promises exit 2 for
  "not checked". Observed before the fix: `python3 -I svg_check.py enc.svg`
  printed a traceback and exited 1, the code that means "defects found". The
  step-7 loop tells the generator to fix each named defect on exit 1, but a
  traceback names none, so the generator has nothing to fix and no refusal
  text to act on.
- Standard: none (the contract is architecture.md's "never raises on file
  content" and the 0/1/2 split that follows ADR-0114).
- Decision: fixed in `3be7ab1`. `_refusal` now catches `LookupError` beside
  `ExpatError` and returns `not well-formed: unknown encoding: bogus`; a test
  was added first and failed before the fix. After the fix the CLI prints one
  line and exits 2. The 20,000-mutation fuzz found no other exception class.

### Minor: a root `<svg>` with no `xmlns` gets the message "root element is svg, not svg"

- Scenario: `<svg width="9" height="9"/>` (the usual forgotten-`xmlns` slip)
  is reported as `root element is svg, not svg` and nothing else is read. It
  still fails, which is right, but the message gives the generator no hint that
  the namespace is the defect.
- Standard: none
- Decision: deferred — the spelling is the one architecture.md pins (`root
  element is <name>, not <svg>`) and the tests assert; the file does fail with
  exit 1, so nothing ships. A clearer spelling is a one-line change when the
  tool is next touched.

### Minor: `xml:id` is not counted as an id, and no `aria-labelledby` reference is checked

- Scenario: two elements with `xml:id="a"`, or an `aria-labelledby` naming an
  absent id, pass. Only the four defects in the brief's success statement are
  in scope, and neither scaffold uses `xml:id`.
- Standard: none
- Decision: deferred — outside the brief's four-defect list; a dangling
  `aria-labelledby` silently drops the accessible name, so it is worth a seed
  if the check is extended.

### Minor: defect lines echo file content verbatim, including control characters

- Scenario: an `href` value written with a character reference such as
  `&#10;` keeps its newline in the printed `external href "..."` line, so a
  hostile file could print a second line that reads like a result line. Exit
  code 1 and the real defect line are unaffected, and the skill text tells the
  generator to act on the exit code.
- Standard: none
- Decision: deferred — the file is the generator's own output, not third-party
  input, and escaping would change the problem-string spellings the tests pin.
  The reviewer-data rule (a tool's output is material to judge) already covers
  how the agent reads it.

### Minor: ADR-0062 says a skill earns a tool only for a fact a seam already owns; architecture.md records "no ADR"

- Scenario: ADR-0062's Decision and Consequences call the precedent
  "deliberately narrow" (`pipeline-board` and `board.py`). The diagram skills
  now run `svg_check.py`, a tool whose rules (what counts as a reference, what
  is refused) it owns itself and no existing seam owns. `voice_grade.py` for
  `house-voice` already stretched the same precedent (ADR-0119, provisional),
  and the architecture never mentions ADR-0062 or ADR-0008.
- Standard: none
- Decision: deferred — the tool is stdlib, tested, linted and root-only, which
  is the ADR's own bar for a skill's tool, and the skill text states what to
  do when Python 3 is unavailable, which keeps ADR-0008's bare-install promise.
  The open question is whether ADR-0062's narrowness still holds once a
  second tool-running skill ships; that is an Owner call, not a defect in this
  diff. Reported at minor, not major, because it forks a convention without
  breaking a security or data contract.

### Minor: "no text" is printed as a second line beside a defect list

- Scenario: for a defective file with no text, the CLI prints the defect line
  and then `...: no text`. The PRD says the check "names only that defect";
  the extra line is a report line, not a defect, and Verify flagged it.
- Standard: none
- Decision: deferred — architecture.md specifies "then the text line when it
  could be read", the tests pin it, and exit code and defect lines are
  unambiguous.

### Minor: a pathological style sheet costs quadratic time

- Scenario: 20,000 one-property rules with 2,000 text elements took about 3.3
  seconds (every text element scans every rule). A real diagram has tens of
  rules.
- Standard: none
- Decision: deferred — not reachable by the skills' own output; no failure
  scenario within the tool's use.

## Passes with no findings

- **Correctness:** one major (fixed above) and the minors above. The refusal
  pass fires at the DOCTYPE and entity declarations before any entity is
  defined (billion-laughs and external-entity fixtures refuse, and a CDATA or
  comment containing `<!ENTITY` does not misfire). SMIL clock values
  (`1.5s`, `indefinite`, `wallclock(...)`) are not read as ids. Honest
  non-reads (`em`, `%`, `var()`, `@media` rules) are counted and printed, not
  dropped. Deep nesting, long attribute values and non-finite or huge numbers
  did not raise.
- **Design:** matches architecture.md's contracts, problem strings and 0/1/2
  split; root-only, no sibling imports, `factory.py` verb added, no MIRRORS row
  needed. The one design note is the ADR-0062 minor above.
- **Security:** the untrusted-parse risk the brief named is closed by the
  DTD and entity refusal. The tool reads one local file and writes nothing; no
  network, no secrets. Echoed file content is covered by the minor above.
- **Complexity:** the lean cut-list found nothing to cut. No `lean:` markers
  in the diff; no unused imports or flags (`argparse` is not imported; the
  architecture's mention of it is prose only). Every `Report` field has a
  reader.
- **ADR compliance:** `adr_status.py` listed the live ADRs (ADR-0001 to ADR-0122). Read in full for the
  subject the diff reaches: ADR-0008, ADR-0062 (finding above), ADR-0091 (no
  sibling import, so no dual-membership row), ADR-0107 and ADR-0108 (unknown
  never rolls up to pass: `unread` and `skipped_rules` are printed), ADR-0114
  (the 0/1/2 exit split followed), ADR-0119 (the voice-grade precedent). The
  rest are out of scope: they concern the factory, tracker, eval and fast-path
  planes, which the diff does not touch. Provisional ADRs were not the basis
  of any finding.
- **Standards:** `stdlib-only` (factory, advisory) is met: imports are
  `math`, `re`, `sys`, `collections`, `dataclasses`, `xml.*`.
- **Domain passes:** none selected. No changed path names a payment word, a
  migrations directory or SQL file, or a package manifest or lockfile.

## Battery after the fix

Run from this worktree after `3be7ab1`:

    python3 run_tests.py -j 3   -> tests: 4027 tests across 127 modules in 53.8s on 3 workers, 0 problem(s)
    python3 lint.py             -> lint: 0 problem(s) across 35 skills
    python3 kb.py drift         -> drift: 0 problem(s)
    python3 gates.py            -> gates: 0 problem(s)
    python3 gates.py --selftest -> selftest: ok
    python3 factory_init.py update-manifest -> factory-init: 0 problem(s) (git status clean after)

## Verdict

Ready to ship. No critical finding was raised, so none remains unfixed. The one
major finding is fixed and the battery was re-run green. Six minors are
deferred, each with its reason above. Not run, by the brief's no-spend rule and
because no skill `description` changed: the routing eval, `claude plugin
eval`, `trigger_eval.py`, `charter_replay.py`. No render or browser check was
made (out of scope by the PRD). The Verify figures for smallest text on the
scaffolds and skill map (7.5px, 8.5px, 9.4px) were not independently re-derived
here.
