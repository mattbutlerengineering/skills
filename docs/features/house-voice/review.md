---
stage: review
run: feature:house-voice
date: 2026-10-25
assumptions:
  - "Autorun stage, no live user: severity is the reviewer's call, and majors were fixed in-stage rather than deferred, as the eval-trends review did. Brief binding: no model run (no claude plugin eval, trigger_eval.py, charter_replay.py or claude -p), no plugin.json version change, nothing under evals/results/ or plugin-evals/records/, no LEDGER maturity move; none was made."
  - "Diff scope is the merge-base with origin/main (d178879) to 03c658b, the Verify commit, 13 commits and 94 files. origin/main has moved to 446fcc2; `git merge-tree --write-tree HEAD origin/main` prints one tree id and no conflict, before and after the review commits."
  - "Recommended default taken (source check): every source in the research note's table was refetched with curl on 2026-10-25, the GitHub raw files and the code.claude.com pages in their .md form, as untrusted data in the scratchpad. One page outside the table, code.claude.com/docs/en/plugins/components, was fetched because the manifest reference links it for output styles. The repo description behind caveman's 65% was read with gh api."
  - "Corrections to earlier artifacts are dated review notes appended to the research note, architecture.md and ADR-0119 (Consequences side, Decision untouched), not rewrites. The skill and the style were edited in place, because they are the deliverable and ADR-0119 already says the skill text is corrected before release if the style name differs."
  - "New tests were added and no existing test was edited. The opt-in sentence keeps the existing needle `/output-style house-voice` by naming the bare form as the one that may not resolve."
---

# Review: A house voice for agent replies, set once instead of corrected every session

## Scope

The whole run diff, read in full: `voice_grade.py`, `skills/house-voice/SKILL.md`,
`output-styles/house-voice.md`, the three new test modules, the
plugin-evals suite (3 prompts, 42 graders, 17 fixtures), the registration
edits (`protocol.py` and its payload twin, the manifest, `factory.py`, the
dual-membership pin, README, CONTEXT, LEDGER, routing cases, the skill
map, CLAUDE.md and AGENTS.md), ADR-0119, the research note, the eight
cost-ledger rows and every run artifact. Verification came first, so the
usual order holds.

Examined by: a refetch of all 17 cited sources and a claim-by-claim
comparison; probes of `voice_grade.slop` on 100 kB and 200 kB adversarial
inputs, cross-paragraph and hard-wrapped text, mismatched fences, quoted
text, a directory argument, a missing file and non-UTF-8 bytes; the CLI
and `factory.py voice-grade` exit codes; the binary-contrast pattern run
in node to confirm the JavaScript reading; the suite's shapes against the
plugin-evals docs' `prompt.md` and grader field tables and against
`plugin-evals/decompose/`; `adr_status.py` for the live ADRs; the gates
for the unmirrored WO rows and the zero-cost ledger rows.

Review commits on this branch:

- ab020c5 `fix(voice-grade): bound binary-contrast so a long reply grades in linear time`
- 3104407 `fix(house-voice): name the namespaced style and carry the exemptions into it`
- 7220c52 `docs(house-voice): dated review notes on the research claims and the architecture`

## Research-claim check (PRD criterion 2's reviewer half)

Confirmed as written: ponytail's one reply rule, its description's goal,
its benchmark (39 tasks, Opus 5.5, 5 runs, -45% tokens, output tokens 55%
of baseline, -53% code, -26% cost), "the rule was never fewest tokens",
its three hooks and "Active every session"; caveman's nine rules and
seven exceptions, the pre-send check, the four output-token figures
(6,983, 4,334, 4,119, 2,693), tiktoken o200k, about 1,160 input tokens,
JetBrains' 8.5% over 86 tasks, its four hooks and "auto-starts every
interactive session, subagents too"; stop-slop's eight rules, the 35/50
scoring, its structure names and its three activation routes; Concise's
first-sentence rule and both full-length cases; the skills page's single
message, 5,000 and 25,000 token figures; `force-for-plugin` overriding the
user's `outputStyle`; styles reaching forks and not other subagents;
"nothing enforces it"; the cache-preserving style switch; a plugin-root
`CLAUDE.md` not loaded; `${CLAUDE_PLUGIN_ROOT}` changing on update;
`outputStyles` replacing the default `output-styles/` scan; the memory
page's "only if it decides to open the file"; and the plugin-evals facts
(only the plugin loads, `last_message` default, `not_contains`, `costUsd`
and no token field, cases found by `prompt.md` or `case.yaml`).

