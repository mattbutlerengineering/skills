# Eval harnesses & agent memory: survey and shortlist

Research note, 2026-09-20/21. Question: which output-eval patterns from
promptfoo and DeepEval could mature this repo's own draft-stage eval suite
(`eval_schema.py`, trigger + output evals — ADR-0019, ADR-0022), and which
agent-memory patterns from mem0 and Letta could deepen the reflect loop
beyond "journal-as-state" — all within this repo's eval-honesty rule
(`evals/results/` is append-only, never rewrite a failing case to pass) and
its stdlib-only constraint? Primary sources: promptfoo's and DeepEval's own
docs, and mem0's/Letta's own docs/blog posts.

## What the factory already has

Two eval kinds, both on-demand and never a CI gate (ADR-0019): **trigger
evals** (`trigger_eval.py`), which install every skill description at once
and check which fires for a routing case, rolling results into a
**confusion matrix** ("expected → fired" counts) but no derived composite
score; and **output evals** (`evals/output/<slug>.json`,
`docs/output-evals.md`), where a fresh subagent grades a produced artifact
against numbered, binary, no-partial-credit expectations — "Do not grade on
style or effort; only on whether the statement is true," each verdict
citing evidence. Results are dated and append-only; never edit an eval
definition to make a failing case pass; a skill graduates LEDGER maturity
only via a real run, never eval evidence alone (ADR-0012, ADR-0019). The
"reflect loop" today is the daily improvement routine (ADR-0044) posting
findings to a pinned journal issue (#181) — append-only, forever, with no
consolidation step.

## promptfoo

**What it is.** An open-source LLM eval/red-team CLI, YAML-configured.
Source: <https://www.promptfoo.dev/docs/configuration/expected-outputs/>,
<https://www.promptfoo.dev/docs/configuration/expected-outputs/model-graded/g-eval/>.

**Core mechanisms.**

- **Deterministic and model-graded assertions in one config surface.**
  Exact-match, regex, and JSON-shape assertions sit alongside model-graded
  ones (`llm-rubric`, `factuality`, `g-eval`, `answer-relevance`) in the
  same test-case list — a project chooses per-assertion which kind of
  check it needs rather than committing the whole suite to one grading
  style.
- **G-Eval: chain-of-thought scoring against free-text criteria**, "using
  gpt-4.1-2025-04-14 by default," producing a `GradingResult` — "whether
  the test case passed, the score, the reason for the result, the tokens
  used, and the results of any component assertions." An assertion passes
  when its score clears a **threshold (default 0.7)**; when the criteria
  value is an array, "each criterion is graded independently and the
  scores are averaged" before the threshold check.
- **Derived/composite metrics** are computed *after* evaluation completes,
  from already-graded named assertions — "useful for metrics like F1
  scores, weighted averages, or custom scoring formulas" — a second pass
  over recorded results, not a new grading run.

## DeepEval

**What it is.** An open-source LLM testing framework, pytest-style.
Source: <https://deepeval.com/docs/metrics-llm-evals>,
<https://deepeval.com/docs/metrics-introduction>.

**Core mechanisms.**

- **G-Eval as the general-purpose custom metric**: "instantiate a `GEval`
  class and define an evaluation criteria in everyday language... employs
  a chain-of-thoughts (CoTs) approach to generate evaluation steps, which
  are then used to score an LLM test case," reported to "significantly
  outperform all traditional non-LLM evaluations across... coherence,
  consistency, fluency, and relevancy" versus non-LLM scoring.
- **A conversational variant** scores whole multi-turn transcripts rather
  than single outputs, using token-probability-weighted summation rather
  than a single terminal judgment.

## mem0

**What it is.** An open-source memory layer for LLM agents. Source:
<https://mem0.ai/blog/long-term-memory-ai-agents>,
<https://mem0.ai/blog/graph-memory-solutions-ai-agents>.

**Core mechanisms.**

- **A two-phase Extractor/Updater pipeline, not append-only.** The
  Extractor "identifies and extracts key facts from new message pairs
  using both a conversation summary and recent messages"; the Updater then
  "consolidates information and ensures memory consistency, **deciding
  whether to ADD, UPDATE, DELETE, or NOOP for each candidate fact**." Every
  new fact is reconciled against what's already stored, not just appended.
- **Hierarchical, retrieval-scoped storage.** Facts are stored in a vector
  database "indexed by user, session, and agent identifiers"; a new
  session retrieves relevant memories "using semantic similarity, keyword
  matching, and entity matching" rather than loading everything.
- **An optional graph variant** adds entity linking — "extracts entities
  from each memory and stores them in a parallel entity collection" —
  for relationship queries beyond flat semantic similarity.

## Letta

**What it is.** An agent framework built around an explicit, tiered memory
model. Source: <https://docs.letta.com/guides/core-concepts/memory/archival-memory>,
<https://docs.letta.com/guides/agents/architectures/sleeptime/>.

**Core mechanisms.**

- **Two memory tiers with different retrieval contracts.** Core memory is
  "in-context memory blocks... pinned to the agent's context window" (a
  user-preferences block, a persona/objectives block); archival memory is
  "a semantically searchable database" that "must be queried on-demand via
  tools" and "cannot be pinned to the context window" — search understands
  concepts, not just keywords ("artificial memories" finds "implanted
  memories"). The split is deliberate: always-loaded vs. retrieved-when-
  relevant are different resources with different costs.
- **Sleep-time compute: memory maintenance as its own scheduled agent.**
  "Sleep-time agents share the memory of your primary agents, but run in
  the background and can modify the memory asynchronously" — reorganizing
  and improving memory "during idle periods" instead of "lazy, incremental
  updates during conversations." A primary agent can have one or more
  associated sleep-time agents dedicated to this.

## Shortlist

| # | Mechanism (source) | Verdict | Own ADR? |
|---|--------------------|---------|----------|
| 1 | ADD/UPDATE/DELETE/NOOP consolidation for durable-knowledge state (mem0) | **Adapt** | Yes |
| 2 | Scheduled background memory-maintenance agent (Letta sleep-time) | **Adapt** | No — extend ADR-0044's routine |
| 3 | Two-tier pinned-vs-queried memory split (Letta core/archival) | **Reject — already true** | — |
| 4 | Chain-of-thought weighted-threshold grading (promptfoo/DeepEval G-Eval) | **Reject** | — |
| 5 | Post-hoc derived composite metrics from recorded assertions (promptfoo) | **Adopt** | No — extend `trigger_eval.py` |

### Rationales

**1. ADD/UPDATE/DELETE/NOOP consolidation — Adapt, and scoped narrowly on
purpose.** The factory's "journal-as-state" reflect loop — the daily
routine posting to issue #181 — is structurally append-only with no
consolidation step, the same shape mem0's Extractor/Updater design
explicitly exists to fix (raw append produces exactly the failure this
survey's own authoring session hit firsthand: a stale, specific-sounding
claim sat uncorrected in a separate memory store until directly
contradicted by current state — the record existed, nothing reconciled it
against reality). mem0's per-fact ADD/UPDATE/DELETE/NOOP decision is the
right shape for **bd remember-style durable knowledge and the improvement
journal** — records that should represent current understanding, not
history. It is the *wrong* shape, and must never be applied, to
`evals/results/`, `docs/factory/costs.jsonl`, or `docs/backlog.md`'s seed
log, whose entire value is being append-only, dated, and never rewritten —
the eval-honesty rule and the cost ledger's audit trail both depend on that
immutability. One ADR, and its first sentence should draw this boundary
explicitly so a future reader doesn't generalize it into the ledger.
Evidence: mem0.ai (quoted above) vs. ADR-0044's journal-as-state design and
this repo's own eval-honesty rule.

**2. Scheduled background memory-maintenance agent — Adapt, extending what
already exists rather than adding new infrastructure.** ADR-0044's daily
improvement routine is already a bounded, scheduled background process —
structurally the same slot Letta's sleep-time agents occupy ("run in the
background," "during idle periods"). The gap is scope: today the routine
only *appends* findings; it does not *reconcile* prior ones. Letta's
framing — memory maintenance as its own first-class scheduled job, distinct
from the primary agent's real-time work — argues for giving the existing
routine (or a second bounded job under the same hard-bounds discipline
ADR-0044 already enforces) an explicit consolidation pass over the journal
and `bd remember` store, applying item 1's ADD/UPDATE/DELETE/NOOP decision
per finding. Not a new ADR: it's a scope extension of ADR-0044's existing
routine, tunable the way that ADR is already tuned — by PR, never by the
routine editing its own protocol. Evidence:
<https://docs.letta.com/guides/agents/architectures/sleeptime/> vs.
`docs/factory/improvement-routine.md`.

**3. Two-tier pinned-vs-queried memory — Reject, already true.** Letta's
core-memory/archival-memory split (always-in-context vs. queried
on-demand) already exists in this repo's own tooling: `bd prime` loads
persistent memories into context at session start (core-memory-shaped), and
`bd search`/`bd memories <keyword>` retrieves on demand without loading
everything (archival-memory-shaped). CLAUDE.md plus CONTEXT.md occupy the
same always-loaded role Letta's core-memory blocks do. Nothing to import;
recorded as convergent evidence the factory's existing memory split matches
a considered design elsewhere, not a gap.

**4. Chain-of-thought weighted-threshold grading — Reject.** G-Eval's
averaged, threshold-gated score (default 0.7, criteria arrays averaged
before the compare) is designed to smooth over noisy single-criterion
judgments — useful when a metric is inherently fuzzy (coherence, fluency).
The factory's output-eval grader deliberately does the opposite: binary,
no-partial-credit, one citation of evidence per expectation, explicitly
"not on style or effort." That stronger bar exists because a threshold
average can hide one real miss behind several passing criteria — precisely
the kind of false-positive the eval-honesty rule exists to prevent
elsewhere in this repo. Adopting G-Eval-style averaging for output evals
would weaken, not strengthen, the existing discipline. Evidence:
promptfoo/DeepEval docs (quoted above) vs. `docs/output-evals.md`'s grader
template.

**5. Post-hoc derived composite metrics — Adopt, and it answers an already-
recorded pain point directly.** `trigger_eval.py` already computes a
confusion matrix (`expected -> fired`) but derives no summary score from
it, and `docs/backlog.md` already names the resulting blind spot: "omp
near-miss under-triggering: 8/16 near-miss cases under-trigger on omp vs
Claude Code." A raw pass-count or a printed confusion matrix does not
surface that ratio as a single trackable number the way a derived
per-skill precision/recall/F1 would — promptfoo's model (compute composite
scores from already-graded, already-recorded assertions, as a second pass,
never re-running the model) fits the factory's append-only results
discipline exactly: the derivation reads `results/trigger-*.json`, it does
not re-grade or touch the eval definition. Cheap, stdlib-only (it's
arithmetic over an existing dict), and does not touch the eval-honesty
boundary since nothing about a case's recorded pass/fail changes — only a
summary computed from it. No new ADR: a function in `trigger_eval.py`
(or a small script reading its results) that derives per-skill precision/
recall/F1 from `confusion`, matching this repo's existing "extend the seam
module" convention rather than growing a parallel report path. Evidence:
promptfoo docs (quoted above) vs. `trigger_eval.py:339-360` and
`docs/backlog.md`'s recorded under-triggering seed.

## Couldn't verify

- **mem0's exact consolidation decision boundary** — what specifically
  triggers UPDATE vs. DELETE vs. NOOP for a given candidate fact (a
  similarity threshold? an LLM judgment call? both?) was not found in the
  fetched material; item 1's ADR would need to design the factory's own
  decision rule rather than copy mem0's undocumented one.
- **Letta sleep-time agents' failure/conflict behavior** — what happens
  when a sleep-time agent's proposed memory edit conflicts with a change
  the primary agent made in the same window was not covered in the fetched
  pages.
- **DeepEval's conversational G-Eval token-probability weighting details**
  — asserted ("uses the probabilities of the LLM output tokens to
  normalize the score") but the exact formula was not fetched; does not
  affect the Reject verdict, which rests on the averaging-hides-misses
  argument, not the formula's precision.
- **Fetch-tool caveat**, as with the two companion surveys in this batch:
  quotes came through a summarizing search/fetch pass, not independently
  re-grepped against raw primary-source text.

## Primary sources

- promptfoo: <https://www.promptfoo.dev/docs/configuration/expected-outputs/>,
  <https://www.promptfoo.dev/docs/configuration/expected-outputs/model-graded/g-eval/>
- DeepEval: <https://deepeval.com/docs/metrics-llm-evals>,
  <https://deepeval.com/docs/metrics-introduction>
- mem0: <https://mem0.ai/blog/long-term-memory-ai-agents>,
  <https://mem0.ai/blog/graph-memory-solutions-ai-agents>
- Letta: <https://docs.letta.com/guides/core-concepts/memory/archival-memory>,
  <https://docs.letta.com/guides/agents/architectures/sleeptime/>
- This repo: `eval_schema.py`, `trigger_eval.py`, `docs/output-evals.md`,
  ADR-0019, ADR-0044
