---
name: automate
description: Use when the ask is what Claude Code automation a repo should have — "what hooks should I add", "should this be a skill or a subagent", "recommend automations for this project", "what's worth automating here", "is there an MCP server worth wiring up". Read-only: it recommends, prices, and hands off — it never scaffolds the thing it proposes. Every recommendation must cite the friction it removes (a step an artifact records as manual, a command the repo repeats, a rule stated in CLAUDE.md that nothing enforces); file presence alone is a suspicion, never evidence. Six categories — hooks, subagents, skills, plugins, MCP servers, and drift detectors for rules nothing checks — each capped, each priced, each routed to a carrier that already exists. Not `doctor` (is the install wired up), not `audit` (what is wrong with the code), not `deepen` (what shape are the modules).
---

# Automate

Look at a repo and answer one question: **what Claude Code automation is
missing, and what would it cost?** The product is a short ranked list where
every row carries the friction it removes, the thing that would construct
it, and its price.

Nothing here writes automation. Proposing is the expensive half —
understanding what a repo actually does by hand — and building a hook or a
subagent from an agreed spec is cheap. A recommender that starts scaffolding
has spent its budget on the cheap half and reviewed its own work.

**The bar is friction, not file presence.** "You have a `package.json`,
therefore add a format-on-save hook" is the failure mode this skill exists
to avoid: it produces plausible output for every repo on earth, which means
it produces information about none of them. A recommendation that cannot
name the specific friction it removes is a suspicion, and it goes in the
suspicions list.

## Process

### 1. Recon — name the tree, then read what is already there

State the **absolute repo root** and `git rev-parse --short HEAD` in the
report's first two lines. A recommendation is scoped to a tree at a commit.

Then read what the repo already has, because recommending something that
exists is the fastest way to be ignored:

