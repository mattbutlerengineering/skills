# Pipeline protocol

Shared rules every stage skill follows. Stage skills read this file before
acting; it is the single source of truth for run discovery, orientation,
gating, and artifact conventions.

## Stage order

Idea → PRD → UX Design (conditional) → Architect → Decompose → Implement →
Verify → Review → Ship → Operate

## Runs and run directories

- **Product run** — a greenfield product moving through the full pipeline.
  Artifacts live at the target repo's `docs/` root.
- **Feature run** — a scaled-down pass for one feature, re-entering at Idea
  or PRD. Artifacts live under `docs/features/<slug>/` (kebab-case slug).
- **Maintenance run** — a scaled-down pass for a defect, regression,
  refactor, or dependency upgrade, entering at a capture step. Artifacts
  live under `docs/fixes/<slug>/` (kebab-case slug).

**Run discovery:** candidate run directories are `docs/` plus every
`docs/features/*/` and every `docs/fixes/*/`. A run is *complete* when
`retro.md` exists; *active* when it has at least one artifact and is not
complete. If the user named a feature or fix, use (or create) its directory.
If exactly one run is active, use it. Otherwise, list the candidates and ask
which one.

### Work already in flight

Run discovery sees the working tree. Work that another agent has already
finished does not live in the working tree — it lives on a branch, waiting
for a human, as a pull request, merge request, or patch in review. No
enumeration of run directories can see it.

So the moment a run **starts** is where that is checked: `capture` claiming
a seed or seeding from tracker intake, `idea` claiming a seed. Before
writing the first artifact, look over the work already waiting for review
and ask whether one of them already does this. Three outcomes, and each
must be visible:

- **Nothing matches** — proceed, and say the check ran.
- **The check could not run** — no review surface, no credentials, no
  network. Proceed, and say *that* instead. A check whose failure looks
  the same as a clean result is worse than no check, because it is a clean
  result nobody can doubt.
- **Something already does this work** — stop and surface it. The pipeline
  does not decide which of two agents' attempts wins; it declines to build
  the second one unattended.

This is a **guard, not a door**. It can only ever stop a run from starting,
so the one-way bound above is untouched: nothing here polls, nothing here
seeds a run, and orientation inside an active run still reads run artifacts
alone. The concrete command that lists work awaiting review is packaging's,
like the tracker CLI — the shape of the check is what lives here.

A related rule, deliberately not the same one: a skill that starts *many*
work orders at once also prefers finishing open review work before opening
more, to keep branches from stacking conflicts. That one is about order and
this one is about duplication; they agree about what to look at and not
about why.

## Artifacts are the state

There is no manifest or state file. Orientation is derived entirely from
which artifacts exist in the run directory:

| Stage | Artifact | Complete when |
|-------|----------|---------------|
| Idea | `idea.md` | file exists |
| PRD | `prd.md` | file exists |
| UX Design | `ux.md` | file exists, **or** stage skipped (see below) |
| Architect | `architecture.md` | file exists |
| Decompose | `breakdown.md` | file exists |
| Implement | code | every checkbox in `breakdown.md` is checked (a breakdown with no checkboxes is not yet implemented) |
| Verify | `verification.md` | file exists |
| Review | `review.md` | file exists |
| Ship | `release.md` | file exists |
| Operate | `retro.md` | file exists (run complete) |

**Next stage = the first stage in order that is not complete.**

### The UX Design conditional

Whether UX Design applies is decided at PRD time and recorded in `prd.md`
frontmatter as `ux: required` or `ux: not-applicable` (it depends on the
feature, not the project). If `not-applicable`, the PRD also records a
one-line rationale as `ux-reason:`, orientation skips straight to Architect,
and the Architect skill echoes that recorded reason in `architecture.md`
frontmatter (e.g. `ux: skipped — no UI surface`) so absence is never
ambiguous downstream.

### Maintenance-run orientation

A maintenance run does not start at Idea. It enters at a **capture step**
whose seed artifact is `defect.md` — a defect brief (what is broken,
reproduction evidence, root-cause hypothesis, blast radius). For refactor or
dependency-upgrade work the same file is a *condition brief* (what is
degraded, evidence, target state); the filename stays `defect.md`.

Re-entry depth is decided at capture time and recorded in `defect.md`
frontmatter as `re-entry: implement` (scoped fix) or `re-entry: architect`
(design-touching), mirroring how `ux:` is decided at PRD time. Orientation
for a maintenance run is:

| Stage | Artifact | Complete when |
|-------|----------|---------------|
| Capture | `defect.md` | file exists |
| Architect | `architecture.md` | file exists — only when `re-entry: architect`, else skipped |
| Decompose | `breakdown.md` | file exists — only when `re-entry: architect`, else skipped |
| Implement | code | every checkbox in the run's breakdown is checked |
| Verify | `verification.md` | file exists — **never skippable**; the regression test is the point |
| Review | `review.md` | file exists |
| Ship | `release.md` | file exists |
| Operate | `retro.md` | file exists (run complete) |

**Where the breakdown lives:** with `re-entry: implement`, the breakdown is
inline in `defect.md` as checkboxes — no separate `breakdown.md`. With
`re-entry: architect`, the run uses the normal `architecture.md` +
`breakdown.md` chain, and checkboxes live in `breakdown.md`. There is no
third option.

### Tracker mirror (optional)

A run MAY mirror its work items to the project's issue tracker
(ADR-0026). The tracker is a mirror, never the state: orientation never
reads tracker state, and on a run without a tracker nothing changes.
Sync happens only at stage boundaries — import at run seeding or
Decompose drafting (existing tracker issues become work items recording
their originating issue references), export at Decompose (work items may
be published as tracker issues, mapping recorded in the breakdown), close
at Implement item boundaries (completing a work item closes its mirrored
issue).

The mirror is one-way **out**: nothing in the tracker starts a run. An
issue filed there — including one a sweep filed unattended, carrying
`source:sentry` / `type:defect` — is intake, and intake is never a work
order: a work order exists only once its breakdown row does, and the
dispatch plane never runs ahead of the knowledge plane (ADR-0032). A bug
therefore reaches a work order only after a person starts a run for it,
through `capture`.

**Tracker intake (ADR-0030).** A marked tracker issue may seed that
capture step — the one inbound door in the bound above, and it opens
only inside capture: seeding is not orientation, and nothing polls; an
unclaimed intake issue just waits. An issue carrying the project's
designated **intake marker** (the concrete marker — a tracker label —
and the tracker CLI live in packaging) is offered two user-initiated
ways: the user names the issue directly, or asks capture to list
intake-marked issues and picks one. Seeding copies into `defect.md` the
issue title as the working title, the filed date, and the body's
observed-behavior and reproduction content as interview raw material —
intake seeds the interview; it does not replace it. The issue itself is
recorded in frontmatter as `intake: #123` (the tracker's own notation;
duplicates of the same defect join an `intake-duplicates:` list and
close together) and is never re-read after seeding — from that moment
the tracker copy is a mirror again, updates flowing one way, out. The
intake issue closes at Ship, when `release.md` exists, with a closing
comment referencing the run directory; a run abandoned before then
un-marks the issue, never silently closes it. An intake-marked feature
request seeds nothing: a missing capability is a feature, and capture
routes it to `idea`, leaving the issue open.

A work item mirroring a tracker issue records the reference at the end of
its checkbox line, in exactly this form:

```markdown
- [ ] **<Item>** — <one line> (tracker: #123)
```

`#123` is the issue reference in the tracker's own notation. Items with
no mirrored issue carry no reference.

### Seed backlog (optional)

A target repo MAY keep a seed inbox at `docs/backlog.md` (ADR-0029).
The backlog is advisory, never the state: orientation never reads
backlog state, and on a repo without one nothing changes. It is not a
run artifact — it carries no frontmatter, never appears in the
orientation tables, and deleting it changes no orientation outcome.
Ordering is the prioritization: top of file = propose first. One line
per seed, in exactly these forms:

```markdown
- <seed text> (from: <run-ref>)
- <seed text> (from: <run-ref>) (claimed: <run-ref>)
```

`<run-ref>` is `product`, `feature:<slug>`, `maintenance:<slug>`, or
`session:<YYYY-MM-DD>` — the `session:` form covers a seed captured
mid-session with no run closing.

**Producers:** Operate appends its retro's idea seeds at run close
(creating the file if absent), and Capture may append a consciously
deferred defect. Producers append well-formed entries only and never
rewrite existing lines.

**Consumers:** `next` reads the backlog in exactly two moments — when
asked what's next with no active run, and at its completed-run step —
and never during active-run orientation. `idea` (or `capture`), when
starting a run from a seed, claims it in place by appending
`(claimed: <run-ref>)` to the seed's line — the origin marker is never
rewritten — and records the seed as the new run's origin. No other
skill reads the backlog.

