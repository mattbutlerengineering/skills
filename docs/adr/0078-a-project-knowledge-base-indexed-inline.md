# A project knowledge base, indexed inline in the always-loaded file

- Status: accepted
- Date: 2026-10-10

Amends no record. ADR-0023's utility-skill taxonomy, ADR-0061's one fact
one owner and ADR-0062's shipped-tool rule stand; this decides where a
target repo's durable project knowledge lives, how an agent finds it, and
who may write it. Issue #625.

## Context

The owner asked for skills that set up and maintain a project knowledge
base and fetch from it token-efficiently. Two research passes are
recorded in `docs/research/knowledge-base.md` (four proposals, A to D)
and `docs/research/knowledge-base-evidence.md` (what has measurably
worked). The evidence that shaped this decision:

- Context pays only when it is **non-inferable**. Repository overviews
  did not help agents navigate, and LLM-generated context files cost
  0.5 to 3 points with roughly 20% more inference cost (Gloaguen et al.).
- **Passive beats on-demand discovery.** A skill went uninvoked in 56% of
  Vercel's cases; an 8KB index inline in AGENTS.md scored 100% against
  53% for no docs. About 97% of llms.txt files are never fetched.
- **Unverified, self-filed knowledge is the measured loser**, and the
  LLM-wiki community's top failure mode is compounding errors. Their
  convergent fix is "agents draft, humans promote".
- **Whole-document rewrites erode detail** (ACE's context collapse);
  itemised deltas do not.
- Knowledge bases die of staleness; the fixes are source pointers,
  verification stamps and a scheduled lint.

The name "knowledge plane" is already taken: it means the run artifacts
(ADR-0004, ADR-0032, `knowledge_plane.py`).

## Decision

1. **One utility skill, `knowledge-base`** (ADR-0023), with three flows:
   setup, ingest, and lint/maintain. It owns no run artifact and is never
   routed to. The read path needs no skill.
2. **Pages live in `docs/kb/`, outside every run directory**, and hold
   only non-inferable knowledge: invariants, gotchas, cross-module flows,
   the why with its ADR cited. No overviews, no restated code, no
   restated vocabulary or decisions. Page frontmatter is `summary` (one
   line, the one owner of the page's index line), `sources` (repo paths),
   `verified` (a commit sha) and `related` (sibling slugs).
3. **The index is inline in the always-loaded file.** `kb.py index`
   writes one line per page between managed markers in every one of
   `CLAUDE.md` and `AGENTS.md` that exists, idempotently, and refuses to
   write a block over 2048 bytes. Page bodies are read on demand.
4. **Ingest proposes, a human promotes.** The agent drafts itemised
   ADD/UPDATE/DELETE/NOOP items (the verbs `docs/research/eval-and-memory.md`
   already adopted); superseded claims are marked, never silently
   overwritten; pages are never regenerated wholesale; an answer to a
   question is never filed without promotion.
5. **"Do not X" guardrails belong in the always-loaded file**, not in
   pages: they work only when they are in front of the agent as it acts.
6. **Freshness is mechanical.** `kb.py lint` returns problem strings for
   an over-budget index, missing frontmatter, broken sources, related
   slugs and links, orphans and dangling index entries, an out-of-date
   index, and stale pages: a cited source changed in git between the
   page's `verified` commit and HEAD.
7. **`kb.py` is a root tool vended with the plugin**, like `board.py`:
   the skill runs it from `<skill dir>/../../kb.py`. It is not mirrored
   into the factory payload, because no payload tool imports it.

## Consequences

- The always-loaded file grows by the index block on every turn. The
  budget caps that cost, and the cap is the lever, not a search engine:
  proposal D (vector or graph retrieval) stays rejected, and proposal C
  (a generated code map) stays parked until the knowledge base itself is
  shown to pay.
- Maturity is earned only by evidence. The LEDGER row stays at draft
  until a paired ablation on a real repo, with the same tasks run with
  the block present and absent, reports pass rate, tokens and steps.
  The evidence predicts the win, if any, is efficiency rather than
  correctness.
- Lint cannot catch a note that is wrong about code nobody changed. The
  skill tells the agent to re-check a page against code before it drives
  a decision.
- This repo dogfoods the skill with a small seeded `docs/kb/` and the
  managed block in its own `CLAUDE.md` and `AGENTS.md`.
