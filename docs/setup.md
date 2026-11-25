# Setting up a repo

What it takes to initialize this pipeline in a repo and confirm it actually
works. Repo-agnostic — nothing here is specific to one project.

Two halves, and the first works alone: the **skills** are a plugin install and
need nothing else, while the **factory** (offline gates, dispatch workflows,
cost ledger) is stamped into a repo that wants to run work orders there. A
repo that installs the plugin and stops is a legitimate, complete setup.

Unattended dispatch is deliberately left off. See the last section.

## 1. Install the plugin

The harnesses are covered in the [README](../README.md#install). Any of
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

From a clone of this repo (`git clone
https://github.com/mattbutlerengineering/skills`), or from the installed
plugin's cache directory,
`~/.claude/plugins/cache/<marketplace>/idea-to-prod/<version>/`, which holds
the same `tools/`. Pick the highest `<version>` there: an older cache's stamp
may lack the `factory-init: next:` lines described below.

```
python3 tools/factory_init.py stamp <path-to-target-repo>
```

A clean stamp ends with `factory-init: next:` lines naming what step 4
still needs from you (tests, CODEOWNERS), only while they are owed. A
tools-only stamp names the one it owes instead: `conductor.gate_command`.

All-or-nothing. It refuses a drifted source payload, a malformed manifest key,
a destination resolving outside the target, and **any existing file** in the
target — one problem line per refusal, no partial stamps. That last refusal is
strict: a repo that already has `docs/adr/README.md` cannot be stamped without
moving the conflict out of the way first. Two refusals come as a single line
instead: a target that is not an existing directory (the stamp never creates
one), and a target that is already stamped (it has `factory/manifest.json`),
which names the `update` command that refreshes it.

A repo with curated files of its own can opt in instead (#701):

```
python3 tools/factory_init.py stamp --keep-existing <path-to-target-repo>
```

It keeps the target's own copy of every curated, non-executable seed already
there (`.github/CODEOWNERS`, `.github/factory.json`, `.github/labels.json`,
the `docs/adr/` and `docs/design/` seeds) and prints one
`factory-init: kept <path>` line per file. It still refuses any collision in
the executable payload (`tools/factory/`, `.github/workflows/`, the `factory/`
mirror, the `Makefile`) and never overwrites. Kept files are yours, so the
checks in section 4 apply to them as they stand: a kept `labels.json` must
carry the labels detector J names, and a kept `CODEOWNERS` needs the factory's
gate paths added by hand. A kept `docs/adr/README.md` decides which seed ADRs
land: one it has no index row for is skipped and reported as
`factory-init: skipped <path>`, so detector D finds no unindexed seed.

105 files land: the 52-file payload installed to its destinations, plus the
pristine mirror it was stamped from. `factory/manifest.json` is the authority.

| Group | Count | What |
|-------|-------|------|
| `factory/` | 53 | the manifest and the pristine mirror the stamped detectors check themselves against |
| `tools/factory/` | 32 | the detector suite, the tools the workflows call, the Conductor's batch tool, the trace view, and a `.gitignore` for their bytecode |
| `docs/adr/` | 8 | the seeded ADR set, the convention, and the template |
| `.github/workflows/` | 6 | validator, assembler, design, cost-report, gate-digest, toolsmith-mine |
| `.github/` | 3 | `factory.json` (budgets, routing bands, WIP cap, monthly cap), `labels.json` (the 33-label taxonomy), `CODEOWNERS` (the code-owner gate) |
| `docs/design/` | 2 | the design-system seed and its template |
| `Makefile` | 1 | `make check` = detectors + selftest + tests, exactly what CI runs |

- [ ] Stamp exits clean
- [ ] Stamped files committed

## 4. Verify the stamp

- [ ] **A `tests/` directory holding at least one test exists.** The
      stamped `check` target runs `python3 -m unittest discover -q tests`
      and errors outright without one. An empty `tests/` (or one with only
      `__init__.py`) fails too: on Python 3.12+ unittest exits 5 on
      "NO TESTS RAN", and git never tracks an empty directory, so CI sees
      none at all.
      A fresh stamp into a test-less repo fails its first gate with
      `ImportError: Start directory is not importable: 'tests'` — which reads
      like a broken tool and isn't.
- [ ] `make check` exits clean
- [ ] **`.github/CODEOWNERS` owner substituted.** The template ships a
      placeholder handle on every entry, including the `*` fallback.
      Replace each with a handle or team with write access (a
      collaborator). If it is not a collaborator on the target, GitHub
      silently ignores the entry and the code-owner gate goes inert.
- [ ] `.github/factory.json` budgets and caps reviewed for this repo
- [ ] **Organization-owned repo: `FACTORY_OWNER_LOGIN` set.** Only the repo
      owner's `wo:ready-for-agent` label dispatches (ADR-0032). The
      assembler compares the labeler against
      `vars.FACTORY_OWNER_LOGIN || github.repository_owner`, and an
      organization repo's `repository_owner` is the org, which never applies
      a label. Unset there, every ready label is skipped with no claim, no
      comment and no red run. Set the repository variable to the login of
      the person who owns the factory:
      `gh variable set FACTORY_OWNER_LOGIN --body <login>`. Set it on the
      repository, not the org: the local work-order planner
      (`work_queue.py plan`) reads it with `gh variable list`, which sees
      repository variables only. A personal repo leaves it unset.

Substituting the owner, tuning the budgets and replacing the test line of the
`Makefile`'s `check` target when the repo's tests are not Python are
*expected* edits — the gates do not compare them against the payload. The executable half (`tools/factory/`
and `.github/workflows/`) is the opposite: never hand-edit it, and detector E
fails the build if you do. Change the template at the source and re-stamp.

`/doctor` covers this whole section.

### Taking a later factory change

A stamp is a snapshot. When the factory gains a fix, refresh the repo:

```
python3 tools/factory_init.py update <path-to-target-repo>
```

It overwrites the executable half and the mirror, lands any payload file the
repo lacks, and leaves everything you were meant to edit alone — reporting
each kept file that differs so you can reconcile it deliberately. Read its
make-target line: the workflows are refreshed and call only `make` targets, so
a factory change that adds one leaves a Makefile that has never heard of it.

## 5. Sync the label taxonomy

The 33-label taxonomy backs the work-order lifecycle machine, the gate digest,
and the sweeps' triage. `label_sync.py` reads and writes labels through the
`gh` CLI, so it needs `gh auth status` to pass and the target repo pushed to
GitHub with an `origin` remote:

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

Finished runs stay in the tree unless you compact them: once the retro is
committed, `operate` offers to collapse a feature or fix run into one
`summary.md` and delete the rest, which git history keeps (#2058). Run
artifacts are records, not living docs, and on a busy repo
`docs/features/` and `docs/fixes/` soon hold most of the markdown under
`docs/`, compacted or not. Keep your own formatters and markdown audits
off them, so a docs-only change doesn't pay for every finished run:

```
# .prettierignore, .markdownlintignore, or your audit script's skip list
docs/features/
docs/fixes/
```

The factory's own detectors still read these trees, and they must: run
discovery, `next` and the gates work from the artifacts.

- [ ] Formatters and markdown audits skip `docs/features/` and `docs/fixes/`

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

- [ ] `python3 <plugin>/tools/kb.py lint` prints `kb: 0 problem(s)` once
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
skill and its tool `tools/conductor.py` (PRD-0013,
`docs/features/orchestrator/`). The payload ships it, so a stamped repo
runs `tools/factory/conductor.py`, passing this plugin's charter stubs
with `--agents` (#678). Its optional `conductor` table in
`.github/factory.json` names the repo's gate command, the
standing-consent policy, and how the repo's own issue labels plan
(#700). `type_labels` maps labels to `feature` or `fix`, and
`size_labels` maps them to the budget sizes `S`, `M` or `L`. Each map,
when set, replaces the built-in rule (the first `type:` label, the first
`size:S|M|L` label), and an issue whose labels map to two different
values is deferred rather than guessed. `default_size` sizes an issue
with no size label at all. `defer_labels` lists labels such as
`blocked` or `needs-review`, and an issue carrying one is deferred with
the label named. An item's size budget is its estimate, split across
its steps as their ceilings by step weight (#724): by default `spec` and
`review`, the two steps at the top band, take three shares each and
`build`, `verify` and `ship` one each (#936), so a size-M feature at $15
plans spec at $4.99, review at $5.00 and each other step at $1.67.
`step_weights` maps any of those steps to a positive number that
replaces its default weight; the batch estimate stays the size budget.
`calibrate_floor` is the fewest samples `calibrate` suggests a weight or
budget from, a positive integer, 5 when absent (#940); below it
`calibrate` still warns about a step whose attempts spent their ceiling
half the time or more, and `plan` repeats that warning when it prices
from the same weights. Detector F checks the table. `implement-queue` still
fans out ready issues or work orders through one stage, and `autorun`
still drives one run end to end. One step needs no Conductor: turn on the merge queue
ADR-0070 already chose, if the repo's plan allows it; the merge turn uses
it when present.

## Consumer adoption

Read this before deleting anything a repo already has (#712). Measured in
mattbutlerengineering/mattbutlerengineering#6332.

**Plugin skills load only in local sessions.** A repo's
`.claude/settings.json` can declare this marketplace in
`extraKnownMarketplaces` and turn the plugin on in `enabledPlugins`. A local
Claude Code session on that repo then lists every `idea-to-prod:*` skill. A
claude.ai cloud routine on the same commit lists none, with no error and no
trust prompt. The RemoteTrigger API accepts `enabled_plugins` and
`extra_marketplaces` on a trigger, but silently drops them and echoes back
`[]`. So `conduct` is an Owner-attended, local-only path. It is not a
replacement for a repo's own unattended queue.

**Retire a repo-local skill or agent only when nothing plugin-less calls
it.** A local skill or agent can give way to a plugin skill only when
nothing that runs without the plugin calls it. Callers that run without the
plugin include cloud routines, prompts that GitHub Actions hand to an agent,
and agents dispatched by name (a classifier's routing table, for example).
If any of them calls it, keep it.

**Follow a skill by path from a pinned commit.** A cloud routine or
GitHub Actions job that clones this repo and follows
`skills/implement-queue/SKILL.md` by path gets whatever `main` holds when
it starts, so a change lands under an unattended run with no review on the
consumer's side (#1697). This repo publishes no tags or releases, so the
only pin is a commit SHA. Fetch exactly that commit in the bootstrap
(`git init`, `git remote add origin <repo-url>`, `git fetch --depth 1
origin <sha>`, `git checkout FETCH_HEAD`: a `git clone --depth 1`
followed by `checkout <sha>` fails for a SHA off the tip) rather than
following `main`, and keep the SHA in the consumer's own repo, where a
PR moves it. The `version` in `.claude-plugin/plugin.json` moves at each
wave's release PR and each Conductor merge (ADR-0095), so it only
roughly dates a SHA. Moving the SHA is the moment to run the skill's
Phase 0 profile check against the new skill, because a hook the table
gained since is the usual way a consumer's profile goes stale
(`skills/implement-queue/references/profile-migration.md`).

**Tools-only (Conductor-only) stamp.** A repo that wants the Conductor and
none of the CI can install just two pieces: `tools/factory/` and
`.github/factory.json` with its `conductor` table. Leave out the workflows,
the `Makefile` and the seeded ADRs, so CI and spend stay as they are:

```
python3 tools/factory_init.py stamp --tools-only <path-to-target-repo>
```

It lands `.github/factory.json`, `tools/factory/` and a manifest marked
tools-only, so detector E checks only those keys. A tools tree copied by
hand is adopted with `update --tools-only <target>`.

- The stamp writes `conductor.gate_command` as `make check`, and a tools-only
  stamp has no `Makefile`, so replace it with your repo's gate (the stamp's
  `factory-init: next:` line says so while it is still `make check`). It must
  be one command with no shell operators, because the Worker's tool allowlist permits that
  exact command and, beyond `python3` and a few `git` commands, nothing
  else. A fresh item worktree has no
  `node_modules` or equivalent. So when the gate needs a dependency install
  first, ship a small gate script that installs and then checks, and point
  `gate_command` at it.
- When the Worker's own commits meet hooks that need those dependencies
  (husky, lefthook or pre-commit), set `conductor.worktree_setup` to the
  install command as an argv list, for example `["npm", "ci"]`. Each Worker
  run executes it in its item worktree before the Worker launches, under the
  step's wall-clock limit, and never in the batch worktree. A failure stalls
  the item with cause `setup-failed` and names the command. It is off when
  absent (#850).
- Open batches from the repo's own checkout, not a throwaway clone. The batch
  ledger is an uncommitted file in the batch worktree until `close` commits
  it (#704).
- The Conductor's own git calls skip the repo's hooks, because they commit
  only generated evidence and `land_branch` waits for green CI on the pushed
  head (#833).

Worked example: mattbutlerengineering/mattbutlerengineering#6364 adds
`tools/factory/`, `.github/factory.json` and a `scripts/conductor-gate.sh`
gate, and nothing else.

## Deliberately not in scope

Unattended dispatch stays off until explicitly opted into:

- `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN` both unset → the
  assembler's agent step skips gracefully (either credential runs it);
  nothing is dispatched and nothing is faked.
- `wo:ready-for-agent` is inert unless applied by the repo owner — enforced by
  an actor check, not by convention. In an organization-owned repo the owner
  is the `FACTORY_OWNER_LOGIN` repository variable (section 4); unset, an org
  repo never dispatches.
- `sweeps.yml` is factory-repo-only and is **not** stamped, so a product repo
  gets no Sentry intake, no label-drift sweep, and no cross-plane reconcile.
  Those stay here.
- The payload ships `assembler.yml` + `assembler.py` but **no charter tree**
  (`factory/agents/`, `factory/charters/` stay here), so a stamped repo's
  dispatch fails closed at the charter lookup even with every secret set.
  Stamped-repo dispatch needs charters authored for that repo — a deliberate
  deferral, recorded in ADR-0055.
