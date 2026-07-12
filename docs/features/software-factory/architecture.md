---
stage: architect
run: feature:software-factory
date: 2026-07-11
ux: skipped — infrastructure feature — no user-facing surface in v1; the operator's surface is the tracker and PRs
assumptions:
  - "Retroactive artifact, operator-directed: the run was already at Implement (WO-0001, WO-0002, WO-0003, WO-0013 merged) when this was written. It consolidates decisions already made in ADR-0032/ADR-0033/ADR-0034 and already embodied in merged code; it decides nothing new."
  - "No new ADRs (architect skill default — offer ADRs sparingly): every decision recorded here is either already in ADR-0032/ADR-0033/ADR-0034 or is a one-line record that does not meet the ADR bar (hard to reverse + surprising + a real trade-off)."
  - "Live trade-off review not held (architect skill step 5): the run is unattended and the trade-offs were settled at ADR time. The PR carrying this artifact is the blueprint gate (ADR-0033 gate 2) and stands in for that conversation."
  - "The approved M1 plan referenced by breakdown.md is a session artifact, not in this repo. Where it is the only source for a detail, this artifact takes the detail from merged code and the breakdown rows instead — the checkable record wins over recollection."
  - "Component status labels (BUILT / PARTIAL / UNBUILT) were derived by reading the tree at authoring time, not from a status field anyone maintains; they are a snapshot, not a contract."
---

# Architecture: Software factory v1 (self-host)

## Preamble: what this artifact is

This is the Architect artifact for `feature:software-factory` (PRD-0001),
written **after** implementation began. `protocol.next_stage()` routed the run
here because the protocol requires `architecture.md` for a feature run and the
file did not exist; the breakdown's Notes recorded that absence as
operator-directed, but prose is not a skip the protocol reads.

So this document **consolidates** a design that already existed, scattered
across three accepted ADRs, an approved plan held outside the repo, and merged
code. It does not invent architecture, and it does not narrate what got built
as if it had been inevitable. Where the built system diverges from the ADRs, or
where a question is genuinely open, it says so — see *Divergences* and *Open
questions*, which are the load-bearing sections for anyone joining this run.

Status snapshot at authoring time: merged — WO-0001 (factory-init + payload +
manifest), WO-0002 (labels + label-sync + CODEOWNERS template), WO-0003
(detector B + Makefile lockstep), WO-0013 (three minimal charters). Everything
else in `breakdown.md` is open. The factory's **knowledge plane is largely
built; its dispatch plane is not** — nothing executes a work order today.

## Approach

The factory is a **layer on top of the existing pipeline, not a replacement for
it**. Artifacts stay the state (ADR-0004); the pipeline stages, the protocol
seam (`protocol.py`), and the skill set are untouched. What the factory adds is
a second plane and a set of gates around it:

- A **knowledge plane** — the run artifacts, the ADRs, `CONTEXT.md`, and (when
  it exists) the cost ledger. It is the only source of truth and the only thing
  orientation reads.
- A **dispatch plane** — work-order issues on GitHub plus a beads dependency
  graph, mirrored **one-way** from `breakdown.md` rows. It is a queue, never a
  source of truth; disagreement is always resolved in the knowledge plane's
  favor.
- A **typed-ID spine** (`PRD-####`, `ADR-####`, `WO-####`) making the link
  between requirement, decision, work order, and PR checkable **offline, with
  regular expressions and a checksum manifest** — no graph database, no daemon,
  no service.
- **Offline detectors in CI** that fail the build when the spine breaks, and a
  small number of **network detectors** kept strictly out of the offline suite
  so `make check` is hermetic and identical to CI.
- **Three human gates** (ADR-0033) around an otherwise unattended middle, and
  **three uncorrelated stops** (ADR-0034) around every unattended run.

The shape is chosen for a solo operator on a free-plan private repo: everything
that can be a file in git is a file in git; everything that must be a service is
GitHub, which is already there. Novelty is confined to the detector set. The
consequence — visible throughout — is that enforcement leans on CI and
convention where the ADRs assumed platform controls.

## Components

Each component carries a status: **BUILT** (merged, exercised by tests),
**PARTIAL** (exists but not wired to anything that runs it), **UNBUILT** (named
in the breakdown, no code).

