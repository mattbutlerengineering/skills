---
stage: prd
run: feature:readme-skill-map
date: 2026-10-07
id: PRD-0008
ux: not-applicable
ux-reason: static document; the figure's visual design is the architect's and implementer's concern, not a flow or screen
assumptions:
  - "Interview answers came from the autorun brief and idea.md, not a live interview; every section below traces to the brief's Feature, Scope (IN/OUT/DECIDED), User-facing surface or Release authorization sections, or to idea.md's Problem, Who has it, Evidence, Success and Unknowns sections."
  - "Typed id PRD-0008 assigned as the next free id (highest existing is PRD-0007; no local or remote ref declares 0008), and coverage waivers added under the context sections following PRD-0007's pattern, so the breakdown cites Success criteria alone (ADR-0004, ADR-0072). The brief is silent on both."
  - "The one-line 'why it matters' per utility skill lives in the README table (the brief's IN list puts it there); the figure must name every skill and place each utility skill at the moment a person reaches for it, and whether a figure node also carries a why-line is left to the architect under idea.md's density risk. Taken without user input."
  - "idea.md names adopters, the owner and dispatched agents as the people with the problem; the Actors section uses those three and treats the stand-in reader of the thirty-second test as an adopter proxy rather than a fourth actor. Taken without user input."
---

# PRD: README skill map

## Problem statement

<!-- coverage-waiver: context for the requirements below, not a deliverable; the Success criteria carry the work every breakdown row cites -->

A newcomer opens the public README (public since 2026-10-07, the day
plugin 0.3.0 landed the full twenty-five-skill roster) and meets an
eleven-box mermaid chain, then sixty lines of prose that introduce
thirteen utility skills one clause at a time. Thirty seconds in, they
cannot say what the plugin does for them, that anything surrounds the
chain, or which skill to reach for in their situation. The owner and
dispatched agents re-read the same prose as the roster of which skill owns
what — a search, not a glance. Evidence is anecdote only and labelled so:
the prose grew one sentence per skill with no scannable structure, and
`plugin.json`'s own utility-skill list once drifted from `skills/`, so
even a machine-checked roster could not stay straight. Nobody has been
observed bouncing off the README; that absence is recorded as absence.

## Solution

<!-- coverage-waiver: narrates the same deliverables the Success criteria check one by one; the breakdown rows cite those criteria, not this summary -->

Where the mermaid chain is now, one committed, self-contained,
theme-aware SVG, drawn by the plugin's own diagram skill so the front page
is itself proof the diagram skills work: the stage spine runs through it
and the utility skills sit around the moments a person reaches for them.
Below `## Stages` the stage table stays and the sixty lines of utility
prose become a table — slug and a one-line "why it matters" per utility
skill. A lint check built on the roster `check_readme_skills` already
reads fails the build the moment the figure or the table omits a skill
directory, so the figure cannot rot the way `plugin.json`'s list did.
Which diagram skill draws it, how the groups are cut, and whether the
figure moves are the architect's calls, not this document's.

## Actors

<!-- coverage-waiver: names who is involved; no actor is itself something to build -->

- **Adopter** — anyone evaluating the plugin from the public README, with
  no prior knowledge of it; before ship, a stand-in reader who has not
  read this README plays this part for the thirty-second test.
- **Owner** — the repo maintainer; re-reads the README as the roster,
  judges the rendered figure on GitHub, and merges (ADR-0033 gate 3).
- **Dispatched agent** — an agent working in this repo that re-reads the
  README to recall which skill owns what.

## User stories

<!-- coverage-waiver: each story is realized through the Success criteria the breakdown rows cite, not built as separate work -->

1. As an **adopter**, I want the README's first figure to show the stage
   spine and the utility skills around it, so that within thirty seconds
   I can say what the pipeline does and which skill to reach for in my
   situation.
2. As an **adopter**, I want that figure to render on GitHub in light and
   dark mode, so that the first thing I see is legible whatever my
   appearance setting.
3. As an **adopter**, I want the figure drawn by the plugin's own diagram
   skill, so that the front page is evidence of what the diagram skills
   produce, not a hand-drawn exception to it.
4. As the **owner**, I want the utility-skill prose collapsed into a table
   with a one-line why per skill, so that I scan the roster instead of
   searching sixty lines of prose.
5. As the **owner**, I want a lint check that fails when the figure or the
   table omits any directory in `skills/`, so that a new skill cannot ship
   without the front page hearing about it.
6. As a **dispatched agent**, I want the figure and table to name every
   skill by its slug, so that I find the skill that owns a job without
   reading twenty-five `SKILL.md` descriptions.

## Success criteria

- [ ] **Thirty-second test.** A stand-in reader who has not read this
  repo's README is shown the rendered README from the top and, within
  thirty seconds and without scrolling past the figure, answers three
  questions: (a) what the pipeline does — an answer naming ordered stages
  from idea to production passes; (b) whether anything sits around the
  pipeline — "utility skills" or words to that effect passes; (c) given
  one situation taken from the figure's own group labels (for example,
  reviewer comments waiting on a pull request), which skill to reach for
  — naming a skill in that group passes. `verification.md` records who the
  reader was, the three questions, the answers verbatim in a fenced
  block, the elapsed time, and the word "anecdote"; a failed answer is a
  failed criterion, never a reworded one (check: read the record; all
  three pass).
