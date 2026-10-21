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
`polish` and `ux-design` only read it (ADR-0079). It is not a run
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

**Outcome signal**:
One of three measures of how a Decompose plan held up, read from git
history by `decompose_signals.py`: re-plan (work items added, dropped,
split or merged between the decompose and implement boundaries), design
gaps routed to Architect, and review-traced findings (review findings
that name a work item). Each is labelled observed or inferred by the
boundaries it read (ADR-0109); a run history cannot answer is
unmeasurable, never zero.
_Avoid_: plan quality score

**Size-band error interval**:
A size band's nearest-rank P10, P50 and P90 of Balanced Relative Error
against the band's budget, one sample per work order, printed by
`size_band_calibration.py` only at or above the calibrate floor and
otherwise refused with the band's n.
_Avoid_: estimate range, confidence interval

**Decompose lesson**:
A derived, sourced, voted line in the Decompose lessons file, describing a
contrast between a hit run and a clean run of the same kind. Its importance
starts at 2, later treated runs move it by 1, and it is removed at 0.
Decompose reads it as a hypothesis, never a rule.
_Avoid_: insight, rule, tip

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

### Claims (ADR-0107)

**Claim kind**:
What a line in a verification or review artifact rests on. Four kinds:
**observed** (quoted output), **derived** (computed from observed),
**inferred** (judgement) and **unknown** (not examined; what NOT RUN,
skipped, deferred and n/a disclose).
_Avoid_: confidence level

**Fail-closed roll-up**:
Unknown, unsupported, truncated and skipped never aggregate to pass. A
Summary or Verdict counts or names every such item, and never reads as an
unqualified pass over them. Detector H enforces it on a `verification.md`
Summary dated on or after `ROLLUP_ADOPTED`.
_Avoid_: rounding up, all green

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

**Knowledge base**:
A target repo's durable, non-inferable project facts — invariants,
gotchas, cross-module flows, the why behind a decision — as pages in
`docs/kb/`, indexed inline in the always-loaded file by `kb.py` and kept
by the knowledge-base utility skill (ADR-0078). Not the knowledge plane:
that is the run artifacts, which belong to one run; a knowledge-base page
outlives every run and cites the code it rests on.
_Avoid_: knowledge plane (taken), wiki, memory bank

**Trace view**:
The dated, chronological report that joins one run's tickets,
requirements, decisions and feedback, derived on demand from their
owners by `trace.py` and never committed (ADR-0092). A reader, not a
store: it owns no fact.
_Avoid_: timeline index, knowledge graph, trace log

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

### Conductor (PRD-0013, ADR-0084)

**Conductor**:
The role the Owner's own session takes while it runs the `conduct`
utility skill: it opens a batch, launches Workers, presents the decision
queue, records the Owner's answers and drives the merge turns they
cover. It never writes or reviews an item's code; `conductor.py` holds
every rule. A role name, not the skill's name.
_Avoid_: orchestrator (the run's working title), dispatcher, scheduler

**Worker**:
One headless harness process running one step of one batch item in that
item's own worktree, on the model, effort and dollar ceiling the Owner's
policy names, metered into the cost ledger. It cannot ask mid-run; it
stops, and the Conductor queues the question.
_Avoid_: subagent (an in-session agent, unmetered in dollars), agent (bare)

**Batch**:
A set of the Owner's issues the Conductor takes from a priced plan to
every item merged or blocked, under one slug, on one batch branch
(`conductor/<batch>`), closed with one scorecard.
_Avoid_: round (work-queue's), sprint

**Batch ledger**:
The append-only JSONL record of one batch
(`docs/factory/batches/<batch>/ledger.jsonl`): its plan, reservations,
every item state change, every Worker run, every ask and answer, and its
close. `conductor.py` owns the row grammar; a line that breaks it fails
every reader. Not the cost ledger, which holds the batch's spend.
_Avoid_: log, journal

**Item view**:
One item's read-only reading of the batch ledger (state, launches, asks,
reservations), computed by `conductor.py` from the rows. Capability
modules ask it; they never filter rows.

**Decision queue**:
The batch ledger's unanswered asks, presented to the Owner oldest first,
one at a time, recommended option first. An answer row written straight
after the Owner picks an option in the Conductor's session is the only
Owner write, and the only consent the tool acts on except standing
consent.
_Avoid_: inbox, approval queue, gate (one of the three human gates)

**Standing consent**:
The Owner's merge consent given in advance through `factory.json`'s
opt-in `conductor.standing_consent` policy, off by default (ADR-0086).
`next` records it as a `consent` row for a shipped item that no merge ask
covers, when the item changes no gate-path file and, if tier labels are
configured, its issue carries one. The merge still needs a reviewed pass
from a distinct Worker and green checks. It is not an answer, and the
scorecard never counts it as an Owner touch.
_Avoid_: auto-merge, pre-approval, blanket consent

**Merge train**:
An ordered list of batch items one merge answer covers: each merges, in
order, only after every earlier item has merged, and an item whose gate
files changed after its gate answer needs its own merge ask instead.
_Avoid_: merge queue (GitHub's, which a train may ride), batch merge
