# idea-to-prod

A Claude Code plugin of lifecycle-pipeline skills that guide work from a raw
idea all the way to production. Each stage produces an artifact the next stage
consumes; the artifacts themselves are the pipeline state.

```
Idea → PRD → UX Design* → Architect → Decompose
     → Implement → Verify → Review → Ship → Operate
                                        (*conditional)
```

## Install

```
/plugin marketplace add mattbutlerengineering/skills
/plugin install idea-to-prod@skills
```

Every skill works on a bare Claude Code install — no third-party tools, MCP
servers, or other plugins required.

## Usage

Two ways in:

- **Guided:** invoke `/next`. It reads your repo's artifact state, tells you
  where the run stands, and hands off to the right stage skill.
- **Direct:** invoke any stage skill (`/prd`, `/architect`, …) to enter
  mid-stream. If a predecessor artifact is missing, the skill offers a quick
  backfill — it never blocks.

The pipeline runs at two scales: a **product run** (greenfield; artifacts at
your repo's `docs/` root) and a **feature run** (artifacts under
`docs/features/<slug>/`, scaled down — a feature PRD is a page, not a book).

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

The shared rules (run discovery, orientation table, soft gating, frontmatter
conventions) live in [`docs/pipeline-protocol.md`](docs/pipeline-protocol.md).

## Development

- [`CONTEXT.md`](CONTEXT.md) — canonical vocabulary
- [`DESIGN.md`](DESIGN.md) — design decisions and their status
- [`LEDGER.md`](LEDGER.md) — per-skill maturity (draft / used-once / battle-tested)
- `python3 lint.py` — structural lint (manifest, frontmatter, templates, router refs)
- `python3 -m unittest discover tests` — orientation decision table vs fixture docs trees
- `python3 orientation.py <run-dir>` — reference implementation of the orientation table

## License

MIT
