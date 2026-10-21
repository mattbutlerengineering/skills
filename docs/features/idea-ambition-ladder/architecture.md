---
stage: architect
run: feature:idea-ambition-ladder
date: 2026-10-20
ux: skipped — skill text, a template, a suite and tests only; no screens or flows (per prd.md).
assumptions:
  - "No live interview: every PRD open question was settled from the code, `claude plugin eval --help` and measurements on a `git archive HEAD` copy of this clone, taking the recommended default each time. No ADR is written: nothing here is hard to reverse (skill text, a template, one protocol sentence, a suite and tests all change in one commit), so the protocol's three-leg test fails on the first leg for every decision. Nothing is surfaced."
  - "Measured, TEMPLATE.md change (PRD open question 2): in a `git archive HEAD` copy under the session scratchpad, the four new sections were inserted into `skills/idea/TEMPLATE.md` ahead of Solution hunch, a sample seed line was appended to `docs/backlog.md`, one ladder bullet was added to `skills/idea/SKILL.md` step 4, the prd hand-off clause was added to step 4 of `skills/prd/SKILL.md`, and the Producers sentence of `docs/pipeline-protocol.md` was reworded (the sed for that last one did not apply on macOS, so the protocol edit is untested as text; it is prose and no checker reads that sentence: `git grep` finds no test or lint reference to `Producers`). Results: `python3 lint.py` read `lint: 0 problem(s) across 34 skills`; `python3 kb.py drift` read `drift: 0 problem(s)`; `python3 gates.py` read `gates: 0 problem(s)`; `python3 gates.py --selftest` read `selftest: ok`; `python3 run_tests.py` read `3632 tests across 111 modules ... 2 problem(s)`, both in modules that need a git checkout and unrelated to the edit (`tests.test_shadowed_definitions`, `tests.test_knowledge_plane.TestRepoRoot`; a `git archive` copy carries no repository metadata). No Python reads idea.md sections: `protocol._stage_complete` treats the idea stage as done when the file exists, and a grep of `*.py` for the template's headings finds only the template, the `plugin-evals/next/idea-exists` scaffold's own pre-change copy of an idea.md (a built-in old-form fixture) and worktrees under `.claude/worktrees/`. `protocol.stage_states` ran without error over all 21 `docs/features/*/idea.md`. Conclusion: adding sections to TEMPLATE.md cannot break an old idea.md, because nothing parses them; the PRD's old-form criterion is still pinned by a test, since that is the cheap way to keep it true."
  - "Recommended default taken (the ladder step's home, PRD open question 1): inside Idea's step 4 Interview as one new bullet, `**Ambition ladder.**`, between the evidence bullet and the solution-hunch bullet, with the detail in a block after the bullet list headed `**The ambition ladder.**`; not a new numbered step. A new numbered step would split the interview list in two. Measured: with the bullet added, `lint.py`'s skill-recital checks (numbered steps, backticked `*.md` names, `next stage is ...`) stay at 0 problems. The Idea step must not backtick `prd.md` or another stage's artifact filename inside a numbered step beyond the existing ones; Implement re-runs lint after the real edit."
  - "Recommended default taken (the unchosen-rung seed rule, PRD requirement 4): seed each unchosen rung that is larger than the pick, never Solid. Pick Solid: seeds for Showstopper and Moonshot. Pick Showstopper: one seed, the Moonshot. A showstopper that fails test 4 and is demoted becomes the Moonshot seed and Solid is the pick. Seeding Solid when a larger rung was picked would file a strict subset of the chosen work as a future idea. The Moonshot is always seeded, as the PRD says. The issue and PRD say 'unchosen rungs'; this reads it as the useful subset and records the reading."
  - "Recommended default taken (who writes the seed, PRD open question 3): the agent running the `idea` skill, by the skill's instruction. Idea stays text only: no tool, module or CLI writes the file. This makes Idea a backlog producer, which `docs/pipeline-protocol.md`'s Seed backlog section does not yet say (it names Operate and Capture), so the Producers sentence gains Idea. That edit is the only change outside skills/, plugin-evals/, tests/ and this run's docs; it is a prose sentence no checker reads (above), so it is not an ADR. The skill's rules inherit the protocol's: append only, never rewrite existing lines, create the file if absent with the header line the file already uses, one line per seed ending `(from: feature:<slug>)` (or `(from: product)` on a product run), seed text on one line with no parentheses and no typed ids. The append is staged with idea.md in the stage-boundary commit (specific paths, never `git add -A`)."
  - "Measured, seed safety (PRD open question 3): `protocol.check_backlog` fullmatches `- (?P<text>.+?) \\(from: (?P<origin>[^()]+)\\)(?: \\(claimed: ...\\))?` with the origin held to `product`, `feature:[a-z0-9-]+`, `maintenance:[a-z0-9-]+` or `session:YYYY-MM-DD`; `lint.check_backlog` runs it over the real file, so a malformed seed fails `lint.py`. Detectors C and I scan every markdown under docs/, the repo root, .github/, skills/ and factory/ (not plugin-evals/), fences included (docs/kb/gates-scan-every-doc.md), so SKILL.md, TEMPLATE.md and this document must show the seed form only as `<seed text> (from: <run-ref>)` placeholders and never as a made-up typed id. Measured: a sample seed line in the trial copy passed lint and gates."
  - "Recommended default taken (demoting, PRD open question 7, a known limit): 'drops to the moonshot rung' is written as a two-step rule so it demotes less. If the riskiest piece cannot be named with a spike of about two days that could prove it, the skill says so, offers to re-scope the showstopper once to a smaller wow moment, and re-applies the four tests; only if that also fails is the showstopper recorded as the Moonshot (and seeded) and Solid becomes the pick. A spike need only be nameable and about two days; it does not need a predicted outcome. Over-demotion for ideas that really have no two-day spike remains a known limit for Review: the rule trades a missed showstopper for an honest Solid."
  - "Recommended default taken (making the four tests more than taste, PRD open question 6): the skill requires each test to be answered in writing, as a labelled line of `Ambition rung` in idea.md, `pass` or `fail` plus one clause of evidence (what is seen after; which step is gone; what only this product holds; the named riskiest piece and spike). A model or hurried user can still write 'pass', but a reviewer sees the claim, the suite's llm grader reads it, and a test that has no evidence clause is visibly empty. This does not make the tests objective; it makes a pass inspectable. Remains a known limit for Review."
  - "Recommended default taken (the feature-run scaled-down version, PRD open question 5): the ladder is one question, not seven. For a feature run the skill shows the three rungs in one line each anchored on the user's own sentence, recommends Showstopper, and asks the user to pick or correct; the three prompts are asked only when the user's framing names no demo moment, at most two of them, one at a time. The four tests still run (they are the check, not interview), the spike is one sentence, and each of the four new template sections is held to two or three lines. A product run asks all three prompts one at a time and fills the sections in full. Weight, measured on the existing skill: step 4 lists 7 interview questions; a feature run adds 1 (the pick) and at most 2 follow-ups. Whether that is light enough is unproven and is a known limit for Review."
  - "Recommended default taken (with/without arms, PRD open question 4; harness fact read from `claude plugin eval --help`, 2.1.296 as in ADR-0081; no eval was run): `--ablation` defaults to `with-without` whenever a plugin resolves, repeating every case with no plugin loaded, and graders marked with-only (including `tool_used: Skill`) are an indicator rather than part of the score. So a with-plugin arm and a without-plugin arm are not two case files; every case already gets both. The kb suite's on/off pairs toggle a repo document, which is a different arm; no such pair is needed here. Each case is therefore one directory under `plugin-evals/idea/`, tagged `idea`, and the static test asserts the layout and the grader types, not an arm."
  - "Recommended default taken (case count): one case, `plugin-evals/idea/ladder-brief/`, a feature run with a seeded `docs/backlog.md`, carrying three groups of graders, one per PRD check, rather than three cases. The decompose suite (the model to mirror) chose one case for cost, which scales as cases times arms times judge calls, and the three checks all read one produced idea.md and one backlog.md. A feature run is the case because it is the common run and it exercises the scaled-down path; the product-run path is a follow-up case only if a paid run shows the first one discriminates. The prompt pre-supplies every answer, including the pick ('take the rung you recommend'), as the decompose prompt does, so the run does not stall on a question."
  - "Recommended default taken (graders per check; types read from the help text and the existing suites): regex and file_exists where a produced file can be matched, llm only for judgement. Wiring graders: `skill-fired` (`tool_used`, Skill, `input_match` for `idea`; with-only), `idea-exists` (`file_exists`). Check 1, a showstopper that passes the four tests: `has-ambition-rung`, `has-the-demo`, `has-riskiest-piece`, `has-kill-test` (four `regex` over the produced idea.md, flags `m`, one per new heading; the without-plugin arm cannot produce them, which is the delta) and `showstopper-passes-four-tests` (`llm`). Check 2, the user's framing kept: `keeps-users-words` (`regex` over idea.md for a distinctive phrase the scaffold's pitch plants, so a replaced framing fails deterministically) and `rung-anchored-on-framing` (`llm`). Check 3, the moonshot saved and not chosen: `moonshot-seed-appended` (`regex` over `docs/backlog.md` for a line ending `(from: feature:<slug>)` that is new, with the slug fixed by the prompt) and `moonshot-not-chosen` (`llm`, also reads that the pre-existing seed line is unchanged). Eight regex/file_exists/tool_used graders and three llm graders; no `baseline` type, since `--ablation` already supplies the delta. The regex headings are exact strings from TEMPLATE.md, so the test pins that the grader patterns and the template agree."
  - "Recommended default taken (no tool, no module; the seam rule): nothing in this run needs a module. CLAUDE.md's seam rule asks for multiple real callers and observed divergence between copies before a shared module exists; here there is no code with logic to share, because the ladder, the tests, the seed form and the hand-off line are prose, and the seed grammar already has an owner (`protocol.parse_backlog` / `check_backlog`). The skill text restates the seed form (a skill cannot import protocol.py, ADR-0008) and the new tests assert the restated form against the owner by calling `protocol.check_backlog`, which is how the pins stay honest. Considered and rejected: a `backlog_append` helper, because the only caller would be this skill, which is text. No new import pair, no `one_owner.py` impact, no `factory.py` VERBS row."
  - "Release (PRD requirement, ADR-0095; confirmed by reading, not by an edit): this branch changes `skills/idea` and `skills/prd`, so the same wave `chore(release)` PR that picks up the Decompose lessons change bumps `.claude-plugin/plugin.json` once after the wave lands. The branch never edits that file. Confirmed: `.claude-plugin/plugin.json` already reads `\"experimental\": {\"evals\": \"plugin-evals\"}`, a directory, so `plugin-evals/idea/` is found by layout and needs no manifest entry; `git diff origin/main..HEAD -- .claude-plugin skills/launch-demo` is empty at this stage. `docs/pipeline-protocol.md` is not in the factory payload (`git grep` finds it nowhere under `factory/templates/`), so the Producers sentence needs no `update-manifest` run; Implement still re-checks `factory_init.MIRRORS` before committing. LEDGER.md, `plugin-evals/records/` and `evals/` are untouched."
