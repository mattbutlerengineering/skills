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
     project.
   - What is out of scope? (Push for real exclusions, not padding.)
   - What open questions remain, and who can answer them?

4. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `prd.md`, with protocol frontmatter including
   the `ux:` field. Scale to the run: a feature PRD is roughly a page; a
   product PRD is comprehensive.

5. **Hand off.** Next stage is UX Design if `ux: required`, otherwise
   Architect. Say which and how to get there.

## Rules

- Requirements, not design: no architecture, no data models, no technology
  choices. If the user volunteers one, park it in Open questions for the
  Architect stage.
- Every user story names a real actor from the actor list.
- Success criteria must be checkable by a person or a test — if you can't
  imagine the check, rewrite the criterion.
