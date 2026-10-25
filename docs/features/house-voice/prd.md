---
stage: prd
run: feature:house-voice
date: 2026-10-25
id: PRD-0015
ux: not-applicable
ux-reason: "No UI; the skill shapes the agent's text replies only (autorun brief, User-facing surface)."
assumptions:
  - "Interview answered from autorun-brief.md and idea.md in this directory; no live interview held. Actors, stories, scope, exclusions and the no-spend constraint trace to the brief; the demo and success statement trace to idea.md."
  - "Typed id PRD-0015: the highest id declared in a docs/features/*/prd.md on this branch is PRD-0013, and the next number is already claimed by an unmerged run on another branch (checked 2026-10-25), so it is skipped to avoid a merge-time collision."
  - "idea.md's The demo is copied into a success criterion worded 'the demo runs as written', as the skill instructs. Its live half needs a model run, which the brief forbids this run, so it is split: the offline half is checked on fixture replies, the live half is the Owner-triggered paid run and Verify records it NOT RUN."
  - "'Measurably fewer output tokens' carries no threshold in the brief or idea.md. The criterion below takes the weakest honest reading (suite total lower with the skill than without, per-prompt counts reported); any stricter margin is Architect's to fix and record before the Owner's run."
  - "How clarity is judged (the Owner reading pairs, or a recorded rubric) is not settled by the brief; left to Architect as an open question rather than guessed. The criterion names the reader as the judge."
  - "Design questions are left to Architect: the activation companion (output style versus a CLAUDE.md line), the precedence order itself, the slop-pattern list, the offline token-count method, and the skill's name. The deliverable's kind (a utility skill in this plugin, ADR-0023) is the brief's decision, not re-decided here."
  - "No evidentiary question was left unanswered by the brief, so nothing was surfaced."
---

# PRD: A house voice for agent replies, set once instead of corrected every session

## Problem statement

Reading an agent's reply costs more than it should. Replies run long and
hedge, restate the question, carry AI tells ("Great question", em-dash
cascades, needless summaries), and spend output tokens on prose instead of
the answer. A plugin user has no way to set a house voice once, so they
correct it by hand, session by session; the Owner does exactly that today.
Four overlapping sources target the problem (ponytail, caveman, stop-slop,
Claude's built-in Concise style) and nothing blends them or says which wins
where they disagree. Evidence is one observer's sessions (the reason #1076
was filed) plus community skills said to have users, which this run
researches rather than assumes.

## Solution

1. **A dated research note** under `docs/research/` comparing each source's
   rules, token effect and conflicts, citing only what was fetched; a source
   that cannot be found is recorded as unidentified.
2. **One generic utility skill** in this plugin that blends the sources with
   a stated precedence where they conflict, and states how it yields to this
   plugin's own prose rules (ux-writing, stage-artifact conventions,
   one-question-at-a-time interviews). It is registered everywhere utility
   skills are listed.
3. **Whatever activation companion Architect justifies** (an output style or
   a CLAUDE.md line), so the voice holds on every turn instead of only when
   the skill's description matches.
4. **An offline-checked eval suite**: lint and routing-eval cases, and a
   plugin-evals suite of fixture prompts with a token-count grader and a
   slop-pattern grader. The live measurement waits on the Owner.

## Actors

- **Plugin user**: reads agent replies all day; wants a voice set once.
- **Owner**: the first such user; files the verdict after a week of use and
  triggers the paid measurement run.
- **Agent**: the Claude Code session whose replies the voice shapes.
- **House-voice skill**: the utility skill, directly invoked, owning no
  artifact.
- **Plugin stage skills**: this plugin's skills whose prose rules the voice
  must not override.
- **Reviewer**: judges at the merge gate that the skill is generic and the
  precedence is defensible.

## User stories

1. As a plugin user, I want to set a house voice once, so that I stop
   correcting replies by hand every session.
2. As a plugin user, I want replies that give the same answer in fewer
   output tokens and without the listed slop patterns, so that reading them
   costs less time and tokens.
3. As a plugin user, I want the voice to hold on every turn, not only the
   first, so that it does not silently stop working.
4. As a plugin user, I want a stated precedence where the sources conflict,
   so that the voice behaves the same way each time.
5. As a plugin user, I want the plugin's stage skills to keep their own
   prose rules under the voice, so that artifacts and interviews do not
   break.
6. As the Owner, I want a cited research note on the four sources, so that
   the blend rests on what they actually say.
7. As the Owner, I want the measurement suite authored and checked offline,
   so that I can run the paid measurement later with one command.
8. As a Reviewer, I want the skill free of any one person's personal voice,
   so that it ships safely to every plugin user.

## Success criteria

Offline criteria are checked this run by a test or a named command. The
three marked **Owner-run** need a live model or a week of use; Verify
records the live ones NOT RUN.

