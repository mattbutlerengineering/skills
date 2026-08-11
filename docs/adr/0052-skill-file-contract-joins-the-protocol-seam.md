# The skill-file contract joins the protocol seam; lint pins the recitals

- Status: accepted
- Date: 2026-08-05

Amends ADR-0021: protocol.py's charter grows from taxonomy, artifact
tables, frontmatter reading, and next-stage derivation to include the
skill-file contract. The 2026-08-05 architecture review surfaced all
three findings.

## Context

- **The path shape.** `skills/<slug>/SKILL.md` was constructed
  independently in lint.py (the skill checker and the router checker)
  and trigger_eval.py's description loader — three copies of a shape
  protocol.py never owned.
- **The frontmatter rules, twice.** lint and the trigger-eval loader
  each stated the frontmatter rules with different error contracts
  (problem strings vs raised ValueErrors), and the loader skipped the
  1024-char Pi description limit lint enforces (ADR-0027) — an observed
  divergence: an overlong description passed eval but failed lint. That
  is the seam bar (multiple real callers AND divergent copies).
- **The recitals.** 40 of the 71 numbered steps across the stage skills
  restate pipeline conventions in prose — soft-gate the predecessor
  artifact, hand off to the successor, artifact filenames — in up to six
  phrasings per convention. The duplication is FORCED: skills are vended
  self-contained (ADR-0008), so a target repo has the prose but not
  protocol.py. It cannot be deduplicated, and nothing pinned it, so
  drift was silent.

## Decision

- `protocol.skill_path(root, slug)` is the one place the
  `skills/<slug>/SKILL.md` shape lives; lint and trigger_eval are thin
  callers (trigger_eval's `--skills-dir` flag becomes `--skills-root`,
  the plugin root the shape hangs off).
- `protocol.skill_frontmatter_problems(root, slug)` is the single
  frontmatter validator with lint's problem strings as the one error
  contract; `SKILL_DESCRIPTION_LIMIT` moves in beside it. The
  trigger-eval loader raises the joined problem strings, gaining the
  1024-char check — the divergence dies.
- `lint.check_skill_recitals` pins the forced prose copies to the
  protocol tables: each stage skill's soft-gate step must name its
  predecessor artifact (both `prd.md` and `ux.md` for the stage after
  the UX conditional, ADR-0017) and no downstream artifact; every
  "next stage is <stage>" claim must name the table successor (none for
  operate, which completes the run); each skill must name its own
  artifact; capture must recite both `re-entry:` options (ADR-0025).
  Matching is robust to phrasing — claims are scanned case-insensitively
  with hyphens as spaces and across line wraps; gate facts are the
  backticked artifact filenames inside the soft-gate step — and strict
  on the facts.

## Consequences

- The recital copies remain (vending forces them) but can no longer
  drift silently: a stage skill that renames an artifact or reroutes a
  hand-off fails lint until protocol.py's tables agree.
- ADR-0021's evidence bar was met, not lowered: three path copies and an
  observed frontmatter divergence graduated this knowledge into the
  seam. Nothing else joins protocol.py without the same evidence.
- An overlong description now refuses to eval with the same string it
  refuses to lint (no current description exceeds the limit; the
  longest is 655 chars).
- Pins live at the seam's suite (tests/test_frontmatter.py:
  TestSkillPath, TestSkillFrontmatterProblems), the checker's suite
  (tests/test_lint_checkers.py: TestSkillRecitals, whose clean fixture
  tree now derives conformant recitals from the tables), and the
  loader's suite (tests/test_trigger_eval.py: TestLoadDescriptions).
