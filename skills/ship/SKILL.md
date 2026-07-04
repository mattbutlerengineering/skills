---
name: ship
description: Use when reviewed work is ready to go to production — pre-flight checks, release steps, rollback plan — or when the user asks to ship, release, or deploy the work. Produces release.md.
---

# Ship

Get the reviewed change into production deliberately: pre-flight, release,
post-release. Checklist-driven — the artifact is the record that each step
actually happened. "Production" means wherever users get this work: a
deployment, a published package, an installable plugin, a merged release
branch.

## Process

1. Read `../../docs/pipeline-protocol.md` for run discovery, gating, and
   frontmatter conventions.

2. **Soft gate.** Predecessor artifact: `review.md` with no unfixed critical
   findings. If missing or blocked, apply soft gating — shipping past an
   unfixed critical requires the user to say so explicitly, logged in the
   artifact.

   In a maintenance run, scale the ceremony to the blast radius recorded
   in `defect.md`: a patch bump still gets the pre-flight, a concrete
   rollback plan, and the regression evidence — but not a product-run
   release train. The rollback plan never scales away.

3. **Pre-flight.** Confirm and record each:
   - Verification is green (`verification.md` has no unresolved failures).
   - No secrets in the diff; required configuration exists in the target
     environment.
   - Migrations/data changes have a tested forward path.
   - The rollback plan exists and is concrete: the actual commands or steps
     to undo this release, not "revert if needed".

4. **Release.** Execute the project's release mechanism step by step,
   recording each command/action and its result as it happens. Version and
   tag according to the project's convention.

5. **Post-release.** Check the shipped thing actually works where users get
   it (smoke check the deployed surface, install the published package).
   Record the evidence.

6. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `release.md` with protocol frontmatter.

7. **Hand off.** Next stage is Operate.

## Rules

- Never ship on a red verification — route back instead.
- Record what actually happened, including hiccups; a clean-looking release
  log that omits the retry is a lie to the next release.
- If the release fails midway, the rollback plan runs and the artifact
  records both — a failed ship is a valid, complete `release.md`.
