# Skills (development lifecycle toolkit)

A from-scratch set of skills and tools that guide a user through the entire
development process, from raw idea to production. Built on lessons from the
ai-tooling repo but independent of it.

## Language

**Lifecycle pipeline**:
The organizing spine of this repo — an ordered sequence of stages from idea to
production, where each stage produces an artifact the next stage consumes.
_Avoid_: workflow (overloaded), process, dev loop

**Stage**:
One step of the lifecycle pipeline, served by one or more skills.
_Avoid_: phase, step

**Artifact**:
The concrete output a stage produces and hands to the next stage (e.g. an idea
brief, a PRD).
_Avoid_: deliverable, output, doc

**Product run**:
A full pass through the pipeline taking a greenfield product from idea to
production. Its artifacts live at the target repo's docs root.
_Avoid_: project run, greenfield run

**Feature run**:
A scaled-down pass through the pipeline for a single feature, re-entering at
Idea or PRD. Its artifacts live under a per-feature directory.
_Avoid_: iteration, cycle

**Utility skill**:
A directly-invoked skill that owns no stage artifact, has no template, and
is never routed to by /next. It acts on the work around a run: address-pr-review
works reviewer feedback on an authored PR; autorun orchestrates a full run,
dispatching a stage subagent per stage without owning an artifact itself. A
full skill for install, lint, ledger, and trigger-eval purposes (ADR-0023).
_Avoid_: helper skill, tool skill

### Stages

**UX Design**:
The stage producing user-facing flows, wireframes, and screens. Conditional —
skipped when the work has no user-facing surface.
_Avoid_: design (ambiguous with Architect)

**Architect**:
The stage producing the technical design: architecture, data model, tech
stack, ADRs. Contains no UX work and no work scheduling.
_Avoid_: design, tech planning

**Decompose**:
The stage breaking a finished technical design into milestones, issues, and a
dependency-ordered sequence. Pure work breakdown — no design decisions.
_Avoid_: plan, planning

### Evals

**Trigger eval**:
A routing eval: does the right skill fire for a query, tested with every
skill description installed at once (`trigger_eval.py`). Measures discrimination
between adjacent stages, not one description in isolation.
_Avoid_: benchmark

**Output eval**:
Given a seeded run directory and pre-supplied interview answers, does the
skill produce an artifact meeting objective expectations
(`evals/output/<slug>.json`, graded per `docs/output-evals.md`).
_Avoid_: quality test

**Eval fixture**:
A seed docs tree under `evals/fixtures/` copied into a scratch project before
an output eval runs. Upstream artifacts pre-answer what the skill would
otherwise interview for.
_Avoid_: test data
