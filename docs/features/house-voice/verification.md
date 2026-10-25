---
stage: verify
run: feature:house-voice
date: 2026-10-25
assumptions:
  - "No live interview: the autorun brief holds no Verify-specific answers, so the skill's defaults were taken. The criteria list is prd.md's thirteen success criteria plus the breakdown acceptance criteria no PRD criterion covers."
  - "Every piece of evidence was produced on HEAD a0cebdf in this session; nothing is carried over from the Implement stage's report or commit message."
  - "Recommended default taken (diff base): the change range is the three-dot form origin/main...HEAD. origin/main (446fcc2) has moved past the merge-base (d178879), so the no-spend checks were also run in the two-dot form against origin/main; both are quoted."
  - "Recommended default taken (independent recount): one before/after pair per case for two cases was recounted with a character-scanning loop written for this stage (no regex, not voice_grade's code), plus whitespace-split word counts and character counts as two cruder measures. The loop ran outside the repo and is not a repo command."
  - "Recommended default taken (source spot-check): three fetched source files (caveman README, ponytail README, stop-slop SKILL.md) were refetched with curl, raw, no model involved, treated as untrusted data, and the note's claims about them compared. The remaining cited claims are left to Review, as breakdown.md's Coverage section assigns."
  - "Recommended default taken (mutations): no mutation was re-applied this stage. Implement's breakdown Notes record five proved mutations; they are not re-proved here and are listed under Not verified."
  - "Criteria 11, 12 and 13 are recorded NOT RUN under the brief's no-spend rule and Operate's seven-day wait; nothing here invoked claude plugin eval, trigger_eval.py, charter_replay.py, claude -p or any model."
---

# Verification: A house voice for agent replies, set once instead of corrected every session

## Summary

3 NOT RUN (criteria 11, 12 and 13), 10 PASS, 0 FAIL, of PRD-0015's
thirteen success criteria, on HEAD a0cebdf. The three unknown criteria are
the Owner-run ones: the paid with/without measurement (11), the voice
holding past the first turn in a real session (12), and the week-of-use
verdict (13). They are unproven until the Owner runs architecture.md's
"The Owner's live run (documented, not run)" procedure and Operate records
the verdict. So the PRD's core claim, that a live reply is shorter, clean
and at least as clear, is UNKNOWN; what this stage proves is the offline
half: the graders, the authored fixtures, the pins and the gates. Two PASS
verdicts carry a reviewer half this stage cannot discharge: the research
note's per-claim source check (2; three sources spot-checked, the rest are
Review's) and the generic check (8; a mechanical grep, the reviewer's
confirmation is Review's). Whether Claude Code lists the plugin's output
style in its `/output-style` menu is unverified offline (criterion 5's live
half, folded into 12). Battery green: 3887 tests across 121 modules,
`lint: 0 problem(s)`, `drift: 0 problem(s)`, `gates: 0 problem(s)`,
selftest ok. The independent recount agrees with `voice_grade.count_tokens`
exactly and in direction.

## Criteria & evidence

### 1. The demo runs as written (offline half)

- Check: `python3 voice_grade.py` on each case's before and after fixture,
  and the fixture tests in `tests.test_voice_grade`. The live half is
  criterion 11's paid run and is disclosed there.
