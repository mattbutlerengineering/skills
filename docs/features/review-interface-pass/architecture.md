---
stage: architect
run: feature:review-interface-pass
date: 2026-11-04
ux: skipped — Skill text only (a domain-table row and a reference); no screen or user-facing surface.
assumptions:
  - "The skill's step 6 (present the draft and revise on feedback) is not run: the run is unattended, so the four trade-offs below are decided here on the draft's own reasoning and recorded in Decisions & alternatives for Review and the Owner to overturn."
  - "The brief's scope line 'offline fixture diffs if Architect wants them' is answered no: the verdicts are a reviewer's judgments over prose, nothing executes a fixture diff, and the worked examples live in the reference itself. The pin test keeps path-list fixtures only, because selection is mechanical."
  - "No decision passes all three legs of the protocol's ADR test (a row and a reference are cheap to reverse), so no ADR is written and no ADR number is taken."
  - "Selection extensions beyond the six the brief names (`*.html` and the other template extensions below) are Architect's reading of 'templates', which the brief marks as an open unknown."
---

# Architecture: An Interface domain pass for review

## Approach

Add the pass the way the three existing passes are built: one row in
the domain table that selects by path, and one reference the row links
to. The row's job is selection and nothing else; the reference holds the
method. Selection is a closed list of file extensions, not path words:
the payments row is broad on purpose because a payment bug hides in any
file that mentions a charge, but an interface regression hides in a
file's *removed lines*, and a word like `template` or `components` would
select this repo's own markdown template directories and every adopter's
non-UI folders of the same name. The method is a fixed reading order over
the diff: take the removed side of each hunk, find the listed signals,
clear any whose equivalent replacement sits on the same element, then
report what is left with a status by cause. A status is a label in the
finding's heading, mapped onto `review`'s existing critical / major /
minor, so the skill's severity model and `review.md` template do not
change. The pass reads the diff and the changed files only; it never
renders anything, which is also the line with `polish`.

## Components

### Interface row (in `skills/review/references/domain-reviewers.md`)

- Responsibility: decide, from the changed-path list alone, whether the
  Interface pass runs, and link the reference.
- Collaborators: the table's shared contract (unchanged); `interface.md`;
  the pin test.

### Interface reference (`skills/review/references/interface.md`, new)

- Responsibility: the method: which signals to look for on the removed
  side, what clears one, how a finding gets a status by cause, how a
  status maps to a severity, and what the pass leaves to others.
- Collaborators: `domain-reviewers.md` (the shared contract it follows,
  linked the way `migrations.md` links it); `polish` (named once, as the
  owner of rendered judgment).

### Credit lines (`skills/review/SKILL.md`, `README.md`)

- Responsibility: record the origin of the method, restated, nothing
  copied. `SKILL.md` carries one sentence in its body (not in the
  frontmatter, whose `description` stays byte-identical) and step 5 names
  `references/interface.md` beside the other three. The README credits
  paragraph gains the source's link and a clause that `review` borrowed
  its removed-side reading.
- Collaborators: `polish`'s credit in `references/moves.md` is the
  pattern: name the source, its licence and owner, say it is a
  restatement. `NOTICE` is not touched.

### Domain-table pin (`tests/test_review_domain_table.py`, new)

- Responsibility: fail when the Interface row, its link, or the
  reference's signal list goes missing, and pin selection on fixed path
  lists.
- Collaborators: the two markdown files above, read as text. Stdlib only
  (`unittest`, `re`, `fnmatch`, `pathlib`), in the style of
  `tests/test_reviewer_data_rule.py`.

## Data model

No stored data. The pass handles three shapes, all in the reviewer's
head or in `review.md`:

- **Selection set** — the row's extension list, read by the test as the
  backticked `*.<ext>` tokens in the row's second cell.
