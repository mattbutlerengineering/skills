---
stage: review
run: maintenance:a-sketch-drawn-from-memory
date: 2026-10-25
---

# Review: ux-design sketches from memory, checks scenarios last, and grades its own work

## Scope

`git diff origin/main...fix/a-sketch-drawn-from-memory` at `1335d40`:
`skills/ux-design/SKILL.md`, `skills/ux-design/TEMPLATE.md`,
`tests/test_ux_design_grounding.py`, and the run's `defect.md` and
`verification.md`. Two readers:

- the author's five passes;
- a fresh general-purpose subagent given the files and issue #1093, not the
  author's conclusions, and asked for Critical and High findings plus at
  most three minors. This is the same rule the fix adds to ux-design.

The fixes landed in `0ddb8c1`. On that commit
`python3 -m unittest tests.test_ux_design_grounding` printed `OK` (13
tests), and the full checks printed `tests: 3907 tests across 122 modules
in 27.1s on 8 workers, 0 problem(s)`, `lint: 0 problem(s) across 35
skills`, `drift: 0 problem(s)`, `gates: 0 problem(s)`, `selftest: ok`.

## Findings

### Major: a contradicting code fact had nowhere to go

- Scenario: step 5 said a fact that contradicts the flow "becomes a
  dependency for Architect", but the template had no section for it.
  Architect reads nothing from `ux.md` beyond whether it exists. A designer
  who finds that roles are unenforced or that cancellations go out by email
  only (#1093's own evidence) buries it in Code facts, and Architect designs
  without it. The hand-repaired consumer doc needed a `## Dependencies
  surfaced for Architect` section for exactly this. (Fresh reviewer.)
- Standard: none
- Decision: fixed in `0ddb8c1`. The template gains that section, and step 5
  now re-opens the affected flow with the user, or records the fact there
  when the fix is technical. Architect's own read of the section is left out
  of scope (minor, below).

### Major: under autorun, the independent review becomes a silent self-review

- Scenario: autorun runs each stage as a fresh subagent. Where a subagent
  cannot dispatch another, every unattended run takes the inline fallback,
  which is the self-review that missed 8 High issues in #1093. Its
  `review: inline, not independent` label sat in the body, and autorun's
  report collects only frontmatter `assumptions:`, so nobody would see it.
  (Fresh reviewer.)
- Standard: none
- Decision: fixed in `0ddb8c1`. In an unattended run the fallback is also
  logged under `assumptions:`, so the run's report shows it.

### Minor: the walkthrough list was chosen without asking the user

- Scenario: step 3 had the designer pick the hardest scenarios alone. That
  sits against ADR-0011's "interview relentlessly" for UX Design. The user
  knows which cases hurt, and a designer-chosen list misses the one they
  would have named. (Author.)
- Standard: none
- Decision: fixed in `0ddb8c1`: "Confirm the list with the user before going
  on".

### Minor: the reviewer did not get `idea.md`, and nothing re-walked after fixes

- Scenario: the walkthroughs come from `idea.md` and `prd.md`, but the
  reviewer got only `prd.md`. It could not tell whether a hard scenario was
  missing. A fix to one finding can also break a walkthrough that already
  passed. (Fresh reviewer.)
- Standard: none
- Decision: fixed in `0ddb8c1`. `idea.md` is in the file list, "a hard
  scenario left out" is in the reviewer's scope, and the walkthroughs are
  re-walked after the fixes.

### Minor: the interview still asks about existing screens before any code is read

- Scenario: step 4 asks "what's on it" for each surface before step 5 reads
  code, so the user answers from memory first. Step 5 catches the
  contradiction afterwards. (Fresh reviewer.)
- Standard: none
- Decision: fixed in `0ddb8c1`. Step 5 now explicitly re-opens the affected
  flow with the user. Moving the code read before the interview was not
  done: until the flows exist, the designer does not know which surfaces
  they touch.

### Minor: the tests pin sentences, not behaviour

- Scenario: rewording any pinned sentence turns a case red, and no case
  shows a designer follows the text. The template's section order and the
  walkthrough-gap link to Deliberately not designed are not pinned. (Fresh
  reviewer.)
- Standard: none
- Decision: deferred. This is the repo's phrase-pinning convention
  (`tests/test_idea_ambition_ladder.py`), and the module docstring says what
  it does not show. Behaviour is criterion 8 in verification.md, NOT RUN.

### Minor: Architect does not read the new Dependencies section

- Scenario: the section now exists, but `skills/architect/SKILL.md` gates
  only on `ux.md` existing. An architect that does not read `ux.md` closely
  can still miss a recorded dependency.
- Standard: none
- Decision: deferred. A change to Architect is outside this run's one-skill
  scope (defect.md, Ruled out). Worth a follow-up issue if a run shows the
  miss.

## Passes with no findings

- Correctness: no failure beyond the findings above. No tool parses `ux.md`
  headings: `protocol.py` checks only that the file exists, or for
  `ux: not-applicable`. So the four new template sections break no consumer.
- Security: prose and a read-only test, with no inputs, secrets or shell
  surface.
- Complexity: no code. The cut-list found nothing to cut, and the diff adds
  no `lean:` marker.
- ADR compliance: checked against `adr_status.py`'s live set. ADR-0011 was
  found and fixed above. ADR-0015 (templates per stage) and ADR-0100 (commit
  at the boundary) hold. ADR-0077 holds: the reviewer is read-only. No new
  ADR is owed, because a skill-prose change is easy to reverse and fails the
  protocol's first leg; the design calls are in defect.md's Notes. Plugin
  version untouched (ADR-0095).
- Domain passes: none selected. No payment, migration or dependency path
  changed.
- Standards: one `pipeline`/`docs` statement applies
  (`adr0004-typed-ids-in-frontmatter`, advisory). The run artifacts carry no
  typed id, so it holds.

## Verdict

Ready to ship. No critical finding was raised; both majors and three minors
are fixed in `0ddb8c1`, and two minors are deferred with reasons. One
check stays unknown: whether a designer following the revised skill catches
#1093's defects on a live run (verification.md criterion 8, NOT RUN). Every
other pass ran.