### Knowledge plane — run artifacts (BUILT, by the pre-existing pipeline)

- Responsibility: hold the truth. `idea.md`, `prd.md` (carrying `id: PRD-0001`),
  `architecture.md` (this file), `breakdown.md` (the work-order rows), the ADRs,
  `CONTEXT.md`, and — once WO-0006 lands — `docs/factory/costs.jsonl`.
- Collaborators: `protocol.py` (frontmatter + next-stage), every stage skill,
  every detector.
- Note: the factory contributed nothing here except the `id:` field and the
  breakdown row grammar. That is the point — ADR-0032's first constraint is that
  dispatch must not become a second source of truth.

### Typed-ID spine (BUILT)

- Responsibility: make cross-plane links checkable without a database.
  `PRD-####` is declared once, in `prd.md` frontmatter (ADR-0004: typed IDs live
  in run-artifact frontmatter, never a parallel `docs/prd/` tree). `ADR-####`
  is the ADR's filename prefix. `WO-####` is a `breakdown.md` row token, and the
  same token names its mirrored issue and is cited by the PR that implements it.
- Collaborators: detectors A, B, C; `factory/skills/*/SKILL.md` (charters cite
  the row, not the issue).

### Gate detectors — `gates.py` (BUILT: A, B, C, E, F; UNBUILT: D, G, H, I)

- Responsibility: fail the build when the spine rots. One module, one convention
  (a checker takes the repo root and returns label-prefixed problem strings; the
  CLI prints them and exits nonzero — the same contract as `lint.py`).
- Built: **A** WO-CITATION (every breakdown work-order row cites a PRD id),
  **B** PR-TRACEABILITY (a PR body carries a `WO-####` and a closing keyword;
  reads the CI event payload, SKIPs locally), **C** LINK-INTEGRITY (every typed
  token in `docs/**` and `CONTEXT.md` resolves; duplicate PRD ids fail),
  **E** SCAFFOLD-SYNC (the template payload matches its checksum manifest),
  **F** CONFIG-SHAPE (`factory.json` parses; every field is a valid token).
- Unbuilt: **D** blueprint-drift, **G** cost-ledger, **I** staleness (WO-0008);
  **H** evidence-honesty (WO-0011).
- Collaborators: `protocol.py` (frontmatter read), `checks.yml`, the stamped
  `Makefile`, `factory_init.py` (which calls `check_scaffold_sync` before
  stamping).
- `--selftest` runs every built detector against fixture trees: each must catch
  its planted defect *and* stay silent on a clean tree. The selftest is the
  detector suite's own test suite and runs in CI beside it.

### Network detector — `label_sync.py` (PARTIAL)

- Responsibility: detector **L** (LABEL-SYNC) — the live GitHub label set must
  match `labels.json`. Reads through the `gh` CLI; `--apply` force-creates
  drifted labels; drift is one-way (labels outside the taxonomy are never
  deleted).
- Collaborators: none that run it. It is deliberately **never** in `gates.py`'s
  `CHECKERS` — the offline suite must stay hermetic — and the sweep that was to
  call it (WO-0010) does not exist. Today it is a correct detector nobody runs.

### Template payload + `factory_init.py` (BUILT)

- Responsibility: make the factory installable in *another* repo. The payload
  (`factory/templates/**`) carries `Makefile`, `.github/CODEOWNERS`,
  `.github/labels.json`, `factory.json`, and machine-copied mirrors of
  `gates.py`, `protocol.py`, `label_sync.py` under `tools/factory/`.
  `update-manifest` refreshes the mirrors from the repo root and rewrites
  `factory/manifest.json` (sha256 per file); `stamp <target>` copies the payload
  into a product repo, refusing a drifted source and any existing destination
  file (no partial stamps, no overwrites).
- Collaborators: detector E pins the result — a hand-edited template fails CI.
- Honest note: this repo **is not itself stamped**. It self-hosts by running the
  root scripts directly from `checks.yml`; there is no `Makefile`, no
  `tools/factory/`, no `.github/factory.json` here. `stamp` has been exercised
  only against scratch trees in tests, never against a real product repo.

### Factory config — `factory.json` (PARTIAL)

