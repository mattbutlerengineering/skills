# Research for issue #625: a skill (or skills) that maintains a project knowledge base

Research note, 2026-10-10. The owner asked for: "a skill or a set of skills to
maintain a world class knowledge base of information about a project. There
should be setup knowledge base. effectively fetching knowledge base data to
utilize tokens and space efficiently. Deep research solutions online and
propose several ideas."

Constraints from this repo that any proposal has to respect: stdlib-only
Python; skills stay harness-neutral (Claude Code + omp) with no MCP or
third-party dependency (README "bare install"); the utility-skill vs
stage-skill taxonomy (ADR-0023); a skill that states repo facts runs a shipped
tool instead of re-deriving them (ADR-0062); one fact, one owner (ADR-0061);
and LEDGER maturity only via real runs.

## 1. What this repo already has (build on it, don't duplicate it)

| Existing piece | Role it already plays | Implication for #625 |
|---|---|---|
| `CLAUDE.md` (short, pointer-heavy) | Always-loaded layer: verify commands, hard conventions, "where things are decided" | Already a hub-and-spoke index. A KB should hang off it with one pointer line, not grow it |
| `CONTEXT.md` | Canonical vocabulary, read by `deepen` step 1 and others | The KB's glossary. KB pages link to its terms and never redefine them |
| `docs/adr/NNNN-*.md` (75 ADRs, status-tagged) | Decisions with supersede-don't-rewrite discipline | The KB's "why" layer. KB pages cite ADR-#### and never restate a decision (ADR-0061) |
| `docs/standards.json` + `standards_index.py` (ADR-0073) | Machine-readable normative statements with `source` anchors | Prior art inside the repo for a structured index whose entries point back to their prose owner |
| `knowledge_plane.py` (ADR-0004/0037/0068) | Typed-ID grammar (PRD/ADR/WO tokens) plus the run-directory walk | Reuse `ADR_TOKEN`/`PRD_TOKEN` for KB link checks. The "knowledge plane" name is already taken by run artifacts, so the new thing needs a different name (e.g. "knowledge base", "project wiki") and a CONTEXT.md entry |
| `orientation_pack.py` | Bundles cited ADRs and named files into a work order's prompt | This is already a token-budgeted, just-in-time context bundle. A KB index could feed it later |
| `docs/research/*.md` | Dated research notes | Same shape as Karpathy's raw-sources layer |
| `bd remember` / `bd memories` (82) + auto-memory `MEMORY.md` index | Agent-gotcha memory: one-line index, topic files on demand | Already the Karpathy/Claude-Code index-plus-topic-files pattern, but for *agent operating knowledge*, not *project knowledge*. Keep that split explicit |
| `docs/factory/doc-gardener-routine.md` | Weekly docs-hygiene routine (trigger deferred) | The natural scheduled home for a KB lint pass |
| `docs/research/eval-and-memory.md` | Already adopted mem0's ADD/UPDATE/DELETE/NOOP consolidation and Letta "sleep-time" maintenance as "Adapt" | The KB's maintain flow should use the same consolidation verbs rather than invent new ones |

So the repo is already a strong hand-built knowledge base. What #625 adds is
**a portable, setup-able version of it for any target repo**, plus mechanical
upkeep: index budgets, staleness, orphans and broken links.

## 2. Sources (2025-2026)

Primary:

- Karpathy, "LLM Wiki" gist (Apr 2026): https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
  - Three layers: immutable raw sources, an LLM-owned wiki, and a schema file (CLAUDE.md/AGENTS.md).
  - `index.md` is "a categorized catalog of every page with a link, a one-line summary", read first on every query. `log.md` is append-only, with greppable prefixes like `## [date] ingest | Title`.
  - Three operations: **ingest** (one source touches 10-15 pages), **query** (index, then pages, then a cited answer, with good answers filed back as pages), and **lint** (contradictions, stale claims, orphans, missing cross-refs).
  - "Works surprisingly well at moderate scale (~100 sources, ~hundreds of pages)" with no embeddings. Optional search (qmd) only past that scale.
- Anthropic, "Effective context engineering for AI agents" (Sep 2025): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - Keep lightweight references and load just in time. A **hybrid** loads some data up front (CLAUDE.md) and the rest by glob/grep.
  - Progressive disclosure, structured note-taking (NOTES.md), and compaction.
  - Sub-agents return "condensed, distilled" summaries of about 1-2k tokens.
- Anthropic, "Equipping agents for the real world with Agent Skills": https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
  - Three disclosure levels: name+description always loaded, the SKILL.md body on relevance, and reference files or script output on demand.
