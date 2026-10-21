---
stage: decompose
run: feature:idea-ambition-ladder
date: 2026-10-20
assumptions:
  - "No live review of the cut: autorun-brief.md holds the Owner's answers (demo carried through the PRD, no paid run, no LEDGER change, no plugin.json edit) and says nothing about milestones or sizing. Milestone boundaries and sizes are the skill's own defaults: each milestone independently demonstrable, one item per sitting, vertical slices where the architecture allows (one slice per touched surface: Idea skill text, template, seed write, PRD line, suite)."
  - "Test-first ordering follows the repo's TDD rule: each implementation item is blocked by a tests item whose Accept says its cases run and fail against the tree before the edit lands. The tests accumulate in the two files architecture.md names, tests/test_idea_ambition_ladder.py (skill text, template, seed, PRD line, protocol sentence) and tests/test_idea_suite.py (static suite wiring and protected paths)."
  - "No work-order ids and no tracker markers: the brief rules out work-order mirroring, and detectors C and I scan every markdown file, fences included. Items carry short labels (S1, S2, ...) at the start of the bold span, the form decompose-eval-suite used. S13 runs gates.py after the skill text, template and suite markdown are authored for that reason; no item may write a typed id or an example link into skill text, the template, the suite or a seed line."
  - "SKILL.md edits are split in two so each has its own red tests: the ladder bullet and detail block (rungs, four tests, three prompts, demotion, scaled-down version, rules sentence), then the seed instruction. lint.py is re-run in the Accept of every SKILL.md and TEMPLATE.md edit item, because its skill-recital checks (numbered steps, backticked artifact filenames) are what architecture.md says Implement must re-measure."
  - "Seed sample line: architecture.md's measurement appended a sample line to docs/backlog.md only inside a scratch copy. This breakdown does not edit the real docs/backlog.md; the seed tests build the sample line in a temp file from the skill's documented form and run protocol.check_backlog over it, so no real backlog line exists for lint.check_backlog to carry beyond what is already there."
  - "The docs/pipeline-protocol.md Producers sentence is its own item pair (S7 tests, S8 edit) because architecture.md flags it as the one change beyond the PRD's skill-and-suite scope, so Review can judge it alone."
  - "No CLAUDE.md or CONTEXT.md item: architecture.md's Stack section states no CLAUDE.md bullet, tool, VERBS row, mirror pair or workflow is added, and no new vocabulary term is introduced that CONTEXT.md would need. If Review disagrees it is a one-line follow-up, not a design gap."
  - "Scope checks are tests, not review prose: S11 pins the protected paths (.claude-plugin, factory/templates, LEDGER.md, plugin-evals/records, evals, skills/launch-demo, skills/verify, the other plugin-evals suites) against main and skills/ changes limited to skills/idea and skills/prd; they skip cleanly when main is absent. The final item re-checks by diff from this run's first implement commit, because the local main ref may trail the branch base."
  - "Size bands are the skill's calibration by sittings: S is a short edit or a data file under about 50 lines, M is a module piece, test group or several files, L is more than one sitting. No item is L; the suite case item is M because it authors a prompt, a scaffold and twelve grader files."
  - "No design gap found, so nothing is routed to Architect. architecture.md fixes the pinned phrases, order pins, section order, seed rule, hand-off wording, case layout and grader file names, so each Accept line is written from them."
---

# Breakdown: An ambition ladder for the Idea stage, with an achievable showstopper as the default

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. Every implementation item is blocked by the
tests item that pins it, and that tests item is run first and must fail
(RED) against the tree before the edit lands. Skill-side tests go in
`tests/test_idea_ambition_ladder.py` and suite wiring tests in
`tests/test_idea_suite.py`, as architecture.md says. Nothing here invokes
`claude plugin eval`, calls a model or touches the network.

## Milestone 1: the Idea skill asks the ladder

When this milestone is done, `skills/idea/SKILL.md` carries the ambition-ladder bullet in step 4 between the evidence and solution-hunch questions, with its detail block, every pinned phrase and the reconciling Rules sentence, and `lint.py` is clean.