- Responsibility: the per-repo knobs — `budgets_usd` (S/M/L), `routing`
  (mechanical / implementation / architecture_review → model id), `wip_cap`,
  `monthly_cap_usd`. One routing source of truth, so a charter names a *band*
  and never a model id.
- Collaborators: detector F validates its shape. Nothing else reads it: the
  budget guard, the routing resolver, and the circuit breaker are all unbuilt.
  Today the config is *validated but inert*.

### Dispatch plane — issues, lifecycle labels, beads (PARTIAL)

- Responsibility: hold the queue. Issues #106–#123 mirror breakdown rows
  WO-0001…WO-0018 one-way; the 27-label taxonomy (9 `wo:*` lifecycle labels plus
  the orthogonal `size:`/`risk:`/`type:`/`source:` families and the
  `budget-exhausted` / `needs-human` / `blueprint-drift` flags) ships in the
  payload and exists live; beads holds the dependency graph (`wo-####`, edges
  from the rows' `blocked by:` fields).
- Collaborators: the assembler (unbuilt) is the only thing that would *drive*
  the state machine. Today every open work-order issue sits at `wo:draft`: the
  lifecycle is declared, not driven, and label transitions are applied by hand
  when they are applied at all.
- Prompt-injection boundary (ADR-0032): the dispatched agent's prompt substrate
  is the repo-controlled `breakdown.md` row, **never** the issue body. This is
  currently enforced only by the charters' prose, because nothing dispatches.

### Charters — `factory/agents/*.md` + `factory/skills/<role>/SKILL.md` (PARTIAL)

- Responsibility: define an agent role — mission, owned stages, entry/exit
  criteria, tool grants, escalation, handoff artifact, and a routing band. Three
  exist (SWE, Reviewer, Planner, WO-0013); the full nine-role set is WO-0014.
  A two-file scheme: a dispatchable agent stub (with `name:` frontmatter) whose
  body points at the full charter skill.
- Collaborators: intended — the assembler, which would load them into a
  dispatched run.
- **Open gap, unchanged since decompose: the charters have no load path.** Claude
  Code discovers subagents under `.claude/agents/` or `<plugin-root>/agents/`;
  nothing discovers or stamps `factory/agents/`. They are inert files. They are
  kept out of `factory/templates/**` on purpose (detector E checksum-pins that
  tree and WO-0014 will churn them heavily). The assembler (WO-0005) is the
  natural owner of the load path, and the charter replays (WO-0016) presuppose
  it. No row owns it today.

### Human-gate surface — CODEOWNERS + CI (PARTIAL)

- Responsibility: make the three gates of ADR-0033 physical. `.github/CODEOWNERS`
  exists here and ships in the payload; `checks.yml` runs lint, the detector
  suite, the selftest, and the tests on every push and PR.
- Honest note: **CODEOWNERS without branch protection requests reviewers; it does
  not require them.** Branch protection needs a paid plan or a public repo, and
  this is a private free-plan repo. So all three gates are today *convention plus
  CI*, not platform controls. See *Divergences*.

### Execution half — assembler, budget guard, handoff, ledger, reports (UNBUILT)

- `assembler.yml` + claude-code-action + owner/pause/WIP guards (WO-0005);
  `budget_guard.py` + `handoff.py` + `costs.jsonl` (WO-0006); routing resolution
  (WO-0007); `validator.yml` incl. the non-authoring review job (WO-0004);
  `cost-report.yml` + monthly circuit breaker (WO-0009); `sweeps.yml` +
  intake stamping (WO-0010); gate-queue digest (WO-0017); rejection mining
  (WO-0018); design pipeline (WO-0012); charter regression replays (WO-0016).
- This is the half that makes the factory a factory. **None of it exists.** The
  PRD's headline capability — dispatch a work order, walk away, return to a
  reviewed PR — is not achievable today by any path.

## Data model

Everything is a file in git except the dispatch plane's issues/labels (GitHub)
and the beads graph (a local Dolt DB synced over a git ref).

**Typed IDs.** `PRD-####` — declared once in `prd.md` frontmatter as `id:`,
globally numbered across runs. `ADR-####` — the four-digit filename prefix under
`docs/adr/`. `WO-####` — a token on a `breakdown.md` row; the same token names
the mirrored issue and is cited by the implementing PR. Regex grammar (from
`gates.py`): `\bPRD-\d{4}\b`, `\bADR-(\d{4})\b`, `\bWO-\d{4}\b`.

**Breakdown row** (the work-order record; one physical line):

```markdown
- [ ] **WO-0005** assembler.yml + claude-code-action + guards — size:L, blocked by: WO-0002, WO-0004 (PRD-0001 §Solution) (tracker: #110)
  - Accept: <one line, the exit criterion>
```

The PRD citation and the blocking edges live **on the row line**, not a
sub-bullet — a template deviation forced by detector A, which reads *any* line
bearing a `WO-####` token as a row requiring a PRD citation.

**Lifecycle label state machine** (exactly one `wo:*` at a time, ADR-0032):

```
wo:draft → wo:prd-approved → wo:blueprint-approved → wo:ready-for-agent
         → wo:in-progress → wo:needs-review → wo:merged | wo:failed | wo:blocked
```

Orthogonal families: `size:S|M|L`, `risk:low|med|high`,
`type:feature|defect|chore|sweep|support`,
`source:validator|sentry|human|sweep`; flags `budget-exhausted`, `needs-human`,
`blueprint-drift`. Only the repo owner may apply `wo:ready-for-agent`, and per
ADR-0032 that must be an actor check inside the dispatch workflow — a label
applied by anyone else is inert. (The workflow is WO-0005; the check does not
exist yet, so the label is inert for a different reason: nothing reads it.)

**`factory.json`** (detector F's contract): `budgets_usd` maps exactly S, M, L
to positive numbers (start table, ADR-0034: ≈$5 / ≈$15 / ≈$40); `routing` maps
exactly `mechanical`, `implementation`, `architecture_review` to model ids;
`wip_cap` is a positive int; `monthly_cap_usd` is a positive number.

**`factory/manifest.json`**: `{plugin, version, files: {<rel path>: <sha256>}}`
covering every file under `factory/templates/**`. Detector E fails on a missing
file, a checksum mismatch, or a payload file absent from the map.

**`.github/labels.json`**: a JSON array of `{name, color, description}`. JSON,
not YAML — the stdlib has no YAML parser and stdlib-only is the first hard
convention.

**`docs/factory/costs.jsonl`** (PLANNED, WO-0006): append-only, one record per
run — `{wo, run_id, model, tokens, cost, outcome}`. Same discipline as
`evals/results/`: dated, never rewritten. The weekly rollup (cost per merged
order by class, acceptance, churn, escapes, MTTR, gate latency) is *derived*
from it, never stored beside it. A merged order with no ledger line is meant to
be a detector finding (G, unbuilt).

**beads**: mirrors the work-order set as `wo-####` with the rows' blocking edges.
It is a convenience for "what is ready", not a plane of record — and no detector
reconciles it against `breakdown.md` (see *Open questions*).

## Interfaces & contracts

### The checker contract (the repo's core seam for all of this)

- Input: the repo root (`pathlib.Path`).
- Output: a list of label-prefixed problem strings, e.g.
  `A: docs/features/x/breakdown.md:22 work-order row WO-0004 cites no PRD id`.
  Empty list = clean.
- Failure modes: a checker never raises on malformed input and never exits; it
  reports. The CLI prints every string and exits 1 if any. Tests assert the
  exact strings through the public interface.
- Rationale: this is `lint.py`'s existing contract. Reusing it verbatim is why
  `gates.py`, `label_sync.py`, and `factory_init.py` need no shared framework.

### `gates.run_all(root, env=None)`

- Input: repo root; optionally an env mapping (threaded to the checkers that
  read the process environment, so tests stay hermetic without mutating global
  state).
- Output: the concatenated problem strings of A, B, C, E, F.
- Failure modes: `B` returns `[]` when `GITHUB_EVENT_PATH` is unset (local runs)
  or when the payload is not a pull request; an unreadable payload is itself a
  `B:` problem, never a traceback.

### `gates.check_pr_traceability(root, env)` — detector B, the gate on every PR

- Input: the CI event payload at `GITHUB_EVENT_PATH`.
- Output: `B: PR body cites no work-order id` and/or
  `B: PR body has no Closes #N link`.
- Failure modes: **no exemptions** — every PR on the repo must carry a
  `WO-####` token and a closing keyword. This is a deliberate absolute, and it
  has a consequence the ADRs did not anticipate: a *gate-2* PR (this one — a
  blueprint/ADR/architecture PR, which by construction precedes any work order)
  cannot satisfy it. See *Divergences*.

### `label_sync.sync(root, apply=False, run=gh_runner)`

- Input: repo root; a `gh` runner (injected in tests, so no test touches the
  network).
- Output: `L:` drift strings; with `apply=True`, also force-creates each drifted
  label.
- Failure modes: a broken `labels.json` short-circuits *before* any network call;
  a missing / unauthenticated / rate-limited `gh` becomes one `L:` problem
  string, never a traceback (it runs in a sweep, where a traceback is noise).

### `factory_init.update-manifest` / `factory_init.stamp <target>`

- Input: repo root (implicit) / a target repo path.
- Output: problem strings; `factory-init: N problem(s)`.
- Failure modes: `stamp` refuses a source payload that fails detector E, and
  refuses any pre-existing destination file — no partial stamps, no overwrites.
  `update-manifest` refuses a repo missing `.claude-plugin/plugin.json` or any
  tool mirror.
- Contract with humans: **never hand-edit `factory/templates/**` or the
  manifest.** Edit the root script, re-run `update-manifest`, commit both.

### Charter contract

- An agent stub (`factory/agents/<role>.md`) carries `name:` (required for
  dispatch), `description:`, `tools:`, and `route:` — a routing **band**, never a
  model id. Its body points at the charter.
- A charter (`factory/skills/<role>/SKILL.md`) states mission, stages with
  entry/exit criteria, actions, loadout, grants, "must never", handoff artifact,
  and escalation triggers.
- Failure mode today: **nothing loads either file.** The contract is written and
  unhonoured.

### Dispatch contract (PLANNED — WO-0005; stated here because the charters
already depend on it)

- Input: a work-order issue at `wo:ready-for-agent`, applied by the owner.
- Substrate: the `breakdown.md` row and its cited `PRD-#### §section` — the
  issue body is *never* instructions (prompt-injection boundary, ADR-0032).
- Stops (all three, uncorrelated, ADR-0034): token budget by size class (80% =
  wrap-up warning, 100% = block further tool use), a max-turns cap, and the job's
  wall-clock timeout.
- Output on success: a PR citing `WO-#### (PRD-#### §…) — Closes #N` with a
  literal evidence block, plus a `costs.jsonl` line.
- Output on exhaustion: a **handoff, not a failure** — WIP committed and pushed,
  a structured comment (done/undone criteria, last state, resume instructions,
  spend), labels `budget-exhausted needs-human wo:failed`. The dispatcher then
  refuses the order until the owner clears the label: no self-retry loops.

### `make check` (stamped repos) == `checks.yml` (this repo)

- The same three commands in both places, pinned in lockstep by a unit test:
  `gates.py`, `gates.py --selftest`, `unittest discover tests` (plus `lint.py`
  here). A local green must mean a CI green.

## Stack & dependencies

- **Python 3 standard library only** — the repo's first hard convention. It is
  why the label taxonomy is JSON (no YAML parser), why link-checking is regex
  and not a graph library, and why the manifest is sha256 in the stdlib.
- **GitHub as the only service** — issues (the queue), labels (the state
  machine), CODEOWNERS (the gate surface), Actions (the detector runner and,
  later, the execution slot). It is already there and already the merge surface;
  a control-plane app is explicitly out of scope in the PRD.
- **`gh` CLI** — the only network dependency, and only for detector L and the
  (unbuilt) sweeps. Never imported by the offline suite.
- **claude-code-action** (PLANNED) — the execution slot. Deliberately the *only*
  agent-specific component, so the coding agent behind the slot stays swappable
  (PRD: "the dispatch contract is agent-agnostic").
- **beads / Dolt** — the dependency graph. Adopted at decompose (a PRD open
  question, answered there).
- **No database, no daemon, no dashboard.** The weekly report is an issue.

## Decisions & alternatives

- **Two planes with one-way mirroring** over a tracker as source of truth — a
  bidirectional sync is a second state store that drifts; ADR-0004 exists to
  prevent exactly that (ADR-0032).
- **Typed IDs + regex detectors** over a knowledge-graph database — a graph DB
  is a service to run and a schema to maintain for a solo operator; revisit only
  when link-checking measurably stops scaling (PRD out-of-scope; ADR-0032).
- **The breakdown row as prompt substrate** over the issue body — the issue body
  is attacker-writable; the row is repo-controlled and code-reviewed. This is the
  prompt-injection boundary (ADR-0032).
- **Exactly three gates** over per-stage sign-offs — more gates make the human
  the bottleneck everywhere; fewer let a bad artifact poison everything
  downstream (ADR-0033).
- **Graduation on evidence** over per-PR auto-merge exceptions — an exception is
  a permanent hole; a graduated class is a revocable one, and one escape revokes
  it (ADR-0033).
- **Three uncorrelated stops** over a token budget alone — a single stop rule
  fails in the one mode it did not model; wall-clock and max-turns catch what
  budget accounting misses (ADR-0034).
- **Exhaustion as handoff** over exhaustion as failure — a failed run that threw
  its WIP away costs the budget *and* the work (ADR-0034).
- **Routing band in the charter, model id in `factory.json`** over a `model:`
  field per charter — two routing sources of truth is precisely the drift the
  factory exists to catch (ADR-0004; breakdown Notes).
- **Checksum-pinned template payload with machine-copied tool mirrors** over
  hand-maintained copies — a second copy of `gates.py` in the payload is a
  guaranteed divergence; detector E makes hand-editing fail the build.
- **Detector L kept out of the offline suite** over one unified detector list —
  `make check` must be hermetic and identical to CI; a network call in the
  offline suite makes local green a coin flip.
- **`labels.json` over `labels.yml`** (the name in the original row) — stdlib
  has no YAML parser, and `gh label list --json` already returns this shape.
- **Detector A reads any `WO-####` line as a row** over parsing the row grammar —
  cheap and impossible to slip past, at the cost of taxing prose (below).

## Divergences: what the ADRs decided vs what exists

These are real, current, and not papered over.

1. **The three gates are not physical.** ADR-0033 says each gate is "a physical
   control, not a norm": CODEOWNERS *plus required code-owner review* for gates 1
   and 2, branch protection for gate 3. Required review and branch protection
   need a paid plan or a public repo; this is a private free-plan repo. Today all
   three gates are **convention plus CI**. CODEOWNERS is present and requests
   reviewers; nothing requires them. (The PRD lists this as an open question and
   defers it to Matt; the breakdown Notes repeat it. It remains open.)

2. **Gate-2 artifacts have not been entering via PR.** ADR-0033 gate 1/2 says
   PRDs and blueprints "enter only via a PR" and "cannot exist on main
   un-approved". In fact `prd.md`, `breakdown.md`, and ADR-0032/0033/0034 were
   pushed directly to `main`. Gate 2 has, so far, been a norm the operator kept in
   their head.

3. **Detector B has no gate-2 branch, and this PR is the first to hit it.**
   B demands a `WO-####` citation *and* a `Closes #N` on every PR. A blueprint
   PR (this artifact) implements no work order and closes no issue: it *precedes*
   work orders. So B fails this PR by design, and the honest options are to fail
   the check or to fabricate a work-order link. The former is correct. The
   detector's model — "every factory PR is a work-order PR" — is simply too
   narrow; the fix (a gate-2 branch: a PR whose diff is confined to gate-2 paths
   satisfies B by citing its `PRD-####` instead) is a real change to `gates.py`
   and needs its own work order and its own review. It is **not** made here,
   because inventing a work order to unblock myself is exactly the drift this
   factory exists to catch.

4. **Detector A cannot distinguish a row from prose.** Any line in
   `breakdown.md` carrying a `WO-####` token must also carry a `PRD-####` token,
   even inside a Notes paragraph. This has already deformed the artifact: the
   breakdown's Notes carry PRD citations mid-sentence, and one note is written
   *around* a work-order token to avoid the check. The over-broad reading is a
   conscious trade (cheap, unfoolable in the safe direction) — but it taxes prose,
   and it will keep taxing it.

5. **The lifecycle state machine is declared, not driven.** Every open
   work-order issue is at `wo:draft`. The transitions ADR-0032 specifies are
   owned by the validator and assembler workflows, which are unbuilt.

6. **`factory.json` is validated but inert.** Detector F checks the shape of
   budgets, routing, wip_cap, and the monthly cap. Nothing reads the values:
   no budget guard, no routing resolver, no circuit breaker.

7. **The charters have no load path** (see the component). Written, checked by
   structural lint, loaded by nothing.

8. **The merge gate was waived for this program.** The autorun brief records a
   one-time operator authorization to merge factory work-order PRs on CI-green
   plus an independent (non-authoring) reviewer pass. That is a recorded
   deviation from ADR-0033, not a new rule — noted here so it is not mistaken for
   the design.

## Open questions

- **Who owns the charter load path?** WO-0005 (the assembler) is the natural
  owner because it builds the dispatched run's environment, and WO-0016 (charter
  replays) presupposes it — but no row says so today. Settle when the assembler
  is implemented.
