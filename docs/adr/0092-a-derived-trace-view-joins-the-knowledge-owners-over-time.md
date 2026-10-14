# A derived trace view joins the knowledge owners over time

- Status: accepted (Owner, 2026-10-14)
- Date: 2026-10-14

The Owner chose this on 2026-10-14, in session ("Accept, build
trace.py"). It resolves issue #849. The evidence and the full candidate
comparison are in `docs/research/knowledge-system-over-time.md`.

## Context

Every kind of project knowledge already has one owner: tickets are
GitHub issues (ADR-0083), requirements are run artifacts with typed ids
in frontmatter (ADR-0004), decisions are ADRs, durable facts are
`docs/kb/` pages (ADR-0078), and feedback lives in each run's
`retro.md`, in issues and in the journals. What nothing provides is the
view over time: "what did we decide, ask for and hear back about X, and
how did it change" takes greps across five places.

The links mostly exist already. Over half the issues cite a typed id or
a run ref, every artifact's history is in `git log`, and the issue
timeline is read by `human_gates.read_timelines` (ADR-0090). The
weakest link is feedback, which names the requirement it concerns only
when its writer remembers to. The missing piece is a reader, not a
store.

## Decision

1. **No new knowledge store.** No database, graph, wiki, tracker or
   index file is added. Each fact keeps its current owner (ADR-0061).
2. **`trace.py` is a derived view.** A stdlib-only, read-only root tool
   that, given a key (a run ref, a typed id, an issue number or a kb
   page path), resolves it to its run and prints one dated,
   chronological report in four sections: ticket, requirement,
   decision, feedback. It draws only edges the existing grammar already
   expresses (typed-id tokens, run refs, `(tracker: #N)` rows and
   `Closes #N` lines, all owned by `knowledge_plane.py` and
   `protocol.py`), and shows ADR supersession with both its dates. It
   runs on demand, caps its output with a byte budget, and has a
   `--json` form that later renderers consume without re-deriving the
   edges (ADR-0062).
3. **The view is never committed.** It is regenerated on every call
   and no file it prints is checked in, so it cannot drift from its
   sources and adds no second owner.
4. **Offline and CI degrade, never fail.** The git-history part runs
   fully offline. Issue history is the one online input; it goes
   through `cli.py`'s existing gh port and, when that is unavailable,
   the report says that issue history was not read rather than erroring
   or guessing.
5. **It ships like `kb.py`** (ADR-0078 clause 7): a root tool vended
   with the plugin and run by the skill from its own directory. Unlike
   `kb.py`, it is also mirrored into the factory payload through
   `factory_init.MIRRORS`, with the manifest regenerated in the same
   change. It imports `knowledge_plane`, `cli`, `protocol` and
   `human_gates`, all mirrored, so a root-only `trace.py` would add
   crossing imports to the set ADR-0091 pins; mirrored, it adds none.
6. **The `knowledge-base` skill gains a "trace" flow** that runs the
   tool and reports what it prints. The skill states no repo fact the
   tool did not print (ADR-0062).
7. **The citation rule for feedback.** Feedback that concerns a
   requirement or decision (a retro note, a review finding, a feedback
   issue, a journal comment) cites the run ref or typed id it concerns.
   This is the one new obligation on writers. It is a convention, not a
   gate: the trace view lists the feedback it can tie to a run. A lint
   that lists feedback citing nothing is optional and needs its own
   decision; making it a gate is a further decision again.

## Rejected options

Each fails a constraint that binds anything shipped in this plugin
(stdlib only, no required MCP or third-party dependency, one fact one
owner, append-only evidence, checkable offline and in CI):

- **GitHub Projects v2**: custom fields copy frontmatter, a second
  owner (ADR-0061); online only, so not CI-checkable.
- **GitHub Discussions**: one more place to grep, not a join; online
  only.
- **GitHub wiki**: a separate repository outside the PR gate and CI, so
  neither `kb.py lint` nor `gates.py` can see it; a second docs tree.
- **Basic Memory**: needs Python 3.12, `uv` and an MCP server, and its
  SQLite index lives outside git; history is a paid feature.
- **Obsidian vault with Bases**: Bases needs the app, so no agent or CI
  can evaluate it. `docs/` already opens as a vault, so it stays
  compatible with nothing shipped.
- **MCP memory server**: needs node and MCP; observations carry no
  timestamps and deletes are hard, so it fails append-only evidence and
  cannot answer what changed when.
- **Graphiti**: needs a graph database and an LLM for extraction. Its
  validity-window idea is kept, as the supersession dates the view
  prints.
- **Backlog.md and git-bug**: a second tracker beside GitHub issues
  (ADR-0083) and a non-stdlib runtime.
- **Linear, Notion, Confluence/Jira**: hosted, credentialed and online
  only; each replaces or duplicates the single tracker.
- **WeKnora**: a service stack (Postgres, Redis, Docker) to run; its
  lessons were already taken in #721.

## Consequences

- This ADR amends neither ADR-0078 nor ADR-0083. ADR-0078 still decides
  where durable facts live and how they are indexed, and its rejection
  of vector or graph retrieval stands; a derived, never-stored view
  changes none of that. ADR-0083 still keeps one tracker; this adds a
  reader, not a tracker. Neither status line changes.
- The build is a separate feature issue, #878; this ADR builds nothing.
- Writers of feedback take on the citation rule from now on. Feedback
  that predates it is shown where the tool can tie it to a run and is
  otherwise left alone.
- The `knowledge-base` LEDGER maturity does not move with this ADR or
  with the build; it moves only on real evidence (ADR-0012).