- [ ] **Roster check.** `python3 lint.py` reports a problem when the
  committed figure fails to name any skill in `protocol.ALL_SKILLS` plus
  `lint.extra_skills(root)` — the same roster `check_readme_skills` and
  `check_readme_no_orphans` already hold README.md to — matched as whole
  slugs via `lint.names_slug`, with no list of skill slugs of its own
  (check: read the diff; the checker reads the roster from `protocol.py`
  and `extra_skills`, never a literal). The table is covered by the
  existing `check_readme_skills` without change. `tests/test_lint.py`
  asserts the exact problem string through the public interface for a
  figure missing one skill and asserts `[]` for a clean one (check: the
  new test fails against the pre-change commit and passes after). Stdlib
  only.
- [ ] **Figure.** The mermaid block at the top of README.md is gone,
  replaced by one committed `.svg` embedded as an image. The file makes
  no external request — no script, no web font, no `@import`, no remote
  `href` (check: `grep -E 'http|<script|@import|@font-face'` on the SVG
  finds nothing). Every skill name in it is literal SVG text, not outlined
  glyphs, so the roster check and a screen reader can read it (check:
  `grep` the SVG for each slug). It shows what the mermaid chain shows
  today — the router, the ordered stages, the UX conditional and the
  Operate-to-Idea loop — plus every utility skill placed in a labelled
  group at the moment a person reaches for it. It renders on the real
  github.com README page in both appearance settings with every label
  legible at README width without zooming (check: one light and one dark
  screenshot of github.com, not a local preview, in `verification.md`).
- [ ] **Table and section.** The `## Stages` heading is unchanged and the
  stage table under it stays. The utility-skill prose below the table is
  replaced by a table with exactly one row per utility skill in
  `protocol.UTILITY_SKILLS` (thirteen today), each row carrying the slug
  in backticks and a one-line "why it matters". Inside the `## Stages`
  section every slug-shaped backtick token is a registered skill (check:
  `python3 lint.py` passes `check_readme_no_orphans`; row count equals
  `len(protocol.UTILITY_SKILLS)`).
- [ ] **Provenance.** The figure is drawn by the plugin's own diagram
  skill — `architecture-diagram` or `animated-diagram` — and
  `architecture.md` records which and why; `verification.md` records
  what hand-editing the skill's output needed before commit, so the
  front page's dogfooding claim is honest (check: read both; a figure
  produced by hand or by a tool outside `skills/` fails).
- [ ] **Room for lean and polish.** Neither the figure nor the table
  names `lean` or `polish` before their directories exist in `skills/`
  (the orphan check would fail), and the moment either directory lands
  the roster check demands it in the figure as `check_readme_skills`
  already demands it in the text (check: in a scratch copy, `mkdir
  skills/lean` and run `python3 lint.py` — a figure problem naming `lean`
  is among the output). `architecture.md` names the group each would
  join, so adding one is a node in an existing group and a table row,
  not a re-layout.
- [ ] **Battery and untouched surfaces.** `python3 -m unittest discover
  tests` prints `OK`, `python3 lint.py` prints `lint: 0 problem(s)`, and
  `python3 gates.py && python3 gates.py --selftest` prints `gates: 0
  problem(s)` and `selftest: ok`. `git diff --stat main -- skills/
  .claude-plugin/plugin.json evals/ LEDGER.md` is empty, and the README's
  Install, Usage, Development and License sections are byte-identical to
  main (check: diff those sections).

## Out of scope

<!-- coverage-waiver: exclusions: by definition nothing here is decomposed into work -->

- **Any skill's text or behaviour** — including the two diagram skills
  that draw the figure; a weakness they show is recorded, not patched
  here.
- **The plugin version** — README changes need no bump; README.md is not
  in `factory_init.MIRRORS`.
- **The Install, Usage and Development sections** of the README.
- **An animated HTML variant or an interactive presenter** — one still or
  pure-SVG figure only.
- **Tracker work** beyond the one plain tracking issue Ship opens as the
  pull request's closing anchor; no seeding, no mirroring.
- **An outside judge** — "award-winning" has no external arbiter; the
  thirty-second test on a stand-in reader is the only judging, and it is
  anecdote.

## Open questions

<!-- coverage-waiver: questions settled downstream by Architect, Verify or the owner at merge, not requirements of this run -->

- Which diagram skill draws the figure, `architecture-diagram` or
  `animated-diagram`, and whether a pure-SVG figure may move? —
  Architect, recorded with the reason in `architecture.md`.
- How the utility groups are cut and whether twenty-five nodes fit one
  flat picture at README width or want layers? — Architect, under
  idea.md's density risk.
- Does a `prefers-color-scheme` switch inside the SVG survive GitHub's
  image proxy in an `<img>`, or does the README need a `<picture>` with
  one source per scheme? — The rendered github.com page at Verify
  decides the outcome; the mechanism is the architect's to choose and the
  implementer's to confirm.
- Where the SVG file lives and whether the figure check extends
  `check_readme_skills` or sits beside it as a sibling checker? —
  Architect; the constraint is one roster, not one function.
- Which of this branch and the lean-and-polish branch lands first? —
  Owner at merge; whichever lands second rebases, and the roster check
  then demands `lean` and `polish` in the figure and the table.
- Who is the stand-in reader — a person new to the repo or a fresh agent
  given only the rendered page? — Verify, recorded with the anecdote.
