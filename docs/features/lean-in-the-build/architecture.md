---
stage: architect
run: feature:lean-in-the-build
date: 2026-10-10
ux: skipped — the deliverable is wording in two stage skills' instruction files; no flow or screen is designed
assumptions:
  - "No live trade-off read-out: the brief (including its 2026-10-10 Amendment) answers the shape, and the two open questions the PRD left to this stage are decided below against the repo's own bar (skills/architect step 7 for ADRs; the Amendment's 'only if needed to stay legal' for a lint pin). Taken without user input."
  - "No new ADR. The cross-kind reference fails the architect skill's three-part ADR bar on 'hard to reverse' (removing it is a two-sentence revert, and nothing persists in its shape), and the one existing sibling reference (pipeline-board -> architecture-diagram) was recorded in its run's architecture.md, not an ADR. Taken without user input."
  - "No lint pin. The backticked `../lean/references/...` form is already legal under lint.py's check_skill_assets, so the Amendment's condition for a pin (needed to stay legal) does not hold. The unchecked-rename gap is recorded for Review to seed, not closed here. Taken from the brief."
  - "Review's TEMPLATE.md gains the word 'complexity' in its clean-pass prompt and nothing else; cuts are filed in the existing Findings list rather than a new section. Recommended default: one findings list ranked by severity is how review.md already reads. Taken without user input."
  - "No install-fallback sentence in the stage skills: every documented install (Claude Code and Grok plugin install, omp Pi package, copying skills/*) ships lean beside implement and review. Taken without user input."
---

# Architecture: lean in the build

## Approach

Nothing new is built. Two stage skills gain a pointer to a utility
skill's reference files, the way `pipeline-board` already points at
`../architecture-diagram/references/design-system.md`: named in
backticks, read at the step that needs it, never copied. `lean` keeps
sole ownership of the ladder and the cut-list, so a change to either
reaches Implement and Review without a second edit. Implement climbs the
ladder inside its existing per-item loop, between the failing test and
the minimum implementation it already asks for. Review gains a fourth
pass, Complexity, beside correctness, design and security, and files
cuts in the findings list it already has. `lean` stays a utility skill:
it is read, never routed to, and owns no artifact (ADR-0023).

The other shape considered was restating the ladder's seven rungs and
the cut-list's six tags inside the two stage skills, so each stands
alone. It loses: it creates a second owner of two facts `lean` already
owns (the class of drift this repo has paid for at least seven times), and the
Amendment rules it out ("reference, never duplicate").

## Components

### skills/implement/SKILL.md, step 4 (the per-item loop)

- Responsibility: make "the minimum implementation that passes" mean
  lean's ladder. One new bullet sits between "Watch it fail for the
  right reason." and "Write the minimum implementation that passes…".
  Wording:

  > - Before writing the implementation, climb `lean`'s ladder in
  >   `../lean/references/ladder.md` and stop at the first rung that
  >   holds. Lean's floor is never cut: validation where untrusted input
  >   enters, error handling that prevents data loss, security controls,
  >   accessibility basics. A deliberate shortcut with a known ceiling
  >   carries a comment starting `lean:` that names the ceiling and what
  >   would trigger the upgrade; that marker is the record, so nothing
  >   about the ladder goes into `breakdown.md`.

  No other step changes. Step 5 (deviations under Notes) and the
  "Surgical scope" rule already say what `lean`'s step 6 asks of a cut
  outside the current item.
- Collaborators: `skills/lean/references/ladder.md` (read, unchanged).

### skills/review/SKILL.md, step 4 (the pass list)

- Responsibility: grade the diff for over-building while the author can
  still act. Step 4's lead-in changes from "Review in three passes:" to
  "Review in four passes:", and a fourth bullet follows **Security**.
  Wording:

  > - **Complexity** — apply `lean`'s cut-list in
  >   `../lean/references/cut-list.md` to the run's diff. Each confirmed
  >   cut is a finding: its cut-list line and the evidence its tag owes
  >   stand in for the failure scenario. A cut whose references you could
  >   not enumerate is a suspicion, not a finding. Every `lean:` marker
  >   the diff adds must name its ceiling and its trigger; one that names
  >   no trigger is a finding. A concern about a module's shape rather
  >   than its size is handed to `deepen` in one line — never refactored
  >   here.

  Severity, ranking, the fix loop (steps 6 and 8), and every Rule are
  unchanged: a cut is ranked like any other finding, so the fix loop
  already decides which cuts block Ship.
- Collaborators: `skills/lean/references/cut-list.md` (read, unchanged);
  `deepen` (named as a hand-off, not invoked).

