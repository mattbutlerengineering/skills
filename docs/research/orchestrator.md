# Research: would an ORCHESTRATOR help the owner's workflow?

Research note, 2026-10-10. Input for an idea brief in `mattbutlerengineering/skills`.
Scope: research only, not a design. Sources fetched this session unless marked.

Owner's problem (as stated): coordinating several sessions/issues at once
(research -> decide -> build -> merge in order, resolving cross-PR conflicts
such as version bumps, ADR numbers, manifest), and controlling which model and
how much context each piece of work gets. Today this happens only inside one
long interactive Claude Code session driven by `/goal`.

Why now (as stated): issue volume, plus new Claude Code capabilities.

Strength tags used below:
- **M-strong**: measured, primary source, large n or controlled
- **M-weak**: measured, but vendor telemetry, single run, secondary summary, or n=1
- **A**: anecdote / practitioner report / docs claim with no measurement
- **1P**: first-party evidence from this repo (git log, gh, memory notes)

---

## 1. What orchestrators exist (2025-2026)

### Claude Code native (all fetched from code.claude.com docs, 2026-10-10)

The docs page "Run agents in parallel" (<https://code.claude.com/docs/en/agents>)
now lists **five** ways to run work concurrently, plus three helpers:

| Surface | Who holds the plan | Status | Relevant limits |
|---|---|---|---|
| Subagents (Agent tool) | Claude, turn by turn | GA | per-call `model`, `effort`, `isolation: worktree`; results land in caller context |
| Agent view (`claude agents`) | You | Research preview | background sessions, each moves into its own worktree before editing |
| Agent teams | A lead agent | **Experimental, off by default** | shared task list + SendMessage; **teammates are NOT worktree-isolated** ("partition the work so each teammate owns a different set of files") |
| Dynamic workflows (Workflow tool) | **A script** | Research preview, all paid plans | up to 16 concurrent agents (configurable to 256), 1,000 agents/run, per-stage model, resumable in-session; **"No mid-run user input ... For sign-off between stages, run each stage as its own workflow"** |
| Projects (claude.ai/code threads) | Claude, over days/weeks | Public beta (Pro/Max) | cloud threads, keeps running with your machine off |

Helpers: worktrees; **cross-session messaging** (list/message your other
sessions locally, on other machines, or in the cloud); `/batch` (5-30
worktree-isolated subagents for one large change). Routines run a session on a
cron in the cloud ("not in parallel on your machine").

Source: <https://code.claude.com/docs/en/workflows> — "A workflow moves the plan
into code ... Claude's context holds only the final answer." Workflows can be
shipped inside a plugin (`workflows/` dir, namespaced `/plugin:name`) and take
`args`. Cost note from the same page: a run that schedules >25 agents or >1.5M
projected tokens shows a `Large workflow` warning (advisory only).

Gap found (open feature request, no maintainer reply):
<https://github.com/anthropics/claude-code/issues/95190> (2026-09-17) — the
desktop orchestrator's `spawn_task` "chips" accept only prompt/title/tldr/cwd;
**no model or effort picker**, so every spawned session inherits the
orchestrator's (expensive) model. Workarounds double the turns. This is exactly
the owner's "control which model each piece gets" pain, reported by others.

### Third-party orchestrators over Claude Code / other CLIs

| Tool | Shape | Notes / source |
|---|---|---|
| Gas Town (Steve Yegge) | Go + tmux, 20-30 agents, roles (Mayor = coordinator, Polecats = workers, Refinery = merge, Witness, Deacon...), state in **Beads** + git hooks | Released 2026-01-01, v1.0 since; heise calls it alpha-ish, sources flag heavy API cost. <https://www.heise.de/en/background/Full-Control-Gas-Town-Orchestrates-Ten-or-More-Coding-Agents-11178824.html>, <https://pkg.go.dev/github.com/steveyegge/gastown>. **This repo already uses Beads**, so Gas Town is the nearest relative. |
| ruflo (ex claude-flow) | swarm meta-harness, A* replanning, per-agent token budget on a dashboard | Already surveyed in `docs/research/autonomous-agent-harnesses.md` (budget enforcement unverified; adaptive replanning rejected deliberately). |
| Conductor | Mac app, workspace -> diff review -> PR | <https://agentsroom.dev/it/blog/best-multi-agent-coding-tools> (secondary) |
| Claude Squad, Crystal | terminal / desktop worktree managers | same roundup; little detail |
| Sculptor (Imbue) | each agent in its own container instead of a worktree | <https://agentsroom.dev/ja/blog/best-multi-agent-coding-tools> |
| vibe-kanban | kanban board dispatching agents into worktrees | original company reportedly shut down Apr 2026, community-maintained (<https://aiidelist.com/ide/vibe-kanban>, unverified) |
| T3 Code "Orchestrator V2" | multi-thread orchestrator UI over Claude Code/Codex | active issues: renders a Claude workflow as a plain subagent, drops phases (<https://github.com/pingdotgg/t3code/issues/15448>) |
| herdr, rondoflow, Pixel Agents, Foremerge | small Show HN orchestrators / dashboards (last 30 days) | Foremerge: agents publish intent+scope before editing to catch "intent conflicts" (<https://github.com/naw103/foremerge>) |
| "Chief of Staff" pattern | one long-lived verifying session + short-lived worker sessions + external board as memory | <https://asyncdot.com/blog/chief-of-staff-pattern-orchestrating-claude-code-sessions/> |

### Hosted async agents
GitHub Copilot coding agent (issue -> PR, GitHub-native review), OpenAI Codex
cloud (several long-running tasks, isolated worktrees), Cursor background
agents (remote isolated envs), Devin ("Managed Devins": manager splits work,
child Devins in own VMs). Sources are mostly comparison blogs
(<https://radar.firstaimovers.com/claude-code-vs-codex-vs-cursor-vs-copilot-2026.md>);
treat feature claims as secondhand. All of them are **issue-in, PR-out** —
none sequences research -> decision -> build -> ordered merge across PRs.

### Model routing
- RouteLLM (LMSYS, 2024): trained routers cut cost >85% on MT-Bench at ~95%
  of GPT-4 quality; only 35-46% on MMLU/GSM8K. <https://lmsys.org/blog/2024-07-01-routellm/>.
  **No coding-agent measurement found.**
- Practitioner warning: cost-only routing on a coding assistant led to
  hallucinated API endpoints while dashboards looked fine
  (<https://tianpan.co/blog/2026-04-14-quality-aware-model-routing>, A).
- Cognition: "smart friend" escalation works "when both models are strong";
  a weak primary sets the ceiling (<https://cognition.com/blog/multi-agents-working>).
- In-repo: `factory.json` already routes by band (mechanical = Haiku 4.5,
  implementation = Sonnet 5, architecture_review = Fable 5) and work-queue
  applies it per work order. No eval yet shows the band choice is right.

---

## 2. Measured evidence

| # | Claim | Source | Strength |
|---|---|---|---|
| E1 | Agents use ~4x the tokens of chat; multi-agent ~15x | Anthropic, "How we built our multi-agent research system", 2025-06-13 <https://www.anthropic.com/engineering/multi-agent-research-system> | M-strong (internal, but primary) |
| E2 | Multi-agent beat single Opus 4 by 90.2% on internal *research* eval; token usage alone explains 80% of variance | same | M-strong for research; **not coding** |
| E3 | "most coding tasks involve fewer truly parallelizable tasks than research"; shared-context / many-dependency domains "are not a good fit for multi-agent systems today"; only pays when task value covers cost | same | A (expert judgment, primary) |
| E4 | Parallel-writer swarms still don't work; what works: clean-context reviewer (~2 bugs/PR found, ~58% severe), smart-friend escalation, manager + child agents; "multi-agent systems work best today when writes stay single-threaded" | Cognition, 2026-04-22 <https://cognition.com/blog/multi-agents-working> | M-weak (vendor numbers) + A |
| E5 | 16 parallel Claudes, ~2,000 sessions, ~$20k, 100k-line C compiler. Merge conflicts "frequent" but handled; on one shared bug "every agent would hit the same bug ... overwrite each other's changes"; "16 agents running didn't help because each was stuck solving the same task"; parallelism worked only when a test oracle (GCC) split the work | Anthropic (Carlini), 2026-02-05 <https://anthropic.com/engineering/building-c-compiler> | M-weak (n=1, but primary and candid) |
| E6 | 33,596 agent PRs / 2,807 repos: 40.2% of repos have co-active agent PR pairs (79.4% of agent PRs); replayed merges: **19.8% textual conflict intra-agent, 41.7% cross-agent**; 84.4% of conflicted files are source, not dependency manifests; ~42% structural | Xu et al., arXiv:2607.04697, 2026-07 <https://arxiv.org/abs/2607.04697> | M-strong |
| E7 | AI adoption: +21% tasks, +98% PRs merged per dev, but **PR review time +91%**, PR size +154%, no company-level delivery gain | Faros AI telemetry, 10k devs (via secondary summaries, e.g. <https://getunblocked.com/blog/ai-productivity-paradox/index.md>) | M-weak (vendor, observational, secondary) |
| E8 | DORA 2025: AI now positively correlated with throughput, still negatively with stability | DORA 2025 via <https://www.gitkraken.com/blog/proving-ai-impact-dora-and-velocity-metrics-guide-2026> | M-weak (secondary) |
| E9 | Ten-agent release postmortem: conflicts clustered at shared registration points, each "keep both", <2 min to resolve | <https://bernstein.readthedocs.io/en/latest/blog/ten-agents-one-release/> | A |
| E10 | Agent teams cost 3-4x a single session (one guide says ~7x in plan mode); no session resume for in-process teammates | <https://www.morphllm.com/claude-code-agent-teams>, <https://blog.laozhang.ai/en/posts/claude-code-agent-teams> | A |
| E11 | Routing savings on chat benchmarks: >85% MT-Bench, 35-46% structured | RouteLLM | M-strong but **off-domain** |
| E12 | Orchestrator-vs-single-agent on SWE-bench-style coding: claims of +12-23% (AdaptOrch) and +16% exist; "single-agent matches multi-agent at equal token budget" also claimed | FlowHunt summaries <https://www.flowhunt.io/de/blog/multi-agent-ai-system/> | **Unverified** (could not reach primaries) |

First-party (this repo):

| # | Fact | Source | Strength |
|---|---|---|---|
| F1 | 141 PRs merged in the last 30 days; 10 open issues; beads `ready` list populated | `gh pr list --search merged:>=2026-09-10`, `gh issue list`, `bd ready` | 1P |
| F2 | Identifier collisions across parallel branches already happened: `fix(codex-standards): renumber WO ids to clear collision with pipeline-board (#506)`; `docs(backlog): ... record the manifest collision (#464)`; ADR numbering jumps 0079 -> 0081 (no 0080 on disk) | `git log`, `ls docs/adr` | 1P |
| F3 | A pairwise merge audit found 2 hazard pairs among 44 green PRs ("green alone, red together"); a 21-PR stack close-out needed a written procedure | memory notes `cross-pr-hazard-pairwise-merge-test.md`, `pr-stack-close-out-blocked.md` | 1P |
| F4 | ADR-0070 (accepted 2026-09-21) adopts GitHub merge queue, but the GraphQL `mergeQueue(branch:"main")` returns `null` today, so it looks **not enabled** | `gh api graphql` | 1P (verify) |
| F5 | Merge authorization: a goal alone never unlocks `gh pr merge`; an explicit AskUserQuestion answer does | memory `merge-permission-classifier.md` | 1P |

Bottom line on evidence: **no controlled measurement shows an orchestrator
improves coding outcomes.** The strongest measured facts are about cost
(~15x tokens, E1) and about integration friction (conflict rates E6, review
time E7). The best-supported positive patterns are narrow: single writer,
parallel readers/reviewers, manager+children with a test oracle, escalation
to a stronger model.

---

## 3. Failure modes people report

1. **Merge conflicts / convergence points.** Measured at 20-42% for co-active
   agent PR pairs (E6); practitioners find them concentrated in shared
   registration files (E9). In this repo the convergence points are known and
   few: `plugin.json` version, ADR/WO/PRD number allocation,
   `factory/templates` manifest checksums, `LEDGER.md`, beads JSONL (F2, F3).
2. **Duplicate / overwriting work** when agents share one problem (E5).
3. **Context loss between agents ("telephone game")** — Cognition's original
   argument; still holds for parallel writers (E4). Chief-of-Staff report:
   compaction loses detail, self-reports drift, lessons vanish unless written
   to a durable store, inter-session messages can be delayed/expire.
4. **Runaway cost.** ~15x tokens (E1); agent teams 3-4x (E10); Gas Town flagged
   for API cost; Workflow docs add a `Large workflow` warning and 1,000-agent
   cap precisely for this. Model inheritance bug (#95190) makes small tasks
   run on the flagship tier.
5. **Review bottleneck.** More PRs, larger PRs, review time up ~91% (E7);
   Google Cloud CTO office says the bottleneck moved from writing to
   reviewing/integrating. This repo's gate 3 (human or independent-review
   merge) is exactly that bottleneck.
6. **Verification theatre.** Workers report checks they never ran; vacuous
   assertions (Chief-of-Staff; also this repo's own "prove the mutation
   landed" memory).
7. **Tool immaturity.** Agent teams experimental, no worktree isolation;
   Workflows forbid mid-run human input; T3 Code orchestrator drops workflow
   phases; Workflow harness relayed user chat into subagents
   (<https://github.com/anthropics/claude-code/issues/95369>); a bare `git
   commit` in a shared tree sweeps another session's staged changes.

---

## 4. How this repo's pieces map onto an orchestrator

| Orchestrator duty | Already here | Missing / partial |
|---|---|---|
| Durable work queue + dependency edges | beads (`bd ready`), `breakdown.md` `blocked by:` rows, WO issues with `wo:*` labels (two planes, ADR-0032) | beads and breakdown rows are two queues; nothing reasons over both plus open PRs as one graph |
| Drive one run end to end | `autorun` (one fresh subagent per stage, artifacts are the only state, brief answers interviews, logs assumptions) | strictly sequential, one run; stops at interview gaps; no cross-run awareness |
| Fan out ready work concurrently | `work-queue` (wip_cap 3, worktree per WO, priced against monthly cap, claims via label, never merges) | only the **implement** stage; only orders already `wo:ready-for-agent`; reports PRs then stops |
| Remote dispatch | `assembler.yml` dispatches WO issues to agents (no write credential, ADR-0077) | one WO per job; no sequencing across jobs |
| Per-piece model choice | `factory.json` routing bands; Agent/Workflow `model` + `effort` params | no evidence the bands are right; desktop chips can't set model (#95190); context budget per piece is not a first-class knob |
| Budget / stop | ADR-0034 budgets (S/M/L $), 3 stops, cost ledger, monthly cap | ledger under-records for cloud path (work-queue SKILL caveat) |
| Human gates | `human_gates.py`, gate digest (#178), labels | research -> **decide** step is a human gate; Workflows cannot pause for it mid-run |
| Ordered merge + cross-PR conflict resolution | ADR-0070 merge queue (accepted), `address-pr-review`, pairwise-merge audit technique, documented stack procedure | merge queue apparently **not enabled** (F4); **no allocator** for shared sequence numbers (ADR/WO/PRD ids, plugin version, manifest regen) — today these collide and get fixed after the fact (F2) |
| Cross-session view | `dashboard.py`, `board.py`, pipeline-board | read-only; nothing acts on it |

What is genuinely missing is **not another fan-out** (work-queue, assembler,
Workflows and `/batch` cover that) but the layer above it: one place that
sees research runs, decisions pending, ready WOs and open PRs together;
sequences them; allocates the shared numbers up front; and drives the merge
order — while staying single-writer per convergence file.

---

## 5. Corroborates / sharpens / contradicts

**Corroborates**
- Cross-PR conflict pain is real and measured (E6: 20-42% of co-active pairs),
  and this repo has its own collisions (F2, F3). Version bumps, ADR numbers and
  manifest regen are textbook "convergence points" (E9).
- Model control per piece is a live gap others report against Claude Code
  itself (#95190), so the owner is not alone.
- Why-now is real: dynamic workflows (resumable, per-stage model, pluginable),
  cross-session messaging, agent view, and Projects all landed in 2026 and the
  docs now present five parallel surfaces. 141 merged PRs in 30 days is volume
  a single interactive `/goal` session has to serialize by hand.

**Sharpens**
- The measured win is in **integration and review**, not in more parallel
  writers. Cognition and Anthropic both say keep writes single-threaded and
  parallelize reads/reviews; the conflict data says the cost lives at merge
  time. So "orchestrator" should mean *sequencer + allocator + merge driver*,
  not "swarm".
- Most collisions are **allocation** problems (next ADR number, next version,
  manifest) that a deterministic reservation step removes before any agent
  writes — cheaper than resolving them after (stdlib Python fits).
- "Control how much context each piece gets" maps directly onto the
  Workflow model (script holds intermediate results; agents get only their
  brief) and onto autorun's existing rule (artifacts are the only state).
- Turning on the already-accepted merge queue (ADR-0070) may remove part of
  the problem with zero new code — check why it is `null` first.
- Human "decide" gates don't fit inside one Workflow run (no mid-run input);
  the docs' own advice is one workflow per stage, which matches the pipeline's
  stage-per-artifact shape.

**Contradicts / cautions**
- No controlled evidence that orchestration improves coding *outcomes*; the
  one large measurement (E2) is research, and Anthropic says coding is a
  weaker fit (E3). Expect ~4-15x token cost for the multi-agent parts.
- More parallel output raises review load (E7); with gate 3 as the human
  bottleneck, an orchestrator that opens more PRs could make the owner's day
  worse, not better, unless it also shrinks review (ordering, batching,
  independent reviewer agent).
- Native surfaces are previews/experimental and moving fast (agent teams off
  by default and not worktree-isolated; T3/Workflow bugs). Building a heavy
  bespoke orchestrator now risks being overtaken — and the owner's own CLAUDE.md
  flags a tendency to over-invest in tooling before shipping.
- Several pieces already exist (autorun, work-queue, assembler, beads, gate
  digest, budgets). The idea must name what is *missing* (cross-run sequencing,
  number allocation, merge ordering, per-piece model/context policy), or it
  duplicates.

### Hunch-level shape (not a design)
A thin "conductor" utility skill (or plugin-shipped saved workflow) that, per
pass: reads beads + breakdown rows + open PRs + pending gates; reserves shared
identifiers (ADR/WO numbers, plugin version, one manifest regen) before
dispatch; hands implement work to the existing work-queue / autorun with an
explicit model+effort+context brief per item; and drives merges in dependency
order through the merge queue, with one writer per convergence file and a
clean-context reviewer agent. Measure it against today's `/goal` session on
tokens, conflicts resolved by hand, and owner minutes per merged PR.

---

## Couldn't verify
- Primary AdaptOrch / 2026 multi-agent SWE-bench papers (E12).
- Faros 91% figure from the original report (E7; one blog claims 441%).
- Agent-teams token multiplier (E10 guides disagree: 3-4x vs 7x).
- Whether merge queue is unavailable (plan/visibility) vs simply not enabled (F4).
- Gas Town convoy/dispatch internals.

## last30days community signal (2026-09-10 to 2026-10-10)
Engine run: Reddit 30 threads, HN 14, GitHub 11, YouTube 6 (X unavailable).
Raw file: `~/Documents/Last30Days/claude-code-orchestrator-multi-agent-coding-agent-teams-raw-v3.md`.
Signal was thin and mostly tooling launches (herdr, rondoflow, Pixel Agents,
Foremerge, Ginu "I run a few Claude Code sessions at once and I'd turned into
their babysitter"), T3 Code Orchestrator V2 bugs, #95190, and agent-teams
YouTube tutorials (Nate Herk; one cites Anthropic's 16-agent compiler).
Dominant r/ClaudeCode thread was about model cost/behaviour ("Opus5 is the
first model where the question of 'Yes, it's good but at what cost?' becomes
relevant", u/fiztah, 430 upvotes), not orchestration. No high-engagement
thread reported measured orchestrator wins.
