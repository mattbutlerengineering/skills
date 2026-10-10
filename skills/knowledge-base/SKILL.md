---
name: knowledge-base
description: Use when the ask is to set up, feed, or check a project knowledge base — "set up a knowledge base for this repo", "write down the gotchas an agent keeps tripping over", "capture what this PR taught us so the next session knows", "is our project knowledge stale". Keeps only non-inferable facts in docs/kb/ — invariants, gotchas, cross-module flows, the why with its ADR — never overviews or restated code. The shipped kb.py tool writes a compressed index of page summaries inline into CLAUDE.md or AGENTS.md, so every session sees it. Ingest proposes itemised page edits and a human promotes them; nothing is filed automatically. Lint flags pages whose cited sources changed since verified, orphans, broken links and an over-budget index. Not audit (find defects), deepen (module shape), doctor (pipeline install) or automate (which hooks to add). Owns no run artifact and is never routed to.
---

# Knowledge Base

Keep the small set of facts about this project that an agent **cannot
cheaply get by reading the code**, in a place every session sees without
being asked. Everything else is noise that costs tokens on every turn.

The evidence behind every rule here is in this plugin's research notes
(ADR-0078). Its short form: context helps only when it carries
non-inferable information; agents skip on-demand discovery about half the
time, so the index is loaded passively; LLM-written, unverified knowledge
is the measured loser, so a human promotes every edit; and knowledge
bases die of staleness, so freshness is checked mechanically.

This is not a stage in the lifecycle pipeline and it owns no run
artifact. The run artifacts are the **knowledge plane**; this is the
**knowledge base** — durable project facts that outlive any one run.

| The ask | Flow |
|---|---|
| No `docs/kb/` yet | **Setup** — step 1 |
| A merged PR, a retro, a research note, a hard-won lesson | **Ingest** — step 2 |
| "Is it still true?", or before trusting a page | **Lint and maintain** — step 3 |

## The tool

Every fact about the knowledge base's state comes from the shipped tool,
two directories above this skill's directory in the same checkout:

    python3 <this skill's directory>/../../kb.py index [repo root]
    python3 <this skill's directory>/../../kb.py lint  [repo root]
    python3 <this skill's directory>/../../kb.py stats [repo root]

`index` writes one line per page — `- docs/kb/<slug>.md: <summary>` —
between managed markers in every always-loaded file present (`CLAUDE.md`,
`AGENTS.md`), idempotently, and refuses when a page has no summary or the
block would pass its ~2KB budget. `lint` prints problem strings and exits
nonzero when there are any. Never hand-edit the managed block and never
re-derive what the tool states.

## 1. Setup

1. Create `docs/kb/`.
2. Find candidate pages. Read `references/page-rubric.md` first. Good
   sources are the repo's own record of pain: ADRs with a "Context"
   section that names a failure, review findings, retros, commit messages
   that say "fix" twice for the same thing, and anything the always-loaded
   file warns about at length. Do **not** seed from the README, a
   directory listing or module docstrings — that is inferable.
3. Propose at most five pages to the user as a numbered list: slug,
   one-line summary, the cited sources, and the one sentence that makes
   the page non-inferable. Write only the ones the user approves.
4. Move "do not X" guardrails you found into the always-loaded file
   itself, not into pages — a guardrail must be in front of the agent
   at the moment it is about to act.
5. Run `kb.py index`, then `kb.py lint`.

Done when: `kb.py lint` prints `kb: 0 problem(s)` and the user has seen
the managed block in the always-loaded file.

## 2. Ingest — propose, the human promotes

Read `references/ingest.md`. For one source (a merged PR, a retro, a
research note, a lesson from this session):

1. Read the source and the pages its summary lines touch — the index is
   already in front of you.
2. Draft an itemised change list. Each item is one verb on one claim:
   **ADD** a claim, **UPDATE** a claim (the old one is kept and marked
   superseded, never silently overwritten), **DELETE** a claim that is no
   longer true (say what disproves it), or **NOOP** (the source teaches
   nothing non-inferable — the most common correct answer).
3. Every added or updated claim cites a source path, and the page's
   `verified:` becomes the commit you checked it against.
4. Present the list and stop. Apply only the items the user promotes.
   Never rewrite a whole page, and never file an answer to a chat
   question as a page without that promotion.
5. Run `kb.py index` and `kb.py lint`.

Done when: every promoted item is applied, nothing unpromoted was
written, and lint is clean.

## 3. Lint and maintain

Run `kb.py lint`. For each problem:

- **stale** — a cited source changed since `verified`. Re-read the
  changed code, then propose UPDATE, DELETE or NOOP per claim (step 2's
  rules). A page that is still true gets its `verified:` moved to HEAD.
- **orphan / out of date / no index** — run `kb.py index`.
- **missing frontmatter, broken source, related or link** — fix the page,
  or delete it if nothing on it survives.
- **over budget** — shorten summaries, merge pages, or delete the page
  that pays least. `kb.py stats` shows page sizes. Past the budget, the
  answer is fewer pages, not a search engine.

Lint cannot see a note that is wrong about code nobody changed. When a
page is about to drive a decision, re-check its claim against the code
first; the oldest `verified:` goes first.

Done when: `kb.py lint` prints `kb: 0 problem(s)`.

## Graduation

This skill stays at draft until a paired ablation on a real repo — the
same tasks with the managed block present and absent — reports pass
rate, tokens and steps. The evidence predicts the win, if any, is
efficiency rather than correctness; report whichever it is.
