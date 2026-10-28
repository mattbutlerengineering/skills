# idea-to-prod

A Claude Code plugin of lifecycle-pipeline skills that guide work from a raw
idea all the way to production. Each stage produces an artifact the next stage
consumes; the artifacts themselves are the pipeline state.

![The skill map: the pipeline stages as a closed loop with the router inside it, a maintenance run entering from outside, and the utility skills grouped in cards by the moment you reach for them.](docs/assets/skill-map.svg)

## Install

**Claude Code** (primary):

```
/plugin marketplace add mattbutlerengineering/skills
/plugin install idea-to-prod@skills
```

Then verify it: run `/idea-to-prod:doctor`. A plugin-only install that is
wired up ends its report with

```
doctor: 0 problem(s) — tier 0 ok, tier 1 skipped (no tools/factory/ — plugin-only install), tier 2 not run (networked, ask to include it)
```

(captured from a run of the skill at version 0.19.0 against an empty
repository, 2026-10-16). "tier 1 skipped" is the factory not being
stamped, which is the normal state at this point; anything else on the
line names the problem and its fix.

**Grok:** the same marketplace. Grok reads `.claude-plugin/` directly
([ADR-0076](docs/adr/0076-grok-supported-harness.md)).

```
grok plugin marketplace add mattbutlerengineering/skills
grok plugin install idea-to-prod --trust
```

Invoke `/next`, or `/idea-to-prod:next` when that name collides with a
built-in.