- Evidence:
  ```
  voice-grade: plugin-evals/house-voice/fixtures/undo-unpushed-commit/before.md: 222 tokens
  voice-grade: plugin-evals/house-voice/fixtures/undo-unpushed-commit/after.md: 69 tokens
  voice-grade: plugin-evals/house-voice/fixtures/undo-unpushed-commit/before.md: praise-opener: "Great question"
  voice-grade: plugin-evals/house-voice/fixtures/undo-unpushed-commit/before.md: throat-clearing: "let me walk you through"
  voice-grade: plugin-evals/house-voice/fixtures/undo-unpushed-commit/before.md: restated-question: "So, you're asking"
  voice-grade: plugin-evals/house-voice/fixtures/undo-unpushed-commit/before.md: hedge: "it's worth noting"
  voice-grade: plugin-evals/house-voice/fixtures/undo-unpushed-commit/before.md: closing-recap: "In summary"
  voice-grade: plugin-evals/house-voice/fixtures/undo-unpushed-commit/before.md: closing-offer: "Hope this helps"
  voice-grade: plugin-evals/house-voice/fixtures/undo-unpushed-commit/before.md: closing-offer: "let me know if"
  voice-grade: plugin-evals/house-voice/fixtures/undo-unpushed-commit/before.md: emphasis-crutch: "Make no mistake"
  voice-grade: plugin-evals/house-voice/fixtures/undo-unpushed-commit/before.md: filler-adverb: "Honestly"
  voice-grade: 9 problem(s)
  exit=1
  voice-grade: plugin-evals/house-voice/fixtures/read-a-traceback/before.md: 213 tokens
  voice-grade: plugin-evals/house-voice/fixtures/read-a-traceback/after.md: 74 tokens
  voice-grade: plugin-evals/house-voice/fixtures/read-a-traceback/before.md: praise-opener: "Good question"
  voice-grade: plugin-evals/house-voice/fixtures/read-a-traceback/before.md: restated-question: "You want to know"
  voice-grade: plugin-evals/house-voice/fixtures/read-a-traceback/before.md: closing-recap: "To sum up"
  voice-grade: plugin-evals/house-voice/fixtures/read-a-traceback/before.md: closing-offer: "Feel free to"
  voice-grade: plugin-evals/house-voice/fixtures/read-a-traceback/before.md: filler-adverb: "genuinely"
  voice-grade: plugin-evals/house-voice/fixtures/read-a-traceback/before.md: binary-contrast: "not just a typo problem but"
  voice-grade: plugin-evals/house-voice/fixtures/read-a-traceback/before.md: narration: "Let me explain"
  voice-grade: 7 problem(s)
  exit=1
  voice-grade: plugin-evals/house-voice/fixtures/pick-a-date-library/before.md: 183 tokens
  voice-grade: plugin-evals/house-voice/fixtures/pick-a-date-library/after.md: 62 tokens
  voice-grade: plugin-evals/house-voice/fixtures/pick-a-date-library/before.md: praise-opener: "Excellent question"
  voice-grade: plugin-evals/house-voice/fixtures/pick-a-date-library/before.md: throat-clearing: "Here's the thing"
  voice-grade: plugin-evals/house-voice/fixtures/pick-a-date-library/before.md: hedge: "it's important to note"
  voice-grade: plugin-evals/house-voice/fixtures/pick-a-date-library/before.md: hedge: "Generally speaking"
  voice-grade: plugin-evals/house-voice/fixtures/pick-a-date-library/before.md: closing-recap: "To summarize"
  voice-grade: plugin-evals/house-voice/fixtures/pick-a-date-library/before.md: closing-offer: "hope this helps"
  voice-grade: plugin-evals/house-voice/fixtures/pick-a-date-library/before.md: closing-offer: "happy to help"
  voice-grade: plugin-evals/house-voice/fixtures/pick-a-date-library/before.md: filler-adverb: "fundamentally"
  voice-grade: plugin-evals/house-voice/fixtures/pick-a-date-library/before.md: filler-adverb: "literally"
  voice-grade: 9 problem(s)
  exit=1

  test_each_after_reply_is_clean ... ok
  test_each_after_reply_is_shorter_than_its_before ... ok
  test_each_before_reply_names_a_pattern ... ok
  ```
  Each after reply is shorter (69 < 222, 74 < 213, 62 < 183), lists no
  match, and each before reply names at least one pattern (9, 7, 9).
  Independent recount, my own character-scanning loop (whitespace skipped,
  a run of alphanumerics or `_` is one unit, any other character is one
  unit), with whitespace-split words and characters beside it:
  ```
  plugin-evals/house-voice/fixtures/undo-unpushed-commit/before.md: scan=222 whitespace-words=181 chars=960
  plugin-evals/house-voice/fixtures/undo-unpushed-commit/after.md: scan=69 whitespace-words=50 chars=277
  plugin-evals/house-voice/fixtures/read-a-traceback/before.md: scan=213 whitespace-words=155 chars=849
  plugin-evals/house-voice/fixtures/read-a-traceback/after.md: scan=74 whitespace-words=42 chars=269
  ```
  The scan equals `count_tokens` on all four files, and all three measures
  point the same way (after below before).
