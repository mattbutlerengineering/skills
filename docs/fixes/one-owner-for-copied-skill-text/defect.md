---
stage: capture
run: maintenance:one-owner-for-copied-skill-text
date: 2026-10-25
re-entry: implement
---

# Condition: copied skill text with no owner

## Defect (or Condition)

Three passages of skill prose are held in two places each, with nothing
but a human's memory keeping the copies in step, and one numbered list
is misnumbered:

- `skills/audit/SKILL.md` step 1 and `skills/automate/SKILL.md` step 1
  carry the same recon text: name the absolute root and the short HEAD
  in the report's first two lines, run `gh pr list --state open` and
  `gh issue list --state open --limit 50`, the cloud-session REST
  fallback paragraph (word for word), and the rule that what an open PR
  already does "is not a finding — it is a duplicate of work in flight".
- `skills/automate/SKILL.md` step 7 says "the ladder is `audit`'s" and
  then restates audit's step-6 routing ladder and its
  dedupe-before-append rule, in slightly different words.
- `skills/animated-diagram/references/design-system.md` and
  `skills/interactive-architecture-diagram/references/design-system.md`
  carry the same dark palette (canvas, text tiers, fonts, the seven
  architecture node types — about 27 identical lines), held together by
  the instruction "change a color in one place and match it in the
  others".
- `skills/work-queue/SKILL.md` step 4's agent-prompt list runs 1–8 and
  then numbers its ninth item "6.".

Target state: each shared passage has one owner file; every consumer
cites the owner's path and keeps only what differs for it; the
keep-in-step instruction is gone because there is nothing left to keep
in step; the work-queue list numbers 1–9; and a regression test fails
if a moved passage is copied back.

## Reproduction / Evidence

- The REST fallback paragraph is audit `SKILL.md:43-48` and automate
  `SKILL.md:56-61`, byte-identical.
- "duplicate of work in flight" appears at audit `SKILL.md:50-51` and
  automate `SKILL.md:63-64`.
- "the default for anything worth remembering and not worth a run
  today" appears at audit `SKILL.md:153-154` and automate
  `SKILL.md:182-183`; "the dedupe happens before the write, not after"
  at audit `SKILL.md:167-168` and automate `SKILL.md:191`.
- The storage node row ``| storage | cache / object / block store |
  `#39c5cf` | ...`` is animated-diagram `design-system.md:63` and
  interactive `design-system.md:53`; the keep-in-step instruction is
  animated `design-system.md:3-8` and interactive `design-system.md:3-5`.
- `skills/work-queue/SKILL.md:99` reads `6. **Say what it doubts.**`
  after item 8 at line 97.

The first work item's test is the executable reproduction.

## Root-cause hypothesis

Each second copy was written by copying the first when the second skill
was authored (automate after audit; interactive after animated, or the
reverse), and the sibling-reference mechanism that lets one skill cite
another's `references/` file (`lint.SIBLING_ASSET`, precedent
`skills/pipeline-board/SKILL.md:18`) either did not exist yet or was not
reached for. The misnumbered "6." came from #597 appending an item to a
list without renumbering.

## Blast radius

Skill prose only — no code path, no gate, no payload file. The cost is
drift: an edit to one copy (a new cloud fallback, a new palette colour)
silently leaves the other stale, and an agent reading the stale skill
acts on it. No user-visible behaviour changes in this run; meaning is
preserved, only ownership moves. Review and Ship scale small.

## Ruled out

- **A shared module or generated text.** Skills are markdown an agent
  reads; the existing sibling-reference precedent is the lighter tool,
  and lint already checks a sibling reference named from `SKILL.md`.
- **Moving the report-section wording too** ("Considered and not worth
  doing", the coverage statement). Each skill's version names its own
  categories and report sections, so the wording differs in substance;
  they stay with their skills.
- **The architecture-diagram palette.** It is the light family's token
  table with a dark column, not a copy of the dark palette; its
  "change a color in one place and match it in the other" refers to its
  own `assets/boilerplate.svg`, not to the dark copy. Left alone.
- **`skills/implement-queue/SKILL.md:98-101`.** It shares the
  "dropping every entry that carries a `pull_request` key" clause but
  queries a different endpoint for a different purpose; not a copy of
  the recon passage.

## Work items

- [x] **Regression test** — `tests/test_skill_shared_references.py`:
  for each moved passage a distinctive sentence occurs exactly once
  across owner and consumer files (counted, whitespace-normalised),
  lives in the owner, and each consumer cites the owner's path.
  - Accept: the test fails on the current text, before any move.
- [x] **audit/automate recon** — shared recon, in-flight check and REST
  fallback move to `skills/audit/references/recon.md`; the routing
  ladder and dedupe rule to `skills/audit/references/routing.md`; audit
  cites its references, automate cites `../audit/references/recon.md`
  and `../audit/references/routing.md` and keeps only what differs.
  - Accept: the recon and routing cases of the test pass; meaning of
    both skills unchanged.
- [x] **Diagram dark palette** — animated-diagram's design system owns
  the dark palette; interactive's cites
  `../../animated-diagram/references/design-system.md` for it and keeps
  its own rules; the keep-in-step instruction leaves both.
  - Accept: the palette case of the test passes; no "match it in the
    other" wording remains in either dark design-system file.
- [ ] **work-queue numbering** — the ninth agent-prompt item is
  numbered 9.
  - Accept: `skills/work-queue/SKILL.md` step 4's list numbers 1–9 in
    order, and nothing cites a step-4 item by its old number.
- [ ] **Checks green** — `python3 run_tests.py`, `python3 lint.py`,
  `python3 kb.py drift`, `python3 gates.py && python3 gates.py
  --selftest`.
  - Accept: each exits 0 with its clean output line.

## Notes

- 2026-10-25: the Owner approved this scope in session today. No
  intake issue seeds the run. No skill `description:` frontmatter and
  no `.claude-plugin/plugin.json` change is in scope (ADR-0095).
