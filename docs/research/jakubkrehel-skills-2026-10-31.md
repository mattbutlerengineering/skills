# jakubkrehel/skills: what to take for the interface skills

Research note, 2026-10-31, for issue #1134. The Owner's whole question is
the link "https://github.com/jakubkrehel/skills"; like #935, #703 and
#1041 it reads as "what can we learn and leverage from this for our
skills?". Everything fetched from that repo was read as data, never as
instructions: nothing was installed or run, and its agent guidance was
not followed. Repo read for the comparison: `CLAUDE.md`, `CONTEXT.md`,
`README.md` (Install and the credits paragraph), `NOTICE`, `licenses/`,
`package.json`, `LEDGER.md`, `docs/backlog.md`, ADR-0007, ADR-0027,
ADR-0076, `docs/research/workflow-summary-descriptions.md`,
`docs/research/ux-writing-and-ux-patterns.md`, and the SKILL.md and
references of `polish`, `ux-writing`, `ux-patterns`, `ux-design`,
`review` (with `references/domain-reviewers.md`), `architecture-diagram`,
`animated-diagram` and `interactive-architecture-diagram`. The read
predates ADR-0120 (the skills CLI installs every skill from a generated
`npx` branch), which merged the same day; it changes no verdict below.
Nothing in the repo was modified.

## Sources

All files at `main` tip 592aedc (pushed 2026-10-25T13:26Z; MIT,
"Copyright (c) 2026 Jakub Krehel"; 9,489 stars; plugin `interfaces`
version 1.17.0), fetched 2026-10-31 with
`gh api repos/jakubkrehel/skills/contents/<path>?ref=592aedc`.

