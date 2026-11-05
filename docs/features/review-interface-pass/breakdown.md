---
stage: decompose
run: feature:review-interface-pass
date: 2026-11-04
assumptions:
  - "The skill's step 6 (present the draft and revise on feedback) is not run: the run is unattended, so the milestone boundaries below are the draft's own and are open for the Owner to overturn."
  - "No tracker mirror: the brief's Tracker section says no tracker interaction, so no item carries a `(tracker: #N)` reference and no `WO-####` issue is created."
  - "No `docs/factory/decompose-lessons.jsonl` exists in this repo, so step 3 (past lessons) drafted as before."
  - "Test first: the pin test is the first item and is written red against the unchanged table, as the brief's Constraints ask where behaviour is testable; the reference and the row then turn it green."
---

# Breakdown: An Interface domain pass for review

Progress lives in the checkboxes below — Implement checks items off as their
acceptance criteria are met.

## Milestone 1: The Interface pass is selected and runs — a UI diff gets looked at, pinned by a test

- [ ] **Domain-table pin** — write (red first) `tests/test_review_domain_table.py` (stdlib `unittest`, `re`, `fnmatch`, `pathlib`, in the style of `tests/test_reviewer_data_rule.py`) against the architecture's Pin test contract, before the row and the reference exist.
  - Accept: `python3 -m unittest tests.test_review_domain_table` runs and fails with named assertions naming the missing Interface row and the missing `interface.md`, on the unchanged `domain-reviewers.md`; it asserts the table's pass names are exactly Payments, Migrations, Dependencies, Interface; every row's Read link resolves to a file; the Interface row carries the six extensions the PRD names (`*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.css`, `*.scss`); `interface.md` names all eight signals; and, with the extension tokens parsed from the row's second cell, `src/App.tsx`, `styles/main.scss`, `views/show.html.erb`, `a/Button.vue` match while `README.md`, `skills/x/templates/TEMPLATE.md`, `src/api.ts`, `package.json`, `migrations/001.sql` do not.
  - Blocked by: —
- [ ] **Interface reference** — write `skills/review/references/interface.md`: the Find / Clear / Status-and-severity method over the removed side of each hunk, per the architecture's "Interface reference → the reviewer" contract.
  - Accept: the file names all eight signals (`aria-label`, `alt=`, `:focus-visible`/`outline`, `tabindex`, `prefers-reduced-motion`, logical properties, `lang=`/`dir=`, a token swapped for a literal) and says to read the removed side of every hunk (`git diff -U0 -M <base>...HEAD`); lists the accepted equivalent replacements and states that a replacement on a different selector or element never clears; sets the statuses Regression, Introduced (three added-side forms) and Pre-existing (at most three, reported last) and maps them onto the skill's critical / major / minor with no new severity; states the limits (plain `.js`/`.ts` UI not selected, generated `*.min.css` skipped with a one-line note, an unreadable hunk named under "Passes with no findings", no rendered or browser check, `polish` named once as the owner of rendered judgment); links `domain-reviewers.md` for the shared contract the way `migrations.md` does; and works the three PRD cases as examples with these verdicts: bare `aria-label="Close"` deletion from an icon button reports a finding; `outline: none` to a `box-shadow` focus ring on the same selector reports nothing; the same swap on a different selector reports a finding. Restated in this repo's words, nothing copied from the source.
  - Blocked by: Domain-table pin
- [ ] **Interface row** — add the fourth row to the table in `skills/review/references/domain-reviewers.md`: pass name Interface, selected by the closed extension list, Read link `[interface.md](interface.md)`.
  - Accept: the row's second cell lists exactly the architecture's extensions (`*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.astro`, `*.css`, `*.scss`, `*.sass`, `*.less`, `*.html`, `*.htm`, `*.erb`, `*.hbs`, `*.ejs`, `*.njk`, `*.twig`, `*.liquid`, `*.jinja`, `*.jinja2`, `*.pug`, `*.cshtml`, `*.razor`) and no path word or directory; the row and its note say selection is by extension only and that generated output (`*.min.css`, built bundles) is skipped with a one-line note; the existing "No match means no domain pass … 'domain passes: none selected'" text is unchanged and still covers a diff with no UI path; `python3 -m unittest tests.test_review_domain_table` now passes with the pin from the previous items.
  - Blocked by: Interface reference

## Milestone 2: Credit on record and the battery green

- [ ] **Credit lines** — in `skills/review/SKILL.md` add step 5's reference to `references/interface.md` beside the other three and one body sentence crediting the removed-side reading to jakubkrehel/skills' `interface-review` (MIT, restated); in `README.md` add the source's link and a clause to the credits paragraph that `review` borrowed its removed-side reading. Follow `polish`'s credit in `skills/polish/references/moves.md` as the pattern.
  - Accept: `SKILL.md` and the README credits paragraph each carry a credit naming jakubkrehel/skills, its licence and that the method is restated; `git diff origin/main -- skills/review/SKILL.md` shows no change to the frontmatter `description` line (byte-identical); `NOTICE` has no diff; no skill outside `skills/review/` and no `polish` file changes.
  - Blocked by: Interface reference
- [ ] **Battery and no-spend check** — run the battery from the worktree and confirm the run's constraints hold.
  - Accept: `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift` and `python3 gates.py && python3 gates.py --selftest` each exit 0 with the output quoted; `git diff --name-only origin/main` lists no file under `factory/templates/**` or a mirrored root file (so no `factory_init.py update-manifest` is owed), no `.claude-plugin/plugin.json`, and no `polish` file; no `claude plugin eval`, `trigger_eval.py`, `charter_replay.py` or `claude -p` was run.
  - Blocked by: Interface row; Credit lines

## Design gaps found

none.

## Notes

<!-- Deviations discovered during Implement are logged here, dated. -->
