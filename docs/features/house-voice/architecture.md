---
stage: architect
run: feature:house-voice
date: 2026-10-25
ux: skipped — No UI; the skill shapes the agent's text replies only (autorun brief, User-facing surface).
assumptions:
  - "No live interview. Every open question in prd.md was settled from autorun-brief.md, the fetched sources (docs/research/house-voice-sources-2026-10-25.md, all fetched 2026-10-25) and this clone, taking the recommended default each time. Nothing was left without a default, so nothing is surfaced."
  - "Activation (PRD open question 1), recommended default taken: the skill plus an output style the plugin ships at output-styles/house-voice.md and the user selects once. It is not forced and there is no hook and no CLAUDE.md line. Evidence, fetched: plugins ship output styles in output-styles/ (output-styles docs; manifest reference standard layout); force-for-plugin overrides the user's own outputStyle for every plugin user; a plugin-root CLAUDE.md is not loaded (manifest reference); an invoked skill stays in context for the session and is re-attached after compaction up to 5,000 tokens (skills docs). Recorded as ADR-0119 (provisional)."
  - "Skill name (PRD open question 6), recommended default taken: house-voice. It is generic, it is the run slug and the PRD's own term, and it does not take the name of the built-in Concise style. Rejected: concise (collides with the built-in style name), terse (names a register, and the voice also bans tells), reply-voice (fine, but a second term for one thing the run already calls the house voice)."
  - "Precedence (PRD open question 2), recommended default taken: the seven named conflicts and the general ladder in the research note's Conflicts section. The voice governs the agent's conversational replies only; persisted artifacts, interviews, interface strings, prescribed output forms and the user's own instructions win (Exemptions, below). The interview rule is this plugin's one-question-at-a-time form, and caveman already sends a question or options offered to the user to full sentences, so the two agree."
  - "Slop patterns (PRD open question 3), recommended default taken: the twelve named patterns in Data model, each a regex that runs in both Python's re and JavaScript, case-insensitive. Taken from stop-slop's lists, caveman's ceremony rules and Concise's narration and recap rule. Left out on purpose: stop-slop's 'really', 'just', 'simply' and 'actually' (too common in correct technical prose, such as 'just run make'), passive voice, and rhythm (no regex can judge either)."
  - "Token count (PRD open question 4), recommended default taken: a stdlib proxy, one unit per run of word characters and one per other non-space character (re.findall over \\w+|[^\\w\\s]). It is not Claude's tokenizer, which the standard library does not have. It counts long and rare words and code as fewer units than a real tokenizer does. It is valid only for comparing two replies to the same prompt in the same language, never as an absolute count or a bill. The Owner's live run reads the real count from the API's usage figure (see Interfaces)."
  - "Token margin (PRD open question 4), recommended default taken: no margin beyond 'lower'. The with-arm suite total must be lower than the without-arm total, with the per-prompt counts reported. Reason: with three runs on each of three cases there is no variance estimate to set a margin from, and both arms carry the same one-clause brevity request (below), against which caveman's own table claims only about 5%. The Owner's first run records the observed delta and spread. A margin is set from that and recorded as a new decision, not guessed now."
  - "Clarity (PRD open question 5), recommended default taken: a recorded rubric gates and the Owner confirms. Each harness case has one llm grader whose body lists the facts the answer must carry. It passes when every fact is stated and no sentence reads two ways, and it is scored in both arms. An offline test checks that the same facts appear in both the before and the after fixture, which is the 'same answer' half. At the Owner's run, the Owner reads each with/without pair blind and records at-least-as-clear or not, which is the PRD's 'confirmed by the Owner'."
  - "Harness facts used, fetched from the plugin-evals docs and not run: regex graders read last_message by default and take match: not_contains; tool_used Skill graders are with-only indicators in a two-arm run; a run loads only the plugin, so user settings, CLAUDE.md and output styles the user selected are absent; the documented result fields carry costUsd and no per-run token count; cases are found as <dir>/**/prompt.md or case.yaml. Fixture files therefore never use those two names."
  - "Both arms of every harness case carry the same one-clause request ('Short answer, no filler.') so the description has a turn to match. The delta then measures what the skill adds beyond a user simply asking, the same comparison caveman's README makes against 'Answer concisely.'. It is the stricter bar and the honest one: without the clause, the skill rarely fires on a plain question, and the comparison would measure nothing."
  - "Fixtures are authored, not recorded: the before replies are written to carry the patterns a long, hedged reply shows. They are labelled authored in the fixture directory, and no fixture is presented as real model output."
  - "ADR number 0119: the highest on this branch and main is 0118, and no remote branch, local branch or open PR carries a docs/adr/0119-* or higher (all refs checked with git ls-tree, 2026-10-25; open PRs: #1091 only, which adds no ADR)."
  - "No plugin.json version change (ADR-0095). The description string gains the slug, which check_plugin_skills requires, and that is the only plugin.json edit."
