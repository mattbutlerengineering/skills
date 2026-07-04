---
name: autorun
description: Use when the user wants a whole run driven end to end from a one-time brief — they supply the feature description and answers to the big questions up front, then an orchestrating agent advances the run from idea through ship, one fresh subagent per stage, answering each stage's interview from the brief and logging an assumption wherever the brief runs out. This drives many stages unattended; it is not the router (next advances one stage, interviewing live) and does not shortcut the pipeline — each stage either produces its artifact or records a protocol-sanctioned skip.
---

# Autorun (agent-driven full run)

Drive a run end to end from a brief collected once, dispatching a fresh
subagent per stage. The artifacts remain the only state between stages —
the orchestrator carries nothing a subagent can't re-read from the run
directory. The brief substitutes for live interviews; every gap in it
becomes a logged assumption, never a silent guess.

## Process

1. **Collect the brief — the only interview.** First read
   `../../docs/pipeline-protocol.md` (relative to this skill's base
   directory) and apply its run-discovery rule: use (or create) the run
   directory before writing anything into it. If that directory already
   holds `autorun-brief.md`, this is a resume — confirm only the gaps,
   keep the assumptions already logged, and go to step 2. Otherwise ask
   once, up front:
   - the feature or product description (what and why);
   - run scale (product or feature) and, for a feature, its slug;
   - the inputs the interview-only early stages need, since the brief is
     their only source — the Idea stage covers all of these (idea/SKILL.md):
     the problem from the sufferer's view; who has it and how they cope
     today; why now; what evidence exists the problem is real (anecdote
     counts, labelled as such); the rough shape of a solution (a hunch,
     not a design); a one-sentence success statement; and the biggest
     unknowns or ways this dies. A brief that omits one of these makes that
     stage stop-and-surface by design — so collect them up front;
   - scope boundaries (in and out), success criteria, stack or design
     constraints, anything already decided;
   - whether existing issues from the project's issue tracker should seed
     the run — if yes, they enter the breakdown as work items carrying
     their issue references (the protocol's opt-in tracker mirror,
     ADR-0026); a brief that says nothing about the tracker means no
     tracker interaction at all;
   - whether the work has a user-facing surface — this drives the PRD's
     `ux:` decision;
   - **release authorization**: the project's release mechanism and
     versioning convention, and whether this run may execute it. Absent
     an explicit yes, the default is prepare-and-stop (see step 5).
   If the user has supplied these, confirm only the gaps. Write the brief
   into the run directory as `autorun-brief.md`. The brief is not an
   artifact: it never counts toward orientation or active-run discovery.

2. **Orient.** Apply the protocol's orientation rules to the run
   directory fixed in step 1, exactly as the `next` router would. The
   next stage is the first incomplete one; a fresh run starts at Idea.

3. **Dispatch one subagent for the current stage.** Where dispatching a
   fresh agent context isn't supported, run the stage inline instead —
   either way, the artifacts stay the only state carried between stages.
   The subagent gets:
   - the stage skill to follow and the run directory;
   - the brief, as the source of interview answers;
   - standing instructions: answer interview questions from the brief;
     where the brief is silent, apply this test: if the stage skill
     presents named options with a recommended default, take that default
     and log it in the stage artifact's frontmatter under `assumptions:`
     (the protocol's `assumptions:` convention — the only place
     assumptions live); otherwise — any question with no skill-supplied
     default, including every evidentiary question — stop and surface,
     never guess; produce the stage artifact per the skill; never fabricate
     verification evidence — run the real commands.

4. **Gate between stages.** When the subagent returns, confirm the stage
   artifact exists and is complete per the protocol before advancing —
   an absent or incomplete artifact after dispatch is a failed stage. If
   the same stage fails twice in this invocation, stop and report —
   don't route past a broken stage.

5. **Repeat 2–4 through ship** (`release.md`), with ship held to the
   release authorization in the brief. Unless the brief explicitly
   authorizes the release, ship **prepares and stops**: run the
   pre-flight checks and write `release.md` recording readiness and the
   exact release steps, but execute no externally visible release action
   — no deploy, publish, tag, or merge. And regardless of what the brief
   authorizes, never release unattended past unfixed critical review
   findings — stop and surface instead. Run operate only when feedback
   already exists to capture.

6. **Report.** Stage by stage: the artifact produced, its `assumptions:`
   entries, verification evidence, anything flagged for human review —
   including a release that was prepared but not executed. Aggregate
   every assumption from the artifacts' frontmatter into one list; note
   that the run was autorun-driven. Ship is where autorun stops: the run
   stays active until `retro.md` exists, and operate remains available
   once there is feedback to capture.

## Rules

- One subagent per stage, always fresh — state lives in the artifacts,
  not in the orchestrator's memory.
- Every assumption is written down in the artifact where it was made
  (frontmatter `assumptions:`); a silent guess is a defect.
- No externally visible release action without explicit authorization in
  the brief — prepare-and-stop is the default. Unfixed critical review
  findings block an unattended release unconditionally.
- Stop and surface instead of assuming when a gap is expensive to get
  wrong: irreversible choices, spend, external commitments.
- Conditional stages follow the protocol's skip-recording rules — skipped
  is recorded, never inferred.
- Verification is real: the verify stage runs the repo's actual commands,
  and evidence is quoted, not asserted.