- Result: PASS

### 2. Research note

- Check: section and URL structure of
  `docs/research/house-voice-sources-2026-10-25.md`; the conflicts table;
  a raw curl refetch of three source files and a comparison of the note's
  claims about them.
- Evidence:
  ```
  4:2026-10-25. Every source below was fetched on 2026-10-25 unless marked
  13:| ponytail README | https://github.com/dietrichgebert/ponytail |
  16:| caveman README | https://github.com/JuliusBrussee/caveman |
  19:| stop-slop README | https://github.com/hardikpandya/stop-slop |
  23:| Claude Code output styles (holds the built-in Concise style) | https://code.claude.com/docs/en/output-styles |
  30:**Unidentified:** the claude.ai chat app's preset "Concise" style. Both help
  ## ponytail :: **Reply rules.**
  ## ponytail :: **Token effect (claim).**
  ## caveman :: **Rules (skill).**
  ## caveman :: **Token effect (claim).**
  ## stop-slop :: **Rules (skill).**
  ## stop-slop :: **Token effect.**
  ## Concise (Claude Code's built-in output style) :: **Rules (docs).**
  ## Concise (Claude Code's built-in output style) :: **Token effect.**
  145:## Conflicts and the precedence the skill uses
  160:General precedence, highest first: the user's explicit instruction in the
  ```
  Refetch: curl's status line per file, then `grep -noE` of the claimed
  phrases in caveman's README, ponytail's README and stop-slop's SKILL.md,
  in that order:
  ```
  200 caveman-README.md
  200 ponytail-README.md
  200 stop-slop-SKILL.md
  98:8.5% fewer output tokens
  120:| None | 6,983
  121:| `Answer concisely.` | 4,334
  122:| `/caveman` | 4,119
  123:| `/ultracave` | **2,693**
  125:cuts 3% more at the median
  125:about 1,160 tokens of input
  42:-53% code &middot; -41% time &middot; -26% cost &middot; -45% tokens
  44:39 tasks including a real FastAPI + React repo, Opus 5.5, 5 runs each
  75:Output tokens: 57% and 55%
  19:No passive constructions.
  25:Mix sentence lengths. Two items beat three.
  25:No em dashes.
  ```
  Every compared number and rule matches. One nuance for Review: the note
  says caveman adds "about 5%" over the plain concise request; that is the
  suite total (4,119 against 4,334, 5.0%), while the README's own prose
  says "3% more at the median". The note's figure is right for totals and
  is labelled a claim. Each source section has rules and a token effect;
  each source's conflicts are stated in the shared Conflicts table (its
  Sources column names ponytail, caveman, stop-slop and Concise), not in a
  per-source subsection. The unfetchable claude.ai Concise preset is
  marked Unidentified and not described.
- Result: PASS (structure, URLs, dates, the unidentified rule and three of
  the sources' claims; the remaining per-claim check is Review's)

### 3. Skill exists and is registered

- Check: the skill file, each roster, and `python3 lint.py`.
- Evidence:
  ```
  skills/house-voice:
  SKILL.md
  True 23
  LEDGER.md:43:| house-voice | draft | — | — |
  README.md:132:| `house-voice` | Around every reply | Sets a voice for the agent's own replies: the answer firs
  CONTEXT.md:60:**House voice**:
  1
  factory-init, house-voice, implement-queue
  lint: 0 problem(s) across 35 skills
  ```
  `True 23` is `'house-voice' in protocol.UTILITY_SKILLS` and the set's
  size; `1` is the count of `>house-voice<` text nodes in
  `docs/assets/skill-map.svg`; the README line is cut at 100 columns; the
  last line is `grep -o` over the added plugin.json description line.
  LEDGER holds it at `draft`.