- [x] **S1 Ladder text tests** — create `tests/test_idea_ambition_ladder.py` with the skill-text cases — size:M
  - Accept: the module reads `skills/idea/SKILL.md` through a `skill_text()` helper that normalises whitespace, and holds these cases. Every phrase in architecture.md's Ladder step pin table is asserted with `assertIn`: the bullet label, the block label, `Showstopper (recommended)`, the anchor, the pick-recorded sentence, the Moonshot sentence, the four test phrases, the spike phrase, both demotion phrases, the three prompts, the tests-written phrase, the scaled-down phrase and the rules sentence. The order pins are asserted with `assertLess` on indexes: `What evidence exists` before `**Ambition ladder.**` before `What's the rough shape of a solution?`; the bullet label before the block label; the four tests in listed order; `**Write the artifact.**` after the block. `text.count` shows each of `Solid`, `Showstopper` and `Moonshot` appears at least twice. `re.search(r"\b(PRD|ADR|WO)-\d{4}\b", text)` is `None`. Run before the edit, the module fails.
  - Blocked by: —
- [x] **S2 Ladder step** — add the `**Ambition ladder.**` bullet to Idea's step 4, the `**The ambition ladder.**` block and the Rules sentence — size:M
  - Accept: the S1 tests pass. The block states the three rungs anchored on the user's own words, Showstopper marked recommended, the pick recorded, the Moonshot never chosen, the four tests answered in writing with a clause of evidence, the three prompts, the one-re-scope demotion rule, and the scaled-down version (one question on a feature run, prompts only when no demo moment is named and at most two, tests run silently with only a failure surfaced, a product run asks all three prompts in full). The Rules section keeps the existing "don't replace their idea with yours" line and gains the reconciling sentence. The skill backticks no `prd.md` or `launch-demo` filename in a numbered step and names no tool for the seed write. `python3 lint.py` prints `lint: 0 problem(s)` after the edit, with no new skill-recital problem.
  - Blocked by: S1 Ladder text tests

## Milestone 2: an idea brief records the rung, the demo, the spike and the kill test, and old briefs still validate

When this milestone is done, `skills/idea/TEMPLATE.md` has the four new sections between Evidence and Solution hunch, and a brief written to the old seven-section form still reads as a finished idea stage.

- [x] **S3 Template and old-brief tests** — add the template cases and the old-idea.md case to `tests/test_idea_ambition_ladder.py` — size:M
  - Accept: the module gains these cases. The four headings `## Ambition rung`, `## The demo`, `## Riskiest piece + spike` and `## Cheapest kill test` exist in `skills/idea/TEMPLATE.md` in that order, between `## Evidence` and `## Solution hunch`. The four test labels `Demo`, `Removes a step`, `Only this product` and `Achievable` exist, each with a pass or fail slot. The template carries no typed id. The old-idea case writes a temp run directory holding the seven original sections as a literal in the test, asserts `protocol.stage_states` reports the idea stage `done`, asserts `protocol.parse_frontmatter` returns the three frontmatter keys, and asserts `lint.check_templates(ROOT)` is `[]`. The template cases fail before the edit; the old-idea case passes immediately and is kept as a pin on a fact architecture.md measured, which the S3 note records.
  - Blocked by: S2 Ladder step
- [x] **S4 Template sections** — insert the four sections into `skills/idea/TEMPLATE.md` — size:S
  - Accept: the S3 tests pass. Ambition rung holds the chosen rung in the user's words, the rungs not taken, and the four labelled test lines each reading pass or fail plus one clause. The demo holds before and after in two sentences, or `none — Solid chosen`. Riskiest piece holds the piece and the two-day spike. Cheapest kill test holds the smallest experiment that could prove the idea wrong. Placeholders use `<...>` slots only and no typed id appears. `python3 lint.py` prints `lint: 0 problem(s)` after the edit.
  - Blocked by: S3 Template and old-brief tests

## Milestone 3: the unchosen larger rungs are saved as backlog seeds in a valid form

When this milestone is done, the Idea skill tells the agent to append one seed line per unchosen rung larger than the pick, the Moonshot always, in the grammar the protocol owns, and the protocol names Idea as a producer.

