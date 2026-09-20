---
stage: ship
run: maintenance:marker-diagnostics-that-lie
date: 2026-08-25
assumptions: ["Prepare-and-stop. autorun-brief.md authorises no release, so this stage runs the pre-flight, opens the PR and stops — no merge, no tag, no publish. ADR-0036 clause 2 independently forbids the author merging: a non-authoring reviewer must re-execute verification and record it on the PR.", "Scaled per the protocol's Run scale section as a scoped fix: one unmirrored module and its suite, so the pre-flight is the battery plus a secret scan plus the mirror check, not a full deployment rehearsal. The rollback plan is present anyway, as that section requires even for a small release."]
---

# Release: two marker diagnostics that state what is actually true

**PR:** https://github.com/mattbutlerengineering/skills/pull/337
**Issue:** #336
**Branch:** `agent/issue-336-marker-diagnostics`, eight commits on
`origin/main` (622e7c0).

## Pre-flight

### Verification is green

`verification.md` records six brief criteria and four breakdown acceptance
criteria, every one PASS, each with the literal output of the command that
settled it. No unresolved failures. Re-run at the branch tip:

```
Ran 1355 tests in 15.551s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
```

### No unfixed critical findings

`review.md` records five items: F1 (major), F2 and F3 (minor) fixed in this
run; F4 and F5 deferred with reasons. No criticals. Nothing blocks Ship.

### No secrets in the diff

```
$ git diff main...HEAD | grep -inE "(api[_-]?key|secret|token|password|bearer|BEGIN [A-Z ]*PRIVATE KEY)[\"'[:space:]]*[:=]"
(no matches)
```

The `token` hits that do exist are `tokenize` module attributes in
`_standalone_comments` and the pre-existing `WO_TOKEN` regex name, both
excluded explicitly rather than by a quiet filter.

### Configuration and mirroring

No configuration is required in any environment: this is a stdlib-only
review pre-pass invoked by hand. `one_owner.py` is not in
`factory_init.MIRRORS`, so no payload copy exists and no manifest
regenerates:

```
$ python3 -c "import factory_init; print(any('one_owner' in str(m) for m in factory_init.MIRRORS))"
False
```

Detector E has nothing to check here, and no eighth manifest conflict is
added to the open PRs.

### Migrations and data changes

None. The tool has no storage, no state file and no baseline — every
comparison is within a single read of a single working tree.

### The base was corrected before opening the PR

The branch had been cut from the tip of the still-open `one-labels-walk`
branch rather than from `main`, which would have stacked this PR on that
one and coupled their merge order. Rebased onto `origin/main` (622e7c0);
the seven commits replayed with no conflict, and every SHA-bound
measurement in `verification.md`, `review.md` and `breakdown.md` was
re-derived against the new base rather than left pointing at commits that
no longer exist. `defect.md` keeps what capture actually saw and carries a
dated note explaining the eight-versus-nine difference.

### CI on the PR

```
check                pass  21s
needs-review-label   pass   6s
review               pass  24s
merged-label         skipping
---
MERGEABLE CLEAN
```

`merged-label` skips because the PR is open, which is the leg's own
precondition. `needs-review-label` ran and passed: the body carries a
`No work order:` declaration and names no work-order id, so detector B is
satisfied by the waiver and the lifecycle leg has no queue entry to record.

## Rollback plan

Concrete, in order of what actually goes wrong:

1. **Before merge — nothing to undo.** Close PR #337 and delete the branch:
   `gh pr close 337 && git push origin --delete agent/issue-336-marker-diagnostics`.
   Nothing outside the branch has changed. The backlog seed's `(claimed: …)`
   suffix is on the branch, so it goes with it.
2. **After merge — revert the merge commit.**
   `git revert -m 1 <merge-sha> && git push`. The change is eight commits in
   two files plus artifacts; nothing depends on it, nothing imports
   `defined_names` outside `one_owner.py` and its suite, and `FactSite`
   never leaves the module.
3. **Partial rollback, if only one diagnostic is unwanted.**
   `git revert 81b268a` undoes the `_rent` split (M2) alone; `git revert
   7b7ad04` undoes the `attach` join (M1) alone. The two milestones share
   no code and no test, which is why they were cut apart.

No data migration to reverse, no deployment to roll back, no published
artifact to unpublish.

## Release

**Not executed.** `autorun-brief.md` grants no release authorization, so
this stage stops here by design.

The remaining steps, for whoever takes them:

1. A non-authoring reviewer re-executes `python3 -m unittest discover
   tests`, `python3 lint.py`, `python3 gates.py`, `python3 gates.py
   --selftest` and `python3 one_owner.py`, and records the output on PR
   #337 (ADR-0036 clause 2).
2. Squash-merge #337 into `main`.
3. Delete the branch.

There is no tag and no publish step: this repo vends skills as a plugin,
and nothing under `skills/` or `.claude-plugin/` changed.

## Post-release

Not applicable — nothing was released. The smoke check that would run after
a merge is `python3 one_owner.py` on `main`, expecting the same nine
findings and exit 1.

## Owed to Operate

This run appends nothing to `docs/backlog.md` — Ship is where autorun
stops, and the seeds below belong to a stage that has not run:

- **F4, `ast.AnnAssign`.** A module-level `NAME: int = 1` is invisible to
  both `defined_names` and `fact_sites`, so a marker naming one still gets
  "not defined in this repo". Zero instances across 28 root modules today.
  Closing it means teaching both readers about the node.
- **F5, the `<module>.<name>` grammar.** It cannot address a nested
  definition: `lint.py` binds `problems_for` three times and
  `charter_replay.py` binds `run` twice, all nested closures, and both
  readers collapse them to one identity. Pre-existing in `fact_sites`;
  inherited deliberately so `defined_names` stays a superset.
- **The two fixes are unreachable in this tree.** One decorated definition
  exists (`cli.py:170 harness_run`), carrying no marker, and no live marker
  names a non-fact counterpart. Both are verified on fixtures and a probe,
  which is the right depth — but the first real instance is what would
  actually settle whether the messages read well.
