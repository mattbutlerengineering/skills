---
stage: decompose
run: feature:pocock-1-3-takeaways
date: 2026-10-06
assumptions:
  - "The approved draft's Milestone 4 had two items: check omp's model-side skill invocation, then reword next step 5 per the decision. architecture.md settled the check (omp's docs/skills.md: skills are on-demand content read via the read tool, no skill tool; decision adopt-with-neutral-wording, no ADR), so the two items collapse into one row that rewords step 5's lead sentence with the architecture's neutral sentence, keeps the eleven list lines byte-identical, and records the decision in the protocol's Harness neutrality section."
  - "The architecture's packaging note says the plugin version is 'bumped at Ship' with the number decided there; PRD-0007's Battery-and-packaging criterion needs the bumped version and regenerated manifest in place for Verify, and factory/manifest.json embeds the version, so the draft's close-out row keeps the bump at Implement (0.3.1 if the lean/polish branch's 0.3.0 has landed on main by then, else 0.3.0) and Ship records the number and re-bumps and regenerates if merge order changed in between."
  - "The cut was not reviewed live (skill step 4): the user approved the draft via /autorun, and this artifact departs from it only where the architecture fixed a specific the draft left open (the rule's exact problem strings and indicator set, the protocol heading and position and its Merge danger sub-shape, operate step 6 and the renumbering, the Environment table's position and columns, the automate table row, the next lead sentence) or settled a question (Milestone 4 above)."
  - "Sizes are this stage's reading, the brief and architecture naming none: S throughout except the rule's tests and the protocol section, both M, because each has the most surface to get exactly right (five exact-string fixtures run red then green; the one owning section three other files point at)."
---

# Breakdown: Pocock 1.3 takeaways

Progress lives in the checkboxes below — Implement checks items off as
their acceptance criteria are met. Rows follow the house grammar: a
repo-global work-order id (continuing from 0076), size class, blocking
edges, and the PRD citation. No tracker mirror for this run (the brief
rules out any tracker interaction; the checkboxes are the state,
ADR-0026). Reconciled against `architecture.md` on 2026-10-06: every
component it names lands in a row below, and every PRD-0007 success
criterion is covered by at least one Accept paragraph; the Coverage section
at the end says which. Descriptions are reworded before the lint rule
lands so every commit stays lint-green, and the rule's tests are written
before the rule.

## Milestone 1: Every skill description survives a strict YAML loader

- [x] **WO-0077** Reword the six colon descriptions — size:S, blocked by: — (PRD-0007 §Success criteria)
  - Accept: the `description:` of audit, automate, deepen, doctor, pipeline-board and work-queue each lose their single `: ` (a semicolon or full stop joins the two clauses instead) and no other skill's description changes; a read-only script over all twenty-five `skills/*/SKILL.md` reports no description containing `: ` or ` #`, none starting with a character from `-?:,[]{}#&*!|>'"%@` or a backtick, and each within 1024 characters; `git diff` of the six description lines read side by side shows every trigger phrase surviving; nothing under `evals/` changes; `python3 lint.py` prints `lint: 0 problem(s)`, `python3 gates.py` prints `gates: 0 problem(s)`, and `python3 -m unittest discover tests` prints `OK`.
