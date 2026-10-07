# Autorun brief — feature:codex-style-standards-enforcement

Collected 2026-09-20. Not an artifact: this file never counts toward
orientation or active-run discovery.

## Run

- Scale: feature. Slug: `codex-style-standards-enforcement`.
- **Fresh run**, seeded directly from GitHub issue #448 rather than a
  live interview or a `docs/backlog.md` seed. No live human was
  available to interview across idea/PRD/architect/decompose, so this
  run was driven end to end from the issue's own text — the issue
  already carries a Design and Acceptance section from its original bd
  authoring, which functions as a one-time brief in the sense
  `skills/autorun/SKILL.md` describes, even though the stage skills were
  followed directly (reading their process + `docs/pipeline-protocol.md`
  and producing the artifact in the documented shape) rather than
  dispatched through the Skill tool, which expects a live back-and-forth
  this session has no other party for.
- Scope boundary honored throughout: **idea → PRD → architecture →
  breakdown only.** No product code, no `docs/adr/**` file, no tracker
  mirror issue, no label, no merge. This file and the four stage
  artifacts are the entire diff outside verifying `gates.py`/`lint.py`
  stay green.

## The brief (issue #448, verbatim scope + design + acceptance)

> Adopt the implementable core of Cloudflare's engineering-standards
> workflow on top of what this repo already has. Already covered,
> do NOT rebuild: mechanical enforcement (gates.py detectors A-L, lint
> checkers incl. check_skill_recitals), decision records with
> machine-readable statuses (docs/adr/ + ADR_STATUS + detectors C/D),
> local-CLI parity with CI, and human ownership gates (ADR-0033/0036).
>
> 1. Normative-statement index — SHOULD/MUST statements from ADRs +
>    CLAUDE.md, JSON, stable slugs, source path, RFC 2119 level,
>    enforcement status.
> 2. Graduated enforcement — advisory (non-blocking) vs enforced
>    (blocking MUST); promotion is an explicit human decision.
> 3. Standards-aware review — review skill + factory reviewer charter
>    cite slugs and apply the blocking rule; architect/blueprint gate
>    runs the same index filtered to design-relevant statements.
> 4. Capture-report completeness — a checker for defect.md required
>    sections, scaled from the post's incident-report reviewer.
>
> Design: docs/standards.json, [{slug, statement, level, source,
> status, domain}]. Deterministic stdlib script, gate detector for
> index<->source drift (pattern of detector E). RFC 2119 keywords
> adopted going forward in new ADRs; back-fill only statements worth
> enforcing. No parallel docs tree (ADR-0004). New-shared-module bar
> applies. Out of scope: dashboards/AI-gateway plumbing, org-wide RFC
> process, linter-package distribution.
>
> Acceptance: (1) index with regen script; (2) gate detector on
> index<->source drift and MUST-statement-supersession; (3) review
> skill cites slugs, distinguishes advisory/enforced; (4) 3 real
> statements promoted enforced with prior-advisory evidence; (5)
> capture-completeness checker with problem strings + tests; (6)
> unittest/lint/gates stay green.

Full text (including the migration provenance note) was fetched live
via `gh issue view 448` and is reproduced in full inside `prd.md`'s
problem statement context and cited, never re-typed as if original.

## Self-answers (no live interviewer — logged here, not silently decided)

- **UX applicability.** `not-applicable` — every surface here is files
  (`docs/standards.json`), a CLI script, gate detectors, and charter/
  skill prose. Nothing a human looks at as a UI.
- **PRD id.** `PRD-0004` — the next free id; `LEDGER.md`/existing
  `docs/features/*/prd.md` frontmatter show `PRD-0001..0003` taken.
- **Detector letters.** `gates.py`'s `DETECTORS` table currently has
  `J` and `K` marked `unused`, but `J`'s docstring entry is already
  fully written (LABEL-WIRING) for unrelated in-flight work
  (`feat/first-live-dispatch`, WO-0039, unmerged at time of writing).
  Self-answered: skip `J`, claim `K` and `M` (`L` is already
  LABEL-SYNC). Logged as an assumption in architecture.md rather than
  silently colliding with someone else's reserved letter.
