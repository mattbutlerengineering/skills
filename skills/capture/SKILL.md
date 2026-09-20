---
name: capture
description: Use when the user reports a bug, defect, or regression to fix, or wants to start a refactor or dependency upgrade as a tracked maintenance run — not a new feature, and no fix artifacts exist yet. Interviews the user and produces the defect brief (defect.md) that seeds the run and records its re-entry depth.
---

# Capture

Turn a reported defect — or a degraded condition worth a refactor or
upgrade — into a brief that seeds a maintenance run. The knowledge is in
the user's head (what broke, what they've already tried), so this skill
interviews — it does not draft.

## Process

1. Read `../../docs/pipeline-protocol.md` for the maintenance-run
   orientation, run discovery, scale, and frontmatter conventions.

2. **Establish the run.** This is a maintenance run; artifacts live under
   `docs/fixes/<slug>/`. Agree on the slug now. Then pick the variant:
   a **defect brief** (something is broken — bug, regression) or a
   **condition brief** (something is degraded — refactor, dependency
   upgrade). The filename is `defect.md` either way.

   When starting from a backlog seed, claim it in place — append
   `(claimed: maintenance:<slug>)` to the seed's line in
   `docs/backlog.md` per the protocol's seed-backlog section — and record
   the seed as the origin in `defect.md`. A parked defect re-enters here,
   not through `idea`: it is still a defect, and a maintenance run is
   what keeps Verify mandatory.

3. **Check what is already in flight.** Run discovery sees the working
   tree; a fix another agent has already finished sits on a branch,
   waiting for a human, where no enumeration of run directories can find
   it. Before writing `defect.md`, look over the work already awaiting
   review and ask whether one of them does this — the protocol's *Work
   already in flight* section. Say which of its three outcomes happened:
   nothing matched, the check could not run, or something already does
   this and the run stops here instead of building it twice. Reporting a
   check that could not run as a clean result is the one failure this
   step must never produce.

4. **Seed from tracker intake (optional).** A defect may arrive as a
   tracker issue carrying the project's intake marker (the protocol's
   tracker-mirror section names the convention; packaging names the
   concrete label). Two entry paths, both user-initiated: the user names
   the issue directly ("capture #123"), or asks what intake is waiting —
   list the intake-marked issues and let them pick. Copy into the brief
   the issue title as the working title, the filed date, and the body's
   observed-behavior and reproduction content — verbatim quotes are
   fine — as raw material for the interview below; intake seeds the
   interview, it does not replace it. Record the issue in frontmatter as
   `intake: #123` (duplicates of the same defect join
   `intake-duplicates:`), then never read it again — the brief is the
   state from here. The issue closes at Ship, not now; a run abandoned
   before then un-marks the issue instead. An intake-marked feature
   request seeds nothing — route it to `idea` and leave the issue open.

5. **Interview.** One question at a time, each with your recommended
   answer when you have one. For a defect brief, cover at least:
   - What exactly is broken — observed behavior vs expected?
   - Reproduction evidence: steps, a failing test, logs, a user report?
     If it can't be reproduced yet, say so — that's the first work item.
   - Best root-cause hypothesis? Label it a hypothesis, not a finding.
   - Blast radius: who and what is affected, how badly, since when?
   - What has already been ruled out — dead ends the fixer should not
     re-walk?

   For a condition brief, cover instead: what is degraded, the evidence
   of degradation (build times, incident count, versions behind), and the
   target state that would end the run.

6. **Decide re-entry depth.** A scoped fix with no design decisions
   re-enters at Implement; anything design-touching re-enters at
   Architect. Record the decision in frontmatter as
   `re-entry: implement` or `re-entry: architect`. With
   `re-entry: implement`, draft the work items as checkboxes inline in
   `defect.md` — there is no separate `breakdown.md`. With
   `re-entry: architect`, leave work items out; the `architecture.md` +
   `breakdown.md` chain owns them.

7. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `defect.md`, with protocol frontmatter.

8. **Hand off.** State the next stage per the recorded re-entry — the
   `implement` skill or the `architect` skill (or the router).

## Rules

- Capture is an entry stage: it has no predecessor artifact, so there is
  never a soft gate — but the protocol read always comes first.
- A missing capability is a new feature, not a defect — route the user to
  the `idea` skill and a feature run instead.
- A defect worth remembering but not worth a run today may be parked as a
  seed in `docs/backlog.md` (the protocol's seed-backlog section) instead
  of opening a run.
- Record hypotheses as hypotheses. A guess dressed as a root cause sends
  the fixer down the wrong path with confidence.
- Ruled-out dead ends are evidence too — capturing them is cheaper than
  re-investigating them.
- The reproduction evidence captured here becomes the regression test:
  Verify is never skippable in a maintenance run.
- Blast radius recorded here drives downstream scale (the protocol's
  Run scale section), so be concrete about who is affected.