- [ ] **The demo runs as written.** Before: a plain question gets several
      paragraphs that restate it, hedge and close with a summary, and the
      user types "shorter, no summary" again. After: the same question gets
      the answer in a few lines, the token count beside it is smaller, the
      slop check lists nothing, and no correction was typed. *Offline half:*
      a test runs both graders on a fixture pair (a before reply and an
      after reply to one prompt) and asserts the after reply's count is
      lower and the slop grader lists nothing for it while listing at least
      one named pattern for the before reply. *Live half:* **Owner-run**.
- [ ] **Research note.** A dated file under `docs/research/` with one
      section per source (ponytail, caveman, stop-slop, Concise), each
      giving the source's rules, its token effect and its conflicts with the
      others, with a fetched URL and fetch date, or the word unidentified
      and no description. It states the precedence the skill uses, and a
      reviewer confirms each cited claim against its source.
- [ ] **Skill exists and is registered.** The skill lives under `skills/`,
      appears in `protocol.UTILITY_SKILLS`, the README, `LEDGER.md` (at the
      initial maturity, no graduation) and the plugin manifest's utility
      skill list; `python3 lint.py` prints `lint: 0 problem(s)`.
- [ ] **Precedence is stated.** The skill text states, for each conflict the
      research note names (fragments versus full sentences at least), which
      rule wins, and states that this plugin's own prose rules (ux-writing,
      stage-artifact conventions, one-question interviews) take precedence
      over or are exempt from the voice as Architect decides; a test asserts
      each named conflict has a stated winner.
- [ ] **Activation path is shipped and documented.** The companion Architect
      justifies ships with the skill, or the skill records why none is
      needed, citing the documentation it rests on.
- [ ] **Graders pass on fixtures.** The token-count grader returns the count
      a test recomputes independently for each fixture reply; the
      slop-pattern grader flags each listed pattern in a fixture built to
      carry it, by exact pattern name, and flags nothing in a clean fixture.
- [ ] **Suite validates offline.** The routing-eval cases and the
      plugin-evals suite pass their offline schema and lint checks; no case
      is run against a model.
- [ ] **Generic.** The skill and companion name no person, account or
      personal preference of the Owner's; a reviewer confirms.
- [ ] **No spend, no fabricated evidence.** No `claude plugin eval`, live
      `trigger_eval.py` or `charter_replay.py` run; `git diff` against main
      shows nothing added or changed under `evals/results/` or
      `plugin-evals/records/`, no LEDGER maturity change, and
      `.claude-plugin/plugin.json`'s version unchanged (ADR-0095).
- [ ] **Standard gates pass:** `python3 run_tests.py`, `python3 lint.py`
      (`lint: 0 problem(s)`), `python3 kb.py drift` (`drift: 0
      problem(s)`), `python3 gates.py && python3 gates.py --selftest`
      (`gates: 0 problem(s)`); any factory-template or mirrored-file edit is
      followed by `python3 factory_init.py update-manifest` in the same
      commit.
- [ ] **Owner-run: fewer tokens, no slop, as clear.** On the plugin-evals
      suite, run by the Owner, total output tokens with the skill active are
      lower than without (per-prompt counts reported), the slop grader lists
      nothing for any with-skill reply, and the reader judges each with-skill
      reply at least as clear as its pair. Verify records NOT RUN.
- [ ] **Owner-run: the voice holds past the first turn.** In one ordinary
      session the voice still applies after several replies. Verify records
      NOT RUN.
- [ ] **Owner-run, at Operate: week-of-use verdict.** Seven days after Ship
      is written back as released, `retro.md` records the Owner's verdict on
      a week of use, keep or drop, in the Owner's words.

## Out of scope

- Rewriting any other skill's prose to match the voice.
- Any paid model run, a cited record under `plugin-evals/records/`, and any
  LEDGER maturity change.
- The Owner's personal, non-generic voice.
- A voice that learns from each user's in-session corrections across
  sessions (the Moonshot rung, seeded separately).
- Merging, tagging or a plugin version bump (prepare and stop; ADR-0095).

## Open questions

- Output style, CLAUDE.md line, or both, as the activation companion; can a
  plugin ship an output style at all? For Architect (the idea's spike).
- The precedence order among the four sources, and how the voice yields to
  this plugin's own prose rules. For Architect, from the research note.
- The slop-pattern list and its exact names. For Architect.
- How output tokens are counted offline with the standard library only (a
  proxy count versus the live usage figure), and whether a margin beyond
  "lower" is required. For Architect.
- How "at least as clear" is judged at the Owner's run: the Owner reading
  pairs, or a recorded rubric. For Architect, confirmed by the Owner.
- The skill's name. For Architect.
- Whether a terse voice costs meaning on some prompts. Unproven; a known
  limit for Review and the Owner's run.