- Result: PASS

### 4. Precedence is stated

- Check: the SKILL.md Conflicts table against the research note's, and
  the tests that pin it.
- Evidence:
  ```
  69:| `fragments-vs-full-sentences` | Short full sentences, articles kept | caveman's own table puts its terse register about 5% under a plain request to be concise, and its own rule says clarity beats brevity |
  70:| `closing-line` | The closing line appears only when something was skipped, left unchecked or carries a risk; never a recap or an offer | A disclosure is information, and a recap repeats it |
  71:| `absolutes-vs-exact-limits` | A true limit stays exactly as stated; the ban covers unsupported sweeping claims | Dropping a real negation costs more than any word saved |
  72:| `rhythm-vs-one-idea-per-sentence` | One idea per sentence; the rhythm rule is not adopted for replies | Rhythm is an essay rule, and a reply is read for its answer |
  73:| `style-bans-vs-verbatim-payload` | Payload verbatim; the bans apply to your own prose only | A quoted error that holds an em dash is still the error |
  74:| `brevity-vs-full-length` | Full length for the union of both sources' lists | Both sources agree on the exception, and the union is the safe reading |
  75:| `two-items-vs-real-count` | List the real items; never pad or trim to reach a count | The count is content |
  77:## Exemptions
  test_the_names_equal_the_research_notes_and_each_has_a_winner ... ok
  test_each_exemption_is_named ... ok
  test_the_general_precedence_ladder_is_stated ... ok
  ```
  Seven conflicts, the same seven names as the note's table, each with a
  winner, `fragments-vs-full-sentences` among them; the Exemptions section
  carries the plugin's own prose rules and the ladder.
- Result: PASS

### 5. Activation path is shipped and documented

- Check: the output style file, its byte pin against the rules block
  (the test, plus my own byte comparison by `bytes.split`, not the test's
  helpers), the manifest, and the Make it stick section's citation.
- Evidence:
  ```
  ---
  name: house-voice
  description: Replies put the answer first, cut ceremony and the tells of generated prose, and keep every fact, command and quoted error exact.
  keep-coding-instructions: true
  ---
  block bytes 1938 c60f282687a422aa
  style body bytes 1938 c60f282687a422aa
  equal True
  0
  test_the_body_equals_the_rules_block_byte_for_byte ... ok
  test_a_one_line_edit_is_named_by_its_line ... ok
  test_the_plugin_manifest_names_no_output_styles_field ... ok
  test_the_one_time_opt_in_and_its_source ... ok
  test_it_says_what_holds_without_the_opt_in ... ok
  - run `/output-style house-voice` in Claude Code, or
  - set `"outputStyle": "house-voice"` in `~/.claude/settings.json` for
  removing the setting turns it off. ADR-0119 records why the opt-in is a
  ```
  `0` is the count of `outputStyles` in `.claude-plugin/plugin.json` (the
  style sits at the default `output-styles/` location). ADR-0119
  (provisional) cites the fetched output-styles, memory and manifest docs
  through the research note. A first attempt at the byte check with awk
  differed by one leading newline: awk dropped the start-marker line's own
  newline, which the rules block, read strictly between the markers,
  keeps. The `bytes.split` comparison above is the correct one.
- Result: PASS (shipped and documented; that Claude Code lists the style
  in its menu is a live check, folded into criterion 12)

### 6. Graders pass on fixtures

- Check: `python3 voice_grade.py` on each of the twelve slop fixtures and
  the clean fixture; the token-count and fixture tests.