- **How does detector B admit a gate-2 PR** without becoming exemptable? A
  path-scoped branch is the obvious answer; it needs a work order, not a
  side-edit under a deadline.
- **Physical gate enforcement** — the repo goes public or Pro, or the gates stay
  convention plus CI. Operator's call (PRD open question, still open).
- **Nothing reconciles beads against `breakdown.md`.** The dependency graph is a
  third store of the work-order set, and the detector suite's coverage stops at
  the GitHub mirror. If beads drifts, no build fails. Either a detector should
  cover it or beads should be documented as strictly advisory; it is currently
  neither.
- **Budget calibration** (S≈$5 / M≈$15 / L≈$40) is a guess with no actuals
  behind it, and cannot be answered until the ledger exists (PRD open question;
  ADR-0034 assigns the estimation loop to the planner role).
- **`factory_init stamp` has never met a real product repo** — only scratch trees
  in tests. The first real stamp is where the payload's assumptions get tested.

## Requirement traceability (PRD-0001 → components)

| PRD-0001 requirement | Component | Status |
|---|---|---|
| Signals become triaged work items | sweeps + intake stamping (WO-0010) | UNBUILT |
| Work orders are dispatchable | dispatch plane + assembler (WO-0005) | PARTIAL / UNBUILT |
| Dispatch contract is agent-agnostic | breakdown row as substrate; claude-code-action confined to the execution slot | PARTIAL (contract written, slot unbuilt) |
| Hard spending limit; clean handoff | budget guard + handoff + three stops (WO-0006) | UNBUILT |
| Generation ≠ verification | non-authoring review job (WO-0004); evidence-honesty detector H (WO-0011) | UNBUILT |
| Exactly three human gates, platform-enforced | CODEOWNERS + CI (+ branch protection when available) | PARTIAL — see Divergences 1 |
| Every change traces to a work order and a requirement; a broken link fails the build | detectors A, B, C | BUILT |
| Weekly self-report; spend per requirement | cost ledger + cost-report (WO-0006, WO-0009, WO-0017) | UNBUILT |
| Charters for the stage-agent roles | three charters (WO-0013); nine-role set (WO-0014) | PARTIAL — no load path |
| Installable in a product repo | template payload + `factory_init.py` (WO-0001) | BUILT (never stamped for real) |

Every PRD requirement maps to a component. **Most of those components do not
exist yet** — which is the accurate state of this run, and the reason this table
is worth more than a design that reads as if it were finished.

## ADRs

None new. The design was decided in — and this artifact consolidates —
**ADR-0032** (factory dispatch plane: two planes, one-way mirror, typed IDs,
lifecycle labels, prompt-injection boundary), **ADR-0033** (three human gates;
graduation-not-exception; the dormant deploy gate), and **ADR-0034** (size-class
budgets, three uncorrelated stops, handoff-not-failure, one append-only ledger,
model routing bands). It also rests on **ADR-0004** (artifacts are the state),
**ADR-0021** (the `protocol.py` seam), and **ADR-0026** (the one-way tracker
mirror this plane extends).

Nothing in this consolidation met the ADR bar (hard to reverse **and** surprising
without context **and** the result of a real trade-off). The two candidates that
came closest are recorded above as open questions rather than decisions, because
neither has been decided: how detector B admits a gate-2 PR, and who owns the
charter load path.
