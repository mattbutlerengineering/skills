---
stage: decompose
run: feature:kb-from-knowledge-work-plugins
date: 2026-11-08
assumptions:
  - "No live review of the cut (step 6): the interview is answered from autorun-brief.md, prd.md and architecture.md, and the brief says nothing about milestones or sizing. Milestone boundaries are the skill's own default (each milestone independently demonstrable, one item per sitting, vertical slices where the architecture allows): lint ages an outside check first, because it is the observed gap with a first user in this repo; harvest's human turns second and memory third, because both extend kb_harvest.py and memory also touches kb.py's dispatch; the skill text fourth, because it names the flag and problem strings the tools add; the battery last. The Owner can move them at the merge gate."
  - "No tracker mirror and no work-order ids: the brief (Tracker) says reference #1274 only, mirror no work orders, create no issues and apply no wo:* labels. Rows carry short labels (K1, K2, ...) leading the bold span, the form size-band-calibration and decompose-outcome-signals used, and every Blocked by names an item by its label and title. No row carries a (tracker: #N) reference."
  - "Sizes are the factory's S/M/L bands written `size:` on the row line, as earlier no-work-order breakdowns write them. The skill text names no sizing rule, so each size is the drafter's reading of one sitting: S for a text edit or one page, M for a test module or a tool change with several functions. No row is L."
  - "Test first: each tool item is blocked by a tests item whose Accept says its cases exist and fail against the tree before the change lands, per the brief's constraint ('Test first where behaviour is testable'). The skill-text items are blocked by the shape-test item for the same reason; the lint-clean fixture pages for items 4, 5, 7 and 8 pin existing behaviour, so they pass on arrival and say so."
  - "docs/factory/decompose-lessons.jsonl does not exist in this repo, so step 3 had nothing to read and the draft is unchanged by it."
  - "The three NOT RUN criteria (PRD 13, item 3's precision hand count; PRD 32, the live demo; and the routing eval, owed only if the knowledge-base skill's frontmatter description changes, which K11 forbids) are not rows to build. K12 records them for the Owner with their procedure or command, per the run's standing instructions."
  - "K3 lets Implement re-run the page's two read-only `gh api` commands to set `checked:`, and otherwise use 2026-11-08, the date the brief records the claim holding, as architecture.md's assumption says. That is Implement's network read, never lint's."
  - "Detector O (ADR-0072) counts only work-order rows as citing a PRD section, and this run has none, so `gates.py` failed on six uncited prd.md sections. Following svg-mechanical-check's precedent, Decompose added a reasoned `coverage-waiver` comment directly under each of those six headings in prd.md (Out of scope already carried one) and commits it with this artifact, because coverage is a Decompose-time property. No prd.md prose changed; the waiver points at this file's Criterion trace."
  - "The battery (run_tests.py, lint.py, kb.py drift, gates.py and its selftest) is run once at the end, in K12, and again by Verify, not per item; items carry narrower checks."
---

# Breakdown: Teach the knowledge base what it cannot see yet

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met.

Component names, function names and problem strings are architecture.md's.
PRD criteria are cited as `PRD n`, counting prd.md's success-criteria
checkboxes top to bottom (1 to 33). New tests point every tool at a fixture
directory under a temporary directory, never the real memory directory, real
transcripts or the home directory.

## Milestone 1: lint ages a declared outside check, offline

Demonstrable: `python3 kb.py lint` over a fixture `docs/kb/` reports a page
past its declared age and each malformed declaration, runs nothing to do it,
and this repo's `docs/kb/main-unprotected.md` declares its check and lints
clean.

- [x] **K1 Age-check tests** — cases in `tests/test_kb.py` for `kb.age_problems(page, today)` and `kb.lint(root, git=_git, today=None)` over fixture pages — size:M
  - Accept: the cases exist and fail before K2 lands. Over a fixture page with `checked-against`, `checked` and `max-age: 30d`, `lint` with an injected `today` one day after `checked` + 30 days returns exactly one string `kb: <path> is past its declared age: checked <date>, max-age <N>d, due <due> — re-check it` naming that page, and with `today` on the due date returns none. Each malformed form returns its exact string from architecture.md: a missing field (one string per missing field when `checked` or `max-age` is present), an empty `checked-against`, a `checked` that is not a date, a `checked` after today, and a `max-age` that is not a whole number of days (`0d`, `30`, `thirty`), so no malformed page reads as fresh. An offline case calls `age_problems` and `lint` with `cli.runner` and `socket.socket` patched to raise on any call and gets the same strings. A page with `checked-against` alone and a page with none of the three fields each return no age string (PRD 1, 2, 3, 24).
  - Blocked by: —