- Claude Code memory docs: https://code.claude.com/docs/en/memory
  - CLAUDE.md files above the cwd load at launch. Subdirectory CLAUDE.md files load on demand, when a file there is touched.
  - `.claude/rules/*.md` with `paths:` globs load only when matching files are in scope.
  - `@imports` do NOT cut context cost, because imports load at launch (max 4 hops). Target under 200 lines per CLAUDE.md.
  - Auto-memory `MEMORY.md` is an index (first 200 lines/25KB loaded, one line per entry). Topic files are "read on demand using its standard file tools".
  - AGENTS.md is read when no CLAUDE.md exists.
- llms.txt spec: https://llmstxt.org/
  - An H1 name (the only required part), a blockquote summary, then H2 sections of `[name](https://...): note` links.
  - An H2 named **"Optional"** holds links "an agent can skip when a shorter context is needed". Pages can also be served as `.md` twins.
- Gloaguen et al., "Evaluating AGENTS.md" (arXiv 2602.11988, ICLR 2026): https://arxiv.org/abs/2602.11988
  - Context files "do not generally improve task success rates" and raise inference cost by more than 20%. This held for both LLM-generated and developer-written files.
  - Agents follow their *instructions* well. **Repository overviews were not helpful.**
  - The authors recommend limiting context files to non-standard practices and evaluating before deploying.
- Khatri, "Do Context Files Help Coding Agents?" (Jul 2026 preprint): https://www.alphaxiv.org/abs/2607.27250
  - 288 runs on Claude Code and Codex found no measurable correctness change.
  - A second-hand report of Lulla et al. (Jan 2026) found about 28.6% lower runtime and about 16.6% fewer output tokens with AGENTS.md: https://codex.danielvaughan.com/2026/08/06/do-context-files-help-coding-agents-agents-md-ablation-study-codex-cli-correctness-vs-efficiency/
- Codebase-Memory (arXiv 2603.27277, Mar 2026): https://arxiv.org/abs/2603.27277
  - A tree-sitter knowledge graph over MCP, tested on 31 repos.
  - It scored **83% answer quality vs 92%** for a grep/file-exploration agent, using **about 10x fewer tokens** and 2.1x fewer tool calls.
- Aider repo map: https://aider.chat/docs/repomap.html
  - Ranks the def/ref graph (PageRank) and emits signatures within `--map-tokens` (default 1k). The map grows when no files are in chat.
  - Pattern write-up: https://www.agentpatterns.ai/context-engineering/repository-map-pattern/

Secondary / ecosystem:

- Karpathy-wiki write-ups:
  - https://blog.starmorph.com/blog/karpathy-llm-wiki-knowledge-base-guide
  - https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an
- LLM Wiki Claude Code plugin (skill, 3 subagents, 5 commands, 8 stdlib Python tools, `/wiki-init`): https://www.claudepluginhub.com/plugins/flight505-llm-wiki-upstream-engineering-llm-wiki
- DeepWiki (Cognition, auto-generated repo wikis, 50k+ public repos): https://docs.devin.ai/work-with-devin/deepwiki
- Cline Memory Bank (projectbrief/activeContext/progress files): https://docs.cline.bot/best-practices/memory-bank.md
- Kiro steering (`.kiro/steering/*.md`): https://kiro.dev/docs/web/memory/
- qmd (local BM25 + vector + rerank search over markdown, with an MCP server): https://awesome.ecosyste.ms/projects/github.com%2Ftobi%2Fqmd
- Doc-drift checkers:
  - stale-cli (doc older than the code it references, broken refs): https://socket.dev/npm/package/stale-cli
  - Staleguard (offline paths/commands/symbols checker): https://gitblind.noratr.app/Arthur920/Staleguard
  - doc-drift-detector skill: https://skillselion.com/skills/borghei/claude-skills/doc-drift-detector
- Code-graph MCP servers:
  - GitNexus: https://ascii.co.uk/news/article/news-20260223-b0a37d50/gitnexus-builds-ai-ready-code-knowledge-graphs-for-agent-rel
  - codegraph-rust (tree-sitter + SQLite FTS5): https://awesome.ecosyste.ms/projects/github.com%2Fsunerpy%2Fcodegraph-rust

### What the evidence says, in one paragraph

Always-loaded context costs tokens on *every* turn and buys little
correctness. Generic overviews are the worst offender (Gloaguen). What pays:
(a) a tiny always-loaded layer limited to non-obvious rules and pointers,
(b) an **index** the agent reads first and follows only as far as needed
(Karpathy's index.md, llms.txt, MEMORY.md, and the skills' three disclosure
levels all converge on this one shape), (c) path-scoped loading, so knowledge
arrives when its files are touched, (d) sub-agents that read deeply and return
1-2k token distillations, and (e) mechanical upkeep, since an LLM-maintained
wiki decays without a lint pass. Pre-computed graphs or maps cut tokens about
10x at a measurable accuracy cost (83% vs 92%). They are a retrieval
accelerator, not a replacement for reading code.

