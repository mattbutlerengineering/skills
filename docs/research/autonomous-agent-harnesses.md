# Autonomous coding agent harnesses: survey and shortlist

Research note, 2026-09-20/21. Question: how do OpenHands, SWE-agent, Aider,
and claude-flow bound, budget, sandbox, recover from failure, and hand off
unattended runs — and which of those mechanics beat this factory's own
ADR-0034 budget/stop/handoff design or the assembler's dispatch path? Primary
sources only (project repos, docs sites, and open issues/PRs where they carry
the load-bearing design detail); quotes below were fetched and are attributed
per source, not recalled from training-time familiarity with these projects
— several have moved fast enough since this model's training cutoff that a
from-memory claim would be unreliable (see "Couldn't verify").

## What the factory already has

Every dispatched work order carries a **dollar-anchored budget by size class**
(S ≈ $5, M ≈ $15, L ≈ $40 — ADR-0034) and is bounded by **three uncorrelated
stops**: a token-budget hook (80% triggers a wrap-up warning, 100% blocks
further tool use), a max-turns cap, and the job's wall-clock timeout.
Exhaustion is explicitly **a handoff, not a failure mode**: the run commits
and pushes WIP, writes a structured handoff (done/undone acceptance criteria,
last state, resume instructions, spend), and labels the order
`budget-exhausted needs-human wo:failed` — the dispatcher refuses to retry it
until the owner clears the label. Every run appends
`{wo, run_id, model, tokens, cost, outcome}` to an append-only cost ledger,
and a monthly circuit breaker pauses dispatch repo-wide when spend crosses a
cap. ADR-0034's own opening cites the same pressure these tools cite: "a
single runaway loop can spend a month's budget overnight."

## OpenHands

**What it is.** An open-source "AI software engineer" platform; V1 replaces
the term "runtime" with "sandbox." Sources:
<https://docs.openhands.dev/openhands/usage/sandboxes/overview>,
<https://github.com/OpenHands/software-agent-sdk/pull/3845>,
<https://github.com/OpenHands/software-agent-sdk/issues/2406>.

**Core mechanisms.**

