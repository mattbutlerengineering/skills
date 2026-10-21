---
name: idea
description: Use when the user has a raw idea, a "what if", or a problem hunch with no artifacts yet — the start of a product or feature run. Interviews the user and produces an idea brief (idea.md).
---

# Idea

Turn a vague thought into a concrete idea brief. The knowledge is entirely in
the user's head at this stage, so this skill interviews — it does not draft.

## Process

1. Read `../../docs/pipeline-protocol.md` for run discovery, scale, and
   frontmatter conventions.

2. **Establish scale.** Is this a new product (product run, artifacts at
   `docs/`) or a feature of an existing one (feature run, artifacts at
   `docs/features/<slug>/`)? For a feature, agree on the slug now. When
   starting from a backlog seed, claim it in place — append
   `(claimed: <run-ref>)` to the seed's line in `docs/backlog.md` per the
   protocol's seed-backlog section — and record the seed as the origin in
   `idea.md`.

3. **Check what is already in flight.** Whenever this run starts from a
   backlog seed — and before `idea.md` exists — look over the work already
   awaiting review and ask whether one of them does this: the protocol's
   *Work already in flight* section. Run discovery sees the working tree,
   and a run someone else has already built sits on a branch where no
   directory listing reaches it. Say which of the three outcomes happened;
   a check that could not run is reported as that, never as a clean one. A
   greenfield product run with no review surface to read satisfies this by
   saying so.

4. **Interview.** One question at a time, each with your recommended answer
   when you have one. Keep going until every section of the template can be
   filled with something concrete. Cover at least:
   - What is the problem, stated from the sufferer's perspective?
   - Who exactly has it? How do they cope today?
   - Why now — what changed to make this worth doing?
   - What evidence exists that the problem is real (even anecdote counts —
     label it as such)?
   - **Ambition ladder.** How big should this be? Offer three rungs,
     Showstopper (recommended), and let the user pick — see the block
     below.
   - What's the rough shape of a solution? (A hunch, not a design.)
   - What would make you call this a success in one sentence?
   - What are the biggest unknowns or ways this dies?

   Challenge weak answers. "Everyone" is not a who; "it would be cool" is not
   a why-now. For a feature run, scale down — a few sharp questions, not a
   product inquisition.

   **Optional — corroborate the two evidence questions.** Where the
   `last30days` skill is installed, "why now" and "what evidence exists"
   can be checked against what people outside this conversation said in the
   last 30 days. Offer it; never run it unasked — it is network-bound and
   costs credits, and a research detour the user did not ask for is a worse
   interview, not a better one. What comes back is anecdote at community
   scale, so it enters `idea.md` labelled as anecdote like any other, never
   as validation. It may corroborate the problem, sharpen the who, or
   contradict the why-now — the contradiction is the most valuable of the
   three, and it is recorded as an unknown, not used to argue the idea out
   of existence. Where the skill is not installed, the interview alone is a
   complete result.

   **The ambition ladder.** After the problem and evidence answers, and
   before the solution hunch, offer three rungs anchored on the user's own
   words: quote their opening sentence and build each rung from it, never
   renaming their idea.

   - **Solid** — fixes the problem and ships fast. The fallback.
   - **Showstopper** — the same problem plus one moment that makes a viewer
     say "wait, do that again". Showstopper (recommended).
   - **Moonshot** — not achievable at this run's scale.

   The pick is the user's, and it is recorded in idea.md. The Moonshot is
   never chosen in this run and is always saved as a seed; if the user picks
   it, say so and ask for the Showstopper or Solid pick. If the user
   declines the ladder, record Solid as chosen and note that they declined.

   Apply four tests to the Showstopper so "wow" is not left to taste. Each
   is answered in writing, pass or fail with one clause of evidence:

   1. A 30-second demo exists: the before and the after fit in two
      sentences, and the after is something you see, not a metric.
   2. It removes a step instead of speeding one up: zero clicks, zero setup,
      or it is done before you ask.
   3. It is built on something only this product has: its data, its place
      in the workflow, or context a competitor cannot see.
   4. It is achievable: it fits this run's scale, and its riskiest technical
      piece is named with a spike of about two days that could prove it.

   When a test fails, say which one and re-scope it once. If it still
   fails, or no spike could prove it, record it as the Moonshot and make
   Solid the pick.

   Save the larger rungs you did not take as backlog seeds: seed every
   unchosen rung larger than the pick. Solid is never seeded and the
   Moonshot always is. Append one line each to `docs/backlog.md` in the form
   `- <seed text> (from: <run-ref>)`, with the run-ref being feature: plus
   the slug on a feature run and product on a product run. The seed text is
   one line with no parentheses and no typed ids. The file is append only:
   add below the last line and never rewrite an existing one, and create the
   file with its header line when it is absent. Stage the append by path in
   the same commit as idea.md. Write well-formed lines only: a seed that
   would fail the grammar is not written. If the file cannot be written, say
   so and put the seeds in the Not taken line of the brief instead.

   Prompts for the demo and the tests, one at a time:
   - What would you show first in a demo?
   - What does the user do today that they would never have to do again?
   - What does the product already know that it is not using?

   For a feature run, ask the ladder as one question: three one-line rungs
   built from the user's own sentence, Showstopper recommended, pick or
   correct. Ask the prompts only when their framing names no demo moment, at
   most two. Run the four tests silently and surface only a failure; keep
   the spike to one sentence. A product run asks all three prompts in full,
   one at a time.

5. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `idea.md`, with protocol frontmatter.

6. **Hand off.** State that the next stage is PRD and how to get there
   (the `prd` skill, or the router). Commit the artifact on the run's branch
   — the protocol's "Commit at the stage boundary" section owns the rule
   and the commit subject.

## Rules

- Capture the user's words, sharpened — don't replace their idea with yours.
  The ladder offers a bigger version anchored on their words; it never swaps
  their idea for yours.
- Outside evidence corroborates or challenges; it never re-authors. And a
  community that has not discussed the problem is not evidence the problem
  is unreal — most real problems are undiscussed, so silence goes in as
  silence, never as a finding.
- Record uncertainty honestly: an unknown listed is worth more than a guess
  dressed as a fact.
- No solution design here. If the user starts designing, note the hunch and
  steer back to problem and evidence.
