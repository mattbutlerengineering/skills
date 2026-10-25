---
stage: idea
run: feature:house-voice
date: 2026-10-25
origin: "GitHub issue #1076 (my voice / tone skill), filed by the Owner; the tracker seeds the run (ADR-0026) and the run's PR carries Closes #1076. Interview answered from autorun-brief.md in this directory; no live interview held. Not a backlog seed: no line in docs/backlog.md is claimed."
assumptions:
  - "In-flight check ran, nothing matches (the skill requires it only for a backlog seed; run anyway). `gh pr list --state open` returned one PR, #1091, a kb re-verify, unrelated. Branches checked by name (voice, tone, slop, style, concise, terse, caveman): fix/launch-demo-voice-parse-once is the launch-demo narration voice template, not reply style; codex-style-standards-enforcement is a shipped standards-index run. docs/backlog.md has no matching seed. Adjacent shipped skills, recorded rather than treated as a match: ux-writing (voice and tone for a product's interface strings, not the agent's own replies), lean (least code), polish (interface look and feel). No one has built this."
  - "Outside corroboration (the optional last30days check) was not run: the skill says never to run it unasked, no human was present to ask, and the brief's no-spend constraint applies. The interview alone is a complete result."
  - "Ambition ladder (feature-run version): the brief gave no rung pick, so the skill's recommended default, Showstopper, was taken and is logged here. The four tests were run silently and all pass (see Ambition rung)."
  - "The Moonshot was not chosen and should be seeded to docs/backlog.md; this stage commits only idea.md by instruction, so the seed text is carried in the Not taken line of the brief instead, as the skill allows when the file is not written."
  - "The demo prompts were not asked: the brief's success statement already names the demo moment (same answer, fewer tokens, no slop patterns)."
  - "Binding scope from the brief, not re-decided here: a generic utility skill in this plugin (ADR-0023), not the Owner's personal voice; no paid run of any kind; LEDGER maturity does not move; prepare-and-stop release; ux not-applicable."
  - "No evidentiary question was left unanswered by the brief, so nothing was surfaced. Evidence below is exactly the brief's two items, with its labels; nothing was researched at this stage."
---

# Idea: A house voice for agent replies, set once instead of corrected every session

## Problem

"I want to create a skill that allows ai to respond in my preferred voice/
tone/format." Reading an agent's reply costs more than it should. Replies
run long and hedge, restate the question, carry AI tells ("Great
question", em-dash cascades, needless summaries), and spend output tokens
on prose instead of the answer. A plugin user has no way to set a house
voice once, so they correct it session by session.

## Who has it

Plugin users who read agent replies all day, the Owner first among them.
The Owner mostly corrects replies by hand, in session, and rarely runs the
existing community skills that target this.

## Why now

Four overlapping sources exist (ponytail, caveman, stop-slop, and Claude's
built-in Concise style) and nothing blends them. Every long agentic run
pays for verbosity twice, in output tokens and in reading time.

## Evidence

- **Anecdote, one observer:** the Owner's own sessions, the reason #1076
  was filed.
- **Indirect:** community skills that target this problem exist and have
  users. To be researched by Architect, not assumed here.
- **None yet** that a blended skill changes token counts or clarity; that
  is what the success statement measures.

## Ambition rung

Chosen: Showstopper (skill default, brief silent), in the user's words: "I want to create a skill that allows ai to respond in my preferred voice/ tone/format."
Not taken: Solid: one utility skill that blends the four sources' rules with a stated precedence, active only when invoked. Moonshot (seed text, not written to docs/backlog.md by this stage): a voice that learns from each user's own in-session corrections and adapts itself across sessions, which needs memory and observed correction data this run does not have.
Demo: pass — the same prompt answered with and without the voice, side by side, the second visibly shorter with its output-token count beside it and a slop-pattern check reading zero.
Removes a step: pass — the per-session hand correction is gone: the voice is set once and holds on every turn.
Only this product: pass — the precedence is stated against this plugin's own prose rules (ux-writing, stage-artifact conventions, one-question interviews) and measured in its own plugin-evals harness, which no standalone voice skill sees.
Achievable: pass — the riskiest piece is activation on every turn; two-day spike: confirm from the docs whether a plugin can ship an output style or must lean on a CLAUDE.md line, and check by hand in one session that the voice holds past the first turn.

## The demo

Before: the agent answers a plain question in several paragraphs that
restate it, hedge, and close with a summary, and the user types "shorter,
no summary" again. After: the same question gets the answer in a few
lines, the token count beside it is smaller, the slop check lists nothing,
and no correction was typed.

## Riskiest piece + spike

Activation. A skill loads only when its description matches the turn, but
a voice must hold on every turn, which is what output styles are for. Spike
of about two days, with no paid run: establish from the Claude Code docs
whether a plugin can ship an output style, and if not what a one-line
CLAUDE.md companion does; then hold one ordinary session by hand and see
whether the voice survives past the first reply.

## Cheapest kill test

Take a few fixed prompts with replies already on hand, rewrite each reply
by hand under the blended rules, and count output tokens offline. If the
rewrite is not clearly shorter, or a reader finds it less clear, the blend
earns nothing and the run stops before building a skill.

## Solution hunch

A hunch, not a design. One utility skill that blends the four sources with
a stated precedence where they conflict, possibly paired with an output
style or a CLAUDE.md line so it actually fires. Architect researches the
sources and decides.

## Success in one sentence

With the skill active, a reply carries the same answer in measurably fewer
output tokens, with none of the listed slop patterns, and a reader judges
it at least as clear; and the Owner's verdict after a week of use is that
it stays.

## Unknowns & risks

- **It never fires.** A skill triggers on its description, a voice must
  hold on every turn. Without a companion (an output style or a CLAUDE.md
  line) it silently does nothing.
- **The sources conflict.** Fragments versus full sentences is one known
  clash; the blend needs a stated precedence, and a precedence nobody can
  defend is a matter of taste.
- **It clashes with house rules.** This plugin's own skills set prose
  rules (ux-writing, stage-artifact conventions, one-question-at-a-time
  interviews) that a global voice could fight.
- **Terse becomes unclear.** Fewer tokens can cost meaning; the clarity
  half of the success statement is the guard.
- **Sources may not be found.** Any source that cannot be fetched is
  recorded as unidentified, never described from memory.
- **No live measurement this run.** The no-spend constraint means the
  token and slop measurement is authored and checked offline, and the
  live number waits on the Owner.
