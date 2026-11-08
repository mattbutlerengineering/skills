---
stage: prd
run: feature:kb-from-knowledge-work-plugins
id: PRD-0022
date: 2026-11-08
ux: not-applicable
ux-reason: "Skill text and two stdlib CLI tools (kb.py, kb_harvest.py) whose output an agent reads; no user-facing surface."
assumptions:
  - "No live interview: every answer comes from autorun-brief.md, collected from the Owner on 2026-11-08. Actors, user stories, success criteria, scope and open questions were derived from the brief and idea.md; where the brief offered a choice it left to the PRD (which of its eight items to keep), the PRD's own bar decided it, as the brief allows."
  - "PRD-0022 is the id the brief reserved (the highest on main and on unmerged branches is PRD-0021)."
  - "ux: not-applicable is the brief's reading, adopted unchanged: the deliverable is skill text and two stdlib CLI tools whose output an agent reads."
  - "The bar each of the brief's eight items was held to: evidence of a failure observed in this repo, and at least one success criterion checkable offline. Items 1 and 2 pass and are kept. Item 3 has observed evidence but is deferred (see Out of scope). Items 4 to 7 are cut for no observed failure. Item 8 is cut except the part item 1 already needs (naming the outside system an external-fact page was checked against). The orchestrator's six rejected candidates are confirmed rejected: no new evidence was found to reopen any."
  - "idea.md's cheapest kill test was applied by file name only, from names idea.md already cites; no memory file was read. Item 2 survives it: beyond the three duplicates, idea.md names four memory-only gotchas that are repo-scoped and non-inferable by name. Item 1 half-fails it: of the six docs/kb pages, main-unprotected.md is the only one whose claim is about an outside system. It is kept because the page rubric invites external-system facts in every repo that installs the skill and lint can check none of them, and an offline age check is cheap."
  - "idea.md's The demo is prose, not a numbered script; it is copied as the steps of the 'demo runs as written' criterion. Its last step (the skill classifying memory candidates as NOOP, CONFLICT or ADD against the real memory directory) needs a model session on the Owner's machine, so it is marked NOT RUN for the Owner rather than offline-checkable."
  - "Success criteria use fixture directories with fixture text written for the tests; fixture memory files may reuse the three duplicate file names idea.md cites, never the real files' contents."
  - "No [NEEDS CLARIFICATION] marker was left in the draft, so the bounded clarify pass had nothing to ask."
---

# PRD: Teach the knowledge base what it cannot see yet

## Problem statement

