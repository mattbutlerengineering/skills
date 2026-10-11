# Research: actors and roles for the orchestrator feature

Date: 2026-10-10. Scope: which actors/roles well-regarded agent-orchestration
designs define, and the practices that govern the split. Builds on
`docs/features/orchestrator/idea.md` and `docs/research/orchestrator.md`
(worktree `.claude/worktrees/orchestrator-idea`); does not redo that survey.
Fetched primary sources where possible; anything secondary is marked.

## 1. Sources and what each says about roles

| # | Source (date) | Roles defined | Notes that bear on our split |
|---|---|---|---|
| S1 | Anthropic, "Building effective agents" (Dec 2024) <https://www.anthropic.com/engineering/building-effective-agents> | Orchestrator + workers; evaluator-optimizer (generator + evaluator) | Orchestrator "dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results"; fits when "you can't predict the subtasks". Evaluator fits "when we have clear evaluation criteria". Human = checkpoints: agents "pause for human feedback at checkpoints or when encountering blockers"; for coding "human review remains crucial". "Add complexity only when it demonstrably improves outcomes." |
| S2 | Anthropic, "How we built our multi-agent research system" (Jun 2025) <https://www.anthropic.com/engineering/multi-agent-research-system> | LeadResearcher, subagents, CitationAgent (a dedicated post-pass verifier) | Lead briefs each subagent with **objective, output format, tool/source guidance, task boundaries**; vague briefs caused duplicate/missed work. Explicit effort-scaling rules in the lead's prompt. Lead **saves its plan to memory** to survive truncation. "Most coding tasks involve fewer truly parallelizable tasks than research." |
| S3 | Anthropic, "Harness design for long-running application development" (2026) <https://www.anthropic.com/engineering/harness-design-long-running-apps> | Planner, generator, evaluator | Separate evaluator because agents "confidently prais[e] the work"; "tuning a standalone evaluator to be skeptical turns out to be far more tractable". Evaluator "is worth the cost when the task sits beyond what the current model does reliably solo". "Every component in a harness encodes an assumption about what the model can't do on its own" -- removed components one at a time as models improved (dropped sprints/context resets, kept planner + evaluator). |
| S4 | Claude Code agent teams docs <https://code.claude.com/docs/en/agent-teams> | Team lead, teammates (+ task list, mailbox as components, not actors) | Lead is fixed for life; no nested teams. "Two teammates editing the same file leads to overwrites" -> partition files. "Start with 3-5 teammates." Quality gates are **hooks** (`TaskCompleted`, `TeammateIdle`), not a role. Messages between agents are never the user's consent -- an agent "can't approve a permission prompt or supply consent on your behalf". Example review team: three lens-specific reviewers, lead synthesizes. Known failure: lead "starts implementing tasks itself instead of waiting". |
| S5 | Claude Code dynamic workflows docs <https://code.claude.com/docs/en/workflows> | A script holds the plan; agents are workers; adversarial verifier agents as a pattern | "No mid-run user input ... For sign-off between stages, run each stage as its own workflow." Recommended quality patterns: "independent agents adversarially review each other's findings", "verify each result". |
| S6 | Claude Managed Agents, multiagent orchestration (beta, 2026) <https://platform.claude.com/docs/en/managed-agents/multiagent-orchestration> | Coordinator (primary thread) + roster of specialist agents; optional **advisor** model | Anthropic's own example roster for engineering: "You coordinate engineering work. Delegate code review to the reviewer agent and test writing to the test agent." Delegation one level deep, <=25 child threads. Advisor = consult a stronger model "at key moments such as planning or a final review" while the primary does the work. Credentials scoped per roster agent. |
| S7 | Cognition, "Don't Build Multi-Agents" (2025-06-12) <https://cognition.com/blog/dont-build-multi-agents> | Single-threaded linear agent (baseline) | "Share context, and share full agent traces"; "actions carry implicit decisions", "conflicting decisions carry bad results". Parallel subagents with divided subtasks = anti-pattern. |
| S8 | Cognition, "Multi-Agents: What's Actually Working" (2026-04-22) <https://cognition.com/blog/multi-agents-working> | Manager + child agents; clean-context reviewer; "smart friend" escalation | Works: reviewer "best when the coding and review agents do not share any context beforehand" (~2 bugs/PR found); "writes stay single-threaded and the additional agents contribute intelligence rather than actions"; "map-reduce-and-manage". Fails: managers over-prescriptive; "agents assume they share state with their children when they don't"; children don't report discoveries back by default; swarms "mostly a distraction". |
| S9 | OpenAI Agents SDK, multi-agent <https://openai.github.io/openai-agents-python/multi_agent/> and HITL <https://openai.github.io/openai-agents-python/human_in_the_loop/> | Manager (agents-as-tools), triage (handoff router), specialists | Manager pattern when "one agent should own the final answer ... or enforce shared guardrails in one place". HITL = **approval gate on tool calls** (`needs_approval`), surfaced as interruptions, durable `RunState`, resume; "Possession of a run ID or decision ID is not authorization." Human is not an agent. |
| S10 | LangChain/LangGraph multi-agent <https://docs.langchain.com/oss/python/langchain/multi-agent> and interrupts <https://docs.langchain.com/oss/python/langgraph/interrupts> | Main agent + subagents-as-tools (supervisor), handoffs, router, custom workflow | "Start with a single agent if possible." "At the center of multi-agent design is context engineering." HITL = **pause** via `interrupt()` + checkpointer + `Command(resume=...)`; not a node/actor. |
| S11 | Google ADK workflows <https://adk.dev/workflows/> and human input <https://adk.dev/graphs/human-input/> | Coordinator agent with sub-agents; sequential/parallel/loop workflow agents | HITL two ways: a model-free **human-input node** that yields `RequestInput` ("makes the pause deterministic"), and **tool confirmation** (`requireConfirmation`) for yes/no approvals. |
| S12 | Microsoft Magentic-One (Nov 2024) <https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/> | Orchestrator + WebSurfer, FileSurfer, Coder, ComputerTerminal | Orchestrator keeps a **Task Ledger** (facts, guesses, plan; outer loop) and a **Progress Ledger** (per-step progress, assignment, "task complete? progress being made?"); stall count > 2 -> replan. Design to "pause and seek human input before proceeding with ... high-risk actions." |
| S13 | Gas Town (Yegge, 2026) README <https://github.com/steveyegge/gastown>, glossary <https://github.com/steveyegge/gastown/blob/main/docs/glossary.md> | Mayor (coordinator/chief of staff), Polecats (workers, ephemeral sessions, worktree each), **Refinery** (per-rig merge queue), Witness (per-rig lifecycle/stuck detection), Deacon (town-wide watchdog), Dogs/Boot (maintenance), Crew (long-lived named agents; the human's workspace), Overseer (human, escalation tier only) | Refinery "batches their merge requests and runs verification gates", bisecting queue; "polecats never push directly to main". Escalation chain Deacon -> Mayor -> Overseer. 7+ roles for 20-30 concurrent agents; heise calls it alpha-ish, cost flagged (see survey). |
| S14 | CrewAI hierarchical process <https://docs.crewai.com/en/learn/hierarchical-process> | Manager agent + crew | Manager "coordinates the workflow, delegates tasks, and validates outcomes" -- the docs do not say how validation works; one LLM both dispatches and validates. |
| S15 | MetaGPT (ICLR 2024) <https://arxiv.org/html/2308.00352v7>; ChatDev <https://arxiv.org/abs/2307.07924> | PM, Architect, Project Manager, Engineer, QA (MetaGPT); specialized agents across design/code/test phases (ChatDev) | SOP roles hand off **structured documents**, not chat; publish-subscribe message pool so each role reads only what it needs; executable test feedback (+4-5% pass@1). Causal link to less hallucination is the authors' argument, not isolated. |
| S16 | Conductor (Melty Labs) Mac app, secondary <https://www.conductor.build/workflows/run-parallel-claude-codes>, <https://www.morphllm.com/conductor-ai-coding> | n/a (product) | Relevant only for naming: "Conductor" is an existing, funded product that runs parallel Claude Code agents in worktrees. |