- Evidence:
  ```
  voice-grade: plugin-evals/house-voice/fixtures/slop/binary-contrast.md: binary-contrast: "not just old but"
  voice-grade: plugin-evals/house-voice/fixtures/slop/business-jargon.md: business-jargon: "circle back"
  voice-grade: plugin-evals/house-voice/fixtures/slop/closing-offer.md: closing-offer: "Let me know if"
  voice-grade: plugin-evals/house-voice/fixtures/slop/closing-recap.md: closing-recap: "In summary"
  voice-grade: plugin-evals/house-voice/fixtures/slop/em-dash.md: em-dash: "—"
  voice-grade: plugin-evals/house-voice/fixtures/slop/emphasis-crutch.md: emphasis-crutch: "Make no mistake"
  voice-grade: plugin-evals/house-voice/fixtures/slop/filler-adverb.md: filler-adverb: "genuinely"
  voice-grade: plugin-evals/house-voice/fixtures/slop/hedge.md: hedge: "It is worth noting"
  voice-grade: plugin-evals/house-voice/fixtures/slop/narration.md: narration: "Let me explain"
  voice-grade: plugin-evals/house-voice/fixtures/slop/praise-opener.md: praise-opener: "Great question"
  voice-grade: plugin-evals/house-voice/fixtures/slop/restated-question.md: restated-question: "You are asking"
  voice-grade: plugin-evals/house-voice/fixtures/slop/throat-clearing.md: throat-clearing: "The truth is"
  voice-grade: plugin-evals/house-voice/fixtures/slop/clean.md: 21 tokens
  voice-grade: 0 problem(s)
  exit=0
  test_a_hand_counted_example ... ok
  test_an_independent_scan_agrees ... ok
  test_each_slop_file_names_exactly_its_own_pattern ... ok
  test_the_clean_file_is_clean ... ok
  test_the_twelve_names_in_order ... ok
  ```
  Each slop file names exactly its own pattern, by name, once; the clean
  file names none. The count half is also confirmed by criterion 1's
  independent recount.
- Result: PASS

### 7. Suite validates offline

- Check: the suite tests, the plugin-eval tag test, the routing cases
  read from `evals/routing.json`, and lint (which runs the routing-eval
  schema check). No case was run against a model.
- Evidence:
  ```
  house-voice-1 direct house-voice
  house-voice-2 situational house-voice
  house-voice-3 situational house-voice
  house-voice-vs-ux-writing-1 near-miss ux-writing
  house-voice-vs-lean-1 near-miss lean
  test_each_slop_grader_is_a_pinned_copy_of_its_pattern ... ok
  test_every_fact_is_in_both_the_before_and_the_after_reply ... ok
  test_skill_fired_matches_the_skill_tool_call ... ok
  test_the_clarity_grader_is_an_llm_rubric_with_facts ... ok
  test_the_grader_set_is_skill_fired_clarity_and_one_per_pattern ... ok
  test_every_case_is_tagged_house_voice ... ok
  test_no_case_yaml_anywhere_in_the_suite ... ok
  test_the_suite_holds_exactly_the_three_cases ... ok
  test_the_body_opens_with_the_brevity_clause_then_a_question ... ok
  test_the_frontmatter_carries_the_harness_keys ... ok
  test_every_case_is_tagged_with_its_skill_directory ... ok
  test_suite_has_cases ... ok
  Ran 31 tests in 0.019s
  OK
  lint: 0 problem(s) across 35 skills
  ```
- Result: PASS

### 8. Generic

- Check: a case-insensitive grep of the skill and the style for the
  Owner's names, handles, email, employer, town and pet, `@`, a GitHub
  URL and "my voice", plus the source names; then voice_grade over both.
- Evidence:
  ```
  skills/house-voice/SKILL.md:12:It blends four sources: caveman's answer-first and payload rules,
  skills/house-voice/SKILL.md:14:Concise output style, and ponytail's closing disclosure. Where they
  skills/house-voice/SKILL.md:54:  - steps whose order matters;
  skills/house-voice/SKILL.md:69:| `fragments-vs-full-sentences` | Short full sentences, articles kept | caveman's own table puts its terse register about 5% under a plain request to be concise, and its own rule says clarity beats brevity |
  output-styles/house-voice.md:39:  - steps whose order matters;
  ```
  The only hits are the public source names (searched on purpose) and
  `matt` inside "matters". No person, account, email or personal
  preference appears. A reviewer's confirmation is Review's.
