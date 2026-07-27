# Architecture Decision Records

Decisions live here as sequentially numbered ADRs (`0001-slug.md`). An ADR
can be a single paragraph; the value is in recording the decision and its
why. Don't delete or rewrite an old ADR when a decision changes — write a new
one that supersedes it and update the old one's status line.

Statuses: **accepted** (explicitly confirmed), **provisional** (recommended
answer adopted while awaiting confirmation — pivot freely),
**superseded by ADR-NNNN** (fully retired — citing it is drift),
**superseded in part by ADR-NNNN**, and **amended by ADR-NNNN** (both
partial: the decision stays live and citable). The machine-readable
authority is `ADR_STATUS` in `gates.py`, which also allows a
parenthesized annotation after any head.

ADRs 0001–0018 were migrated from the former `DESIGN.md`, which captured the
initial design interview (2026-07-01). See [CONTEXT.md](../../CONTEXT.md) for
the canonical vocabulary.

## Index

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](0001-lifecycle-pipeline-spine.md) | Spine: lifecycle pipeline | accepted |
| [0002](0002-stage-taxonomy.md) | Stage taxonomy (Idea → … → Operate) | accepted |
| [0003](0003-two-run-scales.md) | Two run scales (product / feature) | superseded in part by ADR-0025 |
| [0004](0004-artifacts-are-the-state.md) | Artifacts are the state | accepted |
| [0005](0005-soft-gating.md) | Soft gating | accepted |
| [0006](0006-plugin-from-day-one.md) | Plugin from day one | accepted |
| [0007](0007-claude-code-only-target.md) | Claude Code only target harness | amended by ADR-0027 |
| [0008](0008-self-contained-skills.md) | Skills are self-contained | accepted |
| [0009](0009-audience-you-first-publishable-always.md) | Audience: you first, publishable always | provisional |
| [0010](0010-stage-skills-plus-thin-router.md) | Stage skills + thin router | provisional |
| [0011](0011-interview-early-draft-late.md) | Interview early, draft late | provisional |
| [0012](0012-lightweight-ledger.md) | Lightweight ledger | provisional |
| [0013](0013-plugin-name-idea-to-prod.md) | Plugin name: idea-to-prod | provisional |
| [0014](0014-mit-license.md) | License: MIT | accepted |
| [0015](0015-templates-per-stage.md) | Templates per stage | accepted |
| [0016](0016-operate-scope.md) | Operate scope | accepted |
| [0017](0017-conditional-ux-frontmatter.md) | Conditional-UX mechanics | accepted |
| [0018](0018-git-bootstrap.md) | Git bootstrap | accepted |
| [0019](0019-trigger-and-output-evals.md) | Evals: routing discrimination + on-demand output grading | accepted |
| [0020](0020-hybrid-recall-policy.md) | Hybrid recall policy for skill descriptions | accepted |
| [0021](0021-shared-protocol-module.md) | One shared protocol module alongside standalone scripts | accepted |
| [0022](0022-eval-schema-module.md) | One eval-schema module beside the protocol module | accepted |
| [0023](0023-utility-skills.md) | Utility skills alongside stage skills and the router | provisional |
| [0024](0024-eval-schema-charter.md) | eval_schema's charter covers all eval knowledge, not one file's schema | provisional |
| [0025](0025-maintenance-run-scale.md) | A third run scale: the maintenance run | accepted |
| [0026](0026-tracker-mirror-one-way.md) | The issue-tracker bridge is an opt-in one-way mirror | accepted |
| [0027](0027-oh-my-pi-second-harness.md) | oh-my-pi is a supported second harness (Claude primary) | accepted |
| [0028](0028-brownfield-adoption-onramp.md) | Brownfield adoption on-ramp (adopt/onboard entry) | provisional |
| [0029](0029-backlog-seed-inbox.md) | A derived, advisory backlog (seed inbox) | accepted |
| [0030](0030-incident-fastlane-and-tracker-intake.md) | Incident fast lane and tracker intake | provisional |
| [0031](0031-omp-trigger-eval-adapter.md) | The trigger eval drives omp too; results are harness-marked | accepted |
| [0032](0032-factory-dispatch-plane.md) | Factory dispatch plane: issues mirror breakdown rows one-way | accepted |
| [0033](0033-three-human-gates.md) | Three human gates: PRD, blueprint, merge | amended by ADR-0036 |
| [0034](0034-work-order-budgets-and-routing.md) | Work-order budgets and model routing | amended by ADR-0041 |
| [0035](0035-github-is-the-single-work-order-mirror.md) | GitHub issues are the single work-order tracker mirror | accepted |
| [0036](0036-agent-merge-under-independent-review.md) | Agent merges permitted under independent review | accepted |
| [0037](0037-factory-seam-modules.md) | Factory seam modules: knowledge_plane, cli, factory_config, cost_ledger | amended by ADR-0039 |
| [0038](0038-harness-adapter-registry.md) | One registration per harness in the trigger-eval runner | accepted |
| [0039](0039-tracker-grammar-joins-the-knowledge-plane.md) | Tracker-mirror grammar joins the knowledge plane | amended by ADR-0040 |
| [0040](0040-write-outputs-joins-the-cli-seam.md) | write_outputs joins the cli seam | amended by ADR-0042 |
| [0041](0041-gate-latency-rows-join-the-cost-ledger.md) | Gate-latency observations are cost-ledger rows | accepted |
| [0042](0042-gh-port-joins-the-cli-seam.md) | The gh port (gh_runner) joins the cli seam | accepted |
