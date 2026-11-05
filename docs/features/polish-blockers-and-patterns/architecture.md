---
stage: architect
run: feature:polish-blockers-and-patterns
date: 2026-11-04
ux: skipped — the deliverable is skill text and a lint or test pin; no screen or flow is designed (autorun brief, User-facing surface)
assumptions:
  - "Interview answered from the autorun brief, idea.md and prd.md. The brief carries no trade-off answers, and the skill supplies no named options here, so the three open PRD questions (pin shape, credit placement, and the WCAG ids) are settled by the design below rather than asked."
  - "The three decisions below (one owner for the blocker list, credit in moves.md, a test module as the pin) are the Architect's reading and were not confirmed live; each can be reversed by editing one file."
  - "The candidate WCAG 2.2 ids in the pattern table are recalled, not checked. This stage does not fetch the WCAG text; the implementer checks each against the WCAG 2.2 text (PRD criterion) and the design makes an unchecked id visible as `unverified`."
  - "No decision met all three legs of the protocol's ADR test, so none is written. Skill prose that one run's PR can rewrite is not hard to reverse."
---

# Architecture: named blockers and code detection patterns in polish

## Approach

Two prose additions to `skills/polish/`, one pin beside the tests. The
blocker list goes in `SKILL.md` step 5, where the accessibility floor
already lives; it names the six floor items and the eight added blockers
and says each is high severity on sight. `moves.md`'s `inspect` move owns
no second copy: its ranking line cites step 5's list and puts those
findings first. The pattern table goes in `moves.md` under `inspect`,
beside the thresholds it extends, as one table with a WCAG column. A new
`tests/test_polish_shape.py` pins the three countable facts (eight
blockers present, 10 to 15 table rows, an id on every accessibility row)
through one pure function that returns problem strings, which is the
repo's checker contract. No frontmatter, step count or move changes.

The alternative shape was a self-contained reference file
(`references/blockers.md`) holding both lists. It lost because the list
sets severity for step 5 and `inspect`, so a reader at step 5 would
follow a link to learn what the floor is; and `moves.md` already carries
`inspect`'s thresholds, so the table reads best next to them.

## Components

### Blocker list (`skills/polish/SKILL.md`, step 5)

- Responsibility: the one place that names what is high severity on
  sight: the six floor items, kept as written, and the eight added
  blockers as eight list items under one lead line that says the list
  sets severity and adds no rule or step.
- Collaborators: `inspect` ranking (cites it), the pin.

### Inspect ranking and pattern table (`skills/polish/references/moves.md`)

- Responsibility: `inspect`'s **Hand back** line ranks the named blockers
  (the step 5 list) first, then the rest "by who is locked out". A new
  "Code patterns" table sits after the **Do** bullets and before **Hand
  back**, so it reads next to the thresholds. Columns: pattern (the
  shape to grep for), where it shows (HTML, CSS or ARIA terms), WCAG 2.2
  id, and what it costs the person. Rows are plain-HTML/CSS/ARIA only.
  The table is introduced as the code-only reading step 6 requires.
- Collaborators: step 5 list (cited), step 6 of `SKILL.md` (the table is
  what the code-only reading looks for), the pin.

### Credit line (`skills/polish/references/moves.md`, README credits paragraph)

- Responsibility: attribute jakubkrehel/skills (MIT) for the idea of a
  named blocker list and a code-pattern table, in the form of the
  existing Impeccable credit in the same file, and say the text is
  restated, not copied. The README paragraph gains the link to
  `https://github.com/jakubkrehel/skills` in its list of open-source work.
- Collaborators: the Impeccable credit it sits beside; `lint.py`'s README
  checks (implementer confirms none reject the paragraph).

### Shape pin (`tests/test_polish_shape.py`)

- Responsibility: `polish_shape_problems(skill_text, moves_text)` returns
  label-prefixed problem strings; the test asserts it is empty on the
  real files and returns the exact string on each mutated copy.
- Collaborators: the two polish files only. It is a test module, not a
  root script, so there is no manifest to regenerate and no new shared
  module (AGENTS.md: a shared module needs multiple real callers).

## Data model

No stored entities. The pin reads two shapes in markdown:

- **Blockers.** Within `SKILL.md`'s `### 5.` section, the list items under
  the blocker lead line. Count is exactly 8, and each carries a distinct
  anchor phrase the test looks for (listed below). The six floor items
  are checked by their six phrases, so the count of named blockers is
  14.
- **Pattern table.** Within `moves.md`'s `## inspect` section, the
  markdown table whose header's first cell is `Pattern`. Row count is
  10 to 15. Each row's WCAG cell is `—` (a non-accessibility row such as
  hard-coded colour), a criterion id matching `\d\.\d\.\d+`, or the word
  `unverified`; an accessibility row left blank, or not one of these, is
  a problem.

Access patterns: the test reads both files once; the reviewer agent reads
step 5 on every run and `inspect` when that move runs.

The eight blockers and their anchor phrases:

| Blocker | Anchor phrase |
|---|---|
| loss at 320px or 200% zoom | `320` and `200%` |
| meaning carried by colour alone | `colour alone` |
| destructive action, no confirm or undo | `confirm or undo` |
| truncation with no way back | `truncat` |
| content hidden past a scroll edge, no cue | `scroll edge` |
| an error naming no recovery | `recovery` |
| a semantic colour against its meaning | `semantic colour` |
| a state change carried by motion alone | `motion alone` |