- **Signal** — one of the PRD's eight (`aria-label`, `alt=`,
  `:focus-visible`/`outline`, `tabindex`, `prefers-reduced-motion`,
  logical properties, `lang=`/`dir=`, a token swapped for a literal),
  seen on a `-` line.
- **Finding** — the skill's existing format plus the status in the
  heading: `### Major: interface — regression — <one-line statement>`.

The reads the PRD requires: (a) list changed paths and match the row;
(b) read `git diff -U0 -M <base>...HEAD -- <selected paths>` and take
the `-` lines; (c) for each signal found, read the element or selector
on the added side and the whole changed file. All three are read-only.

## Interfaces & contracts

### Interface row → the reviewer

- Input: the changed-path list (`git diff --name-only <base>...HEAD`),
  matched ignoring case, by the table's existing rule.
- Output: the Interface pass is selected when a path matches any of
  `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.astro`, `*.css`, `*.scss`,
  `*.sass`, `*.less`, `*.html`, `*.htm`, `*.erb`, `*.hbs`, `*.ejs`,
  `*.njk`, `*.twig`, `*.liquid`, `*.jinja`, `*.jinja2`, `*.pug`,
  `*.cshtml`, `*.razor`. Never selected by a directory or a word.
  Generated output (`*.min.css`, built bundles) matches the extension and
  is skipped with a one-line note: it has no author's intent on its
  removed side.