---

# Architecture: An ambition ladder for the Idea stage, with an achievable showstopper as the default

## Approach

Prose in four places and tests that pin it. The Idea skill gains one
interview bullet, the ambition ladder, placed after the evidence question
and before the solution hunch, with its detail in a block below the list;
the Idea template gains four sections; the PRD skill gains one clause that
copies the demo into a success criterion; and a new suite
`plugin-evals/idea/` holds one harness case. The one write the skill
causes, appending seeds to `docs/backlog.md`, is done by the agent running
the skill, in the seed grammar the protocol already owns, and a one-sentence
protocol edit names Idea as a producer. Everything is checked offline by
`tests/test_idea_ambition_ladder.py` and `tests/test_idea_suite.py`, which
read files and call `protocol.check_backlog`; no model is called and
`claude plugin eval` is never invoked.

The other shape compared was a tool: a `backlog_append` or `idea_check`
module that writes the seed and checks a produced idea.md. It loses on the
seam rule (one caller, which is a text skill; no divergence to measure), on
the repo's stated constraint that Idea is text only, and because the seed
grammar already has an owner. A third shape, a new numbered step for the
ladder, loses because it would split the interview list in two and move the
evidence and hunch questions into different steps. A fourth, making
`launch-demo` read idea.md, is the issue's rejected alternative and the
brief's Owner decision rules it out.

