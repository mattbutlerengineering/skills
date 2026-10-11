---
name: ship
description: Use when reviewed work is ready to go to production — pre-flight checks, release steps, rollback plan — or when the user asks to ship, release, or deploy the work, get it into production, push it out to users, go live, or cut a release. Produces release.md.
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

3. **Pre-flight.** Confirm and record each:
   - Verification is green (`verification.md` has no unresolved failures).
   - No secrets in the diff; required configuration exists in the target
     environment.
   - Migrations/data changes have a tested forward path.
   - Each ADR the run added has a number free on the base branch and a
     row in `docs/adr/README.md`'s index; a collision renumbers per the
     protocol's "When to write an ADR" numbering rule.
   - The rollback plan exists and is concrete: the actual commands or steps
     to undo this release, not "revert if needed". Beside the steps it
     records the door (one-way or two-way) and the blast radius in the
     words of the protocol's Pull request body section, so `release.md`
     and the PR body make the same call.

4. **Launch brief.** If `docs/launch-demo.json` exists in the repo and
   its `when` field is `ship`, load the `launch-demo` skill through the
   harness's skill-loading mechanism (a skill tool where one exists,
   otherwise a read of the skill file), run it for this run, commit what
   it wrote on the branch, and add one numbered Release-log entry
   quoting the tool's reason line(s) and its verdict verbatim. With no
   config file, or any other `when`, do nothing and write nothing. The
   hook never blocks a release: a COPY-ONLY verdict and a problem exit
   are each one log line, and the release proceeds.

5. **Release.** Execute the project's release mechanism step by step,
   recording each command/action and its result as it happens. Version and
   tag according to the project's convention.

6. **Post-release.** Check the shipped thing actually works where users get
   it (smoke check the deployed surface, install the published package).
   Record the evidence.
   - A maintenance run seeded from a tracker intake issue (`intake:` in
     `defect.md` frontmatter): close that issue — and any
     `intake-duplicates:` — with a comment referencing the run directory.
     "Closed" on the tracker means fixed in a release, not "a run
     started" (the protocol's tracker-mirror section).

7. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `release.md` with protocol frontmatter.

8. **Hand off.** Next stage is Operate.

## Rules

- Never ship on a red verification — route back instead.
- Record what actually happened, including hiccups; a clean-looking release
  log that omits the retry is a lie to the next release.
- If the release fails midway, the rollback plan runs and the artifact
  records both — a failed ship is a valid, complete `release.md`.
- **Maintenance runs**: scale per the protocol's Run scale section — a
  scoped fix may be a single commit merge; a refactor or upgrade gets
  the full pre-flight. The rollback plan is always present, even when
  the release is small.
