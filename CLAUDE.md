# skills — agent notes

Idea-to-prod pipeline skills, vended as a Claude plugin. Artifacts are the
state: each stage skill reads/writes run artifacts (product runs at the
target repo's `docs/` root, feature runs under `docs/features/<slug>/`),
and `skills/next` routes by what exists. Spec: `docs/pipeline-protocol.md`.

## Verify (CI runs both on every push/PR)

- `python3 -m unittest discover tests`
- `python3 lint.py` — exit 0 / output matching `lint: 0 problem(s)`
- `python3 gates.py && python3 gates.py --selftest` — factory drift
  detectors (A/C/D/E/F/G/H/I), output matching `gates: 0 problem(s)`

On demand only (real model runs, costs money, never CI; both need the
`claude` CLI):

- `python3 trigger_eval.py` — routing eval
- `python3 charter_replay.py` — charter regression suite: golden fixture
  work orders replayed against the role charters. Its scoring seam is pure
  and injected, so CI covers degradation detection offline with recorded
  transcripts; only the live replay costs money.

## Hard conventions

- **Stdlib only.** Every script is standalone Python 3 standard library.
  No third-party dependencies.
- **Seam modules, everything else thin callers**: `protocol.py`
  (ADR-0021 — taxonomy, artifact table, frontmatter, next-stage),
  `eval_schema.py` (ADR-0022, ADR-0024 — all eval knowledge: routing
  eval-set shape/kinds/validation, output-eval record shape, results
  naming grammar), and the four factory seams (ADR-0037 —
  `knowledge_plane.py` typed-ID grammar + run walk, `cli.py` subprocess
  adapter, `factory_config.py` factory.json reader/resolvers,
  `cost_ledger.py` cost-ledger shape). A new shared module needs multiple
  real callers AND observed divergence between their copies — anticipated
  reuse doesn't qualify.
- **Three skill kinds**: stage skills (own a run artifact, routed to by
  `next`), the `next` router, and utility skills (ADR-0023 —
  directly-invoked, own no artifact, never routed to; `protocol.py`
  `UTILITY_SKILLS`).
- **Problem-string contracts**: checkers/validators return lists of
  label-prefixed problem strings; callers print and exit nonzero. Tests
  assert the exact strings through public interfaces (see
  `tests/test_lint_checkers.py`).
- **Factory templates are checksum-pinned**: after any edit under
  `factory/templates/**` (or to `gates.py`/`protocol.py`, which are
  mirrored into the payload), run `python3 factory_init.py update-manifest`
  and commit the manifest with the change (detector E gates).
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


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->