| PRD success criterion | Where |
|---|---|
| Ladder step placed after evidence, before hunch; three rungs, Showstopper default | Ladder step, Skill text pins |
| Four tests and three prompts, each by exact phrase | Ladder step, Skill text pins |
| Pick recorded; moonshot saved never chosen; unachievable drops; feature runs scaled down | Ladder step, Seed write, Scaled-down version |
| TEMPLATE has the four headings | Idea template |
| Old idea.md still validates | Idea template, Test files |
| Seed line passes the grammar and gates, moonshot ends `(from: <run-ref>)` | Seed write, Test files |
| PRD line; launch-demo byte-identical | PRD hand-off line, Test files |
| Suite exists, tagged `idea`, wired by the manifest | Suite case, Test files |
| Cases cover the three checks, with and without arms | Suite case (arms by harness) |
| No paid run; LEDGER, records, plugin.json unchanged | Test files, Release (assumptions) |
| No existing eval definition edited | Test files |
| Five repo checks pass | Test files, Verify |

## Components

### Ladder step (`skills/idea/SKILL.md`)

- Responsibility: owns the interview behaviour. One bullet in step 4,
  `**Ambition ladder.**`, between the evidence bullet and the
  solution-hunch bullet, pointing at a block after the list headed
  `**The ambition ladder.**`. The block states: the three rungs anchored on
  the user's own words (quote their sentence; never rename their idea);
  Showstopper marked `recommended`; the pick is the user's and is recorded;
  Moonshot is never picked and is always saved as a seed; the four tests;
  the three prompts; the demotion rule; the seed rule; the scaled-down
  version. The Rules section keeps "don't replace their idea with yours"
  and gains the reconciling sentence below. Nothing else in the skill
  changes, and the skill never names a tool for the seed write.