- [x] **S5 Seed tests** — add the seed-instruction and seed-grammar cases to `tests/test_idea_ambition_ladder.py` — size:M
  - Accept: the module gains these cases. The skill text contains `<seed text> (from: <run-ref>)`, `append only` and `never rewrite`, and states the rule that Solid is never seeded and the Moonshot always is, the failure handling (create the file with its header when absent; a seed that would fail the grammar is not written; seeds go in the brief's Not taken line if the write is refused), and that the append lands in the same commit as the idea brief. The skill text shows no real run slug and no typed id. A grammar case builds the seed line from the documented form in a temp backlog (the file's existing header line, one existing line, the new line) and asserts `protocol.check_backlog` returns `[]`, asserts `protocol.parse_backlog` reports the new line's origin as the run-ref given, and asserts a line missing the suffix yields a problem string. Run before the edit, the skill-text cases fail.
  - Blocked by: S4 Template sections
- [x] **S6 Seed instruction** — add the seed rule and its failure handling to the ladder block in `skills/idea/SKILL.md` — size:S
  - Accept: the S5 tests pass and the S1 tests still pass. The instruction is addressed to the agent running the skill, says to append in the stage-boundary commit using specific paths, gives the run-ref as `feature:` plus the slug on a feature run and `product` on a product run in prose without a literal sample slug, requires one line with no parentheses and no typed ids in the seed text, and names no tool. `python3 lint.py` prints `lint: 0 problem(s)` after the edit.
  - Blocked by: S5 Seed tests
- [x] **S7 Producers sentence test** — add a case to `tests/test_idea_ambition_ladder.py` that pins the protocol's Producers sentence — size:S
  - Accept: the case reads `docs/pipeline-protocol.md` and asserts the Seed backlog section's producers sentence contains `Idea appends the rungs it did not take` alongside the existing Operate and Capture producers, and that the sentence still names both. Run before the edit, it fails.
  - Blocked by: S6 Seed instruction
- [x] **S8 Producers sentence** — the one-sentence edit to `docs/pipeline-protocol.md` naming Idea as a backlog producer — size:S
  - Accept: the S7 case passes. The diff against the pre-edit file is that one sentence and nothing else; this is the single change outside `skills/`, `plugin-evals/`, `tests/` and this run's docs, kept in its own item so Review can judge it. `python3 lint.py` prints `lint: 0 problem(s)` and `python3 kb.py drift` prints `drift: 0 problem(s)`.
  - Blocked by: S7 Producers sentence test

## Milestone 4: the demo reaches the PRD as a success criterion, and no downstream skill changes

When this milestone is done, the PRD skill tells the agent to copy the idea brief's demo into a success criterion worded "the demo runs as written", and `skills/launch-demo` and `skills/verify` are byte-identical to main.

- [x] **S9 PRD line tests** — add the PRD hand-off and byte-identical cases to `tests/test_idea_ambition_ladder.py` — size:M
  - Accept: the module gains these cases. `skills/prd/SKILL.md` contains `the demo runs as written`, `## The demo` and `idea.md`, and states that an absent or `none` demo writes no criterion. `git diff --name-only main -- skills/launch-demo skills/verify` is empty, asserted through a subprocess call to git, and the case skips cleanly when `main` is absent, as the decompose suite's `main_exists` does. A further case asserts that, against main, the only files changed under `skills/` are under `skills/idea` or `skills/prd`. The PRD-text cases fail before the edit; the byte-identical cases pass immediately and stay as scope pins.
  - Blocked by: S8 Producers sentence
- [x] **S10 PRD carrying line** — add the one clause to step 4 of `skills/prd/SKILL.md` — size:S
  - Accept: the S9 tests pass. The clause tells the PRD agent, when `idea.md` has a `## The demo` holding a script, to copy it into a success criterion worded `the demo runs as written` with the script as its checkable body, and to write nothing for an old brief or a `none` demo. The skill names no tool and adds no typed id. `python3 lint.py` prints `lint: 0 problem(s)` after the edit.
  - Blocked by: S9 PRD line tests

## Milestone 5: a harness case for the ladder exists, is statically checked and has never run

When this milestone is done, `plugin-evals/idea/ladder-brief/` is a well-formed case in the existing layout, selected by the `idea` tag, with graders that cannot drift from the template, and the detectors that scan every markdown file are clean over everything authored so far.

