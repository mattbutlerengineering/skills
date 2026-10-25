---
stage: review
run: maintenance:one-owner-for-copied-skill-text
date: 2026-10-25
---

# Review: copied skill text with no owner

## Scope

`git diff origin/main...HEAD` at f905d53..2b90cc3: the new
`skills/audit/references/recon.md` and `skills/audit/references/routing.md`;
edits to `skills/audit/SKILL.md`, `skills/automate/SKILL.md`,
`skills/animated-diagram/references/design-system.md`,
`skills/interactive-architecture-diagram/references/design-system.md`,
`skills/interactive-architecture-diagram/SKILL.md` and
`skills/work-queue/SKILL.md`; the new
`tests/test_skill_shared_references.py`; and this run's artifacts.
Blast radius is skill prose only (defect.md), so the passes are scaled
to it: each one read the whole diff once, side by side with the removed
text.

## Findings

### Minor: each skill now reads the union of the two recon texts

- Scenario: `recon.md` merges the two copies, so audit now also reads
  automate's anecdote (a run rebuilt a fix sitting in an open PR) and
  automate now reads audit's "the reader's tree is not yours" rationale
  and "recon is cheap and re-litigation is not". Neither adds or removes
  an instruction; both were reasons for the same rule.
- Standard: none
- Decision: deferred — accepted as is; the rule each skill follows is
  unchanged, and splitting the reasons back per skill would rebuild the
  copy this run removes.

### Minor: interactive inherits the owner's `external` label

- Scenario: interactive's removed table said `external` meant
  "third-party / SaaS"; the owner's row says "third-party / SaaS /
  client". Same stroke and fill; the label is a superset.
- Standard: none
- Decision: deferred — accepted; the colour, the only value a node is
  drawn from, is identical.

### Minor: a sibling reference only resolves when the plugin installs whole

- Scenario: `automate` and `interactive-architecture-diagram` now read a
  file in another skill's directory. A harness that copies one skill
  directory on its own would leave the reference dangling. The plugin
  installs every skill side by side, `lint.SIBLING_ASSET` (#1046) checks
  a `SKILL.md`'s sibling reference ships, and
  `skills/pipeline-board/SKILL.md:18` and its `board-grammar.md` set the
  precedent for both forms used here.
- Standard: none
- Decision: deferred — accepted under the existing precedent. Lint does
  not check a backticked sibling path inside a `references/` file (the
  interactive design system's `../../animated-diagram/...` form); the
  new test's `test_each_cited_owner_ships` covers this one.

### Minor: copies this run left in place

- Scenario: three smaller shared passages remain. The "flat and
  precise" look paragraph (three lines) opens both dark design systems;
  the "Considered and not worth" and coverage-statement report sections
  of audit and automate share a shape but name each skill's own
  categories; `skills/implement-queue/SKILL.md:100` repeats the
  "dropping every entry that carries a `pull_request` key" clause for a
  different query. The interactive boilerplate's CSS still holds hex
  literals that mirror the owner palette, which is code and cannot cite.
- Standard: none
- Decision: deferred — out of the Owner-approved scope, recorded in
  defect.md's Ruled out; a seed if anyone wants them.

## Passes with no findings

- **Correctness**: every removed sentence was traced to its new home
  (owner file or the consumer's remaining text); the audit step-6 and
  automate step-7 "dedupe read" citations in each Rules section still
  name the step that points at it; work-queue's "item 2's `Closes #N`"
  citation is unaffected by renumbering item 9. Findings above are the
  only drift found.
- **Design**: one owner per passage, consumers keep only their
  differences; no new mechanism, no generated text.
- **Security**: no code path, credential or command changed; the REST
  fallback commands moved byte-identical.
- **Complexity**: the test is one data table and five small tests;
  counting rather than `assertIn` is the point (an `assertIn` cannot see
  a pasted-back copy, and the mutation run in verification.md shows the
  count does).
- **ADR compliance**: ADR-0008 (self-contained skills) is about
  third-party dependencies, and no tool, MCP server or plugin
  dependency was added. ADR-0023: `audit`, `automate` and both diagram
  skills stay utility skills owning no artifact; the new files are
  references, not skills. ADR-0095: no `.claude-plugin/plugin.json`
  change. No skill `description:` frontmatter changed.

No domain passes were selected: the diff is prose and a stdlib test.

## Verdict

Ready to ship: 0 major findings, 4 minor, all deferred as accepted or out
of scope. All five passes ran; none is unknown. The one gap carried from
Verify is the NOT RUN live-agent criterion, so this verdict covers the
text and the checks, not a model's reading of the moved text.