- Collaborators: Idea template (the sections it fills), Seed write, the
  protocol's Seed backlog section.

Exact phrases (the tests pin these after whitespace-normalising, as the
decompose lessons tests do; Implement may adjust wording only by changing
the test in the same commit):

| Pin | Phrase |
|---|---|
| bullet label | `**Ambition ladder.**` |
| block label | `**The ambition ladder.**` |
| rungs | `Solid`, `Showstopper`, `Moonshot` |
| default | `Showstopper (recommended)` |
| anchor | `anchored on the user's own words` |
| pick recorded | `The pick is the user's, and it is recorded in idea.md` |
| moonshot | `The Moonshot is never chosen in this run and is always saved as a seed` |
| test 1 | `A 30-second demo exists` |
| test 2 | `It removes a step instead of speeding one up` |
| test 3 | `It is built on something only this product has` |
| test 4 | `It is achievable` |
| spike | `a spike of about two days` |
| demotion | `re-scope it once`, then `record it as the Moonshot and make Solid the pick` |
| prompts | `What would you show first in a demo?`, `What does the user do today that they would never have to do again?`, `What does the product already know that it is not using?` |
| tests written | `answered in writing, pass or fail with one clause of evidence` |
| scaled down | `For a feature run, ask the ladder as one question` |
| seed | `<seed text> (from: <run-ref>)`, `append only`, `never rewrite` |
| rules sentence | `The ladder offers a bigger version anchored on their words; it never swaps their idea for yours.` |

Order pins (index comparisons, as `test_the_step_sits_between_...` does):
`What evidence exists` < `**Ambition ladder.**` < `What's the rough shape of
a solution?`; `**Ambition ladder.**` < `**The ambition ladder.**`; the four
tests appear in the order listed; `**Write the artifact.**` after the
ladder block. The skill text must not backtick `prd.md` or `launch-demo`
filenames inside a numbered step (lint recitals) and must not show any
typed id.

### Scaled-down version (inside the ladder block)

- Responsibility: keeps a feature run light. Ask the ladder as one
  question: three one-line rungs built from the user's own sentence,
  Showstopper recommended, pick or correct. Ask the three prompts only when
  the user's framing names no demo moment, at most two, one at a time. Run
  the four tests silently first and surface only a failure. The spike is one
  sentence; each new section is two or three lines. A product run asks all
  three prompts, one at a time, and fills the sections in full.
- Collaborators: Ladder step. No file of its own.

### Idea template (`skills/idea/TEMPLATE.md`)