- [x] **K2 Age check in kb.py** — add `age_problems` and the `today` parameter to the Page contract and lint — `kb.py` component, per ADR-0125 — size:M
  - Accept: the K1 cases pass, and every case already in `tests/test_kb.py` passes unedited. `lint` orders field problems, then link and age problems per page, then index, then staleness, as architecture.md's interface states. `age_problems` reads only the parsed fields and `today`, and the rendered index line never includes `checked-against`, `checked` or `max-age`. Run over this repo before K3, `python3 kb.py lint` prints the same output it printed on `main` for the six current pages (PRD 1, 2, 3, 25).
  - Blocked by: K1 Age-check tests
- [x] **K3 main-unprotected.md declares its check** — the First user — `docs/kb/main-unprotected.md` component: add the three fields and drop the hand-written re-check paragraph — size:S
  - Accept: the page's frontmatter carries `checked-against` naming the GitHub API (and what it was not checked against), `checked` as the date Implement re-ran its two `gh api` commands or 2026-11-08 if it could not, and `max-age: 30d`; the two `gh api` commands stay as how to re-check; the "Re-check … nothing in the repo records the setting" paragraph is gone; `summary`, `sources`, `verified` and `related` are unchanged, so the knowledge-base index lines in `CLAUDE.md` and `AGENTS.md` show no diff; `python3 kb.py lint` over this repo exits 0 and prints `kb: 0 problem(s)` (PRD 4).
  - Blocked by: K2 Age check in kb.py

## Milestone 2: harvest lists human corrections and answered questions

Demonstrable: `python3 kb.py harvest --projects-dir <fixture>` prints a
`human_turns` list holding the fixture's correction and answers and nothing
for its approvals, autonomous or subagent transcripts, with `arcs`,
`recurring_errors` and `scanned` unchanged.

- [ ] **K4 Human-turn tests** — cases in `tests/test_kb_harvest.py` for `kb_harvest.human_turns(records)` and the `human_turns` key, over fixture transcripts under a temporary projects directory — size:M
  - Accept: the cases exist and fail before K5 lands. A fixture top-level transcript whose human turn opens with correction wording after an agent action yields exactly one `human_turns` entry with `kind` `correction` and `signal` `correction-wording`, carrying a `human` excerpt and an `agent` excerpt each at most 160 characters. An agent text turn ending in `?` followed by a human text answer yields one `answer` with signal `after-agent-question`; a non-error tool_result of an `AskUserQuestion` tool_use yields one `answer` with signal `question-tool`. Approvals from `APPROVALS` ("go ahead", "ok") after a question, plain new instructions, `isMeta` records and text opening with a tag yield none; two human turns in a row yield at most one candidate; a fixture autonomous transcript with no human turn after the first, a file named `agent-*`, and records carrying `isSidechain` yield none. Over the existing harvest fixtures `arcs`, `recurring_errors` and `scanned` are equal to their current values and `human_turns` is present and empty. Every case passes `projects=` or `--projects-dir` a temporary directory (PRD 9, 10, 11, 12, 27).
  - Blocked by: —
- [ ] **K5 Human turns in kb_harvest.py** — add `human_turns`, the `CORRECTION` and `APPROVALS` patterns, and the always-present `human_turns` key to the Candidate miner — `kb_harvest.py` component, mined only from top-level transcripts — size:M
  - Accept: the K4 cases pass, and every case already in `tests/test_kb_harvest.py` passes unedited. `mine(paths)` calls `human_turns` once per path not named `agent-*`, computes `arcs` and `recurring_errors` exactly as before, and writes no file. `kb_harvest.py` gains no import beyond `cli` and the standard library (PRD 9, 10, 11, 12, 25).
  - Blocked by: K4 Human-turn tests

## Milestone 3: harvest reads auto-memory on request and pairs it with pages

Demonstrable: `python3 kb.py harvest --projects-dir <fixture> --memory` pairs
the three fixture memory files named in PRD 5 with their pages, lists one
unpaired memory-only gotcha, and never shows a user-scoped entry or the
memory index file.

