---
stage: ship
run: maintenance:a-timestamp-the-digest-cannot-parse
date: 2026-09-22
assumptions:
  - "This is a prepare-and-stop dispatch (defect.md Constraints: 'Release authorization: prepare-and-stop... executes no externally visible release action... Merging an agent-authored PR needs separate human approval'). Ship's normal job — execute the release mechanism — does not apply here for a second, independent reason beyond the authorization constraint: there is no diff to release. This run's Implement stage added zero source/test/template/manifest/ADR content (breakdown.md's single checkbox, A1, is a re-confirmation, not a code change), because the gap defect.md was opened to close was already closed on main by two independently-seeded, already-merged, already-reviewed PRs (#326, #499) before this run's Architect stage re-entered. Ship's pre-flight and record-writing steps still apply in full; its release/post-release execution steps are inapplicable by construction, not skipped by choice."
  - "Per the dispatch's explicit instruction, this artifact departs from TEMPLATE.md's exact section labels where the standard shape (a Release log of commands executed, Post-release checks against a deployed surface) does not fit a run with nothing to deploy. The Pre-flight checklist, Rollback plan, and Outcome sections are kept as named; 'Release log' is replaced with 'What this run is shipping' and 'Release steps that would apply, and why none execute' to state honestly that no release action was taken, and 'Post-release checks' is replaced with a statement that no post-release check applies because nothing was deployed."
---

# Release: a timestamp the digest cannot parse — nothing to release, closure recorded

## Pre-flight

