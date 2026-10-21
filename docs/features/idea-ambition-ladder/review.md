---
stage: review
run: feature:idea-ambition-ladder
date: 2026-10-20
assumptions:
  - "Autorun stage, no live user: severity is the reviewer's call. Brief binding: demo reaches launch-demo via the PRD; no paid run, no `claude plugin eval`, no model call; no LEDGER or plugin.json edit; skills/ limited to skills/idea and skills/prd. None was broken."
  - "Diff scope is `git diff origin/main...HEAD` at 609634d (the Verify commit). Anything that would change a recorded Owner decision, the issue's four tests, three prompts and three rungs, or the PRD's fixed strings is deferred, not fixed."
---

# Review: An ambition ladder for the Idea stage

## Scope

skills/idea/SKILL.md (read top to bottom as an agent would) and TEMPLATE.md,
skills/prd/SKILL.md, the docs/pipeline-protocol.md Producers sentence, both
test modules, and plugin-evals/idea/ladder-brief (case.yaml, prompt, scaffold,
all 11 graders), against the PRD, architecture.md, breakdown.md and
verification.md. Verification came first, so the usual order holds.

Examined by: a full read of the skill text for order, contradiction and
overreach; a 24-mutant sweep applied in `git archive` copies (each `old`
string asserted to occur once, bytecode off), run before and after the test
additions below; the five whole-repo checks; `python3 one_owner.py` (9
problems, same baseline, none naming this branch's files). Domain passes: none
selected (no payments, migrations or dependency paths). No
`docs/standards.json` statement matched a finding.

Review commits on this branch:

- c888ca8 `fix(idea-ambition-ladder): ask the three prompts before the four tests they feed`
- 87d1f3a `fix(idea-ambition-ladder): a demotion is told to the user, and a seed never glues onto an unterminated last line`
- eaa784b `test(idea-ambition-ladder): match the capitalised demotion sentence` (87d1f3a carried a wrong-case test phrase; a follow-up commit rather than a history rewrite)
- f40745f `test(idea-ambition-ladder): pin the append, scale-down and scaffold-confinement branches review mutants survived`

## Findings

### Major: the demotion made Solid the pick without telling the user, against "the pick is the user's"

- Scenario: user picks Showstopper; test 4 fails twice. The text said "record it
  as the Moonshot and make Solid the pick" and nothing else. An agent complies
  silently, the user's chosen rung is replaced without a word, and the text is
  also silent on whether the demoted rung is seeded next to the original
  Moonshot (two "Moonshots").
- Standard: none
- Decision: fixed in 87d1f3a. Added "Tell the user which test failed and that
  Solid is now the pick; the demoted Showstopper is seeded as well as the
  Moonshot." The existing pinned phrase is untouched. It cannot loop (re-scope
  once) and the user's framing is not discarded (it is seeded).

### Major: an append to a backlog whose last line has no newline would corrupt that line

- Scenario: `docs/backlog.md` ends `- An older idea (from: session:2026-07-05)`
  with no trailing newline. "Add below the last line" executed as `>>` glues
  the new seed onto the existing line, rewriting it into a line that breaks
  the grammar or the existing seed, against "never rewrite an existing one".
- Standard: none
- Decision: fixed in 87d1f3a ("start each seed on a new line of its own (add
  the missing newline first when the last line lacks one)"), pinned.

### Minor: the prompts that feed the tests came after the tests and the seeding rule

- Scenario: the block read rungs, tests, seeding, then "Prompts for the demo
  and the tests". An agent reading top to bottom judged the demo before
  asking for it.
- Standard: none
- Decision: fixed in c888ca8 (paragraph moved before the tests; an order test
  pins it).

### Minor: ten load-bearing branches had no pin (mutants survived)

- Scenario: the first sweep left these alive: `add below the last line` to
  `add above the first line`; `Stage the append by path` to `git add -A`;
  "if the user picks it, say so and ask" to "build it"; "at most two" to six;
  "silently" to "aloud"; the declined-ladder rule; the Solid fallback; the
  zero-click wording; the "before the solution hunch" clause; the PRD
  "checkable body" clause; the protocol's "never rewrite existing lines"; the
  template's `none — Solid chosen`; and in the suite, the scaffold gaining
  `cd /` (nothing pinned it to its directory), `keeps-users-words` shrunk to
  the single word `rota` (the pattern still matched the scaffold), the
  moonshot rubric's FAIL clause and the prompt's "Do not design the solution".
- Standard: none
- Decision: fixed in f40745f (tests only; each pin was seen to kill its
  mutant in the re-sweep). One survivor remains by nature, below.

### Minor: phrase pins cannot catch contradictory prose

