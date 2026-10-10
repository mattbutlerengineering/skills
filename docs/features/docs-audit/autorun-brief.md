# Autorun brief: docs-audit

Collected 2026-10-10 from the owner, one question at a time. Seeded by
GitHub issue #616 ("Audit documentation": remove stale documentation, fix
inaccurate documentation, organize documentation). This brief is not an
artifact.

## Feature

Audit this repo's living reference documentation and leave it true,
current, and organized. The owner's issue text, verbatim: "Audit
documentation / Remove stale documentation / Fix inaccurate documentation
/ Organize documentation".

## Scale

Feature run, slug `docs-audit`, artifacts under `docs/features/docs-audit/`.
Branch `docs/docs-audit`, worktree `.claude/worktrees/docs-audit`. The
branch is STACKED on `feat/grok-harness` (PR #618, Grok as a supported
harness, ADR-0076), because that PR edits four in-scope docs (README,
CONTEXT, docs/setup.md, docs/pipeline-protocol.md). Audit the docs as they
read on this branch, Grok wording included; do not re-litigate ADR-0076.

## Idea-stage inputs (owner-confirmed draft)

- **Problem:** the living docs have drifted as 76 ADRs and roughly 60
  fix runs landed; a reader gets stale or wrong guidance and has to
  cross-check the code.
- **Who has it / how they cope:** the owner, a new contributor, and
  agents that auto-load CLAUDE.md / AGENTS.md. Today they cope by trusting
  ADRs and code over the docs.
- **Why now:** PRD-0008 just shipped a README skill map; the docs have
  never had a whole-set pass.
- **Evidence:** anecdotal only — the owner filed #616 (2026-10-10). Label
  it as anecdote. The audit's own findings become the hard evidence.
- **Rough solution shape (hunch):** inventory every claim the living docs
  make that the code can falsify (paths, commands, module names, counts,
  checker names, ADR statuses, skill rosters), check each against the
  tree, fix or remove what is false or stale, and dedupe passages that say
  the same thing in two docs down to one owner plus a link.
- **Success statement:** every checkable claim in the living docs is true
  of the code today, nothing stale remains, and each doc has one clear job.
- **Biggest unknowns / ways this dies:** "stale" is a judgement call on
  prose; a fix that silently changes a documented contract (the protocol
  is normative for the skills); duplicated passages that are deliberate
  (e.g. CLAUDE.md summarizing for agents); lint checks that pin exact
  README / CONTEXT text and break when prose moves; scope creep into ADRs
  or run artifacts.

## Scope

IN — the living reference docs only:
- Root: `README.md`, `CONTEXT.md`, `LEDGER.md`, `AGENTS.md`, `CLAUDE.md`
- `docs/setup.md`, `docs/pipeline-protocol.md`, `docs/output-evals.md`
- `docs/factory/*.md` (the four routine protocols)
- `evals/README.md`

OUT:
- ADR bodies under `docs/adr/` (supersede, never rewrite; any docs/adr PR
  is a human gate-2 merge, ADR-0036). A stale ADR claim found in passing
  is reported in the run artifacts as a follow-up, not edited.
- Run artifacts under `docs/features/**` and `docs/fixes/**` (historical
  records), and `docs/backlog.md` (append-only inbox).
- `skills/**/SKILL.md` (product behaviour, eval-covered) and anything
  under `factory/templates/**`.
- Eval definitions and `evals/results/` (append-only, eval honesty).

DECIDED:
- **In-place reorganization only:** reorder sections, merge duplicated
  passages into one owner plus a cross-link, add cross-links. No file
  moves, no renames, no deletion of whole doc files.
- `docs/pipeline-protocol.md` is normative: a correction that changes
  what a skill must do is a behaviour change — report it, don't make it.
  Corrections that make it describe what the code already does are fine.
- Every claim fixed must be checked against the tree (a command, a grep,
  a file read), and the evidence recorded — never fixed from memory.
- Stdlib only for any new or changed check.
- If an edited file is in `factory_init.MIRRORS`, run
  `python3 factory_init.py update-manifest` and commit the manifest.

## Tracker

Seeded by GitHub #616 only. No other tracker interaction; no beads
writes, no new GitHub issues. #616 is the PR's `Closes #616` anchor.

## User-facing surface

None interactive. Recommendation: `ux: not-applicable` — "static
documentation; no flows or screens". The PRD decides.

## Release authorization

Release is a squash merge to `main` (ADR-0033 gate 3). This run is
authorized to: push `docs/docs-audit` by name and open ONE non-draft pull
request with base `feat/grok-harness` (retarget to `main` after #618
merges), body per the protocol's "Pull request body" section, beginning
`Closes #616` and a `No work order:` line, with the `## Merge danger`
heading. Ship then STOPS: no merge, no tag, no version bump. The owner
reads the diff and merges.

## Standing instructions for every stage

Answer interview questions from this brief. Where it is silent and the
stage skill offers a recommended default, take it and log it under the
artifact's `assumptions:` frontmatter; where there is no default —
including every evidentiary question — stop and surface. Never fabricate
verification evidence: run the real commands (`python3 -m unittest
discover tests`, `python3 lint.py`, `python3 gates.py && python3 gates.py
--selftest`). Work only inside `.claude/worktrees/docs-audit`. Commit each
stage's artifact on the branch before handing back (Conventional Commits,
ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`).
Note: this shell is zsh — never name a variable `status`.