- [ ] **K6 Memory tests** — cases in `tests/test_kb_harvest.py` for `kb_harvest.memory_type(text)`, `kb_harvest.pair(stem, slugs)`, `kb_harvest.memory_candidates(memory_dir, slugs)` and `harvest(..., memory=True, kb_dir=...)` over a fixture memory directory and fixture `docs/kb/` — size:M
  - Accept: the cases exist and fail before K7 lands. Fixture memory files named `cross-pr-hazard-pairwise-merge-test`, `manifest-regen-stray-patch-files` and `pr-body-no-work-order-waiver` (text written for the test) pair with fixture pages `cross-pr-merge-hazards`, `manifest-regen` and `pr-body-contract`, with `shared` equal to architecture.md's worked tokens; a fixture `gh-pr-edit-broken-use-rest` has `page` null and empty `shared`. A file with `type: user` holding a sentinel string adds one to `user_scoped`, and neither its name nor the sentinel appears anywhere in the printed JSON; `MEMORY.md` is not listed. A file with no frontmatter block, no `type`, two distinct `type` values, an unknown value, and an undecodable one each add one to `skipped`, and `listed + user_scoped + skipped` equals the files examined. With `--memory` and no memory directory, harvest returns the one problem `harvest: no memory directory at <path>` and prints no JSON; with no `kb_dir` every candidate is unpaired; without `--memory` the output has no `memory` key. After a harvest over the memory and transcript fixtures every fixture file and the fixture `docs/kb/` are byte-identical to before, and every `description` excerpt is at most 160 characters. Every case uses a temporary projects directory (PRD 5, 6, 7, 26, 27).
  - Blocked by: K5 Human turns in kb_harvest.py
- [ ] **K7 Memory source and the --memory flag** — add `memory_type`, `pair`, `memory_candidates` and the `memory`/`kb_dir` parameters to the Candidate miner — `kb_harvest.py`, and have the Page contract and lint — `kb.py` dispatch `kb_harvest.main(argv[1:], KB_DIR)` with `[--memory]` in its usage text — size:M
  - Accept: the K6 cases pass, and every earlier case in `tests/test_kb.py` and `tests/test_kb_harvest.py` still passes. `PAIR_MIN = 2` and the stopword list are architecture.md's. No new module is created and `tests/test_dual_membership.py` passes unedited. `kb_harvest.py`'s docstring carries a one-line credit to anthropics/knowledge-work-plugins (Apache-2.0) for the two new sources. `python3 kb.py harvest --help` or a bad flag prints usage containing `[--memory]` and exits 2 (PRD 5, 6, 7, 26).
  - Blocked by: K6 Memory tests; K2 Age check in kb.py

## Milestone 4: the skill, rubric and ingest text teach items 1 to 8

Demonstrable: `python3 -m unittest tests.test_knowledge_base_shape` passes
over the shipped skill files, and fixture pages in each new shape lint clean.

- [ ] **K8 Shape tests and lint-clean fixtures** — new `tests/test_knowledge_base_shape.py` with text assertions over the shipped skill files (the `tests/test_polish_shape.py` pattern), plus lint-clean fixture pages in `tests/test_kb.py` — size:M
  - Accept: the shape cases exist and fail on the current text. They assert: `references/page-rubric.md` names `checked-against`, `checked` and `max-age` and when to declare all three, a class page proposed when three or more pages or candidates share one cause, a gotcha summary that leads with the symptom inside the 200-byte cap, and one optional `Wrong:` / `Right:` pair under Shape; `references/ingest.md` routes memory, human-turn and setup-answer candidates through the NOOP, CONFLICT, UPDATE, DELETE and ADD table with a human promoting, says a user-scoped or personal fact is never proposed, and carries the one-rule-over-many-instances paragraph; `skills/knowledge-base/SKILL.md` setup asks the newcomer-mistake question one question per turn, at most three, each with a recommendation, keeps answers inside the five-page cap and propose-and-promote, skips the step and says so with no human present, has a flow-table row to run it alone, names a class page in the over-budget advice, and credits anthropics/knowledge-work-plugins (Apache-2.0); no file under `skills/knowledge-base/` contains `~/.claude`, `.claude/projects`, `CLAUDE_CONFIG_DIR`, `MEMORY.md` or a `/memory/` path segment. The `tests/test_kb.py` additions, a class page (one rule, three cited instances), a gotcha page whose summary leads with no symptom, a page with one `Wrong:` / `Right:` pair and one without, each lint clean under `lint` and pass on arrival because they pin existing behaviour (PRD 8, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 28, 29).
  - Blocked by: —
