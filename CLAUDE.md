# skills — agent notes

Idea-to-prod pipeline skills, vended as a Claude plugin. Artifacts are the
state: each stage skill reads/writes run artifacts (product runs at the
target repo's `docs/` root, feature runs under `docs/features/<slug>/`),
and `skills/next` routes by what exists. Spec: `docs/pipeline-protocol.md`.

## Verify (CI runs both on every push/PR)

- `python3 -m unittest discover tests`
- `python3 lint.py` — exit 0 / output matching `lint: 0 problem(s)`

On demand only (real model runs, costs money, never CI):
`python3 trigger_eval.py` (needs the `claude` CLI).

## Hard conventions

- **Stdlib only.** Every script is standalone Python 3 standard library.
  No third-party dependencies.
- **Two seam modules, everything else thin callers**: `protocol.py`
  (ADR-0021 — taxonomy, artifact table, frontmatter, next-stage) and
  `eval_schema.py` (ADR-0022, ADR-0024 — all eval knowledge: routing
  eval-set shape/kinds/validation, output-eval record shape, results
  naming grammar). A new shared module needs multiple real callers AND
  observed divergence between their copies — anticipated reuse doesn't qualify.
- **Three skill kinds**: stage skills (own a run artifact, routed to by
  `next`), the `next` router, and utility skills (ADR-0023 —
  directly-invoked, own no artifact, never routed to; `protocol.py`
  `UTILITY_SKILLS`).
- **Problem-string contracts**: checkers/validators return lists of
  label-prefixed problem strings; callers print and exit nonzero. Tests
  assert the exact strings through public interfaces (see
  `tests/test_lint_checkers.py`).

## Eval honesty (non-negotiable)

- `evals/results/` is append-only: dated snapshots, never rewritten.
- Never edit an eval definition to make a failing case pass.
- LEDGER maturity graduates only via a real run — never fabricate run or
  eval evidence. (ADR-0012, ADR-0019; details in `evals/README.md`.)

## Where things are decided

- `CONTEXT.md` — canonical vocabulary (use these terms in code and docs)
- `docs/adr/` — decisions; supersede with a new ADR, don't rewrite
- `LEDGER.md` — per-skill maturity, linked to eval evidence
