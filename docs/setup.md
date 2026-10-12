# Setting up a repo

What it takes to initialize this pipeline in a repo and confirm it actually
works. Repo-agnostic — nothing here is specific to one project.

Two halves, and the first works alone: the **skills** are a plugin install and
need nothing else, while the **factory** (offline gates, dispatch workflows,
cost ledger) is stamped into a repo that wants to run work orders there. A
repo that installs the plugin and stops is a legitimate, complete setup.

Unattended dispatch is deliberately left off. See the last section.

## 1. Install the plugin

The three harnesses are covered in the [README](../README.md#install). Any of
them works on a bare install — no third-party tools, MCP servers, or other
plugins.

- [ ] Plugin installed
- [ ] `/next` resolves (Claude Code or Grok) or `/skill:next` (omp). On Grok
      a colliding name is `/idea-to-prod:next`.

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

A repo with curated files of its own can opt in instead (#701):

```
python3 factory_init.py stamp --keep-existing <path-to-target-repo>
```

It keeps the target's own copy of every curated, non-executable seed already
there (`.github/CODEOWNERS`, `.github/factory.json`, `.github/labels.json`,
the `docs/adr/` and `docs/design/` seeds) and prints one
`factory-init: kept <path>` line per file. It still refuses any collision in
the executable payload (`tools/factory/`, `.github/workflows/`, the `factory/`
mirror, the `Makefile`) and never overwrites. Kept files are yours, so the
checks in section 4 apply to them as they stand: a kept `labels.json` must
carry the labels detector J names, and a kept `CODEOWNERS` needs the factory's
gate paths added by hand.

91 files land: the 45-file payload installed to its destinations, plus the
pristine mirror it was stamped from. `factory/manifest.json` is the authority.

| Group | Count | What |
|-------|-------|------|
| `factory/` | 46 | the manifest and the pristine mirror the stamped detectors check themselves against |
| `tools/factory/` | 25 | the detector suite, the tools the workflows call, and the Conductor's batch tool |
| `docs/adr/` | 8 | the seeded ADR set, the convention, and the template |
| `.github/workflows/` | 6 | validator, assembler, design, cost-report, gate-digest, toolsmith-mine |
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
a **deletion**. The tools name 13 of these labels between them — `assembler`
reads `wo:ready-for-agent`, `budget-exhausted` and the four `type:` labels,
the three human gates name five `wo:` labels, each Makefile lifecycle target
flips one — and a pruned label fails when CI goes to flip it, at dispatch or
merge time. Detector J catches that offline instead, in `make check`.
Adding labels is always safe; a label nothing names is never a finding.

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

## 8. Project knowledge and reference files (optional)

Two utility skills keep project-level files outside any run. Neither needs
the factory stamp.

- **Knowledge base** — `/knowledge-base` sets up `docs/kb/`: pages hold
  only what the code doesn't tell an agent (invariants, gotchas,
  cross-module flows, the why with its ADR). Its tool `kb.py` writes a
  compressed index of page summaries inline into `CLAUDE.md` or
  `AGENTS.md` between managed markers, so every session sees it (ADR-0078).
  Ingest proposes page edits and a human promotes them. On this repo the
  first paired test showed equal pass rates and roughly half the turns and
  cost on tasks where the agent had to dig
  (`docs/research/knowledge-base-ablation.md`); the index line alone did
  not make an agent open a page for a task that didn't look like it needed
  one, so a hard "do not" rule belongs in `CLAUDE.md` itself.
- **UX patterns** — `/ux-patterns` derives `docs/ux-patterns.md` from the
  code (behaviour rules: loading, errors, empty states, undo, focus);
  `/ux-writing` owns its `## Voice & terms` section; `polish` and
  `ux-design` read it (ADR-0079).

- [ ] `python3 <plugin>/kb.py lint` prints `kb: 0 problem(s)` once
      `docs/kb/` exists
- [ ] The generated block in `CLAUDE.md` stays under its 2 KB budget

## 9. Monorepos

One pipeline root per repository: the repo root's `docs/`. Run discovery,
the gate queue, the cost ledger and the factory stamp are all per repo,
which is how GitHub labels, branch rules and CI already work, so a
monorepo needs conventions rather than different tooling.

- **Runs name their package.** Use the package as the slug prefix —
  `docs/features/<package>-<slug>/`, `docs/fixes/<package>-<slug>/` — and
  say in the idea brief or defect brief which package paths are in scope.
  A change that spans packages is one run, not one per package.
- **One knowledge base at the root.** Pages cite package paths in
  `sources:`, so staleness is still checked per file; one index keeps the
  always-loaded cost fixed however many packages there are.
- **Scoped context in nested `CLAUDE.md` files.** Put package-specific
  commands and "do not" rules in `<package>/CLAUDE.md`; Claude Code loads
  it when work touches that package, on top of the root file.
- **One stamp, one `make check`.** Stamp the factory once at the root; if
  packages have their own test commands, call them from the root
  `Makefile`'s `check` target rather than stamping per package.
- **ADRs at the root**, numbered once for the whole repo (see the
  protocol's "When to write an ADR").

Per-package pipeline roots (a `docs/` inside each package) are not
supported; run discovery would not find them.

- [ ] Run slugs carry the package prefix
- [ ] Package-specific rules live in nested `CLAUDE.md` files

## The Conductor (batches of issues)

Coordinating several issues at once — fanning out agents, choosing a
model and effort per step, ordering merges — is the `conduct` utility
skill and its root tool `conductor.py` (PRD-0013,
`docs/features/orchestrator/`). The payload ships it, so a stamped repo
runs `tools/factory/conductor.py`, passing this plugin's charter stubs
with `--agents` (#678). Its optional `conductor` table in
`.github/factory.json` names the repo's gate command, the
standing-consent policy, and `type_labels`: a map from the repo's own
issue labels to `feature` or `fix` (#700). Without that map an issue
plans by its first `type:` label. With it, only mapped labels count, and
an issue whose labels map to both types is deferred rather than
guessed. Detector F checks the table. `work-queue` still
fans out ready work orders through one stage, and `autorun` still drives
one run end to end. One step needs no Conductor: turn on the merge queue
ADR-0070 already chose, if the repo's plan allows it; the merge turn uses
it when present.

## Deliberately not in scope

Unattended dispatch stays off until explicitly opted into:

- `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN` both unset → the
  assembler's agent step skips gracefully (either credential runs it);
  nothing is dispatched and nothing is faked.
- `wo:ready-for-agent` is inert unless applied by the repo owner — enforced by
  an actor check, not by convention.
- `sweeps.yml` is factory-repo-only and is **not** stamped, so a product repo
  gets no Sentry intake, no label-drift sweep, and no cross-plane reconcile.
  Those stay here.
- The payload ships `assembler.yml` + `assembler.py` but **no charter tree**
  (`factory/agents/`, `factory/charters/` stay here), so a stamped repo's
  dispatch fails closed at the charter lookup even with every secret set.
  Stamped-repo dispatch needs charters authored for that repo — a deliberate
  deferral, recorded in ADR-0055.