**oh-my-pi (omp):** the skills also run under [omp](https://omp.sh). The root
`package.json` declares them as a Pi package (`pi.skills`), so omp discovers all
of them once the repo is on its package path:

```
git clone https://github.com/mattbutlerengineering/skills
omp --skill ./skills/skills/next   # or add the cloned dir as a Pi package
```

Fallbacks: omp inherits `.claude` skills on first run, or copy `skills/*` into
`~/.pi/agent/skills/`.

**Other agents (`npx skills`):** the third-party
[skills CLI](https://github.com/vercel-labs/skills) installs a subset into
Claude Code, Codex, Cursor and the other agents it supports. It copies each
skill's own folder and nothing else, so only the skills that never read the
plugin root work this way ([ADR-0120](docs/adr/0120-skills-cli-installs-the-standalone-skills.md)).
This command installs exactly those:

```
npx skills add mattbutlerengineering/skills \
  --skill address-pr-review --skill animated-diagram \
  --skill architecture-diagram --skill deepen --skill house-voice \
  --skill lean --skill mermaid --skill polish \
  --skill prisma-migrations --skill ux-patterns --skill ux-writing
```

Add `-a claude-code` (or another agent) to skip the agent prompt, and `-g`
to install for every project. The pipeline stages, `next` and the other
utility skills read the pipeline protocol or a root tool, which that copy
leaves behind, so install them through a plugin harness above.
`house-voice` works for the session it is invoked in; its every-session
output style ships only with the plugin. `python3 lint.py` keeps this list
equal to the skills that survive the copy.

Every skill works on a bare install of any of these harnesses — no
third-party tools, MCP servers, or other plugins required.

That is the whole setup for the skills. To also stamp the factory into a repo
— offline gates, dispatch workflows, cost ledger — and confirm the install
works end to end, follow [`docs/setup.md`](docs/setup.md). `/doctor` checks it
mechanically, at whichever tier the repo has reached. Adopting into a repo
that already has its own skills, agents or cloud routines? Read
[Consumer adoption](docs/setup.md#consumer-adoption) first: plugin skills
load only in local sessions, and a tools-only (Conductor-only) stamp is
available.

## Usage

Two ways in:

- **Guided:** invoke `/next` (Claude Code and Grok) or `/skill:next` (omp).
  On Grok, a name that collides with a built-in stays available as
  `/idea-to-prod:next`. It reads your repo's artifact state, tells you where
  the run stands, and hands off to the right stage skill.
- **Direct:** invoke any stage skill (`/prd`, `/architect`, … — `/skill:prd`
  on omp, `/idea-to-prod:prd` on Grok when the bare name collides) to enter
  mid-stream. If a predecessor artifact is missing, the skill offers a quick
  backfill — it never blocks.

The pipeline runs at three scales: a **product run** (greenfield; artifacts
at your repo's `docs/` root), a **feature run** (artifacts under
`docs/features/<slug>/`, scaled down — a feature PRD is a page, not a book),
and a **maintenance run** (a defect, regression, refactor, or dependency
upgrade; artifacts under `docs/fixes/<slug>/`, entering at the capture step
and re-entering the pipeline at the depth recorded in its brief).

## Stages

| Skill | Stage artifact | Style |
|-------|----------------|-------|
| `next` | — (router) | reads state, routes |
| `idea` | `idea.md` | interviews you |
| `prd` | `prd.md` | interviews you |
| `ux-design` | `ux.md` (skipped if no UI surface) | interviews you |
| `architect` | `architecture.md` | drafts, then asks about trade-offs |
| `decompose` | `breakdown.md` | drafts |
| `implement` | code (+ checkboxes in `breakdown.md`) | test-first execution |
| `verify` | `verification.md` | drafts evidence |
| `review` | `review.md` | drafts findings |
| `ship` | `release.md` | checklist-driven |
| `operate` | `retro.md` | closes the loop → next idea |
| `capture` | `defect.md` (seeds a maintenance run) | interviews you |

Beside the stages, the plugin ships utility skills
([ADR-0023](docs/adr/0023-utility-skills.md)) that act on the work
surrounding the pipeline rather than a run's artifacts. The figure above
places each one at the moment you reach for it; the same moments fill the
table's Moment column.

| Skill | Moment | Why it matters |
|-------|--------|----------------|
| `audit` | Before a run exists | Finds what to improve when no defect is named: read-only, every finding reproduced before it is reported, each routed to a backlog seed or a run. Its claims scope checks whether the docs are still true — the shipped md_claims.py settles links, paths and commands by lookup, then a judgement pass that also runs headless from CI. |
| `automate` | Before a run exists | Recommends the hooks, subagents, skills and MCP servers a repo is missing, each priced and tied to a friction it removes; never scaffolds them. |
| `knowledge-base` | Before a run exists | Keeps the project facts an agent cannot get from the code (invariants, gotchas, the why with its ADR) in `docs/kb/`, indexed inline in CLAUDE.md or AGENTS.md by the shipped kb.py tool; ingest proposes itemised edits for a human to promote, and lint flags pages whose cited code changed since they were verified. |
| `deepen` | Reshaping what's built | Finds shallow modules whose interfaces cost nearly as much to learn as their implementations, confirms each at its real call sites, and designs the deeper interface with you. |
| `lean` | Reshaping what's built | Argues for less: climbs a fixed ladder (does this need to exist, is it already in the repo, the standard library, the platform) before building, or hands back a numbered cut-list for a diff or tree, each deletion backed by a reference search; never cuts trust-boundary validation, data-loss handling, security or accessibility. |
| `polish` | Reshaping what's built | Takes a built interface from working to considered: establishes who it is for and what the design system already decided, applies one named move, and judges the rendered result rather than the code; it starts where `ux-design` stops. |
| `ux-writing` | Reshaping what's built | Audits and rewrites the words in an interface as a set: inventories the strings in the code, grades them against a UX-writing rubric and the project's voice and terms, and applies only the rewrites you approve; changes wording, never facts. |
| `ux-patterns` | Reshaping what's built | Derives how the product behaves — confirm or undo, loading, errors, empty states, validation, focus — from the code into a project file, `docs/ux-patterns.md`, asking only the judgement calls, then audits screens against it for consistency. |
| `autorun` | Driving a run | Drives a whole run end to end from a one-time brief, one fresh subagent per stage, logging an assumption wherever the brief runs out. |
| `conduct` | Driving a run | Takes a batch of the owner's issues from a priced plan to merged or blocked: one metered headless worker per step on the policy's model and effort, one question at a time with a recommendation, and merges in order only under an answer; ends with a scorecard. |
| `implement-queue` | Driving a run | Drains a repo's ready GitHub issues unattended: one TDD worktree worker per issue, CI and a distinct reviewer on every PR, then a serial merge train; stops at reviewed, green PRs unless the repo's queue profile opts in to auto-merge. |
| `work-queue` | Driving a run | Works several ready work orders at once, one worktree-isolated agent each, bounded and priced by the factory's caps; stops at merge-ready PRs. |
| `address-pr-review` | Around a pull request | Acts on the feedback reviewers left on your PR: fixes what the comments ask, pushes, replies to and resolves every thread, and merges the base branch when behind. |
| `launch-demo` | Around a pull request | Writes a shipped feature's launch copy in plain words and records a short narrated video whose every line is a sentence of it, from the run's artifacts or the pull request; copy only, with the reason, when a recorder is missing. |
| `mermaid` | Drawing pictures | Turns a process or system into a digestible mermaid diagram, styled with explicit colors that hold contrast in light and dark renderers. |
| `architecture-diagram` | Drawing pictures | A still, theme-aware SVG system figure on light editorial paper that embeds in READMEs and docs as a plain image; the figure above is one. |
| `animated-diagram` | Drawing pictures | A diagram that moves on its own, connectors streaming in execution order, as a pause-able HTML page or a pure SVG a README plays inline. |
| `interactive-architecture-diagram` | Drawing pictures | A self-contained HTML demo with a narrated step-through presenter, click-to-inspect panels and PNG/SVG export, for showing how a system works. |
| `pipeline-board` | Drawing pictures | Places every active run on its current stage as a swimlane SVG, with placement stated by the shipped board.py tool rather than re-derived. |
| `factory-init` | Installing the factory | Stamps the factory scaffold (offline gates, dispatch workflows, the cost ledger) into a product repo, and regenerates the template manifest after an edit. |
| `doctor` | Installing the factory | Answers whether the install is actually wired up, tier by tier and read-only, reporting each problem with the fix rather than applying it. |
| `prisma-migrations` | Looking things up | Reference for getting a Prisma schema change to every database safely: `migrate dev` versus `migrate deploy` versus `db push`, deploy ordering, baselining a database built without migrations, CI/CD wiring and failed-migration recovery, with copyable workflow and script templates. |
| `house-voice` | Around every reply | Sets a voice for the agent's own replies: the answer first, no ceremony or tells of generated prose, every fact and payload kept, and full length where safety needs it; an opt-in output style carries it into every session, and it never rewrites persisted artifacts. |

`lean`, `polish`, `ux-writing`, `ux-patterns` and `house-voice` restate,
in this pipeline's terms, ideas from open-source work —
[Ponytail](https://github.com/DietrichGebert/ponytail),
[Impeccable](https://github.com/pbakaus/impeccable),
[ux-writing-skill](https://github.com/content-designer/ux-writing-skill),
[web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines),
[caveman](https://github.com/JuliusBrussee/caveman) and
[stop-slop](https://github.com/hardikpandya/stop-slop)
— and each skill says what it borrowed.

The shared rules (run discovery, orientation table, soft gating, frontmatter
conventions) live in [`docs/pipeline-protocol.md`](docs/pipeline-protocol.md).

## Development

- [`CONTEXT.md`](CONTEXT.md) — canonical vocabulary
- [`docs/adr/`](docs/adr/) — architecture decision records and their status
- [`LEDGER.md`](LEDGER.md) — per-skill maturity (draft / used-once / battle-tested)
- `python3 lint.py` — structural lint of the install, router, and eval surface (the `CHECKERS` tuple in [`lint.py`](lint.py) is the authoritative list); runs in CI on every push/PR
- `python3 kb.py drift` — instruction-file drift: dangling paths, skill and agent tables, and slash commands in `CLAUDE.md`, `AGENTS.md` and `.claude/rules` ([`kb_drift.py`](kb_drift.py)); runs in CI on every push/PR
- `python3 run_tests.py` — the full offline suite, one process per test module in parallel: pipeline protocol, eval seams, and the factory tools, mostly against fixture trees plus pins on the real repo; runs in CI on every push/PR (`python3 -m unittest discover tests` is the same suite serially)
- `python3 trigger_eval.py --record` — routing eval: which skill fires for each query in [`evals/routing.json`](evals/routing.json) (needs the `claude` CLI; costs real runs)
- [`docs/output-evals.md`](docs/output-evals.md) — on-demand output evals grading skill artifacts against expectations

## License

MIT, except `trigger_eval.py`, which is derived from Apache-2.0-licensed code
from the skill-creator plugin — see [`NOTICE`](NOTICE) and
[`licenses/Apache-2.0.txt`](licenses/Apache-2.0.txt).
