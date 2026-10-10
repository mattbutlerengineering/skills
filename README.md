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

Every skill works on a bare install of any of these harnesses — no
third-party tools, MCP servers, or other plugins required.

That is the whole setup for the skills. To also stamp the factory into a repo
— offline gates, dispatch workflows, cost ledger — and confirm the install
works end to end, follow [`docs/setup.md`](docs/setup.md). `/doctor` checks it
mechanically, at whichever tier the repo has reached.

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
| `audit` | Before a run exists | Finds what to improve when no defect is named: read-only, every finding reproduced before it is reported, each routed to a backlog seed or a run. |
| `automate` | Before a run exists | Recommends the hooks, subagents, skills and MCP servers a repo is missing, each priced and tied to a friction it removes; never scaffolds them. |
| `deepen` | Reshaping what's built | Finds shallow modules whose interfaces cost nearly as much to learn as their implementations, confirms each at its real call sites, and designs the deeper interface with you. |
| `autorun` | Driving a run | Drives a whole run end to end from a one-time brief, one fresh subagent per stage, logging an assumption wherever the brief runs out. |
| `work-queue` | Driving a run | Works several ready work orders at once, one worktree-isolated agent each, bounded and priced by the factory's caps; stops at merge-ready PRs. |
| `address-pr-review` | Around a pull request | Acts on the feedback reviewers left on your PR: fixes what the comments ask, pushes, replies to and resolves every thread, and merges the base branch when behind. |
| `mermaid` | Drawing pictures | Turns a process or system into a digestible mermaid diagram, styled with explicit colors that hold contrast in light and dark renderers. |
| `architecture-diagram` | Drawing pictures | A still, theme-aware SVG system figure on light editorial paper that embeds in READMEs and docs as a plain image; the figure above is one. |
| `animated-diagram` | Drawing pictures | A diagram that moves on its own, connectors streaming in execution order, as a pause-able HTML page or a pure SVG a README plays inline. |
| `interactive-architecture-diagram` | Drawing pictures | A self-contained HTML demo with a narrated step-through presenter, click-to-inspect panels and PNG/SVG export, for showing how a system works. |
| `pipeline-board` | Drawing pictures | Places every active run on its current stage as a swimlane SVG, with placement stated by the shipped board.py tool rather than re-derived. |
| `factory-init` | Installing the factory | Stamps the factory scaffold (offline gates, dispatch workflows, the cost ledger) into a product repo, and regenerates the template manifest after an edit. |
| `doctor` | Installing the factory | Answers whether the install is actually wired up, tier by tier and read-only, reporting each problem with the fix rather than applying it. |

The shared rules (run discovery, orientation table, soft gating, frontmatter
conventions) live in [`docs/pipeline-protocol.md`](docs/pipeline-protocol.md).

## Development

- [`CONTEXT.md`](CONTEXT.md) — canonical vocabulary
- [`docs/adr/`](docs/adr/) — architecture decision records and their status
- [`LEDGER.md`](LEDGER.md) — per-skill maturity (draft / used-once / battle-tested)
- `python3 lint.py` — structural lint of the install, router, and eval surface (the `CHECKERS` tuple in [`lint.py`](lint.py) is the authoritative list); runs in CI on every push/PR
- `python3 -m unittest discover tests` — the full offline suite: pipeline protocol, eval seams, and the factory tools, mostly against fixture trees plus pins on the real repo; runs in CI on every push/PR
- `python3 trigger_eval.py --record` — routing eval: which skill fires for each query in [`evals/routing.json`](evals/routing.json) (needs the `claude` CLI; costs real runs)
- [`docs/output-evals.md`](docs/output-evals.md) — on-demand output evals grading skill artifacts against expectations

## License

MIT, except `trigger_eval.py`, which is derived from Apache-2.0-licensed code
from the skill-creator plugin — see [`NOTICE`](NOTICE) and
[`licenses/Apache-2.0.txt`](licenses/Apache-2.0.txt).
