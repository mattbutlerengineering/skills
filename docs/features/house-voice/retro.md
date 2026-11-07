---
stage: operate
run: feature:house-voice
date: 2026-11-07
users-observed: 0
signal-source: "Owner interview in session 2026-11-07 (usage not remembered), plus a repo scan: no house-voice record under plugin-evals/records/, no recorded live session with the style selected, and no feedback issue or PR naming the voice since the 2026-10-25 merge"
---

# Retro: A house voice for agent replies, set once instead of corrected every session

Shipped 2026-10-25 (PR 1094 merged 16:39Z; write-back PR 1097; the wave's
chore(release) PR 1099 bumped the plugin to 0.23.0 the same day, so
installed caches refreshed and the style has been reachable for 13 days —
past the brief's 7-day Operate wait). With `users-observed: 0`, nothing
below reads as landed, adopted or used: "what happened" records state.

## Outcomes vs. intent

### Fewer output tokens, no slop, at least as clear (PRD criterion 11)

- What happened: still unmeasured. The plugin-evals suite is authored,
  validated offline and one command away, and has never run: no
  house-voice record exists under `plugin-evals/records/` (the three
  2026-10-26 records are `idea` and `decompose` suites). The three
  before-first-paid-run decisions release.md step 6 parked (the clarity
  grader's weight, the quoted-prose divergence, the short-system-prompt
  caveat) are also unsettled, so the run is not yet one command away in
  practice. The LEDGER row stays `draft`.
- Signal strength: unobserved

### The voice holds past the first turn (PRD criterion 12)

- What happened: no session with the style selected is recorded anywhere;
  the menu name `idea-to-prod:house-voice` has still never been seen in a
  live `/output-style` menu (release.md's post-release smoke check for the
  Owner, not done).
- Signal strength: unobserved

### Week-of-use verdict, keep or drop (PRD criterion 13)

- What happened: the Owner's verdict, asked in session 2026-11-07, in
  their words: "Keep". Asked whether they had used the voice since
  release: "I don't remember." A keep verdict resting on no recalled use
  is a preference about the bet, not an outcome of use; the voice stays,
  and the measurement debt above is what would turn the verdict into
  evidence.
- Signal strength: anecdote

### Set once instead of corrected every session (idea.md's success sentence)

- What happened: state only — the skill, style and scorer shipped and are
  installable (plugin now at 0.27.0). Nothing observed anyone setting the
  style, and nothing in the repo records whether per-session hand
  correction stopped. The launch brief was never produced
  (`launch_demo.py config` said SHIP at release), so nothing ever
  announced the style; a zero-use first week may be discoverability, not
  rejection.
- Signal strength: unobserved

### The scorer found a second life (not a PRD criterion)

- What happened: `voice_grade.py`'s `SLOP_PATTERNS` is cited as the
  canonical reply-tell list by later factory work —
  `docs/research/desloppify-2026-10-31.md` names `voice_grade.py:26` as
  the reply-side analogue of the code cut-list it proposes, and a
  2026-10-31 backlog seed maps `lean`'s planned machine-tell table to it.
  The run's measurement tool is doing reference work its PRD never asked
  of it, while the voice it was built to measure goes unexercised.
- Signal strength: anecdote

## Open debt

Issues this run itself filed — Review deferrals, Verify carry-forwards —
are the run's debt, never feedback. This run filed no tracker issues for
its debt; it parked everything in `release.md`'s Owner steps, where all of
it still sits (itself a finding, see Environment):

- Review's deferred minors, from `review.md`: the clarity grader's weight
  (twelve `not_contains` graders at weight 1 outweigh
  `carries-the-answer.md`, so an empty or wrong reply passes 12 of 13);
  quoted prose graded though the rules exempt it; `keep-coding-instructions`
  inert on the short system prompt; the hard-wrap / mixed-fence /
  directory-argument edges in `voice_grade.py`; no routing near-miss case
  for ux-writing's "voice and tone guide".
- ADR-0119 still `provisional` — accept-or-amend was Owner step 1 and has
  not happened 13 days after release.
- The launch brief (Owner-on-demand, `/idea-to-prod:launch-demo` on
  PR 1094) was never produced.

## Run retrospective

- Keep: the offline/online split under the no-spend brief. Ten of
  thirteen criteria verified offline and shipped green, with the paid
  half authored down to one command and the live procedure documented in
  `architecture.md` rather than guessed. Also keep Review's
  refetch-every-cited-source pass: it caught a documented opt-in naming a
  style that did not exist under that name, and six misquoted source
  claims, before ship.
- Change: Owner-run work needs a carrier that resurfaces it. Three NOT
  RUN criteria and eight deferred items went into `release.md` prose that
  nothing re-reads; 13 days later zero have moved and no queue lists
  them. Ship should file a `type:chore` issue per deferred step
  (ADR-0083: `gh issue list` is the queue), so Operate finds a worked-or-
  not list instead of archaeology.
- Stop: deferring measurement choices (the clarity grader's weight) to a
  future paid run with no trigger. Decide at Review time or file the
  decision as an issue; "before the first paid run" is a time that never
  arrives on its own.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| Documented opt-in named a style that does not exist under that name (`"house-voice"` vs the real menu name) | `review.md` §Major | mechanical | `tests/test_house_voice.py`: pin every documented `outputStyle` string in the skill and style docs to the shipped style's real name |
| `binary-contrast` grader quadratic on pathological input (99 kB, no period → 3.7 s) | `review.md` §Minor binary-contrast | mechanical | `tests/test_voice_grade.py`: a size/time bound fixture over `SLOP_PATTERNS` |
| Research note misquoted or misplaced six source claims | `review.md` §Minor research note | judgement | the `review` skill's research-claim refetch pass — it is the thing that caught this; keep it mandatory for any run with a research note |
| Hedge phrase hard-wrapped across a line is missed (literal-space patterns) | `breakdown.md` §Notes WO-0182 | mechanical | whitespace-normalizing the patterns in `voice_grade.py`, pinned by a wrapped fixture in `tests/test_voice_grade.py` |
| Run debt parked as release.md prose that no queue sees; 0 of 8 items moved in 13 days | `release.md` §Release steps for the Owner, this retro §Open debt | mechanical | the `ship` skill files a `type:chore` issue per deferred Owner step; `gh issue list` is the queue (ADR-0083) |

## Idea seeds

- Run the deferred house-voice measurement (criteria 11 and 12) — settle the three before-first-paid-run decisions in release.md step 6, then the paid with/without suite and one hand session past the first turn; the core claim (same answer, fewer tokens, as clear) is unmeasured 13 days after release
- Ship-stage deferrals become tracker issues — house-voice parked 8 deferred items in release.md Owner steps and 0 moved in 13 days; Ship files a type:chore issue per deferred step so the queue, not an artifact, carries them (ADR-0083)
- A staleness pass for provisional ADRs — ADR-0119 is still provisional 13 days after its run released; a free offline check listing provisional ADRs whose run is complete would surface accept-or-amend debt the way kb.py drift surfaces dangling paths
- Announce before judging adoption — the house-voice launch brief was never produced, so zero observed use cannot distinguish rejection from discoverability; produce the brief (launch_demo on PR 1094) or an equivalent announcement before the next adoption read
- The Moonshot rung idea.md carried but never seeded: a voice that learns from each user's in-session corrections and adapts across sessions, which needs memory and observed correction data

## Run complete

Closed 2026-11-07. Verdict: Keep, on the Owner's word; the measurement
that would ground it is the first seed above. Seeds are appended to
`docs/backlog.md` as input to the next Idea-stage runs.