- Responsibility: four new sections, placed between `## Evidence` and
  `## Solution hunch`, in this order: `## Ambition rung`, `## The demo`,
  `## Riskiest piece + spike`, `## Cheapest kill test`. Ambition rung holds:
  the chosen rung in the user's words; the rungs not taken; four labelled
  test lines (`Demo`, `Removes a step`, `Only this product`, `Achievable`),
  each `pass` or `fail` plus one clause. The demo holds the script: before
  and after in two sentences, the after something seen, or `none — Solid
  chosen`. Riskiest piece holds the piece and the two-day spike. Cheapest
  kill test holds the smallest experiment that could prove the idea wrong.
  Placeholder text uses `<...>` slots only, like the rest of the template,
  and no typed ids.
- Collaborators: Ladder step. Read by the PRD hand-off line; read by
  nothing in code (measured: nothing parses idea.md sections).

### Seed write (skill instruction plus protocol sentence)

- Responsibility: states who writes the unchosen rungs to
  `docs/backlog.md`. The agent running Idea, after the pick and in the same
  stage-boundary commit as idea.md. Rule per the assumptions: seed every
  unchosen rung larger than the pick, Moonshot always, Solid never. Form:
  `- <seed text> (from: <run-ref>)` with run-ref `feature:<slug>` on a
  feature run and `product` on a product run; one line; no parentheses and
  no typed ids in the seed text; appended below the last line, existing
  lines never rewritten; the file is created with its existing header line
  when absent. `docs/pipeline-protocol.md`'s Producers sentence gains Idea:
  `Idea appends the rungs it did not take`.
- Collaborators: `protocol.check_backlog` and `lint.check_backlog` (the
  grammar's owner and its filesystem half); detectors C and I (the
  constraint on example text).

### PRD hand-off line (`skills/prd/SKILL.md`)

- Responsibility: one clause in step 4: when `idea.md` has a `## The demo`
  section holding a script (not `none`), copy it into a success criterion
  worded `the demo runs as written`, with the script as the criterion's
  checkable body. `verify` already tests every PRD success criterion
  (`skills/verify` step 3), so it is told by the criterion, not edited.
  `skills/launch-demo` is not touched.
- Collaborators: `prd.md` TEMPLATE success-criteria checkbox form; verify.

### Suite case (`plugin-evals/idea/ladder-brief/`)

- Responsibility: one harness case in the existing layout. `case.yaml`
  (`schema_version: "1.1"`, `name: ladder-brief`, `context.scaffold_script:
  scaffold.sh`); `prompt.md` (frontmatter `description`, `tags: [idea]`,
  `max_turns`, `timeout_seconds`, `allowed_tools: [Read, Glob, Grep, Skill,
  Write, Edit]`) with every interview answer pre-supplied, the pick
  included, and the slug fixed; `scaffold.sh` seeding a small repo (a docs
  directory, a one-paragraph pitch for a made-up scheduling tool that
  plants one distinctive phrase, a `docs/backlog.md` with its header and one
  existing seed), committed so the run can commit; and `graders/` per the
  grader assumption: `skill-fired`, `idea-exists`, `has-ambition-rung`,
  `has-the-demo`, `has-riskiest-piece`, `has-kill-test`,
  `keeps-users-words`, `moonshot-seed-appended`, and the three llm graders
  `showstopper-passes-four-tests`, `rung-anchored-on-framing`,
  `moonshot-not-chosen`. Never executed by this run. The with-plugin and
  without-plugin arms are the harness's own `--ablation with-without`
  default.
- Collaborators: the harness; `skills/idea` (what it would load).

### Test files