- **New ADRs.** The architect charter's convention is to write an ADR
  for every hard-to-reverse decision. Self-answered: **do not** author
  real numbered ADR files in this run. Minting a real `docs/adr/NNNN-*`
  file is itself a gate-2 blueprint action (ADR-0033) this brief has no
  human to approve, and inventing a placeholder number would trip
  detector C (dangling `ADR-####` token) the moment anyone else's ADR
  lands first. architecture.md documents the hard-to-reverse decisions
  inline instead (the same "No ADR — ... a one-line record suffices"
  pattern `first-live-dispatch`'s architecture.md used) and breakdown.md
  carries a work item to author the real ADR(s) once a human has
  actually approved the design — never a number invented ahead of that.
- **Tracker mirror.** Decompose's planner charter normally exports
  breakdown rows to mirrored GitHub issues (ADR-0032). Self-answered:
  **skip** the mirror in this run. ADR-0032's one-way rule and the
  planner charter both presume the blueprint already passed gate 2
  (human blueprint approval) before rows are dispatch-ready; this run's
  architecture.md has not been through that gate yet. Creating mirror
  issues for a design nobody has approved would let the dispatch plane
  run ahead of an unapproved blueprint — the exact ordering ADR-0032
  exists to prevent. breakdown.md notes this explicitly so it isn't
  mistaken for an oversight.
- **Statement extraction realism.** The issue's own text already
  concedes back-fill is non-exhaustive. Self-answered further: full
  NLP-free deterministic extraction of MUST/SHOULD out of *existing*
  free-form ADR prose is not attempted — architecture.md scopes
  extraction to a new, explicit `## Normative statements` section
  convention for ADRs going forward, with existing ADRs back-filled by
  hand only where a statement is judged worth enforcing (mirrors the
  issue's own "back-fill only statements worth enforcing, not
  exhaustively").
- **Acceptance criterion 4 (3 real advisory→enforced promotions).**
  Cannot be honestly satisfied inside this same implementation pass —
  there is no advisory-period history before the index exists on day
  one (fabricating "previously flagged" evidence is exactly what
  eval-honesty/CLAUDE.md forbids). Self-answered: **flagged as needing
  a human decision**, not silently dropped or silently faked — see
  breakdown.md's Milestone for the exact item and the two options
  named there.

## Standing instructions followed across the four stage passes

- `docs/pipeline-protocol.md` was read in full before writing anything
  (run discovery, artifact frontmatter, soft-gating, the in-flight
  check).
- The in-flight check ran for real (`gh pr list`/`gh issue list`/
  `git branch -a` — see idea.md's frontmatter `assumptions:`), not
  skipped and not reported as clean without running.
- 1-2 existing completed/near-complete feature runs
  (`docs/features/first-live-dispatch/`, itself idea→breakdown only,
  and `docs/features/software-factory/`) were read in full before
  drafting, for section shape, tone, and frontmatter — this run does
  not invent a new schema.
- Every stray `WO-####`/`PRD-####`/`ADR-####` token this run's prose
  might otherwise have pasted from an unrelated example was checked
  against `gates.py`'s detector C (LINK-INTEGRITY) contract before
  writing it down; `python3 gates.py` was re-run after writing every
  artifact, not only before.
- No `wo:*` label, no tracker mirror issue, no `docs/adr/**` file, no
  merge — this run's only output is the four artifacts plus this brief.

## Resume — 2026-09-28 (Verify → Review → Ship)

Resumed by `/idea-to-prod:autorun` invoked with no arguments and no live
interviewer. Gaps the original brief leaves for these stages, and how
each was closed:

- **Which run.** Run discovery found many active runs, so the protocol
  says to ask. No one was available to ask. This run was chosen because
  it is the only active run with an autorun brief whose next stage needs
  no human action. Every breakdown row is checked (WO-0064 closed by the
  owner's 2026-09-28 deferral). `first-live-dispatch`'s open failure
  needs a human to apply gate labels. `factory-evolution-v1` has no
  brief and its open rows need live routine triggers. Every shipped
  maintenance run waits only on Operate, which autorun does not drive.
- **Stages covered.** Verify, Review, Ship. Operate is out of scope
  because no post-release feedback exists yet.
- **Release authorization: none.** The original brief forbade merges
  and says nothing about releasing. Ship therefore prepares and stops.
  No merge, tag, push, deploy, or published plugin version bump.
- **Tracker.** The original brief skipped the mirror. No tracker
  interaction in this resume either (WO-0064's issue #518 is read-only
  context).
- **Where the work lives.** Worktree branch
  `docs/standards-448-verify-review-ship` off `origin/main` at 6742c9f.
  Nothing is committed or pushed (the repo's conservative git profile).