(The repo writes British spelling in `polish`; the implementer uses the
file's spelling and the same string in the test.)

## Interfaces & contracts

### `polish_shape_problems(skill_text, moves_text)`

- Input: the text of `skills/polish/SKILL.md` and
  `skills/polish/references/moves.md`.
- Output: a list of problem strings, each prefixed `polish:`, such as
  `polish: SKILL.md step 5 names 7 added blockers, expected 8`,
  `polish: moves.md inspect pattern table has 9 rows, expected 10 to 15`,
  `polish: moves.md pattern row '<pattern>' has no WCAG id`,
  `polish: SKILL.md step 5 does not name '<floor phrase>'`. Empty means
  the shape holds.
- Failure modes: a missing `### 5.` section, a missing `## inspect`
  section or a missing table each return one problem string and no
  exception, so a restructured file fails with a message rather than a
  traceback. Pure: no filesystem access beyond what the test passes in.

### Pattern-table row contract (what the implementer writes)

- Candidate rows, each in HTML, CSS or ARIA terms, with the id the
  implementer must check against the WCAG 2.2 text before stating it (an
  id that cannot be checked is written `unverified`):
  1. `outline: none` or `outline: 0` with no `:focus-visible` rule for the
     same element (candidate 2.4.7)
  2. `onclick` or a click listener on a `div` or `span` with no `role`,
     `tabindex` and key handler (candidate 2.1.1; 4.1.2)
  3. `tabindex` greater than 0 (candidate 2.4.3)
  4. `maximum-scale=1` or `user-scalable=no` in a viewport meta
     (candidate 1.4.4)
  5. `aria-live="assertive"` or `role="alert"` on a success or progress
     message (candidate 4.1.3)
  6. a submit button with `disabled` until the form is valid, with no
     message saying what is missing (candidate 3.3.1; check)
  7. an `img` with no `alt` attribute (candidate 1.1.1)
  8. an `input` with no `label`, `aria-label` or `aria-labelledby`, only a
     `placeholder` (candidate 1.3.1; 3.3.2; 4.1.2)
  9. a pointer target given a width or height under 24px (candidate 2.5.8)
  10. `:hover` that reveals content or a control with no `:focus` or
      `:focus-visible` twin (candidate 1.4.13; 2.1.1)
  11. an animation or transition with no `prefers-reduced-motion` rule
      (candidate 2.3.3; a AAA criterion, so the implementer decides
      whether it belongs or marks it)
  12. a fixed `height` with `overflow: hidden` on a box that holds text
      (candidate 1.4.4; 1.4.10)
  13. a colour literal written in a component instead of a theme token
      (not an accessibility row; cell `—`)

  Thirteen is a starting list, not a quota: the implementer may drop a
  row whose id cannot be supported, as long as the count stays 10 to 15,
  and must include the six PRD-named shapes (rows 1 to 6).
- Failure mode: a wrong id is a defect the pin cannot see, since it checks
  presence of an id and not its truth. The truth check is the implementer
  reading the WCAG 2.2 text, recorded in verification evidence (PRD
  criterion). The pin catches a blank or missing id only.

## Stack & dependencies

- Markdown edits and one stdlib `unittest` module, the same kind as
  `tests/test_skill_shared_references.py` (counts in prose files).
- No new dependency, no root script, no manifest change.

## Decisions & alternatives

- **One owner for the blocker list, in `SKILL.md` step 5, with `inspect` citing it** over restating the eight in `moves.md` too — a copy in two files is the drift `tests/test_skill_shared_references.py` was written to stop. (`inspect` keeps one line of its own: blockers first.)
- **Credit line in `moves.md` beside the Impeccable credit, plus the README paragraph** over putting it in `SKILL.md` — `SKILL.md` carries no credit today; `moves.md` already does and says "restatement, not a copy", and the table that most needs attribution lives there. PRD open question settled.
- **A test module with a pure problem-string function** over a `lint.py` rule — `lint.py` checks structure across all skills, and a rule that names one skill's eight blockers is skill-specific content. The precedent is `test_skill_shared_references.py`. PRD open question settled: test only, no lint rule.
- **The pin counts presence and form and cannot pin truth** over trying to pin WCAG ids by a list in the test — a list of ids in the test would be a second copy of the same unchecked recall; checking against the WCAG 2.2 text is a human step, recorded in verification. Stated limit: the pin catches a blank id, not a wrong one.
- **The description is not pinned by a test** over a hash of the frontmatter description — a hash would force a test edit on any later legitimate description change; the PRD criterion is met by comparing the line to `origin/main` at `eff46d2` in Verify.
- **Patterns table in `moves.md`** over a new `references/patterns.md` — one reader per move, and the table reads next to `inspect`'s thresholds. If it outgrows 15 rows the PRD's own bound says to cut rows.
- **Overlap with `review-interface-pass`**: its removed-signals reference reads diffs for what a change took away; this design reads surfaces and code as they stand. No file is shared and no row is borrowed from it.

PRD traceability: blocker list and "high on sight" to the blocker-list component (step 5); "ranked first" to the inspect ranking; "sets severity only, step count unchanged" to the lead line and the pin's absence of any new step; table of 10 to 15 with the six shapes to the pattern-table contract; framework-neutral rows to the row contract (HTML, CSS, ARIA terms); WCAG ids checked to the row contract and the verification step; credit to the credit component; description unchanged to the decision above and Verify; the pin to the shape-pin component; the battery to the stack section (no manifest change); the NOT RUN kill test is Verify's record, not a component.

## ADRs

none — no decision met the ADR bar.
