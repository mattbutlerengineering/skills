---
stage: prd
run: feature:svg-mechanical-check
date: 2026-11-04
id: PRD-0020
ux: not-applicable
ux-reason: "Skill text and a stdlib check with text output only; no screens or flows."
assumptions:
  - "Interview answered from autorun-brief.md and idea.md in this directory; no live interview held. The brief's Idea inputs are the orchestrator's reading of the seed (backlog line 142) and the jakubkrehel research note, not Owner answers; the Owner's answers are 'do all of these in parallel', feature run, prepare and stop, operate skip, no tracker seeding."
  - "ux: not-applicable. The brief's User-facing surface section says None as the orchestrator reads it (the deliverable is skill text and, where named, a stdlib check, with no screen) and instructs PRD to record this reading. Taken as instructed, not an Owner answer."
  - "Typed id PRD-0020 is the id the brief reserves for this run's PRD."
  - "No interview question this stage offered named options with a recommended default that the brief left open, so no skill default was taken. The one evidentiary gap (which embed width the smallest-text reading uses, and how it handles a viewBox that does not scale to it) is not asked of the Owner: the brief itself lists it as an unknown to 'define what it reads and what it refuses', so it is parked in Open questions for Architect rather than guessed."
  - "Whether the check is an inline snippet or a shipped script, and whether any script joins the plugin payload, is left to Architect (brief: 'Architect's call'). Success criteria below describe observable behaviour only."
  - "Scaffold fix is in scope per the brief's Scope section (orchestrator's scope call): a skill whose scaffold fails its own check ships broken. Marking backlog line 91 claimed is a later stage's act, listed as a criterion so Verify can test it."
  - "Criteria needing a paid run (the routing eval, if a skill description changes) are not included: every seed here is body-only, so none is owed. If an Architect decision changes a description, the eval is recorded NOT RUN with its command."
---

# PRD: A mechanical SVG check for the diagram skills

## Problem statement

Someone generating a diagram with `architecture-diagram` or
`animated-diagram` checks the SVG by eye at step 7. Defects a parser
finds in a second (a duplicate id, a `url(#...)` that points at no id, an
external link, no intrinsic width and height) ship anyway and are found
later by hand, by someone looking at the rendered page. Observed in this
repo's own artifact: the readme-skill-map run hand-fixed a missing root
width/height and 8 to 9px text tiers, and the `architecture-diagram`
scaffold `assets/boilerplate.svg` still carries a viewBox and no root
width/height, so inside an `<img>` it is fitted to the browser's 300x150
default (backlog line 91). How often users of the two skills hit these
defects is unobserved.

## Solution

Step 7 of `architecture-diagram`, and the pure-SVG path of
`animated-diagram`, tell the generator to run a mechanical check over the
SVG it produced before declaring it done. The check parses the file with
the standard library only. On a defective file it fails, exits non-zero
and prints one named line per defect. On a clean file it passes and
reports the smallest text size at README embed width. It refuses an SVG
that declares a DTD or entity rather than parsing it. The
`architecture-diagram` scaffold passes its own check.

## Actors

- **Diagram generator** — the person (or agent) running `architecture-diagram` or `animated-diagram` to produce an SVG, who reaches step 7 and needs to know the file is sound before it ships.
- **Skill maintainer** — whoever edits these two skills or their scaffolds, who needs the scaffold and check to stay consistent and tested offline.
- **README reader** — sees the diagram embedded at README width; gets a correctly sized, self-contained, legible image.

## User stories

1. As a diagram generator, I want step 7 to name each duplicate id, dangling `url(#...)`, external `href` and missing root width/height in my SVG, so that I fix them before the file ships instead of finding them in the rendered page.
2. As a diagram generator, I want a clean SVG to pass and tell me its smallest text size at README embed width, so that I can see whether the smallest tier is legible without rendering it.
3. As a diagram generator on the animated path, I want the check not to misreport SMIL and CSS references as defects, so that a correct animated SVG is not blocked.
4. As a skill maintainer, I want the check refused on DTDs and entities and tested against fixtures offline, so that it never becomes an attack vector and no test needs a model or the network.
5. As a skill maintainer, I want `architecture-diagram`'s scaffold to pass the check, so that the skill does not ship a scaffold that fails its own step 7.
6. As a README reader, I want a diagram with an intrinsic width and height, so that it is not fitted to the 300x150 default inside an `<img>`.

