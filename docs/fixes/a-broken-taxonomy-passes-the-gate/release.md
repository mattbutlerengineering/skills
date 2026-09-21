---
stage: ship
run: maintenance:a-broken-taxonomy-passes-the-gate
date: 2026-08-30
---

# Release — a broken taxonomy passes the gate

**Prepared, not executed.** The brief authorizes no release action. This
records readiness and the exact remaining steps.

## Pre-flight

- **Verification is green.** `verification.md` records eight sections,
  all PASS, with the not-verified list stated. Battery on this branch:
  `lint: 0 problem(s) across 24 skills`, `gates: 0 problem(s)`,
  `selftest: ok`, `Ran 1350 tests ... OK` against a 1344 baseline on
  `origin/main` at `622e7c0`.
- **No unfixed critical review findings.** `review.md` records none;
  two minors accepted with reasons, one deferred with a reason, two
  found and fixed inside the run.
- **No secrets in the diff.** The change touches two Python modules,
  their payload mirrors, the checksum manifest and two test suites. No
  token, credential, URL or environment variable is added.
- **No configuration required in any target environment.** Nothing new
  is read from the environment and no workflow changed.
- **The payload mirror is regenerated, not hand-edited.**
  `python3 factory_init.py update-manifest` → `factory-init: 0
  problem(s)`. Detector E (manifest↔payload) is green above;
  `tests/test_factory_init.py` (payload↔root) is inside the 1350.
- **ADR-0032 holds.** No issue was created before a breakdown row,
  because this run creates no work-order rows at all — it is a
  maintenance run with `re-entry: implement`.
- **Behaviour change is additive and stated.** Detector J gains
  problem strings it did not emit before. It emits them only for a
  taxonomy file that exists and cannot be read; every previously-silent
  and every previously-reported case is byte-identical, pinned by the
  four unchanged exact-string tests in `TestLabelWiring`.

## Blast radius

A repo that has been carrying a malformed `.github/labels.json` will
start failing `make check` on the first run after this lands. That is
the point of the change, and the message names the file and the fault.
This repo is not such a repo — `gates: 0 problem(s)` above — and neither
is a freshly stamped one (§1 of `verification.md`, the "(the stamped
taxonomy)" row).

## Rollback

```
git revert <merge-commit>
python3 factory_init.py update-manifest   # regenerate the manifest
python3 gates.py && python3 -m unittest discover tests
```

The revert is clean: `taxonomy_path` is additive and its only caller
outside `label_sync` is the reverted line in `check_label_wiring`, so
nothing is left dangling. The manifest step is needed because the
payload mirrors move with the revert.

## Remaining steps (a human's)

1. Review PR #NNN — **ADR-0036 clause 2 requires a non-authoring
   reviewer to re-execute the verification and record it on the PR.**
   Every commit here is agent-authored, so this run cannot satisfy it.
   The command to re-execute is `make check`, plus
   `python3 factory_init.py update-manifest && git diff --exit-code` to
   confirm the manifest is current.
2. Merge. This is a gate-1/2 human merge only if a reviewer judges it
   so; the diff touches no `docs/adr/**`, `prd.md`, `architecture.md`
   or `docs/design/**`, so ADR-0036 clause 3 does not force it.
3. Nothing to deploy, publish, or tag. The change ships with the repo.

## Post-release check (for whoever merges)

After the merge, one command in a fresh stamp settles it:

```
python3 factory_init.py stamp /tmp/probe && cd /tmp/probe \
  && python3 tools/factory/gates.py \
  && printf '{ not json' > .github/labels.json \
  && python3 tools/factory/gates.py; echo "exit=$?"
```

Expected: `gates: 0 problem(s)` then
`L: .github/labels.json is not valid JSON: ...` / `gates: 1 problem(s)`
/ `exit=1`. `/tmp/probe` needs a `.git` directory to stamp into.
