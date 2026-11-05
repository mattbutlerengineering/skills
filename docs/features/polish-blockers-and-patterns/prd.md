---
stage: prd
run: feature:polish-blockers-and-patterns
date: 2026-11-04
id: PRD-0019
ux: not-applicable
ux-reason: the deliverable is skill text and a lint or test pin; no screen or flow is designed (autorun brief, User-facing surface)
assumptions:
  - "ux: not-applicable follows the brief's User-facing surface section, which says the deliverable is skill text with no screen."
  - "Interview answered from the autorun brief and idea.md; the brief is the only source of answers. No question needed a skill-supplied default."
  - "Typed id PRD-0019 is the one the brief reserved for this run."
  - "The README credits paragraph and the credit line in polish are in scope because the brief's Scope names both."
---

# PRD: named blockers and code detection patterns in polish

## Problem statement

A person running `polish` on a UI gets a ranking "by who is locked out" with
no named set of what locks people out. Step 5's accessibility floor has six
items, and eight known blockers sit outside it. When nothing renders, the
code-only reading that step 6 requires has no patterns to look for, so it
finds little. Today the reviewer's own judgement supplies both the severity
order and what to grep for. No observed miss is recorded; the gap is read
from `polish`'s own text against an external practitioner's lists
(jakubkrehel/skills, MIT).

## Solution

When this ships, `polish` names its blockers: the floor plus eight more,
each high severity on sight, so "ranked by who is locked out" is checkable.
The list sets severity and adds no rules. `inspect` also carries a
framework-neutral table of 10 to 15 detection patterns, each a
grep-able code shape, with a WCAG 2.2 criterion id on every accessibility
row. Both are restated in this repo's words, with a credit line in `polish`
and in the README credits paragraph. The skill's description is unchanged.

## Actors

- **Plugin user** — a person who runs `polish` on a UI, rendered or code-only, and reads its ranked findings.
- **Reviewer agent** — the model following `polish`'s steps, which ranks findings and does the step 6 code-only reading.
- **Maintainer** — the Owner or contributor who edits `polish` and must keep its shape, credits and checks green.

## User stories

1. As a plugin user, I want `polish` to rank findings against a named list of blockers, so that I can check why one finding outranks another.
2. As a plugin user, I want the code-only reading to flag known risky code shapes, so that a run with nothing rendered still finds something.
3. As a reviewer agent, I want the severity order and a pattern list written in the skill, so that I do not recall or invent them.
4. As a plugin user, I want each accessibility pattern to carry its WCAG 2.2 criterion id, so that I can look the rule up.
5. As a maintainer, I want the external source credited and its text restated, not copied, so that the repo's attribution stays honest.
6. As a maintainer, I want the skill's description unchanged and the battery green, so that no routing eval is owed.

## Success criteria

- [ ] `skills/polish/SKILL.md` step 5 names the eight added blockers (loss at 320px or 200% zoom; meaning carried by color alone; a destructive action with no confirm or undo; truncation with no way back; content hidden past a scroll edge with no cue; an error naming no recovery; a semantic color used against its meaning; a state change carried by motion alone) beside the existing six floor items, and states each is high severity on sight. A reader can count 14 named blockers.
- [ ] `inspect`'s ranking in `skills/polish/references/moves.md` ranks the named blockers first.
- [ ] The blocker text sets severity only: it adds no new rule or step, and the step count in `SKILL.md` is unchanged.
- [ ] `inspect` in `skills/polish/references/moves.md` carries a pattern table of 10 to 15 rows, placed beside its existing thresholds.
- [ ] The table includes at least these shapes: `outline: none` with no `:focus-visible` replacement; a click handler on a non-interactive element; a positive `tabindex`; `maximum-scale=1` or `user-scalable=no`; an assertive live region on a success message; a submit button disabled until valid.
- [ ] No row names a framework, library or framework-only attribute as its only form; each row is expressed in plain HTML, CSS or ARIA terms.
- [ ] Every accessibility row carries a WCAG 2.2 success criterion id, and each id was checked against the WCAG 2.2 text. An id that cannot be checked is marked unverified in the row, not stated as fact. The implementer records the check in the verification evidence.
- [ ] A credit line to the external source appears in `skills/polish/` and in the README credits paragraph, worded the way `polish` credits Impeccable. No sentence is copied from the source; the text is restated.
- [ ] The `description` in `skills/polish/SKILL.md` frontmatter is byte-identical to its value on `origin/main` at `eff46d2`.
- [ ] A test or lint check pins the shape added: the eight blockers are present in `polish`, the pattern table row count is within 10 to 15, and every accessibility row has a criterion id. If no stdlib check can pin one of these, the architecture note says which and why.
- [ ] `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift` and `python3 gates.py && python3 gates.py --selftest` pass from the worktree.
- [ ] The cheapest kill test (run `polish` code-only on a real UI file set before and after, and compare what it names) is recorded NOT RUN with its exact command for the Owner, because it needs a model run and the brief allows no spend.

## Out of scope

- Research item 5 (emoji, unbreakable strings and tall scripts in `states`, and the "name the dropped axes" rule). It stays in the research note.
- Any change to `polish`'s frontmatter `description`, which would owe a routing eval.
- Any `review` change; the `review-interface-pass` run owns it.
- A scanner that runs the pattern table over a source tree (the Moonshot rung); seeded to the backlog by Idea, not built here.
- Moving LEDGER maturity, or any paid eval run.
- Turning `polish` into a checklist: the lists set severity and give grep targets, and add no pass or fail gate.

## Open questions

- Which WCAG 2.2 criterion id fits each accessibility row, and does the text of the criterion support it? — the implementer, checking against the WCAG 2.2 text; the PRD fixes the rule, not the ids.
- Whether the shape pin is a test, a lint rule, or both — the Architect.
- Whether the credit line sits in `SKILL.md` or in a reference file under `skills/polish/` — the Architect.
