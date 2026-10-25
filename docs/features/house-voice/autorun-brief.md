# Autorun brief: feature:house-voice

Not an artifact. The brief autorun collects once, standing in for the
interviews the stages would otherwise run. Collected 2026-10-25, one
question at a time, from the Owner.

## Origin

GitHub issue #1076 ("my voice / tone skill"), filed by the Owner:

> I want to create a skill that allows ai to respond in my preferred
> voice/ tone/format. I want this to be a combination of ponytail,
> caveman, stopslop, Concise. Do research and make recommendations on
> how to improve output to be higher quality, use less tokens, and stop
> overly verbose output.

The tracker seeds the run (ADR-0026): #1076 enters the breakdown as the
run's issue reference, and the run's PR carries `Closes #1076`.

## Run scale and home

Feature, slug `house-voice`, artifacts at `docs/features/house-voice/`.
Starts at Idea. The deliverable is a **utility skill in this plugin**
(Owner decision; ADR-0023: directly invoked, owns no artifact, never
routed to), so it ships to every plugin user and must stay generic,
not the Owner's personal voice.

## Idea inputs

- **Problem, from the reader's side.** Reading an agent's reply costs
  more than it should: replies run long and hedge, restate the
  question, carry AI tells ("Great question", em-dash cascades,
  needless summaries), and spend tokens on prose instead of the answer.
  A plugin user has no way to set a house voice once, so they correct
  it session by session.
- **Who has it, and how they cope today.** Plugin users. The Owner
  mostly corrects replies by hand, in session (Owner's answer); they
  rarely run the existing skills.
- **Why now.** Four overlapping sources exist and nothing blends them,
  and every long agentic run pays for verbosity in tokens and reading
  time.
- **Evidence.** (1) The Owner's own sessions: anecdote, one observer,
  the reason #1076 was filed. (2) Community skills that target this
  problem exist and have users: indirect evidence, to be researched,
  not assumed.
- **Rough shape of a solution (a hunch).** One utility skill that
  blends the four sources with a stated precedence where they conflict.
- **Success statement.** Both of:
  1. With the skill active, a reply carries the same answer in
     measurably fewer output tokens, with none of the listed slop
     patterns, and a reader judges it at least as clear.
  2. The Owner's verdict after a week of use.
- **Biggest unknowns / ways this dies** (Owner's picks):
  - **It never fires.** A skill loads only when its description matches
    the turn; a voice must hold on every turn, which is what output
    styles are for. The design may need to pair the skill with an
    output style or a CLAUDE.md line, or it silently does nothing.
  - **The sources conflict** (fragments versus full sentences, for
    one), so a blend needs a stated precedence.
  - **It clashes with house rules.** This plugin's own skills
    (ux-writing, stage-artifact conventions, one-question-at-a-time
    interviews) set prose rules a global voice could fight.

## Sources to research

Real web research, written to a dated note under `docs/research/`
comparing each source's rules, token effect and conflicts:

- ponytail: https://github.com/dietrichgebert/ponytail
- caveman (a terse-output Claude skill)
- stop-slop (a skill that strips AI writing tells)
- Concise (Claude's built-in response style)

Cite only what is fetched. A source that cannot be found is recorded as
unidentified, never described from memory.

## Scope

**In.** The research note; one utility skill under `skills/`; its
registration (`protocol.UTILITY_SKILLS`, README, LEDGER, and the plugin
description where it lists utility skills); whatever activation
companion Architect justifies (an output style or a CLAUDE.md line);
lint and routing-eval cases; and a plugin-evals suite (fixture prompts,
a token-count grader, a slop-pattern grader), authored and checked
offline.

**Out.** Rewriting other skills' prose; any paid model run; the
Owner's personal, non-generic voice.

## Constraints

- **No spend.** No `claude plugin eval`, `trigger_eval.py` or
  `charter_replay.py` live run (Owner decision). Verify records the
  live measurement as NOT RUN; the Owner triggers it later. LEDGER
  maturity does not move without a real run.
- Stdlib only. Test first. Battery: `python3 run_tests.py`,
  `python3 lint.py`, `python3 kb.py drift`,
  `python3 gates.py && python3 gates.py --selftest`.
- Never fabricate evidence. `evals/results/` is append-only.

## User-facing surface

None: `ux: not-applicable` (no UI; the skill shapes text output).

## Release authorization

**None.** Prepare and stop: Ship pushes, opens the PR with
`Closes #1076`, records `outcome: prepared` with `pending-merge:`, and
stops. No merge, tag or plugin version bump (ADR-0095: the wave's
`chore(release)` PR carries it). ADRs written unattended land
`provisional`.

## Operate

operate:
  wait: 7 days after Ship is written back as released
  minimum-signal: the Owner's verdict on a week of use (success
  statement half 2)

`users-observed:` is counted from the signal Operate finds; this brief
never supplies it.