- Responsibility: `tests/test_idea_ambition_ladder.py` (skill text, template,
  seed, PRD line) and `tests/test_idea_suite.py` (static suite wiring),
  stdlib unittest, no network or model. Two files because the first reads
  skills and protocol, the second mirrors `tests/test_decompose_suite.py`;
  splitting keeps each under about 200 lines.
  - Skill text: `skill_text()` as in the lessons tests; every pin above by
    `assertIn`; the order pins by `assertLess(index, index)`; a count pin
    that the three rung names each appear (`text.count`), since `assertIn`
    cannot see missing duplicates; `assertNotIn` for typed-id shapes
    (`re.search(r"\b(PRD|ADR|WO)-\d{4}\b", text)` is `None`).
  - Template: the four headings exist, in order, between `## Evidence` and
    `## Solution hunch`; the four test labels exist; the template carries no
    typed id.
  - Old idea.md: builds a temp run dir holding the pre-change template
    form (the seven original sections as a literal in the test), runs
    `protocol.stage_states` and asserts the idea stage is `done`; runs
    `protocol.parse_frontmatter` on it and asserts the three keys; asserts
    `lint.check_templates(ROOT)` is `[]`. This is the cheap pin of a fact
    the measurement showed holds.
  - Seed: builds the seed line from the skill's own documented form with a
    sample slug (`feature:sample-slug`), asserts `protocol.check_backlog`
    returns `[]` for a file of header plus an existing line plus the new
    line, asserts `protocol.parse_backlog` reports the new line's origin as
    the run-ref, asserts a line missing the suffix yields a problem string,
    and asserts the skill text shows no real slug.
  - PRD line: `skills/prd/SKILL.md` contains `the demo runs as written`,
    `## The demo` and `idea.md`; `skills/verify/SKILL.md` and
    `skills/launch-demo/SKILL.md` are byte-identical to `main`'s
    (`git diff --name-only main -- skills/launch-demo skills/verify` is
    empty; the test skips cleanly when `main` is absent, as the decompose
    suite's `main_exists` does).
  - Suite wiring (mirrors `tests/test_decompose_suite.py`, reusing
    `tests.test_plugin_eval_tags.case_tags`): the manifest value is
    `plugin-evals`; the case directory holds `case.yaml`, `prompt.md`,
    `scaffold.sh`, `graders`; every `plugin-evals/idea/*/prompt.md` carries
    the `idea` tag; grader file set and `type:` values equal the table above
    and every type is in `{regex, tool_order, tool_used, file_exists, llm,
    baseline}`; the four heading regexes in the graders each match the
    corresponding TEMPLATE.md heading (so grader and template cannot
    drift); the moonshot-seed regex accepts the skill's seed form and
    rejects a line with no suffix; the prompt fixes a slug and the scaffold
    backlog's header and existing line parse under `protocol.check_backlog`;
    the scaffold plants the phrase `keeps-users-words` greps for; the case
    never names `claude plugin eval` and no file in `plugin-evals/idea/`
    imports a network or subprocess module; protected paths
    (`evals`, `LEDGER.md`, `plugin-evals/records`, the other four
    `plugin-evals/` suites, `.claude-plugin`, `skills/launch-demo`) match
    `main`, and no untracked file appears under them.
- Collaborators: `protocol`, `lint`, `tests.test_plugin_eval_tags`.

## Data model

No stored state and no schema. The records that cross a boundary are text:

```
idea.md  (new sections, between Evidence and Solution hunch)
  ## Ambition rung
    Chosen: <rung>, in the user's words: "<their sentence>"
    Not taken: <rung>: <one line>; ...
    Demo: pass | fail — <what is seen after>
    Removes a step: pass | fail — <which step is gone>
    Only this product: pass | fail — <what only this product holds>
    Achievable: pass | fail — <riskiest piece; two-day spike>
  ## The demo
    <before and after, two sentences> | none — Solid chosen
  ## Riskiest piece + spike
  ## Cheapest kill test

docs/backlog.md  (append only)
  - <seed text> (from: feature:<slug>)      # product run: (from: product)

prd.md  (success criteria)
  - [ ] The demo runs as written: <the script copied from idea.md>
```

Access patterns: the Idea agent writes idea.md once and appends at most two
seed lines once; the PRD agent reads The demo once; verify reads the
criterion once. No consistency question: the seed append and idea.md land in
one commit.

## Interfaces & contracts

### Ladder question (skill to user)

- Input: the user's answers to the problem, who, why-now and evidence
  questions, and their opening sentence. Output: the user's pick (Solid or
  Showstopper), recorded under `## Ambition rung`; plus the demo script,
  riskiest piece and spike, and kill test.
