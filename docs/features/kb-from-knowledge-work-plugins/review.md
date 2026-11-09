---
stage: review
run: feature:kb-from-knowledge-work-plugins
date: 2026-11-08
assumptions:
  - "No live arbitration: Review ran unattended for autorun, and the skill's user-arbitration step is answered by the run's standing instructions. Critical and major findings are fixed test-first; minor ones are fixed when cheap and otherwise deferred with a logged reason."
  - "The diff is scoped with git diff origin/main...HEAD (merge base 6f921cb), because origin/main has moved one commit since the branch was cut."
  - "Severity of the three output-leak routes: each needs a hand-made file shape (a symlink, a flow mapping) or a transcript shape this stage could not confirm against real transcripts, which were off limits. None was shown to happen with a harness-written file, so they are ranked major, not critical. All three are fixed."
  - "The copied-text check is a word n-gram overlap (4, 5, 6 and 8 words) between the lines this run adds under skills/knowledge-base/, kb.py, kb_harvest.py and docs/kb/ and the six upstream files the brief cites. The gotchas file compared is small-business/skills/build-agent/reference/gotchas.md."
  - "ADR-0125 is read as treating a max-age that is a valid <N>d but outlasts the calendar (past date.max) as never due, and a value longer than nine digits as malformed. ADR-0125 states neither case."
---

# Review: Teach the knowledge base what it cannot see yet

## Scope

`git diff origin/main...HEAD` on `feat/kb-from-knowledge-work-plugins`,
17 run commits from the idea stage through Verify: `kb.py`,
`kb_harvest.py`, `skills/knowledge-base/SKILL.md` and its references
`ingest.md` and `page-rubric.md`, `docs/kb/main-unprotected.md`,
ADR-0125, ADR-0126, the status line of ADR-0078, the ADR index, the
backlog seed, and tests `test_kb.py`, `test_kb_harvest.py`,
`test_knowledge_base_shape.py` and `test_dual_membership.py`. Inputs
read: verification.md (31 PASS, 0 FAIL, 2 NOT RUN), breakdown.md,
architecture.md, prd.md, autorun-brief.md, the two ADRs,
docs/pipeline-protocol.md, CLAUDE.md, AGENTS.md and CONTEXT.md.

The extra checks this run's brief asked for:

- **Breaking user-scope exclusion.** Probed with fixtures in a
  temporary directory: repeated `type:` keys, nested metadata, a list
  item, a flow mapping, quoted and capitalised values, CRLF, a BOM, a
  fence with a trailing tab, an unclosed block, `type: user` in the
  body, a non-breaking space, line and vertical-tab separators, bytes
  that are not UTF-8, a subdirectory, a directory named `*.md`, and
  symlinks to the index and to a user entry. Two shapes leaked and are
  fixed: findings 2 and 5. Every other shape was skipped or counted as
  user-scoped.
- **Harness neutrality.** The skill text names no harness path. Its
  only `.claude` mentions are repo-relative rules files that were there
  before this run. The memory directory is touched only under
  `--memory`: `harvest` builds the path either way but calls
  `is_dir()` and reads it only when the flag is set, and
  `test_without_the_flag_there_is_no_memory_key` pins that.
- **"Never copied" (PRD 29).** Fetched as untrusted data:
  productivity/skills/memory-management/SKILL.md,
  customer-support/skills/kb-article/SKILL.md,
  small-business/skills/build-agent/reference/capture.md,
  small-business/shared/absent-is-not-zero.md,
  data/skills/data-context-extractor/SKILL.md and
  small-business/skills/build-agent/reference/gotchas.md. The run's
  2,888 added words share no 4-word run with any of them. At 3 words
  the only matches were "is how the" and "that you skipped", both
  against gotchas.md. No sentence is copied. The Credit section's
  Apache-2.0 attribution stands as written.
- **Date-dependent lint in CI.** No CI path runs `kb.py lint`. The
  Makefile's `check` target runs `lint.py`, `kb.py drift`, `gates.py`
  and `run_tests.py`, and no workflow under `.github/` names `kb.py`.
  No test lints the repo's real `docs/kb/`: every age test injects
  `today` into a fixture tree. ADR-0125's Consequences already records
  the hazard for any later change that adds `kb.py lint` to the gate.
  No finding. Note that `main-unprotected.md` (checked 2026-11-08,
  30d) comes due on 2026-12-09 for anyone who runs `kb.py lint` by
  hand, which is the intended behaviour.
- **Mutation.** Deleted the `if kind == "user"` block in
  `memory_candidates` and ran `tests.test_kb_harvest`: 2 failures,
  `test_user_scope_and_the_index_never_reach_the_output` among them,
  with the sentinel showing up in the printed JSON. Reverted with
  `git checkout -- kb_harvest.py`, and `git diff --stat kb_harvest.py`
  printed nothing. The tests are not vacuous on this line.

## Findings

### Major: harness-injected text in a human turn reached the `human_turns` excerpt

- Scenario: a `type: user` record whose content is
  `[{"type": "text", "text": "No, revert that."}, {"type": "text",
  "text": "<system-reminder>…</system-reminder>"}]`, or the string
  `"No, revert that.\n<system-reminder>…</system-reminder>"`. The
  turn did not open with `<`, so it was mined as a correction and the
  reminder (which can carry always-loaded and memory content) was
  printed in `human`, up to 160 characters. The module docstring says
  harness-injected turns yield none.
- Standard: none
- Decision: fixed in faf4bf8. `_words` keeps only text items that open
  with no tag, cut before an appended `<system-reminder>`, and
  `test_injected_text_after_the_human_words_is_dropped` covers both
  shapes.

