---
stage: idea
run: feature:kb-from-knowledge-work-plugins
date: 2026-11-08
origin: "GitHub issue #1274 (titled \"knowledge base improvements\"), filed by the Owner and picked by them as this run's subject; the run's PR carries Closes #1274 and no work orders are mirrored. Interview answered from autorun-brief.md in this directory; no live interview held. Not a backlog seed: no line in docs/backlog.md is claimed."
assumptions:
  - "In-flight check ran and nothing matches (the skill requires it only for a backlog seed; run anyway). `gh pr list --state open` returned one PR, #1606 (docs/research-engineering-plugin, a ship rollback-trigger change), unrelated. `git branch -a --no-merged origin/main` filtered on kb, knowledge, memory and harvest gave four local branches whose PRs are already merged by squash (feat/kb-weknora-lessons #722, feat/knowledge-base-skill #635, docs/knowledge-system-over-time-research #870, fix/a-sketch-drawn-from-memory #1100, a ux-design fix), two local re-verify branches with no diff to main under docs/features, docs/fixes, kb.py, kb_harvest.py or skills/knowledge-base, two branches with no run artifacts (fix/747-adr-record-in-knowledge-plane, fix/knowledge-plane-adr-read-and-row-block), and fifteen remote hourly/*kb* branches, each touching only docs/kb pages (or AGENTS.md and CLAUDE.md lines), never a run directory or kb tool. `git worktree list` showed the same branches. No branch carries run artifacts for this surface."
  - "Seed check: docs/backlog.md has no seed for this run and none carries (from: feature:kb-from-knowledge-work-plugins), so nothing was claimed and the re-run guard found nothing already seeded. Nearest lines, recorded rather than claimed: the unratified issue-436 survey note naming mem0-style memory consolidation, and the 2026-10-16 seeds putting kb.py lint and kb.py drift in make check, which are about gating, not about what lint or harvest can see."
  - "Outside corroboration (the optional last30days check) was not run: the skill says never to run it unasked, no human was present to ask, and the brief's no-spend constraint applies. The interview alone is a complete result."
  - "Ambition ladder (feature-run version): the brief gave no rung pick, so the skill's recommended default, Showstopper, was taken and is logged here. The four tests were run silently and all pass (see Ambition rung)."
  - "The demo prompts were not asked: the brief's success statement already names the demo moment (lint flags an expired external fact; harvest proposes the three duplicated memories as NOOP/CONFLICT and a memory-only gotcha as ADD)."
  - "The verbatim quote is the body of issue #1274, which the brief quotes as the Owner's ask; the issue's title is \"knowledge base improvements\". The Owner's later \"double check, include anything that would improve our knowledge base\" is quoted alongside because it widened the run from one item to all eight."
  - "Binding scope from the brief, not re-decided here: in scope are skills/knowledge-base, kb.py, kb_harvest.py, their tests, the payload mirror and manifest if a mirrored file changes, and this repo's docs/kb/main-unprotected.md as the first user of item 1; out of scope are writing the Owner's auto-memory, promoting any candidate into docs/kb, connectors, search, and usage-based demotion. No paid run; LEDGER maturity does not move; prepare-and-stop release; ux not-applicable is the PRD's to record."
  - "No evidentiary question was left unanswered by the brief, so nothing was surfaced. Evidence below is exactly the brief's, with its labels (observed in this repo versus external practice, unmeasured here); nothing was researched at this stage and no memory file was read."
---

# Idea: Teach the knowledge base what it cannot see yet

> "evaluate these claude code plugins and determine what we can use to improve our knowledge base functionality." — and, offered a single item, "double check, include anything that would improve our knowledge base"

## Problem