- Failure modes: a false selection costs one read that comes back clean
  (the table's own accepted cost). A UI written in plain `.js` or `.ts`
  (styled-components, template literals) is not selected; the reference
  says so as a known limit, since widening to those extensions would
  select most of every adopter's diffs and teach readers to skip the pass.

### Interface reference → the reviewer

- Input: the removed lines of each hunk in the selected paths, the added
  side of the same hunk, and the whole changed file (the shared contract).
- Output: findings in the skill's format, in three steps:
  1. **Find.** Each `-` line that carries a listed signal is a candidate.
     A candidate on an element or rule the diff deletes whole is dropped:
     the signal left with its owner. Renames are read as moves (`-M`), not
     as a deleted file and an added one.
  2. **Clear.** A candidate is cleared when an equivalent replacement is
     on the added side *for the same element or selector*. The accepted
     equivalents: `outline` removed and a `box-shadow`, `border` or other
     `outline` value added on the same selector and state (a `:focus`
     rule rewritten as `:focus-visible` counts); `aria-label` removed and
     `aria-labelledby`, a `<label>`, or visible text giving the element a
     name added on the same element; `alt=` removed and `alt` re-added, or a
     name given by `aria-label`/`aria-labelledby` on that image;
     `tabindex` removed from an element that is natively focusable
     (`button`, `a[href]`, `input`); `lang=`/`dir=` removed and set on an
     ancestor the diff or the changed file shows; a
     `prefers-reduced-motion` block moved where the same animations are
     still covered (read it, do not assume); a token swapped for a literal
     where the changed file *defines* that token. A replacement on a
     different selector or element never clears: it is a finding. When a
     replacement may be elsewhere and the reviewer cannot read it, the
     candidate is reported as a suspicion with what would settle it
     (shared contract: evidence or silence).
  3. **Status and severity.** What is left gets one status, by cause:
     - *Regression* — the diff removes a signal from an element or rule
       that stays, with no equivalent.
     - *Introduced* — the added side carries the bad form of a listed
       signal: `outline: none` or `outline: 0` with no ring on the same
       selector, a positive `tabindex`, a literal where the surrounding
       code uses a token. Added-side defects outside that list are not
       this pass's.
     - *Pre-existing* — the defect is in a line the diff does not touch,
       in a changed file or in an unchanged consumer of a changed token.
       At most three are reported, after the other two, so a cap can
       never hide a regression.
     Severity is the skill's, set by the scenario, never by the status.
     Regression and Introduced: **critical** only where the scenario
     names a task a keyboard or assistive-technology user can no longer
     complete (the only accessible name of an icon-only control removed;
     the only focus indicator of a control removed); otherwise **major**,
     except a token swapped for a literal, **minor** unless the file shows
     the theme or contrast failure it causes. Pre-existing is **minor**
     and never blocks. No new severity and no change to the fix loop.
- Failure modes: a hunk too large to read in full is read in the
  selected paths only and the rest is named as not read in "Passes with
  no findings" (the fail-closed roll-up), never reported clean. A
  signal that is neither cleared nor confirmed gets a suspicion line, not
  a finding.

### Pin test → `python3 run_tests.py`

- Input: `domain-reviewers.md`, `interface.md`, and fixed path lists in
  the test.
- Output: pass or a named failed assertion. Asserts: the table's pass
  names are exactly Payments, Migrations, Dependencies, Interface; every
  row's Read link resolves to a file; the Interface row carries the six
  extensions the PRD names; `interface.md` names all eight signals; and
  with the extension tokens parsed from the row, UI paths
  (`src/App.tsx`, `styles/main.scss`, `views/show.html.erb`,
  `a/Button.vue`) match and non-UI paths (`README.md`,
  `skills/x/templates/TEMPLATE.md`, `src/api.ts`, `package.json`,
  `migrations/001.sql`) do not.
- Failure modes: a reworded table that still carries the facts passes;
  a deleted row, a dead link, a dropped extension or a dropped signal
  fails with the name of what is missing.

## Stack & dependencies

- Markdown only for the pass: the domain-pass contract fits, and the
  Out-of-scope list rules out a script.
- Python stdlib `unittest` for the pin — beside the existing tests, no
  dependency (standard `stdlib-only`).
- No new dependency, no changed frontmatter, no `factory/templates/**`
  or mirrored-root-file edit, so no manifest regeneration is owed.

## Decisions & alternatives

- **Selection by a closed extension list** over path words like the
  payments row (`template`, `component`, `view`, `ui`) — words select this
  repo's own `templates/` directories of markdown and any adopter's
  non-UI folder of the same name; extensions select what is UI and
  nothing else. Accepted cost: a UI in plain `.js`/`.ts` is missed and
  the reference says so.
- **Status is a label, severity stays the scenario's** over a new
  severity or a status-to-severity table that overrides the scenario —
  `review`'s fix loop and `review.md` template key on critical/major/
  minor; a fourth level or a parallel scale would touch both. Cost: the
  status adds no ranking power; it tells the author what the diff owes.
- **Introduced covers three added-side forms, not every added defect**
  over a full added-side accessibility audit — the pass's value is the
  removed side no other pass can see; a full audit duplicates `polish`
  and grows false positives that teach readers to skip the pass.
- **The line with `polish` is the medium**: this pass reads the diff and
  says whether a signal was taken away; `polish` reads a rendered
  surface and says whether what is there works. No `polish` change and
  no cross-reference from it; `interface.md` names `polish` once as the
  owner of rendered judgment, so a reader who wants contrast or layout
  knows where it lives. The polish run's `inspect` edits are checked for
  overlap at merge time, not designed around here.
- **No fixture diffs kept as data** over a directory of fixture diffs
  with expected verdicts — nothing would execute them and a stale one
  would pass silently. The three PRD cases (bare `aria-label` deletion
  reports; `outline: none` to `box-shadow` on the same selector is
  silent; the same swap on a different selector reports) are worked
  examples in `interface.md`, where the reviewer reads them, and Verify
  hand-walks them.
- **Pin the table with a path-list test** over prose-string assertions
  only — the "not selected on a diff with no UI path" criterion is
  checkable mechanically from the parsed extension list; the signal
  list is the one place a string check is the right pin.
- **No ADR.** A table row and a reference are cheap to reverse and the
  choices above follow the three existing passes, so the decision fails
  the "hard to reverse" and "surprising" legs.

## ADRs

none — no decision met the ADR bar.
