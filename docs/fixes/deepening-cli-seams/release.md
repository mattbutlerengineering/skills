---
stage: ship
run: maintenance:deepening-cli-seams
date: 2026-08-13
assumptions:
  - "'production' for this repo is main: the plugin is vended from the repo and the factory payload is stamped into product repos from factory/templates. There is no deploy step and no version tag — the project has never tagged a release, so shipping is a squash merge to main plus a green gate there"
---

# Release: the deepening-cli-seams maintenance run (PR #253)

## Pre-flight

- [x] Verification green (no unresolved failures) — `verification.md` is
      9/9 PASS with two stated narrowings and an explicit "Not verified"
      section; `review.md` closed both of its majors before this stage and
      recorded three minors as deferred with reasons. No critical findings,
      none unfixed.
- [x] No secrets in diff; target config present — the diff is three tools,
      three test files, an ADR, a manifest and the run's own artifacts. No
      credentials, no new environment variables, no new external calls; the
      two tools' `gh` access still runs through injected runners.
- [x] Migrations/data changes have a tested forward path — none exist. No
      persisted shape changed: the cost ledger, the breakdown grammar and
      the manifest format are untouched. The only generated file is
      `factory/manifest.json`, regenerated with `factory_init.py
      update-manifest` and verified idempotent before the commit.
- [x] Rollback plan concrete — below.

## Rollback plan

The release is one squash commit on `main`, so the undo is one revert:

```
git revert 0881918                # the squash merge; no merge-parent flag needed
python3 factory_init.py update-manifest   # payload+manifest travel in the revert,
                                          # this only re-verifies idempotence
python3 -m unittest discover tests && python3 lint.py && python3 gates.py
git push origin main
gh issue reopen 254               # the tracking issue the PR auto-closed
```

Nothing else needs undoing: no tag was cut, no package published, no
deployment triggered, and no stamped product repo has been re-stamped from
the new payload. A revert restores `charter-replay`'s broken dispatch, so
the two beads follow-ups (`wo-bcs`, `wo-huv`) would stay open and correct
either way.

## Release log

1. `git checkout -b fix/deepening-cli-seams` → branched off `main` at
   `57635f6`. Branch-first rather than committing straight to `main`, so
   CI could gate the change.
2. `git add <14 paths>` + `git commit` → one atomic commit. Deliberately
   not split: `factory/manifest.json` pins both mirrored payload copies, so
   any split would leave an intermediate commit failing detector E.
3. `git push -u origin fix/deepening-cli-seams` → new branch pushed.
4. `gh pr create` → **PR #253** opened against `main`.
5. First CI run → **FAILED**, and correctly:

   ```
   B: PR body cites no work-order id
   B: PR body has no Closes #N link
   gates: 2 problem(s)
   ```

   Detector B reads the PR event payload, which is why `gates.py` was green
   locally through the whole run — CLAUDE.md documents this as the one
   detector that skips without a PR event. The local gate was never wrong;
   it was structurally blind here.
6. Resolving the two findings honestly:
   - **The WO citation.** This run's breakdown rows carry no WO id by
     design — a maintenance run with no PRD section to cite, logged in
     `breakdown.md`'s frontmatter assumptions. That is exactly what
     detector B's `No work order: <reason>` waiver exists for, so the body
     declares it with its reason rather than inventing an id.
   - **The Closes link.** No valid target existed: the only two open issues
     are #178 and #181, the permanent marker-bearing state issues that
     automation posts to and that must never be closed by a sweep or a PR.
     Opened **#254** as this run's tracking issue (the condition brief, the
     blast radius, the ruled-out list) and closed that.
7. `gh pr edit 253 --body-file …` → **failed**:
   `GraphQL: Projects (classic) is being deprecated … (repository.pullRequest.projectCards)`.
   Re-read the body and confirmed the edit had *not* applied — the command
   reports the error but leaves the body untouched, so a caller who trusts
   the exit path would ship a stale body. Re-applied via REST:
   `gh api repos/…/pulls/253 -X PATCH -F body=@…` → body updated.
8. Second CI run → **PASS**. The `pull_request` trigger list already
   carries `edited` for precisely this case (`validator.yml:14-19`: a
   re-run replays the payload it was dispatched with, stale body and all —
   issue #216), so the corrected body was genuinely re-checked rather than
   replayed.
9. `gh pr merge 253 --squash --delete-branch` → merged to `main` as
   **`0881918`**; branch deleted; **#254 auto-closed** by the Closes link.
10. Local `main` fast-forwarded to `0881918`; working tree clean.

## Post-release checks

- **The gate on merged `main`** (not on the branch):

  ```
  Ran 1107 tests in 15.137s
  OK
  lint: 0 problem(s) across 23 skills
  gates: 0 problem(s)
  selftest: ok
  ```

- **The defect this run fixed, driven on the shipped code.** The exact
  invocation that failed before is now the tool's own help — real
  argparse, no stub, and `--help` costs nothing:

  ```
  $ python3 factory.py charter-replay --help
  usage: factory.py [-h] [--cases CASES] [--model MODEL] [--timeout TIMEOUT]
                    [--only ONLY] [--transcripts TRANSCRIPTS] [--record]

  Replay golden fixture work orders against the role charters (on demand; a live
  replay costs money)
    ...
    --transcripts TRANSCRIPTS
                          score a recorded {case_id: transcript} JSON file
                          instead of running a model (no cost)
  [exit 0]
  ```

  Before the fix this printed `factory.py: error: unrecognized arguments:
  charter-replay` (exit 2), and `--transcripts` was refused outright as
  "takes no arguments."

- **The front door still indexes the verb** — `python3 factory.py help`
  lists `charter-replay  Charter regression suite: golden fixture work
  orders, replayed.`, read from the module's own docstring at print time.

- **Not smoke-checked:** a live stamped product repo. The payload copies
  are byte-verified against the root through `factory/manifest.json` and
  detector E is green on `main`, but no repo was stamped from the new
  payload in this release. Unchanged from the standing pins
  (`tests/test_factory_init.py`); named here so the gap is not read as
  coverage.

## Outcome

**Shipped with hiccups, all recorded above.** The change is on `main` at
`0881918` with a green gate there and the fixed verb demonstrated on the
shipped code.

Two things the next release should inherit rather than rediscover:

1. **`gh pr edit` is unusable on this repo** — it dies on the Projects
   (classic) deprecation and leaves the body unchanged while reporting an
   error that reads like a warning. Use
   `gh api repos/<owner>/<repo>/pulls/<n> -X PATCH -F body=@<file>`, then
   re-read the body to confirm.
2. **Detector B cannot be pre-flighted locally.** Any PR from this repo
   needs its `Closes #N` target decided *before* the PR opens, and #178 /
   #181 are never that target.

Scope shipped is narrower than `architecture.md` designed, and the ship
note says so rather than burying it: the front-door decision landed in full,
and one of five gh-listing window-policy declarations. The other four and
two companion ADRs are `wo-huv`; the unreachable-remedy minor is `wo-bcs`.
