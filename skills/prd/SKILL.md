---
name: prd
description: Use when an idea needs requirements — turning an idea brief into a PRD with scope and success criteria, or when the user asks for a PRD directly. Interviews the user and produces prd.md.
---

# PRD

Turn an idea brief into requirements: what we're building, for whom, what
"done" means, and what we're explicitly not doing. Interview-driven — intent
lives in the user's head, not in the codebase.

## Process

1. Read `../../docs/pipeline-protocol.md` for run discovery, gating, scale,
   and frontmatter conventions.

2. **Soft gate.** Predecessor artifact: `idea.md`. If missing, apply the
   protocol's soft-gating options (backfill interview or proceed with logged
   assumptions).

3. **Interview.** One question at a time, with your recommended answer where
   you have one. Cover:
   - Who are the actors? (Name them precisely — they become the user-story
     vocabulary.)
   - What can each actor do that they can't today? (These become user
     stories: "As an <actor>, I want <feature>, so that <benefit>.")
   - What are the measurable success criteria? (Verify will test against
     these — vague criteria here means unverifiable work later.)
   - **Does this work have a user-facing surface?** The answer sets the
     `ux:` frontmatter field (`required` or `not-applicable`) that decides
     whether the UX Design stage runs. It depends on the feature, not the
     project. If `not-applicable`, also capture a one-line rationale (e.g.
     "CLI only, no user-facing surface") — it becomes the `ux-reason:`
     frontmatter field, which Architect echoes when recording the skip.
   - What is out of scope? (Push for real exclusions, not padding.)
   - What open questions remain, and who can answer them?

4. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `prd.md`, with protocol frontmatter including
   the `ux:` field (and `ux-reason:` when `ux: not-applicable`). Scale to the run: a feature PRD is roughly a page; a
   product PRD is comprehensive. An ambiguity you hit mid-section that
   the interview did not settle gets an inline marker at the exact clause
   — `[NEEDS CLARIFICATION: <question>]` — rather than a guess; "Open
   questions" stays for what is genuinely open at the artifact's close.

5. **Clarify (bounded).** If `prd.md` carries markers, run one clarify
   pass before hand-off (ADR-0071):
   - Ask at most **5** questions per pass, one at a time, prioritized by
     the artifact's own section headings (Problem statement, Success
     criteria, Scope, Actors, Open questions) — no invented taxonomy.
   - Write each answer back immediately, under a dated
     `### Clarifications / Session YYYY-MM-DD` heading in `prd.md`, and
     remove the resolved marker from its clause (not struck through).
   - While resolving, check for unquantified claims ("prominent display"
     with no measure) and turn them into checkable criteria.
   - Markers left after the pass mean the PRD is not ready for approval:
     `gates.py` detector N fails any `prd.md` or `architecture.md` that
     still carries one. The same pass works ad hoc on `architecture.md`,
     prioritized by its headings (Components, Data model, Interfaces &
     contracts, Decisions & alternatives).

6. **Hand off.** Next stage is UX Design if `ux: required`, otherwise
   Architect. Say which and how to get there.

## Rules

- Requirements, not design: no architecture, no data models, no technology
  choices. If the user volunteers one, park it in Open questions for the
  Architect stage.
- Every user story names a real actor from the actor list.
- Success criteria must be checkable by a person or a test — if you can't
  imagine the check, rewrite the criterion.
