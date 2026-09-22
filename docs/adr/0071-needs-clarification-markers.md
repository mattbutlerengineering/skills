# Inline [NEEDS CLARIFICATION] markers, CI-enforced

- Status: accepted
- Date: 2026-09-21

## Context

- Epic #439 ratified an adopt/adapt/reject pass over four survey
  shortlists (issue #436). `docs/research/spec-driven-sdlc.md`
  shortlisted GitHub Spec Kit's inline ambiguity marker plus its bounded
  clarify protocol as shortlist item 1, verdict Adopt, "Own ADR? Yes"
  (item 7, requirements-quality checklists, folds into this same ADR
  per the survey's own rationale).
- This repo already records unknowns in two places, both *aggregate*
  and detached from the requirement they infect: `assumptions:`
  frontmatter (ADR-0005, soft gating — logs a decision made without
  live user input) and the PRD template's "Open questions" section.
  Neither pins an unresolved ambiguity to the exact clause it sits
  inside, and nothing stops a `prd.md` with an unresolved ambiguity
  from clearing gate 1 (ADR-0033).
- Spec Kit's marker sits inline at the ambiguous clause, in a fixed,
  greppable syntax — `[NEEDS CLARIFICATION: auth method not specified -
  email/password, SSO, OAuth?]` — and its `/speckit.clarify` protocol is
  bounded: "Maximum of 5 total questions across the whole session," a
  nine-category ambiguity taxonomy for prioritization, and each answer
  is written back immediately under a dated `### Session YYYY-MM-DD`
  heading — the spec updates after every answer, not batched.
  (`docs/research/spec-driven-sdlc.md`, "Rationale 1"; primary source
  `templates/spec-template.md` lines 90-99, `templates/commands/
  clarify.md` lines 130, 185-205, github/spec-kit.)
- The survey's own framing of the value-add over Spec Kit's version:
  "this gives the marker teeth Spec Kit itself lacks, since its gate is
  prompt-enforced while the factory's would be CI-enforced." That is
  the part worth its own ADR — the marker syntax alone is a template
  convention (ADR-0015), not a hard-to-reverse decision; the CI
  enforcement rule is.
- This slots directly into ADR-0011 ("interview early, draft late"):
  front-end stages (Idea, PRD, UX Design) interview relentlessly, but
  Architect onward drafts first and asks only about genuine trade-offs
  — a marker lets a front-end stage draft past an ambiguity instead of
  stalling the interview, and the clarify pass burns markers down
  before the artifact can clear its gate.

## Decision

- **Marker convention.** `prd.md` and `architecture.md` drafts (the two
  artifacts with a human approval gate — ADR-0033) MAY carry
  `[NEEDS CLARIFICATION: <question>]` inline, at the exact clause the
  ambiguity sits in, alongside — not replacing — the existing
  `assumptions:` frontmatter and "Open questions" section: the marker
  is for an ambiguity a drafting stage hits mid-section; "Open
  questions" stays for a question genuinely open at the artifact's
  close. `idea.md` is not in scope: its Problem/Evidence/Unknowns &
  risks sections already carry unresolved-ness as prose, and Idea has
  no approval gate to enforce against.
- **Bounded clarify pass.** A clarify step, added to the PRD skill (and
  usable ad hoc against `architecture.md`), resolves markers: at most 5
  questions per pass, prioritized by a taxonomy derived from the
  artifact's own section headings (for `prd.md`: Problem statement,
  Success criteria, Scope, Actors, Open questions; for
  `architecture.md`: Components, Data model, Interfaces & contracts,
  Decisions & alternatives) rather than inventing a new taxonomy. Each
  answer is written back immediately under a dated `### Clarifications
  / Session YYYY-MM-DD` heading in the same artifact — resolved
  markers are removed from the clause, not left struck through — same
  immediacy as Spec Kit's, adapted to this repo's stage-skill shape
  instead of a slash-command chain.
- **CI enforcement, not just prompt enforcement.** A new `gates.py`
  detector (letter assigned at implementation time, avoiding whatever
  is claimed by then — the same "skip a claimed letter rather than
  collide" discipline `docs/features/codex-style-standards-enforcement/
  architecture.md` already used for `K`/`M`) fails when any `prd.md` or
  `architecture.md` still carries an unresolved `[NEEDS CLARIFICATION:
  ...]` marker. This is chosen over a `lint.py` checker because — same
  reasoning the codex-style-standards-enforcement design already
  recorded for its own detector-vs-lint choice — `gates.py`'s detectors
  ship to every factory-stamped product repo via `factory_init.MIRRORS`
  and already gate the knowledge plane generically (PRD/architecture
  drafts in any repo using this pipeline), while `lint.py` is unmirrored
  and specific to this meta-repo's own skill authoring.
- **Requirements-quality checklist (survey item 7) folds in here,
  scoped down.** Rather than a separate checklist artifact (Spec Kit's
  `/speckit.checklist`), the PRD skill's existing gate-1 presentation to
  the human gains a short reminder to check for unquantified claims
  ("prominent display" without a measure) as part of resolving markers
  — not a new file, not a new gate.

## Consequences

- No code ships with this ADR (planning-only, per epic #439's framing);
  the marker convention's template edits, the clarify-pass skill
  update, and the new detector are follow-up implementation work,
  tracked by this run's breakdown row.
- The detector adds a new failure mode gate 1 (PRD approval) did not
  previously have: a `prd.md` with a live marker cannot honestly be
  called ready for human approval, closing a gap the two existing
  aggregate mechanisms (`assumptions:`, "Open questions") could not —
  neither is CI-checked for completeness today.
- Does not touch `assumptions:` frontmatter or "Open questions" — both
  keep their existing meaning and mechanism; the marker is additive,
  narrower-scoped machinery for an ambiguity a clause-level reader
  would otherwise silently paper over while drafting.
- Serves the map's optimization target (autonomy per human-hour at the
  three gates, ADR-0069): an ambiguity caught and resolved before gate
  1, instead of discovered by a human reading the whole PRD at approval
  time or by a downstream work order inventing an answer nobody
  recorded, is gate-wait time not spent re-deriving what the PRD meant.