- [x] **WO-0078** Pin the bare-scalar rule with tests — size:M, blocked by: — (PRD-0007 §Success criteria)
  - Accept: `tests/test_protocol_frontmatter.py` `TestSkillFrontmatterProblems` gains, through its `seed` helper and the public `skill_frontmatter_problems(root, slug)`, tests asserting the exact strings: a description holding `: ` yields `skills/<slug>/SKILL.md description is not a bare YAML scalar: contains ': '`; one holding ` #` yields `skills/<slug>/SKILL.md description is not a bare YAML scalar: contains ' #'`; one holding both yields both strings in that order; a double-quoted description yields `skills/<slug>/SKILL.md description is not a bare YAML scalar: starts with '"'` (the first character rendered with Python's `!r`), plus one further indicator case such as `[` or `|`; a missing description still yields only its existing string; the existing conformant fixture still yields none. Observed red: run against the tree before the rule exists, each new test fails and every other test passes (write the output to a file and grep `FAILED`); the rule's row turns the same file green without editing a test.
- [x] **WO-0079** Add the bare-scalar rule to skill_frontmatter_problems — size:S, blocked by: WO-0077, WO-0078 (PRD-0007 §Success criteria)
  - Accept: `protocol.skill_frontmatter_problems` (ADR-0052) appends, when a description is present, zero or more of the three strings above in the fixed order contains-`: `, contains-` #`, starts-with, using `str` methods only (no YAML parser), with the indicator set `-?:,[]{}#&*!|>'"%@` plus the backtick held as a private constant beside `SKILL_DESCRIPTION_LIMIT`; it never raises, and a missing file, block or description returns its existing string alone and skips the new checks; `lint.py` and `trigger_eval.py` call it unchanged; `python3 factory_init.py update-manifest` rewrites the identity mirror `factory/templates/tools/factory/protocol.py` and `factory/manifest.json`, both committed with the edit; the tests from the previous row pass, `tests.test_factory_init`'s payload-to-root pin and detector E are green, and the full battery is green on both interpreters (`python3.12 -m unittest discover tests` and `python3.14 -m unittest discover tests` print `OK`; `python3 lint.py` prints `lint: 0 problem(s)`; `python3 gates.py && python3 gates.py --selftest` prints `gates: 0 problem(s)` and `selftest: ok`).

## Milestone 2: A pull request body says what the merge risks

- [x] **WO-0080** Protocol section Pull request body — size:M, blocked by: — (PRD-0007 §Success criteria)
  - Accept: `docs/pipeline-protocol.md` gains a `## Pull request body` section placed after `## Artifact frontmatter` and before `## Harness neutrality`, stating the three parts of a body: the smallest visual that shows the change (pseudocode, call tree, file tree, diagram or diff), before-and-after evidence, and a merge-danger call under the one fixed heading `## Merge danger` carrying `Door:` (one-way or two-way) and `Blast radius:` (what breaks if the call is wrong), the heading fixed so a reviewer at gate 2 (ADR-0033) finds it and the rest prose; the section says detector B's lines stay (`Closes #N`, and a work-order id or the `No work order:` waiver, written in prose without a literal id token); it credits mattpocock/skills `pr` and Dex Horthy's `show-me` (Humanlayer), restating structure and copying no text; it is harness-neutral (no Claude Code or omp mechanics); detector B is unchanged so no existing PR goes red; `python3 gates.py` prints `gates: 0 problem(s)` (detector I reads the section's links) and `python3 lint.py` prints `lint: 0 problem(s)`.
- [x] **WO-0081** Work-queue worker brief cites the section — size:S, blocked by: WO-0080 (PRD-0007 §Success criteria)
  - Accept: `skills/work-queue/SKILL.md` step 4's numbered list "Each agent's prompt must carry" gains one new numbered item telling the worker the PR body follows the protocol's Pull request body section (named by heading, nothing restated), keeping item 2's `Closes #N` line and detector B's work-order citation; `grep -n 'Pull request body' skills/work-queue/SKILL.md` finds the item; the skill's `description:` is unchanged; `python3 lint.py` prints `lint: 0 problem(s)`.
- [x] **WO-0082** Ship rollback plan speaks the same words — size:S, blocked by: WO-0080 (PRD-0007 §Success criteria)
  - Accept: `skills/ship/SKILL.md` pre-flight step 3's rollback bullet and `skills/ship/TEMPLATE.md`'s `## Rollback plan` both record the door (one-way or two-way) and the blast radius beside the rollback steps and point at the protocol's Pull request body section by heading, so `release.md` and the PR body agree without a second copy of the shape; `grep -n 'Pull request body'` finds both files; the ship `description:` is unchanged; `python3 lint.py` prints `lint: 0 problem(s)`.
- [x] **WO-0083** Routine PR skeleton gains a merge-danger section — size:S, blocked by: WO-0080 (PRD-0007 §Success criteria)
  - Accept: the fenced PR body skeleton in `docs/factory/improvement-routine.md` §5 gains `## Merge danger` immediately after its `## Verification` block and before `## Daily report`, with a one-line placeholder pointing at the protocol's Pull request body section rather than restating it; the skeleton's first two lines (`<!-- improvement-routine -->` and the `No work order:` line) are byte-identical to before (`git diff` shows them unchanged); the routine's surrounding prose is otherwise untouched; `python3 gates.py` prints `gates: 0 problem(s)` (detectors B selftest and I read this file).

## Milestone 3: The retro asks what in the environment would have caught it

- [x] **WO-0084** Operate step 6 retrospects on the environment — size:S, blocked by: — (PRD-0007 §Success criteria)
  - Accept: `skills/operate/SKILL.md` gains step 6 `**Retrospect on the environment.**` directly after step 5 `**Retrospect on the run itself.**`, and the former steps 6 and 7 (Seed the next runs; Write the artifact) become 7 and 8 with their text unchanged; the new step reads the run's own record of its mistakes (`verification.md` failures, `review.md` findings, `breakdown.md` Notes), names per mistake the check, pointer or rule that would have caught it, classifies it mechanical (a deterministic check: lint rule, hook, CI job, gate detector) or judgement (a CLAUDE.md line or a standards statement), and proposes the carrier; the `description:` line is byte-identical (`git diff` on that line is empty) so `evals/routing.json` stays valid untouched; lint's recital checker still finds the soft-gate and artifact filenames after renumbering, so `python3 lint.py` prints `lint: 0 problem(s)`.
- [x] **WO-0085** Retro template Environment table — size:S, blocked by: WO-0084 (PRD-0007 §Success criteria)
  - Accept: `skills/operate/TEMPLATE.md` gains an `## Environment` section between `## Run retrospective` and `## Idea seeds`, holding a table with the header row `| Mistake | Evidence | Class | Proposed carrier |`, where Evidence cites the artifact and heading or line, Class is `mechanical` or `judgement`, and Proposed carrier names an existing thing (a lint checker, a gates detector, a hook, a CI job, a CLAUDE.md line, a `docs/standards.json` statement), with a one-line note that an absent section reads as no environment findings; the eight existing `docs/**/retro.md` files are not edited (`git diff --stat -- 'docs/**/retro.md'` is empty); `python3 lint.py` prints `lint: 0 problem(s)` and `python3 gates.py` prints `gates: 0 problem(s)`.
- [x] **WO-0086** Automate reads retro Environment sections as friction — size:S, blocked by: WO-0085 (PRD-0007 §Success criteria)
  - Accept: `skills/automate/SKILL.md` step 1's surface table (`| Surface | Where |`) gains one row naming the `## Environment` section of every `docs/**/retro.md` as a surface, and that row is the only edit for this item (step 2 already counts a retro naming a thing that dragged as the strongest friction source; a `mechanical` row maps to the hooks and drift-detector categories, a `judgement` row to the rules-stated-and-unenforced source, and no section means no finding); `grep -n 'Environment' skills/automate/SKILL.md` finds the row; the skill's `description:` is unchanged; `python3 lint.py` prints `lint: 0 problem(s)`.

## Milestone 4: The router's hand-off names the mechanism

- [ ] **WO-0087** Reword next step 5 and record the hand-off decision — size:S, blocked by: — (PRD-0007 §Success criteria)
  - Accept: in `skills/next/SKILL.md` step 5 keeps its number and `**Hand off.**` label and its lead sentence becomes the architecture's neutral wording: "Load the matching stage skill through the harness's skill-loading mechanism (a skill tool where one exists, otherwise a read of the skill file) and follow it; naming the skill in prose does not load it."; the eleven list lines beneath it (`- <stage> → the `<stage>` skill`, capture through operate) are byte-identical to before (`git diff` touches only the lead line) so `lint.check_router`'s `HANDOFF_LINE` membership and order check is unchanged; `docs/pipeline-protocol.md`'s `## Harness neutrality` section records the decision as adopt-with-neutral-wording with its reason and what was checked: omp's `docs/skills.md` exposes skills to the model as on-demand content read via the `read` tool against `skill://` paths and its Skills vs custom tools section separates skill content from model-callable tool APIs, so omp has no skill tool and Pocock's literal "Call the Skill tool with X" fails one harness (ADR-0027), while the lesson (name the mechanism, not just the skill) survives as the neutral sentence, applying ADR-0027 rather than amending it (no new ADR); `evals/routing.json` is untouched; `python3 lint.py` prints `lint: 0 problem(s)` and `python3 gates.py` prints `gates: 0 problem(s)`.

## Milestone 5: Small borrowings and close-out

- [ ] **WO-0088** Glossary under either name — size:S, blocked by: — (PRD-0007 §Success criteria)
  - Accept: `skills/audit/SKILL.md` (the orientation list line naming `CONTEXT.md`, line 30 today), `skills/deepen/SKILL.md` (the domain-glossary bullet, line 29 today) and `skills/automate/SKILL.md` (the Agent instructions row of step 1's surface table) each name `GLOSSARY.md` beside `CONTEXT.md` where they read a target repo's vocabulary; this repo's own `CONTEXT.md` is not renamed and no other file changes; `grep -l 'GLOSSARY.md' skills/audit/SKILL.md skills/deepen/SKILL.md skills/automate/SKILL.md` lists all three; the three `description:` lines are unchanged; `python3 lint.py` prints `lint: 0 problem(s)`.
- [ ] **WO-0089** Worker base-and-tip rules in work-queue — size:S, blocked by: — (PRD-0007 §Success criteria)
  - Accept: `skills/work-queue/SKILL.md` step 4's "Each agent's prompt must carry" list carries two further worker rules: confirm the branch base is the default-branch tip before writing anything, and merge or rebase that tip into the branch before declaring done; both are checkable by grep (`default-branch tip` or equivalent wording appears twice in the brief, once per rule); the existing items (row scope, `Closes #N`, test-first and `make check`, budget, open-a-PR-and-stop) are unchanged in meaning; the skill's `description:` is unchanged; `python3 lint.py` prints `lint: 0 problem(s)`.
- [ ] **WO-0090** Version bump, manifest and full battery — size:S, blocked by: WO-0077, WO-0078, WO-0079, WO-0080, WO-0081, WO-0082, WO-0083, WO-0084, WO-0085, WO-0086, WO-0087, WO-0088, WO-0089 (PRD-0007 §Success criteria)
  - Accept: `.claude-plugin/plugin.json` `version` is bumped from 0.2.0 to 0.3.1 if the lean/polish branch's 0.3.0 has landed on `main` by now, else 0.3.0 (Ship records which and re-bumps if merge order changes); `python3 factory_init.py update-manifest` is run after the bump so `factory/manifest.json`'s `version` matches and detector E is green; on both interpreters `python3.12 -m unittest discover tests` and `python3.14 -m unittest discover tests` print `OK`, `python3 lint.py` prints `lint: 0 problem(s)`, and `python3 gates.py && python3 gates.py --selftest` prints `gates: 0 problem(s)` and `selftest: ok` (write each output to a file and grep, per the brief's zsh note); `git diff --stat main -- evals/ LEDGER.md` is empty; every row above is checked.

## Coverage

Architecture components to rows, by milestone: the Description contract
(`protocol.py`) is Milestone 1, all three rows; the Pull request body
section and its three pointers are Milestone 2 (the section, then the
work-queue brief, ship, and the routine skeleton); the Environment
retrospective (operate producing, automate reading) is Milestone 3; the
Router hand-off (next step 5 and the protocol's Harness neutrality
section) is Milestone 4; Small borrowings and packaging are Milestone 5
(glossary, worker rules, version and manifest). Nothing in the
architecture's Components or tree-claims list is left without a row.

PRD-0007 Success criteria to Accept paragraphs: Strict-YAML descriptions is
Milestone 1 (reword, tests, rule); Pull request body is Milestone 2 (all
four rows); Environment retrospective is Milestone 3 (all three rows);
Hand-off decision is Milestone 4; Small borrowings is the glossary and
worker-rules rows of Milestone 5; Battery and packaging is the close-out
row of Milestone 5, with the per-row lint and gates checks along the way.

## Design gaps found

None. The two gaps the approved draft recorded were settled by Architect
and are now Accept criteria: the rule rejects a quoted description too
(the `starts with` string), so `read_frontmatter` stays a plain `key:
value` splitter; and the protocol section owns the pull-request-body shape
with the work-queue brief, ship and the routine skeleton pointing at it by
heading rather than restating it.

## Notes

- 2026-10-06: `docs/backlog.md` line 6 (is Pi's 1024 limit chars or
  bytes) touches the same check as Milestone 1 and stays out of scope.
- 2026-10-06: `factory/manifest.json` is also touched by the lean/polish
  branch, PR #602 and the unpushed guarded-read branch; whichever lands
  last regenerates it under detector E, watched by the merge reviewer at
  gate 2.
- 2026-10-06: rows of Milestones 2 and 5 both add numbered items to the
  work-queue step 4 brief, and two rows of Milestones 3 and 5 both edit
  automate's surface table; Implement works them in document order on one
  branch, so no merge edge is declared between them.
- 2026-10-06: Implement's checked rows follow this repo's existing
  owner-session ledger policy (`docs/features/process-dashboard/
  breakdown.md`, 2026-08-13 note; reaffirmed 2026-09-21 and in
  ADR-0069's Context): detector G reads a checked row as a merged
  work order owed a `docs/factory/costs.jsonl` line, and this run's
  rows are implemented interactively with no dispatched agent, so
  each check-off appends one honest `$0` row via `budget_guard
  record` (`run_id: session-<date>-wo-<n>`, the session's model,
  `tokens: 0`, `cost: 0.0`, `outcome: owner-session:unmetered`).
  Not in the rows' Accept text, which assumed `gates: 0 problem(s)`
  followed from the edits alone; the ledger row is what makes it so.
- 2026-10-06: the Milestone 2 Accept text and `architecture.md` place
  the merge reviewer at "gate 2 (ADR-0033)"; ADR-0033 numbers the PR
  merge as gate 3 (gate 2 is blueprint/ADR approval; ADR-0036 lets the
  gate-3 reviewer be an agent), as `skills/work-queue/SKILL.md` already
  says. The protocol section cites gate 3. The upstream artifacts'
  wording is left as written, not rewritten.