---

# Architecture: A house voice for agent replies, set once instead of corrected every session

## Approach

One utility skill, `house-voice`, holds a short rules block: the blend of
caveman's answer-first and payload rules, stop-slop's tells, Concise's
lead-in and recap cuts, and ponytail's closing disclosure. It also holds a
conflict table naming which source wins each of the seven conflicts the
research note found, and an exemptions list that hands persisted artifacts,
interviews, interface strings and prescribed output forms back to their own
rules. Once invoked, the skill holds for the rest of the session. To hold
across sessions, the plugin ships an output style whose body is a pinned
copy of the same rules block, and the user selects it once. It is never
forced (ADR-0119). Measurement is two scorers that share fixtures and
nothing else, the ADR-0114 shape. A root-only stdlib grader,
`voice_grade.py`, counts proxy tokens and lists slop patterns by name over
authored before and after replies, offline, in tests. A plugin-eval suite,
`plugin-evals/house-voice/`, carries the same patterns as `not_contains`
regex graders and a clarity rubric as an `llm` grader, for the Owner's paid
run.

The other shape compared was the community one: a plugin hook (ponytail and
caveman both use `SessionStart`) or `force-for-plugin: true`, so the voice
starts itself for everyone. It loses because this plugin ships to every
user. It would change every user's replies on install and override a style
they chose, and a hook needs a runtime the harness-neutral skill cannot
assume. A third shape, a CLAUDE.md line, cannot be shipped by a plugin, and
it reaches the rules only if Claude chooses to invoke the skill.

## Components

### house-voice skill

- Responsibility: the one owner of the voice. `skills/house-voice/SKILL.md`
  carries frontmatter (`name: house-voice`, a description that triggers on
  requests about the agent's own replies being long, hedged or padded, or
  on setting a voice for them, and that excludes interface strings and
  code) and four sections:
  - the rules block between `<!-- house-voice:rules:start -->` and
    `<!-- house-voice:rules:end -->`;
  - `## Conflicts`, a table with one row per conflict name from the
    research note, giving the winner and the reason;
  - `## Exemptions`;
  - `## Make it stick`, the one-time opt-in and what holds without it.

  It names no person, account or personal preference (PRD criterion
  Generic). It is one file and short. The docs re-attach at most 5,000 tokens of an
  invoked skill after compaction, so the whole file must stay well under
  that. Target: under 1,500 words. It cites the research note by path in
  plain text, never as a link, because lint's skill-asset check fails a
  link that leaves the skill directory (ADR-0008).
- Collaborators: the output style (a pinned copy of its rules block); the
  plugin's other skills (whose prose rules it defers to); `voice_grade.py`
  and the harness suite (which check the slop patterns its rules ban). The
  rules name the banned tells in prose; `voice_grade.py` owns the regexes.

### house-voice output style