| Surface | Where |
|---|---|
| Agent instructions | `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `CONTEXT.md` |
| Hooks and settings | `.claude/settings.json`, `settings.local.json`, `~/.claude/settings.json` if the ask is about this user |
| Subagents | `.claude/agents/*.md` |
| Skills and plugins | `.claude/skills/`, `skills/`, `.claude-plugin/plugin.json`, `marketplace.json` |
| MCP servers | `.mcp.json`, `settings.json` `mcpServers` |
| The real command set | `Makefile`, `package.json` scripts, `justfile`, CI workflow files |
| Decisions already taken | `docs/adr/`, design notes, `CONTRIBUTING` |

An automation the repo already has is not a finding. An automation it has
that is **inert** — installed and unable to fire — is one of the best
findings available, and it belongs in the report as a defect, not a
recommendation.

**Then check what is already in flight, before recommending anything:**

    gh pr list --state open
    gh issue list --state open --limit 50

An automation an unmerged PR already adds is not a recommendation — it is
a duplicate of work in flight, and it reads as new, which is worse than
saying nothing. The same goes for an open issue that already proposes it
and for a seed already sitting in `docs/backlog.md`. Read all three
before the sweep, not after. This is not hypothetical bookkeeping: a run
in this repo rebuilt a one-line fix that was sitting in an open PR the
whole time, because discovery listed open issues and never open PRs.

### 2. Find the friction

Read [`references/catalog.md`](references/catalog.md) now — it carries the
six categories, what evidences each, what makes each inert, and what each
costs.

Friction is a thing the repo does by hand, repeatedly, and records
somewhere. Four sources, best first:

1. **Manual steps the repo writes down about itself.** A `release.md` that
   says a step was done by hand; a retro naming a thing that dragged; a
   README section titled "before you commit"; a CI job whose first line is a
   comment apologising for it. These are the strongest signal because
   someone already felt the friction and wrote it down.
2. **Rules stated and unenforced.** Everything `CLAUDE.md`, the ADRs and the
   contributor docs assert, checked against what CI actually runs. A rule
   that is stated, believed, and unchecked is drift waiting to happen, and
   this is the category no marker-file detector can produce.
3. **Repetition in the history.** `git log --oneline -50` and the diffs:
   the same one-line fix landing in five files; a manifest regenerated in
   every second commit; the same review comment recurring. Repetition that
   a machine could have caught is the definition of a missing check.
4. **The command set nobody can remember.** A `Makefile` with fifteen
   targets and a README that documents three. Not automation-worthy on its
   own, but it tells you which surface a hook or a skill would sit on.

Marker files (`package.json`, `pyproject.toml`, `go.mod`) tell you the
*shape* of a recommendation — which linter, which test runner. They never
justify one.

### 3. Match each friction to exactly one category

The catalog's six: **hooks**, **subagents**, **skills**, **plugins**, **MCP
servers**, **drift detectors**. One friction, one category — a friction that
seems to want two usually wants the cheaper one, and the catalog says which.

Cap the output: **two per category** on a bare invocation, expanding to five
when the ask names one category. A list of thirty recommendations is a
reading assignment, not advice.

### 4. Kill the inert ones before they reach the report

For every candidate, name the thing that would **construct or fire** it. If
you cannot, it does not ship:

- a hook whose matcher fires on a tool the repo never uses;
- a subagent with no dispatcher — nothing invokes it, and in Claude Code an
  agent file missing a frontmatter `name:` is not dispatchable at all, no
  matter what the filename says;
- a skill whose description overlaps one already installed, so the router
  picks between them at random;
- an MCP server for a service the repo does not call;
- a detector for a convention the repo does not actually hold.

This is the same rule `deepen` applies to seams: never propose one with a
single adapter, and check that the adapters get constructed somewhere. An
inert automation costs its indirection and returns nothing.

### 5. Price it

Every row carries a cost, because the reader is deciding, not admiring:

- **Hooks** add latency to *every* matching tool call, forever, and a
  PreToolUse hook that blocks on a false positive is a workflow someone has
  to fight. Price the false-positive path, not the happy one.
- **Subagents** cost tokens per dispatch and lose the parent's context.
- **Skills** cost a description in the router's namespace — the real price
  is what they make ambiguous, not what they add.
- **Plugins** cost versioning and a distribution story.
- **MCP servers** cost a network dependency, an auth surface, and a tool
  schema in every context window that loads them.
- **Drift detectors** cost a false-positive budget: a detector that fires on
  good changes gets disabled, and a disabled detector is worse than none
  because the rule now looks enforced.

### 6. Report

Ranked by leverage — friction removed over cost:

| # | Recommendation | Category | Friction (with location) | What constructs it | Cost | How it fails |

Then, separately and never merged into that table:

- **Already there** — automation the repo has that a reader might expect
  this report to recommend. Naming them is how the report proves it looked.
- **Inert** — installed automation that cannot fire, with the reason.
- **Suspicions** — candidates evidenced only by file presence or by a
  feeling, each with what would settle it.
- **Considered and not worth it** — one line of reasoning each, so the next
  run of this skill does not re-derive them.

Close with a **coverage statement**: each of the six categories listed as
*swept, nothing found* or *not swept*, one or the other, never omitted. An
omitted category reads as clean.

### 7. Route each recommendation to a carrier that already exists

Where the lifecycle pipeline is installed, the ladder is `audit`'s:

1. **A seed in `docs/backlog.md`** — the default for anything worth
   remembering and not worth a run today. One line, the protocol's grammar,
   origin `session:YYYY-MM-DD`.
2. **A maintenance run** via `capture` — when an automation the repo already
   has is inert or wrong. That is a defect, and it has a defect's entry.
3. **A feature run** via `idea` — when the recommendation is a build.
4. **Nothing** — a verdict, recorded in the report.

Read `docs/backlog.md` before appending and drop what it already carries;
the dedupe happens before the write, not after.

Where the pipeline is not installed, the report plus an agreed spec for the
top recommendation is a complete result, and the hand-off is that spec.

## Rules

- Read-only on the repo, without exception. The only file this skill may
  write is `docs/backlog.md`, and only after the step-7 dedupe read. It does
  not create hooks, agents, skills, plugins, or MCP config — not even "just
  the scaffold", which is how a recommendation becomes a change nobody
  agreed to.
- No recommendation without a located friction. `path/file:line`, an
  artifact that records the manual step, or a named rule with the check that
  does not exist. "Repos like this usually want X" is not a finding.
- Never recommend something the repo already has, or something already in
  flight. Check step 1's table and its open-PR/open-issue read first; a
  report that recommends an installed hook has proved it did not look, and
  one that recommends what an open PR already adds is worse — it reads as
  new work.
- Every row carries its cost and its failure mode. Wins-only rows are how an
  automation gets approved and then discovered to be a permanent tax on
  every tool call.
- Respect recorded decisions. A repo that wrote down "we deliberately do not
  use hooks" gets that read back to it, not re-litigated — and a decision
  marked provisional is not a constraint.
- Never write a secret into a config example. MCP server recommendations
  name the credential and the store it comes from; the value never appears.
- If asked to build a recommendation, decline and point at the carrier — it
  goes through `capture` or `idea` and gets a plan, a test, and a human
  gate.
- A short list of evidenced, priced recommendations beats a long one.
