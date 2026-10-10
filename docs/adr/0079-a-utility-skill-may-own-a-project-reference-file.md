# A utility skill may own a project reference file, by section

- Status: provisional
- Date: 2026-10-10

Extends ADR-0023. Utility skills still own no run artifact, have no
template and are never routed to; this decides what it means for one to
write a file outside a run, and how two skills share one such file.

## Context

Issues #624 and #627 ask for two utility skills. `ux-writing` audits and
rewrites the words in an interface; `ux-patterns` writes down how the
interface behaves — confirm or undo, loading, errors, empty states,
validation, focus — and holds screens to it. Both are worth little if
their decisions evaporate at the end of a session. The research behind
them (`docs/research/ux-writing-and-ux-patterns.md`) found the same
lesson in the two closest pieces of prior art: Impeccable's `DESIGN.md`
and interface-design's `system.md` both persist decisions in the project
so the next session starts from them instead of re-deriving them.

Until now, every file a skill in this repo wrote was either a run
artifact (ADR-0004: under the docs root for a product run, under
`docs/features/<slug>/` or a fix directory otherwise) or code. A
decision about a whole product's voice or its deletion behaviour belongs
to neither: it outlives any one run, and it is not owned by a stage.

## Decision

1. **A new kind of file: the project reference file.** A utility skill
   may write one file at the target repo's `docs/` root, outside every
   run directory. It is not a run artifact: it has no protocol
   frontmatter, no typed ID, no row in `protocol.py`'s artifact table,
   no soft gate, and `next` never routes on it. Its presence or absence
   changes no run's state.
2. **The first one is `docs/ux-patterns.md`.** It holds the product's
   behaviour rules, each checkable and naming the code that implements
   it; a states checklist; a **Voice & terms** section; and a dated,
   append-only decisions log. Visual tokens are pointed at, never copied
   into it.
3. **One file, owned by section.** `ux-patterns` owns every section
   except `## Voice & terms`, which `ux-writing` owns. Neither skill
   edits the other's sections. The heading `## Voice & terms` is the
   contract between them, written out in both skills' references,
   because skills are self-contained (ADR-0008) and cannot link to each
   other's files. Either skill may create the file; the one that does
   writes only its own sections and leaves the other's heading with an
   ownership note.
4. **Readers do not write.** `polish` and `ux-design` read the file, when
   it exists, before they work: its rules are decisions already made, and
   `ux-design`'s "what existing conventions must this match?" is answered
   from it before it is asked. Neither writes it; a change they find
   necessary is handed to the owning skill.
5. **Written by extraction, changed by decision.** The owning skills
   derive the content from the code first and ask the human only the
   judgement calls, one at a time. A rule changes only through a dated
   decision entry; an audit that finds code disagreeing with a rule
   reports it as a fix or a candidate rule, never edits the rule
   silently.

## Consequences

- One place to look for how a product behaves and speaks, instead of
  separate product, design, glossary and voice files. The cost is shared
  ownership of one file, which the section split and the heading
  contract make explicit.
- Nothing mechanical enforces the section split yet. A lint or gate
  would have to parse a file in a target repo this repo never sees, so
  the split lives in the two skills' instructions. If a real run shows one skill writing the other's
  section, that observed divergence is what would justify a check.
- A stale file is the main risk: rules nobody re-reads drift from the
  code. The audit mode of `ux-patterns` and the dated decisions log are
  the mitigation; there is no expiry.
- Another utility skill wanting a project reference file follows this
  record: one file, at the docs root, ownership stated per section, read
  by others and written only by its owners. A second such file needs no
  new ADR unless it breaks one of those terms.