## 2. Role comparison

Columns are the functions a batch-of-issues orchestrator needs. "Same" = the
coordinator does it itself; "hook/system" = not an agent role.

| System | Coordinator name | Worker | Reviewer / verifier | Merge / integration | Health / stuck watch | Human modeled as |
|---|---|---|---|---|---|---|
| Anthropic patterns (S1) | Orchestrator | Workers | Evaluator (separate LLM) | n/a | n/a | checkpoint pause |
| Anthropic research (S2) | Lead agent | Subagents | CitationAgent (post-pass) | Lead synthesizes | n/a | n/a |
| Anthropic harness (S3) | (script) + Planner | Generator | Evaluator, separate, tuned skeptical | n/a | n/a | n/a |
| Claude agent teams (S4) | Team lead | Teammates | optional reviewer teammates; gates via hooks | none (partition files) | idle notifications/hooks | direct operator; never via agent messages |
| Claude workflows (S5) | Script | Agents | adversarial verifier agents | n/a | runtime retries stalls | none mid-run; separate workflows per sign-off |
| Managed Agents (S6) | Coordinator | Roster agents | reviewer roster agent (Anthropic's example); advisor model | n/a | n/a | n/a |
| Cognition 2026 (S8) | Manager | Child agents (single writer) | Clean-context reviewer | Manager | n/a | n/a |
| OpenAI SDK (S9) | Manager / triage | Specialists | n/a | n/a | n/a | approval gate on tool calls |
| LangGraph (S10) | Supervisor / main agent | Subagents | n/a | n/a | n/a | interrupt pause |
| Google ADK (S11) | Coordinator | Sub-agents | (generator-critic loop pattern) | n/a | n/a | input node or tool confirmation |
| Magentic-One (S12) | Orchestrator (two ledgers) | 4 specialists | Orchestrator self-checks progress | n/a | Orchestrator stall counter | pause before high-risk actions |
| Gas Town (S13) | Mayor | Polecats | Refinery verification gates | **Refinery** (dedicated) | Witness + Deacon + Dogs | Overseer at end of escalation chain |
| CrewAI (S14) | Manager | Crew | Manager (same agent) | n/a | n/a | n/a |
| MetaGPT (S15) | SOP (no runtime coordinator) | Engineer | QA Engineer | n/a | n/a | n/a |

## 3. What recurs, and the best practices

1. **Coordinator + workers is universal.** Every source has exactly one
   coordinator per scope. Agent teams, Managed Agents and Cognition all
   forbid or avoid nesting coordinators (one level deep; no nested teams).
2. **A separate, clean-context verifier is the most consistently endorsed
   extra role.** Anthropic (S1 evaluator, S2 CitationAgent, S3 evaluator,
   S5 adversarial verifiers, S6 reviewer in its own engineering example)
   and Cognition (S8) independently say self-review by the author or the
   coordinator is weak and a fresh-context reviewer catches real defects.
   CrewAI's manager-validates-own-dispatch is the counter-example with no
   evidence behind it. S3 adds the caveat: the evaluator earns its cost
   only where the task is beyond reliable solo capability.
3. **A dedicated merge/integration role is rare.** Only Gas Town has one
   (Refinery), and it exists because 20-30 polecats merge concurrently.
   Everyone else either avoids concurrent writes (single writer, file
   partitioning) or lets the coordinator integrate. Note the Refinery is a
   *queue processor* with verification gates -- i.e. roughly what GitHub's
   merge queue already is. Gas Town also has two separate health roles
   (Witness, Deacon) -- the most roles of any source, and the one flagged
   for cost and alpha quality.
4. **The human is never modeled as an agent.** It is an approval gate on a
   tool call (OpenAI, ADK tool confirmation), a durable pause/interrupt
   (LangGraph, ADK input node, Workflows' "run each stage as its own
   workflow"), a checkpoint (Anthropic S1, Magentic-One), or the top of an
   escalation chain (Gas Town Overseer). It *is* the principal: Claude
   Code says agent messages can never carry the user's consent, and OpenAI
   says holding a decision ID is not authorization. So "Owner as actor" is
   right for a PRD's actor list (it owns authority), but mechanically the
   Owner is reached through a durable question queue, not a peer agent.
5. **Coordinator briefing discipline** (S2, S4): objective, output format,
   tools/sources, boundaries, plus effort scaling; children do not share
   the coordinator's state (S8) -- the brief must be self-contained.
6. **Durable coordinator state** (S2 plan-to-memory, S12 two ledgers,
   S13 Beads): the coordinator's plan and progress live outside its
   context window.
7. **Structured artifact handoffs beat chat** (S15, S7's trace-sharing).

Anti-patterns named by the sources:
- Parallel writers to the same files / shared writes (S4, S7, S8).
- Coordinator doing the work itself instead of waiting (S4).
- Coordinator also being the reviewer of what it dispatched (implied by
  S3/S8; CrewAI shape).
- Over-prescriptive managers; assuming children share state (S8).
- Swarms / free negotiation between agents (S7, S8).
- Role sprawl: many standing roles add cost and coordination with no
  evidence of benefit at small scale (S4 team-size guidance, S3 strip
  components one at a time, Gas Town's 7+ roles for 20-30 agents).
- Treating an agent's relayed message as human approval (S4, S9).

## 4. Fit with what this repo already has

- **A Reviewer role already exists**: `factory/charters/reviewer/` (one of
  nine charters in `factory/CHARTERS.md`), and ADR-0036 makes an
  *independent, non-authoring* review that re-executes verification a
  load-bearing merge condition. The `review` skill exists too. So a
  "Reviewer actor" is not new design -- the question is only whether the
  Conductor dispatches it.
- **GitHub merge queue is already chosen** (ADR-0070), not yet switched on;
  it does what Gas Town's Refinery does (test each PR against main + the
  PRs ahead; eject failures).
- Nine charter roles already exist; the PRD should not add standing roles
  beyond what the batch layer genuinely needs.

## 5. Recommendation

**Confirm Owner / Conductor / Worker, with two revisions and one naming change.**

1. **Keep three actors, but give review an explicit slot: Reviewer as a
   dispatched role, not a fourth standing actor.** Evidence for a separate
   clean-context reviewer is the strongest in the survey (S1, S2, S3, S5,
   S6, S8), and ADR-0036 already requires it for agent merges. Evidence
   against making the Conductor review: Cognition's single-writer +
   clean-context finding and Anthropic's "standalone evaluator is far more
   tractable". So the PRD should state: the Conductor *never reviews or
   verifies* its own dispatched work; for each item it dispatches the
   existing Reviewer charter (fresh context, non-authoring, re-executes
   verification) as a Worker-kind agent, and only a Reviewer pass plus
   green checks lets an item enter the merge order. Model it as a role a
   Worker slot takes, so the actor list stays three and no new charter is
   written. Per S3, allow skipping it only where ADR-0036 does not require
   it (it currently always does for merges, so: always).
2. **No Merger/Integrator actor.** Gas Town is the only source with one,
   at 20-30 concurrent writers; at this repo's scale (wip_cap batches) the
   coordinator-orders-merges shape of every other source fits. Split the
   work honestly instead: the Conductor *decides* merge order and does the
   single-threaded writes to shared files (number/version reservation,
   manifest regen, ADR renumber) -- the Cognition single-writer rule -- and
   GitHub's merge queue *executes and verifies* integration (the Refinery
   function), once ADR-0070 is switched on. Revisit a dedicated
   integration role only if conflict-resolution work becomes a measurable
   share of the Conductor's spend.
3. **Keep GitHub as a system, not an actor.** No source models CI or a
   merge queue as an agent; Gas Town's Refinery is an agent only because
   Gas Town has no hosted queue. Name it in the PRD's "Systems" list
   (CI, merge queue, issues, labels) with the gates it enforces.
4. **Owner: keep as the principal actor, but specify the channel.**
   Sources model the human as gate/pause, never as a peer agent. The PRD
   should say the Owner is reached only through a durable, one-at-a-time
   decision queue owned by the Conductor (OpenAI RunState / LangGraph
   checkpoint shape) and that no agent message counts as Owner consent
   (Claude Code permissions doc; matches the merge-permission memory).
5. **Name: prefer "Conductor" over "Orchestrator", with a caveat.**
   "Orchestrator" is the generic industry term (S1, S12) and collides with
   this repo's own prose ("autorun orchestrates a full run", CONTEXT.md)
   and with Claude Code's desktop "orchestrator" -- it would blur which
   layer is meant. "Conductor" is distinct in-repo and accurately implies
   *directs, does not play* (the S4 anti-pattern of the lead doing the
   work). Caveat: Conductor (conductor.build) is a funded product that
   runs parallel Claude Code agents, so use it as the role name inside the
   plugin and CONTEXT.md, and avoid it as a standalone product/skill name
   if the plugin is ever marketed (e.g. skill `batch` or `conduct`, role
   "Conductor"). Industry-neutral alternatives if the collision matters:
   "Coordinator" (Anthropic Managed Agents' term) or "Lead".
6. **Borrow two practices into the Conductor's definition**: a durable
   two-part ledger (batch plan + per-item progress, Magentic-One / Beads)
   with a stall rule that escalates to the Owner queue; and a brief
   template per Worker (objective, output, tools, boundaries, model,
   effort, context budget -- S2 plus the idea's model/effort control).
   Leave stuck-agent detection (Witness/Deacon) to the Conductor's ledger,
   not new roles.

## Couldn't verify
- Gas Town's Overseer authority and how merge failures reach the human
  (README/glossary silent).
- ChatDev's exact role list (abstract only fetched).
- Whether Cognition's reviewer finding (~2 bugs/PR) holds outside Devin.