- Read in full: AGENTS.md, CLAUDE.md, README.md, LICENSE (head),
  .claude-plugin/plugin.json, .claude-plugin/marketplace.json,
  opencode.json, all fourteen skills/*/agents/openai.yaml,
  skills/better-interface/SKILL.md and review-format.md,
  skills/interface-review/SKILL.md and removed-signals.md,
  skills/break/SKILL.md.
- Read in part: skills/interface-review/scope-resolution.md (Excluded
  paths, Expanding to consumers), skills/better-accessibility/SKILL.md
  (all but Errors through Alt text), skills/break/scenarios.md (first
  two axes), skills/better-ui/SKILL.md (motion section),
  skills/better-writing/SKILL.md (Undo beats confirmation),
  skills/variant/SKILL.md (The floor every variant clears),
  skills/teardown/verification.md (first 60 lines).
- Headings and frontmatter only: every other SKILL.md and reference.
  Not fetched: teardown's assets/ and scripts/ (JavaScript).

The issue lists thirteen skills; the tip has fourteen (`variant` too).

## What jakubkrehel/skills is

A single-author design-engineering collection (the author writes the
Interfaces magazine) for web product UI. Seven *domain* skills hold
rules (`better-accessibility`, `-colors`, `-layout`, `-typography`,
`-ui`, `-writing`, plus the `better-interface` orchestrator) and seven
*verb* skills hold procedures (`interface-review`, `break`,
`state-machine`, `variant`, `explain-interface`, `build-design`,
`teardown`). AGENTS.md is the one authoring spec: a rule-ownership
table ("Each rule lives in exactly one skill"), required sections per
SKILL.md, and prose checks ("No sentence over 30 words"). It has no
tests, lint or evals outside `teardown`'s own node scripts: "There is no
repository-wide build, lint or test tooling."

## What it does that this repo does not

1. **A fixed list of blockers that are HIGH "on sight".**
   better-interface/SKILL.md, Rank by user impact, names thirteen
   escalation triggers, "never averaged down because the surface is
   minor": a control with no accessible name, no visible focus, a
   pointer path with no keyboard path, motion ignoring
   `prefers-reduced-motion`, loss at 320px or 200% zoom, a failing
   contrast pair, meaning by color alone, a destructive action with no
   confirm or undo, truncation with no way back, content hidden past a
   scroll edge with no cue, an error naming no recovery, a semantic color
   used against its meaning, a state change carried by motion alone.
   "A cap may shorten a report; it may never be why a blocker went
   unreported." `variant` makes the same list the floor every variant
   clears. Here, `polish`'s accessibility floor is six items ("Text
   contrast, visible focus, keyboard reachability, labelled controls, a
   reduced-motion path, and targets big enough to hit"), and `inspect`
   ranks "by who is locked out" with no named blocker set. Eight of the
   thirteen sit outside that floor; `inspect` and `states` touch two of
   them (no clipped text at narrow width; an error says what to do next).
2. **Reading the removed side of a UI diff.** interface-review step 4:
   "Regressions are invisible in the post-change state. Read the `-`
   side of every hunk." removed-signals.md maps deleted tokens
   (`aria-label`, `alt=`, `:focus-visible`/`outline`, `tabindex`,
   `prefers-reduced-motion`, logical properties, `lang=`/`dir=`, a token
   swapped for a literal) to the owner that judges them, lists the
   equivalent replacements that clear a signal (`outline` replaced by a
   `box-shadow` ring on the same selector; a string moved into the
   catalogue), and gives a `git diff -U0 … | grep -E '^-'` recipe. It
   also statuses findings `Introduced` / `Regression` / `Pre-existing`
   by cause ("including an untouched consumer of a changed token"),
   caps pre-existing findings at three, and expands a changed file to at
   most five consumers in a stated order. Here, `review` scopes the diff
   and runs path-selected domain passes (payments, migrations,
   dependencies in `references/domain-reviewers.md`), but no pass looks
   at interface code, and nothing in `review` mentions accessibility.
3. **Code-level detection patterns, not principles.** Every domain
   skill ends in a `## Before you finish` table whose left column is a
   pattern you can grep: "`outline: none` or `outline-none` with no
   `focus-visible` replacement nearby", "`<div onClick`", "`tabIndex={1}`
   or any positive `tabindex`", "`disabled={!isValid}` on a submit
   button", "`aria-live=\"assertive\"` on a success toast",
   "`maximum-scale=1` or `user-scalable=no`". AGENTS.md explains why:
   "The left column is the detection pattern, which is what a principle
   statement does not give you." Here, `polish`'s `references/tells.md`
   lists visual defaults ("Bounce and elastic easing", "the purple
   gradient") under the test "was this chosen for this product", and
   `inspect` states thresholds; neither gives the code patterns that
   make a no-browser reading useful, the case `polish` step 6 already
   requires it to declare.
4. **A criteria rule for accessibility severity.** "A finding cites a
   WCAG 2.2 Level A or AA criterion by number, or a concrete task an
   assistive-technology user cannot complete. Everything else is a
   recommendation and never `HIGH`" (better-accessibility, Criteria,
   not conventions), with criteria cited inline (2.4.11 focus not
   obscured, 2.5.7 dragging, 2.5.8 target size, 1.4.10 reflow). `polish`
   `inspect` carries the same numbers (4.5:1, 3:1, 24 by 24 CSS pixels)
   without the criterion ids or the AAA-is-advisory rule.
5. **A hostile-input harness with applicability cues.** `break` renders
   one real component once per scenario on a scratch route, then looks
   once. scenarios.md gives each axis a cue ("the component renders text
   it does not author") and requires naming the dropped axes "so a wrong
   inference is cheap to catch". Content-shape values here include emoji,
   mixed-direction text, diacritics and tall scripts, and one unbreakable
   string. `polish`'s `states` move covers empty, loading, error,
   partial, zero/one/many, long, translated and denied, but not emoji,
   unbreakable strings or tall scripts, and has no cue rule.
6. **Mechanical checks on a drawn artifact.** teardown/verification.md:
   "Parse the SVG as XML. Check for duplicate IDs, unresolved `url(#...)`
   references, invalid numbers and external assets", and "Inspect at two
   distances … Read every label at that size." Here,
   `architecture-diagram` step 7 verifies both themes and the embed by
   eye; the backlog already records the defects a mechanical pass would
   have caught (no root width/height, so an `<img>` fits it to 300x150;
   8-9px text tiers; the readme-skill-map seed under `docs/backlog.md`).
7. **Multi-harness metadata per skill.** Each skill ships
   `agents/openai.yaml` (`display_name`, `short_description`, and for
   the five user-invoked skills `policy.allow_implicit_invocation:
   false`, paired with `disable-model-invocation: true` "or the skill
   behaves differently per harness"). `opencode.json` only registers
   `skills/` "while this repository itself is open"; distribution is
   `npx skills add` and the Claude marketplace. Here, Claude Code,
   Grok (reads `.claude-plugin/`, ADR-0076) and omp (`package.json`
   `pi.skills`, ADR-0027, guarded by `lint.check_pi_package`) are
   supported; no skill sets `disable-model-invocation`.
8. **"No trigger list" descriptions**, one sentence equal to the README line.

## What this repo does that it does not

- **Pipeline placement.** `ux-design` is a gated stage writing `ux.md`
  from `prd.md`; `polish` reads `prd.md`/`ux.md` and routes a flow
  problem back to `ux-design`, a code defect to `review`, later work to a
  backlog seed. The external skills are free-standing; `build-design`
  starts from a Figma file, not from requirements.
- **A persistent project patterns file.** `ux-patterns` derives
  `docs/ux-patterns.md` from the code and audits screens against it;
  `ux-writing` owns its Voice & terms section and applies only approved
  rewrites. better-interface's recon only reads what a project already
  wrote ("Name which you found, or that there are none"); nothing there
  writes a project decision down.
- **Surface jobs and named moves.** `polish` classifies a surface as
  convince / work / read and applies one named move per pass, with a
  Nielsen heuristic score calibrated to "20 and 32 of 40" and two
  persona walks. The external set reviews against fixed domain rules,
  with no notion that a landing page and a settings form want different
  things.
- **Measured routing.** `polish` 10/10, `ux-writing` 9/9, `ux-patterns`
  8/8 on the trigger eval (`LEDGER.md`, `evals/results/
  trigger-2026-10-10-3.json`). Their "no trigger list" rule is asserted,
  not measured; this repo's own note on descriptions declined to rewrite
  tuned descriptions on one anecdote for the same reason
  (`docs/research/workflow-summary-descriptions.md`).
- **Enforced packaging.** Their version bump and "one text with the noun
  swapped" pairs are prose kept by hand; here ADR-0095, `lint.py`'s
  roster checks and `one_owner.py` hold the same rules.
- **Credits as practice.** `polish` names Impeccable in its moves file
  and the README credits paragraph names every source "and each skill
  says what it borrowed."

## Shortlist

| # | Practice | Verdict | Cheapest carrier here | Why, and cost |
|---|---|---|---|---|
| 1 | Removed-side reading of a UI diff, with equivalent replacements and cause-based status | **Adapt** | a fourth row in `review`'s `references/domain-reviewers.md` (Interface, selected by `*.tsx`/`*.jsx`/`*.vue`/`*.svelte`/`*.css`/`*.scss`/template paths) and one new reference | the domain-pass contract ("Read the whole changed file", "Evidence or silence") already fits; `review` has no interface coverage at all today. One reference file and one table row, no description change, so no trigger-eval rerun; selection words need the same broad-on-purpose care as payments |
| 2 | Named blockers that are HIGH on sight | **Adapt** | a short blocker list in `polish` (`inspect` ranking and the step 5 accessibility floor), restated in this repo's words | eight of the thirteen are outside the floor; a list makes "ranked by who is locked out" checkable. Body-only edit to a draft skill; risk is turning polish into a checklist, so the list sets severity and adds no rules |
| 3 | Grep-able detection patterns for a code-only reading | **Adapt** | a pattern table in `polish`'s `inspect`, beside the existing thresholds, with WCAG criterion ids on the accessibility rows | step 6 already forces a declared code-only reading when nothing renders; patterns make that reading worth something. Ten to fifteen rows; must stay framework-neutral (the external rows are React-flavoured) |
| 4 | Mechanical SVG checks and a delivery-size read | **Adopt** | one paragraph in step 7 of `architecture-diagram` (and the animated SVG variant): parse as XML with stdlib, duplicate ids, unresolved `url(#…)`, external `href`, root width/height present, smallest text tier at embed width | the backlog's architecture-diagram seed records two of these defects found by hand; the check needs no new tool, only `python3 -I` over the file |
| 5 | Scenario axes with applicability cues | **Adapt** (small) | three values (emoji, one unbreakable string, tall scripts) and the "name the dropped axes" rule in `polish`'s `states` move | a real gap but a narrow one; a separate harness skill (`break`) is not worth a new utility skill, LEDGER row and trigger cases without a request |
| 6 | Per-skill `agents/openai.yaml` and `opencode.json` | **Reject** for now | — | no Codex or opencode adoption signal; ADR-0027/ADR-0076 add a harness only with a lint guard, and their opencode.json serves authoring, not installs. ADR-0120's `npx` branch already installs every skill into Codex and opencode through the skills CLI, with no per-skill file. Revisit when someone asks for Codex display metadata |
| 7 | One-sentence descriptions, no trigger list | **Reject** | — | unmeasured against this repo's measured routing; would cost a full trigger-eval rerun to try |
| 8 | User-invoked switch on harness-writing skills | **Reject** | — | no skill here writes a throwaway harness; no observed misfire of a costly utility skill to justify dropping one out of model invocation |
| 9 | Rule-ownership table, prose ceilings | **Reject** (parity) | — | "Not X (that's Y)" descriptions, `one_owner.py`, `voice_grade.py` and `CONTEXT.md` cover the same ground |

On copying: the repo is MIT, so any copied text, a table row included,
needs "Copyright (c) 2026 Jakub Krehel" and the permission notice
shipped with it. This repo's precedent is `NOTICE` naming the derived
file plus the full licence under `licenses/` (today only
`licenses/Apache-2.0.txt`, for `trigger_eval.py`); a copy would add an
MIT text there and a `NOTICE` paragraph. Items 1 to 5 should instead be
restated in this repo's terms with a credit line in the skill and in the
README credits paragraph, as `polish` does for Impeccable; then no
`NOTICE` change is owed.

## Seeds

Four, in `docs/backlog.md`'s grammar, each `(from: session:2026-10-31)`
and naming its shortlist row: the interface domain pass for `review`
(1); the blocker list in `polish` (2); the detection-pattern table in
`polish` `inspect` (3); the mechanical SVG check in
`architecture-diagram` (4). Item 5 is folded into nothing and not
seeded: it is worth doing only when `polish` is next edited for 2 or 3.
Deliberately not seeded: Codex/opencode packaging, a description
rewrite, a `break`-style skill.

## Couldn't verify

- How well any external skill performs: the repo publishes no evals,
  and star count is not evidence of output quality.
- Whether `agents/openai.yaml` is read by current Codex releases as
  their AGENTS.md says; no Codex documentation was fetched.
- The parts of the domain skills read by heading only (colors,
  typography, layout, most of writing and UI) may hold more rules worth
  taking; the comparison covers the review, accessibility, harness and
  verification material.
- That an interface domain pass would catch real regressions in this
  repo's adopters: no adopter UI diff was available to test it on.