## 3. Proposals

### Proposal A: Project wiki (the Karpathy LLM-Wiki pattern, adapted to a codebase)

**Skills:**
- `kb-init` (utility): sets up `docs/kb/` and seeds pages from what already exists (README, CONTEXT.md, ADR titles, the top-level module docstrings). It adds a one-line pointer to CLAUDE.md.
- `kb` (utility), with three verbs:
  - **ingest:** a merged PR, a run's retro.md, a research note or a doc. It updates or creates 1-N pages using mem0's ADD/UPDATE/DELETE/NOOP verbs, rewrites the index lines it touched, and appends to log.md.
  - **query:** reads the index, then the pages, then cites. A good answer is filed back as a page.
  - **lint:** runs a shipped `kb.py` per ADR-0062.

**Layout:**
```
docs/kb/
  index.md        # llms.txt grammar: H1, > summary, H2 sections of
                  # "- [Page](https://.../pages/x.md): one-line summary"; H2 "Optional"
                  # for deep/rare pages. Hard budget, e.g. <=150 lines / ~2k tokens
  log.md          # append-only, "## [YYYY-MM-DD] ingest | <source>"
  pages/<slug>.md # frontmatter: title, summary (the index line, one owner),
                  # sources: [code paths / ADR-#### / PRD-####],
                  # verified: <git sha>, related: [slugs]
```

**Token efficiency:** only the CLAUDE.md pointer is always loaded (1 line).
The index is read on demand and is budget-capped and lint-enforced. Pages are
short (lint caps them at about 300 lines) and link to code instead of copying
it. A `query` run can go in a subagent that returns a distilled answer.

**Setup vs maintain:** init is one interactive pass. Maintenance is ingest
on demand, plus `kb.py lint` (a natural job for the doc-gardener routine's
deferred weekly trigger).

**Lint checks (stdlib, deterministic):**
- broken links and orphans
- index and page budgets
- `summary` and index line disagreeing
- **stale page:** `git log <verified>..HEAD -- <sources>` is non-empty
- ADR/PRD tokens that resolve to nothing, via `knowledge_plane` regexes

**Cost/complexity:** medium. Two skills, one tool of about 300 lines plus
tests, two LEDGER rows, and trigger-eval cases. The risk is that the wiki
becomes the "repository overview" Gloaguen found useless, unless the page
rubric bans overview content.

### Proposal B: Context-hierarchy curator (progressive disclosure through harness primitives, no new store)