- Responsibility: carry the rules block on every request once a user
  selects it. `output-styles/house-voice.md` at the plugin root, the
  default scan location, so `plugin.json` gains no `outputStyles` field.
  Frontmatter: `name: house-voice`, `description`,
  `keep-coding-instructions: true` (without it a custom style drops Claude
  Code's software-engineering instructions). It sets no `force-for-plugin`.
  The body is the skill's rules block, byte for byte.
- Collaborators: the skill (its owner); a pin test that compares the two.

### voice_grade.py

- Responsibility: the offline scorer. It owns `SLOP_PATTERNS` (name, regex,
  flags), `count_tokens(text)` and `slop(text)`. Root-only, stdlib, a leaf
  that imports `cli` for the guarded `read_file` and `report`. That adds the
  pair (`voice_grade`, `cli`) to `tests/test_dual_membership.py`'s pin,
  which goes from 56 to 57 pairs (ADR-0119). A `factory.py` `VERBS` row is
  `voice-grade`. It is outside `make check` and every workflow, like
  `decompose_grade.py`.
- Collaborators: the fixtures (its test inputs); the harness suite (whose
  regex graders are pinned copies of its patterns).

### Fixtures

- Responsibility: the authored replies both scorers and the demo rest on.
  Under `plugin-evals/house-voice/fixtures/`:
  - `<case>/before.md` and `<case>/after.md` for each of the three cases;
  - `slop/<pattern-name>.md`, one per pattern, each built to carry exactly
    that one pattern;
  - `slop/clean.md`, which carries none.

  `fixtures/README.md` says the files are authored, not recorded. No file
  is named `prompt.md` or `case.yaml`, because the harness would read it as
  a case. No file carries a typed-id-shaped token or a link, because
  detectors C and I scan every markdown file.
- Collaborators: `voice_grade.py` tests; the suite's clarity graders (whose
  fact lists the before and after fixtures must both carry).

### plugin-evals/house-voice suite

- Responsibility: the model-run side, authored and never run here. Three
  cases (`undo-unpushed-commit`, `read-a-traceback`, `pick-a-date-library`).
  Each holds:
  - `prompt.md`: frontmatter `description`, `tags: [house-voice]`,
    `max_turns`, `allowed_tools: [Skill]`; the body is the one-clause
    request followed by the question.
  - `graders/skill-fired.md`: `tool_used` Skill, matching
    `"skill"\s*:\s*"(?:[\w-]+:)?house-voice"`; a with-only indicator.
  - `graders/no-<pattern-name>.md`: one per slop pattern, `regex`,
    `match: not_contains`, target `last_message`, scored in both arms.
  - `graders/carries-the-answer.md`: an `llm` grader whose body has
    `PASS if` and `FAIL if` and a bullet list of must-carry facts.

  No `case.yaml` is needed, since there is no scaffold.
- Collaborators: `voice_grade.py` (the pattern owner); the fixtures (the
  fact check); `.claude-plugin/plugin.json`'s existing
  `experimental.evals: plugin-evals`.

### Registration

- Responsibility: list the skill everywhere the roster is checked:
  - `protocol.py` `UTILITY_SKILLS`, plus its payload twin
    `factory/templates/tools/factory/protocol.py`, then
    `python3 factory_init.py update-manifest` in the same commit;
  - the `.claude-plugin/plugin.json` description;
  - a row in README.md's `## Stages` utility table, Moment "Around every
    reply", and a mention in the borrowed-sources paragraph;
  - a labelled box in `docs/assets/skill-map.svg`;
  - `LEDGER.md` row `| house-voice | draft | — | — |`;
  - a `CONTEXT.md` entry for **House voice**;
  - at least 3 routing cases in `evals/routing.json`;
  - an on-demand bullet for `voice_grade.py` in both `CLAUDE.md` and
    `AGENTS.md`.
- Collaborators: `lint.py` (`check_plugin_skills`, `check_readme_skills`,
  `check_readme_no_orphans`, `check_readme_figure`, `check_ledger`,
  `check_skills`, `check_skill_assets`, `check_evals`); `kb.py drift`;
  `tests/test_factory_init.py`.

## Data model

**Rules block** (prose, in the skill and the style). Each rule opens with a
bold name, so tests can find it:

- **answer-first**: the first sentence states the answer or what happened;
  a simple question gets one to three sentences.
- **no-ceremony**: no greeting, no praise of the question, no restating it,
  no narrating what comes next, no recap, no sign-off, no offer of more
  help.
- **short-sentences**: one idea per sentence, about 20 words at most; full
  sentences with their articles; active voice; one term per concept.
- **plain-words**: common words and standard acronyms; no invented
  abbreviations, no arrows, no business jargon.
- **no-tells**: no em dashes, throat-clearing openers, emphasis crutches,
  filler adverbs, hedges or "not X, it's Y" setups in your own prose.