Misquoted or misplaced, each corrected by a dated note in 7220c52:

- caveman's "about 5%" is the suite totals (4.96%). The README's own
  sentence is "cuts 3% more at the median". Its "3.1.0 rules, not yet
  re-run" covers all four figures, not `/ultracave` alone.
- caveman's 20-word cap is in the skill (rule 5), not only the README.
- "clarity beats brevity" is not caveman's wording ("Clarity beats
  compression", "Clarity wins").
- caveman's 65% is in the GitHub repository description, not a README line.
- stop-slop has no "filler" category: those two phrases sit under
  Adverbs. The note also omits two of its categories.
- "Not documented on the pages fetched" is wrong about style names. The
  manifest reference, which the run fetched, says Claude Code "namespaces
  every component" under the plugin name (the major finding below).
- `keep-coding-instructions` has no effect on the shorter system prompt,
  which the note omits.

The ADR-0119 activation claims hold, apart from the name. A plugin ships
`output-styles/` by default location with no manifest field.
`keep-coding-instructions: true` keeps the coding section, on the full
system prompt only. An invoked skill is re-attached after compaction
within the stated budget. A plugin-root `CLAUDE.md` is not loaded.

## Findings

### Major: the documented opt-in named a style that does not exist under that name

- Scenario: the user follows Make it stick and sets `"outputStyle":
  "house-voice"` in `~/.claude/settings.json`. The plugin components page
  says a plugin style appears "in `/output-style`, as `<plugin>:<name>`",
  so the style is `idea-to-prod:house-voice`. The output-styles page says
  a value that does not match a style name exactly "gives you the Default
  style". The voice never fires and nothing says so. This is the run's
  named riskiest failure, "it never fires", on its main cross-session
  path. The slash-command form had a fallback line ("type the name the
  menu shows"). The settings form had none.
- Standard: none
- Decision: fixed in 3104407, test first (RED, then green). The skill names
  `/output-style idea-to-prod:house-voice` and
  `"outputStyle": "idea-to-prod:house-voice"`, and says why a bare name may
  not resolve. ADR-0119 gains a dated review note and its Decision is
  unchanged. The Owner's hand session (criterion 12) still confirms the
  name the menu shows.

### Minor: the always-on style dropped the Exemptions

- Scenario: the style's body is the rules block alone. A user who selects
  the style and never invokes the skill gets the voice on every request
  with no hand-back. Nothing tells it that interview questions, problem
  strings or a skill's report template keep their own form, or that the
  user's request wins. ADR-0119's fourth Decision bullet ("persisted
  artifacts, interviews, interface strings and any output whose form a
  loaded skill or instruction file prescribes keep their own rules") then
  holds only when the skill is loaded. The ADR is provisional, which is
  one reason this is graded minor. The other is that the block's opening
  already limits the voice to conversational replies.
- Standard: none
- Decision: fixed in 3104407 (test first). The rules block now opens:
  files you write, questions you put to the user, and output whose form
  the user, an instruction file or a loaded skill sets keep their own
  rules. The style is still its byte copy (the pin passes). The skill
  stays slop-clean and well under the word limit.

### Minor: binary-contrast graded in quadratic time and matched across paragraphs

- Scenario: `\bnot just\b[^.]*\bbut\b` rescans the rest of the text from
  every "not just". `"not just " * 11000` (99 kB, no period) took 3.7 s and
  twice that took 14.7 s, so 1 MB would take minutes. Detector H's bug had
  the same quadratic shape. Separately, `"- Not just the index changes\n\n
  Run the tests\n\nThe commit is local, but it is safe"` was flagged, with
  the match spanning three paragraphs. Graded minor because the tool is
  on demand, offline and outside every gate.
- Standard: none
- Decision: fixed in ab020c5 (test first, two RED). The span is
  `(?:[^.\n]|\n(?![ \t]*\n)){0,120}`: at most 120 characters, stopped by a
  blank line, still crossing a single hard-wrap break, which an existing
  test pins. The three harness graders carry the same pattern, node
  confirms the JavaScript reading, and the 200 kB probe now returns at
  once.

### Minor: the research note misquoted or misplaced six source claims

- Scenario: PRD criterion 2 asks a reviewer to confirm each cited claim.
  The list is under Research-claim check above. None changes a decision,
  but the "about 5%" figure was carried into the skill's conflicts row.
- Standard: none
- Decision: fixed. 7220c52 adds dated notes to the research note and
  architecture.md. 3104407 makes the skill's row cite caveman's own 3% at
  the median.

### Minor: the slop graders pass on an empty or wrong reply and outweigh the clarity grader

- Scenario: twelve `not_contains` graders and one `llm` clarity grader are
  scored at the default weight of 1. A reply that is terse but wrong, or
  empty, passes 12 of 13 scored graders in either arm. The clarity grader
  catches it, but at one thirteenth of the score. The suite does not
  inflate Δ, because both arms see the same graders and the same brevity
  clause. But the score mostly measures the absence of tells, not the
  "same answer" half of the PRD.
- Standard: none
- Decision: deferred to the Owner, before the first paid run. Giving
  `carries-the-answer.md` a `weight` (for example 12) is a change to an
  eval definition that has never run. It does not edit a failing case,
  but its weight is a measurement choice the Owner should make.

### Minor: voice_grade grades quoted prose that the rules exempt

- Scenario: `payload-verbatim` exempts "quoted errors and quoted text", but
  `slop` masks only code. A reply quoting `"Full stop."` in double quotes
  is flagged. Run on the research note, the tool reports 17 hits, all of
  them quoted source phrases. The harness regexes cannot skip quotes
  either.
- Standard: none
- Decision: deferred. The fixtures carry no quoted slop, and masking
  double-quoted spans would also hide the agent's own scare-quoted
  prose. Recorded as a known divergence beside the stated code one.

### Minor: smaller voice_grade edges

- Scenario: a phrase hard-wrapped across a line ("let me be\nclear") is
  missed, because the patterns use literal spaces. This is Implement's
  known limit and stands. A ```` ``` ```` fence closed by `~~~` ends the
  mask early, so "In summary" inside the still-open block is flagged. A
  directory argument prints `cannot read <dir>: no such file`, which is
  the right exit code with a misleading reason.
- Standard: none
- Decision: deferred. All three are offline-tool edges with no gate
  behind them, and model replies are rarely hard-wrapped.

### Minor: "keeps Claude Code's coding instructions" holds on the full system prompt only

- Scenario: the output-styles page says the shorter system prompt has no
  coding section, so `keep-coding-instructions` has no effect there. The
  skill states the benefit without that condition.
- Standard: none
- Decision: deferred. The research note's review note records it. The
  sentence is true for the default full prompt, and the voice works
  either way.

### Minor: no routing near-miss for ux-writing's "voice and tone guide"

- Scenario: ux-writing's description lists "set up a voice and tone
  guide", and house-voice's says "set a voice for them". The one
  ux-writing near-miss is about error messages, so the closest pair of
  phrases has no case.
- Standard: none
- Decision: deferred. Adding a case is cheap, but it only means something
  with a live `trigger_eval.py` run, which the brief rules out.

## Passes with no findings

- **Correctness** of the counter, the masker, the problem strings and the
  exit codes: 0 when clean, 1 on slop, 2 on no argument, a missing file
  or non-UTF-8 input, all through `cli.read_file` and `cli.report`. The
  only findings are the ones above.
- **Security**: no network, no write, no subprocess, stdlib only (`re`,
  `sys` and the repo's `cli`). Input goes through the guarded read. No
  secrets.
- **Complexity** (lean cut-list): no confirmed cut. The one `lean:`
  marker names its ceiling (single-backtick spans) and its trigger (a
  fixture that needs more).
- **Generic** (PRD criterion 8's reviewer half): confirmed. The skill and
  the style name no person, account or personal preference. A grep for
  the Owner's names, employer, accounts and the word Owner finds nothing.
  `idea-to-prod` is the plugin's name.
- **The skill against this plugin's own rules**: the exemptions cover
  persisted artifacts, one-question interviews (stated in their own form)
  and ux-writing's interface strings. The precedence puts loaded skills
  and instruction files above the voice. The description is 664
  characters, under lint's 1024. It excludes ux-writing and lean, and its
  near-miss cases cover both. The skill and the style grade clean under
  their own `voice_grade`.
- **Suite shape**: `prompt.md` uses only documented keys (`description`,
  `tags`, `max_turns`, `allowed_tools`). Graders use documented types and
  fields, `skill-fired` matches decompose's precedent, and a top-level
  `fixtures/` directory with no `prompt.md` is ignored by the harness, as
  in `plugin-evals/decompose/`. Both arms share "Short answer, no
  filler.", as designed.
- **ADR compliance** (from `adr_status.py`): no violation of ADR-0008
  (the research note is cited in plain text, not linked); ADR-0012 and
  ADR-0019 (LEDGER `draft`, no graduation); ADR-0021 and ADR-0023 (a
  utility skill in `UTILITY_SKILLS`, owns no artifact); ADR-0026 and
  ADR-0032, partial (no WO issue was created, rows 0181-0188 are
  unmirrored, and the lean-in-the-build precedent and the gates agree);
  ADR-0050 (the payload twin of `protocol.py` and the manifest move
  together, detector E green); ADR-0051 and ADR-0075, provisional
  (`report`, `read_file`); ADR-0081, partial (the suite is tagged under
  `plugin-evals/`, with no records); ADR-0091, partial (the pin goes from
  56 to 57 pairs); ADR-0095 (`version` stays `0.22.1`, and only the
  description string changed); ADR-0114 (the offline scorer beside a
  harness suite); ADR-0119, provisional (held, with the review note
  above). The other ADRs do not reach this diff.
- **Ledger rows**: eight `owner-session:unmetered` zero-cost rows, one per
  checked WO row, the shape the lean-in-the-build and orchestrator runs
  used for detector G. Nothing was written under `evals/results/` or
  `plugin-evals/records/`. `git diff --name-only` over both is empty.
- **Domain passes**: none selected. No changed path matches the payments,
  migrations or dependencies table.
- **Standards**: `eval-honesty`, `stdlib-only` and `adr0032-one-way-mirror`
  (all advisory) apply and are met. No finding cites one.

## Battery (after the review commits)

    tests: 3892 tests across 121 modules in 27.6s on 8 workers, 0 problem(s)
    lint: 0 problem(s) across 35 skills
    drift: 0 problem(s)
    gates: 0 problem(s)
    selftest: ok

## Verdict

Ready for Ship. No critical finding was raised. The one major, the
un-namespaced style name, is fixed. Of the minors, three are fixed and
five are deferred with reasons. Three PRD criteria remain NOT RUN, all
Owner-run: the paid with/without measurement (11), the voice holding past
the first turn (12), and the week-of-use verdict (13). So the core claim,
that a live reply is shorter, clean and at least as clear, is still
unknown. So is whether the menu lists the style as
`idea-to-prod:house-voice`, which the docs say and no live session has
shown. This review is not a pass over any of those. The Owner should
settle the clarity grader's weight before the first paid run.
