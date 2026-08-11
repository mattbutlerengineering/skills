# Setting up a repo

What it takes to initialize this pipeline in a repo and confirm it actually
works. Repo-agnostic — nothing here is specific to one project.

Two halves, and the first works alone: the **skills** are a plugin install and
need nothing else, while the **factory** (offline gates, dispatch workflows,
cost ledger) is stamped into a repo that wants to run work orders there. A
repo that installs the plugin and stops is a legitimate, complete setup.

Unattended dispatch is deliberately left off. See the last section.

## 1. Install the plugin

Both harnesses are covered in the [README](../README.md#install). Either works
on a bare install — no third-party tools, MCP servers, or other plugins.

- [ ] Plugin installed
- [ ] `/next` resolves (Claude Code) or `/skill:next` (omp)

## 2. Verify the skills before touching CI

- [ ] `/next` on the target repo announces the right state. With no artifacts
      it routes to Idea (greenfield default) rather than guessing.
- [ ] A stage skill invoked directly (`/prd`, `/architect`) offers a backfill
      instead of blocking when its predecessor is missing (ADR-0005 soft
      gating).

`/doctor` checks both mechanically, and works at this point — before any
stamp — because it needs nothing but the installed plugin.

## 3. Stamp the factory payload

From a checkout of this repo:

```
python3 factory_init.py stamp <path-to-target-repo>
```

All-or-nothing. It refuses a drifted source payload, a malformed manifest key,
a destination resolving outside the target, and **any existing file** in the
target — one problem line per refusal, no partial stamps. That last refusal is
strict: a repo that already has `docs/adr/README.md` cannot be stamped without
moving the conflict out of the way first.

69 files land: the 34-file payload installed to its destinations, plus the
pristine mirror it was stamped from. `factory/manifest.json` is the authority.

| Group | Count | What |
|-------|-------|------|
| `factory/` | 35 | the manifest and the pristine mirror the stamped detectors check themselves against |
| `tools/factory/` | 15 | the detector suite and the tools the workflows call |
| `docs/adr/` | 8 | the seeded ADR set, the convention, and the template |
| `.github/workflows/` | 5 | validator, assembler, design, cost-report, gate-digest |
| `.github/` | 3 | `factory.json` (budgets, routing bands, WIP cap, monthly cap), `labels.json` (the 28-label taxonomy), `CODEOWNERS` (the code-owner gate) |
| `docs/design/` | 2 | the design-system seed and its template |
| `Makefile` | 1 | `make check` = detectors + selftest + tests, exactly what CI runs |

- [ ] Stamp exits clean
- [ ] Stamped files committed

## 4. Verify the stamp

- [ ] **A `tests/` directory exists.** The stamped `check` target runs
      `python3 -m unittest discover -q tests` and errors outright without one.
      A fresh stamp into a test-less repo fails its first gate with
      `ImportError: Start directory is not importable: 'tests'` — which reads
      like a broken tool and isn't.
- [ ] `make check` exits clean
- [ ] **`.github/CODEOWNERS` owner substituted.** The template ships a
      placeholder handle on four paths. If it is not a collaborator on the
      target, GitHub silently ignores the entry and the code-owner gate goes
      inert.
- [ ] `.github/factory.json` budgets and caps reviewed for this repo

Substituting the owner and tuning the budgets are *expected* edits — the gates
do not compare them against the payload. The executable half (`tools/factory/`
and `.github/workflows/`) is the opposite: never hand-edit it, and detector E
fails the build if you do. Change the template at the source and re-stamp.

`/doctor` covers this whole section.

### Taking a later factory change

A stamp is a snapshot. When the factory gains a fix, refresh the repo:

```
python3 factory_init.py update <path-to-target-repo>
```

It overwrites the executable half and the mirror, lands any payload file the
repo lacks, and leaves everything you were meant to edit alone — reporting
each kept file that differs so you can reconcile it deliberately. Read its
make-target line: the workflows are refreshed and call only `make` targets, so
a factory change that adds one leaves a Makefile that has never heard of it.

## 5. Sync the label taxonomy

The 28-label taxonomy backs the work-order lifecycle machine, the gate digest,
and the sweeps' triage:

```
python3 tools/factory/label_sync.py            # report drift
python3 tools/factory/label_sync.py --apply    # create/update drifted labels
```

Never deletes: labels the taxonomy doesn't name are left alone.

`.github/labels.json` is yours to curate, and the one edit to make carefully is
a **deletion**. The tools name 15 of these labels between them — `assembler`
reads `wo:ready-for-agent` and `budget-exhausted`, the digest counts the six
gate labels, each Makefile lifecycle target flips one — and a pruned label
fails when CI goes to flip it, at dispatch or merge time. Detector J catches
that offline instead, in `make check`. Adding labels is always safe; a label
nothing names is never a finding.

- [ ] Labels present on the remote
- [ ] Detector L reports no drift

## 6. Wire the gates

- [ ] Branch protection requires the `validator.yml` check
- [ ] Code-owner review required — the merged PR is the approval record
      (ADR-0033)
- [ ] PR bodies carry `Closes #N`, and either a `WO-####` id or an explicit
      `No work order: <reason>`. Detector B fails the build otherwise; it is
      how a merged PR names the one work order it implements

## 7. Choose a run scale (brownfield repos)

ADR-0028's `adopt` entry is still **provisional** — there is no `adopt` skill.
Until one lands, an existing codebase starts either with a feature run
(`docs/features/<slug>/`) or a maintenance run via `capture`
(`docs/fixes/<slug>/`). Do not fake an Idea-through-Ship product run for
software that already shipped.

- [ ] Run scale chosen deliberately (product / feature / maintenance)

## Deliberately not in scope

Unattended dispatch stays off until explicitly opted into:

- `ANTHROPIC_API_KEY` unset → the assembler's agent step skips gracefully;
  nothing is dispatched and nothing is faked.
- `wo:ready-for-agent` is inert unless applied by the repo owner — enforced by
  an actor check, not by convention.
- `sweeps.yml` is factory-repo-only and is **not** stamped, so a product repo
  gets no Sentry intake, no label-drift sweep, and no cross-plane reconcile.
  Those stay here.