- Scenario: the mutant adding "and may rewrite lines" to the protocol's
  Producers sentence survives, because the original "never rewrite" phrase is
  still present. The same holds for any text appended beside a pinned phrase
  in the skill: the tests prove the sentences exist, not that the whole reads
  coherently. Order and contradiction were checked here by reading, not by a
  test.
- Standard: none
- Decision: deferred — a test cannot judge prose; the read is the control. The
  honest limit is stated here and in the Verdict.

### Minor: the Showstopper default carries a ceremony risk the idea names

- Scenario: "Showstopper (recommended)" is unconditional, so a tiny feature
  gets the same push toward a bigger rung as a headline one, and the template
  gains four sections plus four test lines for every feature brief. The
  scale-down (one question, prompts only when no demo moment is named and at
  most two, tests run silently) keeps the interview light, but the brief
  itself grows. No guidance says when Solid is the right recommendation.
- Standard: none
- Decision: deferred to the Owner — "Showstopper (recommended)" is a fixed
  string of the issue and the PRD. Reason to revisit after a paid run:
  whether users inflate scope cannot be judged without one.

### Minor: a Solid pick leaves the four test lines, the spike section and a seeded declined ladder unspecified

- Scenario: when Solid is chosen, "Demo: pass | fail" and "Achievable" have no
  meaning for the unchosen Showstopper; the template only gives the demo a
  `none — Solid chosen` form. A user who declines the ladder still gets the
  Showstopper and Moonshot seeded ("every unchosen rung larger than the
  pick"). Re-running Idea on the same run would append duplicate seeds. The
  seed header line is described as "its header line" without text, so an
  agent invents one (harmless: non-bullet lines are ignored by the grammar).
- Standard: none
- Decision: deferred — none corrupts a file or breaks a checker; changing the
  Solid-path template shape alters the PRD's fixed sections. Candidate for the
  paid run's observations.

### Minor: "riskiest technical piece" sits beside "No solution design here"

- Scenario: test 4 asks the agent to name the riskiest technical piece. The
  rules line "No solution design here" is kept and the ladder block says
  rungs are anchored on the user's words, so naming a risk is a hunch, not a
  design; a model could still drift into designing the spike.
- Standard: none
- Decision: deferred — the four tests are the issue's text; the added Rules
  sentence covers the rung but not the spike. Not worth a new rule without
  evidence of drift.

## Checked with no finding

- (a) Numbering and step order: the ladder bullet sits after evidence and
  before the hunch, the block follows the corroborate paragraph, and Write is
  step 5; "don't replace their idea with yours" survives and the new Rules
  sentence is consistent. A Moonshot pick is refused and re-asked.
- (b) Append safety: only unchosen larger rungs; the grammar is stated; seed
  text is one line, no parentheses, no typed ids (so it cannot forge
  `(from:` or `(claimed:` markers); an absent file is created; a refused write
  falls back to the Not taken line; product and feature run-refs are
  distinguished. User-supplied text is the pre-existing consumer risk of any
  seed (`next` reads seeds), unchanged here.
- (e) The PRD clause does not conflict with the PRD steps; verify's step 4
  ("do the manual check when that's what the criterion needs") covers "the
  demo runs as written" without a verify edit.
- (f) An unfilled `<...>` in a written brief is flagged by no checker; nothing
  parses idea.md sections (the old-brief pin measures this).
- (g) No grader file addresses the model under test. The three llm rubrics do
  not appear in the prompt, so they do not leak. The scaffold uses only
  relative paths in its own temp dir and no network (now pinned). The prompt
  supplies the user's pick and answers, so the case measures whether the brief
  is written to the template, not whether the model would recommend
  Showstopper. Whether the harness reads the grader directory, or any
  fixtures-like extra directory, is unknown until a paid run; noted, not fixed.
- (i) `kb.py drift`, gates (no typed id or link in the skill text, the sample
  seed grammar) and one_owner are clean.
- (j) The Producers sentence is accurate: Idea does append unchosen rungs, and
  the rest of the sentence is unchanged.
- (k) The long single-line Producers sentence is cosmetic: lint, drift and
  gates accept it.

## Verdict

Ready to ship after the two major fixes, which are in. Final lines after the
last change: `tests: 3679 tests across 113 modules in 26.0s on 8 workers, 0
problem(s)`; `lint: 0 problem(s) across 34 skills`; `drift: 0 problem(s)`;
`gates: 0 problem(s)`; `selftest: ok`.

Not run or unknown, and not to be read as passed: the whole ladder has never
been run against a model (by decision), so whether it improves briefs, whether
the four tests discriminate, whether the demotion rule over-demotes, the
Showstopper default's ceremony effect, the three llm graders' judgement and
the harness's handling of the grader directory are all unknown. Prose
coherence is checked by reading only; phrase pins cannot catch contradictory
text. Four deferred minors above await the Owner.