- [x] **S11 Suite wiring and scope tests** — create `tests/test_idea_suite.py` mirroring `tests/test_decompose_suite.py` — size:M
  - Accept: the module reuses `tests.test_plugin_eval_tags.case_tags` and holds these cases. The manifest's `experimental.evals` equals `plugin-evals`. The case directory holds `case.yaml` (schema version 1.1, name `ladder-brief`, `context.scaffold_script`), `prompt.md`, `scaffold.sh` and `graders/`. Every `plugin-evals/idea/*/prompt.md` carries the `idea` tag. The grader file set is exactly `skill-fired`, `idea-exists`, `has-ambition-rung`, `has-the-demo`, `has-riskiest-piece`, `has-kill-test`, `keeps-users-words`, `moonshot-seed-appended`, `showstopper-passes-four-tests`, `rung-anchored-on-framing` and `moonshot-not-chosen`, and each grader `type:` is one of `regex`, `tool_order`, `tool_used`, `file_exists`, `llm`, `baseline`. The four heading regexes each match the corresponding `skills/idea/TEMPLATE.md` heading. The moonshot-seed regex accepts a line in the skill's seed form and rejects one with no suffix. The prompt fixes a slug and supplies every interview answer including the pick. The scaffold backlog's header and existing line pass `protocol.check_backlog`, and the scaffold plants the phrase `keeps-users-words` greps for. The case never names `claude plugin eval` and no file under `plugin-evals/idea/` imports a network or subprocess module. Protected paths match main and have no untracked file: `.claude-plugin`, `factory/templates`, `LEDGER.md`, `plugin-evals/records`, `evals`, `skills/launch-demo`, `skills/verify` and the other four `plugin-evals/` suites; no existing eval definition file changed. Skips cleanly when main is absent. Run before the case exists, the module fails.
  - Blocked by: S10 PRD carrying line
- [x] **S12 Suite case** — author `plugin-evals/idea/ladder-brief/` (case.yaml, prompt.md, scaffold.sh, the eleven grader files); never run — size:M
  - Accept: the S11 tests pass. `prompt.md` has frontmatter `description`, `tags: [idea]`, `max_turns`, `timeout_seconds` and `allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]`, with all interview answers supplied up front and the slug fixed. `scaffold.sh` seeds a small committed repo: a docs directory, a one-paragraph pitch for a made-up scheduling tool planting one distinctive phrase, and a `docs/backlog.md` with its header and one existing seed. The regex graders run over the produced files for headings, the planted phrase and the moonshot seed; the three `llm` graders each name one check. The case carries no typed id and no example link, and no script or tool grant runs a checker. `plugin-evals/records/` gains no file.
  - Blocked by: S11 Suite wiring and scope tests
- [x] **S13 Detectors over the authored text** — run the detectors that scan every markdown file over the skill text, template, protocol sentence and suite — size:S
  - Accept: `python3 gates.py` prints `gates: 0 problem(s)` and `python3 lint.py` prints `lint: 0 problem(s)` with the edited skills, template, protocol sentence and suite present. If a detector fires, the authored text is fixed, not the detector. The result is recorded as a dated line in this file's Notes.
  - Blocked by: S12 Suite case

## Milestone 6: the whole change verifies and stays in scope

- [ ] **S14 Whole-repo verify** — the CI checks and the scope checks over the finished change — size:S
  - Accept: `python3 run_tests.py` exits 0; `python3 lint.py` prints `lint: 0 problem(s)`; `python3 kb.py drift` prints `drift: 0 problem(s)`; `python3 gates.py` and `python3 gates.py --selftest` print `gates: 0 problem(s)` and `selftest: ok`. A diff from this run's first implement commit shows no change under `.claude-plugin/`, `factory/templates/`, `evals/`, `plugin-evals/records/`, `skills/launch-demo` or `skills/verify`, no change to `LEDGER.md`, changes under `skills/` only in `skills/idea` and `skills/prd`, exactly one changed line in `docs/pipeline-protocol.md`, and no edit to an existing eval definition. No `claude plugin eval` run was made. The results are recorded as a dated line in Notes.
  - Blocked by: S13 Detectors over the authored text

## Design gaps found

none.

## Notes


- 2026-10-20 S13: `python3 gates.py` printed `gates: 0 problem(s)` and `python3 lint.py` printed `lint: 0 problem(s) across 34 skills` with the edited skills, template, protocol sentence and suite present.