- Failure modes: the user declines the ladder: record `Chosen: Solid` and
  `declined the ladder` and seed the Moonshot only if the user named one;
  never block the stage. The user picks Moonshot: say it is saved, not
  chosen, and ask for the Showstopper or Solid pick. The user gives no demo
  moment after two prompts on a feature run: Showstopper test 1 fails and
  the demotion rule applies. A test fails: say which, re-scope once, then
  demote.

### Seed append (skill to `docs/backlog.md`)

- Input: the unchosen rungs larger than the pick, the run-ref. Output: one
  appended line each, in the ADR-0029 form. Failure modes: file absent,
  create it with its header line; file unreadable or the write refused,
  say so, put the seeds in idea.md's `Not taken` line and do not retry
  silently; a seed that would fail `protocol.check_backlog` (multi-line,
  a missing suffix, a trailing parenthesis group in the text) is not
  written. `lint.py` is the check that catches a malformed line.

### PRD demo hand-off (idea.md to prd.md)

- Input: `## The demo` holding a script. Output: one success criterion
  worded `the demo runs as written`. Failure modes: The demo is `none` or
  the section is absent (an old idea.md): write no criterion and say
  nothing; the PRD skill is unchanged for those runs.

### Suite case contract (harness side)

- Input: `claude plugin eval . --tag idea` with the flags ADR-0081 fixes.
  Output: the CLI's aggregate JSON with `WITH`, `W/OUT` and the delta.
  Failure modes: the harness owns them. This run asserts only that the case
  is well formed and selected.

## Stack & dependencies

- Markdown skill text and template — the repo's own medium for a skill.
- Python 3 stdlib `unittest` — the repo's hard convention; tests import
  `protocol`, `lint` and `tests.test_plugin_eval_tags`, all existing.
- The harness's own grader types for the suite — `regex`, `file_exists`,
  `tool_used`, `llm`; no code-running grader exists (ADR-0114's finding).
- No new tool, module, seam, mirror pair, VERBS row, CLAUDE.md bullet,
  workflow or Makefile line. Edits Implement owns: `skills/idea/SKILL.md`,
  `skills/idea/TEMPLATE.md`, `skills/prd/SKILL.md`,
  `docs/pipeline-protocol.md` (one sentence), `plugin-evals/idea/**`, the
  two test files. No edit to `.claude-plugin/plugin.json`, `LEDGER.md`,
  `plugin-evals/records/`, `evals/`, `skills/launch-demo`, `skills/verify`
  or any existing suite.

## Decisions & alternatives

- **Prose plus tests, no module** over a `backlog_append` or `idea_check`
  tool — one caller that is a text skill, no divergence, and the grammar has
  an owner already (CLAUDE.md seam rule).
- **One bullet in step 4 with a detail block** over a new numbered step — a
  step would split the interview list and separate the evidence and hunch
  questions it must sit between.
- **Agent appends the seed by instruction, and the Producers sentence names
  Idea** over leaving the protocol silent — the protocol says only Operate
  and Capture produce; an unlisted producer is the drift the repo's tests
  exist to prevent. Reversible in a sentence, so no ADR.
- **Seed every unchosen rung larger than the pick, Moonshot always** over
  seeding every unchosen rung — Solid is a strict subset of any larger pick
  and would file already-chosen work.
- **Each test answered in writing with a clause of evidence** over a bare
  checklist — a pass becomes inspectable; it does not become objective, and
  that is a stated limit.
- **Demotion after one re-scope** over drop-on-first-fail — limits the
  over-demotion the PRD names as a risk.
- **One feature-run case, three grader groups** over three cases or an
  on/off pair per check — cost scales with cases times arms times judges,
  the harness supplies the without-plugin arm, and one produced idea.md and
  backlog.md serve all three checks.
- **Regex graders on the produced file for headings and the planted phrase,
  llm only for judgement** over llm everywhere — free, deterministic, and
  the without-plugin arm fails them by construction, which is the delta.
- **Hand-off by the PRD's own success criterion, verify and launch-demo
  untouched** — the Owner's recorded decision; verify already tests every
  criterion.
- **Old-form idea.md pinned by a test** though measurement shows nothing
  parses idea.md sections — the cheapest way to keep that true as the
  template and protocol evolve.
- **No ADR** — every decision above is reversible by editing text in one
  commit; the protocol's three-leg test fails on hard-to-reverse.

## ADRs

none — no decision met the ADR bar.