## Success criteria

- [ ] Given a fixture SVG with a missing root width/height, a duplicate id, a dangling `url(#...)` and an external `href`, the check exits non-zero and its output names each of the four defects on its own line, with the offending id, reference or URL where one exists.
- [ ] Given a fixture with exactly one of the four defects, the check exits non-zero and names only that defect (four single-defect fixtures, four passes).
- [ ] Given a clean fixture SVG, the check exits zero and its output states a pass and the smallest text size at the embed width it used, in pixels, with that embed width stated in the output.
- [ ] Given a fixture that declares a DTD or an entity (an entity-expansion payload and an external-entity payload), the check exits non-zero with a refusal that names the DTD or entity, and the test shows the payload was not expanded.
- [ ] Given a clean animated fixture using SMIL (`begin="<id>.end"`, `<use href="#id">`) and one using CSS (`animation` and `url(#...)` in a style), the check exits zero; given the same fixtures with one referenced id removed, it exits non-zero and names the dangling reference.
- [ ] Given a fixture with an external `href` or `xlink:href` (any value not starting with `#`), the check fails; given one whose only `href` values are same-document `#id` fragments, it does not.
- [ ] The check uses the Python standard library only, and is invoked under `python3 -I`.
- [ ] The tests for the check run offline, with fixture SVGs committed to the repo, and are picked up by `python3 run_tests.py`; no test calls a model or the network.
- [ ] `skills/architecture-diagram/SKILL.md` step 7 and the pure-SVG path of `skills/animated-diagram/SKILL.md` each instruct running the check and say what a failure means for the file; the by-eye inspection is no longer the only step-7 verification for the four defects.
- [ ] `skills/architecture-diagram/assets/boilerplate.svg` carries a root width and height, and the check passes on it unmodified.
- [ ] The `animated-diagram` scaffold, if the skill has one, passes the check; if it fails, either the scaffold is fixed or the failure is recorded as a seed in `docs/backlog.md`.
- [ ] Backlog line 91 (the boilerplate's missing width/height) is marked claimed by `feature:svg-mechanical-check` in `docs/backlog.md`.
- [ ] If the check is a script inside a skill directory, it lands in the plugin payload only as the repo's packaging rules (`python3 lint.py` and the factory manifest) require, and `python3 lint.py` and `python3 factory_init.py update-manifest` leave no finding or drift.
- [ ] Run from the worktree, `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift` and `python3 gates.py && python3 gates.py --selftest` all pass.
- [ ] No skill frontmatter `description` changes. If one does, the routing eval is recorded NOT RUN with its exact command, for the Owner.
- [ ] Running the check over the README skill map prints its result; any defect it finds there is recorded as a seed in `docs/backlog.md`, and the skill map file is unchanged.

## Out of scope

- Rasterizing the diagram or any browser-based check (the Moonshot, seeded at backlog line 161).
- `interactive-architecture-diagram` (HTML, not SVG).
- Redrawing or editing existing diagrams such as the README skill map; defects found there become a seed.
- Mechanical checks of properties beyond the five named (duplicate ids, dangling `url(#...)`, external `href`, root width/height, smallest text at embed width): contrast, overlap, layout and accessibility stay by eye.
- Any change to a skill's frontmatter `description`, any paid model run, any LEDGER maturity move, and any tracker work beyond the single issue Ship files.

## Open questions

- Which embed width does "smallest text at embed width" use (a fixed README width, or an argument with a default), and what does it do when the viewBox and root width/height give inconsistent scales or the text size is in non-pixel units or inherited? The brief says to define what it reads and what it refuses. — Architect.
- Is the check an inline `python3 -I -c` snippet in each skill or a shipped script, and does a script belong in the plugin payload under lint and the factory manifest? — Architect, after reading the packaging rules.
- Which smallest-text threshold, if any, makes the check fail rather than only report? The seed says "read", not "fail on"; this PRD treats it as a report. — Architect, with the Owner if a floor is wanted.
- Do `animated-diagram`'s CSS and SMIL references need more cases than `begin="<id>.end"`, `<use href>` and `url(#...)` in a style? — Architect, from the skill's own animation patterns.