- [ ] **K9 Page rubric text** — the Page rubric — `references/page-rubric.md` component: the three optional fields, class pages under Admit, the symptom-first gotcha summary, the optional wrong/right pair — size:S
  - Accept: the rubric-file cases in `tests/test_knowledge_base_shape.py` pass; "exactly these fields" becomes "these four fields, plus three optional ones"; the class-page rule names three or more pages or candidates sharing one cause; the symptom-first rule stays inside the existing 200-byte summary cap and adds no lint rule; every line is restated in this repo's words and no sentence is copied from knowledge-work-plugins (PRD 14, 16, 21, 23).
  - Blocked by: K8 Shape tests and lint-clean fixtures
- [ ] **K10 Ingest rules text** — the Ingest rules — `references/ingest.md` component: how to judge a human-turn, memory and setup-answer candidate through the unchanged verb table, the one-rule-over-many-instances paragraph, harvest kinds named — size:S
  - Accept: the ingest-file cases in `tests/test_knowledge_base_shape.py` pass; a paired memory candidate is judged NOOP, CONFLICT or UPDATE and an unpaired one ADD or NOOP; a candidate is a lead whose lesson cites a repo path, never a memory file or transcript; a setup answer with no repo file to cite becomes a proposed always-loaded guardrail or a NOOP; memory text and human words are restated, never pasted; a harvest-sourced item names its kind so the Promoter can decline a kind wholesale; no new path writes to `docs/kb/` (PRD 14, 28).
  - Blocked by: K8 Shape tests and lint-clean fixtures
- [ ] **K11 Skill body text** — the Skill body — `skills/knowledge-base/SKILL.md` component: setup's tribal-knowledge step and flow-table row, step 2a's two new candidate kinds and `--memory`, step 3's age and malformed-declaration problems and class-page remedy, "The tool" usage, the credit paragraph — size:M
  - Accept: every case in `tests/test_knowledge_base_shape.py` passes; step 3 tells the agent what to do with a `is past its declared age` problem (re-run the page's check, then update `checked`) and with each malformed-declaration string; step 2a describes memory as the harness's auto-memory for this repo where the harness keeps one, naming no path; "The tool" lists `[--memory]`; `git diff main -- skills/knowledge-base/SKILL.md` shows no change between the frontmatter `---` lines, so `description` is unchanged and no routing eval is owed (PRD 8, 14, 18, 19, 20, 29, 30).
  - Blocked by: K8 Shape tests and lint-clean fixtures; K7 Memory source and the --memory flag

## Milestone 5: the battery passes and the NOT RUN criteria are recorded

Demonstrable: the four battery commands exit 0 from the worktree, nothing
outside the brief's In list changed, and the Owner has the three NOT RUN
procedures.

- [ ] **K12 Battery, invariants and NOT RUN record** — run the battery and the run-wide invariant checks, and log the three NOT RUN criteria in Notes below for Verify — size:S
  - Accept: `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift` and `python3 gates.py && python3 gates.py --selftest` each exit 0, with their summary lines quoted in Notes; `python3 factory_init.py update-manifest`, run after deleting any stray `.orig`/`.rej`, leaves `git status --porcelain` with no manifest change (neither `kb.py` nor `kb_harvest.py` is mirrored); `git diff main -- LEDGER.md .claude-plugin/plugin.json` prints nothing; `grep -rn "Path.home\|~/.claude" tests/test_kb.py tests/test_kb_harvest.py tests/test_knowledge_base_shape.py` finds no new hit outside the neutrality test's own forbidden-string list; the six current `docs/kb/` pages other than `main-unprotected.md` show no diff. Notes records, each as NOT RUN for the Owner: PRD 13 (hand-label the new-kind candidates from `python3 kb.py harvest --days N` over this repo's interactive transcripts on the Owner's machine and record the counts), PRD 32 (the demo's four steps, the last needing a model session against the real memory directory), and the routing eval `python3 trigger_eval.py`, owed only if a later stage changes the skill's `description` (PRD 25, 27, 30, 31, 33).
  - Blocked by: K3 main-unprotected.md declares its check; K9 Page rubric text; K10 Ingest rules text; K11 Skill body text

## Criterion trace