- Result: PASS (mechanical check; the reviewer's confirmation is Review's)

### 9. No spend, no fabricated evidence

- Check: the protected trees, the plugin version, LEDGER and the cost
  ledger, diffed against origin/main.
- Evidence:
  ```
  --- three-dot
  --- two-dot
  --- version
    "version": "0.22.1",
    "version": "0.22.1",
  --- LEDGER
  --- a/LEDGER.md
  +++ b/LEDGER.md
  +| house-voice | draft | — | — |
  --- costs
  +{"wo": "WO-0181", "run_id": "session-2026-10-25-wo-0181", "model": "claude-opus-5-5", "tokens": 0, "cost": 0.0, "outcome": "owner-session:unmetered", "at": "2026-10-25"}
  +{"wo": "WO-0182", "run_id": "session-2026-10-25-wo-0182", "model": "claude-opus-5-5", "tokens": 0, "cost": 0.0, "outcome": "owner-session:unmetered", "at": "2026-10-25"}
  +{"wo": "WO-0183", "run_id": "session-2026-10-25-wo-0183", "model": "claude-opus-5-5", "tokens": 0, "cost": 0.0, "outcome": "owner-session:unmetered", "at": "2026-10-25"}
  +{"wo": "WO-0184", "run_id": "session-2026-10-25-wo-0184", "model": "claude-opus-5-5", "tokens": 0, "cost": 0.0, "outcome": "owner-session:unmetered", "at": "2026-10-25"}
  +{"wo": "WO-0185", "run_id": "session-2026-10-25-wo-0185", "model": "claude-opus-5-5", "tokens": 0, "cost": 0.0, "outcome": "owner-session:unmetered", "at": "2026-10-25"}
  +{"wo": "WO-0186", "run_id": "session-2026-10-25-wo-0186", "model": "claude-opus-5-5", "tokens": 0, "cost": 0.0, "outcome": "owner-session:unmetered", "at": "2026-10-25"}
  +{"wo": "WO-0187", "run_id": "session-2026-10-25-wo-0187", "model": "claude-opus-5-5", "tokens": 0, "cost": 0.0, "outcome": "owner-session:unmetered", "at": "2026-10-25"}
  +{"wo": "WO-0188", "run_id": "session-2026-10-25-wo-0188", "model": "claude-opus-5-5", "tokens": 0, "cost": 0.0, "outcome": "owner-session:unmetered", "at": "2026-10-25"}
  ```
  Both name-only diffs of `evals/results` and `plugin-evals/records` are
  empty. The plugin.json diff changes only the description line; the
  version is 0.22.1 on both sides. LEDGER adds one draft row and moves no
  maturity. The cost ledger adds eight zero-cost, zero-token
  `owner-session:unmetered` rows, one per checked row (detector G
  bookkeeping, not eval evidence).
- Result: PASS

### 10. Standard gates pass

- Check: the four-command battery on HEAD a0cebdf, then
  `python3 factory_init.py update-manifest` and `git status --porcelain`.
  The one mirrored-file edit (the `protocol.py` twin) and its manifest
  checksum landed in the same commit, 91faf0d.
- Evidence:
  ```
  tests: 3887 tests across 121 modules in 41.9s on 8 workers, 0 problem(s)
  exit=0
  lint: 0 problem(s) across 35 skills
  lint exit=0
  drift: 0 problem(s)
  drift exit=0
  gates: 0 problem(s)
  selftest: ok
  gates exit=0
  cmp exit=0
  factory-init: 0 problem(s)
  exit=0
  porcelain-end
   factory/manifest.json                       |   2 +-
   factory/templates/tools/factory/protocol.py |   2 +-
   protocol.py                                 |   2 +-
  ```
  `cmp exit=0` is `cmp protocol.py factory/templates/tools/factory/protocol.py`;
  nothing printed between the manifest regen and `porcelain-end`, so the
  manifest was already current. The targeted suites:
  ```
  python3 -m unittest tests.test_voice_grade tests.test_house_voice tests.test_house_voice_suite tests.test_dual_membership tests.test_factory_cli
  Ran 79 tests in 1.339s

  OK
  ```