## Soft gating

When your predecessor artifact is missing, never refuse and never silently
proceed. Name the gap, then offer:

1. **Backfill** — a short interview producing a minimal version of the
   missing artifact, then continue; or
2. **Proceed with assumptions** — continue now, logging every assumption in
   your own artifact's frontmatter under `assumptions:`.

`assumptions:` records any decision made without live user input — proceeding
past a missing predecessor (above), or taking a skill-recommended default for
a question the user never answered (e.g. an autorun brief gap). It is the
only place assumptions live.

## Run scale

Feature runs scale artifact depth to feature size — a feature PRD is a page,
not a book; a feature architecture note may be a paragraph. Product runs are
comprehensive. Maintenance runs scale further down: Review and Ship scale to
the blast radius recorded in the brief, but Verify never scales away. When
in doubt, ask the user how big this really is.

## Artifact frontmatter

Every artifact starts with YAML frontmatter:

```yaml
---
stage: prd
run: feature:dark-mode   # or: product, or maintenance:<slug>
date: 2026-07-01
# stage-specific fields, e.g. ux: required | not-applicable
#                          or re-entry: implement | architect (defect.md, at capture time)
# ux-reason: <one line>   when ux is not-applicable
# intake: #123            tracker issue that seeded defect.md (ADR-0030);
#                         duplicates of the same defect join intake-duplicates: [...]
# assumptions: [...]      any decision made without live user input
---
```

## Pull request body

A pull request body tells the reviewer at the merge gate (ADR-0033 gate 3)
what the merge risks, not only what the branch did. Traceability comes
first and is unchanged: the `Closes #N` line for the issue the change
closes, and either the work-order id the change implements or a
`No work order:` line giving the reason. Detector B checks those lines
alone; this section changes the body, not the check.

Below them, three parts:

1. **The smallest visual that shows the change** — pseudocode for a
   rule, a call tree for control flow, a file tree for layout, a diagram
   for interaction between parts, or a diff when the surrounding shape
   already exists and the point is what moved. One view that carries the
   point beats several that share it.
2. **Before-and-after evidence** — the failing output or test before and
   the passing one after, as it actually ran rather than as described. A
   screenshot when the change is visible; command output otherwise.
3. **The merge-danger call**, under this one fixed heading so the
   reviewer finds it without reading everything above it:

   ```markdown
   ## Merge danger

   Door: <one-way or two-way> — <why>
   Blast radius: <what breaks if the call is wrong>
   ```

   A two-way door is undone by a revert; a one-way door is not (a
   migration that drops data, a published version, a renamed public
   interface). The blast radius names who or what notices if the call is
   wrong — one consumer, every stamped repo, nobody until the next
   release.

The heading is the only fixed string; the visual and the evidence vary
with the change. Ship's rollback plan in `release.md` records the same
door and blast radius, so the two documents agree. Structure restated,
no text copied, from mattpocock/skills' `pr` skill (MIT, copyright Matt
Pocock) and the visuals menu of Dex Horthy's `show-me` (Humanlayer).

## Harness neutrality

Skill content must stay harness-neutral: plain process, file conventions, and
questions. Anything specific to one harness (Claude Code invocation
mechanics, plugin paths) belongs in packaging (README, manifests), not in
stage skill instructions.

This is not hypothetical: the skills run on two harnesses — Claude Code
(primary) and oh-my-pi/omp (ADR-0027) — from a single neutral body. Each
harness has its own packaging (`.claude-plugin/` manifests vs the root
`package.json` `pi.skills` entry); the stage instructions know about neither.

Operative hand-offs name the mechanism, never one harness's tool. The
router's step 5 tells the agent to load the stage skill through the
harness's skill-loading mechanism (a skill tool where one exists, otherwise
a read of the skill file), because naming a skill in prose does not load
it. The literal borrowing, "call the Skill tool with X" (mattpocock/skills),
was checked against omp on 2026-10-06 and adopted with neutral wording
instead: omp's `docs/skills.md` exposes skills to the model as on-demand
content read via its `read` tool against `skill://` paths, and its "Skills
vs custom tools" section separates skill content from model-callable tool
APIs, so omp has no skill tool and the literal wording fails one of the two
harnesses. The lesson (name the mechanism, not just the skill) survives as
the neutral sentence. This applies ADR-0027 rather than amending it; no new
ADR.
