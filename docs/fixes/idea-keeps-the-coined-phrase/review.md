---
stage: review
run: maintenance:idea-keeps-the-coined-phrase
date: 2026-10-25
---

# Review: Idea briefs paraphrase away the pitch's coined phrase

## Scope

`git diff origin/main...fix/idea-keeps-the-coined-phrase`: one line in
`skills/idea/TEMPLATE.md`, one sentence in `skills/idea/SKILL.md` step 5,
two tests, one eval record and the run docs. A patch-scale change to skill
prose, so the review ran inline (the protocol's Run scale section).

## Findings

### Minor: the grader cannot see a phrase wrapped inside a blockquote

- Scenario: the brief wraps the quote, so `shift` ends one line and
  `> rota` starts the next. `self-healing shift\s+rota` does not match,
  and the grader scores a kept phrase as dropped (verification run 1).
- Standard: none
- Decision: deferred, not fixed here. Changing the grader in the same run
  that its score judges would look like editing an eval to pass. A
  follow-up can let the pattern allow a quote marker, with the
  verification's evidence as the case for it.

## Passes with no findings

- Correctness: the new line sits between the title and `## Problem`, so
  no section heading moves. Every existing template test passes, as does
  the old-brief validation (`TestOldBriefStillValidates`).
- Downstream readers: `prd` reads the brief's sections by heading. A
  blockquote under the title changes none of them.
- Security: none; prose only.
- Complexity: one template line, one sentence.
- ADR compliance: no ADR touches the brief's first lines; no new ADR owed.
- Domain passes: none selected.
- Standards: no matching statement.

## Verdict

Ready to ship. No critical or major finding; one minor deferred with its
reason.