| PRD | Criterion | Rows |
|---|---|---|
| 1 | Age is flagged | K1, K2 |
| 2 | Lint stays offline | K1, K2 |
| 3 | Malformed declarations are reported | K1, K2 |
| 4 | This repo's page uses it | K3 |
| 5 | Memory duplicates are paired | K6, K7 |
| 6 | A memory-only gotcha is unpaired | K6, K7 |
| 7 | User scope is excluded | K6, K7 |
| 8 | Harness-neutral skill text | K8, K11 |
| 9 | A correction is listed | K4, K5 |
| 10 | An answered question is listed | K4, K5 |
| 11 | Plain turns are not listed | K4, K5 |
| 12 | The kind is separate | K4, K5 |
| 13 | Precision is measured | NOT RUN for the Owner; procedure recorded by K12 |
| 14 | Class-page guidance exists | K8, K9, K10, K11 |
| 15 | Class pages are valid pages | K8 |
| 16 | Symptom-first guidance exists | K8, K9 |
| 17 | No new failure on existing summaries | K8 |
| 18 | Setup asks | K8, K11 |
| 19 | Answers are candidates | K8, K11 |
| 20 | No human, no question | K8, K11 |
| 21 | Shape allows a wrong/right pair | K8, K9 |
| 22 | Pair optional both ways | K8 |
| 23 | A page can say what it was verified against | K8, K9 |
| 24 | Verified-against optional both ways | K1 |
| 25 | Existing pages are unaffected | K2, K5, K12 |
| 26 | Harvest stays read-only | K6, K7 |
| 27 | Fixtures only | K4, K6, K12 |
| 28 | Human still promotes | K8, K10 |
| 29 | Source credited | K8, K11 (and K7's docstring line) |
| 30 | Routing unchanged | K11, K12; the routing eval itself NOT RUN unless the description changes |
| 31 | The battery passes | K12 |
| 32 | The demo runs as written | NOT RUN for the Owner; steps recorded by K12 |
| 33 | LEDGER untouched | K12 |

## Design gaps found

none. Every architecture component (Page contract and lint, Candidate
miner, Skill body, Page rubric, Ingest rules, First user, Tests) appears in
an item, and every interface (`kb.lint`, `kb.age_problems`, `kb.main`,
`kb_harvest.harvest`, `human_turns`, `memory_type`, `pair`,
`memory_candidates`, the `--memory` flag and the skill-text contracts) has an
Accept line. architecture.md's memory-format and transcript-shape
assumptions are carried into K4 and K6 as fixture shapes, not resolved here.

## Notes

Implement, 2026-11-08 (unattended, autorun).

- **K1, red before K2.** `python3 -m unittest -v tests.test_kb.TestAge`
  against the tree before K2: 12 of 13 cases (16 counting subtests)
  ERROR with `TypeError: lint() got an unexpected keyword argument
  'today'` or `AttributeError: module 'kb' has no attribute
  'age_problems'`; `FAILED (errors=16)`. The one case that passed on
  arrival, `test_the_index_line_never_carries_the_fields`, pins existing
  behaviour (K2's Accept line that the rendered index never includes the
  three fields), so it is not vacuous.
- **K1 default taken.** The offline case injects the git runner as a
  stub, as every `TestLint` case does, and patches `cli.runner` and
  `socket.socket` to raise `AssertionError`; patching `cli.runner`
  without the stub would make the existing staleness check (not the age
  check) report `git is unavailable`, which is not what the case tests.
- **K2, green.** `python3 -m unittest tests.test_kb`: `Ran 42 tests`,
  `OK`; no existing case edited (only imports and a helper were added).
  `python3 kb.py lint` over this repo before K3: `kb: 0 problem(s)`,
  the same as before the change.
- **K2 default taken.** Within one page, `age_problems` orders its
  strings: missing fields (in `checked-against`, `checked`, `max-age`
  order), empty `checked-against`, the `checked` problem, the `max-age`
  problem, then past-age. A future `checked` is not also aged. The
  architecture fixes the strings, not their order within a page.
- **K3, the check re-run.** Implement ran the page's two read-only
  commands on 2026-11-08:
  `gh api repos/mattbutlerengineering/skills/branches/main/protection`
  printed `{"message":"Branch not protected",...,"status":"404"}` and
  `gh: Branch not protected (HTTP 404)` (exit 1), and
  `gh api repos/mattbutlerengineering/skills/rulesets` printed `[]`
  (exit 0). The claim holds, so `checked: 2026-11-08`. `verified:` stays
  `f2ba566`, which `git merge-base --is-ancestor` confirms is on
  `origin/main` (6f921cb), as the page rubric asks. The body's
  "Checked 2026-10-10" lead-in now points at the `checked:` field
  instead of carrying a second date. `python3 kb.py lint`:
  `kb: 0 problem(s)`, exit 0; `kb.py index` left `CLAUDE.md` and
  `AGENTS.md` unchanged. With `today` 2026-12-09 lint reports
  `kb: docs/kb/main-unprotected.md is past its declared age: checked
  2026-11-08, max-age 30d, due 2026-12-08 — re-check it`; with
  2026-12-08 it reports nothing.
