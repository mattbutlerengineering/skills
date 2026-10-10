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

**Maintenance run**:
A scaled-down pass through the pipeline for a defect, regression, refactor,
or dependency upgrade, entering at a capture step and re-entering the spine
at the depth recorded in its brief. Its artifacts live under a per-fix
directory.
_Avoid_: bugfix run, hotfix run

**Harness**:
The agent runtime a skill runs inside. The skills run on three harnesses:
**Claude Code** (primary — marketplace plugin, `claude`-CLI evals, LEDGER
maturity), **oh-my-pi / omp** (ADR-0027), and **Grok** (ADR-0076). Stage
and router skill bodies name no harness. Claude Code and Grok share the
`.claude-plugin/` manifests; omp has the root `package.json` `pi.skills`
entry.
_Avoid_: platform, runtime, agent (bare)

**Utility skill**:
A directly-invoked skill that owns no stage artifact, has no template, and
is never routed to by /next. It acts on the work surrounding the pipeline —
a run in flight or the repo the pipeline serves. Examples: address-pr-review
works reviewer feedback on an authored PR; autorun orchestrates a full run
without owning an artifact itself; factory-init stamps a product repo with
the factory scaffold; mermaid turns processes and systems into digestible,
contrast-safe diagrams. The living roster is `protocol.py`'s
`UTILITY_SKILLS` (ADR-0023).
_Avoid_: helper skill, tool skill

**Project reference file**:
A file at a target repo's docs root that a utility skill writes outside
any run, which outlives every run and which skills read before they work.
`docs/ux-patterns.md` is one: the `ux-patterns` skill owns its behaviour
sections and the `ux-writing` skill owns its **Voice & terms** section;
`polish` and `ux-design` only read it (ADR-0078). It is not a run
artifact: no stage gates on it and the router never routes on it.
_Avoid_: run artifact (it is not one), design doc, style guide

**Work item**:
One checkable unit of a breakdown — one sitting's work with an acceptance
criterion.
_Avoid_: issue (reserved for tracker items), task, todo

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
The stage breaking a finished technical design into milestones, work items,
and a dependency-ordered sequence. Pure work breakdown — no design decisions.
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

### Factory (ADR-0032, ADR-0033, ADR-0034)

**Work order**:
A work item promoted for dispatch: carries a typed ID (WO-####), a size
class and budget, and is mirrored one-way to a tracker issue so an
unattended agent can execute it.
_Avoid_: ticket, task

**Knowledge plane**:
The run artifacts as source of truth (ADR-0004, restated for the factory).
Offline detectors gate it; orientation reads only this plane.
_Avoid_: docs, wiki

**Dispatch plane**:
The work queue — work-order issues plus the dependency graph — mirrored
one-way from breakdown rows and never authoritative over the knowledge
plane.
_Avoid_: backlog (reserved for the seed inbox), tracker state

**Cost ledger**:
The append-only spend record (docs/factory/costs.jsonl): one line per
dispatched run or gate passage, the factory's measurement substrate
(ADR-0034, ADR-0041). Shape owned by cost_ledger.py; gated by detector
G; never rewritten.
_Avoid_: billing log, spend history

**Gate**:
One of exactly three human decision points (PRD approval, blueprint/ADR
approval, PR merge), each physically enforced. Everything between gates
runs unattended.
_Avoid_: checkpoint, sign-off, approval step

**Charter**:
The definition of one agent role: mission, owned stages, entry/exit
criteria, actions, tool grants, escalation rules. Encoded as a charter
(`factory/charters/<role>/CHARTER.md`) plus a subagent stub
(`factory/agents/factory-<role>.md`); the roster is `factory/CHARTERS.md`.
_Avoid_: persona, job description