- **exact-meaning**: never drop a negation, limit, number or unit; keep a
  true "never" or "always"; make no unsupported sweeping claim.
- **payload-verbatim**: code, commands, paths, API names, quoted errors and
  quoted text stay exactly as they are.
- **real-counts**: list the items there are; never pad or trim to a count.
- **closing-disclosure**: end with one or two lines on what was skipped or
  not checked and any risk, only when there is one.
- **full-length-when**:
  - the user asks for detail;
  - error reports and failing test output;
  - security warnings;
  - confirmation of a destructive or irreversible action;
  - steps whose order matters;
  - a confused or repeated question.

**Conflicts** (table in the skill, same names as the research note):
`fragments-vs-full-sentences`, `closing-line`, `absolutes-vs-exact-limits`,
`rhythm-vs-one-idea-per-sentence`, `style-bans-vs-verbatim-payload`,
`brevity-vs-full-length`, `two-items-vs-real-count`. Each row has a winner
and a one-line reason.

**Exemptions** (the plugin's own prose rules win):

- `persisted-artifacts`: stage artifacts, ADRs, docs, commit messages, PR
  bodies, code comments. These follow their templates and skills.
- `interviews`: one question at a time, with a recommendation and its
  reasoning, in full sentences.
- `interface-strings`: product copy follows the project's voice and terms
  through `ux-writing`.
- `prescribed-forms`: output whose form a loaded skill or instruction file
  fixes, such as a report template, problem strings or a status line.
- `user-instructions`: the user's explicit request in the turn, and their
  own instruction files.

The general precedence ladder is the research note's, highest first.

**SLOP_PATTERNS** (owned by `voice_grade.py`; all case-insensitive, `m` added
where a pattern anchors on `^`):

| Name | Pattern |
|---|---|
| `praise-opener` | `\b(?:great\|good\|excellent\|fantastic) question\b` |
| `throat-clearing` | `\b(?:here['’]s the thing\|let me be clear\|the truth is\|it turns out\|let me walk you through)\b` |
| `restated-question` | `^(?:so,? )?you(?:['’]re\| are) asking\b\|^you want to know\b` |
| `hedge` | `\bit(?:['’]s\| is) (?:worth noting\|important to note)\b\|\bgenerally speaking\b` |
| `closing-recap` | `\b(?:in summary\|in conclusion\|to summari[sz]e\|to sum up)\b` |
| `closing-offer` | `\b(?:let me know if\|hope this helps\|feel free to\|happy to help)\b` |
| `em-dash` | `—` |
| `business-jargon` | `\b(?:deep dive\|circle back\|game[- ]changer\|lean into\|double down\|moving forward)\b` |
| `emphasis-crutch` | `\b(?:full stop\.\|let that sink in\|make no mistake)` |
| `filler-adverb` | `\b(?:literally\|genuinely\|honestly\|truly\|fundamentally\|inherently)\b` |
| `binary-contrast` | `\bnot just\b[^.]*\bbut\b\|\bisn['’]t (?:just )?[^.]{1,40}\. it['’]s\b` |
| `narration` | `\blet me (?:start\|begin\|take a look\|check\|explain)\b\|\bi['’]ll (?:now\|start by\|begin by)\b` |

(The `\|` is table escaping; each pattern's alternation is a plain `|`.)
`voice_grade.slop` skips fenced code blocks and inline code spans, which is
the payload-verbatim rule. A harness regex cannot skip them, so the harness
questions are chosen so the right answer quotes no code that would trip a
pattern. That divergence is known and stated.

**Proxy token count**: `len(re.findall(r"\w+|[^\w\s]", text))` over the
whole reply, code included.

Access patterns: the tests read every fixture once; the Owner reads replies
from a paid run. Nothing is written and no state is kept.

## Interfaces & contracts

### voice_grade.count_tokens(text) -> int

- Input: a `str`.
- Output: the proxy unit count, `0` for an empty string. Pure and
  deterministic.
- Failure modes: none for `str`. The CLI rejects bad input (below).

### voice_grade.slop(text) -> list[(name, matched_text)]

- Input: a `str`.
- Output: one tuple per match outside code, in pattern order and then text
  order; `[]` when clean.
- Failure modes: none for `str`.

### python3 voice_grade.py <reply.md> [<reply.md> ...]

- Input: one or more reply files.
- Output: one line per file, `voice-grade: <path>: <n> tokens`, then one
  problem string per match,
  `voice-grade: <path>: <pattern-name>: "<matched text>"`.
- Exit: `0` when every file is clean, `1` when any slop is found, `2` on bad
  input (no argument, an unreadable or non-UTF-8 file, through
  `cli.read_file`). No network, no model, no write.

### Pin: output style body equals the rules block

- Input: the text between the two markers in `SKILL.md`, and the style
  file's body after its frontmatter.
- Output: the test passes on byte equality. The failure message names the
  first differing line.

### Pin: harness regex graders equal SLOP_PATTERNS

- Input: every `graders/no-<name>.md` in every case.
- Output: the set of names equals the `SLOP_PATTERNS` names, and each
  grader's `pattern` and `flags` equal the module's. `match: not_contains`
  and target `last_message` (default or explicit) are asserted.

### Pin: conflicts have winners

- Input: the conflict names in the research note's Conflicts table, and the
  skill's `## Conflicts` table.
- Output: the two name sets are equal, and every row in the skill has a
  non-empty winner.

### Fixture assertions (PRD's demo, offline half)

- For each case:
  - `count_tokens(after) < count_tokens(before)`;
  - `slop(after) == []`, and `slop(before)` names at least one pattern;
  - every fact bullet in the case's `carries-the-answer.md` appears,
    case-insensitively, in both `before.md` and `after.md`.
- For each pattern, `slop(fixtures/slop/<name>.md)` names exactly that
  pattern; `slop(fixtures/slop/clean.md) == []`.
- An independent test recomputes the count with a character-scanning loop
  and compares it to `count_tokens`.

### The Owner's live run (documented, not run)

- `claude plugin eval . --tag house-voice --no-publish --max-cost-usd <cap>`
  reports skill-fired, the twelve slop graders and the clarity grader per
  arm, and Δ.
- The documented result fields carry no per-run token count. Output tokens
  are therefore read per question and per arm from `claude -p
  --output-format json`, from the `usage` object that output carries. The
  exact output-token field name is not on the pages fetched, so the Owner
  records the name read. The proxy is reported beside it as a cross-check.
- The Owner reads each pair blind for clarity.
- A hand session with the output style selected answers "holds past the
  first turn". Verify records all of this NOT RUN.

### Routing cases (evals/routing.json)

- `house-voice-1`, `direct`: "Set a house voice for your replies: answer
  first, no filler, no summary at the end."
- `house-voice-2`, `situational`: "Your replies keep restating my question
  and ending with a recap. Stop doing that for the rest of the session."
- `house-voice-3`, `situational`: "Every session I have to type 'shorter, no
  summary' again. Make it stick."
- `house-voice-vs-ux-writing-1`, `near-miss`, expected `ux-writing`:
  "Rewrite our app's error messages so they are shorter and plainer."
- `house-voice-vs-lean-1`, `near-miss`, expected `lean`: "This function is
  too long, make it shorter."

Offline schema checks only (`eval_schema.validate` through
`python3 lint.py`); `trigger_eval.py` is never run.

## Stack & dependencies

- Python 3 standard library only (`re`, `sys`, `pathlib`), plus the
  repo's own `cli.py`. This is the repo's hard convention.
- Claude Code output styles: the only platform feature added. It is
  Claude-Code-only, so oh-my-pi and Grok users get the skill alone.
- No new third-party dependency, no hook, no runtime.

## Decisions & alternatives

- **Skill plus an opt-in plugin output style** over skill alone, a forced
  style, hooks, or a CLAUDE.md line. Skill alone does not cross sessions.
  Forced or hooked changes every user's replies. A CLAUDE.md line cannot be
  shipped and is only a hint (ADR-0119).
- **The skill owns the rules and the style is a pinned copy** over a
  single shared file. A style cannot include or link another file, and a
  skill cannot link outside its directory (ADR-0008). A byte-equality test
  is how this repo holds two copies of one fact.
- **Full short sentences** over caveman's article-dropping register. Its
  own table claims about 5% over a plain concise request, and stop-slop
  and Concise both write sentences. Named conflict
  `fragments-vs-full-sentences`.
- **Exempt the plugin's own prose rules** over letting the voice rewrite
  artifacts. The brief rules out rewriting other skills' prose, and caveman
  already exempts persisted artifacts and questions to the user.
- **Two scorers: an offline module and harness graders** over harness
  graders only. The harness has no code grader and documents no token
  field, and an offline proxy makes the PRD's offline criteria checkable
  for free (ADR-0114's shape).
- **A word-and-punctuation proxy** over chars-divided-by-4 or a vendored
  tokenizer table. A vendored table breaks stdlib-only and goes stale.
  Chars/4 is a rule of thumb this run could not source, and the proxy's
  units are inspectable by hand. Neither is a real count, and the live run
  reads the API figure.
- **Twelve regex-checkable patterns** over the whole stop-slop catalogue.
  Patterns a regex cannot judge (passive voice, rhythm, quotables) would be
  noise. They stay as prose rules in the skill and are not graded.
- **No token margin beyond "lower"** over a guessed 10% or 15%. There is no
  variance data, and the baseline is already asked for brevity.
- **Rubric gate plus the Owner's blind read** for clarity, over the Owner
  alone (not repeatable) or the rubric alone (the PRD names the reader as
  the judge).

## Decompose: handle detector O

PRD-0015 is dated 2026-10-25, after `COVERAGE_ADOPTED` (2026-09-21), and
carries `id: PRD-0015`. So from the moment `breakdown.md` exists,
`gates.check_prd_coverage` fails every `##` section of `prd.md`, unless:

- a work-order row of this run's own `breakdown.md` cites the section, or
- the first non-blank line under the section's heading is a reasoned
  waiver.

A citing row has a `WO-####` id and names `PRD-0015`, with `§<Section
title>` citations, comma-separated, matched case-insensitively against the
whole title. A reasoned waiver is `<!-- coverage-waiver: <reason> -->`; a
bare marker waives nothing.

The PRD's sections are Problem statement, Solution, Actors, User stories,
Success criteria, Out of scope and Open questions. What Decompose should do,
as lean-in-the-build (PRD-0012) did:

- Give every row a `WO-####` id. Take the next free number after checking
  every branch and open PR for the highest in use. Detector C scans run
  artifacts for these tokens, so run `python3 gates.py` after writing.
- Have rows cite `(PRD-0015 §Solution, §Success criteria, §User stories,
  §Actors)` as they apply.
- In the same commit as `breakdown.md`, add a reasoned waiver directly under
  `## Problem statement`, `## Out of scope` and `## Open questions` in
  `prd.md`. For Open questions the reason is that this architecture answers
  them.
- Create no `WO-####` issue: the brief has no tracker mirror (ADR-0032 is
  one-way). The run's PR carries a `No work order:` line and
  `Closes #1076`.

## ADRs

- [ADR-0119](../../adr/0119-a-reply-voice-ships-as-a-utility-skill-with-an-opt-in-output-style.md):
  a reply voice ships as a utility skill with an opt-in output style, never
  forced; the style is a pinned copy; `voice_grade` joins the root-only
  importers of `cli.py` (provisional).

## Review note (2026-10-25)

Four statements above changed in the Review stage; the text above is left
as written.

- The Data model's `binary-contrast` pattern is now
  `\bnot just\b(?:[^.\n]|\n(?![ \t]*\n)){0,120}\bbut\b|...` (the second
  alternative unchanged). The open `[^.]*` graded a 200 kB reply without a
  period in 14.7 seconds and matched a "but" paragraphs away.
- The opt-in style name is `idea-to-prod:house-voice`, for
  `/output-style` and for the `outputStyle` setting (ADR-0119's review
  note).
- "caveman's own table claims about 5%" is a suite-total figure; caveman's
  README states 3% at the median (the research note's review note). The
  no-margin decision does not change.
- The style's body is still the rules block byte for byte, and the block
  now opens by handing files, questions to the user and prescribed forms
  back to their own rules, so the always-on path keeps the Exemptions.
