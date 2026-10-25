---
stage: capture
run: maintenance:a-sketch-drawn-from-memory
date: 2026-10-25
re-entry: implement
intake: #1093
---

# Defect: ux-design sketches from memory, checks scenarios last, and grades its own work

## Defect (or Condition)

`skills/ux-design/SKILL.md` runs interview, then sketch, then write `ux.md`.
Three checks are missing, and on a real run each one let a defect into a
committed `ux.md`:

1. **Code facts.** Nothing tells the designer to read the code behind an
   existing surface before sketching it, so an existing screen gets drawn
   from memory or assumption.
2. **Scenarios first.** Flows are designed and then, if at all, checked
   against hard scenarios. Nothing makes the artifact prove that each hard
   scenario can be done with only the controls the doc itself defines.
3. **Independent review.** The only check before hand-off is "confirm each
   sketch with the user". Nobody reads the finished doc without the
   designer's framing.

Expected: each existing surface a flow changes is grounded in recorded code
facts. The hardest scenarios are written as walkthroughs before the flows
and pass against the final doc. A reviewer with no stake in the doc (or a
labelled inline fallback) reads it before the commit, and each finding is
fixed or recorded.

## Reproduction / Evidence

From intake #1093, filed 2026-10-25, consumer repo `mattbutlerengineering`,
run `docs/features/venue-availability/`:

- "Five confirmed wireframes rested on wrong assumptions about current code:
  the staff booking form (free time input, never calls availability), SMS
  (cancellations are email-only), the `Calendar` component (no per-day
  content), roles (unenforced), and guest manage links (they point at the
  site root, a live defect). These were caught only because the Owner asked
  'double check'."
- "An independent audit walked six hard scenarios through the committed
  `ux.md`: 3 could not be done (summer hours from a date, one occurrence of
  a recurring closure, one setting across many templates) and 3 had gaps."
- "A second fresh reviewer found 8 High issues in the revised doc (sketch
  contradicting its flow, the demo's key moment hidden behind a step,
  vocabulary drift)."

The committed `ux.md` there (`f352aa4e4`, #7536) is the hand-repaired doc. It
already has `## Scenario walkthroughs`, `## Voice & terms` and `## Dependencies
surfaced for Architect` sections that the skill's `TEMPLATE.md` does not have.
That is the shape a fixed skill should produce without the Owner having to
ask for it.

Static reproduction in this repo: `skills/ux-design/SKILL.md` (53 lines on
`98b220e`) has no step that reads code, no scenario walkthrough and no
reviewer; `skills/ux-design/TEMPLATE.md` has no section for any of the three.
The regression test pins their presence.

## Root-cause hypothesis

Hypothesis: the skill treats the user's confirmation as the only check.
"Confirm each sketch with the user" checks taste, not truth. The user
confirms a sketch of code they also have not re-read, so code facts and
scenario completeness have no owner in the stage. The one coverage rule
("every user story ... reachable through some flow") checks reachability,
not whether a scenario can actually be finished.

## Blast radius

Every plugin user whose run has `ux: required`, since the stage shipped. A
wrong `ux.md` flows into Architect and Decompose as settled design, so the
cost is a later audit or rework, not a crash. In this repo, `pipeline-board`
and `process-dashboard` ran the stage. Neither was audited for this, and
this run does not re-audit them. The fix reaches installed caches only after
the wave's version bump (ADR-0095).

## Ruled out

- Already in flight: no open PRs. The two unmerged branches touching
  `skills/ux-design/` (`feat/943-commit-stage-artifacts-at-boundary`,
  `feat/ux-writing-and-ux-patterns`) carry the commit-at-boundary and
  ux-patterns edits already on main, and neither adds code facts, scenarios
  or review.
- Making `ux-patterns` a gate: the Owner chose a one-line suggestion. The
  stage proceeds whether or not `docs/ux-patterns.md` exists.
- A shared independent-review pattern across stages (an Architect question):
  out of scope. This run fixes ux-design only.

## Work items

- [x] **Regression test first** — add `tests/test_ux_design_grounding.py`
  pinning, through the skill and template text, each item below. Run it red
  against `98b220e`'s text.
  - Accept: the new module fails on `main` and passes after the items below,
    and `python3 -m unittest tests.test_ux_design_grounding` exits 0.
- [x] **Code facts before sketches** — in SKILL.md, before Sketch: for each
  existing surface a flow changes, read the code that implements it today and
  record the facts (file, what it does now) in `ux.md`. Never sketch an
  existing surface from memory. TEMPLATE.md gains a `## Code facts` section.
  - Accept: SKILL.md names the step and its "never from memory" rule; the
    template has the section; the test pins both.
- [x] **Walkthroughs first** — in SKILL.md, before the flow interview: pick
  the hardest scenarios from `idea.md` / `prd.md` and write each as an
  acceptance walkthrough. Before finishing, each walkthrough must complete
  using only controls the doc defines, and one that cannot is a gap to fix
  or record. TEMPLATE.md gains a `## Scenario walkthroughs` section.
  - Accept: SKILL.md orders walkthroughs before flows and states the
    "only controls the doc defines" rule; the template has the section; the
    test pins both, including the order.
- [x] **Independent review before hand-off** — in SKILL.md, before Hand off:
  dispatch a fresh reviewer given the files (prd.md, ux.md, the code paths
  in Code facts), not the designer's conclusions, asked for Critical and High
  findings only. Fix or record each one before committing. Without fresh
  agent contexts, the designer re-reads ux.md cold against the walkthroughs
  and code facts and records `review: inline, not independent`. TEMPLATE.md
  gains a `## Review` section recording which review ran and each finding's
  disposition.
  - Accept: SKILL.md names the files-not-conclusions rule, the
    Critical/High scope and the labelled inline fallback; the template has
    the section; the test pins all three.
- [x] **ux-patterns suggestion** — in the interview's conventions bullet:
  when `docs/ux-patterns.md` is absent, suggest running `ux-patterns` first,
  as a suggestion only; the stage proceeds either way.
  - Accept: SKILL.md carries the suggestion and says it is optional; the
    test pins it.
- [x] **Checks green** — `python3 run_tests.py`, `python3 lint.py`,
  `python3 kb.py drift`, `python3 gates.py && python3 gates.py --selftest`.
  `plugin.json`'s `version` stays untouched (ADR-0095).
  - Accept: each prints 0 problems and the selftest prints ok.

## Notes

- 2026-10-25: re-entry `implement` by Owner answer; the two design calls
  (item 4 as a suggestion, labelled inline fallback) were made in the
  capture interview, so Architect has nothing to decide.
- A live run of the revised stage is a paid model run and is not part of
  Verify here; the phrase-pinning tests show the text is present, not that a
  designer follows it.
