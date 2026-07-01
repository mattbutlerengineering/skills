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

**Run discovery:** candidate run directories are `docs/` plus every
`docs/features/*/`. A run is *complete* when `retro.md` exists; *active* when
it has at least one artifact and is not complete. If the user named a feature,
use (or create) its directory. If exactly one run is active, use it.
Otherwise, list the candidates and ask which one.

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
| Implement | code | every checkbox in `breakdown.md` is checked |
| Verify | `verification.md` | file exists |
| Review | `review.md` | file exists |
| Ship | `release.md` | file exists |
| Operate | `retro.md` | file exists (run complete) |

**Next stage = the first stage in order that is not complete.**

### The UX Design conditional

Whether UX Design applies is decided at PRD time and recorded in `prd.md`
frontmatter as `ux: required` or `ux: not-applicable` (it depends on the
feature, not the project). If `not-applicable`, orientation skips straight to
Architect, and the Architect skill echoes the skip in `architecture.md`
frontmatter (e.g. `ux: skipped — no UI surface`) so absence is never
ambiguous downstream.

## Soft gating

When your predecessor artifact is missing, never refuse and never silently
proceed. Name the gap, then offer:

1. **Backfill** — a short interview producing a minimal version of the
   missing artifact, then continue; or
2. **Proceed with assumptions** — continue now, logging every assumption in
   your own artifact's frontmatter under `assumptions:`.

## Run scale

Feature runs scale artifact depth to feature size — a feature PRD is a page,
not a book; a feature architecture note may be a paragraph. Product runs are
comprehensive. When in doubt, ask the user how big this really is.

## Artifact frontmatter

Every artifact starts with YAML frontmatter:

```yaml
---
stage: prd
run: feature:dark-mode   # or: product
date: 2026-07-01
# stage-specific fields, e.g. ux: required | not-applicable
# assumptions: [...]      when produced past a soft gate
---
```

## Harness neutrality

Skill content must stay harness-neutral: plain process, file conventions, and
questions. Anything specific to one harness (Claude Code invocation
mechanics, plugin paths) belongs in packaging (README, manifests), not in
stage skill instructions.
