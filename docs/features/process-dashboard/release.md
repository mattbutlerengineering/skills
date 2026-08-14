---
stage: ship
run: feature:process-dashboard
date: 2026-08-14
assumptions:
  - "'production' for this repo is main (the deepening-cli-seams
    release's precedent): the console is an operator-level root tool,
    deliberately outside factory_init.MIRRORS, so shipping is the
    squash merges to main plus green gates there — no deploy, no
    package, no version tag (the project has never tagged)."
---

# Release: Process dashboard v1

## Pre-flight

- [x] Verification green — `verification.md` is 7/7 PASS, no
      unresolved failures; `review.md` says ready to ship with its one
      finding fixed in-stage and three minors deferred with reasons.
      No critical findings existed.
- [x] No secrets in diff — the run's diff is two root tools
      (`dashboard.py`, `dashboard.html`), a `protocol.py` accessor
      extension with its mirrored template + manifest, tests, and the
      run's own artifacts. No credentials, no new environment
      variables; gh/git access runs through the injected `cli.py`
      runners. Required configuration in the target environment:
      `~/.process-dashboard.json` does **not** yet exist on the
      operator's machine — deliberate: the page's "No repos
      configured" empty state points at it, and creating operator
      state unasked is not the tool's call. Onboarding is one file:
      `{"repos": ["/Users/mbutler/github/skills", ...]}`.
- [x] Migrations/data changes — none. No persisted shape changed: the
      ledger, breakdown grammar, and manifest format are untouched.
      `parse_backlog` entries gained a `line` key (additive; no
      caller pinned the old shape outside this repo's tests, and the
      mirrored payload copy shipped in the same commit, detector E
      green).
- [x] Rollback plan concrete — below.

## Rollback plan

The release is thirteen commits on `main` (eleven squash merges
#266–#276 plus the verification/fix/review commits), all additive, so
the undo is one ranged revert:

```
git revert --no-commit a593b0b^..0b58d0f
python3 factory_init.py update-manifest   # re-verifies idempotence; the
                                          # protocol.py revert carries its
                                          # own manifest+payload back
python3 -m unittest discover tests && python3 lint.py && python3 gates.py
git commit && git push origin main
gh issue reopen 255 256 257 258 259 260 261 262 263 264 265
```

The range deliberately includes a593b0b (WO-0019, the run's first
merge, from the prior session) and excludes 87b59eb (the idea-through-
breakdown docs — artifacts, harmless to keep). Nothing else needs
undoing: no tag, no package, no deployment, and the console is not in
the stamped payload, so no product repo is affected either way.

## Release log

The release happened incrementally across the Implement stage — each
work order shipped as its own gated squash merge, per this session's
standing authorization to merge green PRs:

1. PRs #266–#276 (WO-0019…WO-0029) squash-merged to `main`, each after
   `check`/`review`/`needs-review-label` all passed; mirror issues
   #255–#265 auto-closed by their `Closes` links. One CI-side hiccup
   worth recording: none of the eleven runs failed. Local hiccups the
   log owes the next release: WO-0027's first full-suite run showed
   one failure plus a detector-G finding — both the same intermediate
   state (row checked before its ledger row was appended), cleared by
   recording the row, not by changing any test.
2. Verify: `verification.md` at 9d0a71d, direct to main (stage
   artifacts follow 87b59eb's precedent; detector B's Closes-#N rule
   has no honest target for a docs-only artifact commit).
3. Review's fix: aea2754 (bind failures return problem strings; the
   traceback was reproduced live before fixing, two pinning tests
   added).
4. `review.md` at 0b58d0f. Push CI (validator) on the final state:
   success — `{"conclusion":"success","headSha":"0b58d0f..."}`.

## Post-release

Smoke check from `main` HEAD on the default port, observing this repo
— where the operator actually gets the work:

```
page: 200 text/html; charset=utf-8
repos: {"repos": [{"i": 0, "path": "/Users/mbutler/github/skills",
        "name": "skills"}]}
runs: [('feature:process-dashboard', 'ship'),
       ('feature:software-factory', 'implement'),
       ('maintenance:deepening-cli-seams', 'operate')]
output rows: 29 | drift: ['drift: WO-0018 row is unchecked but its
                          mirror #123 is closed']
problems: []
```

The console served its page, listed the configured set, and gathered
the live repo cleanly — reporting its own run at stage `ship` at the
moment of shipping. The standing drift finding it surfaces (WO-0018 /
#123, the software-factory run) is real cross-plane disagreement the
tool exists to catch, awaiting the operator's judgment.
