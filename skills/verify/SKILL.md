---
name: verify
description: Use when implementation is complete and it's time to demonstrate the work meets the PRD's success criteria — running tests and collecting evidence — or when the user asks to verify the work. Produces verification.md.
---

# Verify

Demonstrate — don't assert — that the built thing meets the PRD's success
criteria. Draft-first: run the checks, collect the evidence, present the
verdict.

## Process

1. Read `../../docs/pipeline-protocol.md` for run discovery, gating, and
   frontmatter conventions.

2. **Soft gate.** Predecessor: `breakdown.md` with all items checked. If
   items are open, say which and offer to route back to Implement (or
   verify the completed subset, noting the gap).

3. **Build the criteria list.** Every success criterion from `prd.md`, plus
   every acceptance criterion from `breakdown.md` not already covered by a
   PRD criterion.

4. **Verify each criterion.** Prefer automated evidence (run the test suite;
   quote the relevant results) over manual walkthroughs, but do the manual
   check when that's what the criterion needs. Record for each: the
   criterion, the check performed, the evidence (actual output, not a
   summary of it), and pass/fail. The artifact's `## Summary` counts or
   names every NOT RUN / unknown criterion and never reads as an
   unqualified pass over them (the fail-closed roll-up; claim kinds in
   `../../CONTEXT.md`). Detector H refuses a Summary that names no
   unknown word over a criterion with a labelled NOT RUN verdict (ADR-0107).

5. **Report honestly.** Failures and gaps go in the artifact as failures and
   gaps — never soften them. A criterion that can't be verified is a finding
   in itself (and a lesson for the next PRD).

6. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `verification.md` with protocol frontmatter.

7. **Hand off.** Failures route back to Implement. Otherwise next stage is
   Review. Commit the artifact on the run's branch — the protocol's
   "Commit at the stage boundary" section owns the rule and the commit
   subject.

## Rules

- Test external behavior against the criteria — never implementation
  details.
- Evidence is quoted output, command results, or observed behavior — a
  checkbox with no evidence is an assertion, not a verification.
- Note what was NOT verified and why; silent coverage gaps read as "covered".
- **Maintenance runs**: Verify never scales away (the protocol's Run
  scale section) — the regression test, from the defect brief's
  reproduction evidence, is the centerpiece. Depth may scale; the
  regression never.