### Major: a symlinked memory entry was followed, so the index or an outside file could be listed

- Scenario: `memory/alias.md` is a symlink to `memory/MEMORY.md` (or to
  a file outside the memory directory) whose frontmatter says `type:
  feedback`. The `MEMORY.md` name check reads the link's name, and
  `is_file()` follows the link, so the target's description was listed
  under `alias.md`.
- Standard: none
- Decision: fixed in faf4bf8. A symlinked entry is counted under
  `skipped` and never read, so `listed + user_scoped + skipped` still
  equals the files examined. `test_a_symlinked_entry_is_skipped_never_read`
  covers both targets.

### Major: an absurd `max-age` crashed `kb.py lint` instead of producing a problem string

- Scenario: a page with `checked: 2026-01-01` and `max-age: 99999999d`.
  `checked + timedelta(days=…)` raised `OverflowError: date value out
  of range`, and `max-age: 9999999999d` raised in `timedelta` itself,
  so lint died with a traceback for the whole knowledge base. That
  breaks the problem-string contract and ADR-0125 decision 3.
- Standard: none
- Decision: fixed in e51413b. `MAX_AGE` takes at most nine digits (a
  longer value is reported as not a whole number of days), and an age
  that outlasts `date.max` is never due. Two new `TestAge` cases cover
  it.

### Minor: a compound approval was listed as an answer

- Scenario: the agent asks "Shall I push now?" and the human replies
  "yes, go ahead". The reply is not one of the exact `APPROVALS`
  phrases, so it was listed as `kind: answer`, against the docstring's
  "approvals … yield none".
- Standard: none
- Decision: fixed in faf4bf8. A reply made only of approval words
  (plus please, thanks, thank, you) is an approval. "Yes, but keep the
  old flag." is still an answer, and
  `test_compound_approvals_are_not_answers` pins both cases.

### Minor: `type: user` in a list item or flow mapping got past the conflicting-type skip

- Scenario: frontmatter with `type: feedback` at the top level plus
  `tags:\n  - type: user` or `metadata: {type: user}`. `TYPE_LINE` sees
  only the `feedback` line, so the entry was listed. That undercuts the
  architecture's fail-safe rule that any second `type` value means
  skip.
- Standard: none
- Decision: fixed in faf4bf8. `memory_type` returns None when any line
  of the block names `type: user` and the value it read is not `user`.
  `test_a_user_type_in_a_list_or_flow_map_is_skipped` covers it.

### Minor: `CORRECTION` matches replies that are not pushback

- Scenario: "No problem, carry on", "Never mind, it's fine" and
  "Actually, yes" each match the opening-words pattern and are listed
  as `kind: correction`.
- Standard: none
- Decision: deferred. A candidate is a lead that a human promotes,
  never a write. Measuring the kind's precision is PRD 13, a hand count
  over real interactive transcripts that is NOT RUN and assigned to the
  Owner, and tuning the pattern without that count would be guesswork.

### Minor: a human turn whose first item is a harness tag is skipped whole

- Scenario: a user record whose content opens with an injected item
  (for example IDE context in angle-bracket tags) followed by the typed
  correction. The joined text opens with `<`, so the whole turn is
  skipped and the correction is lost.
- Standard: none
- Decision: deferred. This is the architecture's documented rule ("text
  opening with `<`" is skipped outright). It fails toward a missed lead,
  never a leak. Revisit it with PRD 13's real-transcript count.

## Passes with no findings

- **Design:** clean. The code matches architecture.md's contracts. The
  one deviation (importing `protocol` for the fence) is recorded in
  ADR-0126. ADR-0078's edit touches only its Status line and points to
  the amending ADR-0125, so no superseding ADR was owed for a Decision
  edit. No unrecorded decision passes the protocol's ADR test.
- **Security:** clean beyond findings 1, 2 and 5. Transcript and memory
  text is treated as data, output is JSON, nothing is written, and no
  secret is in the code.
- **Complexity (lean cut-list):** nothing to cut. The diff adds no
  `lean:` marker. `harvest`'s `kb_dir=None` default exists for its
  pre-existing direct callers, the tests, so it is not a speculative
  option.
- **ADR compliance (adr_status.py, exit 0):** checked against ADR-0007,
  ADR-0027 and ADR-0076 (harness neutrality of the skill text), ADR-0014
  (licence: practices adapted, no Apache-2.0 text copied), ADR-0075
  (memory files go through `cli.read_file`), ADR-0078 as amended by
  ADR-0125, ADR-0118 and ADR-0126 (`kb_harvest` defines no fence and
  calls `protocol.frontmatter_end`), ADR-0091's dual-membership pin
  (updated), and ADR-0095 (`plugin.json` untouched). No violation. The
  other live ADRs are about subjects this diff does not reach (the
  tracker mirror, merge, evals, the cost ledger, the factory seams it
  does not touch) and are out of scope.
- **Standards (docs/standards.json):** `stdlib-only` holds. The other
  two filtered statements (typed IDs, one-way mirror) are not reached.
- **Domain passes:** none selected. No changed path matches the
  Payments, Migrations, Dependencies or Interface rows.

## Verdict

Ready to ship. No critical finding. The three majors and two of the
four minors are fixed test-first in e51413b and faf4bf8, and the full
battery is green afterwards: `run_tests.py` (4,147 tests, 0 problems),
`lint.py`, `kb.py drift`, `kb.py lint`, `gates.py` and
`gates.py --selftest` each exit 0. Two minors are deferred with reasons
above. Verify's two NOT RUN criteria, PRD 13 (human-turn precision on
real transcripts) and PRD 32 (the demo against the real memory
directory), are still not run. They are for the Owner, and this review
does not count them as passed.