- Result: PASS

### 11. Owner-run: fewer tokens, no slop, as clear

- Check: none. The paid with/without run is the Owner's, by
  architecture.md's "The Owner's live run (documented, not run)":
  `claude plugin eval . --tag house-voice --no-publish --max-cost-usd <cap>`
  for the graders, `claude -p --output-format json` per question and arm
  for the real output-token count, and a blind clarity read of each pair.
- Evidence: the brief forbids any paid model run this run. The offline
  proxy in criteria 1 and 6 says nothing about a live reply.
- Result: NOT RUN — no-spend rule (autorun brief, Constraints); the Owner
  triggers it

### 12. Owner-run: the voice holds past the first turn

- Check: none. A hand session with the output style selected, per the
  same architecture.md procedure. This also covers whether Claude Code
  discovers the plugin's style and shows it under `/output-style`.
- Evidence: needs a live session; none was held.
- Result: NOT RUN — needs a live model session, which the brief forbids
  this run

### 13. Owner-run, at Operate: week-of-use verdict

- Check: none. `retro.md` records the Owner's keep or drop verdict seven
  days after Ship is written back as released.
- Evidence: Ship has not run; the seven-day wait has not started.
- Result: NOT RUN — Operate's, by the brief's `operate:` block

### Breakdown acceptance criteria no PRD criterion covers

- Check: the `voice-grade` verb, the dual-membership pin, the root-only
  rule, the CLAUDE.md and AGENTS.md bullets, and the skill's word cap and
  self-grade.
- Evidence:
  ```
  71:    "voice-grade": ("voice_grade", "argv"),
  voice-grade: plugin-evals/house-voice/fixtures/slop/clean.md: 21 tokens
  voice-grade: 0 problem(s)
  exit=0
  tests/test_dual_membership.py:27:# protocol.py row; ADR-0119 added voice_grade to the cli.py row). The
  tests/test_dual_membership.py:36:        "size_band_calibration", "sweeps", "trigger_eval", "voice_grade",
  diff exit=0
  - `python3 voice_grade.py <reply.md> [<reply.md> ...]` — prints each
  voice-grade: skills/house-voice/SKILL.md: 1579 tokens
  voice-grade: output-styles/house-voice.md: 503 tokens
  voice-grade: 0 problem(s)
  exit=0
      1079 skills/house-voice/SKILL.md
  test_under_the_word_limit ... ok
  test_the_skill_follows_the_voice_it_defines ... ok
  ```
  `python3 factory.py voice-grade` is the same tool (the clean-file run
  above went through it). A grep for `voice_grade` in `factory_init.py`
  and the `Makefile` printed nothing, so it is outside `MIRRORS` and
  `make check`. The CLAUDE.md and AGENTS.md bullets diff equal
  (`diff exit=0`). SKILL.md is 1,079 words, under the 1,500 cap, and both
  it and the style carry 0 slop by voice_grade.
- Result: PASS

## Failures

none.

## Not verified

- Criteria 11, 12 and 13 (NOT RUN above): every live claim about a real
  reply, the voice persisting across turns, the style showing in the
  `/output-style` menu, and the Owner's verdict.
- The research note's cited claims beyond the three refetched sources
  (stop-slop's phrase and structure lists, the six Claude Code doc pages)
  were not refetched here; Review owns that check.
- No mutation was re-applied this stage. The five mutations in
  breakdown.md's Notes (filler-adverb's `honestly` and `truly`,
  restated-question's `m` flag, the style's "one to three", a fixture
  fact) are Implement's record, not re-proved.
- Known limit, carried from Implement's Notes: the slop patterns use
  literal spaces, so a phrase hard-wrapped across a line break is missed.
  Real replies are rarely hard-wrapped; the limit stands.
- The proxy count is not Claude's tokenizer; it is valid only for
  comparing two replies to the same prompt, as architecture.md states.
