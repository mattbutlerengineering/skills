---
stage: ship
run: maintenance:a-program-lives-in-the-workflow
date: 2026-08-30
---

# Release — a program lives in the workflow

**Prepared and stopped.** No externally visible release action was
executed: no merge, no tag, no deploy. The brief authorized none, and
ADR-0036 clause 2 requires a non-authoring reviewer to re-execute
verification on the PR — this run authored the change, so it cannot be
that reviewer.

## Pre-flight

| Check | Result |
| --- | --- |
| `verification.md` has no unresolved failures | Yes — eight sections, all green |
| Review's critical findings fixed | No criticals; the one major was fixed and the battery re-run |
| No secrets in the diff | Yes — no token is read, logged or written; `gh` runs through the injected seam |
| Configuration exists in the target environment | Nothing new. The step already had `GH_TOKEN` and `PR`; the target adds no variable a stamped repo must set |
| Migrations / data changes | None |
| Rollback plan | Below, concrete |

The one environment fact worth stating: `make pr-event` runs after
`actions/checkout@v4` and `actions/setup-python@v5` in all three jobs, so
`make`, `python3` and the repo tree are all present where the inline
program used to run. Verified by reading each of the three steps, not
assumed from the first.

## What ships

- `validator.py` gains `pr-event`, the writer that pairs with
  `cli.read_event` (ADR-0042).
- `Makefile` and its generated twin gain the `pr-event` target and the
  `PR` / `EVENT` variables.
- `.github/workflows/validator.yml` and its byte mirror drop three copies
  of an inline program for three calls to that target.
- Five statements of the workflow's command convention are corrected.
- `skills/doctor/SKILL.md` step 6 names the new target, so `doctor` stops
  reporting a complete target set on a stamped repo that is missing it.
  This was not foreseen — `tests/test_factory_init.py` caught it.
- Ten tests: nine in `TestPrEvent`, one counting test in
  `TestValidatorDispatchLockstep`.

## Rollback

The change is one commit on one branch, unmerged. To undo before merge,
close the PR and delete the branch. To undo after a merge:

```
git revert --no-edit <merge-sha>
python3 factory_init.py update-manifest
python3 lint.py && python3 gates.py && python3 gates.py --selftest
python3 -m unittest discover tests
```

The revert restores the three inline copies, which are self-contained
and need nothing else present. `update-manifest` is listed because
`factory/manifest.json` is checksum-pinned and a revert of the payload
files without regenerating it fails detector E — the one step a plain
revert does not cover.

## Not executed

- No merge. Every open PR on this repo is agent-authored; clause 2
  blocks all of them until a non-authoring reviewer re-executes
  verification.
- No `workflow_dispatch` run of `validator.yml` against a real PR. That
  path fires when the assembler triggers it for a PR the factory's own
  token opened, and triggering one by hand would be an externally
  visible action this run is not authorized to take. The two halves of
  the new step were each exercised locally instead
  (`verification.md` §3, §7).

## Carry-forward for whoever reviews this

1. **The behaviour claim to re-check is §3** — that the new target
   produces the same bytes as the program it replaces, modulo the
   trailing newline. Run it against any open PR of your own; it needs
   only a read.
2. **The regression evidence to re-check is §5** — revert one of the
   three steps to a hand-built copy and confirm the new count assertion
   fails while the old `assertIn` passes.
3. **Two seeds were appended to `docs/backlog.md`**, both about what this
   run deliberately did not touch: the five sibling workflows that repeat
   the old wording, and the absent check that would compare a workflow's
   stated convention against its own `run:` blocks.