### skills/review/TEMPLATE.md

- Responsibility: keep review.md's shape honest about four passes. The
  one change is the clean-pass prompt under "Passes with no findings":
  `<Which of correctness / design / security came back clean.>` becomes
  `<Which of correctness / design / security / complexity came back
  clean.>`. No Complexity section is added — cuts go in Findings with
  the other passes' findings, so a clean Complexity pass is one word in
  a list rather than a boilerplate section (the PRD's own named risk).

### skills/lean/** (unchanged)

- Responsibility: sole owner of the ladder, the floor, the `lean:`
  marker convention and the cut-list. Its step 6 already describes the
  Implement hand-off; nothing in this run needs it edited.

### .claude-plugin/plugin.json

- Responsibility: version `0.5.0` -> `0.5.1`, so the installed plugin
  cache refreshes (a stale cache is silent). No file in
  `factory_init.MIRRORS` or under `factory/templates/**` changes, so
  `factory/manifest.json` is not regenerated.

## Data model

None. The only recorded shape is the `lean:` code comment, which `lean`
already defines (its step 3, and the debt harvest in its step 5); this
run adds no field, artifact section or breakdown column. Access pattern:
Review reads the markers its diff adds; `lean`'s debt mode reads them
tree-wide.

## Interfaces & contracts

### Stage skill -> lean reference file

- Input: a backticked path relative to the stage skill's directory,
  `../lean/references/ladder.md` or `../lean/references/cut-list.md`,
  read by the agent at the step that names it.
- Output: the ladder's seven rungs and floor, or the cut-list's entry
  format, six tags and evidence rules.
- Failure modes: the path resolves only when `lean` is installed as a
  sibling skill. Every documented install does that (the plugin ships
  `skills/` whole; omp's Pi package and the copy fallback take
  `skills/*`). A rename of either reference file is not caught by lint:
  `check_skill_assets` deliberately skips `../<skill>/references/...`
  paths (its lookbehind), so a rename surfaces as an agent read that
  returns nothing — the same exposure `pipeline-board` already carries.
  See Decisions.

### Review finding from a cut

- Input: one cut-list entry, `N. path:lines — tag: what goes. What
  replaces it.`, plus the evidence its tag owes.
- Output: a review.md finding in the existing shape — Severity, Scenario
  (the entry and its evidence), Standard, Decision.
- Failure modes: a `?` suspicion is not filed as a finding (Review's
  rule: a finding needs a scenario or a named decayed contract). A
  floor item or the item's one runnable check is never a cut (the
  cut-list's "What never appears").

## Stack & dependencies

- Markdown wording only — no script, no new module, no new checker.
- `lean` (in-plugin sibling, already shipped by PR #632) — read-only
  dependency of two stage skills.

## Decisions & alternatives

- **Reference `lean` by sibling path** over copying the ladder and
  cut-list into the stage skills — a copy is a second owner of a fact
  `lean` owns; the Amendment forbids it.
- **No new ADR** over writing one for the first stage-to-utility
  dependency — the architect skill offers an ADR only when a decision is
  hard to reverse, surprising, and a real trade-off. This is easy to
  reverse (two backticked sentences; no stored data takes its shape),
  and the trade-off was the owner's, recorded in the brief. ADR-0008
  forbids hard dependencies on third-party tools, plugins and MCP
  servers; a sibling skill in the same plugin is none of those, and the
  `pipeline-board` precedent took the same reading without an ADR.
  ADR-0023 is untouched: `lean` is consulted, never routed to, and owns
  no artifact.
- **No lint pin** over extending `check_skill_assets` to resolve
  `../<skill>/(references|assets)/<file>` against `skills/` and report a
  missing target — the Amendment allows a pin only when a reference
  needs one to stay legal, and this one is already legal. The gap is
  real (three sibling references would then go unchecked: one
  `pipeline-board`, two here) and pre-dates this run, so it belongs in
  a backlog seed for its own run; Review should seed it.
- **Cuts in the existing Findings list** over a new Complexity section
  in TEMPLATE.md — one ranked list is how review.md reads; a dedicated
  section invites a boilerplate "none".
- **Ladder bullet inside step 4** over a new numbered step — the ladder
  is per item, so it belongs in the per-item loop; a new step would
  renumber the skill and suggest a separate phase.
- **Leave both skills' descriptions unchanged** over mentioning `lean`
  in them — the descriptions are the routing surface (ADR-0019,
  ADR-0020), and the wiring changes what the stages do, not when they
  trigger. The routing eval is owed, not run (paid).

## ADRs

None — no decision met the ADR bar (see Decisions & alternatives).