An agent working in a repo with a knowledge base trusts a page whose claim
has stopped being true outside the repo, because `kb.py lint` says
`kb: 0 problem(s)`: lint calls a page stale only when a cited repo file
changes after `verified:`, and an external-system fact (a GitHub setting, a
tool's behaviour) cites no file that would change. Lessons the agent or the
Owner already learned sit where the KB never reads them, in personal
auto-memory and in the human's corrections inside transcripts, so a cloud
routine or a fresh worktree agent learns them again the hard way.

## Who has it

This repo's own sessions and routines (the hourly improvement and
merge-train routines included), and any repo that installs the plugin's
knowledge-base skill, which is at draft maturity in `LEDGER.md`. They cope
today by hand: a re-check note written into the page itself, a personal
memory index the Owner curates outside the repo, and repeating corrections
from one session to the next.

## Why now

Issue #1274 asks for this evaluation, and the read of
anthropics/knowledge-work-plugins (Apache-2.0) done for #1275 on 2026-11-08
supplied the sources. That text is data for this run, restated in this
repo's words and credited, never copied.

## Evidence

Observed in this repo:

- **Item 1, external facts go unchecked.** `docs/kb/main-unprotected.md`
  claims a GitHub setting, cites two ADRs, and carries a hand-written note
  to re-check it with two commands because nothing in the repo records the
  setting. The claim still held on 2026-11-08 (`branches/main`
  `protected: false`, rulesets `0`), but nothing would flag it if it
  stopped holding. Source practice: knowledge-work-plugins'
  `customer-support/skills/kb-article/` (a suggested review date, a stale
  check at six months).
- **Item 2, memory the KB never reads.** CLAUDE.md sends durable project
  knowledge to `docs/kb/`, "not into an issue or a memory store", yet the
  Owner's auto-memory for this repo holds 39 memory files (18 feedback, 15
  project, 6 reference; counts from the brief, files not read here). Three
  duplicate KB pages: `cross-pr-hazard-pairwise-merge-test` against
  `cross-pr-merge-hazards`, `manifest-regen-stray-patch-files` against
  `manifest-regen`, `pr-body-no-work-order-waiver` against
  `pr-body-contract`. Repo gotchas such as `gh-pr-edit-broken-use-rest`,
  `closes-keyword-binds-first-issue-only`, `delete-branch-only-after-merged`
  and `gate-exit-masked-by-tail` live only in memory, where the cloud
  routines never see them. The knowledge-base skill never mentions memory,
  and `kb_harvest.py` reads transcripts only. Source practice:
  `productivity/skills/memory-management/` (a hot cache and a deep store,
  with promotion and demotion).
- **Item 3, corrections are not harvested.** `kb_harvest.py` emits two
  candidate kinds only, fail-edit-pass `arcs` and `recurring_errors`, and
  the skill's step 2a says autonomous sessions "rarely produce a human
  correction". Interactive sessions do: the session that set up this run
  produced two that changed the work, one of them ("double check")
  overturning #1606's performance pass. Anecdote, one session. Source
  practice: `small-business/skills/build-agent/reference/capture.md`,
  `sales/skills/setup/`.

External practice, no failure observed here (unmeasured):

- **Item 4, class pages.** One rule over many instances
  (`small-business/shared/absent-is-not-zero.md`). Labelled a hunch: the
  index uses 1,230 of its 2,048 bytes across 6 pages (`kb.py stats`), so
  there is no budget pressure yet.
- **Item 5, gotcha summaries keyed by symptom** (zoom plugin's
  troubleshooting files, `operations/skills/runbook/`).
- **Item 6, setup asks the human for tribal knowledge**
  (`data/skills/data-context-extractor/`, `build-agent/reference/capture.md`),
  asked one question at a time with a recommendation, per the Owner's
  stated working style.
- **Item 7, an optional wrong/right pair on gotcha pages** (31
  `small-business/skills/*/reference/gotchas.md` files).
- **Item 8, what a claim was verified against, and what it was not**
  (`small-business/shared/quickbooks-report-traps.md`, the zoom files):
  `verified:` records a commit, not an environment.

