---
name: verify
description: Use when implementation is complete and it's time to demonstrate the work meets the PRD's success criteria — running tests and collecting evidence — or when the user asks to verify the work or wants regression-test evidence that a fixed defect cannot silently return. Produces verification.md. In a maintenance run this stage is mandatory and the regression test is its centerpiece.
---

# Verify

Demonstrate — don't assert — that the built thing meets the PRD's success
criteria. Draft-first: run the checks, collect the evidence, present the
verdict.

## Process

1. Read `../../docs/pipeline-protocol.md` for run discovery, gating, and
   frontmatter conventions.

2. **Soft gate.** Predecessor: the run's breakdown with all items checked
   (`breakdown.md`, or `defect.md`'s inline items in a maintenance run
   with `re-entry: implement`). If items are open, say which and offer to
   route back to Implement (or verify the completed subset, noting the
   gap).

3. **Build the criteria list.** Every success criterion from `prd.md`, plus
   every acceptance criterion from `breakdown.md` not already covered by a
   PRD criterion. In a maintenance run the criteria come from `defect.md`
   instead: expected behavior restored, the recorded blast radius
   exercised, and a regression test in place.

   The regression test is the centerpiece: a test that reproduces the
   defect from the brief's evidence, failed before the fix, and passes
   now. Without it the same defect can silently return, and the stage is
   not complete.

4. **Verify each criterion.** Prefer automated evidence (run the test suite;
   quote the relevant results) over manual walkthroughs, but do the manual
   check when that's what the criterion needs. Record for each: the
   criterion, the check performed, the evidence (actual output, not a
   summary of it), and pass/fail.

5. **Report honestly.** Failures and gaps go in the artifact as failures and
   gaps — never soften them. A criterion that can't be verified is a finding
   in itself (and a lesson for the next PRD).

6. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `verification.md` with protocol frontmatter.

7. **Hand off.** Failures route back to Implement. Otherwise next stage is
   Review.

## Rules

- Test external behavior against the criteria — never implementation
  details.
- Evidence is quoted output, command results, or observed behavior — a
  checkbox with no evidence is an assertion, not a verification.
- Note what was NOT verified and why; silent coverage gaps read as "covered".
- A maintenance run never skips this stage — the regression test is the
  point of the fix (see the protocol's maintenance orientation).
