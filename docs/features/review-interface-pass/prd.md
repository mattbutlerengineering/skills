---
stage: prd
run: feature:review-interface-pass
id: PRD-0018
date: 2026-11-04
ux: not-applicable
ux-reason: "Skill text only (a domain-table row and a reference); no screen or user-facing surface."
assumptions:
  - "ux: the brief's User-facing surface section reads the deliverable as skill text with no screen, so ux is not-applicable; the Owner was not asked separately."
  - "The interview is answered from the autorun brief and idea.md; no live questions were asked. Actors, user stories and success criteria are the orchestrator's reading of the brief's Idea inputs and Success statement."
  - "The brief names no measure for false positives, so none is invented; the PRD states the criterion as an outcome on fixture diffs hand-walked, not a rate."
  - "Typed id PRD-0018 is the one the brief reserved for this run."
---

# PRD: An Interface domain pass for review

## Problem statement

<!-- coverage-waiver: context for the requirements below, not a deliverable; the run has no tracker mirror (brief, Tracker), so no breakdown row carries a WO id for the gate to count -->

When a pipeline run changes interface code, nothing in `review` looks at
it. No domain pass covers UI paths and the skill never mentions
accessibility. A deleted `aria-label` or focus style is invisible in the
post-change state, so a reviewer reading the changed file sees nothing
wrong and the loss ships. Adopters whose repos have a UI cope with
`polish` (run on demand against a rendered surface, not the diff) or with
nothing. Evidence: a coverage gap seen in this repo (three domain rows, none
for interface paths) and an external practitioner's method; the pass is
unmeasured on real diffs because no adopter UI diff was available.

## Solution

<!-- coverage-waiver: narrates the deliverables the Success criteria list; the run has no tracker mirror (brief, Tracker), so no breakdown row carries a WO id for the gate to count -->

`review` gains an Interface domain pass. When a changed path is a UI path,
the reviewer runs it: it reads the removed side of every hunk for deleted
accessibility and rendering signals, clears a signal whose equivalent
replacement is on the added side, and reports what is left with a status
by cause. A diff with no UI path does not select it. The skill's
description is unchanged. The source of the method is credited in the
skill and in the README credits paragraph.

## Actors

<!-- coverage-waiver: names who is involved; no actor is itself something to build -->

- **Reviewer** — the agent (or person) running `review` on a change.
- **Author** — whoever wrote the diff under review and reads its findings.
- **Adopter maintainer** — owns a repo with a UI that uses the pipeline.
- **Skill maintainer** — maintains this repo's skills, docs and checks.

## User stories

<!-- coverage-waiver: the stories motivate the Success criteria, which the breakdown's Accept lines check; the run has no tracker mirror (brief, Tracker), so no breakdown row carries a WO id for the gate to count -->

1. As a Reviewer, I want a domain pass that is selected when a diff changes UI paths, so that interface changes get looked at.
2. As a Reviewer, I want the pass to read the removed side of each hunk, so that a deleted `aria-label` is found though the changed file reads fine.
3. As an Author, I want a removed signal that has an equivalent on the added side cleared before anything is reported, so that a refactor that kept the signal is not flagged.
4. As an Adopter maintainer, I want each finding to carry a status by cause, so that I can tell what this change introduced from what was already there.
5. As a Reviewer, I want the pass not to run on a diff with no UI paths, so that it costs nothing there and readers do not learn to skip it.
6. As a Skill maintainer, I want the new table row and the reference pinned by an offline check and credited to the source, so that the domain table cannot drift and the method's origin is on record.

## Success criteria

<!-- coverage-waiver: every breakdown item's Accept line checks these criteria, but the run has no tracker mirror (brief, Tracker), so no row carries a WO id and the gate cannot count the citation -->

- [ ] `skills/review/references/domain-reviewers.md` has an Interface row, selected by UI paths (`*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.css`, `*.scss`, templates), that links a new reference under `skills/review/references/`. How "templates" is bounded is decided in Architect. A person reading the table finds the row and the link resolves.
- [ ] The new reference tells the reviewer to read the removed side of every hunk for each of these signals: `aria-label`, `alt=`, `:focus-visible`/`outline`, `tabindex`, `prefers-reduced-motion`, logical properties, `lang=`/`dir=`, a token swapped for a literal.
- [ ] The reference says to clear a removed signal when an equivalent replacement exists, and names the limit: a replacement on a different selector or element does not clear.
- [ ] The reference gives every finding a status by cause (introduced, regression, pre-existing, or the set Architect settles on) and maps each status into `review`'s existing severity model without a new severity.
- [ ] Hand-walked over fixture diffs, the rules give these verdicts: a diff deleting `aria-label="Close"` from an icon button with no replacement reports a finding; a diff replacing `outline: none` with a `box-shadow` focus ring on the same selector reports nothing; the same swap on a different selector reports a finding. (The demo runs as written: before, a diff drops `aria-label="Close"` from an icon button and `review` says nothing; after, `review` lists a finding for that line and stays silent on a second hunk that replaces `outline: none` with a `box-shadow` focus ring on the same selector.)
- [ ] A changed-path list with no UI path selects no Interface pass, and the review reports "domain passes: none selected" for it (or the other passes' result if they match).
- [ ] The pass reads and reports on the diff only; it asks for no rendered page or browser.
- [ ] `skills/review/SKILL.md` and the README credits paragraph each carry a credit line for the source, restated in this repo's words with nothing copied; `NOTICE` is unchanged.
- [ ] `skills/review/SKILL.md`'s frontmatter `description` is byte-identical to its value on `origin/main`, so no routing eval is owed.
- [ ] The domain table is pinned by a stdlib test or lint check that fails when the Interface row or its linked reference goes missing, and the battery passes from the worktree: `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`, `python3 gates.py && python3 gates.py --selftest`.
- [ ] No paid model run is made; a criterion that would need one is recorded NOT RUN with its exact command.

## Out of scope

<!-- coverage-waiver: lists what is not built, so no breakdown row can cover it -->

- Rendered or browser checks (the Moonshot rung: comparing the accessibility tree and focus order before and after).
- Any change to `polish`; another run owns it.
- A change to any skill's frontmatter `description`.
- A script or other executable for the pass itself.
- A reviewer data rule (seed 1); #1141 already shipped it.
- Measuring false-positive rates on real adopter diffs; no such diff exists yet.
- Tracker seeding or work-order issues.

## Open questions

<!-- coverage-waiver: questions Architect answered in architecture.md; nothing to build -->

- How broad the selection globs should be: "templates" is vague, and the payments row is broad on purpose, so the row needs the same care — Architect.
- What counts as an equivalent replacement, beyond the same-selector `outline` to `box-shadow` case — Architect, tested by hand on fixtures.
- Which statuses by cause the reference uses and how each maps onto `review`'s severity levels — Architect.
- Where the line falls between `polish` (live surfaces) and this pass (the diff), so the two do not duplicate — Architect, with the polish run's owner at merge time.
- Whether offline fixture diffs are worth keeping as test data — Architect.
