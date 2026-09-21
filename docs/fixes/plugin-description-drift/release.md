---
stage: ship
run: maintenance:plugin-description-drift
date: 2026-08-23
assumptions: ["The brief granted no release authorization, so Ship prepares and stops: branch, commit, push, issue and PR are how this repo records work and are not externally visible releases, but no merge and no tag were executed", "Scale follows the defect brief's blast radius — user-facing discovery only, no runtime effect — so pre-flight is the scoped-fix form, not the full refactor form"]
---

# Release: maintenance:plugin-description-drift

Prepared and stopped. **Nothing was merged and nothing was tagged.**

## Pre-flight

| Check | Result |
|---|---|
| Verification green | `verification.md` — 7 of 7, 0 FAIL, no unresolved failures |
| No unfixed critical review findings | `review.md` — 0 criticals; 3 fixed before Ship, 3 deferred with reasons |
| No secrets in the diff | Scanned; see below |
| Required configuration present | None needed — no config, no env var, no credential |
| Migrations / data changes | None — no schema, no stored state, no generated file outside `docs/` |
| Mirrored files touched | None, so no `update-manifest` step |
| Rollback plan | Concrete, below |

The secret scan matched three lines, all the identifier `SLUG_TOKEN`
matching on the substring `token`:

```
31:+# "interactive-architecture-diagram" is one token and never also counts
33:+SLUG_TOKEN = re.compile(r"[a-z][a-z0-9-]*")
68:+    named = set(SLUG_TOKEN.findall(data.get("description") or ""))
```

No credential material. Recorded rather than silently dismissed, because
a scan reported clean without saying what it matched is worth less than
one that shows its hits.

Mirror check, run rather than assumed:

```
  MIRRORS entries touched: none — no manifest regeneration required
```

## Release log — what actually executed

Each step, in order, with its result.

1. `gh issue create` → **#323**.
2. `git checkout -b agent/issue-323-plugin-description-drift` → created.
3. `git add` (five explicit paths plus the run directory) and `git commit`
   → `dfcb5a0`, 8 files, 591 insertions, 5 deletions.
4. `git push -u origin agent/issue-323-plugin-description-drift` → new
   remote branch, tracking set.
5. `gh pr create --base main` → **#324**, carrying the detector-B waiver
   (`No work order:` + a reason) and `Closes #323`.
6. CI watch armed on #324.

No step failed and no step was retried. Nothing was merged, tagged,
published or deployed.

## Deliberately not executed

- **Merge.** ADR-0036 clause 2 requires a non-authoring reviewer to
  re-execute verification and record it on the PR. This run authored the
  change, so it cannot be that reviewer. Clause 3 does not apply — the
  diff touches no `docs/adr/**`, no `prd.md`, no `architecture.md` and no
  `docs/design/**` — but clause 2 alone is sufficient to stop here.
- **Tag / version bump.** `plugin.json`'s `version` is untouched at
  `0.1.0`. The description is not a versioned interface and the brief
  authorized no release.

## Rollback plan

Concrete commands, not "revert if needed".

Before merge — close the PR and delete the branch; nothing on `main`
changed:

```
gh pr close 324 --delete-branch
gh issue close 323 --reason "not planned"
```

After merge, if the checker proves too strict in practice:

```
git revert -m 1 <merge-sha>
python3 -m unittest discover tests && python3 lint.py && python3 gates.py
```

The revert is clean and self-contained: `lint.py`, `tests/test_lint.py`
and `plugin.json` only, no mirrored payload and no manifest checksum, so
nothing else has to be regenerated to make the tree consistent again.

A narrower undo, if only the checker is unwanted but the corrected
description should stay, is to drop `check_plugin_skills` from `CHECKERS`
— one line, leaving the description correct and unguarded, which is the
pre-run state with the drift already repaired.

## Post-release check

Not applicable in the usual sense: nothing is deployed and no package is
published, so there is no shipped surface to smoke-test. The equivalent
evidence is that the guard runs where users of this repo will meet it —
CI on #324 — and that watch is armed.

It landed while this file was being written:

```
check: pass
check: pass
needs-review-label: pass
review: pass
PR #324 CI COMPLETE — 4 pass, 4 skipping
```

`needs-review-label` passing is the detector-B traceability leg accepting
the `No work order:` waiver; `merged-label` skipping is correct for an
unmerged PR. The guard therefore runs green where users of this repo meet
it, on a tree that carries the corrected description.

## Hand-off

Next stage is Operate, and it should **wait**. Nothing is merged, so
there is no usage and no feedback to capture; a retro written now would
record hopes. Operate also owns two seeds this run promised and did not
write, both from `review.md`:

- **F4** — a `plugin.json` that parses but is not a JSON object raises
  `AttributeError` from `check_manifest` rather than returning a problem
  string.
- **F6** — `check_readme_skills` carries the same substring blind spot F1
  fixed here, so README.md can silently drop `architecture-diagram`.

They are recorded in `review.md` with their reproductions, so nothing is
lost if Operate is delayed; the backlog entry is a discovery convenience,
and appending it is Operate's job, not Ship's.