**Skills:**
- `context-setup` (utility): audits and restructures what the harness already loads.
  - Splits a fat CLAUDE.md to under 200 lines, keeping only non-standard rules plus a "where things are decided" pointer table (this repo's own CLAUDE.md is the model).
  - Moves area-specific rules into `.claude/rules/<area>.md` with `paths:` globs, or into nested `<dir>/CLAUDE.md` files that load on touch.
  - Ensures a CONTEXT.md glossary and an ADR index exist, and writes a root `llms.txt` index of docs/ in llms.txt grammar.
- `context-tune` (utility, maintain): measures the always-loaded token cost per session and flags overview prose (the Gloaguen anti-pattern). It also flags contradictions between layers, `@imports` that were meant to defer but don't, and rules whose `paths:` match nothing.

**Layout:** none new. It uses CLAUDE.md, `.claude/rules/`, nested CLAUDE.md/AGENTS.md, CONTEXT.md, docs/adr/ and llms.txt.

**Token efficiency:** the best possible for the always-loaded layer, because
it is the layer the evidence says to shrink. Retrieval is the harness's own
lazy loading. There is no query machinery.

**Cost/complexity:** low (one or two skills, a small measuring tool).
However, it overlaps the existing `automate` skill (CLAUDE.md rules that
nothing enforces) and Claude Code's built-in `/doctor prompt-audit`. It is
also partly Claude-Code-specific (`.claude/rules`, `paths:`), which strains
harness neutrality. It does not give the owner "a knowledge base" so much as
a well-pruned instruction tree.

### Proposal C: Generated code map plus symbol index (an aider-style repo map, stdlib)

**Skill:** `kb-map` (utility), backed by a shipped `codemap.py`.
- It walks tracked files.
- For Python it uses `ast` (stdlib) for the module docstring, public defs and import edges.
- For other languages it uses a regex def-extractor or `ctags` if present (degrade honestly).
- It ranks modules by in-degree (simple PageRank over the import graph, in pure Python).
- It emits `docs/kb/map.md` within a token budget (default about 1k, like aider), plus `docs/kb/symbols.json` for `codemap.py find <name>` lookups.

**Token efficiency:** a precomputed, budgeted orientation. `find` returns
file:line without reading files. Per Codebase-Memory, this is about 10x fewer
tokens for structural questions.

**Setup vs maintain:** fully regenerable, so there is no drift. Regeneration
can be a pre-commit/`make check` step, with a gate that fails when the
checked-in map is stale (the same discipline as `factory_init.py
update-manifest`).

**Cost/complexity:** medium-high for good multi-language coverage.
Tree-sitter is not stdlib, so outside Python this is lossy. It captures
*structure*, not *knowledge*: why, gotchas and decisions. On its own it does
not meet "world class knowledge base", but it is a strong complement to A.

### Proposal D: Searchable store with semantic retrieval (graph or vector MCP)

**What it is:** wire a store such as qmd (BM25 + vector + rerank over
markdown) or a code-graph MCP server (Codebase-Memory, GitNexus) in as the
retrieval layer. A setup skill installs and indexes it, and a maintain skill
reindexes it.

**Token efficiency:** the best at large scale (thousands of pages), since
queries return ranked snippets.

**Cost/complexity:** high. It breaks the stdlib-only and "bare install, no
MCP" rules and needs node/GGUF models or binaries. Index state lives outside
git, and it trades 9 points of accuracy for tokens. Karpathy's own guidance
is that it is unnecessary below about 100 sources and hundreds of pages.

**Verdict:** reject as a default. At most, mention it in A's SKILL.md as an
optional escalation once `kb.py stats` shows the index has outgrown its
budget.

## 4. Recommendation: Proposal A, shaped by B's evidence, with C as a later add-on

Build **one utility skill, `knowledge-base`, with three flows** (setup,
ingest, lint) and a shipped stdlib `kb.py`. Let the read path need no skill
at all.

1. **The read path costs zero until used.** Setup adds a single CLAUDE.md
   line: "Project knowledge: start at docs/kb/index.md; read only the pages
   you need." Agents then navigate index, page and code by plain file reads,
   which is Anthropic's just-in-time pattern. No query skill is needed, which
   also avoids a trigger-discrimination fight with every Q&A prompt.
2. **The index is the product.** Use the llms.txt grammar (a recognised
   cross-tool format) with an "Optional" H2 for depth, a hard line/token
   budget enforced by `kb.py lint`, and each page's `summary:` frontmatter as
   the one owner of its index line. `kb.py index` regenerates the index from
   that frontmatter, so it never drifts (ADR-0061/0062).
3. **Content rubric from the evidence.** Pages hold what an agent cannot
   cheaply re-derive by reading code: invariants, gotchas, cross-module flows,
   "why" with ADR citations, glossary links, and operational runbooks.
   Overviews and restated code are banned (Gloaguen). CONTEXT.md and ADRs stay
   the owners; KB pages link to them.
4. **Freshness is mechanical, not hoped for.** `sources:` plus `verified:
   <sha>` frontmatter lets `kb.py lint` list pages whose cited code changed
   since verification. Ingest then re-verifies, using ADD/UPDATE/DELETE/NOOP
   and appending to log.md. That lint is exactly the "rot no detector sees"
   the doc-gardener routine exists for, and in a stamped repo it could become
   a non-blocking detector.
5. **Why not B alone:** it is mostly what `automate`, `/doctor prompt-audit`
   and this repo's own CLAUDE.md discipline already provide, and it doesn't
   produce a knowledge base. Fold its two best rules into A's setup flow:
   keep CLAUDE.md under 200 lines with pointers only, and use path-scoped
   loading where the harness supports it. **Why not C first:** it maps
   structure, not knowledge, and is lossy without tree-sitter. Add it as
   `kb.py map` once A has a real run. **Why not D:** it violates the stdlib
   and bare-install conventions and isn't needed at project scale.

**Open questions for the owner (ask one at a time):**
- One skill with flows, or the `kb-init` + `kb` split? Recommendation: one
  skill. There are fewer descriptions to discriminate, and setup is rare.
- Location: `docs/kb/`, or reuse `docs/` with an `llms.txt` at the root?
  Recommendation: `docs/kb/`. It keeps run artifacts (the knowledge plane)
  and the wiki apart, and avoids a name collision.
- Should this repo dogfood it on itself first, seeding from CONTEXT.md,
  `docs/research/` and the ADR titles? Recommendation: yes. It is the only
  honest way to graduate the LEDGER row.

**Rough size:** SKILL.md plus `references/page-rubric.md`, and `kb.py`
(`index`, `lint`, `stats`) at about 300-400 lines with tests in
`tests/test_kb.py`. It also needs a `UTILITY_SKILLS` entry, a CONTEXT.md term
("Knowledge base", distinct from "knowledge plane"), an ADR for the tool and
its frontmatter contract, trigger-eval cases against `audit`/`deepen`/`doctor`,
and a draft LEDGER row.