- **Per-run budget with a moving baseline, not a lifetime cap.** PR #3845
  (merged design) captures "a cost baseline at the start of each
  `run()`/`arun()` (alongside `iteration = 0`)" and measures spend *since*
  that baseline — so "a single prompt spanning multiple `run()` calls
  (confirmation mode, pause/resume) can spend up to N × `max_budget_per_run`
  total, exactly mirroring how the iteration cap behaves across those
  calls." Exhaustion halts with a typed error: `status: error, error code:
  MaxBudgetReached, error detail: Agent reached maximum budget limit
  ($1.0000); accumulated cost $5.0000` — the conversation transitions to
  `ERROR` via the same path as `MaxIterationsReached`.
- **Sub-agents inherit the parent's remaining budget, not the full
  configured amount.** PR #3845, verbatim: "Sub-agents inherit the parent's
  **remaining** budget (explicit `is not None` check so an exhausted `0.0`
  is honored rather than falling through)." A parent with a $7 cap that has
  spent $2 hands a spawned sub-agent $5, and an exhausted parent hands its
  children a hard $0.
- **No graceful termination yet — it's an open proposal, not shipped
  behavior.** Issue #2406 states plainly what happens today: "The run loop
  in `local_conversation.py` fires a `ConversationErrorEvent` with
  `MaxIterationsReached` and sets status to `ERROR`" with "zero visibility
  into how many steps it has left," so "all the work done up to that point
  is wasted — the instance scores as a hard error." The proposed fix
  (Option B) would inject, near the limit: "`[SYSTEM] You are about to
  reach the maximum number of steps allowed. This is your FINAL step.
  Provide your best answer NOW based on everything you have gathered so
  far.`" The issue does **not** propose resumable checkpoints or a
  structured handoff — only a better last turn inside the same run.
- **Sandbox isolation is a deployment choice, not agent-managed.** Docker
  sandbox ("good isolation from your host machine") is the recommended
  default; a process sandbox trades isolation for speed ("no container
  isolation"); a remote sandbox targets managed deployments. Selected via
  `RUNTIME`/sandbox config, not something the agent negotiates mid-run.

## SWE-agent

**What it is.** A research-lineage coding-agent framework (SWE-bench's
reference agent), config-driven, with `SWE-ReX` as its separately-packaged
sandboxed execution layer. Source: <https://swe-agent.com/latest/> and
<https://swe-agent.com/latest/usage/competitive_runs/>.

**Core mechanisms.**

- **A flat per-instance dollar cap, and an explicit statement of why one is
  necessary.** `agent.model.per_instance_cost_limit` (settable via
  `--agent.model.per_instance_cost_limit=2.00` or in `config.yaml`) is, in
  the docs' own words, "the simplest setting to keep cost in check" —
  "without limiting cost, the average cost will also converge to infinity,
  as the agent will never stop iterating." A cost-conservative recommended
  pairing is "a $1 instance limit or lower and a turn count limit of 50."
  Setting the cost limit to `0` disables cost tracking in favor of
  `per_instance_call_limit`, a pure turn cap.
- **Docker as the default sandbox**, with a documented memory-pressure
  knob (`--instances.deployment.docker_args=--memory=10g`) rather than a
  cost/step relationship — memory limits protect the host, not the budget.
- **What happens at the limit is not documented** in the pages fetched for
  this survey (see "Couldn't verify") — no quoted behavior for
  partial-result reporting, retry, or handoff was found.

## Aider

**What it is.** A terminal-native pair-programming CLI, git-centric.
Source: <https://aider.chat/docs/config/options.html>.

**Core mechanisms.**

- **No cost/budget limit of any kind.** The options reference has no dollar
  cap, no spend ceiling, and nothing analogous to `per_instance_cost_limit`
  or `max_budget_per_run`. The only bounded resource is *context*:
  `--max-chat-history-tokens` ("soft limit on tokens for chat history,
  after which summarization begins") and `--map-tokens` for the repo map,
  which summarizes rather than stops.
- **Every edit is its own commit.** Auto-commit is on by default
  (`--auto-commits`, "Enable/disable auto commit of LLM changes (default:
  True)"); `--dirty-commits` covers a dirty starting tree. There is no
  batching, no end-of-run handoff artifact — the git history *is* the
  resumable state, one edit at a time, and `--no-auto-commits` exists
  specifically for squash-merge workflows that don't want that granularity.
- **"Autonomous" means unattended confirmation, not unattended budgeting.**
  `--yes-always` ("Always say yes to every confirmation") plus
  `--message`/`--exit` for scripted single-shot invocation is the entire
  unattended-mode surface. Nothing stops or reports on a runaway session
  except the human closing the terminal.

## claude-flow (now ruflo)

**What it is.** A multi-agent orchestration layer over Claude Code; the
project has been renamed from `claude-flow` to `ruflo`
(<https://github.com/ruvnet/ruflo> — "The original agent harness... adaptive
memory, self-learning intelligence, federation"). This rename happened
recently enough that most public references (including the issue text this
survey was seeded from) still say "claude-flow"; treat the two names as the
same lineage. Source: <https://github.com/ruvnet/ruflo>.

**Core mechanisms.**

- **Per-agent token budget, dashboard-visible, enforcement unverified.** The
  project references a live dashboard (`goal.ruv.io/agents`) that surfaces
  each spawned agent's "token budget" as a tracked field. The fetched
  content asserts the field exists and is monitored; it does not document
  what happens at zero (no quoted exhaustion behavior — flagged below).
- **A WASM sandbox mode** ("local WASM sandbox (rvagent)") is offered as
  one execution mode, alongside others not detailed in what was fetched.
- **Adaptive replanning instead of blind retry on failure.** Quoted
  directly: "When an action fails or new info arrives, the planner re-runs
  A\* from the current state instead of restarting. Failures become
  learning, not loops." This is a materially different philosophy from
  ADR-0034's "no self-retry loops" — ruflo's planner is designed to
  *correct course autonomously*, where the factory deliberately refuses a
  budget-exhausted order until a human clears it.
- **Cross-session memory persistence** ("Save and restore agent memory
  across sessions" via an "RVF plugin") supports resuming a swarm's state,
  but the fetched material does not describe this as a *budget-exhaustion*
  handoff specifically — it reads as general session continuity.

## Shortlist

| # | Mechanism (source) | Verdict | Own ADR? |
|---|--------------------|---------|----------|
| 1 | Sub-agent remaining-budget inheritance (OpenHands) | **Adapt (deferred)** | Yes, if pursued |
| 2 | Graceful final-step termination message (OpenHands, proposed) | **Reject — already shipped, better** | — |
| 3 | Flat per-instance dollar/turn cap (SWE-agent) | **Reject — already shipped, better** | — |
| 4 | Per-edit auto-commit as a resumability primitive (Aider) | **Reject — already true** | — |
| 5 | Confirmation-only "autonomous mode", no spend bound (Aider) | **Reject** | — |
| 6 | Live per-agent budget-remaining dashboard field (ruflo) | **Adapt** | No — extend `dashboard.py` |
| 7 | Adaptive replanning on failure instead of human handoff (ruflo) | **Reject, deliberately** | — |
| 8 | Agent-managed Docker/WASM sandbox as the execution boundary (OpenHands, SWE-agent, ruflo) | **Not applicable** | — |

### Rationales

**1. Sub-agent remaining-budget inheritance — Adapt, deferred.** This is the
one mechanism found in this survey with no factory equivalent: OpenHands
propagates a shrinking budget ceiling to spawned sub-agents rather than
giving each a fresh allowance, closing an obvious abuse path (a parent that
spawns children to reset its own cap). The factory's ADR-0034 budgets are
per-*work-order*, and the assembler dispatches one agent per order — there
is no in-repo notion yet of one dispatched agent recursively spawning
metered sub-work under the same order (this session's own use of forked
subagents is a Claude Code harness feature, outside the ledger entirely, not
an assembler-managed pattern). Worth an ADR only when the factory actually
grows recursive dispatch under one work order; recording the mechanism now
so it isn't reinvented worse. Evidence: PR #3845 (OpenHands/software-agent-sdk).

**2. Graceful final-step termination — Reject, already shipped and
stronger.** OpenHands' issue #2406 is an *open proposal* for a mechanism the
factory has shipped since ADR-0034: a warning at 80% of budget so the agent
can wrap up, well before the hard stop. The factory's version is also more
capable — it triggers a structured handoff (down to resume instructions and
spend), not just "give your best answer now" inside the same context.
Recorded as convergent evidence the factory's original design anticipated a
gap this ecosystem is still open-issue-tracking. Evidence: issue #2406
(OpenHands/software-agent-sdk).

**3. Flat per-instance cost/turn cap — Reject, already shipped and
stronger.** SWE-agent's own stated rationale — "without limiting cost, the
average cost will also converge to infinity" — is the identical claim
ADR-0034 opens with (8090's AI spend tripling). The mechanism itself is
strictly simpler than the factory's: one dollar figure and one turn count,
no size classing, no ledger, no cross-run rollup, no circuit breaker. Nothing
to adopt; the convergence is useful as independent confirmation the
factory's premise is industry-standard, not overcautious. Evidence:
<https://swe-agent.com/latest/usage/competitive_runs/>.

**4. Per-edit auto-commit — Reject, already true of the factory's own
Implement discipline.** Aider treats git history itself as the resumable
state, one LLM edit at a time. The factory's own Implement-stage convention
(observed directly in this repo's own maintenance-run breakdowns) already
commits at each work-item boundary with its own manifest regeneration where
needed — finer-grained than a whole work order, coarser than Aider's
per-edit, but serving the identical purpose (a bisectable, resumable trail).
Nothing to import.

**5. Confirmation-only autonomy — Reject.** `--yes-always` removes the
human from *approval* but adds no spend bound at all — the failure mode
ADR-0034 exists to prevent (a runaway loop overnight) is entirely
unaddressed in Aider's own docs. Not a design to learn from; recorded so a
future survey doesn't re-open this question having mistaken "autonomous
mode" language for a budget mechanism.

**6. Live per-agent budget-remaining field — Adapt.** The factory computes
cost only after the fact (the weekly ledger rollup, ADR-0034); nothing
today shows a dispatched agent's remaining budget while it is still running.
A dashboard field — remaining budget at the last known checkpoint, derived
from the ledger's own writes rather than a new state source — is a small,
ADR-0004-safe extension of the existing `dashboard.py` rather than new
infrastructure. Not worth a standalone ADR: it's an operational
nice-to-have, not a decision. Evidence: `goal.ruv.io/agents` field
description, ruvnet/ruflo README.

**7. Adaptive replanning on failure — Reject, deliberately, and this is the
survey's most load-bearing finding.** Ruflo's stated philosophy — "failures
become learning, not loops," re-running its planner from the current state
autonomously rather than restarting — is precisely the shape of autonomy
ADR-0034's own opening line warns against: "a single runaway loop can spend
a month's budget overnight." The factory's explicit design choice is the
opposite: a budget-exhausted order **must** stop, and the dispatcher
**refuses to retry it until a human clears the label** — no self-directed
course-correction. This is not an oversight to fix; it's the point. Recorded
as a Reject-and-say-why so the next survey doesn't propose "smarter retry"
without confronting the rationale it would be overriding. Evidence:
ruvnet/ruflo README (quoted above) vs. ADR-0034.

**8. Agent-managed sandbox as the execution boundary — Not applicable.**
OpenHands, SWE-agent, and ruflo all assume the harness itself provisions and
tears down an isolated execution environment (Docker, process, WASM) per
run. The factory's dispatch shape is structurally different: `assembler.yml`
runs the dispatched agent inside a GitHub Actions runner, whose isolation is
already provided by Actions itself (one ephemeral VM per job), and the
agent's repo-write surface is bounded by the PR/branch-protection gates
(ADR-0033/ADR-0036), not by a sandbox the agent negotiates. There is no
adoption question here — the two designs solve isolation at different
layers and neither generalizes to the other.

## Couldn't verify

- **SWE-agent's exact behavior at the cost/turn limit** — whether the run
  reports partial results, exits cleanly, or errors out — was not stated in
  the pages fetched (`usage/competitive_runs/`); the `reference/agent_config/`
  and `reference/model_config/` pages likely have it but were not read for
  this survey.
- **Ruflo's budget enforcement at zero** — the dashboard field's existence
  is confirmed; what happens when an agent's tracked budget reaches zero
  (hard stop, warning, nothing) was not found in the fetched README/wiki
  content.
- **Ruflo vs. claude-flow naming** — the rename from `claude-flow` to
  `ruflo` was inferred from the current canonical repo's own description
  ("The original agent harness") rather than from a dated changelog entry;
  the exact rename date was not captured, and several third-party forks
  still under the `claude-flow` name were not distinguished from the
  canonical project for this survey.
- **OpenHands' remote-sandbox isolation model** — named in the sandbox
  overview page but not detailed (it "operates in external environments for
  managed deployments"); no further specifics were fetched.
- **Fetch-tool caveat.** Pages were retrieved via a summarizing fetch tool;
  every quoted phrase above is reproduced as that tool returned it, and was
  not independently re-verified against raw file/page source the way the
  spec-driven-sdlc survey's quotes were (that survey explicitly re-grepped
  raw text; time budget for this one did not allow the same second pass).
  Treat quotes here as reliable in substance, slightly lower-confidence on
  exact byte-for-byte wording than the spec-driven-sdlc precedent.

## Primary sources

- OpenHands: <https://docs.openhands.dev/openhands/usage/sandboxes/overview>,
  <https://github.com/OpenHands/software-agent-sdk/pull/3845>,
  <https://github.com/OpenHands/software-agent-sdk/issues/2406>
- SWE-agent: <https://swe-agent.com/latest/usage/competitive_runs/>,
  <https://swe-agent.com/latest/>
- Aider: <https://aider.chat/docs/config/options.html>
- ruflo (claude-flow): <https://github.com/ruvnet/ruflo>
