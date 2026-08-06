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
today through `capture`. ADR-0030's inbound leg would add an intake
convention; it is provisional and unimplemented, so this bound currently
holds without exception.

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
# assumptions: [...]      any decision made without live user input
---
```

## Harness neutrality

Skill content must stay harness-neutral: plain process, file conventions, and
questions. Anything specific to one harness (Claude Code invocation
mechanics, plugin paths) belongs in packaging (README, manifests), not in
stage skill instructions.

This is not hypothetical: the skills run on two harnesses — Claude Code
(primary) and oh-my-pi/omp (ADR-0027) — from a single neutral body. Each
harness has its own packaging (`.claude-plugin/` manifests vs the root
`package.json` `pi.skills` entry); the stage instructions know about neither.