- [x] **Verification green (no unresolved failures).** `verification.md`
  (2026-09-22) marks all 7 of `defect.md`'s success criteria **PASS**,
  with zero failures and zero discrepancies. `review.md` (2026-09-22)
  independently re-checked the same claim against the shipped diffs
  themselves (not just prior stages' prose) and found the closure claim
  holds, with no critical/high/medium findings. This Ship stage re-ran
  the load-bearing checks a third time, fresh, right now, at HEAD
  `47b6937`:
  ```
  $ git merge-base --is-ancestor b6b365c HEAD && echo "b6b365c (PR #499) IS ancestor of HEAD"
  b6b365c (PR #499) IS ancestor of HEAD
  $ git merge-base --is-ancestor 9324d31 HEAD && echo "9324d31 (PR #326) IS ancestor of HEAD"
  9324d31 (PR #326) IS ancestor of HEAD

  $ python3 -m unittest discover tests
  Ran 1700 tests in 20.685s
  OK          (exit 0)

  $ python3 lint.py
  lint: 0 problem(s) across 25 skills

  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
  Every check that was green at Architect, Decompose, and Verify is still
  green now, at this stage's own re-run — the fourth independent
  confirmation across this run's later stages (the earlier three being
  Architect, Decompose, and Verify itself), plus Review's adversarial
  fifth pass. No drift since Verify.

- [x] **No secrets in diff; target config present.** There is no diff.
  `git status --short` at this stage shows exactly this run's own
  artifact footprint (`architecture.md`, `autorun-brief.md`,
  `breakdown.md` modified; `review.md`, `verification.md` new — now
  `release.md` too) plus the pre-existing, unrelated staged
  `.beads/issues.jsonl` change that predates this run and this run does
  not touch. No source, test, template, manifest, or config file is
  touched by this run, so there is no secret-scanning surface and no
  target-environment configuration this run introduces a dependency on.

- [x] **Migrations/data changes have a tested forward path.** N/A — no
  data model or schema change exists in this run (confirmed in
  `architecture.md`'s Data model section: "no storage, no schema, no
  persistence" for anything this run touches). The already-shipped fix
  (#326, #499) is pure in-process control flow (an admission-gate check
  plus a `problems`-list append); it introduced no migration when it
  shipped, and this run introduces nothing further.

- [x] **Rollback plan concrete.** See below — stated for completeness per
  the template's own requirement ("The rollback plan is always present,
  even when the release is small"), even though this run has nothing to
  roll back.

## What this run is shipping

**Nothing new.** This run's own artifact chain — `defect.md` through this
`release.md` — is the closure record, not a code change. The defect
`defect.md` was opened to fix (an uncaught `ValueError` when a gate
timeline event carries a truthy-but-non-ISO-8601 timestamp) is resolved on
`main` today, at HEAD `47b6937`, by two commits that predate this run's
own Implement stage:

- **PR #326** (`9324d31`, merged 2026-09-20) — made the timestamp check
  part of `human_gates`'s admission walk, so a malformed timestamp is
  refused rather than reaching an unguarded `datetime.fromisoformat`. This
  closed the crash.
- **PR #499** (`b6b365c`, merged 2026-09-21, closing issue #491) — added
  the `gd:`/`dashboard:`-prefixed problem-string reporting for a refused
  timestamp, so the crash's fix doesn't silently drop the event with no
  operator-visible signal. This closed the residual silent-drop gap.

Both are confirmed ancestors of `HEAD` by `git merge-base
--is-ancestor`, independently, by Architect, Decompose, Verify, Review,
and this Ship stage — five separate re-runs of the same ancestry check
across this run's later stages, none contradicted.

There is no branch for this run, no open PR, no commit authored by this
run's Implement stage, and no diff of any kind to release. Ship has
nothing to merge because there is nothing this run built.

## Release steps that would apply, and why none execute

Stated for completeness, per the ship skill's template, as the steps that
*would* govern getting a change like this into production, had this run
actually produced a diff:

1. **Open a PR from this run's work** — N/A, no branch or commit exists.
2. **Human review and merge authorization.** This repo's human-gate rules
   (ADR-0033, ADR-0036) require an agent-authored PR to receive a
   non-authoring human reviewer's approval before merge; `defect.md`'s own
   Constraints section restates this for this run specifically: "Merging
   an agent-authored PR needs separate human approval." Had this run
   produced a diff, this is the gate it would have to clear before any
   merge — and Ship would stop at "PR opened, awaiting human merge
   approval," not merge it itself.
3. **Merge to main** — N/A, gated on step 2, which is gated on step 1,
   which has no diff to start from.
4. **Template/manifest sync** (`python3 factory_init.py
   update-manifest`, committed with the change) — N/A here; this run adds
   nothing under `factory/templates/**` and touches no
   `factory_init.MIRRORS` root file. (For the record: the three payload
   twins this defect's fix touches — `human_gates.py`, `gate_digest.py`,
   `rejection_mining.py` — already match root, per #326/#499's own
   already-committed manifest sync; re-confirmed by this run's Verify and
   Review stages via clean `diff` and `gates: 0 problem(s)`.)
5. **Tag/version** — N/A; this repo's release convention for a maintenance
   fix is the merge commit itself, and there is no merge commit from this
   run.

**None of the above executes.** There is nothing to open, nothing to get
approved, nothing to merge, and nothing to tag, because this run produced
no diff. This is not a policy choice to hold back a ready release — it is
the simple fact that Ship has no release action available to perform.

## Rollback plan

```
N/A — nothing was deployed, merged, tagged, or published by this run.
There is no artifact of this run's own to roll back.

If a future run needed to undo the underlying fix this run is closing
against (#326 + #499), that is a statement about reverting THEIR merge
commits, not this run's — and is out of this run's authority and scope
regardless. For the record only: git revert b6b365c then git revert
9324d31 (in that order, newest first) would return human_gates.py,
gate_digest.py, and dashboard.py's reporting path to their pre-fix,
crash-on-malformed-timestamp behavior. Nothing in this run's own artifact
set (defect.md through this file) requires or requests that revert, and
this run took no action that revert would undo.
```

## No externally visible release action was taken

Explicit, for the record: **no deploy, publish, tag, or merge was executed
by this stage.** This satisfies `defect.md`'s prepare-and-stop
authorization by construction — there was nothing to release, not merely a
policy choice to withhold a ready release. The distinction matters: a
normal prepare-and-stop run would have a mergeable PR sitting ready,
withheld pending human approval. This run has no PR, no branch, and no
commit to withhold. The only file this stage wrote is this one
(`release.md`); `defect.md`, `architecture.md`, `breakdown.md`,
`verification.md`, `review.md`, `.beads/issues.jsonl`, and every
source/test/template/manifest file were left untouched.

## Post-release checks

**None apply.** Post-release checks smoke-test a deployed surface or a
published artifact against where users actually get it. This run deployed
nothing and published nothing, so there is no surface to smoke-check that
this run itself is responsible for. The underlying fix's own
post-release verification already happened, twice, under its own runs:
`docs/fixes/a-malformed-timestamp-is-silently-dropped/release.md` (PR
#499's own ship record) and the corresponding record for PR #326, each
against their own merges. This run adds no third check of the same
already-shipped, already-checked code — see `review.md`'s Findings
section, which notes one low-severity documentation nuance in that
already-shipped code (below) but nothing that changes its production
behavior.

## Known, already-recorded nuance (not this run's to act on)

`review.md`'s one finding (severity: low) is carried here for completeness,
not as an action item: `_admit`'s "one pass over the raw timeline" framing
(PR #499's own commit message and docstring) is true in the sense that
there is one *spelling* of the admission/refusal walk — a real
`one_owner.py` win — but each call site (`gate_digest._timelines`,
`dashboard._timeline`) that wants both the admitted list and the refused
count still invokes `_admit` twice (once via `label_events`, once via
`refused_timestamps`), not once. This is a documentation-vs-implementation
gap in already-shipped, already-reviewed code (PR #499), immaterial in
cost for a GitHub issue timeline fetched and walked once per issue per
daily run, and changes no output. `review.md` explicitly scoped this as
"not fixed, not this run's to fix" — Review reports, it doesn't patch, and
this run's own scope was verification and closure, not code. Ship makes no
different call: nothing above changes readiness, and nothing here is a
release blocker.

## Outcome

**Shipped cleanly — because there was nothing left to ship.** The
underlying defect is resolved on `main` today, verified independently five
times over this run's own lifecycle (Architect, Decompose, Verify, Review,
and this Ship stage's own pre-flight re-run), each re-running the ancestry
check and the full test/lint/gates battery fresh rather than trusting the
prior stage's prose. This run's contribution is the closure record itself
(`defect.md` through this file), not a code change. No externally visible
release action — no deploy, no publish, no tag, no merge — was taken by
this stage, satisfying `defect.md`'s prepare-and-stop constraint by
construction. Next stage is Operate.