Considered and rejected by the orchestrator, for the PRD to confirm or
reopen: usage-based demotion, glossary decoding of shorthand, confidence
scores and weighted source ranking, enterprise search and digest, a harvest
watermark, and a per-page cold-reader test (reasons in the brief).

## Ambition rung

Chosen: Showstopper, in the user's words: "determine what we can use to improve our knowledge base functionality"
Not taken: Solid: adopt what the plugins teach as lint, harvest and rubric changes that each fix one observed gap, with no single moment that shows the KB catching what it used to miss; Moonshot: a knowledge base that keeps its external claims true by itself, re-running each page's declared check against the live system on a schedule and opening a re-verify change when one stops holding (seeded to docs/backlog.md)
Demo: pass — after one lint and one harvest run, the output names `main-unprotected.md` as past its declared age and lists the three memory duplicates beside their pages plus one memory-only gotcha as a new candidate
Removes a step: pass — the hand-written re-check note and the Owner's by-hand cross-reading of memory against `docs/kb/` are gone; lint and harvest surface both
Only this product: pass — it reads this repo's own pages, its own harvest of its own sessions, and the agent's memory of this repo, none of which an outside tool sees
Achievable: pass — riskiest piece is reading a harness-specific, per-machine memory directory from a shipped tool without breaking harness neutrality or proposing a user-scoped fact; spike below

## The demo

Before: `kb.py lint` prints `kb: 0 problem(s)` over a page whose GitHub claim
nothing re-checks, and the lessons in memory are invisible to harvest. After:
lint flags that page as past its declared age, and harvest prints the three
duplicated memories as NOOP/CONFLICT against their pages and a memory-only
gotcha as an ADD candidate, each still waiting for a human to promote it.

## Riskiest piece + spike

Reading auto-memory: the directory is harness-specific and per machine, and
it holds user-type facts that must never be proposed into a repo. A spike of
about two days over a fixture memory directory, never the real one, could
prove that memory files can be matched to KB pages (the three known
duplicates found, a memory-only gotcha proposed) while user-scoped entries
are excluded and the shipped skill text names no harness path.

## Cheapest kill test

By file name only, set the 39 memory files against the six KB pages and the
rubric's bar for a page: if, beyond the three known duplicates, no
memory-only lesson is repo-scoped and non-inferable enough to pass, item 2
carries no payload; and if `main-unprotected.md` is the only page making an
external claim, item 1 has one user and may be cheaper as the hand note it
already is.

## Solution hunch

Mostly `kb.py` and `kb_harvest.py` changes with tests, plus rubric and
skill-body lines: a way for a page to declare an outside source and a
maximum age or re-check, so lint can flag it; memory files and correction
turns as new harvest candidates, proposed through ingest's unchanged
human-promotes rule; and rubric lines for class pages, symptom-first
summaries, the wrong/right shape and the verified-against line. How each
piece is carried is Architect's call, and the PRD may cut any item that
fails its own bar.

## Success in one sentence

`kb.py lint` flags an external-fact page that is past its declared age, and
harvest proposes the three duplicated memories as NOOP/CONFLICT against
their pages and a memory-only gotcha as an ADD candidate, every new
candidate still going through the human-promotes rule.

## Unknowns & risks

- The auto-memory directory is harness-specific and per machine. Reading it
  from a shipped tool raises harness neutrality (the protocol's section) and
  privacy: memory holds user-type facts that must never be proposed into a
  repo.
- Detecting a "correction" turn from transcript text is fuzzy; false
  positives cost the Owner's attention on every harvest.
- A re-check that runs a command (for example `gh api`) puts network and
  credentials inside lint, which is offline today and runs in `make check`.
- Eight items is a wide PRD for a feature run. Cutting items that fail the
  PRD's bar is a valid outcome, not a failure.
- Items 4 to 8 have no failure observed here; adopting them on external
  practice alone risks rubric growth nobody needed.
- None of this moves LEDGER maturity: the skill's Graduation rule needs a
  real run.
