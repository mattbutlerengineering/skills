# Research for issue #849: one view of tickets, requirements, decisions and feedback over time

Research note, 2026-10-14. The Owner asked: "how can we keep track of
tickets, requirements, feedback, etc over time? what is the best
knowledge base solution available? How can we ship it with this repo?"

This builds on, and does not reopen, what earlier work settled:

- `docs/research/knowledge-base.md` and `knowledge-base-evidence.md`
  (issue #625) chose a small, human-promoted, non-inferable `docs/kb/`
  with an index inline in the always-loaded file, and rejected vector or
  graph retrieval (proposal D) at project scale. ADR-0078 decided it.
- `docs/research/knowledge-base-ablation.md` measured the win as
  efficiency (about half the turns, 41-52% less cost where the agent
  investigated), not correctness.
- `docs/research/eval-and-memory.md` adopted mem0's ADD/UPDATE/DELETE/NOOP
  verbs and rejected a third-party memory layer.
- ADR-0083 made GitHub issues the only tracker, retired beads, and said a
  graph tracker comes back only with "a script that actually reads it".

So the question here is narrower than "which knowledge base": every kind
of knowledge already has one owner. What is missing is the **view over
time** that joins them.

## 1. The gap, measured

Each kind of knowledge has a home (the table in #849). What no tool does
is answer "what did we decide, ask for and hear back about X, and how did
it change" without grepping five places.

The links mostly exist already; nothing reads them together. Measured on
this repo at `8df41e8`:

- **Issues already cite the plane.** 259 of 461 issues (56%) carry a
  typed id (`PRD-`, `ADR-`, `WO-`) or a run ref (`feature:<slug>`,
  `maintenance:<slug>`) in their body.
- **Retros sit in their run's directory**, so retro to PRD is a
  structural edge, not a citation. Only 2 of the 4 feature retros with a PRD also
  name their PRD id in the text, and none carries it in frontmatter.
- **Run artifacts carry history in git.** The orchestrator run's
  artifacts span 11 commits over 2026-10-10 to 2026-10-14 (idea, PRD,
  architecture with ADR-0084, breakdown, implement, release, three
  fixes, retro), all recoverable with `git log --follow`.
- **The issue side carries history in the timeline API**, which
  `human_gates.read_timelines` already reads for label events (ADR-0090).

The weakest link is **feedback**. Toolsmith queue items, journal
comments and review findings name a run or an issue only when the
writer remembers to, and nothing checks that they do.

## 2. Candidates surveyed

Sources were read on 2026-10-14; dates are the source's own where it
gives one. Primary sources (vendor docs and repos) are listed in §6.

**Repo-native, plus a generated trace view.** Keep every owner as it is.
Add a stdlib, read-only tool that joins them by the typed-id grammar
`knowledge_plane.py` already owns, and reads history from `git log` and,
when online, the issue timeline.

**GitHub Projects (v2).** Table, board and roadmap views over issues and
PRs, up to 50 fields (text, number, date, single select, iteration),
built-in workflows, GraphQL and REST APIs. The GraphQL changelog keeps
adding project and issue-field types through 2026 (archived item states
on 2026-06-08, multi-select issue fields on 2026-06-04). Custom fields are
a second owner for anything already in frontmatter, and field-change
history is not documented as an API.

**GitHub Discussions.** Open-ended threads in categories, Q&A answers,
polls, issue-to-discussion conversion. A good inbox for feedback from
people outside the repo, but it adds another place to grep, not a join.

**GitHub wiki.** A separate repository (`<repo>.wiki.git`), editable by
anyone with write access; only pushes to its default branch go live and
the docs name no pull-request flow. Outside the PR gate and outside CI,
so `kb.py lint` and `gates.py` can never see it.

**Basic Memory** (basicmachines-co, AGPL-3.0, 4.2k stars, v0.22 in June
2026). Markdown notes with frontmatter, `[category]` observations and
`relation [[Target]]` links, indexed into SQLite (or Postgres), with
FastEmbed hybrid search, served over MCP. Needs Python 3.12+ installed
with `uv`. Local installs have no note history ("roll your own", with
git); history is a paid cloud feature.

**Obsidian vault with Bases.** Bases is a core plugin giving table,
list, card, kanban and map views over notes' properties, saved as
`.base` files or code blocks. The repo's `docs/` is already a valid
vault: frontmatter is properties, so the Owner can open it in Obsidian
today with nothing shipped. Bases needs the Obsidian app, so no agent
or CI can evaluate one.

**MCP memory server** (`modelcontextprotocol/servers`, `src/memory`,
MIT). Entities, relations and string observations in one JSONL file,
run with `npx`. Observations carry no timestamps and deletes are
permanent, so it cannot answer "what changed and when".

**Graphiti** (getzep, Apache-2.0, 31.7k stars). The strongest newer
entrant on "over time": facts carry validity windows, superseded facts
are invalidated, not deleted, and every fact traces to the episode that
produced it. It needs a graph database (Neo4j, FalkorDB, Neptune or
deprecated Kuzu) and an LLM for extraction, and ships an MCP server.
Its bitemporal model is the idea worth borrowing; the stack is not.

**Backlog.md** (MrLesk, MIT, about 7k stars). Tasks as markdown files
in the repo with acceptance criteria, dependencies and decisions,
`backlog` CLI with `--json`, an optional MCP server, installed through
npm, Bun, Homebrew or Nix. A second tracker beside GitHub issues, which
is what ADR-0083 just removed.

**git-bug** (GPL-3.0, 10.8k stars). Issues stored as git objects,
offline-first, a single Go binary, bridges to GitHub, GitLab and Jira.
Also a second tracker, and a non-Python binary.

**Notion.** Hosted pages and databases with a hosted MCP server behind
OAuth. Readable by an agent only online and only with credentials;
history lives in Notion, outside git and CI.

**Linear.** Hosted tracker with a remote MCP server
(`mcp.linear.app/mcp`, OAuth 2.1 or API key, read-only endpoint) and
one- or two-way GitHub issue sync (title, description, status, labels,
assignee, comments). Strong product, but it would replace ADR-0083's
single tracker, not complement it.

**Confluence / Jira (Atlassian).** Hosted, with a remote MCP server for
Atlassian products. Same trade as Notion and Linear, at enterprise
weight.

**WeKnora** (Tencent, MIT, 34.0k stars, v0.8.3 on 2026-10-14). Go
backend, Vue front end, Postgres with pgvector and Redis under Docker
Compose (or a SQLite "Lite" binary). Its Wiki mode builds interlinked,
source-citing pages with revision history, diff and rollback. #721
already took its lessons; the platform itself is a service to run.

## 3. Comparison

Rating: **3** strong, **2** partial, **1** weak, **0** fails or
violates. "Ships" means a consumer gets it with the plugin or
`factory-init`, with nothing else installed.

| Option | Trace ticket → req → decision → feedback | History over time | Agent token cost | Offline / CI checkable | Fresh session | Ships via plugin / factory-init | Stdlib, no MCP | One owner | Append-only evidence |
|---|---|---|---|---|---|---|---|---|---|
| Repo-native + trace view | 3 (joins typed ids that exist) | 3 (git log + issue timeline) | 3 (one bounded report on demand) | 3 (git part fully offline) | 3 | 3 | 3 | 3 (derived, never stored) | 3 |
| GitHub Projects v2 | 2 (issues/PRs only) | 1 | 2 (GraphQL pages) | 1 (online only) | 3 | 2 (`gh` calls, no files) | 2 (`gh`) | 0 (fields duplicate frontmatter) | 1 |
| GitHub Discussions | 1 | 2 (threads are dated) | 1 | 1 | 3 | 2 | 2 | 2 | 2 |
| GitHub wiki | 1 | 2 (its own git) | 2 | 0 (outside PRs and CI) | 3 | 0 | 3 | 0 (second docs tree) | 2 |
| Basic Memory | 2 (wikilink relations) | 1 (git only, cloud for more) | 2 | 1 (SQLite index off-git) | 3 | 0 | 0 (Py 3.12 + uv + MCP) | 1 | 1 |
| Obsidian vault + Bases | 2 (for a human) | 1 | n/a (app-only) | 0 (Bases needs the app) | 3 | 3 for reading (docs/ already is one) | 3 | 3 | 3 |
| MCP memory server | 1 | 0 (no timestamps, hard deletes) | 1 (`read_graph` dumps all) | 1 | 3 | 0 | 0 (node + MCP) | 0 | 0 |
| Graphiti | 3 | 3 (bitemporal) | 2 | 0 (graph DB + LLM) | 3 | 0 | 0 | 1 | 3 |
| Backlog.md | 2 | 2 (git) | 2 | 2 | 3 | 1 | 0 (node/bun) | 0 (second tracker) | 2 |
| git-bug | 2 | 3 (op log in git) | 2 | 2 | 3 | 0 | 0 (Go binary) | 0 (second tracker) | 3 |
| Notion | 2 | 2 (in-app) | 1 | 0 | 3 | 0 | 0 (hosted + OAuth MCP) | 0 | 1 |
| Linear | 3 (inside Linear) | 2 | 2 | 0 | 3 | 0 | 0 | 0 (replaces the tracker) | 1 |
| Confluence / Jira | 2 | 2 | 1 | 0 | 3 | 0 | 0 | 0 | 1 |
| WeKnora | 2 | 3 (page revisions) | 2 | 0 (service stack) | 3 | 0 | 0 | 1 | 2 |

Reading the table:

- Everything that scores well on history over time **outside** this repo
  (Graphiti, git-bug, Linear, WeKnora) does so by owning a second copy of
  facts the repo already owns. ADR-0061 rules that out, and ADR-0083 rules
  out a second tracker unless a script needs it.
- Every hosted or MCP option fails the bare install and fails CI
  checkability. Proposal D's rejection in ADR-0078 applies to them
  unchanged.
- The repo already holds what the over-time view needs: dated commits for
  every artifact, ADR supersession, typed ids, and issue timelines. The
  missing piece is a **reader**, not a store.

Two ideas are worth borrowing without the products:

- **Graphiti's validity windows**: an edge has a start and, once
  superseded, an end. The repo already expresses this as ADR
  `Supersedes` lines and ADR-0078's "superseded, never silently
  overwritten" claims, and the trace view should show both ends.
- **Obsidian compatibility for free**: frontmatter and plain links
  already make `docs/` a vault. Keep it so; ship nothing for it.

## 4. Recommendation: a generated trace view, shipped as a plugin-vended root tool plus a skill flow

**Build `trace.py`, a stdlib, read-only root tool vended with the
plugin (the `kb.py` and `board.py` pattern, ADR-0078 clause 7), and a
"trace" flow in the existing `knowledge-base` skill that runs it.** That
is option (b), a skill change, backed by a shipped tool as ADR-0062
requires. It is not (a): no payload tool imports it, so it is not
mirrored and not checksum-pinned. It is not (c): it has no dependency to
hide behind a seam. The one online input, the issue timeline, goes
through `cli.py`'s existing gh port and degrades to a stated
"issue history not read" line when offline or in CI.

Why this one:

1. **Nothing new to keep true.** The view is derived on demand from the
   owners and never committed, so it cannot drift and adds no second
   owner. Freshness is free.
2. **It is checkable.** Every edge it draws is a typed-id token,
   a run ref, a `(tracker: #N)` row or a `Closes #N` line — grammar
   `knowledge_plane.py` already owns and the gates already test.
3. **Token cost is paid only when asked**, as one bounded report
   (a `--budget` cap, like the kb index's 2048 bytes), instead of the
   agent grepping five places. The ablation suggests that is where the
   saving is.
4. **Consumers get it with the plugin**, stamped or not, because it reads
   only files every pipeline repo has. Stamped repos already carry
   `knowledge_plane.py` and `human_gates.py` in the payload.
5. **It closes the feedback gap with one convention, not a store**:
   feedback that concerns a requirement cites its run ref or typed id.
   The tool lists feedback it can tie to a run; a later lint (optional)
   can list feedback-labelled issues that cite nothing.

### Sketch of the over-time view (not built)

    python3 trace.py feature:orchestrator     # or PRD-0013, ADR-0084, #849, docs/kb/<slug>.md
    python3 trace.py feature:orchestrator --json

Resolution: any key resolves to its run (a typed id through the run
that declares or cites it; an issue through its `(tracker: #N)` row or
the run ref in its body; a kb page through its `sources`). The report
then has four sections, each a dated, chronological list:

    feature:orchestrator  (PRD-0013)                         as of 8df41e8
    TICKETS     #N  opened/closed dates, wo:* label flips (issue timeline)
    REQUIREMENTS
      2026-10-10  idea.md, prd.md created (PRD-0013)         008dd34
      2026-10-11  breakdown.md created; rows checked off     569695a ..
    DECISIONS
      2026-10-11  ADR-0084 accepted (cited by architecture.md)  b6548a0
                  ...superseded-by edges with both dates
    FEEDBACK
      2026-10-11  review.md findings m1-m10 resolved          35b9806
      2026-10-13  retro.md written                            81999d9
      issues citing feature:orchestrator or PRD-0013, with state and date
    CHANGES SINCE <date>   per-artifact commit list, `git log --follow`

The dates and commits shown are this run's real history at `8df41e8`.
The JSON form carries the same edges for the dashboard or the
pipeline-board skill to render later; neither re-derives them (ADR-0062).

Size: one module of about 300 lines and its tests, reusing
`knowledge_plane.parse_run`, `run_dirs`, the token regexes and
`protocol.run_ref`, plus `human_gates.read_timelines` for issue history.
Rough breakdown for the follow-up feature issue, if accepted:

1. Resolve a key to a run and its artifacts, offline (tests on fixture trees).
2. Git history per artifact and ADR supersession edges.
3. Issue edges through the gh port, with the offline degrade line.
4. The skill flow in `skills/knowledge-base/SKILL.md`, the CONTEXT.md
   term ("trace view"), a LEDGER row at draft, and trigger-eval cases.
5. Optional, separately decided: a lint that lists feedback issues
   citing no run.

### ADR

**A new ADR, amending neither ADR-0078 nor ADR-0083.** ADR-0078 decides
where durable facts live and how they are indexed; a derived, never
stored view changes none of that, and its rejection of proposal D stands.
ADR-0083 keeps one tracker; this adds a reader, not a tracker. The new
ADR records the tool, its key grammar, the never-committed rule, and the
feedback citation convention (the one new obligation on writers). If the
Owner later wants that convention enforced by a gate, the tool moves into
the payload and that is a second decision.

## 5. Rejected, and what would change the verdict

- **GitHub Projects v2**: revisit if the Owner wants a human board across
  repos; it would then be a view over issues with no custom fields that
  copy frontmatter.
- **Discussions**: revisit if outside users start sending feedback; a
  category per run ref would keep the citation convention.
- **Basic Memory, MCP memory, Graphiti, WeKnora**: revisit only past the
  scale ADR-0078 names (hundreds of pages), and then as an optional
  adapter behind a seam, never a requirement.
- **Linear, Notion, Confluence/Jira, Backlog.md, git-bug**: each replaces
  or duplicates the single tracker; revisit only by superseding ADR-0083.
- **GitHub wiki**: outside PRs and CI; no condition makes it fit.

## 6. Sources (read 2026-10-14)

- GitHub Projects: https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects
- GitHub GraphQL changelog 2026: https://docs.github.com/en/graphql/overview/changelog/2026
- GitHub issue timeline events API (version 2026-03-10): https://docs.github.com/en/rest/issues/timeline
- GitHub Discussions: https://docs.github.com/en/discussions/collaborating-with-your-community-using-discussions/about-discussions
- GitHub wikis: https://docs.github.com/en/communities/documenting-your-project-with-wikis/about-wikis and https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages
- Basic Memory: https://github.com/basicmachines-co/basic-memory and https://docs.basicmemory.com/whats-new/changelog
- Obsidian Bases: https://obsidian.md/help/bases
- MCP memory server: https://github.com/modelcontextprotocol/servers/tree/main/src/memory
- Graphiti: https://github.com/getzep/graphiti
- Backlog.md: https://github.com/MrLesk/Backlog.md
- git-bug: https://github.com/git-bug/git-bug
- Notion MCP: https://developers.notion.com/docs/mcp
- Linear MCP: https://linear.app/docs/mcp ; GitHub issue sync: https://linear.app/docs/github and https://www.linear.app/changelog/2023-12-14-github-issues-sync
- Atlassian remote MCP server: https://www.atlassian.com/platform/remote-mcp-server
- WeKnora: https://github.com/Tencent/WeKnora

Not verified: Basic Memory's exact latest version (the repo mentions
v0.23, the changelog's newest entry is v0.22), Backlog.md's and git-bug's
latest release dates, and whether GitHub exposes Projects field-change
history through any API.
