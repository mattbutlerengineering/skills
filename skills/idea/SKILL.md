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

5. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `idea.md`, with protocol frontmatter.

6. **Hand off.** State that the next stage is PRD and how to get there
   (the `prd` skill, or the router).

## Rules

- Capture the user's words, sharpened — don't replace their idea with yours.
- Outside evidence corroborates or challenges; it never re-authors. And a
  community that has not discussed the problem is not evidence the problem
  is unreal — most real problems are undiscussed, so silence goes in as
  silence, never as a finding.
- Record uncertainty honestly: an unknown listed is worth more than a guess
  dressed as a fact.
- No solution design here. If the user starts designing, note the hunch and
  steer back to problem and evidence.