An agent in a repo with a knowledge base trusts a page whose claim has
stopped being true outside the repo, because `kb.py lint` prints
`kb: 0 problem(s)`. Lint calls a page stale only when a cited repo file
changes after its `verified:` commit. A claim about an outside system (a
GitHub setting, a tool's behaviour) cites no file that would ever change.
This repo's `docs/kb/main-unprotected.md` shows it: it claims a GitHub
setting and carries a hand-written note to re-check two commands, because
nothing else will. Lint passes over it forever.

Lessons the Owner and the agent have already learned sit where the
knowledge base never reads them. The Owner's auto-memory for this repo
holds 39 memory files (counts from the brief). Three duplicate existing
pages, and gotchas such as `gh-pr-edit-broken-use-rest` and
`gate-exit-masked-by-tail` live only in memory, which the cloud routines
and fresh worktree agents never see. `kb_harvest.py` reads transcripts
only, and the knowledge-base skill never mentions memory. So those agents
learn the same lessons again the hard way.

## Solution

When this ships, a knowledge-base page whose claim is about an outside
system can say which system it was checked against, when, and how long
that check holds. Lint reports the page once it is past that age, so an
agent re-checks it before relying on it. This repo's `main-unprotected.md`
is the first page to declare this, in place of its hand-written note.

Harvest can also read the repo's auto-memory as a source. It lists each
repo-scoped memory entry as a candidate, beside the existing page it
likely duplicates when there is one. The skill turns those candidates into
NOOP, CONFLICT, UPDATE or ADD proposals through ingest's unchanged table,
and a human still promotes every one. User-scoped memory is never listed,
and the skill text names no harness-specific path. Lint stays offline and
harvest stays read-only.

## Actors

- **Reading agent**: any agent that reads `docs/kb/` before acting. This
  covers interactive sessions, the cloud routines (hourly improvement,
  merge-train) and fresh worktree agents, here and in any repo that
  installs the skill.
- **Ingesting agent**: the agent running the knowledge-base skill's
  ingest, which turns harvest candidates into itemised proposals.
- **Promoter**: the human who rules on proposals and promotes them into
  `docs/kb/` (the Owner, in this repo).

## User stories

1. As a Reading agent, I want lint to report an external-fact page that is
   past its declared age, so that I re-check the claim before trusting it.
2. As a Promoter, I want an external-fact page to state the outside system
   it was checked against, the date and how long the check holds, so that
   the re-check rule lives in a field lint reads, not in a note nothing
   reads.
3. As an Ingesting agent, I want harvest to list this repo's memory
   entries as candidates, each beside the page it likely duplicates, so
   that I can propose NOOP, CONFLICT, UPDATE or ADD without the Promoter
   cross-reading memory against `docs/kb/` by hand.
4. As a Promoter, I want user-scoped memory never to appear as a
   candidate, so that nothing personal is ever proposed into the repo.
5. As a Reading agent in a cloud routine, I want a repo lesson that lives
   only in memory to reach `docs/kb/` once a Promoter promotes it, so that
   I do not learn it again by failing.

## Success criteria

All criteria except the last two are checkable offline: stdlib tests,
fixture directories, an injected "today", and never the real `~/.claude`.

- [ ] **Age is flagged.** In a fixture `docs/kb/`, a page that declares an
      outside source, a check date and a maximum age is reported by
      `kb.py lint` as one problem string naming the page and saying it is
      past its declared age, when the injected today is after date plus
      age. The same page is not reported when today is within the age.
- [ ] **Lint stays offline.** The age check runs no command and opens no
      network connection. A test proves it with the command runner
      replaced by one that fails on any call.
- [ ] **Malformed declarations are reported.** A page whose declared date
      or age cannot be read gets a problem string naming the page and the
      field. It is never silently treated as fresh.
- [ ] **Existing pages are unaffected.** A page that declares no outside
      source is linted exactly as today. The existing `kb.py` tests pass
      unchanged.
- [ ] **This repo's page uses it.** `docs/kb/main-unprotected.md`
      declares its outside source (the GitHub API), its check date and a
      maximum age, and its hand-written "Re-check … nothing in the repo
      records the setting" note is gone. `python3 kb.py lint` over this
      repo exits 0 on the day it ships.
- [ ] **Memory duplicates are paired.** Over a fixture memory directory
      holding files named `cross-pr-hazard-pairwise-merge-test`,
      `manifest-regen-stray-patch-files` and `pr-body-no-work-order-waiver`
      (fixture text), beside a fixture `docs/kb/` holding
      `cross-pr-merge-hazards`, `manifest-regen` and `pr-body-contract`,
      harvest's output lists each memory candidate paired with its page.
- [ ] **A memory-only gotcha is unpaired.** A fixture memory file with no
      matching page appears in harvest's output as a candidate with no
      page beside it.
- [ ] **User scope is excluded.** A fixture memory file marked as
      user-scoped appears nowhere in harvest's output, and no text from
      it does either. The memory directory's own index file is not listed
      as a candidate.
- [ ] **Harvest stays read-only.** After a harvest over the fixtures,
      every fixture file and the fixture `docs/kb/` are byte-identical to
      before. Memory excerpts in the output are capped, as transcript
      excerpts already are.
- [ ] **Fixtures only.** Every new test points harvest at a fixture
      directory. None reads the real memory directory or `~/.claude`.
- [ ] **Harness-neutral skill text.** `skills/knowledge-base/SKILL.md` and
      its `references/` contain no harness-specific path (no `~/.claude`,
      no `projects/<slug>/memory`). A test or grep checks this.
- [ ] **Human still promotes.** `references/ingest.md` routes memory
      candidates through the same NOOP, CONFLICT, UPDATE and ADD table
      and the same rule that a human promotes. No new path writes to
      `docs/kb/`.
- [ ] **Routing unchanged.** The knowledge-base skill's frontmatter
      `description` is unchanged (checked by diff against `main`). If a
      later stage changes it, the routing eval is owed and recorded NOT
      RUN with the command `python3 trigger_eval.py`.
- [ ] **The battery passes.** `python3 run_tests.py`, `python3 lint.py`,
      `python3 kb.py drift` and `python3 gates.py && python3 gates.py
      --selftest` each exit 0. If a mirrored file changed, the manifest
      was regenerated after stray `.orig`/`.rej` files were deleted.
- [ ] **The demo runs as written.** NOT RUN for the Owner: the last step
      needs a model session against the real memory directory, on the
      Owner's machine.
      1. Before: `kb.py lint` prints `kb: 0 problem(s)` over a page whose
         GitHub claim nothing re-checks, and the lessons in memory are
         invisible to harvest.
      2. After: lint flags that page as past its declared age (shown by
         setting its check date or age so that it is past).
      3. Harvest lists the three duplicated memories beside their pages,
         and the skill proposes them as NOOP or CONFLICT.
      4. Harvest lists a memory-only gotcha with no page, and the skill
         proposes it as an ADD candidate, each still waiting for a human
         to promote it.
- [ ] **LEDGER untouched.** The knowledge-base skill's maturity in
      `LEDGER.md` does not move. Its Graduation rule needs a real run,
      and none is made here.

## Out of scope
<!-- coverage-waiver: exclusions build nothing; no work order implements an absence -->

Deferred, with observed evidence:

- **Item 3, harvesting human corrections.** The gap is real: harvest
  emits only arcs and recurring errors. But the evidence is one
  session's anecdote, as idea.md labels it. Its main risk is false
  positives that cost the Promoter's attention on every harvest, and no
  offline check can measure that: a fixture only confirms whatever
  heuristic it was written for. The demo and success sentence do not need
  it. It could be reopened by a precision count of correction candidates
  over real interactive transcripts.

Cut, no failure observed in this repo:

- **Item 4, class pages.** A hunch: the index uses 1,230 of 2,048 bytes
  over six pages, so there is no budget pressure.
- **Item 5, gotcha summaries keyed by symptom.** Unmeasured. No session
  here is known to have missed a page because of how its summary was
  worded.
- **Item 6, setup asking the human for tribal knowledge.** Unmeasured.
  Item 2 reaches the store where that knowledge already sits, without a
  new interview.
- **Item 7, an optional wrong/right pair on gotcha pages.** Unmeasured.
  The rubric's current shape has not been shown to fail.
- **Item 8, a general "verified against" environment line** (local zsh
  against Linux CI, a tool version). Unmeasured. Only the part item 1
  needs is kept: an external-fact page names the outside system it was
  checked against.

Also out:

- Running a page's declared check (such as `gh api`) from lint or on a
  schedule. That puts network and credentials inside an offline gate,
  and it is the Moonshot rung idea.md seeded to the backlog.
- Writing or editing the Owner's auto-memory, and promoting any candidate
  into `docs/kb/`.
- Connectors, MCP search, a search engine over the knowledge base, a
  digest.
- Confirmed rejected: usage-based demotion, glossary decoding of
  shorthand, confidence scores and weighted source ranking, enterprise
  search and digest, a harvest watermark, a per-page cold-reader test.
- Any paid model run, and any LEDGER maturity change.

## Open questions

- How a page declares its outside source, check date and maximum age
  (frontmatter fields or another form), and whether a page with an outside
  source but no age gets a default or a lint problem. Answered by:
  Architect.
- Whether the declared age belongs in the compressed index line, given
  the 2,048-byte budget. Answered by: Architect.
- How harvest finds the memory directory (beside the transcript
  directory it already resolves, an explicit flag, or both), and whether
  memory is read on every harvest or only on request. Answered by:
  Architect, within harness neutrality.
- How a memory file is paired with a page (file name, summary text, cited
  sources) and how a memory file's user scope is read from the harness's
  memory format. Answered by: Architect, from the format's documentation
  and fixture files, never the real directory.
- How harvest's new memory candidates and ingest's text credit
  knowledge-work-plugins (Apache-2.0), restated and never copied, the way
  `polish` credits Impeccable. Answered by: Architect.
- Whether item 3 (correction harvest) earns a later run. Answered by: the
  Owner, once a precision measurement exists.
