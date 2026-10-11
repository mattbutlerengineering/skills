# skills — agent notes

Idea-to-prod pipeline skills, vended as a Claude plugin. Artifacts are the
state: each stage skill reads/writes run artifacts (product runs at the
target repo's `docs/` root, feature runs under `docs/features/<slug>/`),
and `skills/next` routes by what exists. Spec: `docs/pipeline-protocol.md`.

## Verify (CI runs all three on every push/PR)

- `python3 -m unittest discover tests`
- `python3 lint.py` — exit 0 / output matching `lint: 0 problem(s)`
- `python3 gates.py && python3 gates.py --selftest` — factory drift
  detectors (roster in `gates.py`'s module docstring; B skips locally
  without a PR event payload, but the selftest exercises it), output
  matching `gates: 0 problem(s)`

On demand only (real model runs, costs money, never CI; all three need
the `claude` CLI):

- `python3 trigger_eval.py` — routing eval
- `python3 charter_replay.py` — charter regression suite: golden fixture
  work orders replayed against the role charters. Its scoring seam is pure
  and injected, so CI covers degradation detection offline with recorded
  transcripts; only the live replay costs money. `--control` also replays
  each case with its charter's `## Must never` section deleted and fails
  any case whose stripped run never fires a forbidden pattern (a trap the
  model never takes guards nothing); it doubles the cost.
- `claude plugin eval . --scaffold --model claude-sonnet-5
  --judge-model claude-haiku-4-5 --max-cost-usd 15 --no-publish
  --allow-tools Write Edit "Bash(python3 *)" "Bash(git *)"` — per-skill
  with/without-plugin delta over `plugin-evals/` (the manifest's
  `experimental.evals`, so `evals/results/` is never written; ADR-0081).
  `--tag <skill>` runs one suite. Output lands in gitignored
  `plugin-evals/results/`. A cited run's `aggregate-result.json` is
  copied unedited to append-only `plugin-evals/records/<date>[-N].json`.
  It is eval evidence and never graduates LEDGER maturity.

Also on demand, but free and needing nothing installed — a review
pre-pass, deliberately **not** a gate:

- `python3 one_owner.py` — which facts this repo's own Python modules
  state twice (the same value in two modules, or two functions reading
  the same payload keys), as `one-owner:` problem strings. It is outside
  `make check` and outside every workflow, so a finding never colours
  main red — it is a question for a human. A deliberate second owner is
  recorded with a `# one-owner:` marker at the definition it excuses
  (ADR-0061), and the pass re-derives that carve-out in both directions
  on every run.

## Hard conventions

- **Stdlib only.** Every script is standalone Python 3 standard library.
  No third-party dependencies.
- **Bump `.claude-plugin/plugin.json`'s version with any `skills/`
  change.** Installed plugin caches refresh only when the version moves,
  and `lint.py` checks only that the field exists.
- **Seam modules, everything else thin callers**: `protocol.py`
  (ADR-0021 — taxonomy, artifact table, frontmatter, next-stage),
  `eval_schema.py` (ADR-0022, ADR-0024 — all eval knowledge: routing
  eval-set shape/kinds/validation, output-eval record shape, results
  naming grammar), and the four factory seams (ADR-0037, ADR-0039,
  ADR-0040 — `knowledge_plane.py` typed-ID grammar + run walk, `cli.py`
  external-CLI + harness-IO conventions and the guarded local-file read
  (`read_file`, ADR-0075), `factory_config.py` factory.json
  reader/resolvers, `cost_ledger.py` cost-ledger shape), plus
  `human_gates.py` (ADR-0056 — what a gate is: its ledger name, its
  queue and passed labels, its digest heading, the label-event walk, and
  the stay partition the digest and the miner divide between them) and
  `plane_drift.py` (ADR-0060 — the ADR-0032 cross-plane drift rule the
  reconcile sweep files and the dashboard renders; `absent_is_drift` is
  the caller's claim about its own listing). A new shared module needs
  multiple real callers AND observed divergence between their copies —
  anticipated reuse doesn't qualify. It is mirrored into the payload iff
  a payload tool imports it: `plane_drift.py` is root-only because
  neither of its callers ships (ADR-0060).
- **Three skill kinds**: stage skills (own a run artifact, routed to by
  `next`), the `next` router, and utility skills (ADR-0023 —
  directly-invoked, own no artifact, never routed to; `protocol.py`
  `UTILITY_SKILLS`).
- **Problem-string contracts**: checkers/validators return lists of
  label-prefixed problem strings; callers print and exit nonzero. Tests
  assert the exact strings through public interfaces (see
  `tests/test_lint.py`).
- **Factory templates are checksum-pinned**: after any edit under
  `factory/templates/**` or to any root file in `factory_init.MIRRORS`
  (the authority on what is mirrored into the payload — root tools,
  workflows, CODEOWNERS, and the Makefile, each through its entry's
  transform per ADR-0050), run `python3 factory_init.py update-manifest`
  and commit the manifest with the change. Detector E gates
  manifest↔payload; `tests/test_factory_init.py` pins payload↔root.
- **Dispatch mirrors one-way** (ADR-0032): never create a `WO-####` issue
  before its `breakdown.md` row exists.
- **Typed IDs live in run-artifact frontmatter** (`id: PRD-0001`), never a
  parallel `docs/prd/` tree (ADR-0004).

## Eval honesty (non-negotiable)

- `evals/results/` is append-only: dated snapshots, never rewritten.
- Never edit an eval definition to make a failing case pass.
- LEDGER maturity graduates only via a real run — never fabricate run or
  eval evidence. (ADR-0012, ADR-0019; details in `evals/README.md`.)

## Where things are decided

- `CONTEXT.md` — canonical vocabulary (use these terms in code and docs)
- `docs/adr/` — decisions; supersede with a new ADR, don't rewrite
- `LEDGER.md` — per-skill maturity, linked to eval evidence
- `docs/factory/improvement-routine.md` — the daily cloud routine's
  protocol (ADR-0044); tuned by PR, never edited by the routine itself
- `docs/factory/retro-reflect-routine.md`,
  `docs/factory/queue-groomer-routine.md`,
  `docs/factory/doc-gardener-routine.md` — the weekly roster routines'
  protocols (ADR-0044's pattern); only the queue groomer's trigger
  exists (created 2026-09-29 as the pilot), and the retro/reflect and
  doc-gardener triggers are deferred by owner decision

## Issue tracking

GitHub issues are the only tracker (ADR-0083); beads is retired and its
notes are frozen in `docs/research/beads-memories-archive.md`.

- Work orders are mirrored one-way from `breakdown.md` rows with `wo:*`
  labels (ADR-0032, ADR-0035) — never hand-made.
- Any other task is a plain issue: `gh issue create` with a `type:*`
  label from the taxonomy (`factory/templates/.github/labels.json`) and
  no `wo:*` label — the reconcile sweep only judges issues that carry
  one (`plane_drift.reconcile_drift`). `gh issue list` is the queue;
  close an issue from the PR that fixes it (`Closes #N`).
- `docs/backlog.md` stays the advisory seed inbox (ADR-0029).
- Durable project knowledge goes to `docs/kb/` through the
  `knowledge-base` skill, not into an issue or a memory store.

<!-- BEGIN KB INDEX: generated by kb.py index; edit page summaries, not this block -->
## Knowledge base

Non-inferable project knowledge, one page per line. Read a page before changing what its line names.

- docs/kb/cross-pr-merge-hazards.md: Two PRs can each pass CI and fail together; per-PR CI cannot see it — test the pair with merge-tree before merging in sequence.
- docs/kb/gates-scan-every-doc.md: Detectors C and I scan every repo markdown, fences included; an example PRD/ADR/WO id or a sample link fails gates.
- docs/kb/main-unprotected.md: main has no branch protection or rulesets — ADR-0036's required checks are convention, and the ADR-0070 merge queue is off.
- docs/kb/manifest-regen.md: update-manifest hashes every file under factory/templates/; delete stray .orig/.rej first or they get checksum-pinned.
- docs/kb/pr-body-contract.md: A PR body needs a WO id or a "No work order:" line plus Closes #N, or detector B fails on CI only — it skips locally.
- docs/kb/stamp-outside-payload.md: factory-init stamps CODEOWNERS, the Makefile, factory.json, labels.json, seeded ADRs and design docs outside FACTORY_OWNED; update never refreshes them, and only doctor checks most.
<!-- END KB INDEX -->
