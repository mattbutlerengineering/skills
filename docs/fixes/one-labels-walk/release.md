---
stage: ship
run: maintenance:one-labels-walk
date: 2026-08-24
assumptions:
  - "Prepare-and-stop. autorun-brief.md authorises no release, so this stage runs the pre-flight, opens the PR and stops — no merge, no tag, no publish. ADR-0036 clause 2 independently forbids the author merging: a non-authoring reviewer must re-execute the verification and record it on the PR. Clause 3 does NOT apply here — this run adds no ADR and edits no ADR status line."
  - "Scale: a scoped fold, so the pre-flight is the four checks below rather than a full release rehearsal (the protocol's Run scale section). The rollback plan is present regardless, and is one command with no regeneration step — which is itself a consequence of the run touching no mirrored file."
---

# Release: prepared, not executed — PR #335

Branch `agent/issue-334-one-labels-walk`, six commits off `main`
(`486d476`, `48940c8`, `45f4b43`, `f79410e`, `87b3b9a`, `b17d3d1`, plus
this artifact). PR:
https://github.com/mattbutlerengineering/skills/pull/335

## Pre-flight

### Verification is green

`verification.md` records 11 criteria, 11 PASS, 0 FAIL.

```
$ python3 -m unittest discover tests
Ran 1355 tests in 16.080s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

The free review pre-pass, which is what asked for this run in the first
place:

```
$ python3 one_owner.py | tail -1
one-owner: 8 problem(s)
```

### No secrets in the diff; no configuration needed

```
$ git diff main..HEAD | grep -inE "(secret|token|password|api[_-]?key|BEGIN [A-Z ]*PRIVATE KEY)\s*[:=]\s*['\"][^'\"]{8,}"
(no matches)
```

The change adds no environment variable, no credential and no new
external call. It removes a hand-rolled walk and adds an import.

### No migration, no data change — and no manifest

```
$ git diff --stat main..HEAD -- factory/
(no output)
```

`plane_drift.py` is not a `factory_init.MIRRORS` entry (ADR-0060: neither
of its callers ships) and `cli.py` was not edited, so there is no payload
twin to regenerate and no manifest line to conflict with. Seven other PRs
are open against `factory/manifest.json`; this one adds no eighth.

### CI on the PR

```
$ gh pr checks 335
check	pass	19s
needs-review-label	pass	7s
review	pass	29s
merged-label	skipping	0
$ gh pr view 335 --json mergeable,mergeStateStatus
MERGEABLE	CLEAN
```

## Release steps — NOT executed

The release mechanism for this repo is a squash merge to `main`. What a
reviewer runs, in order:

1. Re-execute the verification on the branch (ADR-0036 clause 2): the
   three battery commands above, plus `python3 one_owner.py` (expect
   `one-owner: 8 problem(s)` — nine on `main`).
2. Record that re-execution as a comment on PR #335.
3. `gh pr merge 335 --squash --delete-branch`.
4. Watch the post-merge `merged-label` job on `main`. It is expected to
   **skip**: the PR body claims no work order.
5. Nothing to publish. `.claude-plugin/plugin.json` is untouched, so no
   version bump and no marketplace refresh.

**Not done here, deliberately.** The author may not merge this.

## Rollback plan

One command, and — unusually for this repo — no regeneration step:

```
git revert <squash-merge-sha>
```

The revert restores the hand-rolled walk, drops the `from cli import
label_names` line, restores the old module docstring and removes eleven
tests. No `python3 factory_init.py update-manifest` is needed, because
no `factory_init.MIRRORS` entry changed — the manifest, the payload twin
and `cli.py` are all byte-identical across this run, so nothing on `main`
goes red and no stamped repo is affected either way.

The blast radius of a revert is small and known: `one_owner.py` returns
to nine standing groups, and `tests/test_one_owner.py`'s two headers
return to calling the miss-3 group open.

## The claim, stated exactly — review F1

**One owner for the labels-array *walk*.** Extraction has one owner now.
The `wo:` **filter** does not: `dashboard.py:252-255` applies it to the
same payload, and the two sites already disagree about an issue carrying
two lifecycle labels — `issue_lifecycle` returns both sorted, which is
what lets `reconcile_drift` report the state-machine violation, while the
dashboard takes the first in payload order and strips the prefix.
`next(iter(issue_lifecycle(issue)), None)` is therefore **not** a
behaviour-preserving substitution, and folding it needs a decision about
which order is right. Out of scope by `autorun-brief.md`, deferred by
`review.md`, and written here so the commit subject is never read wider
than it is true.

## What is NOT shipped

- **The eight remaining one-owner groups.** Out of scope; each is its own
  seed per `docs/backlog.md:53`.
- **The `wo:` filter fold** — F1 above.

## Owed to Operate

This run stops at Ship, so the following are recorded here as debt rather
than appended to `docs/backlog.md`:

- **F1** — `dashboard.py:252-255` retypes the `wo:` filter, and folding it
  is a behaviour decision rather than a substitution. Worth a seed that
  states the decision, not just the duplication.
- **`one_owner.py` could not see F1**, and a grep in the file being
  edited could. That is a live instance of the re-implementation class
  `tests/test_one_owner.py` pins as a known miss, found four days after
  the run that built the pass — worth recording as evidence, since
  `docs/backlog.md:59` says the pass's central claim is untested in use
  and names exactly this shape as the negative case.
- **The purity clarification is unconfirmed.** The module docstring now
  says purity here is about runners and I/O rather than the import graph.
  Nobody who wrote ADR-0060 has agreed to that reading.

## Human decisions waiting

- **Merge or reject PR #335** (ADR-0036 clause 2).
- **Nothing else.** This run files no ADR and moves no ADR status line,
  so it adds no confirmation debt to the six provisional ADRs
  `docs/backlog.md:47` already complains about.
